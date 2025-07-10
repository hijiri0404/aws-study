# CKA トラブルシューティングガイド

## 🎯 概要

CKA試験では、実際のKubernetesクラスターでの問題解決能力が評価されます。このガイドでは、頻出する問題とその解決方法を体系的にまとめています。

**試験での配点**:
- Troubleshooting: 30%（最大の配点）
- 実践的な問題解決スキルが重要

---

## 🔍 トラブルシューティングの基本原則

### 1. 体系的なアプローチ

```
問題発生
    ↓
現状把握（症状の確認）
    ↓
情報収集（ログ、イベント、設定）
    ↓
仮説立案（原因の推測）
    ↓
検証・修正
    ↓
動作確認
```

### 2. 基本的な調査コマンド

```bash
# クラスター全体の状態確認
kubectl cluster-info
kubectl get nodes
kubectl get componentstatuses

# 名前空間内のリソース確認
kubectl get all -n <namespace>
kubectl get events -n <namespace> --sort-by=.metadata.creationTimestamp

# 詳細情報とログ確認
kubectl describe <resource> <name> -n <namespace>
kubectl logs <pod-name> -c <container-name> -n <namespace>
```

---

## 🏗️ クラスターレベルの問題

### Issue 1: ノードが NotReady 状態

#### 症状
```bash
$ kubectl get nodes
NAME           STATUS     ROLES    AGE   VERSION
master-node    Ready      master   10d   v1.28.2
worker-node-1  NotReady   <none>   10d   v1.28.2
worker-node-2  Ready      <none>   10d   v1.28.2
```

#### 診断手順

```bash
#!/bin/bash
# スクリプト: diagnose-node-notready.sh

echo "🔍 ノード NotReady 問題の診断開始..."

NODE_NAME="worker-node-1"  # 問題のあるノード名

echo "📊 ノード詳細情報:"
kubectl describe node $NODE_NAME

echo ""
echo "📋 ノード上のPod状態:"
kubectl get pods --all-namespaces -o wide | grep $NODE_NAME

echo ""
echo "⚠️ ノード関連イベント:"
kubectl get events --field-selector involvedObject.name=$NODE_NAME

echo ""
echo "🔧 ノードでの直接確認（SSH必要）:"
echo "ssh $NODE_NAME"
echo "sudo systemctl status kubelet"
echo "sudo journalctl -u kubelet -f"
```

#### よくある原因と解決法

**1. kubelet サービスの問題**
```bash
# ノードにSSH接続
ssh worker-node-1

# kubelet状態確認
sudo systemctl status kubelet

# kubeletログ確認
sudo journalctl -u kubelet -n 50

# kubelet再起動
sudo systemctl restart kubelet
sudo systemctl enable kubelet
```

**2. ディスク容量不足**
```bash
# ディスク使用量確認
df -h

# 不要なコンテナイメージ削除
sudo crictl images
sudo crictl rmi <image-id>

# ログファイル削除
sudo journalctl --vacuum-time=7d
```

**3. ネットワーク設定問題**
```bash
# CNIプラグイン状態確認
kubectl get pods -n kube-system | grep -E "flannel|calico|weave"

# CNI設定確認
ls -la /etc/cni/net.d/
cat /etc/cni/net.d/*

# ネットワーク再起動
sudo systemctl restart containerd
```

**4. 証明書期限切れ**
```bash
# 証明書有効期限確認
sudo kubeadm certs check-expiration

# kubelet証明書更新
sudo kubeadm certs renew kubelet-client
sudo systemctl restart kubelet
```

---

### Issue 2: API Server接続不可

#### 症状
```bash
$ kubectl get nodes
The connection to the server localhost:8080 was refused - did you specify the right host or port?
```

#### 診断と解決

