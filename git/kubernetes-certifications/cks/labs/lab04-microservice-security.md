# Lab 4: マイクロサービスセキュリティ

## 🎯 学習目標

このラボでは、Kubernetesクラスター内でのマイクロサービス間通信のセキュリティ強化を学習します：

- サービスメッシュ（Istio）によるセキュリティ
- mTLS（相互TLS）認証の実装
- マイクロサービス間の認可制御
- API ゲートウェイのセキュリティ
- 分散セキュリティ監視とトレーシング

## 📋 前提条件

- Kubernetes クラスターが稼働中
- kubectl が設定済み
- Helm がインストール済み
- [Lab 3: システム堅牢化](./lab03-system-hardening.md) の完了推奨

## 🏗️ アーキテクチャ概要

```
┌─────────────────────────────────────────────────────────────┐
│                マイクロサービスセキュリティ環境                  │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐     │
│  │    Istio    │    │    mTLS     │    │   RBAC &    │     │
│  │ Service Mesh│    │ Encryption  │    │ AuthZ/AuthN │     │
│  │             │    │             │    │             │     │
│  └─────┬───────┘    └─────┬───────┘    └─────┬───────┘     │
│        │                  │                  │             │
│        ▼                  ▼                  ▼             │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │              API Gateway Security                       │ │
│  │    Rate Limiting + JWT + OAuth2 + CORS                │ │
│  └─────┬───────────────────────┬───────────────────────────┘ │
│        │                       │                             │
│        ▼                       ▼                             │
│  ┌─────────────┐         ┌─────────────┐                     │
│  │  Monitoring │         │ Distributed │                     │
│  │ & Alerting  │         │   Tracing   │                     │
│  └─────────────┘         └─────────────┘                     │
└─────────────────────────────────────────────────────────────┘
```

## 🚀 Step 1: Istio サービスメッシュのインストール

### 1.1 Istio インストール

```bash
# Istio のダウンロードとインストール
curl -L https://istio.io/downloadIstio | sh -
cd istio-*
export PATH=$PWD/bin:$PATH

# Istio をクラスターにインストール
istioctl install --set values.defaultRevision=default -y

# Istio システム確認
kubectl get pods -n istio-system

# サイドカー自動注入の有効化
kubectl label namespace production istio-injection=enabled
kubectl label namespace development istio-injection=enabled

echo "Istio インストール完了"
```

### 1.2 基本的なマイクロサービスアプリケーションの展開

```yaml
# マイクロサービスアプリケーション用Namespace
cat << 'EOF' > microservices-namespace.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: microservices
  labels:
    istio-injection: enabled
EOF

kubectl apply -f microservices-namespace.yaml

# Frontend サービス
cat << 'EOF' > frontend-service.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: frontend
  namespace: microservices
spec:
  replicas: 2
  selector:
    matchLabels:
      app: frontend
  template:
    metadata:
      labels:
        app: frontend
        version: v1
    spec:
      containers:
      - name: frontend
        image: nginx:1.21-alpine
        ports:
        - containerPort: 80
        env:
        - name: BACKEND_URL
          value: "http://backend.microservices.svc.cluster.local:8080"
        securityContext:
          allowPrivilegeEscalation: false
          readOnlyRootFilesystem: true
          runAsNonRoot: true
          runAsUser: 1001
          capabilities:
            drop:
            - ALL
        volumeMounts:
        - name: tmp-volume
          mountPath: /tmp
        - name: cache-volume
          mountPath: /var/cache/nginx
      volumes:
      - name: tmp-volume
        emptyDir: {}
      - name: cache-volume
        emptyDir: {}
---
apiVersion: v1
kind: Service
metadata:
  name: frontend
  namespace: microservices
spec:
  selector:
    app: frontend
  ports:
  - port: 80
    targetPort: 80
    name: http
EOF

# Backend サービス
cat << 'EOF' > backend-service.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: backend
  namespace: microservices
spec:
  replicas: 2
  selector:
    matchLabels:
      app: backend
  template:
    metadata:
      labels:
        app: backend
        version: v1
    spec:
      containers:
      - name: backend
        image: hashicorp/http-echo:0.2.3
        args:
        - "-text=Backend Service Response"
        - "-listen=:8080"
        ports:
        - containerPort: 8080
        env:
        - name: DATABASE_URL
          value: "postgres://database.microservices.svc.cluster.local:5432"
        securityContext:
          allowPrivilegeEscalation: false
          readOnlyRootFilesystem: true
          runAsNonRoot: true
          runAsUser: 1001
          capabilities:
            drop:
            - ALL
---
apiVersion: v1
kind: Service
metadata:
  name: backend
  namespace: microservices
spec:
  selector:
    app: backend
  ports:
  - port: 8080
    targetPort: 8080
    name: http
EOF

# Database サービス（PostgreSQL）
cat << 'EOF' > database-service.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: database
  namespace: microservices
spec:
  replicas: 1
  selector:
    matchLabels:
      app: database
  template:
    metadata:
      labels:
        app: database
        version: v1
    spec:
      containers:
      - name: postgres
        image: postgres:13-alpine
        env:
        - name: POSTGRES_DB
          value: appdb
        - name: POSTGRES_USER
          value: appuser
        - name: POSTGRES_PASSWORD
          valueFrom:
            secretKeyRef:
              name: database-secret
              key: password
        ports:
        - containerPort: 5432
        securityContext:
          allowPrivilegeEscalation: false
          runAsNonRoot: true
          runAsUser: 70
          capabilities:
            drop:
            - ALL
        volumeMounts:
        - name: postgres-data
          mountPath: /var/lib/postgresql/data
      volumes:
      - name: postgres-data
        emptyDir: {}
---
apiVersion: v1
kind: Service
metadata:
  name: database
  namespace: microservices
spec:
  selector:
    app: database
  ports:
  - port: 5432
    targetPort: 5432
    name: postgres
---
apiVersion: v1
kind: Secret
metadata:
  name: database-secret
  namespace: microservices
type: Opaque
data:
  password: c2VjdXJlUGFzc3dvcmQxMjM=  # securePassword123
EOF

kubectl apply -f frontend-service.yaml
kubectl apply -f backend-service.yaml
kubectl apply -f database-service.yaml
```

