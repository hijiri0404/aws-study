# CKAD - よくある問題と解決策

## 📋 概要

CKAD試験と実際のKubernetes開発でよく遭遇する問題とその解決策をまとめています。実技試験での効率的なトラブルシューティング手順も含めて解説します。

## 🚨 Core Concepts - Pod関連

### 問題1: Pod が Pending 状態のまま

#### 症状
```bash
kubectl get pods
NAME        READY   STATUS    RESTARTS   AGE
my-pod      0/1     Pending   0          5m
```

#### 原因分析と解決
```bash
# 1. 詳細情報確認
kubectl describe pod my-pod

# よくある原因と解決策
# - リソース不足
kubectl top nodes
kubectl describe nodes

# - PersistentVolume の問題
kubectl get pv
kubectl get pvc

# - ImagePullBackOff
kubectl describe pod my-pod | grep -A5 Events

# 2. Node セレクター問題
kubectl get nodes --show-labels
# Pod の nodeSelector 確認
kubectl get pod my-pod -o yaml | grep -A5 nodeSelector
```

#### 予防策
```yaml
# リソース制限を適切に設定
apiVersion: v1
kind: Pod
metadata:
  name: resource-aware-pod
spec:
  containers:
  - name: app
    image: nginx
    resources:
      requests:
        memory: "64Mi"
        cpu: "250m"
      limits:
        memory: "128Mi"
        cpu: "500m"
```

### 問題2: Pod が CrashLoopBackOff

#### 症状
```bash
kubectl get pods
NAME        READY   STATUS             RESTARTS   AGE
my-pod      0/1     CrashLoopBackOff   5          10m
```

#### 解決手順
```bash
# 1. ログ確認
kubectl logs my-pod
kubectl logs my-pod --previous

# 2. コンテナ内で直接確認
kubectl exec -it my-pod -- sh
# または
kubectl run debug --image=busybox -it --rm -- sh

# 3. Startup Probe の調整
kubectl patch pod my-pod -p '{
  "spec": {
    "containers": [
      {
        "name": "app",
        "startupProbe": {
          "initialDelaySeconds": 30,
          "periodSeconds": 10,
          "failureThreshold": 30
        }
      }
    ]
  }
}'
```

#### 修正例
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: stable-pod
spec:
  containers:
  - name: app
    image: nginx
    # 適切なヘルスチェック設定
    livenessProbe:
      httpGet:
        path: /
        port: 80
      initialDelaySeconds: 30
      periodSeconds: 10
    readinessProbe:
      httpGet:
        path: /
        port: 80
      initialDelaySeconds: 5
      periodSeconds: 5
```

### 問題3: Multi-container Pod の通信問題

#### 症状
- サイドカーコンテナが主コンテナと通信できない
- 共有ボリュームにアクセスできない

#### 解決手順
```bash
# 1. コンテナ間通信確認
kubectl exec -it multi-pod -c container1 -- curl localhost:8080
kubectl exec -it multi-pod -c container2 -- netstat -tlnp

# 2. ボリュームマウント確認
kubectl exec -it multi-pod -c container1 -- ls -la /shared
kubectl exec -it multi-pod -c container2 -- ls -la /shared

# 3. ログで各コンテナの状態確認
kubectl logs multi-pod -c container1
kubectl logs multi-pod -c container2
```

#### 正しい設定例
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: multi-container-pod
spec:
  containers:
  - name: main-app
    image: nginx
    ports:
    - containerPort: 80
    volumeMounts:
    - name: shared-data
      mountPath: /usr/share/nginx/html
  - name: sidecar
    image: busybox
    command: ['sh', '-c', 'while true; do echo $(date) > /shared/timestamp.html; sleep 30; done']
    volumeMounts:
    - name: shared-data
      mountPath: /shared
  volumes:
  - name: shared-data
    emptyDir: {}
```

## ⚙️ Configuration - ConfigMap/Secret関連