```bash
#!/bin/bash
# スクリプト: diagnose-apiserver.sh

echo "🔍 API Server接続問題の診断..."

echo "📋 kube-apiserver Pod状態:"
kubectl get pods -n kube-system | grep kube-apiserver

echo ""
echo "🔧 API Server関連ファイル確認:"
sudo ls -la /etc/kubernetes/manifests/kube-apiserver.yaml

echo ""
echo "📊 API Serverログ確認:"
sudo crictl logs $(sudo crictl ps -a | grep kube-apiserver | awk '{print $1}')

echo ""
echo "🌐 ネットワーク確認:"
sudo netstat -tlnp | grep :6443
sudo ss -tlnp | grep :6443

echo ""
echo "🔐 証明書確認:"
sudo kubeadm certs check-expiration | grep apiserver
```

**解決手順:**

```bash
# 1. マニフェストファイル確認
sudo cat /etc/kubernetes/manifests/kube-apiserver.yaml

# 2. kubelet再起動
sudo systemctl restart kubelet

# 3. API Server手動起動（デバッグ用）
sudo kube-apiserver \
  --advertise-address=192.168.1.10 \
  --allow-privileged=true \
  --authorization-mode=Node,RBAC \
  --client-ca-file=/etc/kubernetes/pki/ca.crt \
  --enable-admission-plugins=NodeRestriction \
  --etcd-servers=https://127.0.0.1:2379 \
  --v=2

# 4. kubeconfig確認
export KUBECONFIG=/etc/kubernetes/admin.conf
kubectl cluster-info
```

---

## 🔧 ワークロード関連の問題

### Issue 3: Pod が Pending 状態

#### 症状
```bash
$ kubectl get pods
NAME           READY   STATUS    RESTARTS   AGE
nginx-pod      0/1     Pending   0          5m
```

#### 診断スクリプト

```bash
#!/bin/bash
# スクリプト: diagnose-pod-pending.sh

POD_NAME="nginx-pod"
NAMESPACE="default"

echo "🔍 Pod Pending 問題の診断..."

echo "📊 Pod詳細情報:"
kubectl describe pod $POD_NAME -n $NAMESPACE

echo ""
echo "📋 ノードリソース確認:"
kubectl describe nodes

echo ""
echo "⚠️ イベント確認:"
kubectl get events -n $NAMESPACE --sort-by=.metadata.creationTimestamp

echo ""
echo "🏷️ ノードラベル確認:"
kubectl get nodes --show-labels

echo ""
echo "📊 リソース使用量:"
kubectl top nodes
kubectl top pods -A
```

#### よくある原因と解決法

**1. リソース不足**
```yaml
# 問題のあるPod例
apiVersion: v1
kind: Pod
metadata:
  name: high-resource-pod
spec:
  containers:
  - name: app
    image: nginx
    resources:
      requests:
        memory: "8Gi"    # 利用可能メモリを超える要求
        cpu: "4"
```

```bash
# 解決方法
# リソース要求を削減
kubectl patch pod high-resource-pod -p '{
  "spec": {
    "containers": [{
      "name": "app",
      "resources": {
        "requests": {
          "memory": "512Mi",
          "cpu": "500m"
        }
      }
    }]
  }
}'
```

**2. ノードセレクター不一致**
```yaml
# 問題のあるPod例
apiVersion: v1
kind: Pod
metadata:
  name: selective-pod
spec:
  nodeSelector:
    disk-type: ssd    # 該当するノードが存在しない
  containers:
  - name: app
    image: nginx
```

```bash
# 解決方法
# 適切なラベルをノードに追加
kubectl label node worker-node-1 disk-type=ssd

# または、nodeSelector を削除
kubectl patch pod selective-pod -p '{"spec":{"nodeSelector":null}}'
```

**3. PersistentVolumeClaim 不具合**
```bash
# PVC状態確認
kubectl get pvc

# PV状態確認
kubectl get pv

# StorageClass確認
kubectl get storageclass

# 動的プロビジョニング用のStorageClass作成
cat <<EOF | kubectl apply -f -
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: local-storage
provisioner: kubernetes.io/no-provisioner
volumeBindingMode: WaitForFirstConsumer
EOF
```

---

### Issue 4: Pod が CrashLoopBackOff 状態

#### 症状
```bash
$ kubectl get pods
NAME           READY   STATUS             RESTARTS   AGE
crashing-pod   0/1     CrashLoopBackOff   5          5m
```

