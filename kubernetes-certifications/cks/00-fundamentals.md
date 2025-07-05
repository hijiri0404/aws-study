# CKS - Certified Kubernetes Security Specialist 基礎概念と試験戦略

## 🎯 試験概要

**Certified Kubernetes Security Specialist (CKS)**は、Kubernetesクラスターとアプリケーションのセキュリティ専門能力を評価する上級実技試験です。CKA認定取得が前提条件となる最高難易度の認定です。

### 📊 試験詳細
- **試験時間**: 2時間
- **問題数**: 15-20問の実技タスク
- **合格点**: 67%
- **費用**: $395 USD
- **有効期間**: 3年間
- **前提条件**: **CKA認定取得必須**
- **再受験**: 1回無料

### 🎯 対象者
- **セキュリティエンジニア**: Kubernetesセキュリティ専門家
- **プラットフォームエンジニア**: セキュアなK8s基盤構築者  
- **DevSecOpsエンジニア**: セキュリティ統合CI/CD担当者
- **クラウドアーキテクト**: エンタープライズK8s設計者

## 📋 試験ドメインと配点

### Domain 1: Cluster Setup (10%)
**クラスターセキュリティ設定**

**重要なトピック:**
- **CIS Benchmark**: Kubernetesセキュリティベンチマーク適用
- **Ingress TLS**: SSL/TLS証明書管理
- **Network Security**: ネットワーク分離・暗号化
- **GUI Access**: Dashboardのセキュア設定

**実装例:**
```yaml
# Secure Ingress with TLS
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: secure-ingress
  annotations:
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
    nginx.ingress.kubernetes.io/force-ssl-redirect: "true"
spec:
  tls:
  - hosts:
    - secure.example.com
    secretName: secure-tls
  rules:
  - host: secure.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: secure-app
            port:
              number: 443
```

### Domain 2: Cluster Hardening (15%)
**クラスターハードニング**

**重要なトピック:**
- **RBAC**: Role-Based Access Control強化
- **ServiceAccounts**: サービスアカウントセキュリティ
- **API Server**: APIサーバーセキュリティ設定
- **kubelet**: ノードエージェントセキュリティ

**セキュリティ強化例:**
```yaml
# Least Privilege RBAC
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  namespace: production
  name: pod-reader
rules:
- apiGroups: [""]
  resources: ["pods"]
  verbs: ["get", "list"]
  resourceNames: [] # 必要に応じて特定リソースのみ許可
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: read-pods
  namespace: production
subjects:
- kind: User
  name: developer
  apiGroup: rbac.authorization.k8s.io
roleRef:
  kind: Role
  name: pod-reader
  apiGroup: rbac.authorization.k8s.io
```

### Domain 3: System Hardening (15%)
**システムハードニング**

**重要なトピック:**
- **Host Security**: ノードOSセキュリティ設定
- **Container Runtime**: コンテナランタイムセキュリティ
- **Kernel Hardening**: カーネルレベルセキュリティ
- **SSH Hardening**: SSH接続セキュリティ

**システム設定例:**
```bash
# AppArmor Profile Example
cat <<EOF > /etc/apparmor.d/k8s-nginx
#include <tunables/global>

profile k8s-nginx flags=(attach_disconnected,mediate_deleted) {
  #include <abstractions/base>
  
  # Allow network access
  network inet tcp,
  network inet udp,
  
  # Allow file access
  /usr/sbin/nginx mr,
  /var/log/nginx/* w,
  /var/www/html/** r,
  
  # Deny sensitive paths
  deny /proc/sys/** rw,
  deny /sys/** rw,
  deny /etc/shadow r,
}
EOF

# Load AppArmor profile
apparmor_parser -r -W /etc/apparmor.d/k8s-nginx
```

### Domain 4: Minimize Microservice Vulnerabilities (20%)
**マイクロサービス脆弱性の最小化**

