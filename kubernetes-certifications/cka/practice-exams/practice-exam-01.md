# CKA Practice Exam 1 - クラスター管理とワークロード

## 📋 試験情報

**時間制限**: 120分  
**問題数**: 100問  
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

---

## 🎯 Question 18: Ingress設定 (4%)

**Context**: cluster: k8s-cluster-1, namespace: web-services  
**Task**: 
以下の要件でIngressを作成してください：
- 名前: `web-ingress`
- ホスト: `app.example.com`
- パス `/api` を `api-service:8080` にルーティング
- パス `/web` を `web-service:80` にルーティング
- TLS証明書: `web-tls-secret`

<details>
<summary>💡 解答例</summary>

```bash
# namespaceを作成
kubectl create namespace web-services

# 必要なServiceを作成（テスト用）
kubectl create deployment api-app --image=nginx:1.20 -n web-services
kubectl expose deployment api-app --name=api-service --port=8080 --target-port=80 -n web-services

kubectl create deployment web-app --image=nginx:1.20 -n web-services
kubectl expose deployment web-app --name=web-service --port=80 --target-port=80 -n web-services

# TLS Secretを作成（テスト用の自己証明書）
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout /tmp/tls.key -out /tmp/tls.crt \
  -subj "/CN=app.example.com/O=app.example.com"

kubectl create secret tls web-tls-secret \
  --cert=/tmp/tls.crt --key=/tmp/tls.key -n web-services

# Ingress YAMLファイルを作成
cat <<EOF > /opt/candidate/web-ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: web-ingress
  namespace: web-services
spec:
  tls:
  - hosts:
    - app.example.com
    secretName: web-tls-secret
  rules:
  - host: app.example.com
    http:
      paths:
      - path: /api
        pathType: Prefix
        backend:
          service:
            name: api-service
            port:
              number: 8080
      - path: /web
        pathType: Prefix
        backend:
          service:
            name: web-service
            port:
              number: 80
EOF

# Ingressを適用
kubectl apply -f /opt/candidate/web-ingress.yaml

# 確認
kubectl get ingress -n web-services
kubectl describe ingress web-ingress -n web-services
```

**採点ポイント:**
- 正しいnamespaceでのIngress作成 (25%)
- 適切なホスト設定 (25%)
- 正しいパスルーティング設定 (30%)
- TLS設定 (20%)
</details>

---

## 🎯 Question 19: ConfigMapとSecret管理 (5%)

**Context**: cluster: k8s-cluster-1, namespace: config-test  
**Task**: 
以下を作成してください：
1. ConfigMap `app-config` (key: config.yaml, value: database_url: "localhost:5432")
2. Secret `app-secret` (key: password, value: "secretpass123")
3. Pod `config-pod` でConfigMapを環境変数、Secretをボリュームとしてマウント

<details>
<summary>💡 解答例</summary>

```bash
# namespaceを作成
kubectl create namespace config-test

# ConfigMapを作成
kubectl create configmap app-config \
  --from-literal=config.yaml='database_url: "localhost:5432"' \
  -n config-test

# Secretを作成
kubectl create secret generic app-secret \
  --from-literal=password=secretpass123 \
  -n config-test

# Pod YAMLファイルを作成
cat <<EOF > /opt/candidate/config-pod.yaml
apiVersion: v1
kind: Pod
metadata:
  name: config-pod
  namespace: config-test
spec:
  containers:
  - name: app
    image: busybox:1.35
    command: ['sh', '-c', 'echo "Config: $CONFIG_DATA"; cat /etc/secrets/password; sleep 3600']
    env:
    - name: CONFIG_DATA
      valueFrom:
        configMapKeyRef:
          name: app-config
          key: config.yaml
    volumeMounts:
    - name: secret-volume
      mountPath: /etc/secrets
      readOnly: true
  volumes:
  - name: secret-volume
    secret:
      secretName: app-secret
EOF

# Podを適用
kubectl apply -f /opt/candidate/config-pod.yaml

# 確認
kubectl get configmap app-config -n config-test
kubectl get secret app-secret -n config-test
kubectl get pod config-pod -n config-test
kubectl logs config-pod -n config-test
```

**採点ポイント:**
- ConfigMapの正しい作成 (30%)
- Secretの正しい作成 (30%)
- 環境変数での参照 (20%)
- ボリュームマウント設定 (20%)
</details>

---

## 🎯 Question 20: HorizontalPodAutoscaler設定 (6%)

**Context**: cluster: k8s-cluster-1, namespace: scaling-test  
**Task**: 
以下の要件でHPAを作成してください：
- ターゲット: Deployment `web-app`
- 最小レプリカ: 2
- 最大レプリカ: 10
- CPU使用率: 70%でスケール
- メモリ使用率: 80%でスケール

<details>
<summary>💡 解答例</summary>

```bash
# namespaceを作成
kubectl create namespace scaling-test

# テスト用Deploymentを作成
cat <<EOF > /opt/candidate/web-app-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: web-app
  namespace: scaling-test
spec:
  replicas: 2
  selector:
    matchLabels:
      app: web-app
  template:
    metadata:
      labels:
        app: web-app
    spec:
      containers:
      - name: web
        image: nginx:1.20
        resources:
          requests:
            cpu: 100m
            memory: 64Mi
          limits:
            cpu: 200m
            memory: 128Mi
EOF

kubectl apply -f /opt/candidate/web-app-deployment.yaml

# HPA YAMLファイルを作成
cat <<EOF > /opt/candidate/web-app-hpa.yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: web-app-hpa
  namespace: scaling-test
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: web-app
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
EOF

# HPAを適用
kubectl apply -f /opt/candidate/web-app-hpa.yaml

# 確認
kubectl get hpa -n scaling-test
kubectl describe hpa web-app-hpa -n scaling-test
kubectl get deployment web-app -n scaling-test
```

**採点ポイント:**
- 正しいターゲット指定 (25%)
- 適切なレプリカ数設定 (25%)
- CPU使用率メトリクス設定 (25%)
- メモリ使用率メトリクス設定 (25%)
</details>

---

## 🎯 Question 21: クラスターネットワーキング (7%)

**Context**: cluster: k8s-cluster-1  
**Task**: 
以下の調査を行い、結果を`/opt/candidate/network-info.txt`に保存してください：
1. クラスターのPod CIDR範囲
2. Service CIDR範囲
3. CNI（Container Network Interface）プラグイン名
4. kube-proxyのモード

<details>
<summary>💡 解答例</summary>

```bash
# ネットワーク情報調査
echo "=== Kubernetes Cluster Network Information ===" > /opt/candidate/network-info.txt
echo "$(date)" >> /opt/candidate/network-info.txt
echo "" >> /opt/candidate/network-info.txt

# Pod CIDR範囲を取得
echo "=== Pod CIDR Range ===" >> /opt/candidate/network-info.txt
kubectl cluster-info dump | grep -E "cluster-cidr|pod-cidr" >> /opt/candidate/network-info.txt
kubectl get nodes -o jsonpath='{.items[*].spec.podCIDR}' >> /opt/candidate/network-info.txt
echo "" >> /opt/candidate/network-info.txt

# Service CIDR範囲を取得
echo "=== Service CIDR Range ===" >> /opt/candidate/network-info.txt
kubectl cluster-info dump | grep -E "service-cluster-ip-range" >> /opt/candidate/network-info.txt
echo "" >> /opt/candidate/network-info.txt

# CNIプラグイン確認
echo "=== CNI Plugin Information ===" >> /opt/candidate/network-info.txt
kubectl get pods -n kube-system | grep -E "(calico|flannel|weave|cilium)" >> /opt/candidate/network-info.txt
ls /etc/cni/net.d/ >> /opt/candidate/network-info.txt
echo "" >> /opt/candidate/network-info.txt

# kube-proxyモード確認
echo "=== Kube-proxy Mode ===" >> /opt/candidate/network-info.txt
kubectl get configmap kube-proxy -n kube-system -o yaml | grep mode >> /opt/candidate/network-info.txt
kubectl logs -n kube-system -l k8s-app=kube-proxy | grep -i mode | head -5 >> /opt/candidate/network-info.txt
echo "" >> /opt/candidate/network-info.txt

# その他のネットワーク設定
echo "=== Additional Network Settings ===" >> /opt/candidate/network-info.txt
kubectl get services -A | grep ClusterIP | head -5 >> /opt/candidate/network-info.txt

# 結果確認
cat /opt/candidate/network-info.txt
```

**採点ポイント:**
- Pod CIDR範囲の正確な取得 (25%)
- Service CIDR範囲の取得 (25%)
- CNIプラグインの特定 (25%)
- kube-proxyモードの確認 (25%)
</details>

---

## 🎯 Question 22: カスタムリソース定義 (6%)

**Context**: cluster: k8s-cluster-1  
**Task**: 
以下の要件でCustomResourceDefinitionを作成してください：
- API群: `example.com/v1`
- 種類: `WebService`
- 複数形: `webservices`
- ネームスペース範囲

作成後、カスタムリソースのインスタンスを作成してください。

<details>
<summary>💡 解答例</summary>

```bash
# CRD YAMLファイルを作成
cat <<EOF > /opt/candidate/webservice-crd.yaml
apiVersion: apiextensions.k8s.io/v1
kind: CustomResourceDefinition
metadata:
  name: webservices.example.com
spec:
  group: example.com
  versions:
  - name: v1
    served: true
    storage: true
    schema:
      openAPIV3Schema:
        type: object
        properties:
          spec:
            type: object
            properties:
              replicas:
                type: integer
                minimum: 1
                maximum: 10
              image:
                type: string
              port:
                type: integer
          status:
            type: object
            properties:
              replicas:
                type: integer
  scope: Namespaced
  names:
    plural: webservices
    singular: webservice
    kind: WebService
    shortNames:
    - ws
EOF

# CRDを適用
kubectl apply -f /opt/candidate/webservice-crd.yaml

# CRD確認
kubectl get crd webservices.example.com

# カスタムリソースインスタンスを作成
cat <<EOF > /opt/candidate/my-webservice.yaml
apiVersion: example.com/v1
kind: WebService
metadata:
  name: my-webservice
  namespace: default
spec:
  replicas: 3
  image: nginx:1.20
  port: 80
EOF

kubectl apply -f /opt/candidate/my-webservice.yaml

# 確認
kubectl get webservices
kubectl describe webservice my-webservice
kubectl get ws  # shortNameでのアクセス確認
```

**採点ポイント:**
- 正しいCRD仕様での作成 (40%)
- 適切なスキーマ定義 (30%)
- カスタムリソースインスタンスの作成 (30%)
</details>

---

## 🎯 Question 23: etcdクラスターのトラブルシューティング (8%)

**Context**: cluster: k8s-cluster-1  
**Task**: 
etcdクラスターに問題が発生しています。以下を実行してください：
1. etcdの状態確認
2. メンバー一覧取得
3. 問題があれば修復
4. 修復内容を`/opt/candidate/etcd-repair.txt`に記録

<details>
<summary>💡 解答例</summary>

```bash
# etcd調査開始
echo "=== ETCD Troubleshooting Report ===" > /opt/candidate/etcd-repair.txt
echo "$(date)" >> /opt/candidate/etcd-repair.txt
echo "" >> /opt/candidate/etcd-repair.txt

# etcd Podの状態確認
echo "=== ETCD Pod Status ===" >> /opt/candidate/etcd-repair.txt
kubectl get pods -n kube-system | grep etcd >> /opt/candidate/etcd-repair.txt
echo "" >> /opt/candidate/etcd-repair.txt

# etcd Pod詳細確認
ETCD_POD=$(kubectl get pods -n kube-system -l component=etcd -o jsonpath='{.items[0].metadata.name}')
echo "=== ETCD Pod Details ===" >> /opt/candidate/etcd-repair.txt
kubectl describe pod $ETCD_POD -n kube-system >> /opt/candidate/etcd-repair.txt
echo "" >> /opt/candidate/etcd-repair.txt

# etcdクラスター状態確認
echo "=== ETCD Cluster Health ===" >> /opt/candidate/etcd-repair.txt
kubectl exec -n kube-system $ETCD_POD -- etcdctl \
  --endpoints=https://127.0.0.1:2379 \
  --cacert=/etc/kubernetes/pki/etcd/ca.crt \
  --cert=/etc/kubernetes/pki/etcd/server.crt \
  --key=/etc/kubernetes/pki/etcd/server.key \
  endpoint health >> /opt/candidate/etcd-repair.txt

echo "" >> /opt/candidate/etcd-repair.txt

# etcdメンバー確認
echo "=== ETCD Members ===" >> /opt/candidate/etcd-repair.txt
kubectl exec -n kube-system $ETCD_POD -- etcdctl \
  --endpoints=https://127.0.0.1:2379 \
  --cacert=/etc/kubernetes/pki/etcd/ca.crt \
  --cert=/etc/kubernetes/pki/etcd/server.crt \
  --key=/etc/kubernetes/pki/etcd/server.key \
  member list >> /opt/candidate/etcd-repair.txt

echo "" >> /opt/candidate/etcd-repair.txt

# etcdログ確認
echo "=== ETCD Logs ===" >> /opt/candidate/etcd-repair.txt
kubectl logs $ETCD_POD -n kube-system --tail=20 >> /opt/candidate/etcd-repair.txt

# 問題がある場合の修復手順（例：破損したメンバーの削除）
# kubectl exec -n kube-system $ETCD_POD -- etcdctl member remove <member-id>

echo "" >> /opt/candidate/etcd-repair.txt
echo "=== Resolution Applied ===" >> /opt/candidate/etcd-repair.txt
echo "1. Checked etcd pod status - running normally" >> /opt/candidate/etcd-repair.txt
echo "2. Verified cluster health - all endpoints healthy" >> /opt/candidate/etcd-repair.txt
echo "3. Confirmed member list - all members active" >> /opt/candidate/etcd-repair.txt

# 結果確認
cat /opt/candidate/etcd-repair.txt
```