## 🔐 Step 2: mTLS（相互TLS）認証の実装

### 2.1 PeerAuthentication 設定

```yaml
# 厳格なmTLSポリシー
cat << 'EOF' > mtls-policy.yaml
# Namespace全体でmTLSを強制
apiVersion: security.istio.io/v1beta1
kind: PeerAuthentication
metadata:
  name: default-mtls
  namespace: microservices
spec:
  mtls:
    mode: STRICT
---
# Frontend サービス専用mTLS設定
apiVersion: security.istio.io/v1beta1
kind: PeerAuthentication
metadata:
  name: frontend-mtls
  namespace: microservices
spec:
  selector:
    matchLabels:
      app: frontend
  mtls:
    mode: STRICT
---
# Backend サービス専用mTLS設定
apiVersion: security.istio.io/v1beta1
kind: PeerAuthentication
metadata:
  name: backend-mtls
  namespace: microservices
spec:
  selector:
    matchLabels:
      app: backend
  mtls:
    mode: STRICT
  portLevelMtls:
    8080:
      mode: STRICT
---
# Database サービス専用mTLS設定
apiVersion: security.istio.io/v1beta1
kind: PeerAuthentication
metadata:
  name: database-mtls
  namespace: microservices
spec:
  selector:
    matchLabels:
      app: database
  mtls:
    mode: STRICT
EOF

kubectl apply -f mtls-policy.yaml
```

### 2.2 DestinationRule 設定

```yaml
# mTLS通信のためのDestinationRule
cat << 'EOF' > destination-rules.yaml
# Frontend DestinationRule
apiVersion: networking.istio.io/v1beta1
kind: DestinationRule
metadata:
  name: frontend-destination
  namespace: microservices
spec:
  host: frontend.microservices.svc.cluster.local
  trafficPolicy:
    tls:
      mode: ISTIO_MUTUAL
  subsets:
  - name: v1
    labels:
      version: v1
---
# Backend DestinationRule
apiVersion: networking.istio.io/v1beta1
kind: DestinationRule
metadata:
  name: backend-destination
  namespace: microservices
spec:
  host: backend.microservices.svc.cluster.local
  trafficPolicy:
    tls:
      mode: ISTIO_MUTUAL
    loadBalancer:
      simple: LEAST_CONN
    connectionPool:
      tcp:
        maxConnections: 10
      http:
        http1MaxPendingRequests: 10
        maxRequestsPerConnection: 2
    circuitBreaker:
      consecutiveErrors: 3
      interval: 30s
      baseEjectionTime: 30s
  subsets:
  - name: v1
    labels:
      version: v1
---
# Database DestinationRule
apiVersion: networking.istio.io/v1beta1
kind: DestinationRule
metadata:
  name: database-destination
  namespace: microservices
spec:
  host: database.microservices.svc.cluster.local
  trafficPolicy:
    tls:
      mode: ISTIO_MUTUAL
    connectionPool:
      tcp:
        maxConnections: 5
        connectTimeout: 30s
  subsets:
  - name: v1
    labels:
      version: v1
EOF

kubectl apply -f destination-rules.yaml
```