**重要なトピック:**
- **SecurityContexts**: コンテナセキュリティ設定
- **Pod Security Standards**: セキュリティポリシー
- **Admission Controllers**: 許可制御
- **OPA Gatekeeper**: ポリシー管理

**セキュアコンテナ例:**
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: secure-pod
spec:
  securityContext:
    runAsNonRoot: true
    runAsUser: 1000
    runAsGroup: 1000
    fsGroup: 1000
    seccompProfile:
      type: RuntimeDefault
  containers:
  - name: secure-container
    image: nginx:1.20
    securityContext:
      allowPrivilegeEscalation: false
      readOnlyRootFilesystem: true
      capabilities:
        drop:
        - ALL
        add:
        - NET_BIND_SERVICE
    resources:
      limits:
        memory: "256Mi"
        cpu: "200m"
      requests:
        memory: "128Mi"
        cpu: "100m"
    volumeMounts:
    - name: tmp-volume
      mountPath: /tmp
    - name: var-cache
      mountPath: /var/cache/nginx
  volumes:
  - name: tmp-volume
    emptyDir: {}
  - name: var-cache
    emptyDir: {}
```

### Domain 5: Supply Chain Security (20%)
**サプライチェーンセキュリティ**

**重要なトピック:**
- **Image Scanning**: コンテナイメージ脆弱性検査
- **Image Signing**: イメージ署名・検証
- **Admission Controllers**: イメージポリシー制御
- **Private Registries**: プライベートレジストリ管理

**イメージセキュリティ例:**
```yaml
# Image Policy Webhook Configuration
apiVersion: v1
kind: ConfigMap
metadata:
  name: image-policy-webhook
  namespace: kube-system
data:
  policy.yaml: |
    imagePolicy:
      kubeConfigFile: /etc/kubernetes/webhook-config.yaml
      allowTTL: 50
      denyTTL: 50
      retryBackoff: 500
      defaultAllow: false
---
# Only allow images from trusted registries
apiVersion: admissionregistration.k8s.io/v1
kind: ValidatingAdmissionWebhook
metadata:
  name: image-policy
webhooks:
- name: image-policy.example.com
  clientConfig:
    service:
      name: image-policy-webhook
      namespace: default
      path: /image-policy
  rules:
  - operations: ["CREATE", "UPDATE"]
    apiGroups: [""]
    apiVersions: ["v1"]
    resources: ["pods"]
```

### Domain 6: Monitoring, Logging and Runtime Security (20%)
**監視・ログ・ランタイムセキュリティ**

**重要なトピック:**
- **Falco**: ランタイム脅威検知
- **Audit Logs**: APIサーバー監査ログ
- **SIEM Integration**: セキュリティ情報統合
- **Incident Response**: インシデント対応

**Falco設定例:**
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: falco-config
data:
  falco.yaml: |
    rules_file:
      - /etc/falco/falco_rules.yaml
      - /etc/falco/k8s_audit_rules.yaml
    
    # Output channels
    syslog_output:
      enabled: true
    
    file_output:
      enabled: true
      keep_alive: false
      filename: /var/log/falco/events.txt
    
    stdout_output:
      enabled: true
    
    # Syscall event drops
    syscall_event_drops:
      threshold: 0.1
      actions:
        - log
        - alert
---
# Custom Falco Rules
apiVersion: v1
kind: ConfigMap
metadata:
  name: falco-rules
data:
  custom_rules.yaml: |
    - rule: Suspicious Pod Creation
      desc: Detect creation of pods with suspicious characteristics
      condition: >
        k8s_audit and
        ka.target.verb=create and
        ka.target.resource=pods and
        (ka.req.pod.containers.image contains "latest" or
         ka.req.pod.spec.securityContext.privileged=true)
      output: >
        Suspicious pod created (user=%ka.user.name verb=%ka.target.verb 
        pod=%ka.target.name image=%ka.req.pod.containers.image)
      priority: WARNING
```

