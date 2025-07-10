# Lab 2: クラスター堅牢化

## 🎯 学習目標

このラボでは、Kubernetesクラスターのセキュリティ堅牢化を実装します：

- RBAC（Role-Based Access Control）の詳細設計
- Service Account のセキュリティ強化
- Pod Security Standards の実装
- Network Policy による通信制御
- etcd データ暗号化と保護

## 📋 前提条件

- Kubernetes クラスターが稼働中
- kubectl が設定済み
- [Lab 1: クラスターセキュリティ基盤](./lab01-cluster-security-foundation.md) の完了推奨

## 🏗️ アーキテクチャ概要

```
┌─────────────────────────────────────────────────────────────┐
│                   クラスター堅牢化環境                         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐     │
│  │    RBAC     │    │   Pod Sec   │    │   Network   │     │
│  │ Fine-grained│    │  Standards  │    │   Policies  │     │
│  │  Controls   │    │             │    │             │     │
│  └─────┬───────┘    └─────┬───────┘    └─────┬───────┘     │
│        │                  │                  │             │
│        ▼                  ▼                  ▼             │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │              API Server Security                       │ │
│  │         Authentication & Authorization                 │ │
│  └─────┬───────────────────────┬───────────────────────────┘ │
│        │                       │                             │
│        ▼                       ▼                             │
│  ┌─────────────┐         ┌─────────────┐                     │
│  │    etcd     │         │   kubelet   │                     │
│  │ Encryption  │         │  Security   │                     │
│  └─────────────┘         └─────────────┘                     │
└─────────────────────────────────────────────────────────────┘
```

## 🚀 Step 1: RBAC の詳細設計と実装

### 1.1 最小権限の原則に基づくRole設計

```yaml
# 開発者用 Role（読み取り専用）
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  namespace: development
  name: developer-read-only
rules:
- apiGroups: [""]
  resources: ["pods", "services", "configmaps", "secrets"]
  verbs: ["get", "list", "watch"]
- apiGroups: ["apps"]
  resources: ["deployments", "replicasets"]
  verbs: ["get", "list", "watch"]
- apiGroups: [""]
  resources: ["pods/log"]
  verbs: ["get", "list"]
---
# アプリケーション開発者用 Role（デプロイ権限付き）
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  namespace: development
  name: app-developer
rules:
- apiGroups: [""]
  resources: ["pods", "services", "configmaps"]
  verbs: ["get", "list", "watch", "create", "update", "patch", "delete"]
- apiGroups: ["apps"]
  resources: ["deployments", "replicasets"]
  verbs: ["get", "list", "watch", "create", "update", "patch", "delete"]
- apiGroups: [""]
  resources: ["secrets"]
  verbs: ["get", "list"]  # secrets は読み取りのみ
- apiGroups: [""]
  resources: ["pods/exec", "pods/portforward"]
  verbs: ["create"]
---
# SRE用 ClusterRole（クラスター管理権限）
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: sre-cluster-admin
rules:
- apiGroups: [""]
  resources: ["nodes", "persistentvolumes", "namespaces"]
  verbs: ["get", "list", "watch", "create", "update", "patch", "delete"]
- apiGroups: [""]
  resources: ["pods", "services", "configmaps", "secrets"]
  verbs: ["*"]
- apiGroups: ["apps", "extensions"]
  resources: ["*"]
  verbs: ["*"]
- apiGroups: ["rbac.authorization.k8s.io"]
  resources: ["roles", "rolebindings"]
  verbs: ["get", "list", "watch", "create", "update", "patch", "delete"]
- apiGroups: ["networking.k8s.io"]
  resources: ["networkpolicies"]
  verbs: ["*"]
```

### 1.2 Service Account とRoleBinding の設定