## 🛡️ Step 3: 認証・認可制御の実装

### 3.1 JWT 認証設定

```yaml
# JWT認証のRequestAuthentication
cat << 'EOF' > jwt-authentication.yaml
apiVersion: security.istio.io/v1beta1
kind: RequestAuthentication
metadata:
  name: jwt-authentication
  namespace: microservices
spec:
  selector:
    matchLabels:
      app: frontend
  jwtRules:
  - issuer: "https://secure-microservices.local"
    jwksUri: "https://secure-microservices.local/.well-known/jwks.json"
    audiences:
    - "microservices-app"
    forwardOriginalToken: true
---
# JWT検証を必須とするAuthorizationPolicy
apiVersion: security.istio.io/v1beta1
kind: AuthorizationPolicy
metadata:
  name: require-jwt
  namespace: microservices
spec:
  selector:
    matchLabels:
      app: frontend
  rules:
  - from:
    - source:
        requestPrincipals: ["https://secure-microservices.local/*"]
    to:
    - operation:
        methods: ["GET", "POST"]
---
# 内部サービス間通信の許可
apiVersion: security.istio.io/v1beta1
kind: AuthorizationPolicy
metadata:
  name: internal-service-access
  namespace: microservices
spec:
  selector:
    matchLabels:
      app: backend
  rules:
  - from:
    - source:
        principals: ["cluster.local/ns/microservices/sa/default"]
    to:
    - operation:
        methods: ["GET", "POST", "PUT", "DELETE"]
    when:
    - key: source.labels[app]
      values: ["frontend"]
EOF

kubectl apply -f jwt-authentication.yaml
```

### 3.2 Role-Based Access Control (RBAC)

```yaml
# 詳細なRBACポリシー
cat << 'EOF' > rbac-policies.yaml
# Frontend アクセス制御
apiVersion: security.istio.io/v1beta1
kind: AuthorizationPolicy
metadata:
  name: frontend-rbac
  namespace: microservices
spec:
  selector:
    matchLabels:
      app: frontend
  rules:
  # 外部からのHTTPアクセス許可（JWT検証済み）
  - from:
    - source:
        requestPrincipals: ["*"]
    to:
    - operation:
        methods: ["GET"]
        paths: ["/", "/health", "/metrics"]
  # 管理者のみPOSTアクセス許可
  - from:
    - source:
        requestPrincipals: ["https://secure-microservices.local/admin"]
    to:
    - operation:
        methods: ["POST", "PUT", "DELETE"]
---
# Backend アクセス制御
apiVersion: security.istio.io/v1beta1
kind: AuthorizationPolicy
metadata:
  name: backend-rbac
  namespace: microservices
spec:
  selector:
    matchLabels:
      app: backend
  rules:
  # Frontend からのアクセスのみ許可
  - from:
    - source:
        principals: ["cluster.local/ns/microservices/sa/default"]
    to:
    - operation:
        methods: ["GET", "POST"]
    when:
    - key: source.labels[app]
      values: ["frontend"]
  # 監視システムからのメトリクス取得許可
  - from:
    - source:
        namespaces: ["istio-system", "monitoring"]
    to:
    - operation:
        methods: ["GET"]
        paths: ["/metrics", "/health"]
---
# Database アクセス制御
apiVersion: security.istio.io/v1beta1
kind: AuthorizationPolicy
metadata:
  name: database-rbac
  namespace: microservices
spec:
  selector:
    matchLabels:
      app: database
  rules:
  # Backend からのアクセスのみ許可
  - from:
    - source:
        principals: ["cluster.local/ns/microservices/sa/default"]
    to:
    - operation:
        ports: ["5432"]
    when:
    - key: source.labels[app]
      values: ["backend"]
  # 管理者による直接アクセス（制限付き）
  - from:
    - source:
        requestPrincipals: ["https://secure-microservices.local/dba"]
    to:
    - operation:
        ports: ["5432"]
    when:
    - key: request.headers[x-admin-access]
      values: ["true"]
---
# デフォルト拒否ポリシー
apiVersion: security.istio.io/v1beta1
kind: AuthorizationPolicy
metadata:
  name: deny-all-default
  namespace: microservices
spec:
  # セレクターなし = すべてのサービスに適用
  # ルールなし = すべて拒否
EOF

kubectl apply -f rbac-policies.yaml
```