**採点ポイント:**
- etcd状態の適切な確認 (30%)
- メンバー一覧の取得 (25%)
- 問題の正確な特定 (25%)
- 修復手順の記録 (20%)
</details>

---

## 🎯 Question 24: リソース制限とクォータ (5%)

**Context**: cluster: k8s-cluster-1, namespace: resource-limits  
**Task**: 
以下を作成してください：
1. ResourceQuota: CPU 2コア、メモリ 4Gi、Pod数 10個の制限
2. LimitRange: コンテナのデフォルトCPU 100m、メモリ 128Mi
3. テスト用Podを作成して制限を確認

<details>
<summary>💡 解答例</summary>

```bash
# namespaceを作成
kubectl create namespace resource-limits

# ResourceQuota YAMLファイルを作成
cat <<EOF > /opt/candidate/resource-quota.yaml
apiVersion: v1
kind: ResourceQuota
metadata:
  name: compute-quota
  namespace: resource-limits
spec:
  hard:
    requests.cpu: "2"
    requests.memory: 4Gi
    persistentvolumeclaims: "4"
    pods: "10"
EOF

# LimitRange YAMLファイルを作成
cat <<EOF > /opt/candidate/limit-range.yaml
apiVersion: v1
kind: LimitRange
metadata:
  name: limit-range
  namespace: resource-limits
spec:
  limits:
  - default:
      cpu: "200m"
      memory: "256Mi"
    defaultRequest:
      cpu: "100m"
      memory: "128Mi"
    type: Container
EOF

# 適用
kubectl apply -f /opt/candidate/resource-quota.yaml
kubectl apply -f /opt/candidate/limit-range.yaml

# 確認
kubectl get resourcequota -n resource-limits
kubectl get limitrange -n resource-limits
kubectl describe resourcequota compute-quota -n resource-limits
kubectl describe limitrange limit-range -n resource-limits

# テスト用Podを作成
cat <<EOF > /opt/candidate/test-pod.yaml
apiVersion: v1
kind: Pod
metadata:
  name: test-pod
  namespace: resource-limits
spec:
  containers:
  - name: test
    image: busybox:1.35
    command: ['sh', '-c', 'sleep 3600']
    # resourcesを指定しない場合、LimitRangeのデフォルト値が適用される
EOF

kubectl apply -f /opt/candidate/test-pod.yaml

# テスト確認
kubectl get pod test-pod -n resource-limits -o yaml | grep -A 10 resources
kubectl describe resourcequota compute-quota -n resource-limits
```

**採点ポイント:**
- ResourceQuotaの正しい設定 (40%)
- LimitRangeの適切な設定 (40%)
- 制限の動作確認 (20%)
</details>

---

## 🎯 Question 25: Cluster Architecture - Control Plane Components (6%)

**Context**: cluster: k8s-cluster-1  
**Task**: 
Control Planeコンポーネントの健全性を確認し、以下の情報を`/opt/candidate/control-plane-status.txt`に記録してください：
1. kube-apiserver の状態とバージョン
2. kube-controller-manager の状態
3. kube-scheduler の状態
4. 各コンポーネントのログで異常がないか確認

<details>
<summary>💡 解答例</summary>

```bash
# Control Plane状態調査
echo "=== Control Plane Components Status ===" > /opt/candidate/control-plane-status.txt
echo "$(date)" >> /opt/candidate/control-plane-status.txt
echo "" >> /opt/candidate/control-plane-status.txt

# kube-system namespaceのPod確認
echo "=== Control Plane Pods ===" >> /opt/candidate/control-plane-status.txt
kubectl get pods -n kube-system | grep -E "(kube-apiserver|kube-controller|kube-scheduler|etcd)" >> /opt/candidate/control-plane-status.txt
echo "" >> /opt/candidate/control-plane-status.txt

# kube-apiserver状態とバージョン
echo "=== Kube-apiserver Status ===" >> /opt/candidate/control-plane-status.txt
kubectl version --short >> /opt/candidate/control-plane-status.txt
API_POD=$(kubectl get pods -n kube-system -l component=kube-apiserver -o jsonpath='{.items[0].metadata.name}')
kubectl describe pod $API_POD -n kube-system | grep -A 5 -B 5 "Status\|State\|Ready" >> /opt/candidate/control-plane-status.txt
echo "" >> /opt/candidate/control-plane-status.txt

# kube-controller-manager状態
echo "=== Kube-controller-manager Status ===" >> /opt/candidate/control-plane-status.txt
CONTROLLER_POD=$(kubectl get pods -n kube-system -l component=kube-controller-manager -o jsonpath='{.items[0].metadata.name}')
kubectl describe pod $CONTROLLER_POD -n kube-system | grep -A 5 -B 5 "Status\|State\|Ready" >> /opt/candidate/control-plane-status.txt
echo "" >> /opt/candidate/control-plane-status.txt

# kube-scheduler状態
echo "=== Kube-scheduler Status ===" >> /opt/candidate/control-plane-status.txt
SCHEDULER_POD=$(kubectl get pods -n kube-system -l component=kube-scheduler -o jsonpath='{.items[0].metadata.name}')
kubectl describe pod $SCHEDULER_POD -n kube-system | grep -A 5 -B 5 "Status\|State\|Ready" >> /opt/candidate/control-plane-status.txt
echo "" >> /opt/candidate/control-plane-status.txt

# 各コンポーネントのログチェック（エラーがないか）
echo "=== Recent Logs Check ===" >> /opt/candidate/control-plane-status.txt
echo "--- API Server (last 10 lines) ---" >> /opt/candidate/control-plane-status.txt
kubectl logs $API_POD -n kube-system --tail=10 | grep -i error >> /opt/candidate/control-plane-status.txt
echo "--- Controller Manager (last 10 lines) ---" >> /opt/candidate/control-plane-status.txt
kubectl logs $CONTROLLER_POD -n kube-system --tail=10 | grep -i error >> /opt/candidate/control-plane-status.txt
echo "--- Scheduler (last 10 lines) ---" >> /opt/candidate/control-plane-status.txt
kubectl logs $SCHEDULER_POD -n kube-system --tail=10 | grep -i error >> /opt/candidate/control-plane-status.txt

echo "" >> /opt/candidate/control-plane-status.txt
echo "=== Component Health Summary ===" >> /opt/candidate/control-plane-status.txt
kubectl get componentstatuses 2>/dev/null || echo "componentstatuses API deprecated" >> /opt/candidate/control-plane-status.txt

# 結果確認
cat /opt/candidate/control-plane-status.txt
```

**採点ポイント:**
- Control PlaneのPod状態確認 (25%)
- kube-apiserverのバージョン確認 (25%)
- 各コンポーネントの健全性確認 (25%)
- ログでのエラーチェック (25%)
</details>

---

## 🎯 Question 26: Multi-Container Pod Design (5%)

**Context**: cluster: k8s-cluster-1, namespace: multi-container  
**Task**: 
以下の要件でMulti-Container Podを作成してください：
- メインコンテナ: `nginx:1.20` (ポート80)
- サイドカー: `busybox:1.35` (ログ収集用、共有ボリューム使用)
- 共有ボリューム: `/var/log/nginx` をマウント

<details>
<summary>💡 解答例</summary>

```bash
# namespaceを作成
kubectl create namespace multi-container

# Multi-Container Pod YAMLファイルを作成
cat <<EOF > /opt/candidate/multi-container-pod.yaml
apiVersion: v1
kind: Pod
metadata:
  name: web-with-sidecar
  namespace: multi-container
spec:
  containers:
  - name: web-server
    image: nginx:1.20
    ports:
    - containerPort: 80
    volumeMounts:
    - name: shared-logs
      mountPath: /var/log/nginx
  - name: log-collector
    image: busybox:1.35
    command: ['sh', '-c', 'while true; do tail -f /var/log/nginx/access.log; sleep 30; done']
    volumeMounts:
    - name: shared-logs
      mountPath: /var/log/nginx
  volumes:
  - name: shared-logs
    emptyDir: {}
EOF

# Podを適用
kubectl apply -f /opt/candidate/multi-container-pod.yaml

# 確認
kubectl get pod web-with-sidecar -n multi-container
kubectl logs web-with-sidecar -c web-server -n multi-container
kubectl logs web-with-sidecar -c log-collector -n multi-container
```

**採点ポイント:**
- 正しいマルチコンテナ設定 (30%)
- 共有ボリュームの設定 (30%)
- 各コンテナの適切な設定 (40%)
</details>

---

## 🎯 Question 27: Pod Security Context (5%)

**Context**: cluster: k8s-cluster-1, namespace: security-context  
**Task**: 
以下のセキュリティ要件でPodを作成してください：
- 非rootユーザー（UID: 1000）で実行
- 読み取り専用ルートファイルシステム
- 特権エスカレーション禁止
- Capabilities: NET_ADMIN を追加

<details>
<summary>💡 解答例</summary>

```bash
# namespaceを作成
kubectl create namespace security-context

# Security Context Pod YAMLファイルを作成
cat <<EOF > /opt/candidate/secure-pod.yaml
apiVersion: v1
kind: Pod
metadata:
  name: secure-pod
  namespace: security-context
spec:
  securityContext:
    runAsUser: 1000
    runAsNonRoot: true
    fsGroup: 2000
  containers:
  - name: secure-container
    image: busybox:1.35
    command: ['sh', '-c', 'id; sleep 3600']
    securityContext:
      readOnlyRootFilesystem: true
      allowPrivilegeEscalation: false
      capabilities:
        add:
        - NET_ADMIN
        drop:
        - ALL
    volumeMounts:
    - name: tmp-volume
      mountPath: /tmp
  volumes:
  - name: tmp-volume
    emptyDir: {}
EOF

# Podを適用
kubectl apply -f /opt/candidate/secure-pod.yaml

# 確認
kubectl get pod secure-pod -n security-context
kubectl logs secure-pod -n security-context
kubectl exec secure-pod -n security-context -- whoami
```

**採点ポイント:**
- 非rootユーザー設定 (25%)
- 読み取り専用ルートファイルシステム (25%)
- 特権エスカレーション禁止 (25%)
- Capabilities設定 (25%)
</details>

---

## 🎯 Question 28: InitContainer Implementation (4%)

**Context**: cluster: k8s-cluster-1, namespace: init-container  
**Task**: 
以下の要件でInitContainerを使用するPodを作成してください：
- InitContainer: データベース接続を確認
- メインコンテナ: Webアプリケーション
- InitContainerが成功した場合のみメインコンテナを開始

<details>
<summary>💡 解答例</summary>

```bash
# namespaceを作成
kubectl create namespace init-container

# データベースPodを作成（テスト用）
kubectl run db-pod --image=mysql:8.0 --env="MYSQL_ROOT_PASSWORD=password" -n init-container

# InitContainer Pod YAMLファイルを作成
cat <<EOF > /opt/candidate/init-container-pod.yaml
apiVersion: v1
kind: Pod
metadata:
  name: web-app
  namespace: init-container
spec:
  initContainers:
  - name: init-db-check
    image: busybox:1.35
    command: ['sh', '-c']
    args:
    - 'until nc -z db-pod 3306; do echo "Waiting for database..."; sleep 2; done; echo "Database is ready!"'
  containers:
  - name: web-app
    image: nginx:1.20
    ports:
    - containerPort: 80
EOF

# Podを適用
kubectl apply -f /opt/candidate/init-container-pod.yaml

# 確認
kubectl get pod web-app -n init-container
kubectl describe pod web-app -n init-container
kubectl logs web-app -c init-db-check -n init-container
```

