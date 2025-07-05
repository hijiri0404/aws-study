# CKAD Practice Exam 1 - アプリケーション開発と管理

## 📋 試験情報

**時間制限**: 120分  
**問題数**: 19問  
**合格点**: 66%  
**環境**: Kubernetes v1.28  

**重要な注意事項:**
- 実際のKubernetesクラスターでの実技試験です
- 各問題で指定されたnamespaceを使用してください
- すべてのYAMLマニフェストは`/opt/candidate/`に保存してください
- 試験中は [kubernetes.io](https://kubernetes.io) のドキュメントが参照可能です

---

## 🎯 Question 1: Pod作成とラベル管理 (3%)

**Context**: namespace: `app-development`  
**Task**: 
以下の要件でPodを作成してください：
- 名前: `web-server`
- イメージ: `nginx:1.20`
- ラベル: `app=web`, `version=v1`, `environment=production`
- ポート: 80

作成後、ラベル `tier=frontend` を追加してください。

<details>
<summary>💡 解答例</summary>

```bash
# namespace作成
kubectl create namespace app-development

# Podを作成
kubectl run web-server --image=nginx:1.20 --port=80 \
  --labels="app=web,version=v1,environment=production" \
  -n app-development

# または、YAMLファイルで作成
cat <<EOF > /opt/candidate/web-server-pod.yaml
apiVersion: v1
kind: Pod
metadata:
  name: web-server
  namespace: app-development
  labels:
    app: web
    version: v1
    environment: production
spec:
  containers:
  - name: nginx
    image: nginx:1.20
    ports:
    - containerPort: 80
EOF

kubectl apply -f /opt/candidate/web-server-pod.yaml

# ラベル追加
kubectl label pod web-server tier=frontend -n app-development

# 確認
kubectl get pod web-server --show-labels -n app-development
```

**採点ポイント:**
- 正しいnamespaceでのPod作成 (25%)
- 指定されたイメージとポート (25%)
- 初期ラベルの正確な設定 (25%)
- 追加ラベルの正確な設定 (25%)
</details>

---

## 🎯 Question 2: ConfigMapとSecret管理 (5%)

**Context**: namespace: `config-demo`  
**Task**: 
以下を作成してください：

ConfigMap `app-config`:
- `database_url`: `postgresql://localhost:5432/myapp`
- `log_level`: `debug`
- 設定ファイル `app.properties`: `server.port=8080\napp.name=demo-app`

Secret `app-credentials`:
- `username`: `admin`
- `password`: `secretpassword123`

<details>
<summary>💡 解答例</summary>

```bash
# namespace作成
kubectl create namespace config-demo

# ConfigMap作成
kubectl create configmap app-config \
  --from-literal=database_url="postgresql://localhost:5432/myapp" \
  --from-literal=log_level="debug" \
  --from-literal=app.properties="server.port=8080\napp.name=demo-app" \
  -n config-demo

# Secret作成
kubectl create secret generic app-credentials \
  --from-literal=username="admin" \
  --from-literal=password="secretpassword123" \
  -n config-demo

# または、YAMLファイルで作成
cat <<EOF > /opt/candidate/config-resources.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: app-config
  namespace: config-demo
data:
  database_url: "postgresql://localhost:5432/myapp"
  log_level: "debug"
  app.properties: |
    server.port=8080
    app.name=demo-app
---
apiVersion: v1
kind: Secret
metadata:
  name: app-credentials
  namespace: config-demo
type: Opaque
data:
  username: YWRtaW4=        # admin (base64)
  password: c2VjcmV0cGFzc3dvcmQxMjM=  # secretpassword123 (base64)
EOF

kubectl apply -f /opt/candidate/config-resources.yaml

# 確認
kubectl get configmap app-config -o yaml -n config-demo
kubectl get secret app-credentials -o yaml -n config-demo
```

**採点ポイント:**
- ConfigMapの正確な作成 (40%)
- Secretの正確な作成 (40%)
- 指定されたnamespaceでの作成 (20%)
</details>

---

## 🎯 Question 3: マルチコンテナPod - サイドカーパターン (8%)

**Context**: namespace: `multi-container`  
**Task**: 
以下の要件でマルチコンテナPodを作成してください：
- 名前: `web-app-with-sidecar`
- メインコンテナ: `nginx:1.20`、ポート80
- サイドカーコンテナ: `busybox:1.35`、nginxのアクセスログを監視
- 共有ボリューム: `/var/log/nginx` (emptyDir)
- サイドカーはログファイルを `tail -f` で監視

<details>
<summary>💡 解答例</summary>

```bash
# namespace作成
kubectl create namespace multi-container

# マルチコンテナPod作成
cat <<EOF > /opt/candidate/sidecar-pod.yaml
apiVersion: v1
kind: Pod
metadata:
  name: web-app-with-sidecar
  namespace: multi-container
spec:
  containers:
  - name: nginx
    image: nginx:1.20
    ports:
    - containerPort: 80
    volumeMounts:
    - name: shared-logs
      mountPath: /var/log/nginx
  - name: log-monitor
    image: busybox:1.35
    command: ['sh', '-c', 'while true; do if [ -f /var/log/nginx/access.log ]; then tail -f /var/log/nginx/access.log; else sleep 5; fi; done']
    volumeMounts:
    - name: shared-logs
      mountPath: /var/log/nginx
      readOnly: true
  volumes:
  - name: shared-logs
    emptyDir: {}
EOF

kubectl apply -f /opt/candidate/sidecar-pod.yaml

# 確認
kubectl get pod web-app-with-sidecar -n multi-container
kubectl describe pod web-app-with-sidecar -n multi-container
```

**採点ポイント:**
- 正しいマルチコンテナ構成 (30%)
- メインコンテナの正確な設定 (25%)
- サイドカーコンテナの正確な設定 (25%)
- 共有ボリューム設定 (20%)
</details>

---

## 🎯 Question 4: Init Container実装 (6%)

**Context**: namespace: `init-demo`  
**Task**: 
以下の要件でInit ContainerつきPodを作成してください：
- 名前: `web-app-with-init`
- Init Container: `busybox:1.35`、依存サービス（service1:80、service2:8080）の起動を待機
- メインコンテナ: `nginx:1.20`
- Init Containerは両方のサービスに接続できるまで待機

<details>
<summary>💡 解答例</summary>

```bash
# namespace作成
kubectl create namespace init-demo

# Init ContainerつきPod作成
cat <<EOF > /opt/candidate/init-container-pod.yaml
apiVersion: v1
kind: Pod
metadata:
  name: web-app-with-init
  namespace: init-demo
spec:
  initContainers:
  - name: wait-for-services
    image: busybox:1.35
    command: ['sh', '-c']
    args:
    - |
      echo "Waiting for service1:80..."
      until nc -z service1 80; do
        echo "service1 not ready, waiting..."
        sleep 2
      done
      echo "service1 is ready!"
      
      echo "Waiting for service2:8080..."
      until nc -z service2 8080; do
        echo "service2 not ready, waiting..."
        sleep 2
      done
      echo "service2 is ready!"
      
      echo "All services are ready!"
  containers:
  - name: nginx
    image: nginx:1.20
    ports:
    - containerPort: 80
EOF

kubectl apply -f /opt/candidate/init-container-pod.yaml

# 模擬サービス作成（テスト用）
kubectl run service1 --image=nginx:1.20 --port=80 -n init-demo
kubectl run service2 --image=nginx:1.20 --port=8080 -n init-demo

kubectl expose pod service1 --port=80 -n init-demo
kubectl expose pod service2 --port=8080 --target-port=80 -n init-demo

# 確認
kubectl get pod web-app-with-init -n init-demo
kubectl describe pod web-app-with-init -n init-demo
```

**採点ポイント:**
- Init Containerの正確な設定 (40%)
- 依存関係チェックロジック (30%)
- メインコンテナの設定 (20%)
- 全体的な動作確認 (10%)
</details>

---

## 🎯 Question 5: Deployment作成と管理 (7%)

**Context**: namespace: `deployment-demo`  
**Task**: 
以下の要件でDeploymentを作成してください：
- 名前: `nginx-deployment`
- イメージ: `nginx:1.20`
- レプリカ数: 3
- リソース要求: CPU 100m、メモリ 128Mi
- リソース制限: CPU 200m、メモリ 256Mi

作成後、イメージを `nginx:1.21` に更新し、レプリカ数を5に変更してください。

<details>
<summary>💡 解答例</summary>

```bash
# namespace作成
kubectl create namespace deployment-demo

# Deployment作成
kubectl create deployment nginx-deployment --image=nginx:1.20 --replicas=3 -n deployment-demo

# リソース制限設定
kubectl patch deployment nginx-deployment -n deployment-demo -p '{
  "spec": {
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
              "cpu": "200m",
              "memory": "256Mi"
            }
          }
        }]
      }
    }
  }
}'

# または、YAMLファイルで作成
cat <<EOF > /opt/candidate/nginx-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: nginx-deployment
  namespace: deployment-demo
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
        resources:
          requests:
            cpu: "100m"
            memory: "128Mi"
          limits:
            cpu: "200m"
            memory: "256Mi"
EOF

kubectl apply -f /opt/candidate/nginx-deployment.yaml

# イメージ更新
kubectl set image deployment/nginx-deployment nginx=nginx:1.21 -n deployment-demo

# レプリカ数変更
kubectl scale deployment nginx-deployment --replicas=5 -n deployment-demo

# 確認
kubectl get deployment nginx-deployment -n deployment-demo
kubectl rollout status deployment/nginx-deployment -n deployment-demo
```

**採点ポイント:**
- 正しいDeployment作成 (25%)
- リソース要求・制限の設定 (25%)
- イメージ更新の実行 (25%)
- レプリカ数変更の実行 (25%)
</details>

---

## 🎯 Question 6: Service作成とエンドポイント管理 (4%)

**Context**: namespace: `service-demo`  
**Task**: 
前問のDeploymentに対してServiceを作成してください：
- 名前: `nginx-service`
- タイプ: NodePort
- ポート: 80
- ターゲットポート: 80
- NodePort: 30080

Serviceが正しく動作していることを確認してください。

<details>
<summary>💡 解答例</summary>

```bash
# namespace作成（必要に応じて）
kubectl create namespace service-demo

# まず対象のDeploymentを作成（前問と同じ）
kubectl create deployment nginx-deployment --image=nginx:1.20 --replicas=3 -n service-demo

# Service作成
kubectl expose deployment nginx-deployment \
  --name=nginx-service \
  --port=80 \
  --target-port=80 \
  --type=NodePort \
  -n service-demo

# NodePortを指定
kubectl patch service nginx-service -n service-demo -p '{
  "spec": {
    "ports": [{
      "port": 80,
      "targetPort": 80,
      "nodePort": 30080
    }]
  }
}'

# または、YAMLファイルで作成
cat <<EOF > /opt/candidate/nginx-service.yaml
apiVersion: v1
kind: Service
metadata:
  name: nginx-service
  namespace: service-demo
spec:
  selector:
    app: nginx-deployment
  ports:
  - port: 80
    targetPort: 80
    nodePort: 30080
  type: NodePort
EOF

kubectl apply -f /opt/candidate/nginx-service.yaml

# 動作確認
kubectl get service nginx-service -n service-demo
kubectl get endpoints nginx-service -n service-demo

# 接続テスト
kubectl run test-pod --image=busybox:1.35 --rm -it -n service-demo -- wget -qO- nginx-service:80
```

**採点ポイント:**
- 正しいService作成 (30%)
- NodePortタイプの設定 (25%)
- 指定されたポート設定 (25%)
- Endpointsの正常確認 (20%)
</details>

---

## 🎯 Question 7: Job作成 (4%)

**Context**: namespace: `batch-jobs`  
**Task**: 
以下の要件でJobを作成してください：
- 名前: `pi-calculation-job`
- イメージ: `perl:5.34`
- コマンド: 円周率を2000桁計算 `["perl", "-Mbignum=bpi", "-wle", "print bpi(2000)"]`
- 完了回数: 3
- 並列度: 2
- 再試行制限: 2回

<details>
<summary>💡 解答例</summary>

```bash
# namespace作成
kubectl create namespace batch-jobs

# Job作成
cat <<EOF > /opt/candidate/pi-calculation-job.yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: pi-calculation-job
  namespace: batch-jobs
spec:
  completions: 3
  parallelism: 2
  backoffLimit: 2
  template:
    spec:
      restartPolicy: Never
      containers:
      - name: pi-calculator
        image: perl:5.34
        command: ["perl", "-Mbignum=bpi", "-wle", "print bpi(2000)"]
EOF

kubectl apply -f /opt/candidate/pi-calculation-job.yaml

# 確認
kubectl get job pi-calculation-job -n batch-jobs
kubectl describe job pi-calculation-job -n batch-jobs

# Job完了待機
kubectl wait --for=condition=complete job/pi-calculation-job -n batch-jobs --timeout=300s

# 結果確認
kubectl logs -l job-name=pi-calculation-job -n batch-jobs
```

**採点ポイント:**
- 正しいJob設定 (25%)
- 完了回数・並列度の設定 (25%)
- 再試行制限の設定 (25%)
- コマンドの正確な指定 (25%)
</details>

---

## 🎯 Question 8: CronJob作成 (4%)

**Context**: namespace: `scheduled-jobs`  
**Task**: 
以下の要件でCronJobを作成してください：
- 名前: `backup-cronjob`
- スケジュール: 毎日午前2時 (`0 2 * * *`)
- イメージ: `alpine:3.18`
- コマンド: `['sh', '-c', 'echo "Backup started at $(date)" && sleep 30 && echo "Backup completed"']`
- 成功履歴保持: 3個
- 失敗履歴保持: 1個

<details>
<summary>💡 解答例</summary>

```bash
# namespace作成
kubectl create namespace scheduled-jobs

# CronJob作成
cat <<EOF > /opt/candidate/backup-cronjob.yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: backup-cronjob
  namespace: scheduled-jobs
spec:
  schedule: "0 2 * * *"
  successfulJobsHistoryLimit: 3
  failedJobsHistoryLimit: 1
  jobTemplate:
    spec:
      template:
        spec:
          restartPolicy: OnFailure
          containers:
          - name: backup
            image: alpine:3.18
            command: ['sh', '-c', 'echo "Backup started at $(date)" && sleep 30 && echo "Backup completed"']
EOF

kubectl apply -f /opt/candidate/backup-cronjob.yaml

# 確認
kubectl get cronjob backup-cronjob -n scheduled-jobs
kubectl describe cronjob backup-cronjob -n scheduled-jobs

# 手動実行テスト
kubectl create job --from=cronjob/backup-cronjob manual-backup -n scheduled-jobs
```

**採点ポイント:**
- 正しいスケジュール設定 (25%)
- 履歴保持設定 (25%)
- コマンドの正確な指定 (25%)
- CronJob基本設定 (25%)
</details>

---

## 🎯 Question 9: ヘルスチェック設定 (6%)

**Context**: namespace: `health-check`  
**Task**: 
以下の要件でPodを作成してください：
- 名前: `healthy-app`
- イメージ: `nginx:1.20`
- Liveness Probe: HTTP GET `/`、ポート80、30秒後開始、10秒間隔
- Readiness Probe: HTTP GET `/`、ポート80、5秒後開始、5秒間隔  
- Startup Probe: HTTP GET `/`、ポート80、10秒後開始、5秒間隔、30回まで失敗許可

<details>
<summary>💡 解答例</summary>

```bash
# namespace作成
kubectl create namespace health-check

# ヘルスチェック付きPod作成
cat <<EOF > /opt/candidate/healthy-app-pod.yaml
apiVersion: v1
kind: Pod
metadata:
  name: healthy-app
  namespace: health-check
spec:
  containers:
  - name: nginx
    image: nginx:1.20
    ports:
    - containerPort: 80
    startupProbe:
      httpGet:
        path: /
        port: 80
      initialDelaySeconds: 10
      periodSeconds: 5
      failureThreshold: 30
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
EOF

kubectl apply -f /opt/candidate/healthy-app-pod.yaml

# 確認
kubectl get pod healthy-app -n health-check
kubectl describe pod healthy-app -n health-check | grep -A 10 Probes
```

**採点ポイント:**
- Startup Probeの正確な設定 (30%)
- Liveness Probeの正確な設定 (35%)
- Readiness Probeの正確な設定 (35%)
</details>

---

## 🎯 Question 10: 環境変数と設定ファイル (5%)

**Context**: namespace: `config-injection`  
**Task**: 
既存のConfigMap `database-config` とSecret `database-credentials` を使用してPodを作成してください：
- 名前: `configured-pod`
- イメージ: `nginx:1.20`
- 環境変数として注入:
  - ConfigMapから `DB_HOST`、`DB_PORT`
  - Secretから `DB_USER`、`DB_PASSWORD`
- ボリュームマウント: ConfigMapを `/etc/config`、Secretを `/etc/secrets`

```bash
# 事前準備（試験では事前に作成済み）
kubectl create namespace config-injection
kubectl create configmap database-config \
  --from-literal=DB_HOST="db.example.com" \
  --from-literal=DB_PORT="5432" \
  -n config-injection
kubectl create secret generic database-credentials \
  --from-literal=DB_USER="admin" \
  --from-literal=DB_PASSWORD="password123" \
  -n config-injection
```

<details>
<summary>💡 解答例</summary>

```bash
# 設定済みPod作成
cat <<EOF > /opt/candidate/configured-pod.yaml
apiVersion: v1
kind: Pod
metadata:
  name: configured-pod
  namespace: config-injection
spec:
  containers:
  - name: nginx
    image: nginx:1.20
    env:
    - name: DB_HOST
      valueFrom:
        configMapKeyRef:
          name: database-config
          key: DB_HOST
    - name: DB_PORT
      valueFrom:
        configMapKeyRef:
          name: database-config
          key: DB_PORT
    - name: DB_USER
      valueFrom:
        secretKeyRef:
          name: database-credentials
          key: DB_USER
    - name: DB_PASSWORD
      valueFrom:
        secretKeyRef:
          name: database-credentials
          key: DB_PASSWORD
    volumeMounts:
    - name: config-volume
      mountPath: /etc/config
    - name: secret-volume
      mountPath: /etc/secrets
      readOnly: true
  volumes:
  - name: config-volume
    configMap:
      name: database-config
  - name: secret-volume
    secret:
      secretName: database-credentials
EOF

kubectl apply -f /opt/candidate/configured-pod.yaml

# 確認
kubectl exec configured-pod -n config-injection -- env | grep DB_
kubectl exec configured-pod -n config-injection -- ls -la /etc/config
kubectl exec configured-pod -n config-injection -- ls -la /etc/secrets
```

**採点ポイント:**
- 環境変数の正確な注入 (40%)
- ConfigMapボリュームマウント (30%)
- Secretボリュームマウント (30%)
</details>

---

## 🎯 Question 11: リソース制限とQoS (5%)

**Context**: namespace: `resource-management`  
**Task**: 
以下のQoSクラスのPodをそれぞれ作成してください：

1. Guaranteed QoS Pod `guaranteed-pod`:
   - イメージ: `nginx:1.20`
   - CPU request/limit: 500m
   - Memory request/limit: 256Mi

2. Burstable QoS Pod `burstable-pod`:
   - イメージ: `nginx:1.20`
   - CPU request: 200m, limit: 1000m
   - Memory request: 128Mi, limit: 512Mi

<details>
<summary>💡 解答例</summary>

```bash
# namespace作成
kubectl create namespace resource-management

# Guaranteed QoS Pod
cat <<EOF > /opt/candidate/guaranteed-pod.yaml
apiVersion: v1
kind: Pod
metadata:
  name: guaranteed-pod
  namespace: resource-management
spec:
  containers:
  - name: nginx
    image: nginx:1.20
    resources:
      requests:
        cpu: "500m"
        memory: "256Mi"
      limits:
        cpu: "500m"
        memory: "256Mi"
EOF

# Burstable QoS Pod
cat <<EOF > /opt/candidate/burstable-pod.yaml
apiVersion: v1
kind: Pod
metadata:
  name: burstable-pod
  namespace: resource-management
spec:
  containers:
  - name: nginx
    image: nginx:1.20
    resources:
      requests:
        cpu: "200m"
        memory: "128Mi"
      limits:
        cpu: "1000m"
        memory: "512Mi"
EOF

kubectl apply -f /opt/candidate/guaranteed-pod.yaml
kubectl apply -f /opt/candidate/burstable-pod.yaml

# QoSクラス確認
kubectl get pod guaranteed-pod -o jsonpath='{.status.qosClass}' -n resource-management
kubectl get pod burstable-pod -o jsonpath='{.status.qosClass}' -n resource-management
```

**採点ポイント:**
- Guaranteed QoS設定の正確性 (50%)
- Burstable QoS設定の正確性 (50%)
</details>

---

## 🎯 Question 12: NetworkPolicy作成 (6%)

**Context**: namespace: `network-security`  
**Task**: 
以下の要件でNetworkPolicyを作成してください：
- 名前: `deny-all-allow-frontend`
- 対象: `app=backend` ラベルのPod
- ルール: すべての入力を拒否、ただし `app=frontend` ラベルのPodからのport 8080への接続は許可

テスト用にbackendとfrontendのPodも作成してください。

<details>
<summary>💡 解答例</summary>

```bash
# namespace作成
kubectl create namespace network-security

# NetworkPolicy作成
cat <<EOF > /opt/candidate/network-policy.yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: deny-all-allow-frontend
  namespace: network-security
spec:
  podSelector:
    matchLabels:
      app: backend
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

# テスト用Pod作成
kubectl run backend-pod --image=nginx:1.20 --labels="app=backend" --port=8080 -n network-security
kubectl run frontend-pod --image=busybox:1.35 --labels="app=frontend" --command -n network-security -- sleep 3600
kubectl run unauthorized-pod --image=busybox:1.35 --labels="app=other" --command -n network-security -- sleep 3600

kubectl apply -f /opt/candidate/network-policy.yaml

# 確認
kubectl get networkpolicy -n network-security
kubectl describe networkpolicy deny-all-allow-frontend -n network-security
```

**採点ポイント:**
- NetworkPolicyの正確な設定 (40%)
- podSelectorの正確性 (25%)
- Ingressルールの正確性 (25%)
- テスト環境の準備 (10%)
</details>

---

## 🎯 Question 13: Ingress設定 (5%)

**Context**: namespace: `ingress-demo`  
**Task**: 
以下の要件でIngressを作成してください：
- 名前: `web-ingress`
- ホスト: `myapp.example.com`
- パス `/api` を `api-service:8080` にルーティング
- パス `/web` を `web-service:80` にルーティング
- デフォルトパス `/` を `web-service:80` にルーティング

<details>
<summary>💡 解答例</summary>

```bash
# namespace作成
kubectl create namespace ingress-demo

# Ingress作成
cat <<EOF > /opt/candidate/web-ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: web-ingress
  namespace: ingress-demo
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /
spec:
  rules:
  - host: myapp.example.com
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
      - path: /
        pathType: Prefix
        backend:
          service:
            name: web-service
            port:
              number: 80
EOF

kubectl apply -f /opt/candidate/web-ingress.yaml

# 確認
kubectl get ingress web-ingress -n ingress-demo
kubectl describe ingress web-ingress -n ingress-demo
```

**採点ポイント:**
- 正しいIngress設定 (30%)
- ホストの設定 (20%)
- パスルーティングの正確性 (40%)
- Service参照の正確性 (10%)
</details>

---

## 🎯 Question 14: ボリューム管理 (4%)

**Context**: namespace: `volume-demo`  
**Task**: 
以下の要件でPodを作成してください：
- 名前: `data-pod`
- イメージ: `busybox:1.35`
- emptyDirボリューム `shared-data` を `/data` にマウント
- hostPathボリューム `/tmp/host-data` を `/host-data` にマウント（読み取り専用）
- コマンド: `['sleep', '3600']`

<details>
<summary>💡 解答例</summary>

```bash
# namespace作成
kubectl create namespace volume-demo

# ボリューム付きPod作成
cat <<EOF > /opt/candidate/data-pod.yaml
apiVersion: v1
kind: Pod
metadata:
  name: data-pod
  namespace: volume-demo
spec:
  containers:
  - name: busybox
    image: busybox:1.35
    command: ['sleep', '3600']
    volumeMounts:
    - name: shared-data
      mountPath: /data
    - name: host-data
      mountPath: /host-data
      readOnly: true
  volumes:
  - name: shared-data
    emptyDir: {}
  - name: host-data
    hostPath:
      path: /tmp/host-data
      type: DirectoryOrCreate
EOF

kubectl apply -f /opt/candidate/data-pod.yaml

# 確認
kubectl get pod data-pod -n volume-demo
kubectl exec data-pod -n volume-demo -- ls -la /data
kubectl exec data-pod -n volume-demo -- ls -la /host-data
```

**採点ポイント:**
- emptyDirボリューム設定 (30%)
- hostPathボリューム設定 (40%)
- 読み取り専用設定 (20%)
- マウントパスの正確性 (10%)
</details>

---

## 🎯 Question 15: セキュリティコンテキスト (5%)

**Context**: namespace: `security-demo`  
**Task**: 
以下のセキュリティ設定でPodを作成してください：
- 名前: `secure-pod`
- イメージ: `nginx:1.20`
- 非rootユーザー (UID: 1000) で実行
- 読み取り専用ルートファイルシステム
- 特権昇格禁止
- すべてのCapability削除、NET_BIND_SERVICEのみ追加

<details>
<summary>💡 解答例</summary>

```bash
# namespace作成
kubectl create namespace security-demo

# セキュアPod作成
cat <<EOF > /opt/candidate/secure-pod.yaml
apiVersion: v1
kind: Pod
metadata:
  name: secure-pod
  namespace: security-demo
spec:
  securityContext:
    runAsUser: 1000
    runAsNonRoot: true
  containers:
  - name: nginx
    image: nginx:1.20
    securityContext:
      readOnlyRootFilesystem: true
      allowPrivilegeEscalation: false
      capabilities:
        drop:
        - ALL
        add:
        - NET_BIND_SERVICE
    volumeMounts:
    - name: tmp-volume
      mountPath: /tmp
    - name: var-cache
      mountPath: /var/cache/nginx
    - name: var-run
      mountPath: /var/run
  volumes:
  - name: tmp-volume
    emptyDir: {}
  - name: var-cache
    emptyDir: {}
  - name: var-run
    emptyDir: {}
EOF

kubectl apply -f /opt/candidate/secure-pod.yaml

# 確認
kubectl get pod secure-pod -n security-demo
kubectl describe pod secure-pod -n security-demo | grep -A 10 "Security Context"
```

**採点ポイント:**
- 非rootユーザー設定 (25%)
- 読み取り専用ファイルシステム (25%)
- 特権昇格禁止設定 (25%)
- Capability設定 (25%)
</details>

---

## 🎯 Question 16: PersistentVolume管理 (4%)

**Context**: namespace: `storage-demo`  
**Task**: 
以下の要件でPersistentVolumeClaimを作成し、Podで使用してください：
- PVC名: `data-pvc`
- ストレージ要求: 1Gi
- アクセスモード: ReadWriteOnce
- Pod名: `storage-pod`、イメージ: `nginx:1.20`
- PVCを `/data` にマウント

<details>
<summary>💡 解答例</summary>

```bash
# namespace作成
kubectl create namespace storage-demo

# PVC作成
cat <<EOF > /opt/candidate/data-pvc.yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: data-pvc
  namespace: storage-demo
spec:
  accessModes:
  - ReadWriteOnce
  resources:
    requests:
      storage: 1Gi
EOF

# PVC使用Pod作成
cat <<EOF > /opt/candidate/storage-pod.yaml
apiVersion: v1
kind: Pod
metadata:
  name: storage-pod
  namespace: storage-demo
spec:
  containers:
  - name: nginx
    image: nginx:1.20
    volumeMounts:
    - name: data-volume
      mountPath: /data
  volumes:
  - name: data-volume
    persistentVolumeClaim:
      claimName: data-pvc
EOF

kubectl apply -f /opt/candidate/data-pvc.yaml
kubectl apply -f /opt/candidate/storage-pod.yaml

# 確認
kubectl get pvc data-pvc -n storage-demo
kubectl get pod storage-pod -n storage-demo
kubectl exec storage-pod -n storage-demo -- df -h | grep /data
```

**採点ポイント:**
- PVCの正確な作成 (40%)
- 正しいストレージ要求 (20%)
- Podでの正確なマウント (30%)
- 動作確認 (10%)
</details>

---

## 🎯 Question 17: トラブルシューティング (8%)

**Context**: namespace: `troubleshooting`  
**Task**: 
`troubleshooting` namespaceにある `broken-app` Deploymentが正常に動作していません。
問題を特定し、修正してください。すべてのPodが Ready 状態になる必要があります。

```bash
# 事前準備（問題のあるDeployment作成）
kubectl create namespace troubleshooting
cat <<EOF | kubectl apply -f -
apiVersion: apps/v1
kind: Deployment
metadata:
  name: broken-app
  namespace: troubleshooting
spec:
  replicas: 3
  selector:
    matchLabels:
      app: broken-app
  template:
    metadata:
      labels:
        app: broken-app
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
# 問題の調査
kubectl get deployment broken-app -n troubleshooting
kubectl get pods -l app=broken-app -n troubleshooting
kubectl describe deployment broken-app -n troubleshooting

# Pod詳細確認
POD_NAME=$(kubectl get pods -l app=broken-app -n troubleshooting -o jsonpath='{.items[0].metadata.name}')
kubectl describe pod $POD_NAME -n troubleshooting

# ログ確認
kubectl logs $POD_NAME -n troubleshooting

# イベント確認
kubectl get events -n troubleshooting --sort-by=.metadata.creationTimestamp

# 問題特定: livenessProbeのポートが間違っている (8080 instead of 80)
# readinessProbeのパスも存在しない (/ready)

# 修正
kubectl patch deployment broken-app -n troubleshooting -p '{
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

# 修正確認
kubectl rollout status deployment/broken-app -n troubleshooting
kubectl get pods -l app=broken-app -n troubleshooting
```

**採点ポイント:**
- 正確な問題特定 (40%)
- 適切な調査手順 (20%)
- 正しい修正実装 (30%)
- 修正後の動作確認 (10%)
</details>

---

## 🎯 Question 18: カスタムリソース管理 (3%)

**Context**: namespace: `custom-resource`  
**Task**: 
以下の要件でServiceAccountとRoleBindingを作成してください：
- ServiceAccount: `app-service-account`
- Role: `pod-manager` (Podの取得・一覧・作成権限)
- RoleBinding: `app-pod-manager` (ServiceAccountにRoleを付与)
- テスト用Pod: ServiceAccountを使用してPod作成権限をテスト

<details>
<summary>💡 解答例</summary>

```bash
# namespace作成
kubectl create namespace custom-resource

# ServiceAccount作成
kubectl create serviceaccount app-service-account -n custom-resource

# Role作成
cat <<EOF > /opt/candidate/pod-manager-role.yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: pod-manager
  namespace: custom-resource
rules:
- apiGroups: [""]
  resources: ["pods"]
  verbs: ["get", "list", "create"]
EOF

# RoleBinding作成
cat <<EOF > /opt/candidate/app-pod-manager-binding.yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: app-pod-manager
  namespace: custom-resource
subjects:
- kind: ServiceAccount
  name: app-service-account
  namespace: custom-resource
roleRef:
  kind: Role
  name: pod-manager
  apiGroup: rbac.authorization.k8s.io
EOF

kubectl apply -f /opt/candidate/pod-manager-role.yaml
kubectl apply -f /opt/candidate/app-pod-manager-binding.yaml

# テスト用Pod作成
kubectl run test-pod --image=nginx:1.20 --serviceaccount=app-service-account -n custom-resource

# 権限確認
kubectl auth can-i get pods --as=system:serviceaccount:custom-resource:app-service-account -n custom-resource
kubectl auth can-i create pods --as=system:serviceaccount:custom-resource:app-service-account -n custom-resource
```

**採点ポイント:**
- ServiceAccount作成 (25%)
- Role設定の正確性 (35%)
- RoleBinding設定 (25%)
- 権限テスト (15%)
</details>

---

## 🎯 Question 19: アプリケーション統合 (6%)

**Context**: namespace: `integration-demo`  
**Task**: 
以下の要件で完全なアプリケーションスタックを作成してください：
- Frontend Deployment: `nginx:1.20`、3レプリカ、ClusterIP Service
- Backend Deployment: `nginx:1.20`、2レプリカ、ClusterIP Service  
- Database StatefulSet: `postgres:13`、1レプリカ、Headless Service
- 環境変数でサービス間連携設定
- Ingress でフロントエンドを外部公開 (`app.local`)

<details>
<summary>💡 解答例</summary>

```bash
# namespace作成
kubectl create namespace integration-demo

# Frontend Deployment & Service
cat <<EOF > /opt/candidate/frontend.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: frontend
  namespace: integration-demo
spec:
  replicas: 3
  selector:
    matchLabels:
      app: frontend
  template:
    metadata:
      labels:
        app: frontend
    spec:
      containers:
      - name: nginx
        image: nginx:1.20
        ports:
        - containerPort: 80
        env:
        - name: BACKEND_URL
          value: "http://backend:8080"
---
apiVersion: v1
kind: Service
metadata:
  name: frontend
  namespace: integration-demo
spec:
  selector:
    app: frontend
  ports:
  - port: 80
    targetPort: 80
  type: ClusterIP
EOF

# Backend Deployment & Service
cat <<EOF > /opt/candidate/backend.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: backend
  namespace: integration-demo
spec:
  replicas: 2
  selector:
    matchLabels:
      app: backend
  template:
    metadata:
      labels:
        app: backend
    spec:
      containers:
      - name: nginx
        image: nginx:1.20
        ports:
        - containerPort: 80
        env:
        - name: DATABASE_URL
          value: "postgresql://postgres:5432/appdb"
---
apiVersion: v1
kind: Service
metadata:
  name: backend
  namespace: integration-demo
spec:
  selector:
    app: backend
  ports:
  - port: 8080
    targetPort: 80
  type: ClusterIP
EOF

# Database StatefulSet & Headless Service
cat <<EOF > /opt/candidate/database.yaml
apiVersion: v1
kind: Service
metadata:
  name: postgres
  namespace: integration-demo
spec:
  clusterIP: None
  selector:
    app: postgres
  ports:
  - port: 5432
    targetPort: 5432
---
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: postgres
  namespace: integration-demo
spec:
  serviceName: postgres
  replicas: 1
  selector:
    matchLabels:
      app: postgres
  template:
    metadata:
      labels:
        app: postgres
    spec:
      containers:
      - name: postgres
        image: postgres:13
        ports:
        - containerPort: 5432
        env:
        - name: POSTGRES_DB
          value: appdb
        - name: POSTGRES_USER
          value: user
        - name: POSTGRES_PASSWORD
          value: password
EOF

# Ingress
cat <<EOF > /opt/candidate/ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: app-ingress
  namespace: integration-demo
spec:
  rules:
  - host: app.local
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: frontend
            port:
              number: 80
EOF

# すべて適用
kubectl apply -f /opt/candidate/frontend.yaml
kubectl apply -f /opt/candidate/backend.yaml
kubectl apply -f /opt/candidate/database.yaml
kubectl apply -f /opt/candidate/ingress.yaml

# 確認
kubectl get all -n integration-demo
kubectl get ingress -n integration-demo
```

**採点ポイント:**
- Frontend Deployment/Service (25%)
- Backend Deployment/Service (25%)
- Database StatefulSet/Service (25%)
- Ingress設定 (25%)
</details>

---

## 📊 採点基準

| 問題番号 | 配点 | 分野 |
|----------|------|------|
| Q1 | 3% | Pod基本管理 |
| Q2 | 5% | 設定管理 |
| Q3 | 8% | マルチコンテナ |
| Q4 | 6% | Init Container |
| Q5 | 7% | Deployment管理 |
| Q6 | 4% | Service管理 |
| Q7 | 4% | Job管理 |
| Q8 | 4% | CronJob |
| Q9 | 6% | ヘルスチェック |
| Q10 | 5% | 設定注入 |
| Q11 | 5% | リソース管理 |
| Q12 | 6% | ネットワークセキュリティ |
| Q13 | 5% | Ingress |
| Q14 | 4% | ボリューム管理 |
| Q15 | 5% | セキュリティ |
| Q16 | 4% | ストレージ |
| Q17 | 8% | トラブルシューティング |
| Q18 | 3% | RBAC |
| Q19 | 6% | 総合実装 |
| **合計** | **100%** | |

**合格ライン**: 66%以上

---

## 🎯 試験後の振り返り

練習試験完了後、以下を確認してください：

1. **時間管理**: 120分以内に完了できたか
2. **正解率**: 66%以上達成できたか  
3. **弱点分野**: 間違った問題の分野を特定
4. **効率化**: YAML作成やkubectlコマンドの速度

**改善ポイント:**
- kubectl コマンドの高速化
- YAML テンプレートの暗記
- トラブルシューティング手順の体系化
- マルチコンテナパターンの理解深化

**次のステップ**: [Practice Exam 2](./practice-exam-02.md) でより高度なアプリケーション開発問題に挑戦してください。