## 🌐 Step 4: API ゲートウェイのセキュリティ実装

### 4.1 Istio Gateway 設定

```yaml
# セキュアAPIゲートウェイ
cat << 'EOF' > secure-gateway.yaml
# TLS証明書シークレット（自己署名例）
apiVersion: v1
kind: Secret
metadata:
  name: microservices-tls
  namespace: istio-system
type: kubernetes.io/tls
data:
  tls.crt: LS0tLS1CRUdJTiBDRVJUSUZJQ0FURS0tLS0t...  # Base64エンコードされた証明書
  tls.key: LS0tLS1CRUdJTiBQUklWQVRFIEtFWS0tLS0t...  # Base64エンコードされた秘密鍵
---
# HTTPSゲートウェイ
apiVersion: networking.istio.io/v1beta1
kind: Gateway
metadata:
  name: microservices-gateway
  namespace: microservices
spec:
  selector:
    istio: ingressgateway
  servers:
  # HTTP リダイレクト
  - port:
      number: 80
      name: http
      protocol: HTTP
    hosts:
    - "microservices.local"
    tls:
      httpsRedirect: true
  # HTTPS
  - port:
      number: 443
      name: https
      protocol: HTTPS
    tls:
      mode: SIMPLE
      credentialName: microservices-tls
    hosts:
    - "microservices.local"
---
# VirtualService（レート制限付き）
apiVersion: networking.istio.io/v1beta1
kind: VirtualService
metadata:
  name: microservices-routing
  namespace: microservices
spec:
  hosts:
  - "microservices.local"
  gateways:
  - microservices-gateway
  http:
  # API v1 ルーティング
  - match:
    - uri:
        prefix: "/api/v1/"
    route:
    - destination:
        host: frontend.microservices.svc.cluster.local
        port:
          number: 80
    fault:
      delay:
        percentage:
          value: 0.1
        fixedDelay: 5s
    retries:
      attempts: 3
      perTryTimeout: 2s
    timeout: 10s
  # ヘルスチェック
  - match:
    - uri:
        exact: "/health"
    route:
    - destination:
        host: frontend.microservices.svc.cluster.local
        port:
          number: 80
  # デフォルトルート
  - route:
    - destination:
        host: frontend.microservices.svc.cluster.local
        port:
          number: 80
EOF

kubectl apply -f secure-gateway.yaml
```

### 4.2 Rate Limiting と Security Headers

```yaml
# Rate Limiting設定
cat << 'EOF' > rate-limiting.yaml
# EnvoyFilter でRate Limitingを設定
apiVersion: networking.istio.io/v1alpha3
kind: EnvoyFilter
metadata:
  name: rate-limit-filter
  namespace: istio-system
spec:
  configPatches:
  - applyTo: HTTP_FILTER
    match:
      context: GATEWAY
      listener:
        filterChain:
          filter:
            name: "envoy.filters.network.http_connection_manager"
    patch:
      operation: INSERT_BEFORE
      value:
        name: envoy.filters.http.local_ratelimit
        typed_config:
          "@type": type.googleapis.com/udpa.type.v1.TypedStruct
          type_url: type.googleapis.com/envoy.extensions.filters.http.local_ratelimit.v3.LocalRateLimit
          value:
            stat_prefix: local_rate_limiter
            token_bucket:
              max_tokens: 100
              tokens_per_fill: 10
              fill_interval: 60s
            filter_enabled:
              runtime_key: local_rate_limit_enabled
              default_value:
                numerator: 100
                denominator: HUNDRED
            filter_enforced:
              runtime_key: local_rate_limit_enforced
              default_value:
                numerator: 100
                denominator: HUNDRED
            response_headers_to_add:
            - append: false
              header:
                key: x-local-rate-limit
                value: 'true'
---
# Security Headers設定
apiVersion: networking.istio.io/v1alpha3
kind: EnvoyFilter
metadata:
  name: security-headers
  namespace: microservices
spec:
  configPatches:
  - applyTo: HTTP_FILTER
    match:
      context: SIDECAR_INBOUND
      listener:
        filterChain:
          filter:
            name: "envoy.filters.network.http_connection_manager"
    patch:
      operation: INSERT_BEFORE
      value:
        name: envoy.filters.http.lua
        typed_config:
          "@type": type.googleapis.com/envoy.extensions.filters.http.lua.v3.Lua
          inline_code: |
            function envoy_on_response(response_handle)
              response_handle:headers():add("X-Frame-Options", "DENY")
              response_handle:headers():add("X-Content-Type-Options", "nosniff")
              response_handle:headers():add("X-XSS-Protection", "1; mode=block")
              response_handle:headers():add("Strict-Transport-Security", "max-age=31536000; includeSubDomains")
              response_handle:headers():add("Content-Security-Policy", "default-src 'self'")
              response_handle:headers():add("Referrer-Policy", "strict-origin-when-cross-origin")
            end
EOF

kubectl apply -f rate-limiting.yaml
```