## 🛡️ セキュリティ学習の重要概念

### 1. ゼロトラストアーキテクチャ

**基本原則:**
```
"Trust Nothing, Verify Everything"
├── Identity Verification（認証）
├── Device Compliance（デバイス準拠）
├── Network Segmentation（ネットワーク分離）
├── Data Encryption（データ暗号化）
└── Continuous Monitoring（継続監視）
```

**Kubernetes実装:**
- mTLS による暗号化通信
- NetworkPolicy による微細な通信制御
- Pod Security Standards による強制
- RBAC による最小権限の原則

### 2. 多層防御（Defense in Depth）

```
Application Layer:
├── Secure Coding Practices
├── Input Validation
├── Output Encoding
└── Authentication/Authorization

Container Layer:
├── Image Scanning
├── Runtime Security
├── Resource Limits
└── Security Contexts

Orchestration Layer:
├── RBAC
├── Network Policies
├── Pod Security Standards
└── Admission Controllers

Infrastructure Layer:
├── Node Hardening
├── Network Segmentation
├── Encryption at Rest
└── Audit Logging
```

### 3. DevSecOps統合

**Shift-Left Security:**
```
Development → Testing → Deployment → Operations
     ↓           ↓          ↓           ↓
Static Code → Dynamic  → Image    → Runtime
Analysis     Testing    Scanning   Monitoring
```

## 🛠️ 学習環境セットアップ

### セキュリティ特化学習環境

#### 1. 脆弱なクラスター構築（学習用）
```bash
# Insecure cluster for practice
kind create cluster --config - <<EOF
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
nodes:
- role: control-plane
  kubeadmConfigPatches:
  - |
    kind: ClusterConfiguration
    apiServer:
      extraArgs:
        # Insecure settings for learning
        insecure-port: "8080"
        insecure-bind-address: "0.0.0.0"
        anonymous-auth: "true"
- role: worker
- role: worker
EOF

# Deploy vulnerable applications
kubectl apply -f https://raw.githubusercontent.com/OWASP/WebGoat/main/webgoat-server/k8s/webgoat-deployment.yaml
```

#### 2. セキュリティツールインストール
```bash
# Falco installation
helm repo add falcosecurity https://falcosecurity.github.io/charts
helm repo update
helm install falco falcosecurity/falco \
  --set tty=true \
  --set falco.grpc.enabled=true \
  --set falco.grpcOutput.enabled=true

# Trivy for image scanning
curl -sfL https://raw.githubusercontent.com/aquasecurity/trivy/main/contrib/install.sh | sh -s -- -b /usr/local/bin

# OPA Gatekeeper
kubectl apply -f https://raw.githubusercontent.com/open-policy-agent/gatekeeper/release-3.14/deploy/gatekeeper.yaml

# kube-score for security analysis
curl -L https://github.com/zegl/kube-score/releases/latest/download/kube-score_linux_amd64 -o kube-score
chmod +x kube-score
sudo mv kube-score /usr/local/bin/
```

### 必須セキュリティツール

```bash
# Security scanning tools
alias trivy-scan='trivy image --severity HIGH,CRITICAL'
alias kube-scan='kube-score score'
alias falco-logs='kubectl logs -n falco -l app=falco'

# Security analysis commands
alias security-check='kubectl get pods --all-namespaces -o jsonpath="{range .items[*]}{.metadata.name}{'\t'}{.spec.securityContext}{'\n'}{end}"'
alias privileged-pods='kubectl get pods --all-namespaces -o jsonpath="{.items[?(@.spec.securityContext.privileged==true)].metadata.name}"'
alias root-pods='kubectl get pods --all-namespaces -o jsonpath="{.items[?(@.spec.securityContext.runAsUser==0)].metadata.name}"'
```

## 📚 学習リソースと順序

### 上級者向け学習パス（16-20週間）

