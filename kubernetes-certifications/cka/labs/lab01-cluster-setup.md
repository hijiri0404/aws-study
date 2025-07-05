# Lab 1: kubeadm によるKubernetesクラスター構築実践

## 🎯 学習目標

このラボでは、kubeadm を使用してマルチノードKubernetesクラスターを一から構築します。CKA試験で最も重要な実技の一つであるクラスター管理の基礎を習得します。

**習得スキル**:
- kubeadm によるクラスター初期化
- ワーカーノードの追加・管理
- CNI (Container Network Interface) の設定
- etcd クラスターの理解
- クラスターのヘルスチェック

**所要時間**: 4-6時間  
**推定コスト**: $15-25

## 📋 シナリオ

**企業**: 中規模ITサービス企業  
**課題**: 本番環境用Kubernetesクラスターの構築  
**要件**: 
- 高可用性マスターノード（3台）
- ワーカーノード（3台） 
- Flannelネットワーク
- セキュアな通信設定

## Phase 1: 環境準備

### 1.1 インフラストラクチャのセットアップ

#### AWS EC2インスタンス作成

```bash
#!/bin/bash
# スクリプト: setup-cluster-infrastructure.sh

echo "🚀 Kubernetes クラスター用インフラ作成中..."

# 変数設定
REGION="us-east-1"
KEY_NAME="k8s-cluster-key"
SECURITY_GROUP="k8s-cluster-sg"

# セキュリティグループ作成
echo "🔒 セキュリティグループ作成中..."
aws ec2 create-security-group \
    --group-name $SECURITY_GROUP \
    --description "Kubernetes Cluster Security Group" \
    --region $REGION

SG_ID=$(aws ec2 describe-security-groups \
    --group-names $SECURITY_GROUP \
    --region $REGION \
    --query 'SecurityGroups[0].GroupId' \
    --output text)

# セキュリティグループルール追加
echo "📋 セキュリティルール設定中..."

# SSH アクセス
aws ec2 authorize-security-group-ingress \
    --group-id $SG_ID \
    --protocol tcp \
    --port 22 \
    --cidr 0.0.0.0/0 \
    --region $REGION

# Kubernetes API Server
aws ec2 authorize-security-group-ingress \
    --group-id $SG_ID \
    --protocol tcp \
    --port 6443 \
    --source-group $SG_ID \
    --region $REGION

# etcd server client API
aws ec2 authorize-security-group-ingress \
    --group-id $SG_ID \
    --protocol tcp \
    --port 2379-2380 \
    --source-group $SG_ID \
    --region $REGION

# kubelet API
aws ec2 authorize-security-group-ingress \
    --group-id $SG_ID \
    --protocol tcp \
    --port 10250 \
    --source-group $SG_ID \
    --region $REGION

# kube-scheduler
aws ec2 authorize-security-group-ingress \
    --group-id $SG_ID \
    --protocol tcp \
    --port 10259 \
    --source-group $SG_ID \
    --region $REGION

# kube-controller-manager
aws ec2 authorize-security-group-ingress \
    --group-id $SG_ID \
    --protocol tcp \
    --port 10257 \
    --source-group $SG_ID \
    --region $REGION

# NodePort Services
aws ec2 authorize-security-group-ingress \
    --group-id $SG_ID \
    --protocol tcp \
    --port 30000-32767 \
    --source-group $SG_ID \
    --region $REGION

# Flannel VXLAN
aws ec2 authorize-security-group-ingress \
    --group-id $SG_ID \
    --protocol udp \
    --port 8472 \
    --source-group $SG_ID \
    --region $REGION

echo "✅ セキュリティグループ設定完了: $SG_ID"

# マスターノード作成（3台）
echo "🖥️ マスターノード作成中..."
for i in 1 2 3; do
    aws ec2 run-instances \
        --image-id ami-0c02fb55956c7d316 \
        --instance-type t3.medium \
        --key-name $KEY_NAME \
        --security-group-ids $SG_ID \
        --tag-specifications "ResourceType=instance,Tags=[{Key=Name,Value=k8s-master-$i},{Key=Role,Value=master}]" \
        --region $REGION
done

# ワーカーノード作成（3台）
echo "👷 ワーカーノード作成中..."
for i in 1 2 3; do
    aws ec2 run-instances \
        --image-id ami-0c02fb55956c7d316 \
        --instance-type t3.medium \
        --key-name $KEY_NAME \
        --security-group-ids $SG_ID \
        --tag-specifications "ResourceType=instance,Tags=[{Key=Name,Value=k8s-worker-$i},{Key=Role,Value=worker}]" \
        --region $REGION
done

echo "⏳ インスタンス起動中... 3分待機"
sleep 180

# インスタンス情報取得
echo "📋 インスタンス情報:"
aws ec2 describe-instances \
    --filters "Name=tag:Name,Values=k8s-*" \
             "Name=instance-state-name,Values=running" \
    --query 'Reservations[*].Instances[*].[Tags[?Key==`Name`].Value|[0],InstanceId,PrivateIpAddress,PublicIpAddress]' \
    --output table \
    --region $REGION

echo "🎉 インフラストラクチャ作成完了！"
```