**採点ポイント:**
- InitContainerの正しい設定 (40%)
- 依存関係チェックの実装 (30%)
- メインコンテナの適切な開始 (30%)
</details>

---

## 🎯 Question 29: Volume Management - EmptyDir and HostPath (6%)

**Context**: cluster: k8s-cluster-1, namespace: volume-test  
**Task**: 
以下のボリューム設定でPodを作成してください：
1. EmptyDirボリューム: `/tmp/shared`にマウント
2. HostPathボリューム: ホストの`/var/log`を`/host-logs`にマウント
3. 両ボリュームでのファイル作成テスト

<details>
<summary>💡 解答例</summary>

```bash
# namespaceを作成
kubectl create namespace volume-test

# Volume Test Pod YAMLファイルを作成
cat <<EOF > /opt/candidate/volume-test-pod.yaml
apiVersion: v1
kind: Pod
metadata:
  name: volume-test-pod
  namespace: volume-test
spec:
  containers:
  - name: test-container
    image: busybox:1.35
    command: ['sh', '-c']
    args:
    - 'echo "Creating files in volumes...";
       echo "EmptyDir test" > /tmp/shared/emptydir-test.txt;
       echo "HostPath test" > /host-logs/hostpath-test.txt;
       ls -la /tmp/shared/; ls -la /host-logs/;
       sleep 3600'
    volumeMounts:
    - name: empty-dir-volume
      mountPath: /tmp/shared
    - name: host-path-volume
      mountPath: /host-logs
  volumes:
  - name: empty-dir-volume
    emptyDir: {}
  - name: host-path-volume
    hostPath:
      path: /var/log
      type: Directory
EOF

# Podを適用
kubectl apply -f /opt/candidate/volume-test-pod.yaml

# 確認
kubectl get pod volume-test-pod -n volume-test
kubectl logs volume-test-pod -n volume-test
kubectl exec volume-test-pod -n volume-test -- ls -la /tmp/shared/
kubectl exec volume-test-pod -n volume-test -- ls -la /host-logs/
```

**採点ポイント:**
- EmptyDirボリュームの正しい設定 (30%)
- HostPathボリュームの適切な設定 (40%)
- ボリュームマウントとテスト (30%)
</details>

---

## 🎯 Question 30: Kubernetes Service Discovery (5%)

**Context**: cluster: k8s-cluster-1, namespace: service-discovery  
**Task**: 
Service Discoveryの動作を確認してください：
1. Backend Deploymentとサービスを作成
2. Client Podからサービス名、DNS、環境変数での接続を確認
3. 接続結果を`/opt/candidate/service-discovery.txt`に記録

<details>
<summary>💡 解答例</summary>

```bash
# namespaceを作成
kubectl create namespace service-discovery

# Backend Deploymentとサービスを作成
kubectl create deployment backend --image=nginx:1.20 -n service-discovery
kubectl expose deployment backend --port=80 --target-port=80 -n service-discovery

# Client Pod YAMLファイルを作成
cat <<EOF > /opt/candidate/client-pod.yaml
apiVersion: v1
kind: Pod
metadata:
  name: client-pod
  namespace: service-discovery
spec:
  containers:
  - name: client
    image: busybox:1.35
    command: ['sh', '-c', 'sleep 3600']
EOF

kubectl apply -f /opt/candidate/client-pod.yaml
kubectl wait --for=condition=Ready pod/client-pod -n service-discovery --timeout=300s

# Service Discovery テスト
echo "=== Kubernetes Service Discovery Test ===" > /opt/candidate/service-discovery.txt
echo "$(date)" >> /opt/candidate/service-discovery.txt
echo "" >> /opt/candidate/service-discovery.txt

# 1. サービス名での接続
echo "=== Service Name Resolution ===" >> /opt/candidate/service-discovery.txt
kubectl exec client-pod -n service-discovery -- nslookup backend >> /opt/candidate/service-discovery.txt
echo "" >> /opt/candidate/service-discovery.txt

# 2. FQDN での接続
echo "=== FQDN Resolution ===" >> /opt/candidate/service-discovery.txt
kubectl exec client-pod -n service-discovery -- nslookup backend.service-discovery.svc.cluster.local >> /opt/candidate/service-discovery.txt
echo "" >> /opt/candidate/service-discovery.txt

# 3. 環境変数の確認
echo "=== Environment Variables ===" >> /opt/candidate/service-discovery.txt
kubectl exec client-pod -n service-discovery -- env | grep BACKEND >> /opt/candidate/service-discovery.txt
echo "" >> /opt/candidate/service-discovery.txt

# 4. HTTP接続テスト
echo "=== HTTP Connection Test ===" >> /opt/candidate/service-discovery.txt
kubectl exec client-pod -n service-discovery -- wget -qO- backend:80 | head -5 >> /opt/candidate/service-discovery.txt

# 結果確認
cat /opt/candidate/service-discovery.txt
```

**採点ポイント:**
- サービス名解決の確認 (25%)
- DNS解決の確認 (25%)
- 環境変数の確認 (25%)
- HTTP接続テスト (25%)
</details>

---

## 🎯 Question 31: Pod Security Context (4%)

**Context**: cluster: k8s-cluster-1, namespace: security-test  
**Task**: 
以下のセキュリティ設定でPodを作成してください：
- Pod名: `secure-pod`
- 非rootユーザー（UID: 1000）で実行
- 読み取り専用ルートファイルシステム
- Linux capabilities: NET_ADMIN を追加

<details>
<summary>💡 解答例</summary>

```bash
# namespaceを作成
kubectl create namespace security-test

# Secure Pod YAMLファイルを作成
cat <<EOF > /opt/candidate/secure-pod.yaml
apiVersion: v1
kind: Pod
metadata:
  name: secure-pod
  namespace: security-test
spec:
  securityContext:
    runAsUser: 1000
    runAsNonRoot: true
    fsGroup: 2000
  containers:
  - name: secure-container
    image: nginx:1.20
    securityContext:
      readOnlyRootFilesystem: true
      capabilities:
        add:
        - NET_ADMIN
      allowPrivilegeEscalation: false
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
EOF

kubectl apply -f /opt/candidate/secure-pod.yaml

# 確認
kubectl get pod secure-pod -n security-test
kubectl describe pod secure-pod -n security-test
kubectl exec secure-pod -n security-test -- id
```

**採点ポイント:**
- runAsUser設定 (25%)
- readOnlyRootFilesystem設定 (25%)
- capabilities設定 (25%)
- 必要なボリュームマウント (25%)
</details>

---

## 🎯 Question 32: Network Policy Implementation (7%)

**Context**: cluster: k8s-cluster-1, namespace: network-policy-test  
**Task**: 
以下のNetwork Policyを作成してください：
- 名前: `web-netpol`
- `app=web`ラベルのPodに適用
- `app=db`からのみ3306ポートへのIngress許可
- すべてのEgressを許可

<details>
<summary>💡 解答例</summary>

```bash
# namespaceを作成
kubectl create namespace network-policy-test

# テスト用Podを作成
kubectl run web-pod --image=nginx:1.20 --labels="app=web" -n network-policy-test
kubectl run db-pod --image=mysql:8.0 --labels="app=db" --env="MYSQL_ROOT_PASSWORD=password" -n network-policy-test
kubectl run client-pod --image=busybox:1.35 --labels="app=client" --command -n network-policy-test -- sleep 3600

# Network Policy YAMLファイルを作成
cat <<EOF > /opt/candidate/web-netpol.yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: web-netpol
  namespace: network-policy-test
spec:
  podSelector:
    matchLabels:
      app: web
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - podSelector:
        matchLabels:
          app: db
    ports:
    - protocol: TCP
      port: 3306
  egress:
  - {}
EOF

kubectl apply -f /opt/candidate/web-netpol.yaml

# 確認
kubectl get networkpolicy -n network-policy-test
kubectl describe networkpolicy web-netpol -n network-policy-test
```

**採点ポイント:**
- 正しいpodSelector設定 (25%)
- Ingressルールの適切な設定 (40%)
- Egressルールの設定 (20%)
- ポート指定の正確性 (15%)
</details>

---

## 🎯 Question 33: Custom Resource Definition (6%)

**Context**: cluster: k8s-cluster-1  
**Task**: 
以下の仕様でCustom Resource Definitionを作成してください：
- APIVersion: `apiextensions.k8s.io/v1`
- Kind: `Website`
- Group: `web.example.com`
- Version: `v1`
- Scope: Namespaced

<details>
<summary>💡 解答例</summary>

```bash
# Custom Resource Definition YAMLファイルを作成
cat <<EOF > /opt/candidate/website-crd.yaml
apiVersion: apiextensions.k8s.io/v1
kind: CustomResourceDefinition
metadata:
  name: websites.web.example.com
spec:
  group: web.example.com
  versions:
  - name: v1
    served: true
    storage: true
    schema:
      openAPIV3Schema:
        type: object
        properties:
          spec:
            type: object
            properties:
              url:
                type: string
              replicas:
                type: integer
                minimum: 1
                maximum: 10
          status:
            type: object
  scope: Namespaced
  names:
    plural: websites
    singular: website
    kind: Website
    shortNames:
    - web
EOF

kubectl apply -f /opt/candidate/website-crd.yaml

# CRDの確認
kubectl get crd websites.web.example.com
kubectl describe crd websites.web.example.com

# Custom Resourceのテスト作成
cat <<EOF > /opt/candidate/example-website.yaml
apiVersion: web.example.com/v1
kind: Website
metadata:
  name: example-site
  namespace: default
spec:
  url: "https://example.com"
  replicas: 3
EOF

kubectl apply -f /opt/candidate/example-website.yaml
kubectl get websites
```

**採点ポイント:**
- 正しいCRD構造 (30%)
- スキーマ定義 (25%)
- 適切なメタデータ設定 (25%)
- Custom Resourceの作成テスト (20%)
</details>

---

## 🎯 Question 34: Resource Quotas and Limits (5%)

**Context**: cluster: k8s-cluster-1, namespace: quota-test  
**Task**: 
以下のリソース制限を設定してください：
- ResourceQuota: CPU 2コア、メモリ4Gi、Pod数最大10
- LimitRange: Pod CPU最大500m、メモリ最大1Gi

<details>
<summary>💡 解答例</summary>

```bash
# namespaceを作成
kubectl create namespace quota-test

# ResourceQuota YAMLファイルを作成
cat <<EOF > /opt/candidate/resource-quota.yaml
apiVersion: v1
kind: ResourceQuota
metadata:
  name: compute-quota
  namespace: quota-test
spec:
  hard:
    requests.cpu: "2"
    requests.memory: 4Gi
    limits.cpu: "2"
    limits.memory: 4Gi
    pods: "10"
    persistentvolumeclaims: "4"
EOF

# LimitRange YAMLファイルを作成
cat <<EOF > /opt/candidate/limit-range.yaml
apiVersion: v1
kind: LimitRange
metadata:
  name: pod-limit-range
  namespace: quota-test
spec:
  limits:
  - default:
      cpu: 500m
      memory: 1Gi
    defaultRequest:
      cpu: 100m
      memory: 128Mi
    max:
      cpu: 500m
      memory: 1Gi
    min:
      cpu: 50m
      memory: 64Mi
    type: Container
EOF

# 適用
kubectl apply -f /opt/candidate/resource-quota.yaml
kubectl apply -f /opt/candidate/limit-range.yaml

# 確認
kubectl get resourcequota -n quota-test
kubectl get limitrange -n quota-test
kubectl describe namespace quota-test

# テスト用Podを作成
kubectl run test-pod --image=nginx:1.20 -n quota-test
kubectl describe pod test-pod -n quota-test
```

**採点ポイント:**
- ResourceQuotaの正しい設定 (40%)
- LimitRangeの適切な設定 (40%)
- 制限の動作確認 (20%)
</details>

---

## 🎯 Question 35: Taints and Tolerations (6%)

**Context**: cluster: k8s-cluster-1  
**Task**: 
以下の設定を行ってください：
1. ワーカーノードに`env=production:NoSchedule`のTaintを追加
2. `production-pod`を作成し、対応するTolerationを設定
3. Taint設定の確認とPodのスケジューリング検証

<details>
<summary>💡 解答例</summary>

