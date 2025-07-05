# CKA Practice Exam 1 - クラスター管理とワークロード

## 📋 試験情報

**時間制限**: 120分  
**問題数**: 17問  
**合格点**: 66%  
**環境**: Kubernetes v1.28  

**重要な注意事項:**
- 実際のKubernetesクラスターでの実技試験です
- 各問題で指定されたクラスターとnamespaceを使用してください
- すべてのYAMLマニフェストは`/opt/candidate/`に保存してください
- 試験中は [kubernetes.io](https://kubernetes.io) のドキュメントが参照可能です

---

## 🎯 Question 1: クラスター情報確認 (2%)

**Context**: cluster: k8s-cluster-1  
**Task**: 
クラスターの詳細情報を確認し、以下の情報を`/opt/candidate/cluster-info.txt`に保存してください：
- クラスター内のノード数
- 各ノードのKubernetesバージョン
- 各ノードの内部IP
- マスターノードのクラスターIP

<details>
<summary>💡 解答例</summary>

```bash
# クラスター情報を確認
kubectl cluster-info

# ノード情報を確認
kubectl get nodes -o wide

# ノード詳細情報をファイルに保存
echo "=== Cluster Information ===" > /opt/candidate/cluster-info.txt
echo "Total Nodes: $(kubectl get nodes --no-headers | wc -l)" >> /opt/candidate/cluster-info.txt
echo "" >> /opt/candidate/cluster-info.txt

echo "=== Node Details ===" >> /opt/candidate/cluster-info.txt
kubectl get nodes -o custom-columns=NAME:.metadata.name,VERSION:.status.nodeInfo.kubeletVersion,INTERNAL-IP:.status.addresses[?(@.type==\"InternalIP\")].address --no-headers >> /opt/candidate/cluster-info.txt

echo "" >> /opt/candidate/cluster-info.txt
echo "=== Master Node Cluster IP ===" >> /opt/candidate/cluster-info.txt
kubectl cluster-info | grep "Kubernetes control plane" >> /opt/candidate/cluster-info.txt
```

**採点ポイント:**
- ノード数の正確な記録 (25%)
- Kubernetesバージョンの記録 (25%)
- 内部IPアドレスの記録 (25%)
- マスターノードクラスターIPの記録 (25%)
</details>

---

## 🎯 Question 2: etcdバックアップ作成 (7%)

**Context**: cluster: k8s-cluster-1  
**Task**: 
etcdクラスターのスナップショットを作成し、`/opt/candidate/etcd-backup.db`として保存してください。
etcdは `https://127.0.0.1:2379` でリッスンしており、以下の証明書を使用してください：
- CA証明書: `/etc/kubernetes/pki/etcd/ca.crt`
- Client証明書: `/etc/kubernetes/pki/etcd/server.crt`
- Client秘密鍵: `/etc/kubernetes/pki/etcd/server.key`

<details>
<summary>💡 解答例</summary>

```bash
# etcdctl がインストールされているか確認
which etcdctl

# etcdctl がない場合は、etcd pod内で実行
kubectl exec -it etcd-<master-node-name> -n kube-system -- sh

# etcdバックアップの作成
ETCDCTL_API=3 etcdctl snapshot save /opt/candidate/etcd-backup.db \
  --endpoints=https://127.0.0.1:2379 \
  --cacert=/etc/kubernetes/pki/etcd/ca.crt \
  --cert=/etc/kubernetes/pki/etcd/server.crt \
  --key=/etc/kubernetes/pki/etcd/server.key

# バックアップの検証
ETCDCTL_API=3 etcdctl snapshot status /opt/candidate/etcd-backup.db --write-out=table
```

**採点ポイント:**
- 正しいetcdctl APIバージョンの使用 (20%)
- 正しいエンドポイントの指定 (20%)
- 正しい証明書ファイルの使用 (30%)
- 指定されたパスでのバックアップファイル作成 (30%)
</details>

---

## 🎯 Question 3: ワーカーノードの追加 (8%)

**Context**: cluster: k8s-cluster-1  
**Task**: 
新しいワーカーノード `worker-node-new` をクラスターに追加してください。
ノードは事前に準備されており、必要なコンポーネント（kubelet、kubeadm、kubectl）がインストール済みです。
追加後、ノードが `Ready` 状態になることを確認してください。

<details>
<summary>💡 解答例</summary>

```bash
# マスターノードでjoinコマンドを生成
kubeadm token create --print-join-command

# または、既存のトークンを確認
kubeadm token list

# CA証明書ハッシュを取得（必要な場合）
openssl x509 -pubkey -in /etc/kubernetes/pki/ca.crt | openssl rsa -pubin -outform der 2>/dev/null | openssl dgst -sha256 -hex | sed 's/^.* //'

# worker-node-new にSSHして、joinコマンドを実行
ssh worker-node-new
sudo kubeadm join <master-ip>:6443 --token <token> --discovery-token-ca-cert-hash sha256:<hash>

# マスターノードでノード追加を確認
kubectl get nodes

# ノードがReady状態になるまで待機
kubectl wait --for=condition=Ready node/worker-node-new --timeout=300s
```

**採点ポイント:**
- 正しいjoinコマンドの生成と実行 (40%)
- ノードがクラスターに正常に追加 (40%)
- ノードがReady状態になること (20%)
</details>

---

## 🎯 Question 4: Deploymentの作成と管理 (5%)

**Context**: cluster: k8s-cluster-1, namespace: web-app  
**Task**: 
`web-app` namespaceに以下の要件でDeploymentを作成してください：
- 名前: `nginx-deployment`
- イメージ: `nginx:1.20`
- レプリカ数: 3
- リソース要求: CPU 100m, メモリ 128Mi
- リソース制限: CPU 500m, メモリ 256Mi
- ポート: 80

作成後、レプリカ数を5に増やしてください。

<details>
<summary>💡 解答例</summary>

```bash
# namespaceを作成（存在しない場合）
kubectl create namespace web-app

# Deploymentを作成
kubectl create deployment nginx-deployment --image=nginx:1.20 -n web-app

# Deploymentの設定を更新（リソース要求・制限、レプリカ数）
kubectl patch deployment nginx-deployment -n web-app -p '{
  "spec": {
    "replicas": 3,
    "template": {
      "spec": {
        "containers": [{
          "name": "nginx",
          "resources": {
            "requests": {
              "cpu": "100m",
              "memory": "128Mi"
            },
            "limits": {
              "cpu": "500m",
              "memory": "256Mi"
            }
          },
          "ports": [{
            "containerPort": 80
          }]
        }]
      }
    }
  }
}'

# または、YAMLファイルを作成
cat <<EOF > /opt/candidate/nginx-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: nginx-deployment
  namespace: web-app
spec:
  replicas: 3
  selector:
    matchLabels:
      app: nginx-deployment
  template:
    metadata:
      labels:
        app: nginx-deployment
    spec:
      containers:
      - name: nginx
        image: nginx:1.20
        ports:
        - containerPort: 80
        resources:
          requests:
            cpu: "100m"
            memory: "128Mi"
          limits:
            cpu: "500m"
            memory: "256Mi"
EOF

kubectl apply -f /opt/candidate/nginx-deployment.yaml

# レプリカ数を5に増やす
kubectl scale deployment nginx-deployment --replicas=5 -n web-app

# 結果確認
kubectl get deployment nginx-deployment -n web-app
kubectl get pods -n web-app
```

**採点ポイント:**
- 正しいnamespaceでのDeployment作成 (20%)
- 指定されたイメージとレプリカ数 (20%)
- 正しいリソース要求と制限 (30%)
- スケーリング操作の実行 (30%)
</details>

---

## 🎯 Question 5: ServiceとEndpointの作成 (4%)

**Context**: cluster: k8s-cluster-1, namespace: web-app  
**Task**: 
前の問題で作成した `nginx-deployment` に対してServiceを作成してください：
- 名前: `nginx-service`
- タイプ: ClusterIP
- ポート: 80
- ターゲットポート: 80

Serviceが正しく動作していることを確認し、エンドポイント情報を確認してください。

<details>
<summary>💡 解答例</summary>

```bash
# Serviceを作成
kubectl expose deployment nginx-deployment --name=nginx-service --port=80 --target-port=80 --type=ClusterIP -n web-app

# または、YAMLファイルで作成
cat <<EOF > /opt/candidate/nginx-service.yaml
apiVersion: v1
kind: Service
metadata:
  name: nginx-service
  namespace: web-app
spec:
  selector:
    app: nginx-deployment
  ports:
  - port: 80
    targetPort: 80
  type: ClusterIP
EOF

kubectl apply -f /opt/candidate/nginx-service.yaml

# Service確認
kubectl get service nginx-service -n web-app

# Endpoint確認
kubectl get endpoints nginx-service -n web-app

# Service動作確認
kubectl run test-pod --image=busybox:1.35 --rm -it -n web-app -- wget -qO- nginx-service:80
```

**採点ポイント:**
- 正しい名前とnamespaceでのService作成 (30%)
- 正しいポート設定 (25%)
- 正しいServiceタイプ (20%)
- エンドポイントの正常な確認 (25%)
</details>

---

## 🎯 Question 6: DaemonSetの作成 (6%)

**Context**: cluster: k8s-cluster-1, namespace: monitoring  
**Task**: 
`monitoring` namespaceに以下の要件でDaemonSetを作成してください：
- 名前: `node-monitor`
- イメージ: `busybox:1.35`
- コマンド: `['sh', '-c', 'while true; do date; sleep 30; done']`
- すべてのノード（マスターノードを含む）で実行される
- hostPathボリューム `/var/log` を `/host/var/log` にマウント

<details>
<summary>💡 解答例</summary>

```bash
# namespaceを作成
kubectl create namespace monitoring

# DaemonSet YAMLファイルを作成
cat <<EOF > /opt/candidate/node-monitor-daemonset.yaml
apiVersion: apps/v1
kind: DaemonSet
metadata:
  name: node-monitor
  namespace: monitoring
  labels:
    app: node-monitor
spec:
  selector:
    matchLabels:
      app: node-monitor
  template:
    metadata:
      labels:
        app: node-monitor
    spec:
      tolerations:
      - key: node-role.kubernetes.io/control-plane
        operator: Exists
        effect: NoSchedule
      - key: node-role.kubernetes.io/master
        operator: Exists
        effect: NoSchedule
      containers:
      - name: monitor
        image: busybox:1.35
        command: ['sh', '-c', 'while true; do date; sleep 30; done']
        volumeMounts:
        - name: varlog
          mountPath: /host/var/log
          readOnly: true
      volumes:
      - name: varlog
        hostPath:
          path: /var/log
EOF

# DaemonSetを適用
kubectl apply -f /opt/candidate/node-monitor-daemonset.yaml

# 結果確認
kubectl get daemonset -n monitoring
kubectl get pods -n monitoring -o wide
```

**採点ポイント:**
- 正しいnamespaceでのDaemonSet作成 (20%)
- 指定されたイメージとコマンド (25%)
- マスターノードでの実行設定（tolerations） (30%)
- 正しいhostPathボリュームマウント (25%)
</details>

---

## 🎯 Question 7: StatefulSetの作成 (7%)

**Context**: cluster: k8s-cluster-1, namespace: database  
**Task**: 
`database` namespaceに以下の要件でStatefulSetを作成してください：
- 名前: `mysql-sts`
- イメージ: `mysql:8.0`
- レプリカ数: 2
- 環境変数: `MYSQL_ROOT_PASSWORD=root123`
- 永続ボリューム要求: 10Gi、ReadWriteOnce
- サービス名: `mysql-headless`（Headlessサービス）

<details>
<summary>💡 解答例</summary>

```bash
# namespaceを作成
kubectl create namespace database

# Headlessサービスを作成
cat <<EOF > /opt/candidate/mysql-headless-service.yaml
apiVersion: v1
kind: Service
metadata:
  name: mysql-headless
  namespace: database
spec:
  clusterIP: None
  selector:
    app: mysql-sts
  ports:
  - port: 3306
    targetPort: 3306
EOF

# StatefulSetを作成
cat <<EOF > /opt/candidate/mysql-statefulset.yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: mysql-sts
  namespace: database
spec:
  serviceName: mysql-headless
  replicas: 2
  selector:
    matchLabels:
      app: mysql-sts
  template:
    metadata:
      labels:
        app: mysql-sts
    spec:
      containers:
      - name: mysql
        image: mysql:8.0
        env:
        - name: MYSQL_ROOT_PASSWORD
          value: root123
        ports:
        - containerPort: 3306
        volumeMounts:
        - name: mysql-storage
          mountPath: /var/lib/mysql
  volumeClaimTemplates:
  - metadata:
      name: mysql-storage
    spec:
      accessModes: ["ReadWriteOnce"]
      resources:
        requests:
          storage: 10Gi
EOF

# 適用
kubectl apply -f /opt/candidate/mysql-headless-service.yaml
kubectl apply -f /opt/candidate/mysql-statefulset.yaml

# 結果確認
kubectl get statefulset -n database
kubectl get pods -n database
kubectl get pvc -n database
```

**採点ポイント:**
- 正しいnamespaceでのStatefulSet作成 (20%)
- 指定されたイメージと環境変数 (25%)
- 正しいレプリカ数 (15%)
- 永続ボリューム要求の設定 (25%)
- Headlessサービスの作成 (15%)
</details>

---

## 🎯 Question 8: Jobの作成と管理 (5%)

**Context**: cluster: k8s-cluster-1, namespace: batch  
**Task**: 
`batch` namespaceに以下の要件でJobを作成してください：
- 名前: `pi-calculation`
- イメージ: `perl:5.34`
- コマンド: `["perl", "-Mbignum=bpi", "-wle", "print bpi(2000)"]`
- 完了回数: 1
- 再試行制限: 3回
- TTL: 300秒（完了後300秒で自動削除）

<details>
<summary>💡 解答例</summary>

```bash
# namespaceを作成
kubectl create namespace batch

# Job YAMLファイルを作成
cat <<EOF > /opt/candidate/pi-calculation-job.yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: pi-calculation
  namespace: batch
spec:
  completions: 1
  parallelism: 1
  backoffLimit: 3
  ttlSecondsAfterFinished: 300
  template:
    spec:
      restartPolicy: Never
      containers:
      - name: pi
        image: perl:5.34
        command: ["perl", "-Mbignum=bpi", "-wle", "print bpi(2000)"]
EOF

# Jobを適用
kubectl apply -f /opt/candidate/pi-calculation-job.yaml

# Job状態確認
kubectl get job -n batch
kubectl describe job pi-calculation -n batch

# Job完了確認
kubectl wait --for=condition=complete job/pi-calculation -n batch --timeout=300s

# Jobログ確認
POD_NAME=$(kubectl get pods -n batch -l job-name=pi-calculation -o jsonpath='{.items[0].metadata.name}')
kubectl logs $POD_NAME -n batch
```

**採点ポイント:**
- 正しいnamespaceでのJob作成 (20%)
- 指定されたイメージとコマンド (30%)
- 正しい完了回数と再試行制限 (25%)
- TTL設定 (25%)
</details>

---

## 🎯 Question 9: CronJobの作成 (4%)

**Context**: cluster: k8s-cluster-1, namespace: batch  
**Task**: 
`batch` namespaceに以下の要件でCronJobを作成してください：
- 名前: `cleanup-job`
- スケジュール: 毎日午前3時（`0 3 * * *`）
- イメージ: `alpine:3.18`
- コマンド: `['sh', '-c', 'echo "Cleanup completed at $(date)"']`
- 成功履歴保持: 3個
- 失敗履歴保持: 1個

<details>
<summary>💡 解答例</summary>

```bash
# CronJob YAMLファイルを作成
cat <<EOF > /opt/candidate/cleanup-cronjob.yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: cleanup-job
  namespace: batch
spec:
  schedule: "0 3 * * *"
  successfulJobsHistoryLimit: 3
  failedJobsHistoryLimit: 1
  jobTemplate:
    spec:
      template:
        spec:
          restartPolicy: OnFailure
          containers:
          - name: cleanup
            image: alpine:3.18
            command: ['sh', '-c', 'echo "Cleanup completed at $(date)"']
EOF

# CronJobを適用
kubectl apply -f /opt/candidate/cleanup-cronjob.yaml

# CronJob確認
kubectl get cronjob -n batch
kubectl describe cronjob cleanup-job -n batch

# 手動でJobを作成してテスト
kubectl create job --from=cronjob/cleanup-job manual-cleanup -n batch
```

**採点ポイント:**
- 正しいnamespaceでのCronJob作成 (25%)
- 正しいスケジュール設定 (25%)
- 指定されたイメージとコマンド (25%)
- 履歴保持設定 (25%)
</details>

---

## 🎯 Question 10: ノードのメンテナンス (8%)

**Context**: cluster: k8s-cluster-1  
**Task**: 
ワーカーノード `worker-node-1` をメンテナンスのために準備してください：
1. ノードを安全にドレインし、すべてのPodを他のノードに移行
2. ノードをスケジュール不可に設定
3. メンテナンス完了後、ノードを再びスケジュール可能に戻す

<details>
<summary>💡 解答例</summary>

```bash
# 現在のノード状態を確認
kubectl get nodes

# ノードをスケジュール不可に設定
kubectl cordon worker-node-1

# ノード上のPodを確認
kubectl get pods --all-namespaces -o wide | grep worker-node-1

# ノードを安全にドレイン
kubectl drain worker-node-1 --ignore-daemonsets --delete-emptydir-data --force

# ドレイン完了確認
kubectl get pods --all-namespaces -o wide | grep worker-node-1

# ノード状態確認
kubectl get nodes

# メンテナンス完了後、ノードを再びスケジュール可能に設定
kubectl uncordon worker-node-1

# 最終状態確認
kubectl get nodes
```

**採点ポイント:**
- 正しいcordon操作 (25%)
- 適切なdrainオプションの使用 (40%)
- メンテナンス後のuncordon操作 (25%)
- 操作前後の状態確認 (10%)
</details>

---

## 🎯 Question 11: Pod間通信のトラブルシューティング (8%)

**Context**: cluster: k8s-cluster-1, namespace: debug  
**Task**: 
`debug` namespaceに2つのPodがあります：`app-pod` と `db-pod`。
`app-pod` から `db-pod` への通信ができません。
問題を特定し、修正してください。通信は port 3306 で行われる必要があります。

```bash
# 事前セットアップ（問題再現用）
kubectl create namespace debug

# 問題のあるPodを作成
kubectl run app-pod --image=busybox:1.35 --command -n debug -- sleep 3600
kubectl run db-pod --image=mysql:8.0 -n debug --env="MYSQL_ROOT_PASSWORD=password"

# 意図的に間違ったServiceを作成
kubectl expose pod db-pod --port=3305 --target-port=3306 -n debug
```

<details>
<summary>💡 解答例</summary>

```bash
# 問題の調査開始
kubectl get pods -n debug
kubectl get services -n debug

# app-podから db-podへの接続テスト
kubectl exec app-pod -n debug -- nc -zv db-pod 3306
kubectl exec app-pod -n debug -- nc -zv db-pod 3305

# db-podの状態確認
kubectl describe pod db-pod -n debug
kubectl logs db-pod -n debug

# Serviceの確認
kubectl describe service db-pod -n debug

# 問題発見：Serviceのポートが間違っている（3305 instead of 3306）
# Serviceを修正
kubectl patch service db-pod -n debug -p '{"spec":{"ports":[{"port":3306,"targetPort":3306}]}}'

# または、Serviceを削除して再作成
kubectl delete service db-pod -n debug
kubectl expose pod db-pod --port=3306 --target-port=3306 -n debug

# 修正後の接続テスト
kubectl exec app-pod -n debug -- nc -zv db-pod 3306

# 最終確認
kubectl get service db-pod -n debug
kubectl describe service db-pod -n debug
```

**採点ポイント:**
- 問題の正確な特定 (40%)
- 適切な調査手順 (30%)
- 正しい修正方法 (20%)
- 修正後の動作確認 (10%)
</details>

---

## 🎯 Question 12: リソース使用量の監視 (4%)

**Context**: cluster: k8s-cluster-1  
**Task**: 
クラスター内で最もCPUを使用しているPodを特定し、以下の情報を`/opt/candidate/high-cpu-pods.txt`に保存してください：
- Pod名
- Namespace
- CPU使用量
- メモリ使用量

上位5つのPodの情報を記録してください。

<details>
<summary>💡 解答例</summary>

```bash
# メトリクスサーバーが動作しているか確認
kubectl get pods -n kube-system | grep metrics-server

# 全PodのCPU使用量を確認
kubectl top pods --all-namespaces --sort-by=cpu

# 上位5つのPodをファイルに保存
echo "=== Top 5 CPU-consuming Pods ===" > /opt/candidate/high-cpu-pods.txt
echo "$(date)" >> /opt/candidate/high-cpu-pods.txt
echo "" >> /opt/candidate/high-cpu-pods.txt

kubectl top pods --all-namespaces --sort-by=cpu --no-headers | head -5 | while read namespace pod cpu memory; do
    echo "Pod: $pod" >> /opt/candidate/high-cpu-pods.txt
    echo "Namespace: $namespace" >> /opt/candidate/high-cpu-pods.txt
    echo "CPU Usage: $cpu" >> /opt/candidate/high-cpu-pods.txt
    echo "Memory Usage: $memory" >> /opt/candidate/high-cpu-pods.txt
    echo "---" >> /opt/candidate/high-cpu-pods.txt
done

# 結果確認
cat /opt/candidate/high-cpu-pods.txt
```

**採点ポイント:**
- 正しいメトリクス取得コマンドの使用 (30%)
- CPU使用量による正しいソート (25%)
- 指定されたファイル形式での保存 (25%)
- 上位5つのPodの正確な特定 (20%)
</details>

---

## 🎯 Question 13: NetworkPolicyの作成 (6%)

**Context**: cluster: k8s-cluster-1, namespace: secure-app  
**Task**: 
`secure-app` namespaceにNetworkPolicyを作成し、以下のルールを実装してください：
- 名前: `deny-all-ingress`
- すべての入力トラフィックを拒否
- ただし、`app: frontend` ラベルを持つPodからの port 8080 への接続は許可

<details>
<summary>💡 解答例</summary>

```bash
# namespaceを作成
kubectl create namespace secure-app

# NetworkPolicy YAMLファイルを作成
cat <<EOF > /opt/candidate/deny-all-ingress-policy.yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: deny-all-ingress
  namespace: secure-app
spec:
  podSelector: {}
  policyTypes:
  - Ingress
  ingress:
  - from:
    - podSelector:
        matchLabels:
          app: frontend
    ports:
    - protocol: TCP
      port: 8080
EOF

# NetworkPolicyを適用
kubectl apply -f /opt/candidate/deny-all-ingress-policy.yaml

# NetworkPolicy確認
kubectl get networkpolicy -n secure-app
kubectl describe networkpolicy deny-all-ingress -n secure-app

# テスト用Podを作成
kubectl run backend-pod --image=nginx:1.20 -n secure-app
kubectl run frontend-pod --image=busybox:1.35 --labels="app=frontend" -n secure-app --command -- sleep 3600
kubectl run unauthorized-pod --image=busybox:1.35 -n secure-app --command -- sleep 3600

# 接続テスト
# frontend-podから接続（許可されるべき）
kubectl exec frontend-pod -n secure-app -- nc -zv backend-pod 8080

# unauthorized-podから接続（拒否されるべき）
kubectl exec unauthorized-pod -n secure-app -- nc -zv backend-pod 8080
```

**採点ポイント:**
- 正しいnamespaceでのNetworkPolicy作成 (20%)
- 正しいpodSelectorの使用 (25%)
- 適切な入力トラフィック拒否設定 (25%)
- frontendからの例外許可設定 (30%)
</details>

---

## 🎯 Question 14: ログ分析とトラブルシューティング (7%)

**Context**: cluster: k8s-cluster-1, namespace: problem-app  
**Task**: 
`problem-app` namespaceにあるDeployment `failing-app` が正常に動作していません。
問題を特定し、修正してください。修正内容を`/opt/candidate/fix-summary.txt`に記録してください。

```bash
# 問題のあるDeploymentを事前作成
kubectl create namespace problem-app
cat <<EOF | kubectl apply -f -
apiVersion: apps/v1
kind: Deployment
metadata:
  name: failing-app
  namespace: problem-app
spec:
  replicas: 3
  selector:
    matchLabels:
      app: failing-app
  template:
    metadata:
      labels:
        app: failing-app
    spec:
      containers:
      - name: app
        image: nginx:1.20
        ports:
        - containerPort: 80
        livenessProbe:
          httpGet:
            path: /health
            port: 8080  # 間違ったポート
          initialDelaySeconds: 10
          periodSeconds: 5
        readinessProbe:
          httpGet:
            path: /ready
            port: 80
          initialDelaySeconds: 5
          periodSeconds: 5
EOF
```

<details>
<summary>💡 解答例</summary>

```bash
# 問題の調査開始
kubectl get deployments -n problem-app
kubectl get pods -n problem-app
kubectl describe deployment failing-app -n problem-app

# Pod詳細確認
kubectl describe pods -l app=failing-app -n problem-app

# Podログ確認
kubectl logs -l app=failing-app -n problem-app

# イベント確認
kubectl get events -n problem-app --sort-by=.metadata.creationTimestamp

# 問題発見：livenessProbeのポートが間違っている
# Deploymentを修正
kubectl patch deployment failing-app -n problem-app -p '{
  "spec": {
    "template": {
      "spec": {
        "containers": [{
          "name": "app",
          "livenessProbe": {
            "httpGet": {
              "path": "/",
              "port": 80
            }
          },
          "readinessProbe": {
            "httpGet": {
              "path": "/",
              "port": 80
            }
          }
        }]
      }
    }
  }
}'

# 修正後の状態確認
kubectl get pods -n problem-app
kubectl wait --for=condition=Ready pod -l app=failing-app -n problem-app --timeout=300s

# 修正内容をファイルに記録
cat <<EOF > /opt/candidate/fix-summary.txt
Problem Analysis and Fix Summary
================================

Issue Identified:
- Liveness probe was configured with wrong port (8080 instead of 80)
- Readiness probe was using non-existent path (/ready)

Root Cause:
- Nginx container listens on port 80, but liveness probe was checking port 8080
- Nginx default setup doesn't have /ready endpoint

Fix Applied:
- Changed liveness probe port from 8080 to 80
- Changed liveness probe path from /health to /
- Changed readiness probe path from /ready to /

Result:
- All pods are now in Ready state
- Deployment is successfully running with 3/3 replicas
EOF
```

**採点ポイント:**
- 正確な問題特定 (30%)
- 適切な調査手順 (25%)
- 正しい修正実装 (25%)
- 詳細な修正レポート作成 (20%)
</details>

---

## 🎯 Question 15: PersistentVolumeとClaim (6%)

**Context**: cluster: k8s-cluster-1, namespace: storage-test  
**Task**: 
以下の要件でPersistentVolumeとPersistentVolumeClaimを作成してください：

PersistentVolume:
- 名前: `test-pv`
- 容量: 5Gi
- アクセスモード: ReadWriteOnce
- ストレージクラス: manual
- hostPath: `/opt/pvdata`

PersistentVolumeClaim:
- 名前: `test-pvc`
- 容量要求: 3Gi
- アクセスモード: ReadWriteOnce
- ストレージクラス: manual

<details>
<summary>💡 解答例</summary>

```bash
# namespaceを作成
kubectl create namespace storage-test

# PersistentVolume YAMLファイルを作成
cat <<EOF > /opt/candidate/test-pv.yaml
apiVersion: v1
kind: PersistentVolume
metadata:
  name: test-pv
spec:
  capacity:
    storage: 5Gi
  accessModes:
  - ReadWriteOnce
  persistentVolumeReclaimPolicy: Retain
  storageClassName: manual
  hostPath:
    path: /opt/pvdata
EOF

# PersistentVolumeClaim YAMLファイルを作成
cat <<EOF > /opt/candidate/test-pvc.yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: test-pvc
  namespace: storage-test
spec:
  accessModes:
  - ReadWriteOnce
  resources:
    requests:
      storage: 3Gi
  storageClassName: manual
EOF

# PVとPVCを作成
kubectl apply -f /opt/candidate/test-pv.yaml
kubectl apply -f /opt/candidate/test-pvc.yaml

# 状態確認
kubectl get pv test-pv
kubectl get pvc test-pvc -n storage-test

# PVCがPVにバインドされていることを確認
kubectl describe pvc test-pvc -n storage-test
kubectl describe pv test-pv

# テスト用Podを作成してマウント確認
cat <<EOF > /opt/candidate/test-pod.yaml
apiVersion: v1
kind: Pod
metadata:
  name: test-pod
  namespace: storage-test
spec:
  containers:
  - name: test
    image: busybox:1.35
    command: ['sh', '-c', 'echo "Test data" > /mnt/test.txt; sleep 3600']
    volumeMounts:
    - name: test-volume
      mountPath: /mnt
  volumes:
  - name: test-volume
    persistentVolumeClaim:
      claimName: test-pvc
EOF

kubectl apply -f /opt/candidate/test-pod.yaml
kubectl wait --for=condition=Ready pod/test-pod -n storage-test --timeout=300s
```

**採点ポイント:**
- 正しいPV仕様での作成 (30%)
- 正しいPVC仕様での作成 (30%)
- PVとPVCの正常なバインディング (25%)
- 適切なストレージクラスの設定 (15%)
</details>

---

## 🎯 Question 16: RBAC設定 (8%)

**Context**: cluster: k8s-cluster-1, namespace: rbac-test  
**Task**: 
以下の要件でRBAC設定を作成してください：
- ServiceAccount: `dev-user`
- Role: `pod-reader` (podの読み取り権限のみ)
- RoleBinding: `dev-user-binding` (dev-userにpod-readerロールを付与)
- namespace: `rbac-test`

設定後、権限をテストしてください。

<details>
<summary>💡 解答例</summary>

```bash
# namespaceを作成
kubectl create namespace rbac-test

# ServiceAccountを作成
kubectl create serviceaccount dev-user -n rbac-test

# Role YAMLファイルを作成
cat <<EOF > /opt/candidate/pod-reader-role.yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: pod-reader
  namespace: rbac-test
rules:
- apiGroups: [""]
  resources: ["pods"]
  verbs: ["get", "list", "watch"]
EOF

# RoleBinding YAMLファイルを作成
cat <<EOF > /opt/candidate/dev-user-binding.yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: dev-user-binding
  namespace: rbac-test
subjects:
- kind: ServiceAccount
  name: dev-user
  namespace: rbac-test
roleRef:
  kind: Role
  name: pod-reader
  apiGroup: rbac.authorization.k8s.io
EOF

# RoleとRoleBindingを適用
kubectl apply -f /opt/candidate/pod-reader-role.yaml
kubectl apply -f /opt/candidate/dev-user-binding.yaml

# 確認
kubectl get serviceaccount dev-user -n rbac-test
kubectl get role pod-reader -n rbac-test
kubectl get rolebinding dev-user-binding -n rbac-test

# 権限テスト用のPodを作成
kubectl run test-pod --image=nginx:1.20 -n rbac-test

# dev-userの権限をテスト
# Pod読み取り権限（許可されるべき）
kubectl auth can-i get pods --as=system:serviceaccount:rbac-test:dev-user -n rbac-test

# Pod作成権限（拒否されるべき）
kubectl auth can-i create pods --as=system:serviceaccount:rbac-test:dev-user -n rbac-test

# Service読み取り権限（拒否されるべき）
kubectl auth can-i get services --as=system:serviceaccount:rbac-test:dev-user -n rbac-test
```

**採点ポイント:**
- ServiceAccountの正しい作成 (20%)
- Roleの適切な権限設定 (30%)
- RoleBindingの正しい設定 (30%)
- 権限テストの実行と確認 (20%)
</details>

---

## 🎯 Question 17: クラスター証明書の更新 (5%)

**Context**: cluster: k8s-cluster-1  
**Task**: 
Kubernetesクラスターの証明書の有効期限を確認し、API Serverの証明書を更新してください。
更新前後の有効期限を`/opt/candidate/cert-renewal.txt`に記録してください。

<details>
<summary>💡 解答例</summary>

```bash
# 証明書有効期限確認
echo "=== Certificate Expiration Check (Before Renewal) ===" > /opt/candidate/cert-renewal.txt
echo "$(date)" >> /opt/candidate/cert-renewal.txt
echo "" >> /opt/candidate/cert-renewal.txt

kubeadm certs check-expiration >> /opt/candidate/cert-renewal.txt

echo "" >> /opt/candidate/cert-renewal.txt
echo "=== API Server Certificate Details (Before) ===" >> /opt/candidate/cert-renewal.txt
openssl x509 -in /etc/kubernetes/pki/apiserver.crt -text -noout | grep -A 2 "Validity" >> /opt/candidate/cert-renewal.txt

# 証明書のバックアップ
sudo cp -r /etc/kubernetes/pki /etc/kubernetes/pki-backup-$(date +%Y%m%d_%H%M%S)

# API Server証明書を更新
sudo kubeadm certs renew apiserver

# 更新後の確認
echo "" >> /opt/candidate/cert-renewal.txt
echo "=== Certificate Expiration Check (After Renewal) ===" >> /opt/candidate/cert-renewal.txt
echo "$(date)" >> /opt/candidate/cert-renewal.txt

kubeadm certs check-expiration >> /opt/candidate/cert-renewal.txt

echo "" >> /opt/candidate/cert-renewal.txt
echo "=== API Server Certificate Details (After) ===" >> /opt/candidate/cert-renewal.txt
openssl x509 -in /etc/kubernetes/pki/apiserver.crt -text -noout | grep -A 2 "Validity" >> /opt/candidate/cert-renewal.txt

# kubeletとcontainerdの再起動
sudo systemctl restart kubelet
sudo systemctl restart containerd

# クラスター接続確認
kubectl cluster-info
kubectl get nodes

echo "" >> /opt/candidate/cert-renewal.txt
echo "=== Cluster Status After Renewal ===" >> /opt/candidate/cert-renewal.txt
kubectl get nodes >> /opt/candidate/cert-renewal.txt

# 結果確認
cat /opt/candidate/cert-renewal.txt
```

**採点ポイント:**
- 証明書有効期限の正確な確認 (25%)
- 適切な証明書バックアップ (20%)
- 正しい証明書更新コマンドの実行 (30%)
- 更新前後の比較記録 (25%)
</details>

---

## 📊 採点基準

| 問題番号 | 配点 | 分野 |
|----------|------|------|
| Q1 | 2% | クラスター管理 |
| Q2 | 7% | etcdバックアップ |
| Q3 | 8% | ノード管理 |
| Q4 | 5% | ワークロード管理 |
| Q5 | 4% | サービス管理 |
| Q6 | 6% | DaemonSet |
| Q7 | 7% | StatefulSet |
| Q8 | 5% | Job管理 |
| Q9 | 4% | CronJob |
| Q10 | 8% | ノードメンテナンス |
| Q11 | 8% | トラブルシューティング |
| Q12 | 4% | 監視・メトリクス |
| Q13 | 6% | ネットワークセキュリティ |
| Q14 | 7% | 問題解決 |
| Q15 | 6% | ストレージ管理 |
| Q16 | 8% | RBAC・セキュリティ |
| Q17 | 5% | 証明書管理 |
| **合計** | **100%** | |

**合格ライン**: 66%以上

---

## 🎯 試験後の振り返り

練習試験完了後、以下を確認してください：

1. **時間管理**: 120分以内に完了できたか
2. **正解率**: 66%以上達成できたか  
3. **弱点分野**: 間違った問題の分野を特定
4. **改善点**: 次回に向けての学習ポイント

**次のステップ**: [Practice Exam 2](./practice-exam-02.md) でより高度な問題に挑戦してください。