#### Phase 1: セキュリティ基礎固め（4-5週間）
1. **Kubernetes Security Fundamentals**
   - セキュリティアーキテクチャ理解
   - 脅威モデリング手法
   - セキュリティベストプラクティス

2. **Network Security Deep Dive**
   - CNI セキュリティ
   - Service Mesh セキュリティ
   - 暗号化通信実装

#### Phase 2: アクセス制御・認証（4-5週間）
1. **RBAC Advanced**
   - 複雑な権限設計
   - カスタムリソース対応
   - 外部認証統合

2. **Admission Control**
   - ValidatingWebhook開発
   - MutatingWebhook実装
   - OPA Gatekeeper運用

#### Phase 3: ランタイムセキュリティ（4-5週間）
1. **Container Security**
   - AppArmor/SELinux設定
   - seccomp プロファイル
   - Capabilities管理

2. **Runtime Monitoring**
   - Falco ルール作成
   - 異常検知設定
   - インシデント対応

#### Phase 4: 企業レベルセキュリティ（3-4週間）
1. **Supply Chain Security**
   - イメージ署名・検証
   - SBOM（Software Bill of Materials）
   - 脆弱性管理プロセス

2. **Compliance & Audit**
   - CIS Benchmark適用
   - 監査ログ分析
   - コンプライアンス自動化

#### Phase 5: 試験対策（1-2週間）
1. **実技演習**
   - 本教材のラボ実践
   - セキュリティシナリオ演習
   - 時間制限での問題解決

## 💰 学習コスト管理

### セキュリティ特化環境コスト
```
AWS EKS + Security Tools:
- EKS クラスター: $0.10/時間
- ワーカーノード: $0.10/時間 × 3
- セキュリティツール: $0.05/時間
- 合計: 約$0.45/時間 = $11/日

Google GKE + Istio:
- GKE クラスター: 無料
- ワーカーノード: $0.12/時間 × 3
- Istio サービスメッシュ: 無料
- 合計: 約$8.6/日

ローカル環境（推奨）:
- kind/minikube: 無料
- セキュリティツール: 無料
- 制約: 機能制限あり
```

### 学習効率の最大化
1. **ローカル中心**: 基礎学習は kind/minikube
2. **クラウド応用**: 高度機能はマネージドサービス
3. **短期集中**: セキュリティツール検証は集約実行
4. **自動化**: スクリプト化によるセットアップ効率化

## 🎯 CKS特有の学習ポイント

### 1. セキュリティマインドセット

**攻撃者視点の思考:**
```
How would an attacker exploit this?
├── Privilege Escalation
├── Data Exfiltration  
├── Lateral Movement
├── Persistence
└── Impact Maximization
```

**防御者の対応:**
```
How do we prevent, detect, and respond?
├── Prevention: Security Controls
├── Detection: Monitoring & Alerting
├── Response: Incident Handling
└── Recovery: Business Continuity
```

### 2. 実践的なセキュリティ実装

**セキュリティ設定の系統的アプローチ:**
```yaml
# Security Layering Example
apiVersion: v1
kind: Pod
metadata:
  name: secure-production-pod
  annotations:
    container.apparmor.security.beta.kubernetes.io/secure-app: localhost/k8s-nginx
spec:
  # Pod-level security
  securityContext:
    runAsNonRoot: true
    runAsUser: 1000
    runAsGroup: 1000
    fsGroup: 1000
    seccompProfile:
      type: Localhost
      localhostProfile: profiles/secure.json
  
  containers:
  - name: secure-app
    image: registry.company.com/secure-nginx:1.20-hardened
    # Container-level security
    securityContext:
      allowPrivilegeEscalation: false
      readOnlyRootFilesystem: true
      capabilities:
        drop: ["ALL"]
        add: ["NET_BIND_SERVICE"]
    
    # Resource constraints
    resources:
      limits:
        memory: "128Mi"
        cpu: "100m"
      requests:
        memory: "64Mi"
        cpu: "50m"
    
    # Health checks
    livenessProbe:
      httpGet:
        path: /health
        port: 8080
        scheme: HTTPS
      initialDelaySeconds: 30
      periodSeconds: 10
    
    # Environment restrictions
    env:
    - name: ENVIRONMENT
      value: "production"
    
    volumeMounts:
    - name: tmp-volume
      mountPath: /tmp
    - name: tls-certs
      mountPath: /etc/tls
      readOnly: true
  
  volumes:
  - name: tmp-volume
    emptyDir:
      sizeLimit: "100Mi"
  - name: tls-certs
    secret:
      secretName: app-tls-certs
      defaultMode: 0400
  
  # Network policy enforcement
  serviceAccountName: secure-app-sa
  automountServiceAccountToken: false
```

