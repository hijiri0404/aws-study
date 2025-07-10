# Lab 2: Pod とワークロード管理実践

## 🎯 学習目標

このラボでは、Kubernetes の基本的なワークロード管理について実践的に学習します。Pod、Deployment、DaemonSet、StatefulSet、Jobs/CronJobs の作成・管理・トラブルシューティングを習得します。

**習得スキル**:
- Pod のライフサイクル管理
- Deployment の作成・更新・ロールバック
- DaemonSet による全ノード展開
- StatefulSet でのステートフルアプリケーション管理
- Jobs/CronJobs でのバッチ処理
- リソース制限とクォータ管理

**所要時間**: 5-7時間  
**推定コスト**: $10-20

## 📋 シナリオ

**企業**: ウェブサービス運営会社  
**課題**: マイクロサービス環境でのワークロード管理体制構築  
**要件**: 
- 高可用性ウェブアプリケーション
- 全ノードでのログ収集
- データベースクラスター
- 定期的なバックアップ処理

## Phase 1: Pod 基本操作とライフサイクル管理

### 1.1 Pod の基本的な作成と管理

```yaml
# ファイル: basic-pod.yaml
apiVersion: v1
kind: Pod
metadata:
  name: nginx-pod
  labels:
    app: nginx
    environment: development
spec:
  containers:
  - name: nginx
    image: nginx:1.20
    ports:
    - containerPort: 80
    resources:
      requests:
        memory: "64Mi"
        cpu: "250m"
      limits:
        memory: "128Mi"
        cpu: "500m"
    env:
    - name: ENVIRONMENT
      value: "development"
    volumeMounts:
    - name: nginx-config
      mountPath: /etc/nginx/conf.d
  volumes:
  - name: nginx-config
    configMap:
      name: nginx-config
```

```bash
#!/bin/bash
# スクリプト: pod-basic-operations.sh

echo "🚀 Pod基本操作の実践..."

# ConfigMap作成
echo "📋 ConfigMap作成中..."
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: ConfigMap
metadata:
  name: nginx-config
data:
  default.conf: |
    server {
        listen 80;
        server_name localhost;
        
        location / {
            root /usr/share/nginx/html;
            index index.html index.htm;
        }
        
        location /health {
            access_log off;
            return 200 "healthy\n";
            add_header Content-Type text/plain;
        }
    }
EOF

# Pod作成
echo "🎯 Pod作成中..."
kubectl apply -f basic-pod.yaml

# Pod状態確認
echo "⏳ Pod起動待機中..."
kubectl wait --for=condition=Ready pod/nginx-pod --timeout=300s

echo "📊 Pod状態確認:"
kubectl get pod nginx-pod -o wide
kubectl describe pod nginx-pod

echo "🔍 Pod詳細情報:"
kubectl get pod nginx-pod -o yaml

# ログ確認
echo "📋 Podログ確認:"
kubectl logs nginx-pod

# Pod内でのコマンド実行
echo "💻 Pod内コマンド実行テスト:"
kubectl exec nginx-pod -- nginx -v
kubectl exec nginx-pod -- cat /etc/nginx/conf.d/default.conf

# ポートフォワーディングテスト
echo "🌐 ポートフォワーディングテスト:"
kubectl port-forward pod/nginx-pod 8080:80 &
PF_PID=$!
sleep 5

curl -s http://localhost:8080/health
kill $PF_PID

echo "✅ Pod基本操作完了!"
```

### 1.2 マルチコンテナ Pod の実践