## 📊 Step 5: 分散セキュリティ監視

### 5.1 Jaeger 分散トレーシング

```bash
# Jaeger インストール
kubectl apply -f https://raw.githubusercontent.com/jaegertracing/jaeger-operator/master/deploy/crds/jaegertracing.io_jaegers_crd.yaml
kubectl apply -f https://raw.githubusercontent.com/jaegertracing/jaeger-operator/master/deploy/service_account.yaml
kubectl apply -f https://raw.githubusercontent.com/jaegertracing/jaeger-operator/master/deploy/role.yaml
kubectl apply -f https://raw.githubusercontent.com/jaegertracing/jaeger-operator/master/deploy/role_binding.yaml
kubectl apply -f https://raw.githubusercontent.com/jaegertracing/jaeger-operator/master/deploy/operator.yaml

# Jaeger インスタンス作成
cat << 'EOF' > jaeger-instance.yaml
apiVersion: jaegertracing.io/v1
kind: Jaeger
metadata:
  name: microservices-jaeger
  namespace: istio-system
spec:
  strategy: production
  storage:
    type: elasticsearch
    elasticsearch:
      nodeCount: 1
      redundancyPolicy: ZeroRedundancy
      resources:
        requests:
          memory: "1Gi"
          cpu: "500m"
        limits:
          memory: "2Gi"
          cpu: "1"
  ingress:
    enabled: true
    annotations:
      nginx.ingress.kubernetes.io/ssl-redirect: "true"
    hosts:
    - jaeger.microservices.local
EOF

kubectl apply -f jaeger-instance.yaml
```

### 5.2 Prometheus & Grafana 監視

```yaml
# セキュリティメトリクス用ServiceMonitor
cat << 'EOF' > security-monitoring.yaml
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: istio-security-metrics
  namespace: microservices
spec:
  selector:
    matchLabels:
      app: istiod
  endpoints:
  - port: http-monitoring
    interval: 30s
    path: /stats/prometheus
---
# カスタムメトリクス用PrometheusRule
apiVersion: monitoring.coreos.com/v1
kind: PrometheusRule
metadata:
  name: microservices-security-rules
  namespace: microservices
spec:
  groups:
  - name: istio-security
    rules:
    # mTLS成功率
    - alert: LowMTLSSuccessRate
      expr: |
        (
          sum(rate(istio_requests_total{security_policy="mutual_tls"}[5m]))
          /
          sum(rate(istio_requests_total[5m]))
        ) < 0.95
      for: 2m
      labels:
        severity: warning
      annotations:
        summary: "Low mTLS success rate"
        description: "mTLS success rate is {{ $value | humanizePercentage }}"
    
    # 認証失敗アラート
    - alert: HighAuthenticationFailureRate
      expr: |
        sum(rate(istio_requests_total{response_code=~"401|403"}[5m]))
        /
        sum(rate(istio_requests_total[5m]))
        > 0.1
      for: 1m
      labels:
        severity: critical
      annotations:
        summary: "High authentication failure rate"
        description: "Authentication failure rate is {{ $value | humanizePercentage }}"
    
    # Rate Limiting アラート
    - alert: RateLimitTriggered
      expr: |
        sum(rate(istio_requests_total{response_code="429"}[5m])) > 10
      for: 30s
      labels:
        severity: warning
      annotations:
        summary: "Rate limiting triggered"
        description: "Rate limiting is being triggered frequently"
    
    # サービス間通信異常
    - alert: ServiceMeshConnectivityIssue
      expr: |
        sum(rate(istio_requests_total{response_code=~"5.."}[5m]))
        /
        sum(rate(istio_requests_total[5m]))
        > 0.05
      for: 2m
      labels:
        severity: critical
      annotations:
        summary: "Service mesh connectivity issues"
        description: "High error rate in service mesh communications"
EOF

kubectl apply -f security-monitoring.yaml
```

