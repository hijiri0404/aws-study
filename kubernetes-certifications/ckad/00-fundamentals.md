# CKAD - Certified Kubernetes Application Developer 基礎概念と試験戦略

## 🎯 試験概要

**Certified Kubernetes Application Developer (CKAD)**は、Kubernetes上でのアプリケーション開発・デプロイ・運用能力を評価する実技試験です。開発者視点でのKubernetes活用に重点を置いています。

### 📊 試験詳細
- **試験時間**: 2時間
- **問題数**: 15-20問の実技タスク
- **合格点**: 66%
- **費用**: $395 USD
- **有効期間**: 3年間
- **再受験**: 1回無料

### 🎯 対象者
- **アプリケーション開発者**: コンテナ化アプリケーション開発者
- **DevOpsエンジニア**: CI/CDパイプライン構築者
- **フルスタック開発者**: クラウドネイティブアプリ開発者
- **プラットフォームエンジニア**: 開発プラットフォーム構築者

## 📋 試験ドメインと配点

### Domain 1: Application Design and Build (20%)
**アプリケーション設計と構築**

**重要なトピック:**
- **Container Images**: Dockerfileの作成・最適化
- **Jobs/CronJobs**: バッチ処理・定期実行タスク
- **Multi-Container Pods**: サイドカー・アンバサダーパターン
- **Init Containers**: 初期化処理の実装

**実践例:**
```yaml
# Multi-Container Pod Example
apiVersion: v1
kind: Pod
metadata:
  name: multi-container-app
spec:
  initContainers:
  - name: init-db
    image: busybox:1.35
    command: ['sh', '-c', 'until nc -z db 5432; do sleep 1; done']
  containers:
  - name: web-app
    image: nginx:1.20
    ports:
    - containerPort: 80
    volumeMounts:
    - name: shared-data
      mountPath: /usr/share/nginx/html
  - name: log-agent
    image: fluent/fluent-bit:2.1
    volumeMounts:
    - name: shared-logs
      mountPath: /var/log
  volumes:
  - name: shared-data
    emptyDir: {}
  - name: shared-logs
    emptyDir: {}
```

### Domain 2: Application Deployment (20%)
**アプリケーションのデプロイメント**

**重要なトピック:**
- **Deployments**: ローリングアップデート・ロールバック
- **ReplicaSets**: レプリカ管理
- **Scaling**: 水平スケーリング・垂直スケーリング
- **Deployment Strategies**: Blue/Green・Canary

**学習ポイント:**
```bash
# Deployment基本操作
kubectl create deployment app --image=nginx:1.20 --replicas=3
kubectl scale deployment app --replicas=5
kubectl set image deployment/app nginx=nginx:1.21
kubectl rollout undo deployment/app
kubectl rollout history deployment/app
```

### Domain 3: Application Observability and Maintenance (15%)
**アプリケーションの可観測性とメンテナンス**

**重要なトピック:**
- **Liveness/Readiness Probes**: ヘルスチェック
- **Logging**: アプリケーションログ管理
- **Monitoring**: メトリクス収集
- **Debugging**: トラブルシューティング

**プローブ設定例:**
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: healthy-app
spec:
  containers:
  - name: app
    image: nginx:1.20
    ports:
    - containerPort: 80
    livenessProbe:
      httpGet:
        path: /healthz
        port: 80
      initialDelaySeconds: 30
      periodSeconds: 10
    readinessProbe:
      httpGet:
        path: /ready
        port: 80
      initialDelaySeconds: 5
      periodSeconds: 5
    startupProbe:
      httpGet:
        path: /startup
        port: 80
      initialDelaySeconds: 10
      periodSeconds: 5
      failureThreshold: 30
```

### Domain 4: Application Environment, Configuration and Security (25%)
**アプリケーション環境、設定、セキュリティ**

**重要なトピック:**
- **ConfigMaps/Secrets**: 設定管理・機密情報管理
- **SecurityContexts**: セキュリティ設定
- **Resource Quotas**: リソース制限
- **ServiceAccounts**: 認証・認可

**設定管理例:**
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: app-config
data:
  database_url: "postgresql://localhost:5432/mydb"
  log_level: "info"
  config.yaml: |
    server:
      port: 8080
      timeout: 30s
    database:
      host: localhost
      port: 5432
---
apiVersion: v1
kind: Secret
metadata:
  name: app-secrets
type: Opaque
data:
  username: YWRtaW4=
  password: cGFzc3dvcmQ=
---
apiVersion: v1
kind: Pod
metadata:
  name: configured-app
spec:
  containers:
  - name: app
    image: myapp:1.0
    env:
    - name: DATABASE_URL
      valueFrom:
        configMapKeyRef:
          name: app-config
          key: database_url
    - name: DB_USERNAME
      valueFrom:
        secretKeyRef:
          name: app-secrets
          key: username
    volumeMounts:
    - name: config-volume
      mountPath: /etc/config
  volumes:
  - name: config-volume
    configMap:
      name: app-config
```