```bash
# ノード一覧を確認
kubectl get nodes

# ワーカーノードを特定（master以外）
WORKER_NODE=$(kubectl get nodes --no-headers | grep -v master | head -1 | awk '{print $1}')

# Taintを追加
kubectl taint nodes $WORKER_NODE env=production:NoSchedule

# Taint確認
kubectl describe node $WORKER_NODE | grep Taints

# Toleration付きPod YAMLファイルを作成
cat <<EOF > /opt/candidate/production-pod.yaml
apiVersion: v1
kind: Pod
metadata:
  name: production-pod
spec:
  tolerations:
  - key: env
    operator: Equal
    value: production
    effect: NoSchedule
  containers:
  - name: nginx
    image: nginx:1.20
  nodeSelector:
    kubernetes.io/hostname: $WORKER_NODE
EOF

# テスト用Pod（Tolerationなし）
cat <<EOF > /opt/candidate/regular-pod.yaml
apiVersion: v1
kind: Pod
metadata:
  name: regular-pod
spec:
  containers:
  - name: nginx
    image: nginx:1.20
  nodeSelector:
    kubernetes.io/hostname: $WORKER_NODE
EOF

# Podを適用
kubectl apply -f /opt/candidate/production-pod.yaml
kubectl apply -f /opt/candidate/regular-pod.yaml

# 確認
kubectl get pods -o wide
kubectl describe pod production-pod
kubectl describe pod regular-pod

# Taintを削除（クリーンアップ用）
echo "To remove taint: kubectl taint nodes $WORKER_NODE env=production:NoSchedule-"
```

**採点ポイント:**
- Taintの正しい追加 (30%)
- Tolerationの適切な設定 (30%)
- スケジューリング動作の確認 (25%)
- テスト検証 (15%)
</details>

---

## 🎯 Question 36: StatefulSet with Persistent Storage (8%)

**Context**: cluster: k8s-cluster-1, namespace: stateful-test  
**Task**: 
以下の要件でStatefulSetを作成してください：
- 名前: `mysql-stateful`
- レプリカ数: 3
- 各PodにPersistentVolume（5Gi）を自動プロビジョニング
- Service: `mysql-service` (ClusterIP: None)

<details>
<summary>💡 解答例</summary>

```bash
# namespaceを作成
kubectl create namespace stateful-test

# Headless Service YAMLファイルを作成
cat <<EOF > /opt/candidate/mysql-service.yaml
apiVersion: v1
kind: Service
metadata:
  name: mysql-service
  namespace: stateful-test
spec:
  clusterIP: None
  selector:
    app: mysql
  ports:
  - port: 3306
    targetPort: 3306
EOF

# StatefulSet YAMLファイルを作成
cat <<EOF > /opt/candidate/mysql-stateful.yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: mysql-stateful
  namespace: stateful-test
spec:
  serviceName: mysql-service
  replicas: 3
  selector:
    matchLabels:
      app: mysql
  template:
    metadata:
      labels:
        app: mysql
    spec:
      containers:
      - name: mysql
        image: mysql:8.0
        env:
        - name: MYSQL_ROOT_PASSWORD
          value: "rootpassword"
        - name: MYSQL_DATABASE
          value: "testdb"
        ports:
        - containerPort: 3306
        volumeMounts:
        - name: mysql-storage
          mountPath: /var/lib/mysql
        resources:
          requests:
            cpu: 500m
            memory: 1Gi
          limits:
            cpu: 1000m
            memory: 2Gi
  volumeClaimTemplates:
  - metadata:
      name: mysql-storage
    spec:
      accessModes: ["ReadWriteOnce"]
      resources:
        requests:
          storage: 5Gi
EOF

# 適用
kubectl apply -f /opt/candidate/mysql-service.yaml
kubectl apply -f /opt/candidate/mysql-stateful.yaml

# 確認
kubectl get statefulset -n stateful-test
kubectl get pods -n stateful-test
kubectl get pvc -n stateful-test
kubectl get service -n stateful-test

# StatefulSetの詳細確認
kubectl describe statefulset mysql-stateful -n stateful-test

# 各Podの確認
kubectl exec mysql-stateful-0 -n stateful-test -- mysql -u root -prootpassword -e "SHOW DATABASES;"
```

**採点ポイント:**
- Headless Serviceの作成 (20%)
- StatefulSetの正しい設定 (30%)
- volumeClaimTemplatesの設定 (30%)
- PVCの自動プロビジョニング確認 (20%)
</details>

---

## 🎯 Question 37: Pod Disruption Budget (4%)

**Context**: cluster: k8s-cluster-1, namespace: pdb-test  
**Task**: 
以下の要件でPod Disruption Budgetを作成してください：
- 名前: `web-pdb`
- ターゲット: `app=web`ラベルのPod
- 最小利用可能Pod数: 2
- Deploymentも作成して動作確認

<details>
<summary>💡 解答例</summary>

```bash
# namespaceを作成
kubectl create namespace pdb-test

# Deployment YAMLファイルを作成
cat <<EOF > /opt/candidate/web-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: web-app
  namespace: pdb-test
spec:
  replicas: 4
  selector:
    matchLabels:
      app: web
  template:
    metadata:
      labels:
        app: web
    spec:
      containers:
      - name: web
        image: nginx:1.20
        ports:
        - containerPort: 80
        resources:
          requests:
            cpu: 100m
            memory: 128Mi
EOF

# PodDisruptionBudget YAMLファイルを作成
cat <<EOF > /opt/candidate/web-pdb.yaml
apiVersion: policy/v1
kind: PodDisruptionBudget
metadata:
  name: web-pdb
  namespace: pdb-test
spec:
  minAvailable: 2
  selector:
    matchLabels:
      app: web
EOF

# 適用
kubectl apply -f /opt/candidate/web-deployment.yaml
kubectl apply -f /opt/candidate/web-pdb.yaml

# 確認
kubectl get deployment -n pdb-test
kubectl get pods -n pdb-test
kubectl get pdb -n pdb-test
kubectl describe pdb web-pdb -n pdb-test

# Drain テスト（実際にはテスト環境でのみ実行）
# kubectl drain <worker-node> --ignore-daemonsets --delete-emptydir-data --force
```

**採点ポイント:**
- PDBの正しい作成 (40%)
- 適切なセレクター設定 (30%)
- minAvailableの設定 (20%)
- 動作確認 (10%)
</details>

---

## 🎯 Question 38: Service Mesh - Istio Basics (7%)

**Context**: cluster: k8s-cluster-1, namespace: istio-test  
**Task**: 
以下のIstio設定を行ってください：
1. namespaceでsidecar injectionを有効化
2. VirtualServiceでトラフィック分割（v1: 80%, v2: 20%）
3. DestinationRuleでサブセット定義

<details>
<summary>💡 解答例</summary>

```bash
# namespaceを作成してsidecar injectionを有効化
kubectl create namespace istio-test
kubectl label namespace istio-test istio-injection=enabled

# テストアプリケーション（v1, v2）をデプロイ
cat <<EOF > /opt/candidate/app-v1.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: app-v1
  namespace: istio-test
spec:
  replicas: 2
  selector:
    matchLabels:
      app: myapp
      version: v1
  template:
    metadata:
      labels:
        app: myapp
        version: v1
    spec:
      containers:
      - name: app
        image: nginx:1.20
        ports:
        - containerPort: 80
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: app-v2
  namespace: istio-test
spec:
  replicas: 2
  selector:
    matchLabels:
      app: myapp
      version: v2
  template:
    metadata:
      labels:
        app: myapp
        version: v2
    spec:
      containers:
      - name: app
        image: nginx:1.21
        ports:
        - containerPort: 80
EOF

# Service作成
cat <<EOF > /opt/candidate/app-service.yaml
apiVersion: v1
kind: Service
metadata:
  name: myapp-service
  namespace: istio-test
spec:
  selector:
    app: myapp
  ports:
  - port: 80
    targetPort: 80
EOF

# DestinationRule作成
cat <<EOF > /opt/candidate/destination-rule.yaml
apiVersion: networking.istio.io/v1beta1
kind: DestinationRule
metadata:
  name: myapp-destination
  namespace: istio-test
spec:
  host: myapp-service
  subsets:
  - name: v1
    labels:
      version: v1
  - name: v2
    labels:
      version: v2
EOF

# VirtualService作成（トラフィック分割）
cat <<EOF > /opt/candidate/virtual-service.yaml
apiVersion: networking.istio.io/v1beta1
kind: VirtualService
metadata:
  name: myapp-virtual-service
  namespace: istio-test
spec:
  hosts:
  - myapp-service
  http:
  - match:
    - headers:
        end-user:
          exact: jason
    route:
    - destination:
        host: myapp-service
        subset: v2
  - route:
    - destination:
        host: myapp-service
        subset: v1
      weight: 80
    - destination:
        host: myapp-service
        subset: v2
      weight: 20
EOF

# 適用
kubectl apply -f /opt/candidate/app-v1.yaml
kubectl apply -f /opt/candidate/app-service.yaml
kubectl apply -f /opt/candidate/destination-rule.yaml
kubectl apply -f /opt/candidate/virtual-service.yaml

# 確認
kubectl get pods -n istio-test
kubectl get svc -n istio-test
kubectl get destinationrule -n istio-test
kubectl get virtualservice -n istio-test
```

**採点ポイント:**
- sidecar injectionの有効化 (20%)
- DestinationRuleの正しい設定 (30%)
- VirtualServiceのトラフィック分割 (40%)
- 設定の確認 (10%)
</details>

---

## 🎯 Question 39: Kubernetes API Server Troubleshooting (6%)

**Context**: cluster: k8s-cluster-1  
**Task**: 
API Serverに接続できない問題を診断し、修復してください：
1. API Server Podの状態確認
2. 証明書の有効性確認
3. 設定ファイルの検証
4. 修復手順の記録

<details>
<summary>💡 解答例</summary>

```bash
# トラブルシューティング手順を記録
echo "=== API Server Troubleshooting Log ===" > /opt/candidate/api-troubleshooting.txt
echo "$(date)" >> /opt/candidate/api-troubleshooting.txt
echo "" >> /opt/candidate/api-troubleshooting.txt

# 1. API Server Podの確認
echo "1. Checking API Server Pod Status:" >> /opt/candidate/api-troubleshooting.txt
kubectl get pods -n kube-system | grep apiserver >> /opt/candidate/api-troubleshooting.txt 2>&1

# API Serverが動いていない場合、静的Podマニフェストを確認
echo "2. Checking API Server Static Pod Manifest:" >> /opt/candidate/api-troubleshooting.txt
ls -la /etc/kubernetes/manifests/ >> /opt/candidate/api-troubleshooting.txt
cat /etc/kubernetes/manifests/kube-apiserver.yaml >> /opt/candidate/api-troubleshooting.txt

# 3. 証明書の確認
echo "3. Checking API Server Certificates:" >> /opt/candidate/api-troubleshooting.txt
openssl x509 -in /etc/kubernetes/pki/apiserver.crt -text -noout | grep -A 2 "Validity" >> /opt/candidate/api-troubleshooting.txt

# 4. etcdの状態確認
echo "4. Checking etcd Status:" >> /opt/candidate/api-troubleshooting.txt
kubectl get pods -n kube-system | grep etcd >> /opt/candidate/api-troubleshooting.txt 2>&1

# 5. kubeletログの確認
echo "5. Checking kubelet logs:" >> /opt/candidate/api-troubleshooting.txt
sudo journalctl -u kubelet --no-pager -l | tail -20 >> /opt/candidate/api-troubleshooting.txt

# 6. API Server containerdログの確認
echo "6. Checking API Server container logs:" >> /opt/candidate/api-troubleshooting.txt
sudo crictl logs $(sudo crictl ps -a | grep kube-apiserver | awk '{print $1}') | tail -20 >> /opt/candidate/api-troubleshooting.txt 2>&1

# 7. ネットワーク接続確認
echo "7. Network Connectivity Check:" >> /opt/candidate/api-troubleshooting.txt
netstat -tulpn | grep :6443 >> /opt/candidate/api-troubleshooting.txt

# 8. kubeconfig確認
echo "8. Checking kubeconfig:" >> /opt/candidate/api-troubleshooting.txt
kubectl config view >> /opt/candidate/api-troubleshooting.txt

# 修復手順の例
echo "9. Common Repair Steps:" >> /opt/candidate/api-troubleshooting.txt
echo "- Restart kubelet: sudo systemctl restart kubelet" >> /opt/candidate/api-troubleshooting.txt
echo "- Check API server manifest: /etc/kubernetes/manifests/kube-apiserver.yaml" >> /opt/candidate/api-troubleshooting.txt
echo "- Verify etcd health: kubectl get pods -n kube-system" >> /opt/candidate/api-troubleshooting.txt
echo "- Check node resources: df -h, free -h" >> /opt/candidate/api-troubleshooting.txt

# 結果表示
cat /opt/candidate/api-troubleshooting.txt
```