### 1.2 全ノードでの基本設定

```bash
#!/bin/bash
# スクリプト: prepare-all-nodes.sh
# 全ノード（マスター・ワーカー）で実行

echo "🔧 Kubernetes ノード準備中..."

# システム更新
sudo apt-get update -y
sudo apt-get upgrade -y

# 必要なパッケージインストール
sudo apt-get install -y \
    apt-transport-https \
    ca-certificates \
    curl \
    gnupg \
    lsb-release

# swap無効化（Kubernetes要件）
echo "💾 swap無効化中..."
sudo swapoff -a
sudo sed -i '/ swap / s/^\(.*\)$/#\1/g' /etc/fstab

# カーネルモジュール設定
echo "🔌 カーネルモジュール設定中..."
cat <<EOF | sudo tee /etc/modules-load.d/k8s.conf
overlay
br_netfilter
EOF

sudo modprobe overlay
sudo modprobe br_netfilter

# sysctl設定
echo "⚙️ ネットワーク設定中..."
cat <<EOF | sudo tee /etc/sysctl.d/k8s.conf
net.bridge.bridge-nf-call-iptables  = 1
net.bridge.bridge-nf-call-ip6tables = 1
net.ipv4.ip_forward                 = 1
EOF

sudo sysctl --system

# containerd インストール
echo "📦 containerd インストール中..."
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

sudo apt-get update -y
sudo apt-get install -y containerd.io

# containerd設定
sudo mkdir -p /etc/containerd
containerd config default | sudo tee /etc/containerd/config.toml

# SystemdCgroup有効化
sudo sed -i 's/SystemdCgroup \= false/SystemdCgroup \= true/g' /etc/containerd/config.toml

sudo systemctl restart containerd
sudo systemctl enable containerd

# Kubernetesリポジトリ追加
echo "📚 Kubernetes リポジトリ追加中..."
curl -s https://packages.cloud.google.com/apt/doc/apt-key.gpg | sudo apt-key add -
echo "deb https://apt.kubernetes.io/ kubernetes-xenial main" | sudo tee /etc/apt/sources.list.d/kubernetes.list

# kubelet, kubeadm, kubectl インストール
echo "⚡ Kubernetes コンポーネントインストール中..."
sudo apt-get update -y
sudo apt-get install -y kubelet=1.28.2-00 kubeadm=1.28.2-00 kubectl=1.28.2-00
sudo apt-mark hold kubelet kubeadm kubectl

# kubelet有効化
sudo systemctl enable kubelet

echo "✅ ノード準備完了！"
echo "📝 次の手順: マスターノードで kubeadm init を実行してください"
```

## Phase 2: クラスター初期化

### 2.1 プライマリマスターノードの初期化