```yaml
# ファイル: multi-container-pod.yaml
apiVersion: v1
kind: Pod
metadata:
  name: multi-container-pod
  labels:
    app: web-with-sidecar
spec:
  containers:
  # メインアプリケーション
  - name: web-app
    image: nginx:1.20
    ports:
    - containerPort: 80
    volumeMounts:
    - name: shared-logs
      mountPath: /var/log/nginx
  
  # ログ収集サイドカー
  - name: log-collector
    image: busybox:1.35
    command: ['sh', '-c', 'tail -f /var/log/nginx/access.log']
    volumeMounts:
    - name: shared-logs
      mountPath: /var/log/nginx
  
  # 監視エージェント
  - name: monitoring
    image: busybox:1.35
    command: ['sh', '-c', 'while true; do date; sleep 30; done']
    resources:
      requests:
        memory: "32Mi"
        cpu: "100m"
      limits:
        memory: "64Mi"
        cpu: "200m"
  
  volumes:
  - name: shared-logs
    emptyDir: {}
```

```bash
#!/bin/bash
# スクリプト: multi-container-operations.sh

echo "🔄 マルチコンテナPod操作の実践..."

# マルチコンテナPod作成
kubectl apply -f multi-container-pod.yaml

# Pod起動待機
kubectl wait --for=condition=Ready pod/multi-container-pod --timeout=300s

echo "📊 マルチコンテナPod状態:"
kubectl get pod multi-container-pod
kubectl describe pod multi-container-pod

# 各コンテナのログ確認
echo "📋 各コンテナのログ確認:"
echo "Web-app コンテナ:"
kubectl logs multi-container-pod -c web-app

echo "Log-collector コンテナ:"
kubectl logs multi-container-pod -c log-collector

echo "Monitoring コンテナ:"
kubectl logs multi-container-pod -c monitoring --tail=5

# 特定コンテナでのコマンド実行
echo "💻 特定コンテナでのコマンド実行:"
kubectl exec multi-container-pod -c web-app -- nginx -t
kubectl exec multi-container-pod -c monitoring -- ps aux

# リソース使用量確認
echo "📊 リソース使用量:"
kubectl top pod multi-container-pod --containers

echo "✅ マルチコンテナPod操作完了!"
```

## Phase 2: Deployment による本格的なアプリケーション管理

### 2.1 Deployment の作成と管理

```yaml
# ファイル: web-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: web-app-deployment
  labels:
    app: web-app
spec:
  replicas: 3
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxUnavailable: 1
      maxSurge: 1
  selector:
    matchLabels:
      app: web-app
  template:
    metadata:
      labels:
        app: web-app
        version: v1.0
    spec:
      containers:
      - name: web-app
        image: nginx:1.20
        ports:
        - containerPort: 80
        resources:
          requests:
            memory: "128Mi"
            cpu: "100m"
          limits:
            memory: "256Mi"
            cpu: "200m"
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
        env:
        - name: APP_VERSION
          value: "v1.0"
---
apiVersion: v1
kind: Service
metadata:
  name: web-app-service
spec:
  selector:
    app: web-app
  ports:
  - port: 80
    targetPort: 80
    nodePort: 30080
  type: NodePort
```

```bash
#!/bin/bash
# スクリプト: deployment-operations.sh

echo "🚀 Deployment操作の実践..."

# Deployment作成
echo "📦 Deployment作成中..."
kubectl apply -f web-deployment.yaml

# デプロイ完了待機
echo "⏳ Deployment完了待機中..."
kubectl wait --for=condition=Available deployment/web-app-deployment --timeout=300s

# Deployment状態確認
echo "📊 Deployment状態確認:"
kubectl get deployment web-app-deployment
kubectl get replicaset
kubectl get pods -l app=web-app

echo "🔍 Deployment詳細:"
kubectl describe deployment web-app-deployment

# スケーリング操作
echo "📈 スケーリング操作:"
echo "レプリカ数を5に増加..."
kubectl scale deployment web-app-deployment --replicas=5

kubectl wait --for=condition=Available deployment/web-app-deployment --timeout=300s
kubectl get pods -l app=web-app

echo "レプリカ数を2に減少..."
kubectl scale deployment web-app-deployment --replicas=2

kubectl wait --for=condition=Available deployment/web-app-deployment --timeout=300s
kubectl get pods -l app=web-app

# ローリングアップデート
echo "🔄 ローリングアップデート実行:"
kubectl set image deployment/web-app-deployment web-app=nginx:1.21

# アップデート進行状況監視
kubectl rollout status deployment/web-app-deployment

echo "📊 アップデート後の状態:"
kubectl get pods -l app=web-app
kubectl describe deployment web-app-deployment | grep Image

# ロールアウト履歴確認
echo "📋 ロールアウト履歴:"
kubectl rollout history deployment/web-app-deployment

# ロールバック操作
echo "⏪ ロールバック操作:"
kubectl rollout undo deployment/web-app-deployment

kubectl rollout status deployment/web-app-deployment
echo "ロールバック完了後の状態:"
kubectl get pods -l app=web-app

echo "✅ Deployment操作完了!"
```