```bash
# 開発チーム用 Namespace 作成
kubectl create namespace development
kubectl create namespace staging
kubectl create namespace production

# Service Account 作成
kubectl create serviceaccount developer-sa -n development
kubectl create serviceaccount app-dev-sa -n development
kubectl create serviceaccount sre-sa -n production

# RoleBinding の作成
cat << EOF | kubectl apply -f -
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: developer-read-binding
  namespace: development
subjects:
- kind: ServiceAccount
  name: developer-sa
  namespace: development
- kind: User
  name: dev-team-readonly
  apiGroup: rbac.authorization.k8s.io
roleRef:
  kind: Role
  name: developer-read-only
  apiGroup: rbac.authorization.k8s.io
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: app-developer-binding
  namespace: development
subjects:
- kind: ServiceAccount
  name: app-dev-sa
  namespace: development
- kind: User
  name: senior-developer
  apiGroup: rbac.authorization.k8s.io
roleRef:
  kind: Role
  name: app-developer
  apiGroup: rbac.authorization.k8s.io
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: sre-cluster-binding
subjects:
- kind: ServiceAccount
  name: sre-sa
  namespace: production
- kind: User
  name: sre-team
  apiGroup: rbac.authorization.k8s.io
roleRef:
  kind: ClusterRole
  name: sre-cluster-admin
  apiGroup: rbac.authorization.k8s.io
EOF
```

### 1.3 RBAC 権限テストと検証

```bash
# 権限テストスクリプト作成
cat << 'EOF' > rbac-test.sh
#!/bin/bash

echo "=== RBAC Permission Testing ==="

# テスト用 kubeconfig 作成関数
create_test_kubeconfig() {
    local sa_name=$1
    local namespace=$2
    local context_name=$3
    
    # Service Account のトークン取得
    SECRET_NAME=$(kubectl get serviceaccount $sa_name -n $namespace -o jsonpath='{.secrets[0].name}')
    TOKEN=$(kubectl get secret $SECRET_NAME -n $namespace -o jsonpath='{.data.token}' | base64 -d)
    
    # kubeconfig 作成
    kubectl config set-cluster test-cluster --server=$(kubectl config view --minify -o jsonpath='{.clusters[0].cluster.server}') --insecure-skip-tls-verify=true
    kubectl config set-credentials $sa_name --token=$TOKEN
    kubectl config set-context $context_name --cluster=test-cluster --user=$sa_name --namespace=$namespace
}

# 権限テスト関数
test_permissions() {
    local context=$1
    local test_name=$2
    
    echo "Testing permissions for: $test_name"
    echo "Context: $context"
    
    # Pod 読み取りテスト
    echo -n "  Pod read access: "
    kubectl --context=$context get pods -n development >/dev/null 2>&1
    [ $? -eq 0 ] && echo "✓ ALLOWED" || echo "✗ DENIED"
    
    # Pod 作成テスト
    echo -n "  Pod create access: "
    kubectl --context=$context run test-pod --image=nginx --dry-run=client -n development >/dev/null 2>&1
    [ $? -eq 0 ] && echo "✓ ALLOWED" || echo "✗ DENIED"
    
    # Secret 読み取りテスト
    echo -n "  Secret read access: "
    kubectl --context=$context get secrets -n development >/dev/null 2>&1
    [ $? -eq 0 ] && echo "✓ ALLOWED" || echo "✗ DENIED"
    
    # Secret 作成テスト
    echo -n "  Secret create access: "
    kubectl --context=$context create secret generic test-secret --from-literal=key=value --dry-run=client -n development >/dev/null 2>&1
    [ $? -eq 0 ] && echo "✓ ALLOWED" || echo "✗ DENIED"
    
    # Cluster レベルリソースアクセステスト
    echo -n "  Node read access: "
    kubectl --context=$context get nodes >/dev/null 2>&1
    [ $? -eq 0 ] && echo "✓ ALLOWED" || echo "✗ DENIED"
    
    echo ""
}

# テスト実行
create_test_kubeconfig "developer-sa" "development" "dev-readonly-context"
create_test_kubeconfig "app-dev-sa" "development" "app-dev-context"
create_test_kubeconfig "sre-sa" "production" "sre-context"

test_permissions "dev-readonly-context" "Developer (Read-Only)"
test_permissions "app-dev-context" "App Developer"
test_permissions "sre-context" "SRE Team"

echo "=== RBAC Testing Complete ==="
EOF

chmod +x rbac-test.sh
./rbac-test.sh
```

## 🛡️ Step 2: Pod Security Standards の実装

### 2.1 Pod Security Standards 設定