```bash
#!/bin/bash
# スクリプト: init-primary-master.sh
# プライマリマスターノードでのみ実行

echo "🎯 プライマリマスターノード初期化中..."

# クラスター初期化
echo "🚀 kubeadm init 実行中..."
sudo kubeadm init \
    --pod-network-cidr=10.244.0.0/16 \
    --apiserver-advertise-address=$(hostname -I | awk '{print $1}') \
    --control-plane-endpoint=$(hostname -I | awk '{print $1}'):6443 \
    --upload-certs

# kubectl設定
echo "⚙️ kubectl設定中..."
mkdir -p $HOME/.kube
sudo cp -i /etc/kubernetes/admin.conf $HOME/.kube/config
sudo chown $(id -u):$(id -g) $HOME/.kube/config

# クラスター状態確認
echo "🔍 クラスター状態確認中..."
kubectl cluster-info
kubectl get nodes
kubectl get pods -A

# Flannelネットワークアドオンインストール
echo "🌐 Flannel CNI インストール中..."
kubectl apply -f https://github.com/flannel-io/flannel/releases/latest/download/kube-flannel.yml

# コントロールプレーンへの追加用コマンド生成
echo "🔑 コントロールプレーン追加用トークン生成中..."
kubeadm token create --print-join-command > /tmp/worker-join-command.sh

# コントロールプレーン追加用の証明書キー取得
echo "📜 証明書アップロード用キー生成中..."
sudo kubeadm init phase upload-certs --upload-certs

echo "✅ プライマリマスター初期化完了！"
echo ""
echo "📋 次の手順:"
echo "1. 他のマスターノードに証明書キーを使用してジョイン"
echo "2. ワーカーノードをクラスターにジョイン"
echo "3. すべてのノードが Ready 状態になることを確認"
```

### 2.2 セカンダリマスターノードの追加

```bash
#!/bin/bash
# スクリプト: join-secondary-masters.sh
# セカンダリマスターノードで実行

echo "🤝 セカンダリマスターノードをクラスターに追加中..."

# プライマリマスターから取得した情報を設定
PRIMARY_MASTER_IP="<プライマリマスターのIP>"
JOIN_TOKEN="<kubeadm token>"
DISCOVERY_TOKEN_CA_CERT_HASH="<CA証明書ハッシュ>"
CERTIFICATE_KEY="<証明書キー>"

# コントロールプレーンとしてジョイン
sudo kubeadm join $PRIMARY_MASTER_IP:6443 \
    --token $JOIN_TOKEN \
    --discovery-token-ca-cert-hash $DISCOVERY_TOKEN_CA_CERT_HASH \
    --control-plane \
    --certificate-key $CERTIFICATE_KEY

# kubectl設定
mkdir -p $HOME/.kube
sudo cp -i /etc/kubernetes/admin.conf $HOME/.kube/config
sudo chown $(id -u):$(id -g) $HOME/.kube/config

# クラスター状態確認
kubectl get nodes
kubectl get pods -A

echo "✅ セカンダリマスターノード追加完了！"
```

### 2.3 ワーカーノードの追加

```bash
#!/bin/bash
# スクリプト: join-worker-nodes.sh
# ワーカーノードで実行

echo "👷 ワーカーノードをクラスターに追加中..."

# プライマリマスターから取得した情報を設定
PRIMARY_MASTER_IP="<プライマリマスターのIP>"
JOIN_TOKEN="<kubeadm token>"
DISCOVERY_TOKEN_CA_CERT_HASH="<CA証明書ハッシュ>"

# ワーカーノードとしてジョイン
sudo kubeadm join $PRIMARY_MASTER_IP:6443 \
    --token $JOIN_TOKEN \
    --discovery-token-ca-cert-hash $DISCOVERY_TOKEN_CA_CERT_HASH

echo "✅ ワーカーノード追加完了！"
echo "📝 マスターノードで 'kubectl get nodes' を実行して確認してください"
```

## Phase 3: クラスター検証とテスト

### 3.1 クラスター正常性確認