### 2.2 高度な Deployment 戦略

```yaml
# ファイル: advanced-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: canary-deployment
  labels:
    app: canary-app
spec:
  replicas: 5
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxUnavailable: 0  # ダウンタイムなし
      maxSurge: 2        # 最大2つのPodを同時に作成
  selector:
    matchLabels:
      app: canary-app
  template:
    metadata:
      labels:
        app: canary-app
        version: stable
    spec:
      containers:
      - name: app
        image: nginx:1.20
        ports:
        - containerPort: 80
        resources:
          requests:
            memory: "128Mi"
            cpu: "100m"
          limits:
            memory: "256Mi"
            cpu: "200m"
        livenessProbe:
          httpGet:
            path: /
            port: 80
          initialDelaySeconds: 30
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
          failureThreshold: 2
      affinity:
        podAntiAffinity:
          preferredDuringSchedulingIgnoredDuringExecution:
          - weight: 100
            podAffinityTerm:
              labelSelector:
                matchExpressions:
                - key: app
                  operator: In
                  values:
                  - canary-app
              topologyKey: kubernetes.io/hostname
```

```bash
#!/bin/bash
# スクリプト: canary-deployment.sh

echo "🎯 カナリアデプロイメント実践..."

# カナリアデプロイメント作成
kubectl apply -f advanced-deployment.yaml

kubectl wait --for=condition=Available deployment/canary-deployment --timeout=300s

echo "📊 初期状態確認:"
kubectl get pods -l app=canary-app -o wide

# カナリア版の準備
echo "🐤 カナリア版デプロイメント作成..."
cat <<EOF | kubectl apply -f -
apiVersion: apps/v1
kind: Deployment
metadata:
  name: canary-deployment-v2
  labels:
    app: canary-app
    version: canary
spec:
  replicas: 1  # カナリア版は少数から開始
  selector:
    matchLabels:
      app: canary-app
      version: canary
  template:
    metadata:
      labels:
        app: canary-app
        version: canary
    spec:
      containers:
      - name: app
        image: nginx:1.21  # 新バージョン
        ports:
        - containerPort: 80
        env:
        - name: VERSION
          value: "canary"
        resources:
          requests:
            memory: "128Mi"
            cpu: "100m"
          limits:
            memory: "256Mi"
            cpu: "200m"
EOF

kubectl wait --for=condition=Available deployment/canary-deployment-v2 --timeout=300s

echo "📊 カナリア版デプロイ後の状態:"
kubectl get pods -l app=canary-app -o wide

# トラフィック分散確認用サービス
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: Service
metadata:
  name: canary-service
spec:
  selector:
    app: canary-app  # 両方のバージョンを対象
  ports:
  - port: 80
    targetPort: 80
  type: ClusterIP
EOF

echo "🔍 サービスエンドポイント確認:"
kubectl get endpoints canary-service

# カナリア版の段階的スケールアップ
echo "📈 カナリア版段階的スケールアップ:"
for replicas in 2 3; do
    kubectl scale deployment canary-deployment-v2 --replicas=$replicas
    kubectl wait --for=condition=Available deployment/canary-deployment-v2 --timeout=300s
    echo "カナリア版レプリカ数: $replicas"
    kubectl get pods -l app=canary-app --no-headers | wc -l
    sleep 30
done

# 安定版の段階的スケールダウン
echo "📉 安定版段階的スケールダウン:"
for replicas in 3 2 1; do
    kubectl scale deployment canary-deployment --replicas=$replicas
    kubectl wait --for=condition=Available deployment/canary-deployment --timeout=300s
    echo "安定版レプリカ数: $replicas"
    sleep 30
done

echo "✅ カナリアデプロイメント完了!"
```