### Domain 5: Services and Networking (20%)
**サービスとネットワーキング**

**重要なトピック:**
- **Services**: ClusterIP・NodePort・LoadBalancer
- **Ingress**: HTTP/HTTPSルーティング
- **NetworkPolicies**: ネットワークセキュリティ
- **Service Discovery**: DNS・環境変数

**サービス設定例:**
```yaml
apiVersion: v1
kind: Service
metadata:
  name: web-service
spec:
  selector:
    app: web-app
  ports:
  - name: http
    port: 80
    targetPort: 8080
  - name: https
    port: 443
    targetPort: 8443
  type: ClusterIP
---
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: web-ingress
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /
spec:
  rules:
  - host: myapp.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: web-service
            port:
              number: 80
```

## 🛠️ 学習環境セットアップ

### 開発者向け学習環境

#### 1. ローカル開発環境
```bash
# Docker Desktop + minikube
curl -LO https://storage.googleapis.com/minikube/releases/latest/minikube-linux-amd64
sudo install minikube-linux-amd64 /usr/local/bin/minikube

# クラスター起動
minikube start --nodes 2 --cpus 2 --memory 4096
minikube addons enable ingress
minikube addons enable metrics-server

# 開発ツール
kubectl create namespace development
kubectl config set-context --current --namespace=development
```

#### 2. クラウド開発環境
```bash
# Google Cloud Shell (無料)
gcloud container clusters create ckad-cluster \
  --zone us-central1-a \
  --num-nodes 2 \
  --machine-type e2-medium

# AWS Cloud9 + EKS
eksctl create cluster --name ckad-cluster --nodes 2 --node-type t3.medium

# Azure Cloud Shell + AKS
az aks create --resource-group myResourceGroup \
  --name ckad-cluster --node-count 2 --node-vm-size Standard_B2s
```

### 必須開発ツール

```bash
# kubectl プラグイン
kubectl krew install ctx ns tree
kubectl krew install konfig stern

# 便利なコマンドエイリアス
alias k=kubectl
alias kgp='kubectl get pods'
alias kgs='kubectl get svc'
alias kgd='kubectl get deployment'
alias kdp='kubectl describe pod'
alias kl='kubectl logs'
alias ke='kubectl exec -it'

# YAML生成用エイリアス
alias dry='kubectl apply --dry-run=client -o yaml'
```

## 📚 学習リソースと順序

### 初心者向け学習パス（8-12週間）

#### Phase 1: コンテナ基礎（2-3週間）
1. **Docker基礎**
   - Dockerfile作成・イメージビルド
   - コンテナ実行・管理
   - ボリューム・ネットワーク

2. **コンテナ開発ベストプラクティス**
   - Multi-stage builds
   - 軽量イメージ作成
   - セキュリティ考慮事項

#### Phase 2: Kubernetes開発基礎（3-4週間）
1. **Pod・Deployment管理**
   - 基本的なワークロード作成
   - 設定管理（ConfigMap・Secret）
   - リソース制限

2. **サービス・ネットワーキング**
   - Service作成・管理
   - Ingress設定
   - 基本的なネットワーキング

#### Phase 3: アプリケーション開発実践（3-4週間）
1. **マイクロサービス開発**
   - 複数コンテナ連携
   - ヘルスチェック実装
   - ログ・メトリクス

2. **CI/CD統合**
   - GitOps基礎
   - 自動化デプロイ
   - 継続的テスト

#### Phase 4: 試験対策（1-2週間）
1. **実技演習**
   - 本教材のラボ実践
   - Practice Exams
   - 弱点補強

### 経験者向け学習パス（4-6週間）

#### Week 1-2: CKAD特化知識
- 試験ドメイン別の集中学習
- kubectl効率化テクニック
- YAML作成高速化

#### Week 3-4: 実践プロジェクト
- エンドツーエンドアプリケーション開発
- 本教材ラボの完全実践

#### Week 5-6: 試験対策
- Practice Exams (複数回)
- 時間制限での実技演習
- 弱点分野の集中補強

## 💰 学習コスト管理

### クラウド利用料金の目安
```
minikube (ローカル):
- 完全無料
- 制約: 単一ノード、リソース制限

Google GKE:
- Autopilot: ~$2.5/日
- Standard: ~$1.5/日
- 無料枠: 月$300クレジット

AWS EKS:
- クラスター: $0.10/時間
- ワーカーノード: ~$0.05/時間 × 2
- 合計: ~$3.6/日

Azure AKS:
- クラスター: 無料
- ワーカーノード: ~$0.06/時間 × 2
- 合計: ~$2.9/日
```

### コスト削減のコツ
1. **学習時間の集約**: 連続した学習でクラスター使用時間を最小化
2. **リソース管理**: 不要なリソースの即座削除
3. **ローカル優先**: 基礎学習はminikube活用
4. **クラウド無料枠**: 各プロバイダの無料枠を活用