#### 診断と解決

```bash
#!/bin/bash
# スクリプト: diagnose-crashloop.sh

POD_NAME="crashing-pod"
NAMESPACE="default"

echo "🔍 CrashLoopBackOff 問題の診断..."

echo "📊 Pod詳細情報:"
kubectl describe pod $POD_NAME -n $NAMESPACE

echo ""
echo "📋 現在のログ:"
kubectl logs $POD_NAME -n $NAMESPACE

echo ""
echo "📋 前回のログ:"
kubectl logs $POD_NAME -n $NAMESPACE --previous

echo ""
echo "⚠️ イベント履歴:"
kubectl get events -n $NAMESPACE --field-selector involvedObject.name=$POD_NAME

echo ""
echo "🔧 リソース制限確認:"
kubectl get pod $POD_NAME -n $NAMESPACE -o jsonpath='{.spec.containers[*].resources}'
```

**よくある原因と解決法:**

**1. アプリケーションエラー**
```bash
# ログでエラーメッセージを確認
kubectl logs crashing-pod --previous

# 設定ミスの修正例（環境変数）
kubectl patch deployment app-deployment -p '{
  "spec": {
    "template": {
      "spec": {
        "containers": [{
          "name": "app",
          "env": [{
            "name": "DATABASE_URL",
            "value": "postgresql://user:pass@db:5432/mydb"
          }]
        }]
      }
    }
  }
}'
```

**2. ヘルスチェック設定ミス**
```yaml
# 問題のある設定
apiVersion: v1
kind: Pod
metadata:
  name: health-check-pod
spec:
  containers:
  - name: app
    image: nginx
    livenessProbe:
      httpGet:
        path: /health
        port: 8080    # nginxは80番ポート
      initialDelaySeconds: 5
      periodSeconds: 5
```

```bash
# 修正
kubectl patch pod health-check-pod -p '{
  "spec": {
    "containers": [{
      "name": "app",
      "livenessProbe": {
        "httpGet": {
          "path": "/",
          "port": 80
        }
      }
    }]
  }
}'
```

**3. リソース制限による強制終了**
```bash
# メモリ使用量確認
kubectl top pod crashing-pod

# リソース制限緩和
kubectl patch deployment app-deployment -p '{
  "spec": {
    "template": {
      "spec": {
        "containers": [{
          "name": "app",
          "resources": {
            "limits": {
              "memory": "1Gi",
              "cpu": "1000m"
            }
          }
        }]
      }
    }
  }
}'
```

---

## 🌐 ネットワーク関連の問題

### Issue 5: Service接続不可

#### 症状
```bash
$ kubectl exec test-pod -- curl service-name
curl: (7) Failed to connect to service-name port 80: Connection refused
```

#### 診断スクリプト

```bash
#!/bin/bash
# スクリプト: diagnose-service-connectivity.sh

SERVICE_NAME="web-service"
NAMESPACE="default"

echo "🔍 Service接続問題の診断..."

echo "📊 Service詳細:"
kubectl describe service $SERVICE_NAME -n $NAMESPACE

echo ""
echo "📋 Endpoints確認:"
kubectl get endpoints $SERVICE_NAME -n $NAMESPACE

echo ""
echo "🏷️ Pod label確認:"
kubectl get pods -n $NAMESPACE --show-labels

echo ""
echo "🌐 DNS解決テスト:"
kubectl run dns-test --image=busybox:1.35 --rm -it -- nslookup $SERVICE_NAME

echo ""
echo "🔗 ポート接続テスト:"
kubectl run connectivity-test --image=busybox:1.35 --rm -it -- nc -zv $SERVICE_NAME 80
```

**よくある原因と解決法:**

**1. ラベルセレクターの不一致**
```bash
# Service確認
kubectl get service web-service -o yaml | grep -A 5 selector

# Pod確認
kubectl get pods --show-labels

# ラベル修正
kubectl label pod web-pod app=web-app
```

**2. ポート設定ミス**
```yaml
# 問題のあるService例
apiVersion: v1
kind: Service
metadata:
  name: web-service
spec:
  selector:
    app: web-app
  ports:
  - port: 80
    targetPort: 8080  # アプリが80番ポートで動作
```