## Phase 3: DaemonSet による全ノード管理

### 3.1 ログ収集 DaemonSet

```yaml
# ファイル: log-collector-daemonset.yaml
apiVersion: apps/v1
kind: DaemonSet
metadata:
  name: log-collector
  labels:
    app: log-collector
spec:
  selector:
    matchLabels:
      app: log-collector
  template:
    metadata:
      labels:
        app: log-collector
    spec:
      tolerations:
      # マスターノードでも実行
      - key: node-role.kubernetes.io/control-plane
        operator: Exists
        effect: NoSchedule
      containers:
      - name: log-collector
        image: fluent/fluent-bit:2.1
        resources:
          requests:
            memory: "64Mi"
            cpu: "100m"
          limits:
            memory: "128Mi"
            cpu: "200m"
        volumeMounts:
        - name: varlog
          mountPath: /var/log
          readOnly: true
        - name: varlibdockercontainers
          mountPath: /var/lib/docker/containers
          readOnly: true
        - name: fluent-bit-config
          mountPath: /fluent-bit/etc
        env:
        - name: NODE_NAME
          valueFrom:
            fieldRef:
              fieldPath: spec.nodeName
      volumes:
      - name: varlog
        hostPath:
          path: /var/log
      - name: varlibdockercontainers
        hostPath:
          path: /var/lib/docker/containers
      - name: fluent-bit-config
        configMap:
          name: fluent-bit-config
      serviceAccount: log-collector
---
apiVersion: v1
kind: ServiceAccount
metadata:
  name: log-collector
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: log-collector
rules:
- apiGroups: [""]
  resources: ["pods", "namespaces"]
  verbs: ["get", "list", "watch"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: log-collector
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: log-collector
subjects:
- kind: ServiceAccount
  name: log-collector
  namespace: default
```

```bash
#!/bin/bash
# スクリプト: daemonset-operations.sh

echo "🔄 DaemonSet操作の実践..."

# Fluent Bit設定用ConfigMap作成
echo "📋 Fluent Bit設定作成中..."
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: ConfigMap
metadata:
  name: fluent-bit-config
data:
  fluent-bit.conf: |
    [SERVICE]
        Flush         1
        Log_Level     info
        Daemon        off
        Parsers_File  parsers.conf

    [INPUT]
        Name              tail
        Path              /var/log/containers/*.log
        Parser            docker
        Tag               kube.*
        Refresh_Interval  5
        Mem_Buf_Limit     5MB
        Skip_Long_Lines   On

    [FILTER]
        Name                kubernetes
        Match               kube.*
        Kube_URL            https://kubernetes.default.svc:443
        Kube_CA_File        /var/run/secrets/kubernetes.io/serviceaccount/ca.crt
        Kube_Token_File     /var/run/secrets/kubernetes.io/serviceaccount/token
        Merge_Log           On
        K8S-Logging.Parser  On
        K8S-Logging.Exclude Off

    [OUTPUT]
        Name  stdout
        Match *

  parsers.conf: |
    [PARSER]
        Name   docker
        Format json
        Time_Key time
        Time_Format %Y-%m-%dT%H:%M:%S.%L
        Time_Keep   On
EOF

# DaemonSet作成
echo "🚀 DaemonSet作成中..."
kubectl apply -f log-collector-daemonset.yaml

# DaemonSet状態確認
echo "⏳ DaemonSet起動待機中..."
kubectl rollout status daemonset/log-collector --timeout=300s

echo "📊 DaemonSet状態確認:"
kubectl get daemonset log-collector
kubectl get pods -l app=log-collector -o wide

# ノード毎の配置確認
echo "🗺️ ノード毎のPod配置確認:"
kubectl get pods -l app=log-collector -o wide --sort-by='{.spec.nodeName}'

# DaemonSetの詳細情報
echo "🔍 DaemonSet詳細情報:"
kubectl describe daemonset log-collector

# ログ収集動作確認
echo "📋 ログ収集動作確認:"
LOG_POD=$(kubectl get pods -l app=log-collector -o jsonpath='{.items[0].metadata.name}')
kubectl logs $LOG_POD --tail=20

# DaemonSetの更新
echo "🔄 DaemonSet更新テスト:"
kubectl patch daemonset log-collector -p '{"spec":{"template":{"spec":{"containers":[{"name":"log-collector","env":[{"name":"LOG_LEVEL","value":"debug"}]}]}}}}'

kubectl rollout status daemonset/log-collector --timeout=300s
echo "更新完了!"

echo "✅ DaemonSet操作完了!"
```