```bash
#!/bin/bash
# スクリプト: verify-cluster-health.sh
# マスターノードで実行

echo "🔍 Kubernetesクラスター正常性確認中..."

echo "📊 ノード状態確認:"
kubectl get nodes -o wide

echo ""
echo "🏗️ システムPod状態確認:"
kubectl get pods -n kube-system

echo ""
echo "🌐 ネットワーク確認:"
kubectl get pods -n kube-flannel

echo ""
echo "⚡ コンポーネント状態確認:"
kubectl get componentstatuses

echo ""
echo "📡 クラスター情報:"
kubectl cluster-info

echo ""
echo "🔧 クラスター設定確認:"
kubectl config view --minify

# ネットワーク接続テスト
echo ""
echo "🌐 ネットワーク接続テスト実行中..."

# テスト用Podデプロイ
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: network-test-1
  labels:
    app: network-test
spec:
  containers:
  - name: busybox
    image: busybox:1.35
    command: ['sleep', '3600']
---
apiVersion: v1
kind: Pod
metadata:
  name: network-test-2
  labels:
    app: network-test
spec:
  containers:
  - name: busybox
    image: busybox:1.35
    command: ['sleep', '3600']
EOF

echo "⏳ テストPod起動待機中..."
kubectl wait --for=condition=Ready pod/network-test-1 --timeout=300s
kubectl wait --for=condition=Ready pod/network-test-2 --timeout=300s

# Pod間通信テスト
echo "📡 Pod間通信テスト:"
POD1_IP=$(kubectl get pod network-test-1 -o jsonpath='{.status.podIP}')
POD2_IP=$(kubectl get pod network-test-2 -o jsonpath='{.status.podIP}')

echo "Pod1 IP: $POD1_IP"
echo "Pod2 IP: $POD2_IP"

kubectl exec network-test-1 -- ping -c 3 $POD2_IP

# DNS解決テスト
echo ""
echo "🔍 DNS解決テスト:"
kubectl exec network-test-1 -- nslookup kubernetes.default

# クリーンアップ
kubectl delete pod network-test-1 network-test-2

echo ""
echo "✅ クラスター正常性確認完了！"
```

### 3.2 基本的なアプリケーションデプロイテスト

```yaml
# ファイル: test-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: nginx-test
  labels:
    app: nginx-test
spec:
  replicas: 3
  selector:
    matchLabels:
      app: nginx-test
  template:
    metadata:
      labels:
        app: nginx-test
    spec:
      containers:
      - name: nginx
        image: nginx:1.20
        ports:
        - containerPort: 80
        resources:
          requests:
            cpu: 100m
            memory: 128Mi
          limits:
            cpu: 200m
            memory: 256Mi
---
apiVersion: v1
kind: Service
metadata:
  name: nginx-test-service
spec:
  selector:
    app: nginx-test
  ports:
  - port: 80
    targetPort: 80
    nodePort: 30080
  type: NodePort
```

```bash
#!/bin/bash
# スクリプト: test-application-deployment.sh

echo "🚀 アプリケーションデプロイテスト実行中..."

# テストアプリケーションデプロイ
kubectl apply -f test-deployment.yaml

echo "⏳ Deployment準備完了待機中..."
kubectl wait --for=condition=Available deployment/nginx-test --timeout=300s

# デプロイ状態確認
echo "📊 Deployment状態:"
kubectl get deployment nginx-test
kubectl get pods -l app=nginx-test
kubectl get service nginx-test-service

# サービス接続テスト
echo "🔗 サービス接続テスト:"
NODE_IP=$(kubectl get nodes -o jsonpath='{.items[0].status.addresses[?(@.type=="ExternalIP")].address}')
if [ -z "$NODE_IP" ]; then
    NODE_IP=$(kubectl get nodes -o jsonpath='{.items[0].status.addresses[?(@.type=="InternalIP")].address}')
fi

echo "ノードIP: $NODE_IP"
curl -I http://$NODE_IP:30080

# Pod分散確認
echo ""
echo "📍 Pod分散状態:"
kubectl get pods -l app=nginx-test -o wide

# ログ確認
echo ""
echo "📋 Podログサンプル:"
POD_NAME=$(kubectl get pods -l app=nginx-test -o jsonpath='{.items[0].metadata.name}')
kubectl logs $POD_NAME --tail=10

echo ""
echo "✅ アプリケーションデプロイテスト完了！"
echo "🧹 テストリソースクリーンアップ中..."
kubectl delete -f test-deployment.yaml

echo "✨ クリーンアップ完了！"
```