### 3. セキュリティ運用の自動化

**CI/CDパイプラインセキュリティ:**
```bash
#!/bin/bash
# secure-deployment-pipeline.sh

echo "🔒 セキュアデプロイメントパイプライン開始..."

# 1. Image security scanning
echo "📊 イメージセキュリティスキャン..."
trivy image --severity HIGH,CRITICAL --exit-code 1 ${IMAGE_NAME}

# 2. Kubernetes manifest security analysis
echo "📋 マニフェストセキュリティ分析..."
kube-score score deployment.yaml --ignore-test pod-networkpolicy

# 3. Policy validation
echo "🛡️ ポリシー検証..."
conftest verify --policy security-policies/ deployment.yaml

# 4. Admission controller simulation
echo "🚪 アドミッションコントローラーシミュレーション..."
kubectl apply --dry-run=server -f deployment.yaml

# 5. Runtime security check
echo "⚡ ランタイムセキュリティチェック..."
kubectl apply -f deployment.yaml
sleep 30
falco_alerts=$(kubectl logs -n falco -l app=falco --since=30s | grep CRITICAL | wc -l)
if [ $falco_alerts -gt 0 ]; then
    echo "❌ セキュリティアラート検出: $falco_alerts"
    exit 1
fi

echo "✅ セキュアデプロイメント完了!"
```

## 📊 スキルチェックリスト

### 基本レベル（CKA取得者想定）
- [ ] Kubernetes基本セキュリティ理解
- [ ] RBAC基本設定
- [ ] Network Policy基本実装
- [ ] セキュリティコンテキスト設定
- [ ] TLS基本設定

### 中級レベル
- [ ] Admission Controller実装
- [ ] AppArmor/SELinux設定
- [ ] Falco ルール作成
- [ ] イメージスキャニング自動化
- [ ] 監査ログ分析

### 上級レベル（CKS合格レベル）
- [ ] カスタムAdmission Webhook開発
- [ ] 高度なネットワークセキュリティ
- [ ] サプライチェーンセキュリティ実装
- [ ] セキュリティインシデント対応
- [ ] コンプライアンス自動化

## 🔍 実技試験のコツ

### セキュリティ観点での時間管理
```
問題分析（セキュリティリスク評価）: 2-3分
実装（段階的セキュリティ強化）: 5-8分
検証（セキュリティ設定確認）: 2-3分
合計: 9-14分/問題
```

### セキュリティ設定の優先順位
1. **Critical**: 権限昇格防止、機密情報保護
2. **High**: ネットワーク分離、リソース制限
3. **Medium**: 監視・ログ設定、ポリシー実装
4. **Low**: 細かな設定最適化

---

**次のステップ**: [Lab 1: クラスターセキュリティ基盤構築](./labs/lab01-cluster-security-foundation.md) でセキュリティ実装を開始してください。

**重要な心構え:**
CKS試験は単なる設定技術の試験ではありません。セキュリティエンジニアとしての思考能力、脅威に対する理解、防御戦略の立案能力が問われます。攻撃者の視点と防御者の視点の両方を持ち、バランスの取れたセキュリティ実装を心がけてください。