```bash
# 各 Namespace に Pod Security Standards を適用
kubectl label namespace development \
  pod-security.kubernetes.io/enforce=restricted \
  pod-security.kubernetes.io/audit=restricted \
  pod-security.kubernetes.io/warn=restricted

kubectl label namespace staging \
  pod-security.kubernetes.io/enforce=baseline \
  pod-security.kubernetes.io/audit=restricted \
  pod-security.kubernetes.io/warn=restricted

kubectl label namespace production \
  pod-security.kubernetes.io/enforce=restricted \
  pod-security.kubernetes.io/audit=restricted \
  pod-security.kubernetes.io/warn=restricted

# デフォルト Namespace（テスト用）
kubectl label namespace default \
  pod-security.kubernetes.io/enforce=baseline \
  pod-security.kubernetes.io/audit=baseline \
  pod-security.kubernetes.io/warn=baseline
```

### 2.2 Pod Security Policy（Kubernetes 1.25未満）の実装

```yaml
# Pod Security Policy（レガシー参考用）
apiVersion: policy/v1beta1
kind: PodSecurityPolicy
metadata:
  name: restricted-psp
spec:
  privileged: false
  allowPrivilegeEscalation: false
  requiredDropCapabilities:
    - ALL
  volumes:
    - 'configMap'
    - 'emptyDir'
    - 'projected'
    - 'secret'
    - 'downwardAPI'
    - 'persistentVolumeClaim'
  runAsUser:
    rule: 'MustRunAsNonRoot'
  runAsGroup:
    rule: 'MustRunAs'
    ranges:
      - min: 1
        max: 65535
  seLinux:
    rule: 'RunAsAny'
  fsGroup:
    rule: 'RunAsAny'
  readOnlyRootFilesystem: true
  seccompProfile:
    type: 'RuntimeDefault'
---
# 制限的でないPSP
apiVersion: policy/v1beta1
kind: PodSecurityPolicy
metadata:
  name: baseline-psp
spec:
  privileged: false
  allowPrivilegeEscalation: false
  volumes:
    - 'configMap'
    - 'emptyDir'
    - 'projected'
    - 'secret'
    - 'downwardAPI'
    - 'persistentVolumeClaim'
    - 'hostPath'
  runAsUser:
    rule: 'RunAsAny'
  runAsGroup:
    rule: 'RunAsAny'
  seLinux:
    rule: 'RunAsAny'
  fsGroup:
    rule: 'RunAsAny'
```

### 2.3 セキュアなPodマニフェスト例

```yaml
# 制限的なセキュリティコンテキストを持つPod
apiVersion: v1
kind: Pod
metadata:
  name: secure-web-app
  namespace: production
  labels:
    app: secure-web
spec:
  securityContext:
    runAsNonRoot: true
    runAsUser: 1001
    runAsGroup: 1001
    fsGroup: 1001
    seccompProfile:
      type: RuntimeDefault
  containers:
  - name: web-server
    image: nginx:1.21-alpine
    securityContext:
      allowPrivilegeEscalation: false
      readOnlyRootFilesystem: true
      capabilities:
        drop:
        - ALL
      runAsNonRoot: true
      runAsUser: 1001
    resources:
      limits:
        memory: "128Mi"
        cpu: "100m"
      requests:
        memory: "64Mi"
        cpu: "50m"
    volumeMounts:
    - name: tmp-volume
      mountPath: /tmp
    - name: cache-volume
      mountPath: /var/cache/nginx
    - name: run-volume
      mountPath: /var/run
  volumes:
  - name: tmp-volume
    emptyDir: {}
  - name: cache-volume
    emptyDir: {}
  - name: run-volume
    emptyDir: {}
---
# 違反するPodマニフェスト（テスト用）
apiVersion: v1
kind: Pod
metadata:
  name: insecure-pod-test
  namespace: development
spec:
  containers:
  - name: bad-container
    image: nginx
    securityContext:
      privileged: true  # これは拒否される
      runAsUser: 0      # rootユーザー（restricted で拒否）
```

## 🌐 Step 3: Network Policy による通信制御

### 3.1 基本的なNetwork Policy