## Phase 4: etcd バックアップ・復元の実践

### 4.1 etcd バックアップ

```bash
#!/bin/bash
# スクリプト: backup-etcd.sh
# マスターノードで実行

echo "💾 etcd バックアップ実行中..."

# etcdctl のインストール確認
if ! command -v etcdctl &> /dev/null; then
    echo "📥 etcdctl インストール中..."
    ETCD_VER=v3.5.9
    curl -L https://github.com/etcd-io/etcd/releases/download/${ETCD_VER}/etcd-${ETCD_VER}-linux-amd64.tar.gz -o /tmp/etcd-${ETCD_VER}-linux-amd64.tar.gz
    
    tar xzvf /tmp/etcd-${ETCD_VER}-linux-amd64.tar.gz -C /tmp/
    sudo mv /tmp/etcd-${ETCD_VER}-linux-amd64/etcdctl /usr/local/bin/
    rm -rf /tmp/etcd-${ETCD_VER}-linux-amd64*
fi

# 証明書パス設定
ETCD_CERT_DIR="/etc/kubernetes/pki/etcd"
BACKUP_DIR="/backup/etcd"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# バックアップディレクトリ作成
sudo mkdir -p $BACKUP_DIR

echo "🔐 etcd バックアップ作成中..."
sudo ETCDCTL_API=3 etcdctl snapshot save ${BACKUP_DIR}/etcd-backup-${TIMESTAMP}.db \
    --endpoints=https://127.0.0.1:2379 \
    --cacert=${ETCD_CERT_DIR}/ca.crt \
    --cert=${ETCD_CERT_DIR}/server.crt \
    --key=${ETCD_CERT_DIR}/server.key

# バックアップ検証
echo "✅ バックアップ検証中..."
sudo ETCDCTL_API=3 etcdctl snapshot status ${BACKUP_DIR}/etcd-backup-${TIMESTAMP}.db \
    --write-out=table

echo "📊 バックアップファイル情報:"
ls -lh ${BACKUP_DIR}/etcd-backup-${TIMESTAMP}.db

echo "✅ etcd バックアップ完了: ${BACKUP_DIR}/etcd-backup-${TIMESTAMP}.db"
```

### 4.2 etcd 復元テスト

```bash
#!/bin/bash
# スクリプト: restore-etcd-test.sh
# マスターノードで実行（注意: テスト用）

echo "⚠️  etcd 復元テスト実行中..."
echo "📝 注意: これはテスト用手順です。本番環境では慎重に実行してください。"

BACKUP_FILE="/backup/etcd/etcd-backup-*.db"
RESTORE_DIR="/var/lib/etcd-restore"

# 現在のクラスター状態確認
echo "📊 復元前のクラスター状態:"
kubectl get nodes
kubectl get pods -A --no-headers | wc -l

# テスト用データ作成
echo "🧪 テスト用データ作成中..."
kubectl create namespace restore-test
kubectl create deployment test-app --image=nginx:1.20 -n restore-test
kubectl scale deployment test-app --replicas=3 -n restore-test

echo "⏳ テストデータ準備完了待機..."
kubectl wait --for=condition=Available deployment/test-app -n restore-test --timeout=180s

echo "📊 テストデータ確認:"
kubectl get all -n restore-test

# etcd 停止（復元のため）
echo "⏹️ etcd サービス停止中..."
sudo systemctl stop kubelet
sudo systemctl stop etcd

# データディレクトリバックアップ
echo "💾 現在のetcdデータディレクトリバックアップ中..."
sudo mv /var/lib/etcd /var/lib/etcd-backup-$(date +%Y%m%d_%H%M%S)

# 復元実行
echo "🔄 etcd データ復元中..."
sudo ETCDCTL_API=3 etcdctl snapshot restore $BACKUP_FILE \
    --data-dir=$RESTORE_DIR \
    --name=master-1 \
    --initial-cluster=master-1=https://127.0.0.1:2380 \
    --initial-cluster-token=etcd-cluster-1 \
    --initial-advertise-peer-urls=https://127.0.0.1:2380

# 復元されたデータをetcdディレクトリに移動
sudo mv $RESTORE_DIR /var/lib/etcd
sudo chown -R etcd:etcd /var/lib/etcd

# サービス再開
echo "▶️ サービス再開中..."
sudo systemctl start etcd
sudo systemctl start kubelet

echo "⏳ クラスター復旧待機中..."
sleep 60

# 復元後の状態確認
echo "📊 復元後のクラスター状態:"
kubectl get nodes
kubectl get pods -A --no-headers | wc -l

echo "🧪 テストデータ確認:"
kubectl get all -n restore-test 2>/dev/null || echo "テストデータは復元されていません（期待される動作）"

echo "✅ etcd 復元テスト完了！"
echo "📝 注意: 復元により最新のクラスター状態は失われました"
```