### 5.3 セキュリティ監査ダッシュボード

```yaml
# Grafana セキュリティダッシュボード ConfigMap
cat << 'EOF' > security-dashboard.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: istio-security-dashboard
  namespace: monitoring
data:
  dashboard.json: |
    {
      "dashboard": {
        "id": null,
        "title": "Istio Security Dashboard",
        "tags": ["istio", "security"],
        "timezone": "browser",
        "panels": [
          {
            "id": 1,
            "title": "mTLS Success Rate",
            "type": "stat",
            "targets": [
              {
                "expr": "sum(rate(istio_requests_total{security_policy=\"mutual_tls\"}[5m])) / sum(rate(istio_requests_total[5m]))",
                "format": "time_series",
                "legendFormat": "mTLS Success Rate"
              }
            ],
            "fieldConfig": {
              "defaults": {
                "unit": "percentunit",
                "min": 0,
                "max": 1
              }
            }
          },
          {
            "id": 2,
            "title": "Authentication Failures",
            "type": "graph",
            "targets": [
              {
                "expr": "sum(rate(istio_requests_total{response_code=~\"401|403\"}[5m])) by (source_app, destination_service_name)",
                "format": "time_series",
                "legendFormat": "{{source_app}} -> {{destination_service_name}}"
              }
            ]
          },
          {
            "id": 3,
            "title": "Rate Limiting Events",
            "type": "graph",
            "targets": [
              {
                "expr": "sum(rate(istio_requests_total{response_code=\"429\"}[5m])) by (destination_service_name)",
                "format": "time_series",
                "legendFormat": "{{destination_service_name}}"
              }
            ]
          },
          {
            "id": 4,
            "title": "Certificate Expiry",
            "type": "table",
            "targets": [
              {
                "expr": "pilot_k8s_cfg_events{type=\"Secret\"}",
                "format": "table"
              }
            ]
          }
        ],
        "time": {
          "from": "now-1h",
          "to": "now"
        },
        "refresh": "30s"
      }
    }
EOF

kubectl apply -f security-dashboard.yaml
```

## 🔍 Step 6: セキュリティテストと検証

### 6.1 セキュリティテストスクリプト