```yaml
# デフォルト拒否ポリシー
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: default-deny-all
  namespace: production
spec:
  podSelector: {}
  policyTypes:
  - Ingress
  - Egress
---
# Web Tier Network Policy
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: web-tier-policy
  namespace: production
spec:
  podSelector:
    matchLabels:
      tier: web
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          name: ingress-nginx
    - podSelector:
        matchLabels:
          app: load-balancer
    ports:
    - protocol: TCP
      port: 8080
  egress:
  - to:
    - podSelector:
        matchLabels:
          tier: app
    ports:
    - protocol: TCP
      port: 8080
  - to:
    - namespaceSelector:
        matchLabels:
          name: kube-system
    - podSelector:
        matchLabels:
          k8s-app: kube-dns
    ports:
    - protocol: UDP
      port: 53
---
# Application Tier Network Policy
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: app-tier-policy
  namespace: production
spec:
  podSelector:
    matchLabels:
      tier: app
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - podSelector:
        matchLabels:
          tier: web
    ports:
    - protocol: TCP
      port: 8080
  egress:
  - to:
    - podSelector:
        matchLabels:
          tier: database
    ports:
    - protocol: TCP
      port: 5432
  - to:
    - namespaceSelector:
        matchLabels:
          name: kube-system
    - podSelector:
        matchLabels:
          k8s-app: kube-dns
    ports:
    - protocol: UDP
      port: 53
---
# Database Tier Network Policy
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: database-tier-policy
  namespace: production
spec:
  podSelector:
    matchLabels:
      tier: database
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - podSelector:
        matchLabels:
          tier: app
    ports:
    - protocol: TCP
      port: 5432
  egress:
  - to:
    - namespaceSelector:
        matchLabels:
          name: kube-system
    - podSelector:
        matchLabels:
          k8s-app: kube-dns
    ports:
    - protocol: UDP
      port: 53
```

### 3.2 高度なNetwork Policy

```yaml
# 名前空間間通信制御
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: cross-namespace-policy
  namespace: production
spec:
  podSelector:
    matchLabels:
      app: api-gateway
  policyTypes:
  - Ingress
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          environment: staging
    - podSelector:
        matchLabels:
          app: test-client
    ports:
    - protocol: TCP
      port: 443
---
# 外部通信制御
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: external-access-policy
  namespace: production
spec:
  podSelector:
    matchLabels:
      app: external-api-client
  policyTypes:
  - Egress
  egress:
  - to: []  # すべての外部IP
    ports:
    - protocol: TCP
      port: 443
  - to:
    - ipBlock:
        cidr: 10.0.0.0/8
        except:
        - 10.0.1.0/24  # 特定のサブネットを除外
    ports:
    - protocol: TCP
      port: 80
```

### 3.3 Network Policy テストスクリプト