## Phase 5: クラスター管理とメンテナンス

### 5.1 ノード管理操作

```bash
#!/bin/bash
# スクリプト: node-management.sh

echo "🔧 ノード管理操作の実践..."

# ノード情報詳細表示
echo "📊 現在のノード状態:"
kubectl get nodes -o wide

echo ""
echo "🏷️ ノードラベル管理:"

# ワーカーノードにラベル追加
WORKER_NODE=$(kubectl get nodes --no-headers | grep -v master | head -n1 | awk '{print $1}')
kubectl label node $WORKER_NODE node-type=worker-high-memory
kubectl label node $WORKER_NODE environment=production

# ラベル確認
kubectl get nodes --show-labels

echo ""
echo "🚫 ノードのドレイン（メンテナンス準備）:"

# ノードをスケジュール不可に設定
kubectl cordon $WORKER_NODE

# ノード上のPodを他ノードに移動
kubectl drain $WORKER_NODE --ignore-daemonsets --delete-emptydir-data --force

echo "ノード $WORKER_NODE がドレインされました"

echo ""
echo "⏳ 30秒待機（メンテナンス時間をシミュレート）..."
sleep 30

echo ""
echo "✅ ノードを再びスケジュール可能に設定:"
kubectl uncordon $WORKER_NODE

echo "ノード $WORKER_NODE が再び利用可能になりました"

# 最終状態確認
echo ""
echo "📊 最終ノード状態:"
kubectl get nodes
```

### 5.2 クラスター証明書管理

```bash
#!/bin/bash
# スクリプト: certificate-management.sh

echo "🔐 クラスター証明書管理..."

# 証明書有効期限確認
echo "📅 証明書有効期限確認:"
sudo kubeadm certs check-expiration

echo ""
echo "📋 証明書ファイル一覧:"
sudo find /etc/kubernetes/pki -name "*.crt" -exec openssl x509 -in {} -text -noout -subject -dates \; 2>/dev/null | grep -E "(subject=|notAfter=)"

echo ""
echo "🔄 証明書更新テスト:"

# バックアップ作成
sudo cp -r /etc/kubernetes/pki /etc/kubernetes/pki-backup-$(date +%Y%m%d_%H%M%S)

# API Server証明書更新
sudo kubeadm certs renew apiserver

# 更新確認
echo "✅ 更新後の証明書確認:"
sudo kubeadm certs check-expiration | head -5

echo "📝 注意: 証明書更新後は各マスターノードでkubeletとcontainerdの再起動が必要です"
```

## Phase 6: クリーンアップとコスト管理

### 6.1 リソースクリーンアップ