## Phase 4: StatefulSet でのステートフルアプリケーション

### 4.1 MongoDB クラスター StatefulSet

```yaml
# ファイル: mongodb-statefulset.yaml
apiVersion: v1
kind: Service
metadata:
  name: mongodb-headless
  labels:
    app: mongodb
spec:
  ports:
  - port: 27017
    targetPort: 27017
  clusterIP: None
  selector:
    app: mongodb
---
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: mongodb
spec:
  serviceName: mongodb-headless
  replicas: 3
  selector:
    matchLabels:
      app: mongodb
  template:
    metadata:
      labels:
        app: mongodb
    spec:
      containers:
      - name: mongodb
        image: mongo:5.0
        ports:
        - containerPort: 27017
        env:
        - name: MONGO_INITDB_ROOT_USERNAME
          value: admin
        - name: MONGO_INITDB_ROOT_PASSWORD
          value: password123
        volumeMounts:
        - name: mongodb-data
          mountPath: /data/db
        - name: mongodb-config
          mountPath: /data/configdb
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "1Gi"
            cpu: "1000m"
        livenessProbe:
          exec:
            command:
            - mongo
            - --eval
            - "db.adminCommand('ping')"
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          exec:
            command:
            - mongo
            - --eval
            - "db.adminCommand('ping')"
          initialDelaySeconds: 5
          periodSeconds: 10
  volumeClaimTemplates:
  - metadata:
      name: mongodb-data
    spec:
      accessModes: ["ReadWriteOnce"]
      resources:
        requests:
          storage: 10Gi
  - metadata:
      name: mongodb-config
    spec:
      accessModes: ["ReadWriteOnce"]
      resources:
        requests:
          storage: 1Gi
```