```bash
# Network Policy テストスクリプト
cat << 'EOF' > test-network-policies.sh
#!/bin/bash

echo "=== Network Policy Testing ==="

# テスト用Podを作成
create_test_pods() {
    echo "Creating test pods..."
    
    # Web tier pod
    kubectl run web-pod --image=nginx --labels="tier=web" -n production --restart=Never
    
    # App tier pod
    kubectl run app-pod --image=nginx --labels="tier=app" -n production --restart=Never
    
    # Database tier pod
    kubectl run db-pod --image=nginx --labels="tier=database" -n production --restart=Never
    
    # 別namespace のテストpod
    kubectl run external-pod --image=nginx -n development --restart=Never
    
    echo "Waiting for pods to be ready..."
    kubectl wait --for=condition=ready pod --all -n production --timeout=60s
    kubectl wait --for=condition=ready pod --all -n development --timeout=60s
}

# 接続テスト
test_connectivity() {
    echo "Testing connectivity between pods..."
    
    # Get pod IPs
    WEB_IP=$(kubectl get pod web-pod -n production -o jsonpath='{.status.podIP}')
    APP_IP=$(kubectl get pod app-pod -n production -o jsonpath='{.status.podIP}')
    DB_IP=$(kubectl get pod db-pod -n production -o jsonpath='{.status.podIP}')
    
    echo "Pod IPs:"
    echo "  Web: $WEB_IP"
    echo "  App: $APP_IP"
    echo "  Database: $DB_IP"
    echo ""
    
    # Web to App テスト（許可されるべき）
    echo "Testing Web -> App connectivity:"
    kubectl exec web-pod -n production -- timeout 5 nc -zv $APP_IP 80 2>&1 | grep -q "succeeded"
    [ $? -eq 0 ] && echo "  ✓ ALLOWED" || echo "  ✗ DENIED"
    
    # App to Database テスト（許可されるべき）
    echo "Testing App -> Database connectivity:"
    kubectl exec app-pod -n production -- timeout 5 nc -zv $DB_IP 80 2>&1 | grep -q "succeeded"
    [ $? -eq 0 ] && echo "  ✓ ALLOWED" || echo "  ✗ DENIED"
    
    # Web to Database テスト（拒否されるべき）
    echo "Testing Web -> Database connectivity (should be denied):"
    kubectl exec web-pod -n production -- timeout 5 nc -zv $DB_IP 80 2>&1 | grep -q "succeeded"
    [ $? -eq 0 ] && echo "  ✗ UNEXPECTEDLY ALLOWED" || echo "  ✓ CORRECTLY DENIED"
    
    # 外部からのアクセステスト
    echo "Testing External -> App connectivity (should be denied):"
    kubectl exec external-pod -n development -- timeout 5 nc -zv $APP_IP 80 2>&1 | grep -q "succeeded"
    [ $? -eq 0 ] && echo "  ✗ UNEXPECTEDLY ALLOWED" || echo "  ✓ CORRECTLY DENIED"
}

# クリーンアップ
cleanup() {
    echo "Cleaning up test pods..."
    kubectl delete pod web-pod app-pod db-pod -n production --ignore-not-found
    kubectl delete pod external-pod -n development --ignore-not-found
}

# メイン実行
create_test_pods
test_connectivity
cleanup

echo "=== Network Policy Testing Complete ==="
EOF

chmod +x test-network-policies.sh
```

## 🔐 Step 4: etcd データ暗号化

### 4.1 etcd 暗号化設定

```bash
# 暗号化キー生成
head -c 32 /dev/urandom | base64 > encryption-key.txt

# 暗号化設定ファイル作成
cat << EOF > /etc/kubernetes/encryption-config.yaml
apiVersion: apiserver.config.k8s.io/v1
kind: EncryptionConfiguration
resources:
- resources:
  - secrets
  - configmaps
  providers:
  - aescbc:
      keys:
      - name: key1
        secret: $(cat encryption-key.txt)
  - identity: {}
EOF

# API Server の設定更新（/etc/kubernetes/manifests/kube-apiserver.yaml）
# 以下の行を追加:
# --encryption-provider-config=/etc/kubernetes/encryption-config.yaml

# API Server再起動後、既存データの再暗号化
kubectl get secrets --all-namespaces -o json | kubectl replace -f -
kubectl get configmaps --all-namespaces -o json | kubectl replace -f -
```

### 4.2 etcd バックアップとリストア

```bash
# etcd バックアップスクリプト
cat << 'EOF' > etcd-backup.sh
#!/bin/bash

BACKUP_DIR="/var/backups/etcd"
DATE=$(date +%Y%m%d-%H%M%S)
BACKUP_FILE="$BACKUP_DIR/etcd-backup-$DATE.db"

# バックアップディレクトリ作成
mkdir -p $BACKUP_DIR

# etcd バックアップ実行
ETCDCTL_API=3 etcdctl snapshot save $BACKUP_FILE \
    --endpoints=https://127.0.0.1:2379 \
    --cacert=/etc/kubernetes/pki/etcd/ca.crt \
    --cert=/etc/kubernetes/pki/etcd/server.crt \
    --key=/etc/kubernetes/pki/etcd/server.key

# バックアップ検証
ETCDCTL_API=3 etcdctl snapshot status $BACKUP_FILE

echo "Backup completed: $BACKUP_FILE"

# 古いバックアップを削除（7日以上前）
find $BACKUP_DIR -name "etcd-backup-*.db" -mtime +7 -delete

echo "Backup retention applied"
EOF

chmod +x etcd-backup.sh

# cron で定期バックアップ設定
echo "0 2 * * * /path/to/etcd-backup.sh" | crontab -
```

## 🔒 Step 5: Service Account セキュリティ強化