```bash
#!/bin/bash
# スクリプト: cleanup-cluster.sh

echo "🧹 Kubernetesクラスター完全クリーンアップ中..."

# ワーカーノードからの離脱
echo "👋 ワーカーノードをクラスターから除外中..."
WORKER_NODES=$(kubectl get nodes --no-headers | grep -v master | awk '{print $1}')

for node in $WORKER_NODES; do
    echo "ノード $node を削除中..."
    kubectl drain $node --ignore-daemonsets --delete-emptydir-data --force
    kubectl delete node $node
done

# マスターノードでのクラスター停止
echo "🛑 マスターノードでクラスター停止中..."
sudo kubeadm reset --force

# 設定ファイル削除
sudo rm -rf /etc/kubernetes/
sudo rm -rf ~/.kube/
sudo rm -rf /var/lib/kubelet/
sudo rm -rf /var/lib/etcd/

# iptablesルール削除
sudo iptables -F && sudo iptables -t nat -F && sudo iptables -t mangle -F && sudo iptables -X

# containerd停止・削除
sudo systemctl stop containerd
sudo systemctl disable containerd

echo "✅ ローカルクリーンアップ完了！"
```

### 6.2 AWS リソース削除

```bash
#!/bin/bash
# スクリプト: cleanup-aws-infrastructure.sh

echo "☁️ AWS インフラストラクチャ削除中..."

REGION="us-east-1"

# インスタンス削除
echo "🖥️ EC2インスタンス削除中..."
INSTANCE_IDS=$(aws ec2 describe-instances \
    --filters "Name=tag:Name,Values=k8s-*" \
              "Name=instance-state-name,Values=running" \
    --query 'Reservations[*].Instances[*].InstanceId' \
    --output text \
    --region $REGION)

if [ ! -z "$INSTANCE_IDS" ]; then
    aws ec2 terminate-instances --instance-ids $INSTANCE_IDS --region $REGION
    echo "⏳ インスタンス終了待機中..."
    aws ec2 wait instance-terminated --instance-ids $INSTANCE_IDS --region $REGION
fi

# セキュリティグループ削除
echo "🔒 セキュリティグループ削除中..."
SG_ID=$(aws ec2 describe-security-groups \
    --group-names k8s-cluster-sg \
    --query 'SecurityGroups[0].GroupId' \
    --output text \
    --region $REGION 2>/dev/null)

if [ "$SG_ID" != "None" ] && [ ! -z "$SG_ID" ]; then
    aws ec2 delete-security-group --group-id $SG_ID --region $REGION
fi

echo "✅ AWS インフラストラクチャ削除完了！"

# コスト確認
echo "💰 本ラボの推定コスト："
echo "   - EC2インスタンス (t3.medium × 6): ~$0.0416/時間 × 6 × 実行時間"
echo "   - EBS ストレージ: ~$0.10/GB/月"
echo "   - データ転送: 最小限"
echo "   合計推定: $15-25 (6時間実行の場合)"
```

## 📚 学習のポイント

### CKA試験でのクラスター管理要点

1. **kubeadm コマンドの習熟**
   ```bash
   kubeadm init     # クラスター初期化
   kubeadm join     # ノード追加
   kubeadm reset    # クラスター削除
   kubeadm token    # トークン管理
   kubeadm certs    # 証明書管理
   ```

2. **重要な設定ファイル場所**
   ```
   /etc/kubernetes/manifests/    # 静的Pod定義
   /etc/kubernetes/pki/          # 証明書ファイル
   /var/lib/kubelet/config.yaml  # kubelet設定
   /var/lib/etcd/                # etcdデータ
   ```

3. **トラブルシューティング手順**
   ```bash
   # ノード状態確認
   kubectl get nodes
   kubectl describe node <node-name>
   
   # Pod状態確認
   kubectl get pods -A
   kubectl describe pod <pod-name> -n <namespace>
   
   # ログ確認
   sudo journalctl -u kubelet
   sudo journalctl -u containerd
   ```

## 🎯 次のステップ

**完了したスキル:**
- [x] kubeadm を使用したクラスター構築
- [x] マルチノード構成の理解
- [x] etcd バックアップ・復元
- [x] 証明書管理の基礎
- [x] ノード管理操作

**次のラボ:** [Lab 2: Pod とワークロード管理](./lab02-pods-workloads.md)

**重要な注意:**
CKA試験では、クラスター構築だけでなく、既存クラスターでの運用・保守作業も出題されます。このラボで学んだ基本操作を土台に、より高度な管理技術を習得していきます。