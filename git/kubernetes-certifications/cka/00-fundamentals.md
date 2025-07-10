# CKA - Certified Kubernetes Administrator 基礎概念と試験戦略

## 🎯 試験概要

**Certified Kubernetes Administrator (CKA)**は、Kubernetesクラスターの管理・運用能力を評価する実技試験です。実際のKubernetesクラスターでタスクを完了する必要があります。

### 📊 試験詳細
- **試験時間**: 2時間
- **問題数**: 15-20問の実技タスク
- **合格点**: 66%
- **費用**: $395 USD
- **有効期間**: 3年間
- **再受験**: 1回無料

### 🎯 対象者
- **Kubernetesクラスター管理者**: 本番環境の運用担当者
- **インフラエンジニア**: コンテナ基盤の構築・管理者
- **DevOpsエンジニア**: CI/CD環境でのKubernetes活用者
- **SRE**: サイト信頼性エンジニア

## 📋 試験ドメインと配点

### Domain 1: Cluster Architecture, Installation & Configuration (25%)
**クラスターアーキテクチャ、インストール、設定**

**重要なトピック:**
- **kubeadm**: クラスターの構築・管理
- **etcd**: バックアップ・復元
- **API Server**: 設定とセキュリティ
- **Node管理**: 追加・削除・メンテナンス
- **高可用性**: マルチマスター構成

**実務での重要性:**
```bash
# クラスター初期化
kubeadm init --pod-network-cidr=10.244.0.0/16

# ノード参加
kubeadm join <master-ip>:6443 --token <token> \
    --discovery-token-ca-cert-hash sha256:<hash>

# etcdバックアップ
ETCDCTL_API=3 etcdctl snapshot save /backup/etcd-snapshot.db \
    --endpoints=https://127.0.0.1:2379 \
    --cacert=/etc/etcd/ca.crt \
    --cert=/etc/etcd/etcd-server.crt \
    --key=/etc/etcd/etcd-server.key
```

### Domain 2: Workloads & Scheduling (15%)
**ワークロードとスケジューリング**

**重要なトピック:**
- **Deployments**: アプリケーションのデプロイ・管理
- **DaemonSets**: 全ノードでの実行
- **StatefulSets**: ステートフルアプリケーション
- **Jobs/CronJobs**: バッチ処理・定期実行
- **Pod Scheduling**: ノード選択・リソース管理

**実践例:**
```yaml
# Deployment作成
apiVersion: apps/v1
kind: Deployment
metadata:
  name: nginx-deployment
spec:
  replicas: 3
  selector:
    matchLabels:
      app: nginx
  template:
    metadata:
      labels:
        app: nginx
    spec:
      containers:
      - name: nginx
        image: nginx:1.20
        resources:
          requests:
            memory: "64Mi"
            cpu: "250m"
          limits:
            memory: "128Mi"
            cpu: "500m"
```

### Domain 3: Services & Networking (20%)
**サービスとネットワーキング**

**重要なトピック:**
- **Services**: ClusterIP、NodePort、LoadBalancer
- **Ingress**: 外部アクセスの管理
- **Network Policies**: セキュリティルール
- **CNI**: ネットワークプラグイン
- **DNS**: クラスター内名前解決

**実装例:**
```yaml
# Service作成
apiVersion: v1
kind: Service
metadata:
  name: nginx-service
spec:
  selector:
    app: nginx
  ports:
  - port: 80
    targetPort: 80
  type: ClusterIP

---
# NetworkPolicy作成
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: deny-all
spec:
  podSelector: {}
  policyTypes:
  - Ingress
  - Egress
```

### Domain 4: Storage (10%)
**ストレージ**

**重要なトピック:**
- **Persistent Volumes**: 永続ストレージ
- **Persistent Volume Claims**: ストレージ要求
- **Storage Classes**: 動的プロビジョニング
- **Volume Types**: hostPath、NFS、CSI

### Domain 5: Troubleshooting (30%)
**トラブルシューティング**

**重要なトピック:**
- **ログ分析**: Pod・コンテナログの確認
- **リソース監視**: CPU・メモリ使用量
- **ネットワーク問題**: 接続性の診断
- **クラスター問題**: ノード・コンポーネント異常

**診断コマンド:**
```bash
# Pod状態確認
kubectl get pods -o wide
kubectl describe pod <pod-name>
kubectl logs <pod-name> -c <container-name>

# ノード状態確認
kubectl get nodes
kubectl describe node <node-name>
kubectl top node

# クラスターコンポーネント確認
kubectl get componentstatuses
kubectl cluster-info
```

## 🛠️ 学習環境セットアップ

### 必須ツール

```bash
# kubectl インストール
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
chmod +x kubectl
sudo mv kubectl /usr/local/bin/

# kubectlバージョン確認
kubectl version --client

# Docker インストール
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# kubeadm、kubelet インストール
curl -s https://packages.cloud.google.com/apt/doc/apt-key.gpg | sudo apt-key add -
echo "deb https://apt.kubernetes.io/ kubernetes-xenial main" | sudo tee /etc/apt/sources.list.d/kubernetes.list
sudo apt-get update
sudo apt-get install -y kubelet kubeadm kubectl
sudo apt-mark hold kubelet kubeadm kubectl
```

### 練習環境の選択

#### 1. クラウドマネージドサービス（推奨）
```bash
# AWS EKS
eksctl create cluster --name cka-practice --nodes 3

# Google GKE  
gcloud container clusters create cka-practice --num-nodes=3

# Azure AKS
az aks create --resource-group myResourceGroup --name cka-practice --node-count 3
```