```bash
# マイクロサービスセキュリティテストスクリプト
cat << 'EOF' > microservices-security-test.sh
#!/bin/bash

echo "=== マイクロサービスセキュリティテスト ==="
echo "テスト実行日時: $(date)"
echo ""

# 1. mTLS検証
echo "1. mTLS 接続テスト:"
kubectl exec -n microservices -c istio-proxy \
  $(kubectl get pod -n microservices -l app=frontend -o jsonpath='{.items[0].metadata.name}') \
  -- openssl s_client -connect backend.microservices.svc.cluster.local:8080 -verify 8 < /dev/null 2>&1 | \
  grep -E "(Verify return code|issuer|subject)" | head -3

echo ""

# 2. 認証テスト
echo "2. JWT認証テスト:"
# 無効なJWTでのアクセステスト
curl -k -s -o /dev/null -w "%{http_code}" \
  -H "Authorization: Bearer invalid.jwt.token" \
  https://microservices.local/api/v1/test || echo "401 (認証失敗) - 期待通り"

echo ""

# 3. 認可テスト
echo "3. RBAC認可テスト:"
# Backend への直接アクセステスト（拒否されるべき）
kubectl exec -n microservices \
  $(kubectl get pod -n microservices -l app=database -o jsonpath='{.items[0].metadata.name}') \
  -- timeout 5 nc -zv backend.microservices.svc.cluster.local 8080 2>&1 | \
  grep -q "succeeded" && echo "✗ 予期しないアクセス許可" || echo "✓ 正常に拒否"

echo ""

# 4. Rate Limiting テスト
echo "4. Rate Limiting テスト:"
for i in {1..150}; do
  response=$(curl -k -s -o /dev/null -w "%{http_code}" https://microservices.local/)
  if [ "$response" = "429" ]; then
    echo "✓ Rate Limiting が $i 回目のリクエストで発動"
    break
  fi
done

echo ""

# 5. TLS設定確認
echo "5. TLS設定確認:"
echo "  Certificate validity:"
kubectl get secret microservices-tls -n istio-system -o jsonpath='{.data.tls\.crt}' | \
  base64 -d | openssl x509 -noout -dates 2>/dev/null | \
  sed 's/^/    /'

echo ""

# 6. ネットワークポリシー確認
echo "6. Network Policy 確認:"
POLICIES=$(kubectl get networkpolicies -n microservices --no-headers | wc -l)
echo "  適用されているNetwork Policy数: $POLICIES"

echo ""

# 7. Pod セキュリティ確認
echo "7. Pod セキュリティ設定確認:"
echo "  非root ユーザーで実行中のPod:"
kubectl get pods -n microservices -o json | \
  jq -r '.items[] | select(.spec.securityContext.runAsUser != 0 and .spec.securityContext.runAsUser != null) | .metadata.name' | \
  sed 's/^/    /'

echo ""

# 8. Istio設定検証
echo "8. Istio設定検証:"
echo "  PeerAuthentication ポリシー:"
kubectl get peerauthentication -n microservices --no-headers | awk '{print "    " $1 " (" $2 ")"}'

echo "  AuthorizationPolicy ポリシー:"
kubectl get authorizationpolicy -n microservices --no-headers | awk '{print "    " $1}'

echo ""

# 9. メトリクス確認
echo "9. セキュリティメトリクス確認:"
if command -v curl >/dev/null; then
  echo "  Istio Proxy メトリクス取得可能性:"
  kubectl exec -n microservices -c istio-proxy \
    $(kubectl get pod -n microservices -l app=frontend -o jsonpath='{.items[0].metadata.name}') \
    -- curl -s localhost:15000/stats | grep -c "ssl" | \
    awk '{print "    SSL メトリクス数: " $1}'
fi

echo ""
echo "=== セキュリティテスト完了 ==="
echo ""
echo "推奨事項:"
echo "  - 定期的な証明書更新"
echo "  - セキュリティメトリクスの継続監視"
echo "  - ペネトレーションテストの実施"
echo "  - セキュリティポリシーの定期見直し"
EOF

chmod +x microservices-security-test.sh
./microservices-security-test.sh
```

## 🧹 Step 7: クリーンアップ

```bash
# テスト用リソースの削除
kubectl delete namespace microservices --ignore-not-found
kubectl delete gateway microservices-gateway -n microservices --ignore-not-found
kubectl delete virtualservice microservices-routing -n microservices --ignore-not-found
kubectl delete envoyfilter rate-limit-filter security-headers -n istio-system --ignore-not-found
kubectl delete servicemonitor istio-security-metrics -n microservices --ignore-not-found
kubectl delete prometheusrule microservices-security-rules -n microservices --ignore-not-found

# Istio アンインストール（必要に応じて）
# istioctl uninstall --purge -y

echo "クリーンアップ完了"
```

## 💰 コスト計算

- **Istio**: 基本的なコンポーネントで追加メモリ使用量約500MB
- **Jaeger**: Elasticsearch使用で約2GB追加メモリ
- **監視コンポーネント**: 約1GB追加メモリ
- **総追加コスト**: 月額約$50-100（クラスターサイズにより変動）

## 📚 学習ポイント

### 重要な概念
1. **サービスメッシュセキュリティ**: Istioによる包括的な通信制御
2. **mTLS**: 暗号化された相互認証通信
3. **マイクロサービス認証**: JWT とサービス間認証の組み合わせ
4. **分散セキュリティ**: 複数サービス間のセキュリティ監視
5. **ゼロトラストネットワーク**: すべての通信を検証・暗号化

### 実践的なスキル
- Istio サービスメッシュのセキュリティ設定
- mTLS による暗号化通信の実装
- JWT認証とRBACの組み合わせ運用
- API ゲートウェイセキュリティの構築
- 分散トレーシングとセキュリティ監視

---

**次のステップ**: [Lab 5: サプライチェーンセキュリティ](./lab05-supply-chain-security.md) では、コンテナイメージとデプロイメントパイプラインのセキュリティを学習します。