```bash
#!/bin/bash
# スクリプト: statefulset-operations.sh

echo "🗃️ StatefulSet操作の実践..."

# StatefulSet作成
echo "📦 MongoDB StatefulSet作成中..."
kubectl apply -f mongodb-statefulset.yaml

# StatefulSet起動待機
echo "⏳ StatefulSet起動待機中..."
kubectl wait --for=condition=Ready pod/mongodb-0 --timeout=600s
kubectl wait --for=condition=Ready pod/mongodb-1 --timeout=600s
kubectl wait --for=condition=Ready pod/mongodb-2 --timeout=600s

echo "📊 StatefulSet状態確認:"
kubectl get statefulset mongodb
kubectl get pods -l app=mongodb
kubectl get pvc

# Pod順序確認
echo "🔢 Pod作成順序確認:"
kubectl get pods -l app=mongodb -o wide --sort-by='{.metadata.creationTimestamp}'

# 永続ボリューム確認
echo "💾 永続ボリューム確認:"
kubectl get pv

# MongoDB接続テスト
echo "🔗 MongoDB接続テスト:"
kubectl exec mongodb-0 -- mongo --eval "
db.adminCommand('ping');
db.stats();
"

# レプリカセット設定
echo "🔄 MongoDB レプリカセット設定:"
kubectl exec mongodb-0 -- mongo --eval "
rs.initiate({
  _id: 'rs0',
  members: [
    {_id: 0, host: 'mongodb-0.mongodb-headless.default.svc.cluster.local:27017'},
    {_id: 1, host: 'mongodb-1.mongodb-headless.default.svc.cluster.local:27017'},
    {_id: 2, host: 'mongodb-2.mongodb-headless.default.svc.cluster.local:27017'}
  ]
});
"

sleep 30

# レプリカセット状態確認
echo "📊 レプリカセット状態確認:"
kubectl exec mongodb-0 -- mongo --eval "rs.status();"

# スケーリングテスト
echo "📈 StatefulSetスケーリングテスト:"
kubectl scale statefulset mongodb --replicas=5

echo "⏳ スケールアップ待機中..."
kubectl wait --for=condition=Ready pod/mongodb-4 --timeout=600s

kubectl get pods -l app=mongodb

# スケールダウン
kubectl scale statefulset mongodb --replicas=3

echo "⏳ スケールダウン完了待機..."
sleep 60

kubectl get pods -l app=mongodb
kubectl get pvc

echo "✅ StatefulSet操作完了!"
```

## Phase 5: Jobs と CronJobs でのバッチ処理

### 5.1 バックアップ Job

```yaml
# ファイル: backup-job.yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: database-backup
spec:
  completions: 1
  parallelism: 1
  backoffLimit: 3
  template:
    metadata:
      labels:
        app: backup
    spec:
      restartPolicy: Never
      containers:
      - name: backup
        image: alpine:3.18
        command:
        - /bin/sh
        - -c
        - |
          echo "🔄 バックアップ開始: $(date)"
          
          # 模擬データベースバックアップ
          mkdir -p /backup
          echo "データベース内容のダミー" > /backup/db-backup-$(date +%Y%m%d_%H%M%S).sql
          
          # 圧縮
          tar -czf /backup/backup-$(date +%Y%m%d_%H%M%S).tar.gz /backup/*.sql
          
          echo "📁 バックアップファイル作成:"
          ls -la /backup/
          
          echo "✅ バックアップ完了: $(date)"
          sleep 10
        volumeMounts:
        - name: backup-storage
          mountPath: /backup
        resources:
          requests:
            memory: "128Mi"
            cpu: "100m"
          limits:
            memory: "256Mi"
            cpu: "200m"
      volumes:
      - name: backup-storage
        emptyDir: {}
```

### 5.2 定期実行 CronJob

```yaml
# ファイル: cleanup-cronjob.yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: cleanup-job
spec:
  schedule: "*/5 * * * *"  # 5分毎に実行
  jobTemplate:
    spec:
      template:
        spec:
          restartPolicy: OnFailure
          containers:
          - name: cleanup
            image: alpine:3.18
            command:
            - /bin/sh
            - -c
            - |
              echo "🧹 クリーンアップ開始: $(date)"
              
              # 古いログファイルの削除（模擬）
              echo "古いログファイルを削除中..."
              find /tmp -name "*.log" -mtime +7 -delete 2>/dev/null || true
              
              # 一時ファイルの削除
              echo "一時ファイルを削除中..."
              rm -rf /tmp/temp-* 2>/dev/null || true
              
              # ディスク使用量確認
              echo "📊 ディスク使用量:"
              df -h
              
              echo "✅ クリーンアップ完了: $(date)"
            resources:
              requests:
                memory: "64Mi"
                cpu: "50m"
              limits:
                memory: "128Mi"
                cpu: "100m"
  successfulJobsHistoryLimit: 3
  failedJobsHistoryLimit: 1
  concurrencyPolicy: Forbid
```