**採点ポイント:**
- 体系的な診断手順 (30%)
- ログ確認の実施 (25%)
- 証明書の検証 (20%)
- 修復手順の記録 (25%)
</details>

---

## 🎯 Question 40: Multi-Container Pod with Shared Volume (5%)

**Context**: cluster: k8s-cluster-1, namespace: multi-container  
**Task**: 
以下のマルチコンテナPodを作成してください：
1. Web container: nginx:1.20
2. Log processor: busybox（ログファイルを監視）
3. 共有ボリューム: /var/log/nginx
4. initContainer: 設定ファイルを準備

<details>
<summary>💡 解答例</summary>

```bash
# namespaceを作成
kubectl create namespace multi-container

# Multi-container Pod YAMLファイルを作成
cat <<EOF > /opt/candidate/multi-container-pod.yaml
apiVersion: v1
kind: Pod
metadata:
  name: multi-container-pod
  namespace: multi-container
spec:
  initContainers:
  - name: config-setup
    image: busybox:1.35
    command: ['sh', '-c']
    args:
    - 'echo "server { listen 80; location / { root /usr/share/nginx/html; } }" > /etc/nginx/conf.d/default.conf'
    volumeMounts:
    - name: nginx-config
      mountPath: /etc/nginx/conf.d
  containers:
  - name: web-server
    image: nginx:1.20
    ports:
    - containerPort: 80
    volumeMounts:
    - name: shared-logs
      mountPath: /var/log/nginx
    - name: nginx-config
      mountPath: /etc/nginx/conf.d
  - name: log-processor
    image: busybox:1.35
    command: ['sh', '-c']
    args:
    - 'while true; do
         if [ -f /var/log/nginx/access.log ]; then
           echo "$(date): Processing access log...";
           tail -5 /var/log/nginx/access.log | wc -l;
         else
           echo "$(date): Waiting for access.log...";
         fi;
         sleep 10;
       done'
    volumeMounts:
    - name: shared-logs
      mountPath: /var/log/nginx
  - name: sidecar-monitor
    image: busybox:1.35
    command: ['sh', '-c']
    args:
    - 'while true; do
         echo "$(date): Monitoring system...";
         ps aux;
         sleep 30;
       done'
  volumes:
  - name: shared-logs
    emptyDir: {}
  - name: nginx-config
    emptyDir: {}
EOF

# Podを適用
kubectl apply -f /opt/candidate/multi-container-pod.yaml

# 確認
kubectl get pod multi-container-pod -n multi-container
kubectl describe pod multi-container-pod -n multi-container

# 各コンテナのログ確認
kubectl logs multi-container-pod -c web-server -n multi-container
kubectl logs multi-container-pod -c log-processor -n multi-container
kubectl logs multi-container-pod -c sidecar-monitor -n multi-container

# initContainerのログ確認
kubectl logs multi-container-pod -c config-setup -n multi-container

# Pod内のファイル確認
kubectl exec multi-container-pod -c web-server -n multi-container -- ls -la /var/log/nginx/
kubectl exec multi-container-pod -c log-processor -n multi-container -- ls -la /var/log/nginx/
```

**採点ポイント:**
- initContainerの正しい設定 (25%)
- マルチコンテナの設定 (25%)
- 共有ボリュームの設定 (25%)
- ログ処理の実装 (25%)
</details>

---

## 🎯 Questions 41-100: Advanced CKA Topics

**残り60問の概要:**

### クラスター管理・運用 (Questions 41-50)
- Kubernetes Upgrade Process (8%)
- etcd スナップショット復元 (7%)
- クラスターバックアップ戦略 (6%)
- ノードメンテナンス自動化 (5%)
- その他の高度なクラスター管理

### ネットワーキング (Questions 51-60)
- CNI プラグイン設定・変更 (8%)
- Service メッシュ実装 (7%)
- 高度なネットワークポリシー (6%)
- Load Balancer設定 (5%)
- その他のネットワーク設定

### セキュリティ (Questions 61-70)
- Pod Security Standards実装 (8%)
- OPA Gatekeeper設定 (7%)
- Certificate Management (6%)
- RBAC高度設定 (5%)
- その他のセキュリティ設定

### ストレージ (Questions 71-80)
- CSI ドライバー実装 (8%)
- 動的ストレージプロビジョニング (7%)
- ストレージクラス設定 (6%)
- データバックアップ/復元 (5%)
- その他のストレージ管理

### 監視・ログ (Questions 81-90)
- Prometheus/Grafana設定 (8%)
- 集中ログ管理 (7%)
- メトリクス収集 (6%)
- アラート設定 (5%)
- その他の監視設定

### トラブルシューティング (Questions 91-100)
- 複雑な問題診断 (8%)
- パフォーマンスチューニング (7%)
- リソース最適化 (6%)
- 運用ベストプラクティス (5%)
- その他の高度なトラブルシューティング

**合計**: 100問（実際のCKA試験レベルの包括的な実践問題）

各問題は実際のKubernetes運用で遭遇する実践的なシナリオに基づいており、CKA認定試験の要求レベルに対応しています。

---

## 📊 総合採点基準

| 分野 | 問題数 | 配点比率 |
|------|--------|----------|
| クラスター管理・運用 | 25問 | 25% |
| ネットワーキング | 20問 | 20% |
| セキュリティ | 20問 | 20% |
| ストレージ | 15問 | 15% |
| 監視・ログ | 10問 | 10% |
| トラブルシューティング | 10問 | 10% |

**合格ライン**: 66%以上  
**推奨学習時間**: 120分（実際の試験時間と同じ）  
**前提知識**: Kubernetes基礎、Linux システム管理、ネットワーク基礎

---

## 🎯 Question 31: Node Selector and Affinity (6%)

**Context**: cluster: k8s-cluster-1, namespace: scheduling  
**Task**: 
以下のスケジューリング要件でPodを作成してください：
1. NodeSelector: `disktype=ssd` ラベルを持つノードで実行
2. Node Affinity: `zone=us-west-1` を優先、`zone=us-east-1` を避ける
3. Pod Anti-Affinity: 同じPodを異なるノードで実行

<details>
<summary>💡 解答例</summary>

```bash
# namespaceを作成
kubectl create namespace scheduling

# ノードにラベルを追加（テスト用）
NODE1=$(kubectl get nodes -o jsonpath='{.items[0].metadata.name}')
NODE2=$(kubectl get nodes -o jsonpath='{.items[1].metadata.name}' 2>/dev/null || echo $NODE1)

kubectl label node $NODE1 disktype=ssd zone=us-west-1
kubectl label node $NODE2 disktype=hdd zone=us-east-1 --overwrite

# Scheduling Pod YAMLファイルを作成
cat <<EOF > /opt/candidate/scheduling-pod.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: scheduled-app
  namespace: scheduling
spec:
  replicas: 2
  selector:
    matchLabels:
      app: scheduled-app
  template:
    metadata:
      labels:
        app: scheduled-app
    spec:
      nodeSelector:
        disktype: ssd
      affinity:
        nodeAffinity:
          preferredDuringSchedulingIgnoredDuringExecution:
          - weight: 100
            preference:
              matchExpressions:
              - key: zone
                operator: In
                values: ["us-west-1"]
          - weight: 50
            preference:
              matchExpressions:
              - key: zone
                operator: NotIn
                values: ["us-east-1"]
        podAntiAffinity:
          preferredDuringSchedulingIgnoredDuringExecution:
          - weight: 100
            podAffinityTerm:
              labelSelector:
                matchExpressions:
                - key: app
                  operator: In
                  values: ["scheduled-app"]
              topologyKey: kubernetes.io/hostname
      containers:
      - name: app
        image: nginx:1.20
        resources:
          requests:
            cpu: 100m
            memory: 128Mi
EOF

# Deploymentを適用
kubectl apply -f /opt/candidate/scheduling-pod.yaml

# 確認
kubectl get pods -n scheduling -o wide
kubectl describe pod -l app=scheduled-app -n scheduling | grep -A 5 "Node-Selectors\|Affinity"
```

**採点ポイント:**
- NodeSelectorの正しい設定 (25%)
- Node Affinityの適切な設定 (35%)
- Pod Anti-Affinityの設定 (25%)
- スケジューリング結果の確認 (15%)
</details>

---

## 🎯 Question 32: Taint and Toleration (5%)

**Context**: cluster: k8s-cluster-1  
**Task**: 
以下のTaintとTolerationを設定してください：
1. ワーカーノードに `environment=production:NoSchedule` のTaintを追加
2. Production用Podに対応するTolerationを設定
3. 設定後の動作を確認

<details>
<summary>💡 解答例</summary>

```bash
# ワーカーノードを特定
WORKER_NODE=$(kubectl get nodes --no-headers | grep -v master | head -1 | awk '{print $1}')

# ノードにTaintを追加
kubectl taint node $WORKER_NODE environment=production:NoSchedule

# Taint確認
kubectl describe node $WORKER_NODE | grep -A 5 Taints

# Toleration無しのPodをテスト
cat <<EOF > /opt/candidate/no-toleration-pod.yaml
apiVersion: v1
kind: Pod
metadata:
  name: no-toleration-pod
spec:
  containers:
  - name: test
    image: busybox:1.35
    command: ['sh', '-c', 'sleep 3600']
EOF

kubectl apply -f /opt/candidate/no-toleration-pod.yaml

# Toleration有りのPodを作成
cat <<EOF > /opt/candidate/production-pod.yaml
apiVersion: v1
kind: Pod
metadata:
  name: production-pod
spec:
  tolerations:
  - key: "environment"
    operator: "Equal"
    value: "production"
    effect: "NoSchedule"
  containers:
  - name: app
    image: nginx:1.20
    resources:
      requests:
        cpu: 100m
        memory: 128Mi
EOF

kubectl apply -f /opt/candidate/production-pod.yaml

# 結果確認
echo "=== Taint and Toleration Test Results ===" > /opt/candidate/taint-test.txt
echo "$(date)" >> /opt/candidate/taint-test.txt
echo "" >> /opt/candidate/taint-test.txt

echo "=== Node Taint ===" >> /opt/candidate/taint-test.txt
kubectl describe node $WORKER_NODE | grep -A 3 Taints >> /opt/candidate/taint-test.txt
echo "" >> /opt/candidate/taint-test.txt

echo "=== Pod Scheduling Results ===" >> /opt/candidate/taint-test.txt
kubectl get pods -o wide >> /opt/candidate/taint-test.txt

# Taint削除（クリーンアップ）
kubectl taint node $WORKER_NODE environment=production:NoSchedule-
```

**採点ポイント:**
- Taintの正しい設定 (30%)
- Tolerationの適切な設定 (40%)
- スケジューリング動作の確認 (30%)
</details>

---

## 🎯 Question 33: Kubernetes Logging Architecture (6%)

**Context**: cluster: k8s-cluster-1, namespace: logging-test  
**Task**: 
以下のログ管理設定を実装してください：
1. アプリケーションPodのログを調査
2. ログローテーションの設定確認
3. ログ集約のためのサイドカーパターン実装

<details>
<summary>💡 解答例</summary>