### 5.1 Service Account Token の管理

```yaml
# 短期間トークンを使用するService Account
apiVersion: v1
kind: ServiceAccount
metadata:
  name: short-lived-sa
  namespace: production
automountServiceAccountToken: false
---
# TokenRequest を使用した一時的トークン取得
apiVersion: v1
kind: Secret
metadata:
  name: short-lived-token
  namespace: production
  annotations:
    kubernetes.io/service-account.name: short-lived-sa
type: kubernetes.io/service-account-token
---
# Projected Token を使用するPod
apiVersion: v1
kind: Pod
metadata:
  name: secure-app-with-token
  namespace: production
spec:
  serviceAccountName: short-lived-sa
  containers:
  - name: app
    image: nginx
    volumeMounts:
    - name: token
      mountPath: /var/run/secrets/tokens
      readOnly: true
  volumes:
  - name: token
    projected:
      sources:
      - serviceAccountToken:
          path: token
          expirationSeconds: 3600  # 1時間で期限切れ
          audience: api
```

### 5.2 Service Account の権限最小化

```bash
# デフォルトService Account の無効化
kubectl patch serviceaccount default -p '{"automountServiceAccountToken": false}' -n production
kubectl patch serviceaccount default -p '{"automountServiceAccountToken": false}' -n development
kubectl patch serviceaccount default -p '{"automountServiceAccountToken": false}' -n staging

# 専用Service Account作成と権限設定
cat << EOF | kubectl apply -f -
apiVersion: v1
kind: ServiceAccount
metadata:
  name: monitoring-sa
  namespace: production
automountServiceAccountToken: false
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: monitoring-cluster-role
rules:
- apiGroups: [""]
  resources: ["nodes", "pods", "services", "endpoints"]
  verbs: ["get", "list", "watch"]
- apiGroups: ["apps"]
  resources: ["deployments", "daemonsets", "replicasets"]
  verbs: ["get", "list", "watch"]
- apiGroups: ["metrics.k8s.io"]
  resources: ["nodes", "pods"]
  verbs: ["get", "list"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: monitoring-cluster-binding
subjects:
- kind: ServiceAccount
  name: monitoring-sa
  namespace: production
roleRef:
  kind: ClusterRole
  name: monitoring-cluster-role
  apiGroup: rbac.authorization.k8s.io
EOF
```

## 📊 Step 6: セキュリティ監査とコンプライアンス

### 6.1 自動セキュリティ監査スクリプト

```bash
# セキュリティ監査スクリプト
cat << 'EOF' > security-audit.sh
#!/bin/bash

echo "=== Kubernetes Security Audit ==="
echo "Audit Date: $(date)"
echo ""

# 1. RBAC 設定確認
echo "1. RBAC Configuration Audit:"
echo "  Cluster Roles with dangerous permissions:"
kubectl get clusterroles -o json | jq -r '.items[] | select(.rules[]?.verbs[]? == "*" or .rules[]?.resources[]? == "*") | .metadata.name'

echo ""
echo "  Service Accounts with cluster-admin:"
kubectl get clusterrolebindings -o json | jq -r '.items[] | select(.roleRef.name == "cluster-admin") | "ClusterRoleBinding: " + .metadata.name + " -> Subjects: " + (.subjects[]?.name // "N/A")'

echo ""

# 2. Pod Security 確認
echo "2. Pod Security Audit:"
echo "  Pods running as root:"
kubectl get pods --all-namespaces -o json | jq -r '.items[] | select(.spec.securityContext.runAsUser == 0 or .spec.containers[]?.securityContext.runAsUser == 0) | .metadata.namespace + "/" + .metadata.name'

echo ""
echo "  Pods with privileged containers:"
kubectl get pods --all-namespaces -o json | jq -r '.items[] | select(.spec.containers[]?.securityContext.privileged == true) | .metadata.namespace + "/" + .metadata.name'

echo ""
echo "  Pods without resource limits:"
kubectl get pods --all-namespaces -o json | jq -r '.items[] | select(.spec.containers[]? | has("resources") | not) | .metadata.namespace + "/" + .metadata.name'

echo ""

# 3. Network Policy 確認
echo "3. Network Policy Audit:"
echo "  Namespaces without network policies:"
for ns in $(kubectl get namespaces -o jsonpath='{.items[*].metadata.name}'); do
    policy_count=$(kubectl get networkpolicies -n $ns --no-headers 2>/dev/null | wc -l)
    if [ $policy_count -eq 0 ]; then
        echo "    $ns"
    fi
done

echo ""

# 4. Secret 管理確認
echo "4. Secret Management Audit:"
echo "  Secrets in default service accounts:"
kubectl get serviceaccounts --all-namespaces -o json | jq -r '.items[] | select(.metadata.name == "default" and (.secrets | length > 0)) | .metadata.namespace + "/default"'

echo ""

# 5. Node セキュリティ確認
echo "5. Node Security Audit:"
echo "  Node versions:"
kubectl get nodes -o json | jq -r '.items[] | .metadata.name + ": " + .status.nodeInfo.kubeletVersion'

echo ""

# 6. etcd 暗号化確認
echo "6. etcd Encryption Audit:"
if kubectl get --raw /api/v1/namespaces/kube-system/secrets | grep -q "encryption.configuration"; then
    echo "  ✓ etcd encryption appears to be configured"
else
    echo "  ✗ etcd encryption not detected"
fi

echo ""

# 7. 推奨事項
echo "=== Security Recommendations ==="
echo "  - Review all cluster-admin bindings"
echo "  - Ensure all pods run with non-root users"
echo "  - Implement network policies for all namespaces"
echo "  - Use Pod Security Standards"
echo "  - Regular security scanning of container images"
echo "  - Enable audit logging"
echo "  - Implement secret management solutions"

echo ""
echo "=== Audit Complete ==="
EOF

chmod +x security-audit.sh
./security-audit.sh
```