```bash
#!/bin/bash
# スクリプト: jobs-cronjobs-operations.sh

echo "⏰ Jobs と CronJobs 操作の実践..."

# 単発Job実行
echo "🚀 バックアップJob実行中..."
kubectl apply -f backup-job.yaml

# Job完了待機
echo "⏳ Job完了待機中..."
kubectl wait --for=condition=complete job/database-backup --timeout=300s

echo "📊 Job状態確認:"
kubectl get job database-backup
kubectl describe job database-backup

# Job実行ログ確認
echo "📋 Jobログ確認:"
JOB_POD=$(kubectl get pods -l app=backup -o jsonpath='{.items[0].metadata.name}')
kubectl logs $JOB_POD

# CronJob作成
echo "⏰ CronJob作成中..."
kubectl apply -f cleanup-cronjob.yaml

echo "📊 CronJob状態確認:"
kubectl get cronjob cleanup-job
kubectl describe cronjob cleanup-job

# CronJobの実行を待機
echo "⏳ CronJob実行待機中（最大10分）..."
sleep 360  # 6分待機（次の実行を確認）

echo "📊 CronJob実行履歴:"
kubectl get jobs -l app=cleanup

# 手動でCronJob実行
echo "🔧 CronJobの手動実行:"
kubectl create job --from=cronjob/cleanup-job manual-cleanup-$(date +%s)

# 実行中Jobの確認
echo "📊 実行中Job確認:"
kubectl get jobs

# 失敗するJobの例
echo "❌ 失敗Job例の作成:"
cat <<EOF | kubectl apply -f -
apiVersion: batch/v1
kind: Job
metadata:
  name: failing-job
spec:
  backoffLimit: 2
  template:
    spec:
      restartPolicy: Never
      containers:
      - name: failing-container
        image: alpine:3.18
        command: ['sh', '-c', 'echo "処理開始..."; sleep 10; exit 1']
EOF

# 失敗Jobの動作確認
echo "⏳ 失敗Job動作確認中..."
sleep 60

kubectl get job failing-job
kubectl describe job failing-job

echo "✅ Jobs と CronJobs 操作完了!"
```

## Phase 6: リソース管理とクォータ設定

### 6.1 Namespace とリソースクォータ

```yaml
# ファイル: resource-management.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: production
  labels:
    environment: production
---
apiVersion: v1
kind: ResourceQuota
metadata:
  name: production-quota
  namespace: production
spec:
  hard:
    requests.cpu: "4"
    requests.memory: 8Gi
    limits.cpu: "8"
    limits.memory: 16Gi
    persistentvolumeclaims: "10"
    pods: "20"
    services: "5"
    secrets: "10"
    configmaps: "10"
---
apiVersion: v1
kind: LimitRange
metadata:
  name: production-limits
  namespace: production
spec:
  limits:
  - default:
      cpu: "500m"
      memory: "512Mi"
    defaultRequest:
      cpu: "100m"
      memory: "128Mi"
    type: Container
  - max:
      cpu: "2"
      memory: "2Gi"
    min:
      cpu: "50m"
      memory: "64Mi"
    type: Container
```