```bash
# 修正
kubectl patch service web-service -p '{
  "spec": {
    "ports": [{
      "port": 80,
      "targetPort": 80
    }]
  }
}'
```

**3. NetworkPolicyによる通信ブロック**
```bash
# NetworkPolicy確認
kubectl get networkpolicy -A

# 問題のあるNetworkPolicy削除
kubectl delete networkpolicy deny-all-policy

# または、適切な許可ルール追加
cat <<EOF | kubectl apply -f -
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-web-traffic
spec:
  podSelector:
    matchLabels:
      app: web-app
  policyTypes:
  - Ingress
  ingress:
  - from: []
    ports:
    - protocol: TCP
      port: 80
EOF
```

---

### Issue 6: DNS解決失敗

#### 症状
```bash
$ kubectl exec test-pod -- nslookup kubernetes.default
Server:    10.96.0.10
Address 1: 10.96.0.10
nslookup: can't resolve 'kubernetes.default'
```

#### 診断と解決

```bash
#!/bin/bash
# スクリプト: diagnose-dns.sh

echo "🔍 DNS問題の診断..."

echo "📊 CoreDNS Pod状態:"
kubectl get pods -n kube-system -l k8s-app=kube-dns

echo ""
echo "📋 CoreDNS設定:"
kubectl get configmap coredns -n kube-system -o yaml

echo ""
echo "🔧 CoreDNSログ:"
kubectl logs -n kube-system -l k8s-app=kube-dns

echo ""
echo "🌐 DNS Service確認:"
kubectl get service kube-dns -n kube-system

echo ""
echo "📊 ノードのDNS設定:"
echo "各ノードで以下を確認:"
echo "cat /etc/resolv.conf"
echo "systemctl status systemd-resolved"
```

**解決手順:**

```bash
# 1. CoreDNS再起動
kubectl delete pod -n kube-system -l k8s-app=kube-dns

# 2. CoreDNS設定確認・修正
kubectl edit configmap coredns -n kube-system

# 3. DNSテストPod作成
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: dns-test
spec:
  containers:
  - name: dns-test
    image: busybox:1.35
    command: ['sleep', '3600']
  dnsPolicy: ClusterFirst
EOF

# 4. DNS動作確認
kubectl exec dns-test -- nslookup kubernetes.default
kubectl exec dns-test -- nslookup google.com
```

---

## 💾 ストレージ関連の問題

### Issue 7: PersistentVolumeClaim が Pending

#### 症状
```bash
$ kubectl get pvc
NAME        STATUS    VOLUME   CAPACITY   ACCESS MODES   STORAGECLASS   AGE
data-pvc    Pending                                      fast-ssd       5m
```

#### 診断と解決

```bash
#!/bin/bash
# スクリプト: diagnose-pvc-pending.sh

PVC_NAME="data-pvc"
NAMESPACE="default"

echo "🔍 PVC Pending 問題の診断..."

echo "📊 PVC詳細:"
kubectl describe pvc $PVC_NAME -n $NAMESPACE

echo ""
echo "📋 利用可能PV一覧:"
kubectl get pv

echo ""
echo "🏷️ StorageClass確認:"
kubectl get storageclass

echo ""
echo "⚠️ イベント確認:"
kubectl get events -n $NAMESPACE --field-selector involvedObject.name=$PVC_NAME
```

**よくある原因と解決法:**

**1. StorageClassが存在しない**
```bash
# 利用可能なStorageClass確認
kubectl get storageclass

# StorageClass作成（hostPath例）
cat <<EOF | kubectl apply -f -
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: fast-ssd
provisioner: kubernetes.io/no-provisioner
volumeBindingMode: WaitForFirstConsumer
EOF
```

**2. 適合するPVが存在しない**
```bash
# 手動でPV作成
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: PersistentVolume
metadata:
  name: local-pv-1
spec:
  capacity:
    storage: 10Gi
  accessModes:
  - ReadWriteOnce
  persistentVolumeReclaimPolicy: Retain
  storageClassName: fast-ssd
  hostPath:
    path: /mnt/data
EOF
```