### 問題4: ConfigMap の値が Pod に反映されない

#### 症状
- 環境変数として設定した値が取得できない
- ボリュームマウントしたファイルが空

#### 解決手順
```bash
# 1. ConfigMap の存在確認
kubectl get configmap my-config -o yaml

# 2. Pod での環境変数確認
kubectl exec -it my-pod -- env | grep MY_VAR

# 3. マウントされたファイル確認
kubectl exec -it my-pod -- cat /config/app.properties

# 4. ConfigMap 更新後のPod再起動
kubectl rollout restart deployment my-deployment
```

#### 正しい設定例
```yaml
# ConfigMap作成
apiVersion: v1
kind: ConfigMap
metadata:
  name: app-config
data:
  database_url: "postgresql://localhost:5432/myapp"
  app.properties: |
    server.port=8080
    app.name=myapp
---
# Pod設定
apiVersion: v1
kind: Pod
metadata:
  name: app-pod
spec:
  containers:
  - name: app
    image: nginx
    env:
    - name: DB_URL
      valueFrom:
        configMapKeyRef:
          name: app-config
          key: database_url
    volumeMounts:
    - name: config-volume
      mountPath: /config
  volumes:
  - name: config-volume
    configMap:
      name: app-config
      items:
      - key: app.properties
        path: app.properties
```

### 問題5: Secret が Base64 デコードされない

#### 症状
- 環境変数にBase64エンコードされた値が設定される
- アプリケーションが認証に失敗

#### 解決手順
```bash
# 1. Secret の内容確認
kubectl get secret my-secret -o yaml

# 2. デコードして確認
kubectl get secret my-secret -o jsonpath='{.data.password}' | base64 -d

# 3. 正しく参照されているか確認
kubectl exec -it my-pod -- echo $PASSWORD
```

#### 正しい設定例
```bash
# Secret作成（自動でBase64エンコード）
kubectl create secret generic db-secret \
  --from-literal=username=admin \
  --from-literal=password=secretpassword

# Pod設定（自動でデコードされる）
apiVersion: v1
kind: Pod
metadata:
  name: app-pod
spec:
  containers:
  - name: app
    image: nginx
    env:
    - name: DB_USER
      valueFrom:
        secretKeyRef:
          name: db-secret
          key: username
    - name: DB_PASS
      valueFrom:
        secretKeyRef:
          name: db-secret
          key: password
```

## 🔄 Pod Design - Deployment/Job関連

### 問題6: Deployment のローリングアップデートが進まない

#### 症状
```bash
kubectl get deployments
NAME           READY   UP-TO-DATE   AVAILABLE   AGE
my-deployment  2/3     1            2           10m
```

#### 解決手順
```bash
# 1. ローリングアップデート状態確認
kubectl rollout status deployment/my-deployment

# 2. ReplicaSet の状態確認
kubectl get replicasets

# 3. 詳細なイベント確認
kubectl describe deployment my-deployment

# 4. Pod の状態確認
kubectl get pods -l app=my-app

# 5. 必要に応じてロールバック
kubectl rollout undo deployment/my-deployment
```

#### 正しい設定例
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: my-deployment
spec:
  replicas: 3
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 1
  selector:
    matchLabels:
      app: my-app
  template:
    metadata:
      labels:
        app: my-app
    spec:
      containers:
      - name: app
        image: nginx:1.20
        readinessProbe:
          httpGet:
            path: /
            port: 80
          initialDelaySeconds: 5
          periodSeconds: 5
```

### 問題7: Job が完了しない

#### 症状
```bash
kubectl get jobs
NAME      COMPLETIONS   DURATION   AGE
my-job    0/1           5m         5m
```

#### 解決手順
```bash
# 1. Job の詳細確認
kubectl describe job my-job

# 2. Pod の状態確認
kubectl get pods -l job-name=my-job