```bash
#!/bin/bash
# スクリプト: resource-management.sh

echo "📊 リソース管理の実践..."

# リソース管理設定適用
kubectl apply -f resource-management.yaml

echo "📋 リソースクォータ確認:"
kubectl get resourcequota -n production
kubectl describe resourcequota production-quota -n production

echo "📏 LimitRange確認:"
kubectl get limitrange -n production
kubectl describe limitrange production-limits -n production

# リソース制限テスト用アプリケーション
echo "🧪 リソース制限テスト:"
cat <<EOF | kubectl apply -f -
apiVersion: apps/v1
kind: Deployment
metadata:
  name: resource-test
  namespace: production
spec:
  replicas: 2
  selector:
    matchLabels:
      app: resource-test
  template:
    metadata:
      labels:
        app: resource-test
    spec:
      containers:
      - name: app
        image: nginx:1.20
        resources:
          requests:
            memory: "256Mi"
            cpu: "200m"
          limits:
            memory: "512Mi"
            cpu: "400m"
EOF

kubectl wait --for=condition=Available deployment/resource-test -n production --timeout=300s

echo "📊 リソース使用量確認:"
kubectl top pods -n production
kubectl describe resourcequota production-quota -n production

# クォータ制限テスト
echo "⚠️ クォータ制限テスト（失敗例）:"
cat <<EOF | kubectl apply -f -
apiVersion: apps/v1
kind: Deployment
metadata:
  name: quota-exceed-test
  namespace: production
spec:
  replicas: 10  # 意図的にPod数制限を超過
  selector:
    matchLabels:
      app: quota-exceed-test
  template:
    metadata:
      labels:
        app: quota-exceed-test
    spec:
      containers:
      - name: app
        image: nginx:1.20
        resources:
          requests:
            memory: "1Gi"  # 意図的にメモリ制限を超過
            cpu: "500m"
EOF

sleep 30
kubectl get deployment quota-exceed-test -n production
kubectl describe deployment quota-exceed-test -n production

echo "✅ リソース管理テスト完了!"
```

## Phase 7: クリーンアップ

```bash
#!/bin/bash
# スクリプト: cleanup-workloads.sh

echo "🧹 ワークロード完全クリーンアップ中..."

# 作成したリソースの削除
kubectl delete pod nginx-pod --ignore-not-found
kubectl delete pod multi-container-pod --ignore-not-found

kubectl delete deployment web-app-deployment --ignore-not-found
kubectl delete deployment canary-deployment --ignore-not-found
kubectl delete deployment canary-deployment-v2 --ignore-not-found
kubectl delete service web-app-service --ignore-not-found
kubectl delete service canary-service --ignore-not-found

kubectl delete daemonset log-collector --ignore-not-found
kubectl delete configmap fluent-bit-config --ignore-not-found
kubectl delete serviceaccount log-collector --ignore-not-found
kubectl delete clusterrole log-collector --ignore-not-found
kubectl delete clusterrolebinding log-collector --ignore-not-found

kubectl delete statefulset mongodb --ignore-not-found
kubectl delete service mongodb-headless --ignore-not-found
kubectl delete pvc -l app=mongodb --ignore-not-found

kubectl delete job database-backup --ignore-not-found
kubectl delete job failing-job --ignore-not-found
kubectl delete cronjob cleanup-job --ignore-not-found
kubectl delete job -l app=cleanup --ignore-not-found

kubectl delete namespace production --ignore-not-found

kubectl delete configmap nginx-config --ignore-not-found

echo "✅ クリーンアップ完了!"

# 残存リソース確認
echo "📊 残存リソース確認:"
kubectl get all
kubectl get pv
```

## 📚 学習のポイント

### CKA試験でのワークロード管理要点

1. **必須kubectl コマンド**
   ```bash
   kubectl create deployment
   kubectl scale deployment
   kubectl rollout status/undo/history
   kubectl exec -it
   kubectl logs
   kubectl describe
   ```

2. **リソース管理**
   ```bash
   kubectl top nodes/pods
   kubectl apply -f
   kubectl delete
   kubectl get events
   ```

3. **トラブルシューティング**
   ```bash
   kubectl describe pod <name>
   kubectl logs <pod> -c <container>
   kubectl get events --sort-by=.metadata.creationTimestamp
   ```

## 🎯 次のステップ

**完了したスキル:**
- [x] Pod ライフサイクル管理
- [x] Deployment によるアプリケーション管理
- [x] DaemonSet による全ノード展開
- [x] StatefulSet でのステートフル管理
- [x] Jobs/CronJobs でのバッチ処理
- [x] リソース制限とクォータ管理

**次のラボ:** [Lab 3: Services とネットワーキング](./lab03-services-networking.md)