#### 2. ローカル環境（学習用）
```bash
# minikube
curl -LO https://storage.googleapis.com/minikube/releases/latest/minikube-linux-amd64
sudo install minikube-linux-amd64 /usr/local/bin/minikube
minikube start --nodes 3

# kind (Kubernetes in Docker)
curl -Lo ./kind https://kind.sigs.k8s.io/dl/v0.20.0/kind-linux-amd64
chmod +x ./kind
sudo mv ./kind /usr/local/bin/kind
kind create cluster --config multi-node-cluster.yaml
```

#### 3. 自作クラスター（上級者向け）
```bash
# kubeadmでのクラスター構築
# マスターノード
sudo kubeadm init --pod-network-cidr=10.244.0.0/16

# ワーカーノード
sudo kubeadm join <master-ip>:6443 --token <token> \
    --discovery-token-ca-cert-hash sha256:<hash>

# CNI（Flannel）インストール
kubectl apply -f https://raw.githubusercontent.com/flannel-io/flannel/master/Documentation/kube-flannel.yml
```

## 📚 学習リソース

### 公式リソース
- **[Kubernetes公式ドキュメント](https://kubernetes.io/docs/)**: 最重要リソース
- **[CKA試験ガイド](https://www.cncf.io/certification/cka/)**: 公式試験情報
- **[Kubernetes the Hard Way](https://github.com/kelseyhightower/kubernetes-the-hard-way)**: 基礎理解

### 学習パス（推奨12-16週間）

#### Phase 1: Kubernetes基礎（3-4週間）
1. **コンテナ基礎**: Docker、コンテナの概念
2. **Kubernetes概要**: アーキテクチャ、コンポーネント
3. **基本操作**: kubectl、Pod、Service作成

#### Phase 2: クラスター管理（4-5週間）
1. **クラスター構築**: kubeadm、ネットワーク設定
2. **ノード管理**: 追加・削除・メンテナンス
3. **etcd管理**: バックアップ・復元

#### Phase 3: アプリケーション管理（3-4週間）
1. **ワークロード**: Deployment、StatefulSet
2. **サービス**: 負荷分散、Ingress
3. **ストレージ**: PV、PVC、StorageClass

#### Phase 4: 運用・トラブルシューティング（3-4週間）
1. **監視**: リソース使用量、ヘルスチェック
2. **ログ管理**: 中央集約、分析
3. **問題解決**: 実践的なトラブルシューティング

#### Phase 5: 試験対策（1-2週間）
1. **模擬試験**: 時間制限での実技演習
2. **弱点補強**: 苦手分野の集中学習

## 💰 学習コスト管理

### クラウド利用料金の目安
```
AWS EKS:
- クラスター料金: $0.10/時間
- ワーカーノード: $0.096/時間 × 3 = $0.288/時間
- 合計: 約$0.40/時間 = $10/日

Google GKE:
- クラスター料金: 無料（Autopilot推奨）
- ワーカーノード: $0.10/時間 × 3 = $0.30/時間
- 合計: 約$7.2/日

minikube:
- 完全無料（ローカル実行）
- 制約: シングルノード、リソース制限
```

### コスト削減のコツ
1. **学習時間の集約**: 短期集中で利用
2. **リソース削除**: 使用後は必ずクラスター削除
3. **ローカル環境**: 基礎学習はminikube活用
4. **スポットインスタンス**: クラウドでのコスト削減

## 🎯 試験対策のポイント

### 重要な設定ファイル場所（暗記必須）
```bash
# kubelet設定
/var/lib/kubelet/config.yaml
/etc/systemd/system/kubelet.service.d/10-kubeadm.conf

# etcd設定
/etc/etcd/etcd.conf
/etc/kubernetes/manifests/etcd.yaml

# API Server設定
/etc/kubernetes/manifests/kube-apiserver.yaml

# kubeconfig
~/.kube/config
/etc/kubernetes/admin.conf
```

### よく使うkubectlコマンド（高速化必須）
```bash
# エイリアス設定（必須）
alias k=kubectl
alias kg='kubectl get'
alias kd='kubectl describe'
alias kdel='kubectl delete'

# 補完設定
source <(kubectl completion bash)
complete -F __start_kubectl k

# よく使うオプション
kubectl get pods -o wide --all-namespaces
kubectl describe pod <name> -n <namespace>
kubectl logs <pod-name> -c <container> --previous
kubectl exec -it <pod-name> -- /bin/bash
```

### 時間管理テクニック
- **1問あたり6-8分**: 120分÷15問=8分/問
- **簡単な問題から**: 確実に点数を獲得
- **YAML生成**: `kubectl create --dry-run=client -o yaml`活用
- **ドキュメント参照**: 試験中もKubernetes.ioが参照可能

## 🔍 実技試験のコツ

### 1. 環境設定の効率化
```bash
# bashrcに追加
export do="--dry-run=client -o yaml"
export now="--force --grace-period 0"

# 使用例
kubectl create deployment nginx --image=nginx $do > deployment.yaml
kubectl delete pod nginx $now
```

### 2. YAMLファイルの効率的作成
```bash
# テンプレート生成
kubectl create deployment nginx --image=nginx --dry-run=client -o yaml > deployment.yaml

# 即座に適用
kubectl create deployment nginx --image=nginx --dry-run=client -o yaml | kubectl apply -f -
```

### 3. トラブルシューティングの体系的アプローチ
```bash
# 1. 問題の特定
kubectl get all --all-namespaces

# 2. 詳細確認
kubectl describe <resource> <name>

# 3. ログ確認
kubectl logs <pod-name> --previous

# 4. リソース使用量確認
kubectl top nodes
kubectl top pods
```

---

**次のステップ**: [Lab 1: kubeadmクラスター構築実践](./labs/lab01-cluster-setup.md) で実際のクラスター構築を開始してください。

**重要**: CKA試験は実技中心です。理論学習と並行して、必ず実際のKubernetesクラスターでの操作経験を積んでください。