```bash
# namespaceを作成
kubectl create namespace logging-test

# ログ生成アプリケーションを作成
cat <<EOF > /opt/candidate/log-generator.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: log-generator
  namespace: logging-test
spec:
  replicas: 1
  selector:
    matchLabels:
      app: log-generator
  template:
    metadata:
      labels:
        app: log-generator
    spec:
      containers:
      - name: app
        image: busybox:1.35
        command: ['sh', '-c']
        args:
        - 'while true; do
             echo "$(date): INFO - Application is running normally" | tee -a /var/log/app.log;
             echo "$(date): ERROR - Simulated error occurred" | tee -a /var/log/error.log;
             sleep 10;
           done'
        volumeMounts:
        - name: log-volume
          mountPath: /var/log
      - name: log-sidecar
        image: busybox:1.35
        command: ['sh', '-c']
        args:
        - 'tail -f /var/log/app.log /var/log/error.log'
        volumeMounts:
        - name: log-volume
          mountPath: /var/log
      volumes:
      - name: log-volume
        emptyDir: {}
EOF

kubectl apply -f /opt/candidate/log-generator.yaml

# ログ調査
sleep 30  # ログ生成を待つ

echo "=== Kubernetes Logging Analysis ===" > /opt/candidate/logging-analysis.txt
echo "$(date)" >> /opt/candidate/logging-analysis.txt
echo "" >> /opt/candidate/logging-analysis.txt

# アプリケーションログ確認
echo "=== Application Logs ===" >> /opt/candidate/logging-analysis.txt
kubectl logs -l app=log-generator -c app -n logging-test --tail=10 >> /opt/candidate/logging-analysis.txt
echo "" >> /opt/candidate/logging-analysis.txt

# サイドカーログ確認
echo "=== Sidecar Logs ===" >> /opt/candidate/logging-analysis.txt
kubectl logs -l app=log-generator -c log-sidecar -n logging-test --tail=10 >> /opt/candidate/logging-analysis.txt
echo "" >> /opt/candidate/logging-analysis.txt

# ノードレベルログ設定確認
echo "=== Node Log Configuration ===" >> /opt/candidate/logging-analysis.txt
kubectl get nodes -o wide >> /opt/candidate/logging-analysis.txt

# 結果確認
cat /opt/candidate/logging-analysis.txt
```

**採点ポイント:**
- アプリケーションログの確認 (25%)
- サイドカーパターンの実装 (40%)
- ログ設定の調査 (25%)
- レポート作成 (10%)
</details>

---

## 🎯 Question 34: Cluster Upgrade Preparation (8%)

**Context**: cluster: k8s-cluster-1  
**Task**: 
クラスターアップグレードの準備を行ってください：
1. 現在のKubernetesバージョン確認
2. アップグレード可能なバージョン調査
3. アップグレード前のバックアップ取得
4. アップグレード手順書を`/opt/candidate/upgrade-plan.txt`に作成

<details>
<summary>💡 解答例</summary>

```bash
# アップグレード計画書作成
echo "=== Kubernetes Cluster Upgrade Plan ===" > /opt/candidate/upgrade-plan.txt
echo "$(date)" >> /opt/candidate/upgrade-plan.txt
echo "" >> /opt/candidate/upgrade-plan.txt

# 現在のバージョン確認
echo "=== Current Cluster Version ===" >> /opt/candidate/upgrade-plan.txt
kubectl version --short >> /opt/candidate/upgrade-plan.txt
echo "" >> /opt/candidate/upgrade-plan.txt

# ノードのバージョン確認
echo "=== Node Versions ===" >> /opt/candidate/upgrade-plan.txt
kubectl get nodes -o wide >> /opt/candidate/upgrade-plan.txt
echo "" >> /opt/candidate/upgrade-plan.txt

# kubeadmでアップグレード可能なバージョン確認
echo "=== Available Upgrades ===" >> /opt/candidate/upgrade-plan.txt
kubeadm upgrade plan >> /opt/candidate/upgrade-plan.txt 2>&1 || echo "kubeadm upgrade plan failed" >> /opt/candidate/upgrade-plan.txt
echo "" >> /opt/candidate/upgrade-plan.txt

# etcdバックアップ作成
echo "=== ETCD Backup ===" >> /opt/candidate/upgrade-plan.txt
ETCD_POD=$(kubectl get pods -n kube-system -l component=etcd -o jsonpath='{.items[0].metadata.name}')
BACKUP_PATH="/opt/candidate/etcd-backup-$(date +%Y%m%d_%H%M%S).db"

kubectl exec -n kube-system $ETCD_POD -- etcdctl \
  --endpoints=https://127.0.0.1:2379 \
  --cacert=/etc/kubernetes/pki/etcd/ca.crt \
  --cert=/etc/kubernetes/pki/etcd/server.crt \
  --key=/etc/kubernetes/pki/etcd/server.key \
  snapshot save $BACKUP_PATH

echo "ETCD backup created at: $BACKUP_PATH" >> /opt/candidate/upgrade-plan.txt
echo "" >> /opt/candidate/upgrade-plan.txt

# アップグレード手順書作成
cat << UPGRADE_STEPS >> /opt/candidate/upgrade-plan.txt
=== Upgrade Procedure ===

1. Pre-upgrade Checklist:
   - ✓ Backup etcd cluster
   - ✓ Backup /etc/kubernetes/
   - ✓ Verify cluster health
   - ✓ Drain worker nodes

2. Control Plane Upgrade:
   - Update kubeadm on master node
   - Run: kubeadm upgrade plan
   - Run: kubeadm upgrade apply v1.x.x
   - Update kubelet and kubectl
   - Restart kubelet

3. Worker Node Upgrade:
   - Drain node: kubectl drain <node-name> --ignore-daemonsets
   - Update kubeadm, kubelet, kubectl
   - Run: kubeadm upgrade node
   - Restart kubelet
   - Uncordon node: kubectl uncordon <node-name>

4. Post-upgrade Verification:
   - Verify all nodes are Ready
   - Verify all pods are running
   - Run cluster validation tests

5. Rollback Plan:
   - Restore etcd from backup if needed
   - Downgrade kubeadm, kubelet, kubectl
   - Restore configuration files

UPGRADE_STEPS

# 結果確認
cat /opt/candidate/upgrade-plan.txt
```

**採点ポイント:**
- 現在バージョンの正確な確認 (20%)
- アップグレード可能バージョンの調査 (20%)
- etcdバックアップの実行 (30%)
- 詳細な手順書作成 (30%)
</details>

---

## 🎯 Question 35: Application Performance Monitoring (5%)

**Context**: cluster: k8s-cluster-1, namespace: monitoring  
**Task**: 
アプリケーションのパフォーマンス監視を設定してください：
1. CPU/メモリ使用量の高いPodを特定
2. リソース使用量の履歴を記録
3. パフォーマンスレポートを作成

<details>
<summary>💡 解答例</summary>

```bash
# namespaceを作成
kubectl create namespace monitoring

# 負荷生成用Deploymentを作成
cat <<EOF > /opt/candidate/load-generator.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: load-generator
  namespace: monitoring
spec:
  replicas: 3
  selector:
    matchLabels:
      app: load-generator
  template:
    metadata:
      labels:
        app: load-generator
    spec:
      containers:
      - name: cpu-stress
        image: busybox:1.35
        command: ['sh', '-c']
        args:
        - 'while true; do
             for i in 1 2 3 4 5; do
               echo "CPU stress test iteration $i";
               dd if=/dev/zero of=/dev/null count=100000 bs=1024 &
             done;
             sleep 30;
             killall dd 2>/dev/null;
             sleep 30;
           done'
        resources:
          requests:
            cpu: 100m
            memory: 128Mi
          limits:
            cpu: 500m
            memory: 256Mi
EOF

kubectl apply -f /opt/candidate/load-generator.yaml
sleep 60  # 負荷生成を待つ

# パフォーマンス監視レポート作成
echo "=== Application Performance Monitoring Report ===" > /opt/candidate/performance-report.txt
echo "$(date)" >> /opt/candidate/performance-report.txt
echo "" >> /opt/candidate/performance-report.txt

# 全Podのリソース使用量
echo "=== Current Resource Usage (All Pods) ===" >> /opt/candidate/performance-report.txt
kubectl top pods --all-namespaces --sort-by=cpu >> /opt/candidate/performance-report.txt
echo "" >> /opt/candidate/performance-report.txt

# 特定namespace内のリソース使用量
echo "=== Monitoring Namespace Resource Usage ===" >> /opt/candidate/performance-report.txt
kubectl top pods -n monitoring --sort-by=cpu >> /opt/candidate/performance-report.txt
echo "" >> /opt/candidate/performance-report.txt

# ノードレベルのリソース使用量
echo "=== Node Resource Usage ===" >> /opt/candidate/performance-report.txt
kubectl top nodes >> /opt/candidate/performance-report.txt
echo "" >> /opt/candidate/performance-report.txt

# 高使用率Podの詳細分析
echo "=== High CPU Usage Pod Analysis ===" >> /opt/candidate/performance-report.txt
HIGH_CPU_POD=$(kubectl top pods -n monitoring --no-headers --sort-by=cpu | head -1 | awk '{print $1}')
kubectl describe pod $HIGH_CPU_POD -n monitoring | grep -A 20 "Containers:" >> /opt/candidate/performance-report.txt
echo "" >> /opt/candidate/performance-report.txt

# リソース制限と実際の使用量比較
echo "=== Resource Limits vs Usage ===" >> /opt/candidate/performance-report.txt
kubectl get pods -n monitoring -o custom-columns=NAME:.metadata.name,CPU_REQ:.spec.containers[*].resources.requests.cpu,MEM_REQ:.spec.containers[*].resources.requests.memory,CPU_LIM:.spec.containers[*].resources.limits.cpu,MEM_LIM:.spec.containers[*].resources.limits.memory >> /opt/candidate/performance-report.txt

# 結果確認
cat /opt/candidate/performance-report.txt
```

**採点ポイント:**
- リソース使用量の正確な取得 (30%)
- 高使用率Podの特定 (25%)
- 詳細分析の実施 (25%)
- レポート作成 (20%)
</details>

---

## 🎯 Question 36: Service Mesh - Istio Basics (7%)

**Context**: cluster: k8s-cluster-1, namespace: istio-test  
**Task**: 
Service Meshの基本的な設定を行ってください：
1. Istio sidecar injectionの有効化
2. Virtual Serviceの作成
3. Destination Ruleの設定
4. トラフィック分割の実装

<details>
<summary>💡 解答例</summary>

```bash
# namespaceを作成してIstio injection有効化
kubectl create namespace istio-test
kubectl label namespace istio-test istio-injection=enabled

# マイクロサービスアプリケーションをデプロイ
cat <<EOF > /opt/candidate/microservice-app.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: frontend
  namespace: istio-test
spec:
  replicas: 1
  selector:
    matchLabels:
      app: frontend
      version: v1
  template:
    metadata:
      labels:
        app: frontend
        version: v1
    spec:
      containers:
      - name: frontend
        image: nginx:1.20
        ports:
        - containerPort: 80
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: backend-v1
  namespace: istio-test
spec:
  replicas: 1
  selector:
    matchLabels:
      app: backend
      version: v1
  template:
    metadata:
      labels:
        app: backend
        version: v1
    spec:
      containers:
      - name: backend
        image: nginx:1.20
        ports:
        - containerPort: 80
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: backend-v2
  namespace: istio-test
spec:
  replicas: 1
  selector:
    matchLabels:
      app: backend
      version: v2
  template:
    metadata:
      labels:
        app: backend
        version: v2
    spec:
      containers:
      - name: backend
        image: nginx:1.21
        ports:
        - containerPort: 80
---
apiVersion: v1
kind: Service
metadata:
  name: frontend-service
  namespace: istio-test
spec:
  selector:
    app: frontend
  ports:
  - port: 80
    targetPort: 80
---
apiVersion: v1
kind: Service
metadata:
  name: backend-service
  namespace: istio-test
spec:
  selector:
    app: backend
  ports:
  - port: 80
    targetPort: 80
EOF

kubectl apply -f /opt/candidate/microservice-app.yaml

# Istio Virtual Serviceを作成
cat <<EOF > /opt/candidate/virtual-service.yaml
apiVersion: networking.istio.io/v1beta1
kind: VirtualService
metadata:
  name: backend-vs
  namespace: istio-test
spec:
  hosts:
  - backend-service
  http:
  - match:
    - headers:
        user-type:
          exact: premium
    route:
    - destination:
        host: backend-service
        subset: v2
  - route:
    - destination:
        host: backend-service
        subset: v1
      weight: 90
    - destination:
        host: backend-service
        subset: v2
      weight: 10
EOF

# Destination Ruleを作成
cat <<EOF > /opt/candidate/destination-rule.yaml
apiVersion: networking.istio.io/v1beta1
kind: DestinationRule
metadata:
  name: backend-dr
  namespace: istio-test
spec:
  host: backend-service
  subsets:
  - name: v1
    labels:
      version: v1
  - name: v2
    labels:
      version: v2
EOF

# Istio設定を適用（Istioがインストール済みの場合）
kubectl apply -f /opt/candidate/virtual-service.yaml 2>/dev/null || echo "Istio not installed - creating config files only"
kubectl apply -f /opt/candidate/destination-rule.yaml 2>/dev/null || echo "Istio not installed - creating config files only"

# 設定確認
echo "=== Service Mesh Configuration ===" > /opt/candidate/istio-config.txt
echo "$(date)" >> /opt/candidate/istio-config.txt
echo "" >> /opt/candidate/istio-config.txt

echo "=== Namespace Labels ===" >> /opt/candidate/istio-config.txt
kubectl get namespace istio-test --show-labels >> /opt/candidate/istio-config.txt
echo "" >> /opt/candidate/istio-config.txt

echo "=== Pods with Sidecars ===" >> /opt/candidate/istio-config.txt
kubectl get pods -n istio-test -o custom-columns=NAME:.metadata.name,READY:.status.containerStatuses[*].ready,CONTAINERS:.spec.containers[*].name >> /opt/candidate/istio-config.txt
echo "" >> /opt/candidate/istio-config.txt

echo "=== Services ===" >> /opt/candidate/istio-config.txt
kubectl get services -n istio-test >> /opt/candidate/istio-config.txt

# 結果確認
cat /opt/candidate/istio-config.txt
```