**3. アクセスモードの不一致**
```bash
# PVC要求確認
kubectl get pvc data-pvc -o yaml | grep -A 5 spec

# PV提供内容確認
kubectl get pv -o yaml | grep -A 10 accessModes
```

---

## 🔐 セキュリティ関連の問題

### Issue 8: RBAC権限エラー

#### 症状
```bash
$ kubectl get pods
Error from server (Forbidden): pods is forbidden: User "john" cannot list resource "pods" in API group "" in the namespace "default"
```

#### 診断と解決

```bash
#!/bin/bash
# スクリプト: diagnose-rbac.sh

USER="john"
NAMESPACE="default"

echo "🔍 RBAC権限問題の診断..."

echo "📊 現在のユーザー権限確認:"
kubectl auth can-i list pods --as=$USER -n $NAMESPACE
kubectl auth can-i get pods --as=$USER -n $NAMESPACE
kubectl auth can-i create pods --as=$USER -n $NAMESPACE

echo ""
echo "📋 ユーザーのRoleBinding確認:"
kubectl get rolebinding -n $NAMESPACE -o wide | grep $USER
kubectl get clusterrolebinding -o wide | grep $USER

echo ""
echo "🔧 ServiceAccount確認:"
kubectl get serviceaccount -n $NAMESPACE
```

**解決手順:**

```bash
# 1. 適切なRole作成
cat <<EOF | kubectl apply -f -
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  namespace: default
  name: pod-reader
rules:
- apiGroups: [""]
  resources: ["pods"]
  verbs: ["get", "list", "watch"]
EOF

# 2. RoleBinding作成
cat <<EOF | kubectl apply -f -
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: read-pods
  namespace: default
subjects:
- kind: User
  name: john
  apiGroup: rbac.authorization.k8s.io
roleRef:
  kind: Role
  name: pod-reader
  apiGroup: rbac.authorization.k8s.io
EOF

# 3. 権限確認
kubectl auth can-i list pods --as=john -n default
```

---

## 🔧 実践的なトラブルシューティング演習

### Exercise 1: 総合診断スクリプト

```bash
#!/bin/bash
# スクリプト: comprehensive-cluster-check.sh

echo "🔍 Kubernetes クラスター総合診断開始..."
echo "実行時刻: $(date)"
echo "==========================================="

# 1. クラスター基本状態
echo ""
echo "🏗️ クラスター基本状態:"
kubectl cluster-info
kubectl get componentstatuses

# 2. ノード状態
echo ""
echo "🖥️ ノード状態:"
kubectl get nodes -o wide
kubectl describe nodes | grep -E "Name:|Conditions:" -A 5

# 3. システムPod状態
echo ""
echo "⚙️ システムPod状態:"
kubectl get pods -n kube-system
echo ""
echo "❌ 異常なシステムPod:"
kubectl get pods -n kube-system | grep -v Running | grep -v Completed

# 4. ワークロード状態
echo ""
echo "🚀 ワークロード状態:"
kubectl get pods --all-namespaces | grep -v Running | grep -v Completed | grep -v Succeeded

# 5. サービス状態
echo ""
echo "🌐 サービス接続性:"
kubectl get services --all-namespaces
echo ""
echo "Endpoints確認:"
kubectl get endpoints --all-namespaces | grep -v "10\."

# 6. ストレージ状態
echo ""
echo "💾 ストレージ状態:"
kubectl get pv
kubectl get pvc --all-namespaces | grep -v Bound

# 7. 最近のイベント
echo ""
echo "⚠️ 最近のイベント（警告・エラー）:"
kubectl get events --all-namespaces --sort-by=.metadata.creationTimestamp | grep -E "Warning|Error" | tail -10

# 8. リソース使用量
echo ""
echo "📊 リソース使用量:"
kubectl top nodes 2>/dev/null || echo "メトリクスサーバーが利用できません"
kubectl top pods --all-namespaces --sort-by=cpu 2>/dev/null | head -10

echo ""
echo "✅ 診断完了!"
```