# 3. Pod のログ確認
kubectl logs -l job-name=my-job

# 4. Job の設定確認
kubectl get job my-job -o yaml
```

#### 正しい設定例
```yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: successful-job
spec:
  completions: 1
  backoffLimit: 3
  template:
    spec:
      restartPolicy: Never  # 重要: OnFailure または Never
      containers:
      - name: job-container
        image: busybox
        command: ['sh', '-c', 'echo "Job completed successfully" && exit 0']
```

### 問題8: CronJob が期待した時間に実行されない

#### 症状
- CronJob が全く実行されない
- 想定と異なる時間に実行される

#### 解決手順
```bash
# 1. CronJob の状態確認
kubectl get cronjobs

# 2. 過去の実行履歴確認
kubectl get jobs

# 3. CronJob の詳細確認
kubectl describe cronjob my-cronjob

# 4. タイムゾーン確認
kubectl get cronjob my-cronjob -o yaml | grep timeZone
```

#### 正しい設定例
```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: scheduled-job
spec:
  schedule: "0 2 * * *"  # 毎日午前2時（UTC）
  timeZone: "Asia/Tokyo"  # タイムゾーン指定
  jobTemplate:
    spec:
      template:
        spec:
          restartPolicy: OnFailure
          containers:
          - name: job
            image: busybox
            command: ['sh', '-c', 'date && echo "Scheduled job executed"']
```

## 🌐 Services & Networking

### 問題9: Service で Pod にアクセスできない

#### 症状
```bash
kubectl exec -it test-pod -- curl my-service
curl: (6) Could not resolve host: my-service
```

#### 解決手順
```bash
# 1. Service の存在確認
kubectl get services

# 2. Endpoints の確認
kubectl get endpoints my-service

# 3. セレクターとラベルの一致確認
kubectl get service my-service -o yaml | grep -A5 selector
kubectl get pods --show-labels

# 4. DNS解決確認
kubectl exec -it test-pod -- nslookup my-service
kubectl exec -it test-pod -- cat /etc/resolv.conf

# 5. ネットワークポリシー確認
kubectl get networkpolicies
```

#### 正しい設定例
```yaml
# Service
apiVersion: v1
kind: Service
metadata:
  name: my-service
spec:
  selector:
    app: my-app  # Pod のラベルと一致させる
  ports:
  - port: 80
    targetPort: 8080
---
# Pod
apiVersion: v1
kind: Pod
metadata:
  name: my-pod
  labels:
    app: my-app  # Service のselectorと一致
spec:
  containers:
  - name: app
    image: nginx
    ports:
    - containerPort: 8080
```

### 問題10: Ingress でアクセスできない

#### 症状
- 外部からIngress経由でアクセスできない
- 502/503エラーが発生

#### 解決手順
```bash
# 1. Ingress Controller の状態確認
kubectl get pods -n ingress-nginx

# 2. Ingress リソースの確認
kubectl get ingress
kubectl describe ingress my-ingress

# 3. Service の確認
kubectl get service backend-service

# 4. DNS設定確認
nslookup myapp.example.com
```

#### 正しい設定例
```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: my-ingress
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
            name: my-service
            port:
              number: 80
```

## 💾 State Persistence

### 問題11: PersistentVolumeClaim が Pending

#### 症状
```bash
kubectl get pvc
NAME      STATUS    VOLUME   CAPACITY   ACCESS MODES   STORAGECLASS   AGE
my-pvc    Pending                                      standard       5m
```

#### 解決手順
```bash
# 1. 利用可能なPV確認
kubectl get pv

# 2. StorageClass 確認
kubectl get storageclass

# 3. PVC の詳細確認
kubectl describe pvc my-pvc

# 4. Dynamic provisioning の確認
kubectl get sc default -o yaml
```

#### 正しい設定例
```yaml
# PVC
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: my-pvc
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 1Gi
  storageClassName: standard