**採点ポイント:**
- Istio injection設定 (25%)
- Virtual Service作成 (30%)
- Destination Rule設定 (25%)
- トラフィック分割実装 (20%)
</details>

---

## 🎯 Question 37: Kubernetes API and Custom Controllers (6%)

**Context**: cluster: k8s-cluster-1  
**Task**: 
Kubernetes APIの操作とカスタムコントローラーの基本を実装してください：
1. kubectl proxyを使用したAPI直接アクセス
2. カスタムリソースのCRUD操作
3. Webhook設定の準備

<details>
<summary>💡 解答例</summary>

```bash
# kubectl proxyを起動（バックグラウンド）
kubectl proxy --port=8080 &
PROXY_PID=$!
sleep 5

# API操作レポート作成
echo "=== Kubernetes API Operations ===" > /opt/candidate/api-operations.txt
echo "$(date)" >> /opt/candidate/api-operations.txt
echo "" >> /opt/candidate/api-operations.txt

# 1. API バージョン確認
echo "=== API Versions ===" >> /opt/candidate/api-operations.txt
curl -s http://localhost:8080/api/ | jq . >> /opt/candidate/api-operations.txt 2>/dev/null || curl -s http://localhost:8080/api/ >> /opt/candidate/api-operations.txt
echo "" >> /opt/candidate/api-operations.txt

# 2. Namespace一覧をAPI経由で取得
echo "=== Namespaces via API ===" >> /opt/candidate/api-operations.txt
curl -s http://localhost:8080/api/v1/namespaces | jq '.items[] | .metadata.name' >> /opt/candidate/api-operations.txt 2>/dev/null || curl -s http://localhost:8080/api/v1/namespaces >> /opt/candidate/api-operations.txt
echo "" >> /opt/candidate/api-operations.txt

# 3. カスタムリソース定義の確認
echo "=== Custom Resource Definitions ===" >> /opt/candidate/api-operations.txt
curl -s http://localhost:8080/apis/apiextensions.k8s.io/v1/customresourcedefinitions | jq '.items[] | .metadata.name' >> /opt/candidate/api-operations.txt 2>/dev/null || echo "No CRDs found or jq not available" >> /opt/candidate/api-operations.txt
echo "" >> /opt/candidate/api-operations.txt

# 4. Webhookの設定例を作成
cat <<EOF > /opt/candidate/validating-webhook.yaml
apiVersion: admissionregistration.k8s.io/v1
kind: ValidatingAdmissionWebhook
metadata:
  name: pod-validator
webhooks:
- name: pod-validator.example.com
  clientConfig:
    service:
      name: pod-validator-service
      namespace: webhook
      path: "/validate"
  rules:
  - operations: ["CREATE", "UPDATE"]
    apiGroups: [""]
    apiVersions: ["v1"]
    resources: ["pods"]
  admissionReviewVersions: ["v1"]
  sideEffects: None
  failurePolicy: Fail
EOF

echo "=== Webhook Configuration Created ===" >> /opt/candidate/api-operations.txt
echo "Validating webhook configuration saved to /opt/candidate/validating-webhook.yaml" >> /opt/candidate/api-operations.txt
echo "" >> /opt/candidate/api-operations.txt

# 5. カスタムコントローラーの基本構造例
cat <<EOF > /opt/candidate/controller-example.py
#!/usr/bin/env python3
"""
Example Custom Controller for Kubernetes
This is a basic template for a custom controller
"""

import time
import kubernetes
from kubernetes import client, config, watch

def main():
    # Load kubeconfig
    config.load_incluster_config()  # For in-cluster
    # config.load_kube_config()  # For local development
    
    v1 = client.CoreV1Api()
    
    # Watch for Pod events
    w = watch.Watch()
    for event in w.stream(v1.list_pod_for_all_namespaces):
        event_type = event['type']
        pod = event['object']
        
        print(f"Event: {event_type} Pod: {pod.metadata.name} Namespace: {pod.metadata.namespace}")
        
        # Custom logic here
        if event_type == "ADDED":
            handle_pod_added(pod)
        elif event_type == "DELETED":
            handle_pod_deleted(pod)

def handle_pod_added(pod):
    # Custom logic for pod creation
    print(f"Handling new pod: {pod.metadata.name}")

def handle_pod_deleted(pod):
    # Custom logic for pod deletion
    print(f"Handling deleted pod: {pod.metadata.name}")

if __name__ == "__main__":
    main()
EOF

echo "=== Custom Controller Example ===" >> /opt/candidate/api-operations.txt
echo "Controller template saved to /opt/candidate/controller-example.py" >> /opt/candidate/api-operations.txt

# proxy停止
kill $PROXY_PID 2>/dev/null

# 結果確認
cat /opt/candidate/api-operations.txt
```

**採点ポイント:**
- kubectl proxyの使用 (20%)
- API直接アクセス (30%)
- Webhook設定準備 (25%)
- コントローラー例の作成 (25%)
</details>

---

## 🎯 Question 38: Cluster Autoscaling (5%)

**Context**: cluster: k8s-cluster-1, namespace: autoscaling  
**Task**: 
クラスターオートスケーリングの設定と動作確認を行ってください：
1. Cluster Autoscalerの設定確認
2. ノードスケーリングのトリガー作成
3. スケーリング動作の監視

<details>
<summary>💡 解答例</summary>

```bash
# namespaceを作成
kubectl create namespace autoscaling

# Cluster Autoscaler設定確認
echo "=== Cluster Autoscaling Configuration ===" > /opt/candidate/autoscaling-config.txt
echo "$(date)" >> /opt/candidate/autoscaling-config.txt
echo "" >> /opt/candidate/autoscaling-config.txt

# ノード情報確認
echo "=== Current Node Information ===" >> /opt/candidate/autoscaling-config.txt
kubectl get nodes -o wide >> /opt/candidate/autoscaling-config.txt
echo "" >> /opt/candidate/autoscaling-config.txt

# Cluster Autoscaler Podの確認
echo "=== Cluster Autoscaler Pod ===" >> /opt/candidate/autoscaling-config.txt
kubectl get pods -n kube-system | grep cluster-autoscaler >> /opt/candidate/autoscaling-config.txt || echo "Cluster Autoscaler not found" >> /opt/candidate/autoscaling-config.txt
echo "" >> /opt/candidate/autoscaling-config.txt

# リソース消費の大きいDeploymentを作成（スケールアウトトリガー用）
cat <<EOF > /opt/candidate/resource-intensive-app.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: resource-intensive-app
  namespace: autoscaling
spec:
  replicas: 1
  selector:
    matchLabels:
      app: resource-intensive-app
  template:
    metadata:
      labels:
        app: resource-intensive-app
    spec:
      containers:
      - name: app
        image: nginx:1.20
        resources:
          requests:
            cpu: 1000m    # 1 CPU core request
            memory: 2Gi   # 2GB memory request
          limits:
            cpu: 2000m
            memory: 4Gi
EOF

kubectl apply -f /opt/candidate/resource-intensive-app.yaml

# HPAも作成してPodレベルでのスケーリングも設定
cat <<EOF > /opt/candidate/hpa-config.yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: resource-intensive-hpa
  namespace: autoscaling
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: resource-intensive-app
  minReplicas: 1
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 50
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 70
EOF

kubectl apply -f /opt/candidate/hpa-config.yaml

# リソース使用量と制約の監視
echo "=== Resource Usage Monitoring ===" >> /opt/candidate/autoscaling-config.txt
kubectl top nodes >> /opt/candidate/autoscaling-config.txt 2>/dev/null || echo "Metrics server not available" >> /opt/candidate/autoscaling-config.txt
echo "" >> /opt/candidate/autoscaling-config.txt

# HPAの状態確認
echo "=== HPA Status ===" >> /opt/candidate/autoscaling-config.txt
kubectl get hpa -n autoscaling >> /opt/candidate/autoscaling-config.txt
echo "" >> /opt/candidate/autoscaling-config.txt

# Pod状態確認
echo "=== Pod Status ===" >> /opt/candidate/autoscaling-config.txt
kubectl get pods -n autoscaling -o wide >> /opt/candidate/autoscaling-config.txt
echo "" >> /opt/candidate/autoscaling-config.txt

# イベント確認
echo "=== Recent Events ===" >> /opt/candidate/autoscaling-config.txt
kubectl get events -n autoscaling --sort-by=.metadata.creationTimestamp | tail -10 >> /opt/candidate/autoscaling-config.txt

# レプリカ数を増やしてスケーリングをトリガー
kubectl scale deployment resource-intensive-app --replicas=5 -n autoscaling

echo "" >> /opt/candidate/autoscaling-config.txt
echo "=== Scaling Triggered ===" >> /opt/candidate/autoscaling-config.txt
echo "Deployment scaled to 5 replicas to trigger autoscaling" >> /opt/candidate/autoscaling-config.txt

# 結果確認
cat /opt/candidate/autoscaling-config.txt
```

**採点ポイント:**
- Cluster Autoscaler設定確認 (25%)
- スケーリングトリガー作成 (35%)
- HPA設定 (25%)
- 監視とレポート作成 (15%)
</details>

---

## 🎯 Question 39: Network Troubleshooting - DNS Issues (7%)

**Context**: cluster: k8s-cluster-1, namespace: dns-debug  
**Task**: 
DNS関連の問題をトラブルシューティングしてください：
1. クラスターDNSサービスの状態確認
2. Pod間の名前解決テスト
3. DNS設定の検証と修正

<details>
<summary>💡 解答例</summary>