### 6.2 継続的コンプライアンス監視

```yaml
# CronJob で定期的なセキュリティスキャン
apiVersion: batch/v1
kind: CronJob
metadata:
  name: security-compliance-scan
  namespace: kube-system
spec:
  schedule: "0 2 * * *"  # 毎日午前2時
  jobTemplate:
    spec:
      template:
        spec:
          serviceAccountName: security-scanner-sa
          containers:
          - name: scanner
            image: aquasec/kube-bench:latest
            command:
            - kube-bench
            - --config-dir=/opt/kube-bench/cfg/
            - --config=rh-0.7
            volumeMounts:
            - name: var-lib-etcd
              mountPath: /var/lib/etcd
              readOnly: true
            - name: etc-kubernetes
              mountPath: /etc/kubernetes
              readOnly: true
          volumes:
          - name: var-lib-etcd
            hostPath:
              path: "/var/lib/etcd"
          - name: etc-kubernetes
            hostPath:
              path: "/etc/kubernetes"
          restartPolicy: OnFailure
          hostPID: true
          hostIPC: true
```

## 🧹 Step 7: クリーンアップ

```bash
# テスト用リソースの削除
kubectl delete pods --all -n development
kubectl delete networkpolicy --all -n production
kubectl delete rolebinding developer-read-binding app-developer-binding -n development
kubectl delete clusterrolebinding sre-cluster-binding
kubectl delete role developer-read-only app-developer -n development
kubectl delete clusterrole sre-cluster-admin
kubectl delete serviceaccount developer-sa app-dev-sa -n development
kubectl delete serviceaccount sre-sa -n production

echo "クリーンアップ完了"
```

## 💰 コスト計算

このラボは既存のKubernetesクラスター内での設定変更が中心のため、追加コストは発生しません。

## 📚 学習ポイント

### 重要な概念
1. **RBAC**: 最小権限の原則に基づく詳細な権限設計
2. **Pod Security**: Pod Security Standards による統一的なセキュリティ
3. **Network Policy**: ゼロトラストネットワークの実現
4. **暗号化**: etcd データの保護
5. **監査**: 継続的なセキュリティ監視

### 実践的なスキル
- RBAC の詳細設計と実装
- Pod Security Standards の適用
- Network Policy による通信制御
- Service Account のセキュア運用
- セキュリティ監査の自動化

---

**次のステップ**: [Lab 3: システム堅牢化](./lab03-system-hardening.md) では、ホストレベルのセキュリティ強化を学習します。