### Exercise 2: 自動修復スクリプト

```bash
#!/bin/bash
# スクリプト: auto-healing.sh

echo "🔧 自動修復スクリプト開始..."

# 1. 再起動が必要なPodの検出と修復
echo "🔄 異常Podの修復中..."
PROBLEMATIC_PODS=$(kubectl get pods --all-namespaces | grep -E "Error|CrashLoopBackOff|ImagePullBackOff" | awk '{print $2 " " $1}')

if [ ! -z "$PROBLEMATIC_PODS" ]; then
    echo "$PROBLEMATIC_PODS" | while read pod namespace; do
        echo "Pod $pod (namespace: $namespace) を再起動中..."
        kubectl delete pod $pod -n $namespace
    done
else
    echo "修復が必要なPodはありません"
fi

# 2. Pending状態のPVCのチェック
echo ""
echo "💾 Pending PVCのチェック..."
PENDING_PVCS=$(kubectl get pvc --all-namespaces | grep Pending | awk '{print $2 " " $1}')

if [ ! -z "$PENDING_PVCS" ]; then
    echo "⚠️ Pending状態のPVCが見つかりました:"
    echo "$PENDING_PVCS"
    echo "手動での確認が必要です"
else
    echo "すべてのPVCは正常です"
fi

# 3. ノードの健全性チェック
echo ""
echo "🖥️ ノードの健全性チェック..."
NOT_READY_NODES=$(kubectl get nodes | grep NotReady | awk '{print $1}')

if [ ! -z "$NOT_READY_NODES" ]; then
    echo "⚠️ NotReady状態のノードが見つかりました:"
    echo "$NOT_READY_NODES"
    echo "ノードレベルでの確認が必要です"
else
    echo "すべてのノードは正常です"
fi

# 4. システムPodの健全性チェック
echo ""
echo "⚙️ システムPodの健全性チェック..."
SYSTEM_ISSUES=$(kubectl get pods -n kube-system | grep -v Running | grep -v Completed | wc -l)

if [ $SYSTEM_ISSUES -gt 0 ]; then
    echo "⚠️ システムPodに問題があります:"
    kubectl get pods -n kube-system | grep -v Running | grep -v Completed
else
    echo "すべてのシステムPodは正常です"
fi

echo ""
echo "✅ 自動修復完了!"
```

---

## 📚 CKA試験のためのトラブルシューティング戦略

### 1. 時間管理

```
問題分析: 2-3分
調査・診断: 5-8分
修正実装: 3-5分
動作確認: 1-2分
合計: 10-15分/問題
```

### 2. 優先順位

1. **簡単で確実な問題**: 基本的な設定ミス
2. **影響範囲の大きい問題**: クラスター全体の機能停止
3. **複雑な問題**: 詳細な調査が必要な問題

### 3. 必須暗記事項

```bash
# よく使うデバッグコマンド
kubectl describe
kubectl logs
kubectl get events
kubectl exec -it

# 重要な設定ファイル場所
/etc/kubernetes/manifests/
/etc/kubernetes/pki/
/var/lib/kubelet/config.yaml
/etc/cni/net.d/
```

### 4. トラブルシューティングチェックリスト

- [ ] 症状の正確な把握
- [ ] 関連リソースの状態確認
- [ ] ログとイベントの分析
- [ ] 設定ファイルの確認
- [ ] ネットワーク接続性の確認
- [ ] リソース使用量の確認
- [ ] 権限設定の確認
- [ ] 修正後の動作確認

---

## 🎯 次のステップ

このトラブルシューティングガイドを活用して：

1. **実践練習**: 意図的に問題を作り、解決する演習
2. **ログ分析**: 各種ログの読み方に慣れる
3. **体系的診断**: 問題発生時の調査手順を身につける
4. **時間管理**: 制限時間内での問題解決練習

**関連リソース:**
- [Practice Exam 1](../practice-exams/practice-exam-01.md): 実践的な問題演習
- [Lab 3: Services とネットワーキング](../labs/lab03-services-networking.md): ネットワーク関連の実践