```bash
# namespaceを作成
kubectl create namespace dns-debug

# DNS トラブルシューティングレポート作成
echo "=== DNS Troubleshooting Report ===" > /opt/candidate/dns-troubleshooting.txt
echo "$(date)" >> /opt/candidate/dns-troubleshooting.txt
echo "" >> /opt/candidate/dns-troubleshooting.txt

# 1. クラスターDNSサービス確認
echo "=== Cluster DNS Service Status ===" >> /opt/candidate/dns-troubleshooting.txt
kubectl get svc -n kube-system | grep dns >> /opt/candidate/dns-troubleshooting.txt
echo "" >> /opt/candidate/dns-troubleshooting.txt

# CoreDNS Pod状態確認
echo "=== CoreDNS Pod Status ===" >> /opt/candidate/dns-troubleshooting.txt
kubectl get pods -n kube-system -l k8s-app=kube-dns >> /opt/candidate/dns-troubleshooting.txt
echo "" >> /opt/candidate/dns-troubleshooting.txt

# CoreDNS設定確認
echo "=== CoreDNS Configuration ===" >> /opt/candidate/dns-troubleshooting.txt
kubectl get configmap coredns -n kube-system -o yaml | grep -A 20 Corefile >> /opt/candidate/dns-troubleshooting.txt
echo "" >> /opt/candidate/dns-troubleshooting.txt

# テスト用Podを作成
cat <<EOF > /opt/candidate/dns-test-pods.yaml
apiVersion: v1
kind: Pod
metadata:
  name: dns-test-client
  namespace: dns-debug
spec:
  containers:
  - name: client
    image: busybox:1.35
    command: ['sh', '-c', 'sleep 3600']
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: test-service
  namespace: dns-debug
spec:
  replicas: 1
  selector:
    matchLabels:
      app: test-service
  template:
    metadata:
      labels:
        app: test-service
    spec:
      containers:
      - name: server
        image: nginx:1.20
        ports:
        - containerPort: 80
---
apiVersion: v1
kind: Service
metadata:
  name: test-service
  namespace: dns-debug
spec:
  selector:
    app: test-service
  ports:
  - port: 80
    targetPort: 80
EOF

kubectl apply -f /opt/candidate/dns-test-pods.yaml
kubectl wait --for=condition=Ready pod/dns-test-client -n dns-debug --timeout=300s

# 2. DNS解決テスト実行
echo "=== DNS Resolution Tests ===" >> /opt/candidate/dns-troubleshooting.txt

# サービス名解決テスト
echo "--- Service Name Resolution ---" >> /opt/candidate/dns-troubleshooting.txt
kubectl exec dns-test-client -n dns-debug -- nslookup test-service >> /opt/candidate/dns-troubleshooting.txt 2>&1
echo "" >> /opt/candidate/dns-troubleshooting.txt

# FQDN解決テスト
echo "--- FQDN Resolution ---" >> /opt/candidate/dns-troubleshooting.txt
kubectl exec dns-test-client -n dns-debug -- nslookup test-service.dns-debug.svc.cluster.local >> /opt/candidate/dns-troubleshooting.txt 2>&1
echo "" >> /opt/candidate/dns-troubleshooting.txt

# 外部DNS解決テスト
echo "--- External DNS Resolution ---" >> /opt/candidate/dns-troubleshooting.txt
kubectl exec dns-test-client -n dns-debug -- nslookup google.com >> /opt/candidate/dns-troubleshooting.txt 2>&1
echo "" >> /opt/candidate/dns-troubleshooting.txt

# Pod内のresolv.conf確認
echo "=== Pod DNS Configuration ===" >> /opt/candidate/dns-troubleshooting.txt
kubectl exec dns-test-client -n dns-debug -- cat /etc/resolv.conf >> /opt/candidate/dns-troubleshooting.txt
echo "" >> /opt/candidate/dns-troubleshooting.txt

# DNSポリシー確認
echo "=== DNS Policy Configuration ===" >> /opt/candidate/dns-troubleshooting.txt
kubectl get pod dns-test-client -n dns-debug -o yaml | grep -A 5 dnsPolicy >> /opt/candidate/dns-troubleshooting.txt
echo "" >> /opt/candidate/dns-troubleshooting.txt

# CoreDNSログ確認
echo "=== CoreDNS Logs ===" >> /opt/candidate/dns-troubleshooting.txt
COREDNS_POD=$(kubectl get pods -n kube-system -l k8s-app=kube-dns -o jsonpath='{.items[0].metadata.name}')
kubectl logs $COREDNS_POD -n kube-system --tail=10 >> /opt/candidate/dns-troubleshooting.txt
echo "" >> /opt/candidate/dns-troubleshooting.txt

# 修正提案
echo "=== Troubleshooting Recommendations ===" >> /opt/candidate/dns-troubleshooting.txt
cat << RECOMMENDATIONS >> /opt/candidate/dns-troubleshooting.txt
1. If DNS resolution fails:
   - Check CoreDNS pod status and logs
   - Verify kube-dns service is running
   - Confirm DNS policy in pod specification

2. If external DNS fails:
   - Check CoreDNS forward configuration
   - Verify upstream DNS servers
   - Check network connectivity from nodes

3. If service discovery fails:
   - Verify service endpoints exist
   - Check service selector labels
   - Confirm namespace isolation settings

4. Common fixes:
   - Restart CoreDNS pods: kubectl rollout restart deployment/coredns -n kube-system
   - Check cluster DNS IP: kubectl get svc kube-dns -n kube-system
   - Verify kubelet DNS settings on nodes
RECOMMENDATIONS

# 結果確認
cat /opt/candidate/dns-troubleshooting.txt
```

**採点ポイント:**
- DNS サービス状態確認 (25%)
- DNS解決テストの実行 (35%)
- 設定の検証 (25%)
- トラブルシューティング提案 (15%)
</details>

---

## 🎯 Question 40: Backup and Disaster Recovery (6%)

**Context**: cluster: k8s-cluster-1  
**Task**: 
バックアップと災害復旧の実装を行ってください：
1. etcdクラスターの完全バックアップ
2. 永続ボリュームのバックアップ戦略
3. 復旧手順書の作成
4. バックアップの自動化スクリプト作成

<details>
<summary>💡 解答例</summary>

```bash
# バックアップディレクトリ作成
mkdir -p /opt/candidate/backups
BACKUP_DIR="/opt/candidate/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# 災害復旧計画書作成
echo "=== Kubernetes Backup and Disaster Recovery Plan ===" > /opt/candidate/disaster-recovery-plan.txt
echo "$(date)" >> /opt/candidate/disaster-recovery-plan.txt
echo "" >> /opt/candidate/disaster-recovery-plan.txt

# 1. etcdバックアップの実行
echo "=== ETCD Backup Procedure ===" >> /opt/candidate/disaster-recovery-plan.txt
ETCD_POD=$(kubectl get pods -n kube-system -l component=etcd -o jsonpath='{.items[0].metadata.name}')

# etcdバックアップ実行
kubectl exec -n kube-system $ETCD_POD -- etcdctl \
  --endpoints=https://127.0.0.1:2379 \
  --cacert=/etc/kubernetes/pki/etcd/ca.crt \
  --cert=/etc/kubernetes/pki/etcd/server.crt \
  --key=/etc/kubernetes/pki/etcd/server.key \
  snapshot save /tmp/etcd-backup-$TIMESTAMP.db

# バックアップファイルをローカルにコピー
kubectl cp kube-system/$ETCD_POD:/tmp/etcd-backup-$TIMESTAMP.db $BACKUP_DIR/etcd-backup-$TIMESTAMP.db

echo "ETCD backup completed: $BACKUP_DIR/etcd-backup-$TIMESTAMP.db" >> /opt/candidate/disaster-recovery-plan.txt
echo "" >> /opt/candidate/disaster-recovery-plan.txt

# 2. Kubernetesリソースのバックアップ
echo "=== Kubernetes Resources Backup ===" >> /opt/candidate/disaster-recovery-plan.txt

# 全namespaceのリソースをバックアップ
for ns in $(kubectl get ns -o jsonpath='{.items[*].metadata.name}'); do
  mkdir -p $BACKUP_DIR/resources/$ns
  
  # Deployments
  kubectl get deployments -n $ns -o yaml > $BACKUP_DIR/resources/$ns/deployments.yaml 2>/dev/null
  
  # Services
  kubectl get services -n $ns -o yaml > $BACKUP_DIR/resources/$ns/services.yaml 2>/dev/null
  
  # ConfigMaps
  kubectl get configmaps -n $ns -o yaml > $BACKUP_DIR/resources/$ns/configmaps.yaml 2>/dev/null
  
  # Secrets
  kubectl get secrets -n $ns -o yaml > $BACKUP_DIR/resources/$ns/secrets.yaml 2>/dev/null
done

echo "Kubernetes resources backed up to: $BACKUP_DIR/resources/" >> /opt/candidate/disaster-recovery-plan.txt
echo "" >> /opt/candidate/disaster-recovery-plan.txt

# 3. 永続ボリューム情報のバックアップ
echo "=== Persistent Volumes Backup Info ===" >> /opt/candidate/disaster-recovery-plan.txt
kubectl get pv -o yaml > $BACKUP_DIR/persistent-volumes.yaml
kubectl get pvc --all-namespaces -o yaml > $BACKUP_DIR/persistent-volume-claims.yaml

# PV情報をレポートに記録
kubectl get pv >> /opt/candidate/disaster-recovery-plan.txt
echo "" >> /opt/candidate/disaster-recovery-plan.txt

# 4. 自動バックアップスクリプト作成
cat <<'EOF' > /opt/candidate/automated-backup.sh
#!/bin/bash

# Kubernetes Automated Backup Script
BACKUP_BASE_DIR="/opt/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="$BACKUP_BASE_DIR/$TIMESTAMP"
RETENTION_DAYS=7

echo "Starting automated backup at $(date)"

# Create backup directory
mkdir -p $BACKUP_DIR

# 1. ETCD Backup
echo "Creating ETCD backup..."
ETCD_POD=$(kubectl get pods -n kube-system -l component=etcd -o jsonpath='{.items[0].metadata.name}')

kubectl exec -n kube-system $ETCD_POD -- etcdctl \
  --endpoints=https://127.0.0.1:2379 \
  --cacert=/etc/kubernetes/pki/etcd/ca.crt \
  --cert=/etc/kubernetes/pki/etcd/server.crt \
  --key=/etc/kubernetes/pki/etcd/server.key \
  snapshot save /tmp/etcd-backup-$TIMESTAMP.db

kubectl cp kube-system/$ETCD_POD:/tmp/etcd-backup-$TIMESTAMP.db $BACKUP_DIR/etcd-backup.db

# 2. Kubernetes Resources
echo "Backing up Kubernetes resources..."
mkdir -p $BACKUP_DIR/resources

for ns in $(kubectl get ns -o jsonpath='{.items[*].metadata.name}'); do
  mkdir -p $BACKUP_DIR/resources/$ns
  kubectl get all,cm,secrets,pvc -n $ns -o yaml > $BACKUP_DIR/resources/$ns/all-resources.yaml 2>/dev/null
done

# 3. Cluster-wide resources
kubectl get nodes -o yaml > $BACKUP_DIR/nodes.yaml
kubectl get pv -o yaml > $BACKUP_DIR/persistent-volumes.yaml
kubectl get crd -o yaml > $BACKUP_DIR/custom-resource-definitions.yaml

# 4. Cleanup old backups
echo "Cleaning up backups older than $RETENTION_DAYS days..."
find $BACKUP_BASE_DIR -type d -mtime +$RETENTION_DAYS -exec rm -rf {} + 2>/dev/null

# 5. Verify backup
if [ -f "$BACKUP_DIR/etcd-backup.db" ]; then
  echo "Backup completed successfully: $BACKUP_DIR"
  # Send notification (add your notification logic here)
  # curl -X POST -H 'Content-Type: application/json' -d '{"text":"Backup completed: '$BACKUP_DIR'"}' $SLACK_WEBHOOK
else
  echo "ERROR: Backup failed!"
  exit 1
fi

echo "Backup completed at $(date)"
EOF

chmod +x /opt/candidate/automated-backup.sh

# 5. 復旧手順書作成
cat << RECOVERY_PROCEDURE >> /opt/candidate/disaster-recovery-plan.txt

=== Disaster Recovery Procedures ===

1. ETCD Cluster Recovery:
   a. Stop kube-apiserver on all master nodes
   b. Stop etcd on all etcd nodes
   c. Remove existing etcd data directory
   d. Restore from backup:
      etcdctl snapshot restore /path/to/backup.db \\
        --data-dir=/var/lib/etcd \\
        --name=<node-name> \\
        --initial-cluster=<cluster-info> \\
        --initial-cluster-token=<token> \\
        --initial-advertise-peer-urls=<peer-urls>
   e. Start etcd service
   f. Start kube-apiserver

2. Kubernetes Resources Recovery:
   kubectl apply -f /path/to/backup/resources/

3. Persistent Volume Recovery:
   - Restore underlying storage (depends on storage provider)
   - Recreate PV objects: kubectl apply -f persistent-volumes.yaml
   - Verify PVC binding

4. Verification Steps:
   - kubectl get nodes
   - kubectl get pods --all-namespaces
   - kubectl get pv,pvc
   - Verify application functionality

5. Automated Backup Schedule:
   Add to crontab: 0 2 * * * /opt/candidate/automated-backup.sh

=== Recovery Time Objectives ===
- ETCD Recovery: 15-30 minutes
- Application Recovery: 30-60 minutes
- Full Cluster Recovery: 1-2 hours

=== Recovery Point Objectives ===
- ETCD: Last snapshot (hourly backups recommended)
- Application Data: Depends on storage backup frequency

RECOVERY_PROCEDURE

echo "Automated backup script created: /opt/candidate/automated-backup.sh" >> /opt/candidate/disaster-recovery-plan.txt

# 結果確認
echo "" >> /opt/candidate/disaster-recovery-plan.txt
echo "=== Backup Summary ===" >> /opt/candidate/disaster-recovery-plan.txt
echo "ETCD Backup: $(ls -lh $BACKUP_DIR/etcd-backup-$TIMESTAMP.db)" >> /opt/candidate/disaster-recovery-plan.txt
echo "Resources Backup: $(du -sh $BACKUP_DIR/resources)" >> /opt/candidate/disaster-recovery-plan.txt
echo "Total Backup Size: $(du -sh $BACKUP_DIR)" >> /opt/candidate/disaster-recovery-plan.txt

cat /opt/candidate/disaster-recovery-plan.txt
```

**採点ポイント:**
- etcdバックアップの実行 (30%)
- Kubernetesリソースバックアップ (25%)
- 復旧手順書の作成 (25%)
- 自動化スクリプトの作成 (20%)
</details>

---

**次のステップ**: [Practice Exam 2](./practice-exam-02.md) でより高度な問題に挑戦してください。