## 🎯 CKAD特有の学習ポイント

### 1. 開発者中心の視点

**CKAとの違い:**
- クラスター管理 → アプリケーション開発
- インフラ運用 → アプリケーション運用
- システム管理 → 開発ワークフロー

**重要な考え方:**
```
開発者が考慮すべき要素:
├── アプリケーション設計
│   ├── コンテナ化戦略
│   ├── マイクロサービス分割
│   └── データ永続化
├── 運用性
│   ├── ヘルスチェック
│   ├── ログ・監視
│   └── 設定管理
└── セキュリティ
    ├── 最小権限の原則
    ├── シークレット管理
    └── ネットワーク分離
```

### 2. 実用的なコード例重視

**学習すべき実装パターン:**

```yaml
# 1. サイドカーパターン
apiVersion: v1
kind: Pod
metadata:
  name: sidecar-example
spec:
  containers:
  - name: main-app
    image: nginx:1.20
    volumeMounts:
    - name: shared-logs
      mountPath: /var/log/nginx
  - name: log-shipper
    image: fluent/fluent-bit:2.1
    volumeMounts:
    - name: shared-logs
      mountPath: /var/log/nginx
      readOnly: true
  volumes:
  - name: shared-logs
    emptyDir: {}
```

```yaml
# 2. Ambassadorパターン
apiVersion: v1
kind: Pod
metadata:
  name: ambassador-example
spec:
  containers:
  - name: main-app
    image: myapp:1.0
    env:
    - name: DATABASE_URL
      value: "localhost:5432"
  - name: db-proxy
    image: postgres-proxy:1.0
    ports:
    - containerPort: 5432
```

### 3. kubectl効率化（CKAD必須）

```bash
# 高速YAML生成
kubectl run nginx --image=nginx:1.20 --dry-run=client -o yaml > pod.yaml
kubectl create deployment app --image=nginx:1.20 --dry-run=client -o yaml > deployment.yaml
kubectl expose deployment app --port=80 --dry-run=client -o yaml > service.yaml

# 設定管理
kubectl create configmap app-config --from-literal=key1=value1 --dry-run=client -o yaml
kubectl create secret generic app-secret --from-literal=password=secret123 --dry-run=client -o yaml

# 素早い動作確認
kubectl run test --image=busybox:1.35 --rm -it -- /bin/sh
kubectl exec -it <pod> -- /bin/bash
kubectl logs <pod> -f
```

## 📊 スキルチェックリスト

### 初級レベル
- [ ] 基本的なPod作成・管理
- [ ] Docker概念とコンテナ操作
- [ ] kubectl基本コマンド習得
- [ ] ConfigMap・Secret基本使用
- [ ] Service基本設定

### 中級レベル
- [ ] Deployment作成・管理・更新
- [ ] Multi-container Pod設計
- [ ] リソース制限・要求設定
- [ ] ヘルスチェック実装
- [ ] Ingress設定

### 上級レベル
- [ ] 複雑なアプリケーション設計
- [ ] セキュリティベストプラクティス実装
- [ ] パフォーマンス最適化
- [ ] トラブルシューティング
- [ ] CI/CD統合

## 🔍 実技試験のコツ

### 時間管理戦略
```
問題分析: 1-2分
実装: 4-6分
テスト・確認: 1-2分
合計: 6-10分/問題
```

### 必須暗記コマンド
```bash
# Pod関連
kubectl run <name> --image=<image>
kubectl get pods -o wide
kubectl describe pod <name>
kubectl logs <pod> -c <container>
kubectl exec -it <pod> -- /bin/bash

# Deployment関連
kubectl create deployment <name> --image=<image> --replicas=<count>
kubectl scale deployment <name> --replicas=<count>
kubectl set image deployment/<name> <container>=<image>
kubectl rollout undo deployment/<name>

# Service関連
kubectl expose deployment <name> --port=<port> --target-port=<port>
kubectl get endpoints <service>

# 設定関連
kubectl create configmap <name> --from-literal=<key>=<value>
kubectl create secret generic <name> --from-literal=<key>=<value>
```

### よくある間違いと対策
1. **YAML書式ミス**: インデント・引用符に注意
2. **ラベルセレクター不一致**: Service・Deploymentのラベル整合性
3. **ポート設定ミス**: containerPort・port・targetPortの違い
4. **namespace指定忘れ**: 問題で指定されたnamespaceを確実に使用

---

**次のステップ**: [Lab 1: Pod・Container基礎](./labs/lab01-pods-containers.md) で実践的なアプリケーション開発を開始してください。

**重要な心構え:**
CKAD試験は実際の開発現場で必要となるスキルを評価します。単なる暗記ではなく、実際にアプリケーションを動かしながら体感的に学習することが成功の鍵です。