---
# Pod でのPVC使用
apiVersion: v1
kind: Pod
metadata:
  name: pvc-pod
spec:
  containers:
  - name: app
    image: nginx
    volumeMounts:
    - name: storage
      mountPath: /data
  volumes:
  - name: storage
    persistentVolumeClaim:
      claimName: my-pvc
```

## 🔍 Observability

### 問題12: Liveness Probe でPodが再起動を繰り返す

#### 症状
```bash
kubectl get pods
NAME      READY   STATUS    RESTARTS   AGE
my-pod    1/1     Running   10         5m
```

#### 解決手順
```bash
# 1. Pod の詳細とイベント確認
kubectl describe pod my-pod

# 2. アプリケーションの起動時間確認
kubectl logs my-pod --previous

# 3. ヘルスチェックエンドポイント確認
kubectl exec -it my-pod -- curl localhost:8080/health

# 4. Probe 設定の調整
kubectl patch pod my-pod -p '{
  "spec": {
    "containers": [
      {
        "name": "app",
        "livenessProbe": {
          "initialDelaySeconds": 60,
          "periodSeconds": 30,
          "timeoutSeconds": 10,
          "failureThreshold": 3
        }
      }
    ]
  }
}'
```

#### 正しい設定例
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: healthy-pod
spec:
  containers:
  - name: app
    image: nginx
    livenessProbe:
      httpGet:
        path: /
        port: 80
      initialDelaySeconds: 30  # 十分な起動時間を確保
      periodSeconds: 10
      timeoutSeconds: 5
      failureThreshold: 3
    readinessProbe:
      httpGet:
        path: /
        port: 80
      initialDelaySeconds: 5
      periodSeconds: 5
      timeoutSeconds: 3
      failureThreshold: 3
```

## 🛠️ 試験対策のための効率的デバッグ

### 高速診断コマンド集

```bash
# 基本状態確認
alias k=kubectl
k get all
k get events --sort-by=.metadata.creationTimestamp

# Pod 関連
k get pods -o wide
k describe pod <pod-name>
k logs <pod-name> --previous
k exec -it <pod-name> -- sh

# Service 関連
k get svc,ep
k describe svc <service-name>

# 設定関連
k get cm,secret
k describe cm <configmap-name>

# ネットワーク関連
k get ing,netpol
k describe ing <ingress-name>
```

### YAML作成の効率化

```bash
# Dry-run でテンプレート生成
k run pod-name --image=nginx --dry-run=client -o yaml > pod.yaml
k create deployment dep-name --image=nginx --dry-run=client -o yaml > deployment.yaml
k expose deployment dep-name --port=80 --dry-run=client -o yaml > service.yaml

# 既存リソースからテンプレート
k get pod existing-pod -o yaml > template.yaml
```

### 時間節約のためのエイリアス

```bash
# .bashrc に追加
alias k=kubectl
alias kgp='kubectl get pods'
alias kgs='kubectl get svc'
alias kgd='kubectl get deployment'
alias kdp='kubectl describe pod'
alias kds='kubectl describe svc'
alias kl='kubectl logs'
alias ke='kubectl exec -it'
export do='--dry-run=client -o yaml'
export now='--force --grace-period=0'
```

## 📚 予防策とベストプラクティス

### 1. リソース管理
- 適切なリソース制限設定
- QoS クラスの理解
- Node のリソース監視

### 2. ヘルスチェック
- 適切なProbe設定
- アプリケーション起動時間の考慮
- Graceful shutdown の実装

### 3. ネットワーク
- Service とPod ラベルの一致
- DNS設定の確認
- Network Policy の理解

### 4. ストレージ
- PVC のライフサイクル理解
- StorageClass の選択
- バックアップ戦略

---

**重要**: CKAD試験では制限時間内での問題解決が求められます。基本的なトラブルシューティングコマンドを覚え、効率的なワークフローを身につけることが合格の鍵です。