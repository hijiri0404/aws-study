# Certified Kubernetes Application Developer (CKAD) 想定問題集

## 📋 試験について

- **問題数**: 100問（実際の試験は15-20問の実技）
- **制限時間**: 120分
- **合格点**: 66%
- **形式**: 実技問題（kubectl コマンド実行）

## 🎯 Core Concepts (13%) - 問題1-13

### 問題1
以下の要件でPodを作成してください：
- Pod名: `nginx-pod`
- Image: `nginx:1.20`
- Namespace: `development`

**コマンド例**:
```bash
kubectl create namespace development
kubectl run nginx-pod --image=nginx:1.20 -n development
```

### 問題2
既存のPod `web-app` を編集して、環境変数 `DB_HOST=mysql-service` を追加してください。

**コマンド例**:
```bash
kubectl edit pod web-app
# または
kubectl set env pod/web-app DB_HOST=mysql-service
```

### 問題3
次の条件を満たすPodマニフェストを作成してください：
- Pod名: `multi-container-pod`
- Container1: `nginx:1.20`, name: `web`
- Container2: `redis:6.0`, name: `cache`
- Labels: `app=web`, `tier=frontend`

**YAML例**:
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: multi-container-pod
  labels:
    app: web
    tier: frontend
spec:
  containers:
  - name: web
    image: nginx:1.20
  - name: cache
    image: redis:6.0
```

## 🎯 Configuration (18%) - 問題14-31

### 問題14
ConfigMapを作成し、Podで使用してください：
- ConfigMap名: `app-config`
- Key: `database.url`, Value: `mongodb://localhost:27017`
- Podでこの値を環境変数として使用

**コマンド例**:
```bash
kubectl create configmap app-config --from-literal=database.url=mongodb://localhost:27017
```

## 📊 実技試験のコツ

### 時間管理
- **120分で15-20問**: 問題あたり6-8分
- **簡単な問題から**: 確実に点数を取る
- **複雑な問題**: 後回しにして時間配分を調整

### kubectl コマンド効率化
```bash
# エイリアス設定
alias k=kubectl
export do="--dry-run=client -o yaml"
export now="--force --grace-period 0"
```

---

### 問題4
Secretを作成し、Podでボリュームマウントしてください：
- Secret名: `app-secret`
- Key: `password`, Value: `mySecretPassword`
- Podでこの値を `/etc/secret` にマウント

**コマンド例**:
```bash
kubectl create secret generic app-secret --from-literal=password=mySecretPassword
# Pod YAML で volumeMounts と volumes を設定
```

### 問題5
以下の条件でReplicaSetを作成してください：
- ReplicaSet名: `nginx-rs`
- Replicas: 3
- Image: `nginx:1.20`
- Labels: `app=nginx`

**YAML例**:
```yaml
apiVersion: apps/v1
kind: ReplicaSet
metadata:
  name: nginx-rs
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
```

### 問題6
Deploymentを作成し、イメージをアップデートしてください：
- Deployment名: `web-deployment`
- 初期イメージ: `nginx:1.19`
- アップデート後: `nginx:1.20`
- Replicas: 4

**コマンド例**:
```bash
kubectl create deployment web-deployment --image=nginx:1.19 --replicas=4
kubectl set image deployment/web-deployment nginx=nginx:1.20
```

### 問題7
Serviceを作成してDeploymentを公開してください：
- Service名: `web-service`
- Type: ClusterIP
- Port: 80
- Target Port: 8080
- Selector: `app=web`

**YAML例**:
```yaml
apiVersion: v1
kind: Service
metadata:
  name: web-service
spec:
  type: ClusterIP
  ports:
  - port: 80
    targetPort: 8080
  selector:
    app: web
```

### 問題8
JobとCronJobを作成してください：
- Job名: `data-processing-job`
- Image: `busybox`
- Command: `echo "Processing data..." && sleep 30`
- Completions: 1

**コマンド例**:
```bash
kubectl create job data-processing-job --image=busybox -- /bin/sh -c "echo 'Processing data...' && sleep 30"
```

### 問題9
StatefulSetを作成してください：
- StatefulSet名: `database-sts`
- Image: `mysql:8.0`
- Replicas: 2
- 環境変数: `MYSQL_ROOT_PASSWORD=password`

**YAML例**:
```yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: database-sts
spec:
  replicas: 2
  serviceName: database-service
  selector:
    matchLabels:
      app: database
  template:
    metadata:
      labels:
        app: database
    spec:
      containers:
      - name: mysql
        image: mysql:8.0
        env:
        - name: MYSQL_ROOT_PASSWORD
          value: password
```

### 問題10
DaemonSetを作成してください：
- DaemonSet名: `log-collector`
- Image: `fluentd:v1.14`
- 全ノードで実行
- hostPath volume を `/var/log` から `/var/log` にマウント

**YAML例**:
```yaml
apiVersion: apps/v1
kind: DaemonSet
metadata:
  name: log-collector
spec:
  selector:
    matchLabels:
      app: log-collector
  template:
    metadata:
      labels:
        app: log-collector
    spec:
      containers:
      - name: fluentd
        image: fluentd:v1.14
        volumeMounts:
        - name: varlog
          mountPath: /var/log
      volumes:
      - name: varlog
        hostPath:
          path: /var/log
```

### 問題11
NetworkPolicyを作成してください：
- NetworkPolicy名: `deny-all`
- すべての Ingress トラフィックを拒否
- Namespace: `secure`

**YAML例**:
```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: deny-all
  namespace: secure
spec:
  podSelector: {}
  policyTypes:
  - Ingress
```

### 問題12
ResourceQuotaを作成してください：
- ResourceQuota名: `compute-quota`
- CPU requests: 4 cores
- Memory requests: 8Gi
- Pods: 10
- Namespace: `limited`

**YAML例**:
```yaml
apiVersion: v1
kind: ResourceQuota
metadata:
  name: compute-quota
  namespace: limited
spec:
  hard:
    requests.cpu: "4"
    requests.memory: 8Gi
    pods: "10"
```

### 問題13
PersistentVolumeClaimを作成してください：
- PVC名: `data-pvc`
- Storage: 10Gi
- Access Mode: ReadWriteOnce
- Storage Class: `standard`

**YAML例**:
```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: data-pvc
spec:
  accessModes:
  - ReadWriteOnce
  storageClassName: standard
  resources:
    requests:
      storage: 10Gi
```

## 🎯 Configuration (18%) - 問題14-31

### 問題14
ConfigMapを作成し、Podで使用してください：
- ConfigMap名: `app-config`
- Key: `database.url`, Value: `mongodb://localhost:27017`
- Podでこの値を環境変数として使用

**コマンド例**:
```bash
kubectl create configmap app-config --from-literal=database.url=mongodb://localhost:27017
```

### 問題15
Secretを使用してPodに認証情報を提供してください：
- Secret名: `db-credentials`
- Keys: `username=admin`, `password=secret123`
- Podで環境変数として使用

**コマンド例**:
```bash
kubectl create secret generic db-credentials --from-literal=username=admin --from-literal=password=secret123
```

### 問題16
ConfigMapをファイルとしてPodにマウントしてください：
- ConfigMap名: `nginx-conf`
- Key: `nginx.conf`, Value: nginx設定内容
- Mount path: `/etc/nginx/nginx.conf`

**YAML例**:
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: nginx-pod
spec:
  containers:
  - name: nginx
    image: nginx:1.20
    volumeMounts:
    - name: nginx-config
      mountPath: /etc/nginx/nginx.conf
      subPath: nginx.conf
  volumes:
  - name: nginx-config
    configMap:
      name: nginx-conf
```

### 問題17
SecurityContextを設定してPodを作成してください：
- 非rootユーザーで実行 (UID: 1000)
- 読み取り専用ルートファイルシステム
- runAsNonRoot: true

**YAML例**:
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: secure-pod
spec:
  securityContext:
    runAsUser: 1000
    runAsNonRoot: true
  containers:
  - name: app
    image: nginx:1.20
    securityContext:
      readOnlyRootFilesystem: true
```

### 問題18
ResourcesのRequestsとLimitsを設定してください：
- CPU request: 100m, limit: 200m
- Memory request: 128Mi, limit: 256Mi
- Pod名: `resource-controlled-pod`

**YAML例**:
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: resource-controlled-pod
spec:
  containers:
  - name: app
    image: nginx:1.20
    resources:
      requests:
        cpu: 100m
        memory: 128Mi
      limits:
        cpu: 200m
        memory: 256Mi
```

### 問題19
ServiceAccountを作成し、Podで使用してください：
- ServiceAccount名: `app-sa`
- Namespace: `default`
- Podでこの ServiceAccount を使用

**コマンド例**:
```bash
kubectl create serviceaccount app-sa
kubectl patch pod my-pod -p '{"spec":{"serviceAccountName":"app-sa"}}'
```

### 問題20
Environmentファイルから ConfigMap を作成してください：
- ファイル名: `app.env`
- 内容: `DB_HOST=localhost`, `DB_PORT=5432`
- ConfigMap名: `env-config`

**コマンド例**:
```bash
echo -e "DB_HOST=localhost\nDB_PORT=5432" > app.env
kubectl create configmap env-config --from-env-file=app.env
```

### 問題21
複数のSecretを組み合わせてPodで使用してください：
- Secret1: `api-key` (key: apikey)
- Secret2: `db-password` (key: password)
- 両方とも環境変数として使用

**YAML例**:
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: multi-secret-pod
spec:
  containers:
  - name: app
    image: nginx:1.20
    env:
    - name: API_KEY
      valueFrom:
        secretKeyRef:
          name: api-key
          key: apikey
    - name: DB_PASSWORD
      valueFrom:
        secretKeyRef:
          name: db-password
          key: password
```

### 问题22
InitContainerを使用してPodを作成してください：
- InitContainer: データベース接続確認
- MainContainer: アプリケーション実行
- initContainer image: `busybox`
- main container image: `nginx:1.20`

**YAML例**:
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: init-container-pod
spec:
  initContainers:
  - name: init-db
    image: busybox
    command: ['sh', '-c', 'until nc -z db-service 5432; do sleep 1; done']
  containers:
  - name: app
    image: nginx:1.20
```

### 問題23
Podの環境変数にDownward APIを使用してください：
- Pod名を環境変数 `POD_NAME` として設定
- Namespaceを環境変数 `POD_NAMESPACE` として設定

**YAML例**:
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: downward-api-pod
spec:
  containers:
  - name: app
    image: nginx:1.20
    env:
    - name: POD_NAME
      valueFrom:
        fieldRef:
          fieldPath: metadata.name
    - name: POD_NAMESPACE
      valueFrom:
        fieldRef:
          fieldPath: metadata.namespace
```

### 問題24
EmptyDirボリュームを使用してください：
- Volume名: `shared-data`
- Mount path: `/data`
- 2つのコンテナで共有

**YAML例**:
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: shared-volume-pod
spec:
  containers:
  - name: container1
    image: nginx:1.20
    volumeMounts:
    - name: shared-data
      mountPath: /data
  - name: container2
    image: busybox
    command: ['sleep', '3600']
    volumeMounts:
    - name: shared-data
      mountPath: /data
  volumes:
  - name: shared-data
    emptyDir: {}
```

### 問題25
HostPathボリュームを使用してください：
- Host path: `/var/log`
- Container mount path: `/host-logs`
- 読み取り専用でマウント

**YAML例**:
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: hostpath-pod
spec:
  containers:
  - name: app
    image: nginx:1.20
    volumeMounts:
    - name: host-logs
      mountPath: /host-logs
      readOnly: true
  volumes:
  - name: host-logs
    hostPath:
      path: /var/log
      type: Directory
```

### 問題26
PersistentVolumeClaimを使用してPodでストレージを利用してください：
- PVC名: `app-storage`
- Storage: 5Gi
- Mount path: `/app/data`

**YAML例**:
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: pvc-pod
spec:
  containers:
  - name: app
    image: nginx:1.20
    volumeMounts:
    - name: app-data
      mountPath: /app/data
  volumes:
  - name: app-data
    persistentVolumeClaim:
      claimName: app-storage
```

### 問題27
NodeSelectorを使用してPodを特定のノードにスケジュールしてください：
- NodeSelector: `disktype=ssd`
- Pod名: `node-selector-pod`

**YAML例**:
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: node-selector-pod
spec:
  nodeSelector:
    disktype: ssd
  containers:
  - name: app
    image: nginx:1.20
```

### 問題28
Affinityを使用してPodスケジューリングを制御してください：
- nodeAffinity: `zone=us-west-1` を優先
- podAntiAffinity: 同じアプリの Pod を異なるノードに配置

**YAML例**:
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: affinity-pod
  labels:
    app: web-server
spec:
  affinity:
    nodeAffinity:
      preferredDuringSchedulingIgnoredDuringExecution:
      - weight: 100
        preference:
          matchExpressions:
          - key: zone
            operator: In
            values: ["us-west-1"]
    podAntiAffinity:
      preferredDuringSchedulingIgnoredDuringExecution:
      - weight: 100
        podAffinityTerm:
          labelSelector:
            matchExpressions:
            - key: app
              operator: In
              values: ["web-server"]
          topologyKey: kubernetes.io/hostname
  containers:
  - name: app
    image: nginx:1.20
```

### 問題29
TaintとTolerationを使用してください：
- ノードにTaint: `special=true:NoSchedule`
- Podに対応するToleration

**コマンド例**:
```bash
kubectl taint nodes node1 special=true:NoSchedule
```

**YAML例**:
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: toleration-pod
spec:
  tolerations:
  - key: "special"
    operator: "Equal"
    value: "true"
    effect: "NoSchedule"
  containers:
  - name: app
    image: nginx:1.20
```

### 問題30
LivenessProbeとReadinessProbeを設定してください：
- LivenessProbe: HTTP GET `/health` port 8080
- ReadinessProbe: HTTP GET `/ready` port 8080
- 初期遅延: 30秒、間隔: 10秒

**YAML例**:
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: probe-pod
spec:
  containers:
  - name: app
    image: nginx:1.20
    ports:
    - containerPort: 8080
    livenessProbe:
      httpGet:
        path: /health
        port: 8080
      initialDelaySeconds: 30
      periodSeconds: 10
    readinessProbe:
      httpGet:
        path: /ready
        port: 8080
      initialDelaySeconds: 30
      periodSeconds: 10
```

### 問題31
StartupProbeを含む包括的なProbe設定をしてください：
- StartupProbe: TCP socket port 8080
- LivenessProbe: exec command
- ReadinessProbe: HTTP GET

**YAML例**:
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: comprehensive-probe-pod
spec:
  containers:
  - name: app
    image: nginx:1.20
    ports:
    - containerPort: 8080
    startupProbe:
      tcpSocket:
        port: 8080
      initialDelaySeconds: 10
      periodSeconds: 5
      failureThreshold: 10
    livenessProbe:
      exec:
        command:
        - cat
        - /tmp/healthy
      initialDelaySeconds: 30
      periodSeconds: 10
    readinessProbe:
      httpGet:
        path: /ready
        port: 8080
      initialDelaySeconds: 5
      periodSeconds: 5
```

## 🎯 Multi-Container Pods (10%) - 問題32-41

### 問題32
サイドカーパターンでログ収集を実装してください：
- メインコンテナ: `nginx:1.20`
- サイドカー: `busybox` (ログ収集)
- 共有ボリューム: `/var/log/nginx`

**YAML例**:
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: sidecar-logging-pod
spec:
  containers:
  - name: nginx
    image: nginx:1.20
    volumeMounts:
    - name: shared-logs
      mountPath: /var/log/nginx
  - name: log-collector
    image: busybox
    command: ['sh', '-c', 'tail -f /var/log/nginx/access.log']
    volumeMounts:
    - name: shared-logs
      mountPath: /var/log/nginx
  volumes:
  - name: shared-logs
    emptyDir: {}
```

### 問題33
Ambassadorパターンでプロキシを実装してください：
- アプリコンテナ: `nginx:1.20`
- Ambassadorコンテナ: `envoyproxy/envoy:v1.18.0`
- ポート: アプリ8080、プロキシ80

**YAML例**:
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: ambassador-pod
spec:
  containers:
  - name: app
    image: nginx:1.20
    ports:
    - containerPort: 8080
  - name: ambassador
    image: envoyproxy/envoy:v1.18.0
    ports:
    - containerPort: 80
```

### 問題34
Adapterパターンでデータ変換を実装してください：
- メインコンテナ: カスタムアプリ
- Adapterコンテナ: データフォーマット変換
- 共有ボリューム使用

**YAML例**:
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: adapter-pod
spec:
  containers:
  - name: app
    image: my-app:latest
    volumeMounts:
    - name: shared-data
      mountPath: /app/data
  - name: adapter
    image: data-adapter:latest
    command: ['sh', '-c', 'while true; do convert_data.sh; sleep 60; done']
    volumeMounts:
    - name: shared-data
      mountPath: /data
  volumes:
  - name: shared-data
    emptyDir: {}
```

### 問題35
InitContainerでデータベースマイグレーションを実行してください：
- InitContainer: データベースマイグレーション
- MainContainer: Webアプリケーション
- 共有設定使用

**YAML例**:
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: migration-pod
spec:
  initContainers:
  - name: db-migration
    image: migrate/migrate
    command: ['migrate', '-path', '/migrations', '-database', 'postgres://...', 'up']
  containers:
  - name: web-app
    image: my-web-app:latest
    ports:
    - containerPort: 8080
```

### 問題36
複数InitContainerの順次実行を設定してください：
- InitContainer1: 設定ファイル準備
- InitContainer2: データベース接続確認
- InitContainer3: 権限設定
- MainContainer: アプリケーション

**YAML例**:
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: multi-init-pod
spec:
  initContainers:
  - name: setup-config
    image: busybox
    command: ['sh', '-c', 'echo "Config prepared" > /shared/config.txt']
    volumeMounts:
    - name: shared-vol
      mountPath: /shared
  - name: check-db
    image: busybox
    command: ['sh', '-c', 'until nc -z database 5432; do sleep 1; done']
  - name: set-permissions
    image: busybox
    command: ['sh', '-c', 'chmod 755 /shared/config.txt']
    volumeMounts:
    - name: shared-vol
      mountPath: /shared
  containers:
  - name: app
    image: nginx:1.20
    volumeMounts:
    - name: shared-vol
      mountPath: /app/config
  volumes:
  - name: shared-vol
    emptyDir: {}
```

### 問題37
共有メモリを使用するMulti-Containerを作成してください：
- Container1: データプロデューサー
- Container2: データコンシューマー
- 共有メモリボリューム使用

**YAML例**:
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: shared-memory-pod
spec:
  containers:
  - name: producer
    image: busybox
    command: ['sh', '-c', 'while true; do echo $(date) > /shared/data.txt; sleep 5; done']
    volumeMounts:
    - name: shared-memory
      mountPath: /shared
  - name: consumer
    image: busybox
    command: ['sh', '-c', 'while true; do cat /shared/data.txt; sleep 10; done']
    volumeMounts:
    - name: shared-memory
      mountPath: /shared
  volumes:
  - name: shared-memory
    emptyDir:
      medium: Memory
```

### 問題38
ファイル監視とレスポンスのパターンを実装してください：
- Container1: ファイル作成
- Container2: ファイル監視と処理
- 共有ボリューム使用

**YAML例**:
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: file-watcher-pod
spec:
  containers:
  - name: file-creator
    image: busybox
    command: ['sh', '-c', 'while true; do echo "New file $(date)" > /watch/file-$(date +%s).txt; sleep 30; done']
    volumeMounts:
    - name: watch-dir
      mountPath: /watch
  - name: file-watcher
    image: busybox
    command: ['sh', '-c', 'while true; do inotifywait -e create /watch && echo "File detected"; done']
    volumeMounts:
    - name: watch-dir
      mountPath: /watch
  volumes:
  - name: watch-dir
    emptyDir: {}
```

### 問題39
ネットワーク監視サイドカーを実装してください：
- アプリコンテナ: Webサーバー
- 監視コンテナ: ネットワークトラフィック監視
- localhost 通信使用

**YAML例**:
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: network-monitor-pod
spec:
  containers:
  - name: web-server
    image: nginx:1.20
    ports:
    - containerPort: 80
  - name: network-monitor
    image: nicolaka/netshoot
    command: ['sh', '-c', 'while true; do ss -tulpn; sleep 30; done']
    securityContext:
      capabilities:
        add: ["NET_ADMIN"]
```

### 問題40
セキュリティスキャンサイドカーを実装してください：
- アプリコンテナ: 標準アプリケーション
- セキュリティコンテナ: 脆弱性スキャン
- 定期実行設定

**YAML例**:
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: security-scan-pod
spec:
  containers:
  - name: app
    image: nginx:1.20
    ports:
    - containerPort: 80
  - name: security-scanner
    image: aquasec/trivy:latest
    command: ['sh', '-c', 'while true; do trivy fs /; sleep 3600; done']
    volumeMounts:
    - name: app-volume
      mountPath: /scan-target
  volumes:
  - name: app-volume
    emptyDir: {}
```

### 問題41
データ同期パターンを実装してください：
- Container1: データソース
- Container2: データ同期
- Container3: データ検証
- 順次処理パイプライン

**YAML例**:
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: data-sync-pod
spec:
  containers:
  - name: data-source
    image: busybox
    command: ['sh', '-c', 'while true; do echo "Data: $(date)" >> /data/source.log; sleep 10; done']
    volumeMounts:
    - name: data-volume
      mountPath: /data
  - name: data-sync
    image: busybox
    command: ['sh', '-c', 'while true; do cp /data/source.log /data/synced.log; sleep 15; done']
    volumeMounts:
    - name: data-volume
      mountPath: /data
  - name: data-validator
    image: busybox
    command: ['sh', '-c', 'while true; do wc -l /data/synced.log; sleep 20; done']
    volumeMounts:
    - name: data-volume
      mountPath: /data
  volumes:
  - name: data-volume
    emptyDir: {}
```

## 🎯 Observability (18%) - 問題42-59

### 問題42
包括的なロギング設定をしてください：
- アプリケーションログ出力
- 構造化JSON形式
- ログレベル設定
- ローテーション設定

**YAML例**:
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: logging-pod
spec:
  containers:
  - name: app
    image: nginx:1.20
    env:
    - name: LOG_LEVEL
      value: "INFO"
    - name: LOG_FORMAT
      value: "json"
    volumeMounts:
    - name: log-volume
      mountPath: /var/log/app
  volumes:
  - name: log-volume
    emptyDir: {}
```

### 問題43
アプリケーションのヘルスチェックを実装してください：
- HTTP health endpoint
- Custom health check script
- 失敗時の再起動設定

**YAML例**:
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: health-check-pod
spec:
  containers:
  - name: app
    image: nginx:1.20
    ports:
    - containerPort: 80
    livenessProbe:
      httpGet:
        path: /health
        port: 80
      initialDelaySeconds: 30
      periodSeconds: 10
      failureThreshold: 3
    readinessProbe:
      exec:
        command:
        - /bin/sh
        - -c
        - "curl -f http://localhost/ready || exit 1"
      initialDelaySeconds: 5
      periodSeconds: 5
```

### 問題44
メトリクス収集の設定をしてください：
- Prometheus形式メトリクス
- カスタムメトリクス
- アノテーション設定

**YAML例**:
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: metrics-pod
  annotations:
    prometheus.io/scrape: "true"
    prometheus.io/port: "8080"
    prometheus.io/path: "/metrics"
spec:
  containers:
  - name: app
    image: my-app:latest
    ports:
    - containerPort: 8080
      name: metrics
    env:
    - name: METRICS_ENABLED
      value: "true"
```

### 問題45
分散トレーシングを設定してください：
- Jaeger tracing
- トレースID伝播
- スパン作成

**YAML例**:
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: tracing-pod
spec:
  containers:
  - name: app
    image: my-app:latest
    env:
    - name: JAEGER_AGENT_HOST
      value: "jaeger-agent"
    - name: JAEGER_AGENT_PORT
      value: "6831"
    - name: JAEGER_SERVICE_NAME
      value: "my-service"
```

### 問題46
ログ集約サイドカーを実装してください：
- アプリケーションログ
- システムログ
- エラーログ分離

**YAML例**:
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: log-aggregation-pod
spec:
  containers:
  - name: app
    image: nginx:1.20
    volumeMounts:
    - name: app-logs
      mountPath: /var/log/nginx
  - name: log-aggregator
    image: fluentd:v1.14
    command: ['fluentd', '-c', '/fluentd/etc/fluent.conf']
    volumeMounts:
    - name: app-logs
      mountPath: /var/log/nginx
    - name: fluentd-config
      mountPath: /fluentd/etc
  volumes:
  - name: app-logs
    emptyDir: {}
  - name: fluentd-config
    configMap:
      name: fluentd-config
```

### 問題47
エラー処理とアラートを設定してください：
- エラー検出
- アラート送信
- 自動復旧

**YAML例**:
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: error-handling-pod
spec:
  containers:
  - name: app
    image: my-app:latest
    livenessProbe:
      httpGet:
        path: /health
        port: 8080
      initialDelaySeconds: 30
      periodSeconds: 10
      failureThreshold: 3
    env:
    - name: ALERT_WEBHOOK_URL
      valueFrom:
        secretKeyRef:
          name: alert-config
          key: webhook-url
```

### 問題48
パフォーマンス監視を実装してください：
- CPU/メモリ使用量
- レスポンス時間測定
- スループット測定

**YAML例**:
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: performance-monitoring-pod
spec:
  containers:
  - name: app
    image: my-app:latest
    resources:
      requests:
        cpu: 100m
        memory: 128Mi
      limits:
        cpu: 500m
        memory: 512Mi
    env:
    - name: PERFORMANCE_MONITORING
      value: "enabled"
  - name: performance-collector
    image: telegraf:latest
    volumeMounts:
    - name: telegraf-config
      mountPath: /etc/telegraf
  volumes:
  - name: telegraf-config
    configMap:
      name: telegraf-config
```

### 問題49
デバッグ情報収集を設定してください：
- Debug endpoints
- 詳細ログ設定
- プロファイリング有効化

**YAML例**:
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: debug-pod
spec:
  containers:
  - name: app
    image: my-app:latest
    ports:
    - containerPort: 8080
    - containerPort: 6060
      name: debug
    env:
    - name: DEBUG_MODE
      value: "true"
    - name: LOG_LEVEL
      value: "DEBUG"
    - name: PPROF_ENABLED
      value: "true"
```

### 問題50
カスタムメトリクスエクスポーターを作成してください：
- ビジネスメトリクス
- 技術メトリクス
- Prometheusフォーマット

**YAML例**:
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: custom-metrics-pod
  annotations:
    prometheus.io/scrape: "true"
    prometheus.io/port: "9090"
spec:
  containers:
  - name: app
    image: my-app:latest
  - name: metrics-exporter
    image: prom/node-exporter:latest
    ports:
    - containerPort: 9090
      name: metrics
```

### 問題51
ログ解析とフィルタリングを実装してください：
- ログパースィング
- エラーフィルタリング
- 重要度分類

**YAML例**:
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: log-analysis-pod
spec:
  containers:
  - name: app
    image: nginx:1.20
    volumeMounts:
    - name: log-volume
      mountPath: /var/log/nginx
  - name: log-analyzer
    image: logstash:7.15.0
    command: ['logstash', '-f', '/usr/share/logstash/pipeline/logstash.conf']
    volumeMounts:
    - name: log-volume
      mountPath: /var/log/nginx
    - name: logstash-config
      mountPath: /usr/share/logstash/pipeline
  volumes:
  - name: log-volume
    emptyDir: {}
  - name: logstash-config
    configMap:
      name: logstash-config
```

### 問題52
リアルタイム監視ダッシュボードを設定してください：
- Grafana統合
- 基本メトリクス
- アラート設定

**YAML例**:
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: monitoring-dashboard-pod
spec:
  containers:
  - name: grafana
    image: grafana/grafana:latest
    ports:
    - containerPort: 3000
    env:
    - name: GF_SECURITY_ADMIN_PASSWORD
      valueFrom:
        secretKeyRef:
          name: grafana-config
          key: admin-password
    volumeMounts:
    - name: grafana-storage
      mountPath: /var/lib/grafana
  volumes:
  - name: grafana-storage
    emptyDir: {}
```

### 問題53
アプリケーション状態監視を実装してください：
- サービスディスカバリー
- 依存関係チェック
- サーキットブレーカー

**YAML例**:
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: service-monitor-pod
spec:
  containers:
  - name: app
    image: my-app:latest
    env:
    - name: CIRCUIT_BREAKER_ENABLED
      value: "true"
    - name: DEPENDENCY_CHECK_INTERVAL
      value: "30s"
    livenessProbe:
      httpGet:
        path: /health/dependencies
        port: 8080
      initialDelaySeconds: 60
      periodSeconds: 30
```

### 問題54
ログローテーションとアーカイブを設定してください：
- 日次ローテーション
- 圧縮設定
- 保持期間設定

**YAML例**:
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: log-rotation-pod
spec:
  containers:
  - name: app
    image: nginx:1.20
    volumeMounts:
    - name: log-volume
      mountPath: /var/log/nginx
  - name: logrotate
    image: alpine:latest
    command: ['sh', '-c', 'while true; do logrotate /etc/logrotate.conf; sleep 86400; done']
    volumeMounts:
    - name: log-volume
      mountPath: /var/log/nginx
    - name: logrotate-config
      mountPath: /etc/logrotate.conf
      subPath: logrotate.conf
  volumes:
  - name: log-volume
    emptyDir: {}
  - name: logrotate-config
    configMap:
      name: logrotate-config
```

### 問題55
セキュリティ監査ログを実装してください：
- アクセスログ
- 認証ログ
- 権限変更ログ

**YAML例**:
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: security-audit-pod
spec:
  containers:
  - name: app
    image: my-secure-app:latest
    env:
    - name: AUDIT_LOG_ENABLED
      value: "true"
    - name: AUDIT_LOG_LEVEL
      value: "INFO"
    volumeMounts:
    - name: audit-logs
      mountPath: /var/log/audit
  - name: audit-log-shipper
    image: filebeat:7.15.0
    volumeMounts:
    - name: audit-logs
      mountPath: /var/log/audit
    - name: filebeat-config
      mountPath: /usr/share/filebeat/filebeat.yml
      subPath: filebeat.yml
  volumes:
  - name: audit-logs
    emptyDir: {}
  - name: filebeat-config
    configMap:
      name: filebeat-config
```

### 問題56
エラー率とSLO監視を設定してください：
- エラー率計算
- SLO達成度測定
- アラート設定

**YAML例**:
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: slo-monitoring-pod
  annotations:
    prometheus.io/scrape: "true"
    prometheus.io/port: "8080"
spec:
  containers:
  - name: app
    image: my-app:latest
    ports:
    - containerPort: 8080
    env:
    - name: SLO_ERROR_RATE_THRESHOLD
      value: "0.01"  # 1%
    - name: SLO_LATENCY_THRESHOLD
      value: "100ms"
```

### 問題57
分散システムの可視性を向上させてください：
- サービスマップ
- 依存関係可視化
- パフォーマンストポロジー

**YAML例**:
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: service-mesh-observability-pod
spec:
  containers:
  - name: app
    image: my-app:latest
    env:
    - name: JAEGER_ENDPOINT
      value: "http://jaeger-collector:14268/api/traces"
    - name: SERVICE_NAME
      value: "user-service"
  - name: envoy-proxy
    image: envoyproxy/envoy:v1.18.0
    volumeMounts:
    - name: envoy-config
      mountPath: /etc/envoy
  volumes:
  - name: envoy-config
    configMap:
      name: envoy-config
```

### 問題58
アプリケーションインサイトを収集してください：
- ユーザー行動分析
- パフォーマンス分析
- ビジネスメトリクス

**YAML例**:
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: app-insights-pod
spec:
  containers:
  - name: app
    image: my-app:latest
    env:
    - name: ANALYTICS_ENABLED
      value: "true"
    - name: METRICS_COLLECTION_INTERVAL
      value: "60s"
  - name: analytics-collector
    image: my-analytics-collector:latest
    env:
    - name: ELASTICSEARCH_URL
      valueFrom:
        secretKeyRef:
          name: elasticsearch-config
          key: url
```

### 問題59
プロアクティブな問題検出を実装してください：
- 異常検出
- 予測分析
- 自動アラート

**YAML例**:
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: proactive-monitoring-pod
spec:
  containers:
  - name: app
    image: my-app:latest
  - name: anomaly-detector
    image: my-anomaly-detector:latest
    env:
    - name: DETECTION_SENSITIVITY
      value: "medium"
    - name: ALERT_THRESHOLD
      value: "0.95"
    - name: ML_MODEL_PATH
      value: "/models/anomaly-detection.pkl"
    volumeMounts:
    - name: ml-models
      mountPath: /models
  volumes:
  - name: ml-models
    configMap:
      name: ml-models
```

## 🎯 Pod Design (20%) - 問題60-79

### 問題60
Deploymentのローリングアップデート戦略を設定してください：
- maxUnavailable: 1
- maxSurge: 1
- 段階的ロールアウト

**YAML例**:
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: rolling-update-deployment
spec:
  replicas: 5
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxUnavailable: 1
      maxSurge: 1
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
```

### 問題61
Blue-Greenデプロイメントパターンを実装してください：
- Blue環境: 現在のバージョン
- Green環境: 新しいバージョン
- トラフィック切り替え

**YAML例**:
```yaml
# Blue Deployment
apiVersion: apps/v1
kind: Deployment
metadata:
  name: blue-deployment
  labels:
    version: blue
spec:
  replicas: 3
  selector:
    matchLabels:
      app: web
      version: blue
  template:
    metadata:
      labels:
        app: web
        version: blue
    spec:
      containers:
      - name: web
        image: nginx:1.19
---
# Green Deployment
apiVersion: apps/v1
kind: Deployment
metadata:
  name: green-deployment
  labels:
    version: green
spec:
  replicas: 3
  selector:
    matchLabels:
      app: web
      version: green
  template:
    metadata:
      labels:
        app: web
        version: green
    spec:
      containers:
      - name: web
        image: nginx:1.20
---
# Service (switch between blue and green)
apiVersion: v1
kind: Service
metadata:
  name: web-service
spec:
  selector:
    app: web
    version: blue  # Change to 'green' for switching
  ports:
  - port: 80
    targetPort: 80
```

### 問題62
Canaryデプロイメント戦略を実装してください：
- 小規模テスト: 10%
- 段階的拡大: 50%, 100%
- 自動ロールバック設定

**YAML例**:
```yaml
# Stable Deployment
apiVersion: apps/v1
kind: Deployment
metadata:
  name: stable-deployment
spec:
  replicas: 9
  selector:
    matchLabels:
      app: web
      version: stable
  template:
    metadata:
      labels:
        app: web
        version: stable
    spec:
      containers:
      - name: web
        image: nginx:1.19
---
# Canary Deployment (10%)
apiVersion: apps/v1
kind: Deployment
metadata:
  name: canary-deployment
spec:
  replicas: 1
  selector:
    matchLabels:
      app: web
      version: canary
  template:
    metadata:
      labels:
        app: web
        version: canary
    spec:
      containers:
      - name: web
        image: nginx:1.20
---
# Service (load balances between stable and canary)
apiVersion: v1
kind: Service
metadata:
  name: web-service
spec:
  selector:
    app: web
  ports:
  - port: 80
    targetPort: 80
```

### 問題63
HorizontalPodAutoscaler設定をしてください：
- CPU使用率: 70%
- 最小レプリカ: 2
- 最大レプリカ: 10
- メモリ使用率: 80%

**YAML例**:
```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: web-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: web-deployment
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
```

### 問題64
VerticalPodAutoscaler設定をしてください：
- 自動リソース調整
- リソース推奨値生成
- 更新ポリシー設定

**YAML例**:
```yaml
apiVersion: autoscaling.k8s.io/v1
kind: VerticalPodAutoscaler
metadata:
  name: web-vpa
spec:
  targetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: web-deployment
  updatePolicy:
    updateMode: "Auto"
  resourcePolicy:
    containerPolicies:
    - containerName: web
      minAllowed:
        cpu: 100m
        memory: 128Mi
      maxAllowed:
        cpu: 1
        memory: 1Gi
```

### 問題65
PodDisruptionBudgetを設定してください：
- 最小可用Pod数: 2
- 最大不可用Pod数: 1
- メンテナンス中の可用性確保

**YAML例**:
```yaml
apiVersion: policy/v1
kind: PodDisruptionBudget
metadata:
  name: web-pdb
spec:
  minAvailable: 2
  # または maxUnavailable: 1
  selector:
    matchLabels:
      app: web
```

### 問題66
リソース制限とQuotaを設定してください：
- Namespace レベルのQuota
- Pod レベルの制限
- LimitRange設定

**YAML例**:
```yaml
# ResourceQuota
apiVersion: v1
kind: ResourceQuota
metadata:
  name: compute-quota
  namespace: production
spec:
  hard:
    requests.cpu: "4"
    requests.memory: 8Gi
    limits.cpu: "8"
    limits.memory: 16Gi
    pods: "10"
---
# LimitRange
apiVersion: v1
kind: LimitRange
metadata:
  name: limit-range
  namespace: production
spec:
  limits:
  - default:
      cpu: 500m
      memory: 512Mi
    defaultRequest:
      cpu: 100m
      memory: 128Mi
    type: Container
```

### 問題67
ジョブとCronJobの包括的な設定をしてください：
- バッチ処理Job
- 定期実行CronJob
- 失敗時の再試行設定

**YAML例**:
```yaml
# Job
apiVersion: batch/v1
kind: Job
metadata:
  name: batch-job
spec:
  parallelism: 3
  completions: 6
  backoffLimit: 3
  ttlSecondsAfterFinished: 300
  template:
    spec:
      restartPolicy: Never
      containers:
      - name: worker
        image: busybox
        command: ['sh', '-c', 'echo "Processing batch job" && sleep 30']
---
# CronJob
apiVersion: batch/v1
kind: CronJob
metadata:
  name: scheduled-job
spec:
  schedule: "0 2 * * *"
  successfulJobsHistoryLimit: 3
  failedJobsHistoryLimit: 1
  concurrencyPolicy: Forbid
  jobTemplate:
    spec:
      template:
        spec:
          restartPolicy: OnFailure
          containers:
          - name: worker
            image: busybox
            command: ['sh', '-c', 'echo "Daily backup completed"']
```

### 問題68
StatefulSetの設定をしてください：
- 順序付きデプロイメント
- 永続ストレージ
- ヘッドレスサービス

**YAML例**:
```yaml
# Headless Service
apiVersion: v1
kind: Service
metadata:
  name: database-headless
spec:
  clusterIP: None
  selector:
    app: database
  ports:
  - port: 3306
---
# StatefulSet
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: database-sts
spec:
  serviceName: database-headless
  replicas: 3
  selector:
    matchLabels:
      app: database
  template:
    metadata:
      labels:
        app: database
    spec:
      containers:
      - name: mysql
        image: mysql:8.0
        env:
        - name: MYSQL_ROOT_PASSWORD
          valueFrom:
            secretKeyRef:
              name: mysql-secret
              key: password
        volumeMounts:
        - name: data
          mountPath: /var/lib/mysql
  volumeClaimTemplates:
  - metadata:
      name: data
    spec:
      accessModes: ["ReadWriteOnce"]
      resources:
        requests:
          storage: 10Gi
```

### 問題69
DaemonSetの高度な設定をしてください：
- ローリングアップデート
- ノードセレクション
- リソース制限

**YAML例**:
```yaml
apiVersion: apps/v1
kind: DaemonSet
metadata:
  name: log-collector-ds
spec:
  updateStrategy:
    type: RollingUpdate
    rollingUpdate:
      maxUnavailable: 1
  selector:
    matchLabels:
      app: log-collector
  template:
    metadata:
      labels:
        app: log-collector
    spec:
      nodeSelector:
        node-role.kubernetes.io/worker: ""
      tolerations:
      - key: node-role.kubernetes.io/master
        effect: NoSchedule
      containers:
      - name: log-collector
        image: fluentd:v1.14
        resources:
          requests:
            cpu: 100m
            memory: 128Mi
          limits:
            cpu: 200m
            memory: 256Mi
        volumeMounts:
        - name: varlog
          mountPath: /var/log
          readOnly: true
      volumes:
      - name: varlog
        hostPath:
          path: /var/log
```

### 問題70
Pod優先度とプリエンプション設定をしてください：
- 高優先度Pod
- 通常優先度Pod
- プリエンプション動作

**YAML例**:
```yaml
# PriorityClass
apiVersion: scheduling.k8s.io/v1
kind: PriorityClass
metadata:
  name: high-priority
value: 1000
globalDefault: false
description: "High priority class for critical applications"
---
# High Priority Pod
apiVersion: v1
kind: Pod
metadata:
  name: high-priority-pod
spec:
  priorityClassName: high-priority
  containers:
  - name: app
    image: nginx:1.20
---
# Normal Priority Pod
apiVersion: v1
kind: Pod
metadata:
  name: normal-priority-pod
spec:
  containers:
  - name: app
    image: nginx:1.20
```

### 問題71
複雑なスケジューリングを実装してください：
- 複数の制約条件
- アフィニティとアンチアフィニティ
- カスタムスケジューラー

**YAML例**:
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: complex-scheduling-pod
spec:
  schedulerName: my-custom-scheduler
  affinity:
    nodeAffinity:
      requiredDuringSchedulingIgnoredDuringExecution:
        nodeSelectorTerms:
        - matchExpressions:
          - key: zone
            operator: In
            values: ["us-west-1", "us-west-2"]
      preferredDuringSchedulingIgnoredDuringExecution:
      - weight: 100
        preference:
          matchExpressions:
          - key: disktype
            operator: In
            values: ["ssd"]
    podAffinity:
      requiredDuringSchedulingIgnoredDuringExecution:
      - labelSelector:
          matchExpressions:
          - key: app
            operator: In
            values: ["database"]
        topologyKey: "kubernetes.io/hostname"
    podAntiAffinity:
      preferredDuringSchedulingIgnoredDuringExecution:
      - weight: 100
        podAffinityTerm:
          labelSelector:
            matchExpressions:
            - key: app
              operator: In
              values: ["web"]
          topologyKey: "kubernetes.io/hostname"
  tolerations:
  - key: "special"
    operator: "Equal"
    value: "true"
    effect: "NoSchedule"
  containers:
  - name: app
    image: nginx:1.20
```

### 問題72
Pod lifecycleイベントとハンドラーを設定してください：
- postStart hook
- preStop hook
- 終了処理

**YAML例**:
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: lifecycle-pod
spec:
  containers:
  - name: app
    image: nginx:1.20
    lifecycle:
      postStart:
        exec:
          command:
          - /bin/sh
          - -c
          - echo "Container started" > /shared/startup.log
      preStop:
        exec:
          command:
          - /bin/sh
          - -c
          - echo "Container stopping" > /shared/shutdown.log && sleep 15
    volumeMounts:
    - name: shared
      mountPath: /shared
  volumes:
  - name: shared
    emptyDir: {}
  terminationGracePeriodSeconds: 30
```

### 問題73
Quality of Service (QoS) classesを理解して設定してください：
- Guaranteed class
- Burstable class
- BestEffort class

**YAML例**:
```yaml
# Guaranteed QoS
apiVersion: v1
kind: Pod
metadata:
  name: guaranteed-pod
spec:
  containers:
  - name: app
    image: nginx:1.20
    resources:
      requests:
        cpu: 200m
        memory: 256Mi
      limits:
        cpu: 200m
        memory: 256Mi
---
# Burstable QoS
apiVersion: v1
kind: Pod
metadata:
  name: burstable-pod
spec:
  containers:
  - name: app
    image: nginx:1.20
    resources:
      requests:
        cpu: 100m
        memory: 128Mi
      limits:
        cpu: 200m
        memory: 256Mi
---
# BestEffort QoS
apiVersion: v1
kind: Pod
metadata:
  name: besteffort-pod
spec:
  containers:
  - name: app
    image: nginx:1.20
```

### 問題74
Pod Topologyの理解と実装をしてください：
- Zone/Region awareness
- ラック分散
- 障害ドメイン設定

**YAML例**:
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: topology-aware-deployment
spec:
  replicas: 6
  selector:
    matchLabels:
      app: web
  template:
    metadata:
      labels:
        app: web
    spec:
      topologySpreadConstraints:
      - maxSkew: 1
        topologyKey: topology.kubernetes.io/zone
        whenUnsatisfiable: DoNotSchedule
        labelSelector:
          matchLabels:
            app: web
      - maxSkew: 1
        topologyKey: kubernetes.io/hostname
        whenUnsatisfiable: ScheduleAnyway
        labelSelector:
          matchLabels:
            app: web
      containers:
      - name: web
        image: nginx:1.20
```

### 問題75
RuntimeClassとContainer Runtime設定をしてください：
- 異なるランタイム選択
- セキュリティ要件
- パフォーマンス最適化

**YAML例**:
```yaml
# RuntimeClass
apiVersion: node.k8s.io/v1
kind: RuntimeClass
metadata:
  name: secure-runtime
handler: gvisor
---
# Pod using RuntimeClass
apiVersion: v1
kind: Pod
metadata:
  name: secure-pod
spec:
  runtimeClassName: secure-runtime
  containers:
  - name: app
    image: nginx:1.20
```

### 問題76
Pod Securityの高度な設定をしてください：
- Pod Security Standards
- Security Contexts
- Capability管理

**YAML例**:
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: security-hardened-pod
spec:
  securityContext:
    runAsNonRoot: true
    runAsUser: 1000
    runAsGroup: 3000
    fsGroup: 2000
    seccompProfile:
      type: RuntimeDefault
  containers:
  - name: app
    image: nginx:1.20
    securityContext:
      allowPrivilegeEscalation: false
      readOnlyRootFilesystem: true
      capabilities:
        drop:
        - ALL
        add:
        - NET_BIND_SERVICE
    volumeMounts:
    - name: tmp
      mountPath: /tmp
    - name: cache
      mountPath: /var/cache/nginx
  volumes:
  - name: tmp
    emptyDir: {}
  - name: cache
    emptyDir: {}
```

### 問題77
Pod Networkingの詳細設定をしてください：
- Network Policies
- DNS設定
- Service Mesh統合

**YAML例**:
```yaml
# Network Policy
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: web-network-policy
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
          app: frontend
    ports:
    - protocol: TCP
      port: 80
  egress:
  - to:
    - podSelector:
        matchLabels:
          app: database
    ports:
    - protocol: TCP
      port: 5432
---
# Pod with custom DNS
apiVersion: v1
kind: Pod
metadata:
  name: custom-dns-pod
spec:
  dnsPolicy: "None"
  dnsConfig:
    nameservers:
    - 8.8.8.8
    searches:
    - company.local
    options:
    - name: ndots
      value: "2"
  containers:
  - name: app
    image: nginx:1.20
```

### 問題78
Pod Storageの高度な設定をしてください：
- 複数ボリューム
- ストレージクラス
- 動的プロビジョニング

**YAML例**:
```yaml
# StorageClass
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: fast-ssd
provisioner: kubernetes.io/aws-ebs
parameters:
  type: gp2
  iopsPerGB: "10"
  encrypted: "true"
volumeBindingMode: WaitForFirstConsumer
---
# Pod with multiple storage types
apiVersion: v1
kind: Pod
metadata:
  name: multi-storage-pod
spec:
  containers:
  - name: app
    image: nginx:1.20
    volumeMounts:
    - name: config
      mountPath: /etc/nginx/conf.d
    - name: data
      mountPath: /var/www/html
    - name: logs
      mountPath: /var/log/nginx
    - name: temp
      mountPath: /tmp
  volumes:
  - name: config
    configMap:
      name: nginx-config
  - name: data
    persistentVolumeClaim:
      claimName: web-data-pvc
  - name: logs
    hostPath:
      path: /var/log/nginx
      type: DirectoryOrCreate
  - name: temp
    emptyDir:
      medium: Memory
      sizeLimit: 1Gi
```

### 問題79
Pod Troubleshootingとデバッグ設定をしてください：
- デバッグコンテナ
- ログ収集
- 問題診断

**YAML例**:
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: debug-pod
spec:
  containers:
  - name: app
    image: nginx:1.20
    # Enable debug mode
    env:
    - name: DEBUG
      value: "true"
    - name: LOG_LEVEL
      value: "debug"
    # Resource constraints for debugging
    resources:
      requests:
        cpu: 100m
        memory: 128Mi
    # Additional debugging tools
    volumeMounts:
    - name: debug-tools
      mountPath: /debug
  # Debug sidecar container
  - name: debug-sidecar
    image: nicolaka/netshoot
    command: ['sleep', '3600']
    securityContext:
      capabilities:
        add:
        - NET_ADMIN
  volumes:
  - name: debug-tools
    emptyDir: {}
  # Enable debugging features
  shareProcessNamespace: true
```

## 🎯 Services & Networking (13%) - 問題80-92

### 問題80
Service types の包括的な実装をしてください：
- ClusterIP Service
- NodePort Service  
- LoadBalancer Service
- ExternalName Service

**YAML例**:
```yaml
# ClusterIP Service
apiVersion: v1
kind: Service
metadata:
  name: clusterip-service
spec:
  type: ClusterIP
  selector:
    app: web
  ports:
  - port: 80
    targetPort: 8080
---
# NodePort Service
apiVersion: v1
kind: Service
metadata:
  name: nodeport-service
spec:
  type: NodePort
  selector:
    app: web
  ports:
  - port: 80
    targetPort: 8080
    nodePort: 30080
---
# LoadBalancer Service
apiVersion: v1
kind: Service
metadata:
  name: loadbalancer-service
spec:
  type: LoadBalancer
  selector:
    app: web
  ports:
  - port: 80
    targetPort: 8080
---
# ExternalName Service
apiVersion: v1
kind: Service
metadata:
  name: external-service
spec:
  type: ExternalName
  externalName: api.example.com
```

### 問題81
Ingressの高度な設定をしてください：
- パスベースルーティング
- ホストベースルーティング
- TLS設定
- アノテーション活用

**YAML例**:
```yaml
# TLS Secret
apiVersion: v1
kind: Secret
metadata:
  name: tls-secret
type: kubernetes.io/tls
data:
  tls.crt: # base64 encoded certificate
  tls.key: # base64 encoded private key
---
# Ingress
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: complex-ingress
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /
    nginx.ingress.kubernetes.io/rate-limit: "100"
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
spec:
  tls:
  - hosts:
    - app.example.com
    - api.example.com
    secretName: tls-secret
  rules:
  - host: app.example.com
    http:
      paths:
      - path: /web
        pathType: Prefix
        backend:
          service:
            name: web-service
            port:
              number: 80
      - path: /api
        pathType: Prefix
        backend:
          service:
            name: api-service
            port:
              number: 8080
  - host: api.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: api-service
            port:
              number: 8080
```

### 問題82
Network Policies の詳細設定をしてください：
- Ingress/Egress制御
- 複数ルール設定
- CIDR指定

**YAML例**:
```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: comprehensive-network-policy
  namespace: production
spec:
  podSelector:
    matchLabels:
      app: web
  policyTypes:
  - Ingress
  - Egress
  ingress:
  # Allow from frontend pods
  - from:
    - podSelector:
        matchLabels:
          app: frontend
    ports:
    - protocol: TCP
      port: 80
  # Allow from specific namespace
  - from:
    - namespaceSelector:
        matchLabels:
          name: monitoring
    ports:
    - protocol: TCP
      port: 9090
  # Allow from specific IP range
  - from:
    - ipBlock:
        cidr: 10.0.0.0/8
        except:
        - 10.0.1.0/24
    ports:
    - protocol: TCP
      port: 443
  egress:
  # Allow to database
  - to:
    - podSelector:
        matchLabels:
          app: database
    ports:
    - protocol: TCP
      port: 5432
  # Allow to external services
  - to: []
    ports:
    - protocol: TCP
      port: 443
    - protocol: UDP
      port: 53
```

### 問題83
Service Discovery の実装をしてください：
- DNS based discovery
- Environment variables
- Service endpoints

**YAML例**:
```yaml
# Backend Service
apiVersion: v1
kind: Service
metadata:
  name: backend-service
  namespace: production
spec:
  selector:
    app: backend
  ports:
  - port: 8080
    targetPort: 8080
---
# Client Pod using service discovery
apiVersion: v1
kind: Pod
metadata:
  name: client-pod
  namespace: production
spec:
  containers:
  - name: client
    image: busybox
    command: ['sh', '-c']
    args:
    - |
      # DNS-based discovery
      echo "Testing DNS discovery..."
      nslookup backend-service
      nslookup backend-service.production.svc.cluster.local
      
      # Environment variable discovery
      echo "Environment variables:"
      env | grep BACKEND_SERVICE
      
      # HTTP test
      wget -qO- http://backend-service:8080/health
      
      sleep 3600
```

### 問題84
External Services の統合をしてください：
- External endpoints
- Service without selector
- External DNS integration

**YAML例**:
```yaml
# External Service (without selector)
apiVersion: v1
kind: Service
metadata:
  name: external-database
spec:
  ports:
  - port: 5432
    targetPort: 5432
---
# External Endpoints
apiVersion: v1
kind: Endpoints
metadata:
  name: external-database
subsets:
- addresses:
  - ip: 192.168.1.100
  - ip: 192.168.1.101
  ports:
  - port: 5432
---
# Pod using external service
apiVersion: v1
kind: Pod
metadata:
  name: app-pod
spec:
  containers:
  - name: app
    image: my-app:latest
    env:
    - name: DATABASE_URL
      value: "postgresql://external-database:5432/mydb"
```

### 問題85
Headless Services の実装をしてください：
- DNS records for each pod
- StatefulSet integration
- Direct pod communication

**YAML例**:
```yaml
# Headless Service
apiVersion: v1
kind: Service
metadata:
  name: headless-service
spec:
  clusterIP: None
  selector:
    app: database
  ports:
  - port: 3306
    targetPort: 3306
---
# StatefulSet using headless service
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: database-sts
spec:
  serviceName: headless-service
  replicas: 3
  selector:
    matchLabels:
      app: database
  template:
    metadata:
      labels:
        app: database
    spec:
      containers:
      - name: mysql
        image: mysql:8.0
        env:
        - name: MYSQL_ROOT_PASSWORD
          value: password
        - name: POD_NAME
          valueFrom:
            fieldRef:
              fieldPath: metadata.name
---
# Client testing individual pod access
apiVersion: v1
kind: Pod
metadata:
  name: database-client
spec:
  containers:
  - name: client
    image: mysql:8.0
    command: ['sh', '-c']
    args:
    - |
      # Test individual pod access
      echo "Testing direct pod access..."
      mysql -h database-sts-0.headless-service -u root -ppassword -e "SELECT 1"
      mysql -h database-sts-1.headless-service -u root -ppassword -e "SELECT 1"
      mysql -h database-sts-2.headless-service -u root -ppassword -e "SELECT 1"
      sleep 3600
```

### 问题86
Load Balancing strategies の実装をしてください：
- Session affinity
- Custom load balancing
- Health check integration

**YAML例**:
```yaml
# Service with session affinity
apiVersion: v1
kind: Service
metadata:
  name: session-affinity-service
spec:
  selector:
    app: web
  ports:
  - port: 80
    targetPort: 8080
  sessionAffinity: ClientIP
  sessionAffinityConfig:
    clientIP:
      timeoutSeconds: 3600
---
# Service with custom annotations for load balancing
apiVersion: v1
kind: Service
metadata:
  name: custom-lb-service
  annotations:
    service.beta.kubernetes.io/aws-load-balancer-type: "nlb"
    service.beta.kubernetes.io/aws-load-balancer-backend-protocol: "tcp"
    service.beta.kubernetes.io/aws-load-balancer-healthcheck-interval: "10"
spec:
  type: LoadBalancer
  selector:
    app: web
  ports:
  - port: 80
    targetPort: 8080
```

### 問題87
DNS Customization を実装してください：
- Custom DNS policy
- DNS configuration
- Search domains

**YAML例**:
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: custom-dns-pod
spec:
  dnsPolicy: "None"
  dnsConfig:
    nameservers:
    - 8.8.8.8
    - 8.8.4.4
    searches:
    - company.local
    - cluster.local
    options:
    - name: ndots
      value: "2"
    - name: edns0
  containers:
  - name: app
    image: nginx:1.20
    command: ['sh', '-c']
    args:
    - |
      echo "Testing custom DNS configuration..."
      cat /etc/resolv.conf
      nslookup google.com
      nslookup kubernetes.default.svc.cluster.local
      sleep 3600
```

### 问题88
Service Mesh Integration を実装してください：
- Istio integration
- Traffic policies
- Security policies

**YAML例**:
```yaml
# Enable Istio injection
apiVersion: v1
kind: Namespace
metadata:
  name: service-mesh
  labels:
    istio-injection: enabled
---
# Virtual Service
apiVersion: networking.istio.io/v1beta1
kind: VirtualService
metadata:
  name: web-virtual-service
  namespace: service-mesh
spec:
  hosts:
  - web-service
  http:
  - match:
    - headers:
        user-type:
          exact: premium
    route:
    - destination:
        host: web-service
        subset: v2
      weight: 100
  - route:
    - destination:
        host: web-service
        subset: v1
      weight: 90
    - destination:
        host: web-service
        subset: v2
      weight: 10
---
# Destination Rule
apiVersion: networking.istio.io/v1beta1
kind: DestinationRule
metadata:
  name: web-destination-rule
  namespace: service-mesh
spec:
  host: web-service
  subsets:
  - name: v1
    labels:
      version: v1
  - name: v2
    labels:
      version: v2
```

### 問題89
Network Troubleshooting を実装してください：
- Connectivity testing
- DNS resolution testing
- Network policy testing

**YAML例**:
```yaml
# Network troubleshooting pod
apiVersion: v1
kind: Pod
metadata:
  name: network-debug-pod
spec:
  containers:
  - name: debug
    image: nicolaka/netshoot
    command: ['sleep', '3600']
    securityContext:
      capabilities:
        add:
        - NET_ADMIN
---
# Test target pods
apiVersion: v1
kind: Pod
metadata:
  name: test-target-pod
  labels:
    app: test-target
spec:
  containers:
  - name: target
    image: nginx:1.20
    ports:
    - containerPort: 80
---
# Test service
apiVersion: v1
kind: Service
metadata:
  name: test-service
spec:
  selector:
    app: test-target
  ports:
  - port: 80
    targetPort: 80
```

### 問题90
Multi-cluster Networking を実装してください：
- Cross-cluster communication
- Service mirroring
- Traffic routing

**YAML例**:
```yaml
# ServiceExport (for multi-cluster)
apiVersion: networking.x-k8s.io/v1alpha1
kind: ServiceExport
metadata:
  name: web-service
  namespace: production
---
# Cross-cluster service
apiVersion: v1
kind: Service
metadata:
  name: cross-cluster-service
  annotations:
    networking.istio.io/exportTo: "*"
spec:
  selector:
    app: web
  ports:
  - port: 80
    targetPort: 8080
---
# Gateway for multi-cluster
apiVersion: networking.istio.io/v1beta1
kind: Gateway
metadata:
  name: cross-cluster-gateway
spec:
  selector:
    istio: eastwestgateway
  servers:
  - port:
      number: 15443
      name: tls
      protocol: TLS
    tls:
      mode: ISTIO_MUTUAL
    hosts:
    - "*.local"
```

### 問題91
Service Performance Optimization を実装してください：
- Connection pooling
- Circuit breakers
- Retry policies

**YAML例**:
```yaml
# Destination Rule with traffic policies
apiVersion: networking.istio.io/v1beta1
kind: DestinationRule
metadata:
  name: performance-optimized-service
spec:
  host: backend-service
  trafficPolicy:
    connectionPool:
      tcp:
        maxConnections: 100
        connectTimeout: 30s
      http:
        http1MaxPendingRequests: 50
        http2MaxRequests: 100
        maxRequestsPerConnection: 10
        maxRetries: 3
        consecutiveGatewayErrors: 5
        interval: 30s
        baseEjectionTime: 30s
    circuitBreaker:
      consecutiveErrors: 5
      interval: 30s
      baseEjectionTime: 30s
      maxEjectionPercent: 50
    retryPolicy:
      attempts: 3
      perTryTimeout: 2s
      retryOn: 5xx,reset,connect-failure,refused-stream
```

### 問題92
Service Security を実装してください：
- mTLS configuration
- Authorization policies
- Security scanning

**YAML例**:
```yaml
# PeerAuthentication
apiVersion: security.istio.io/v1beta1
kind: PeerAuthentication
metadata:
  name: secure-communication
  namespace: production
spec:
  selector:
    matchLabels:
      app: web
  mtls:
    mode: STRICT
---
# AuthorizationPolicy
apiVersion: security.istio.io/v1beta1
kind: AuthorizationPolicy
metadata:
  name: web-authorization
  namespace: production
spec:
  selector:
    matchLabels:
      app: web
  rules:
  - from:
    - source:
        principals: ["cluster.local/ns/frontend/sa/frontend-sa"]
  - to:
    - operation:
        methods: ["GET", "POST"]
        paths: ["/api/*"]
  - when:
    - key: request.headers[user-role]
      values: ["admin", "user"]
---
# Security scanning sidecar
apiVersion: v1
kind: Pod
metadata:
  name: secure-web-pod
spec:
  containers:
  - name: web
    image: nginx:1.20
    ports:
    - containerPort: 80
  - name: security-scanner
    image: aquasec/trivy:latest
    command: ['sh', '-c']
    args:
    - |
      while true; do
        trivy image --exit-code 1 nginx:1.20
        sleep 3600
      done
```

## 🎯 State Persistence (8%) - 問題93-100

### 問題93
PersistentVolume と PersistentVolumeClaim の包括的な設定をしてください：
- 複数のストレージタイプ
- アクセスモード設定
- 容量管理

**YAML例**:
```yaml
# PersistentVolume
apiVersion: v1
kind: PersistentVolume
metadata:
  name: local-pv
spec:
  capacity:
    storage: 10Gi
  accessModes:
  - ReadWriteOnce
  persistentVolumeReclaimPolicy: Retain
  storageClassName: local-storage
  local:
    path: /mnt/data
  nodeAffinity:
    required:
      nodeSelectorTerms:
      - matchExpressions:
        - key: kubernetes.io/hostname
          operator: In
          values:
          - worker-node-1
---
# PersistentVolumeClaim
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: app-data-pvc
spec:
  accessModes:
  - ReadWriteOnce
  storageClassName: local-storage
  resources:
    requests:
      storage: 5Gi
---
# Pod using PVC
apiVersion: v1
kind: Pod
metadata:
  name: persistent-app-pod
spec:
  containers:
  - name: app
    image: nginx:1.20
    volumeMounts:
    - name: app-data
      mountPath: /usr/share/nginx/html
  volumes:
  - name: app-data
    persistentVolumeClaim:
      claimName: app-data-pvc
```

### 問題94
StorageClass の詳細設定をしてください：
- 動的プロビジョニング
- カスタムパラメータ
- 保持ポリシー

**YAML例**:
```yaml
# Fast SSD StorageClass
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: fast-ssd
provisioner: kubernetes.io/aws-ebs
parameters:
  type: gp3
  iops: "3000"
  throughput: "125"
  encrypted: "true"
  fsType: ext4
volumeBindingMode: WaitForFirstConsumer
allowVolumeExpansion: true
reclaimPolicy: Delete
---
# Network storage StorageClass
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: network-storage
provisioner: nfs.csi.k8s.io
parameters:
  server: nfs-server.example.com
  share: /exports
mountOptions:
- hard
- intr
- nfsvers=4.1
volumeBindingMode: Immediate
allowVolumeExpansion: true
reclaimPolicy: Retain
```

### 問題95
Volume Snapshots の実装をしてください：
- スナップショット作成
- 復元処理
- スケジューリング

**YAML例**:
```yaml
# VolumeSnapshotClass
apiVersion: snapshot.storage.k8s.io/v1
kind: VolumeSnapshotClass
metadata:
  name: csi-snapclass
driver: ebs.csi.aws.com
deletionPolicy: Delete
---
# VolumeSnapshot
apiVersion: snapshot.storage.k8s.io/v1
kind: VolumeSnapshot
metadata:
  name: app-data-snapshot
spec:
  volumeSnapshotClassName: csi-snapclass
  source:
    persistentVolumeClaimName: app-data-pvc
---
# Restore from snapshot
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: restored-pvc
spec:
  accessModes:
  - ReadWriteOnce
  storageClassName: fast-ssd
  resources:
    requests:
      storage: 10Gi
  dataSource:
    name: app-data-snapshot
    kind: VolumeSnapshot
    apiGroup: snapshot.storage.k8s.io
```

### 問題96
Data backup strategies を実装してください：
- 自動バックアップ
- データ同期
- 災害復旧

**YAML例**:
```yaml
# Backup CronJob
apiVersion: batch/v1
kind: CronJob
metadata:
  name: data-backup
spec:
  schedule: "0 2 * * *"
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: backup
            image: postgres:13
            command: ['sh', '-c']
            args:
            - |
              pg_dump -h database-service -U postgres -d myapp > /backup/backup-$(date +%Y%m%d).sql
              # Upload to S3 or other storage
              aws s3 cp /backup/backup-$(date +%Y%m%d).sql s3://my-backup-bucket/
            env:
            - name: PGPASSWORD
              valueFrom:
                secretKeyRef:
                  name: db-secret
                  key: password
            - name: AWS_ACCESS_KEY_ID
              valueFrom:
                secretKeyRef:
                  name: aws-secret
                  key: access-key
            - name: AWS_SECRET_ACCESS_KEY
              valueFrom:
                secretKeyRef:
                  name: aws-secret
                  key: secret-key
            volumeMounts:
            - name: backup-storage
              mountPath: /backup
          volumes:
          - name: backup-storage
            emptyDir: {}
          restartPolicy: OnFailure
```

### 問題97
Stateful application patterns を実装してください：
- データベースクラスタ
- 順序付きデプロイメント
- データ整合性

**YAML例**:
```yaml
# StatefulSet for database cluster
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: postgres-cluster
spec:
  serviceName: postgres-headless
  replicas: 3
  selector:
    matchLabels:
      app: postgres
  template:
    metadata:
      labels:
        app: postgres
    spec:
      initContainers:
      - name: init-postgres
        image: postgres:13
        command: ['sh', '-c']
        args:
        - |
          if [ "$HOSTNAME" = "postgres-cluster-0" ]; then
            echo "Initializing primary database..."
            initdb -D /var/lib/postgresql/data
          else
            echo "Waiting for primary to be ready..."
            until pg_isready -h postgres-cluster-0.postgres-headless; do sleep 1; done
            echo "Creating replica..."
            pg_basebackup -h postgres-cluster-0.postgres-headless -D /var/lib/postgresql/data -U postgres -v -P -W
          fi
        env:
        - name: PGUSER
          value: postgres
        - name: PGPASSWORD
          valueFrom:
            secretKeyRef:
              name: postgres-secret
              key: password
        volumeMounts:
        - name: postgres-data
          mountPath: /var/lib/postgresql/data
      containers:
      - name: postgres
        image: postgres:13
        env:
        - name: POSTGRES_PASSWORD
          valueFrom:
            secretKeyRef:
              name: postgres-secret
              key: password
        - name: POSTGRES_USER
          value: postgres
        ports:
        - containerPort: 5432
        volumeMounts:
        - name: postgres-data
          mountPath: /var/lib/postgresql/data
        livenessProbe:
          exec:
            command:
            - pg_isready
            - -U
            - postgres
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          exec:
            command:
            - pg_isready
            - -U
            - postgres
          initialDelaySeconds: 5
          periodSeconds: 5
  volumeClaimTemplates:
  - metadata:
      name: postgres-data
    spec:
      accessModes: ["ReadWriteOnce"]
      storageClassName: fast-ssd
      resources:
        requests:
          storage: 20Gi
```

### 問題98
Data migration strategies を実装してください：
- ゼロダウンタイム移行
- データ変換
- 検証プロセス

**YAML例**:
```yaml
# Data migration job
apiVersion: batch/v1
kind: Job
metadata:
  name: data-migration
spec:
  parallelism: 3
  completions: 3
  template:
    spec:
      initContainers:
      - name: pre-migration-check
        image: postgres:13
        command: ['sh', '-c']
        args:
        - |
          echo "Checking source database connectivity..."
          pg_isready -h old-database-service -p 5432
          echo "Checking target database connectivity..."
          pg_isready -h new-database-service -p 5432
          echo "Pre-migration checks passed"
      containers:
      - name: migrate
        image: migrate/migrate
        command: ['sh', '-c']
        args:
        - |
          # Run migrations
          migrate -path /migrations -database $TARGET_DB_URL up
          
          # Data migration with verification
          psql $SOURCE_DB_URL -c "\copy (SELECT * FROM users WHERE id BETWEEN $START_ID AND $END_ID) TO STDOUT" | \
          psql $TARGET_DB_URL -c "\copy users FROM STDIN"
          
          # Verify data integrity
          SOURCE_COUNT=$(psql $SOURCE_DB_URL -t -c "SELECT COUNT(*) FROM users WHERE id BETWEEN $START_ID AND $END_ID")
          TARGET_COUNT=$(psql $TARGET_DB_URL -t -c "SELECT COUNT(*) FROM users WHERE id BETWEEN $START_ID AND $END_ID")
          
          if [ "$SOURCE_COUNT" != "$TARGET_COUNT" ]; then
            echo "Data migration failed: count mismatch"
            exit 1
          fi
          
          echo "Migration completed successfully"
        env:
        - name: SOURCE_DB_URL
          valueFrom:
            secretKeyRef:
              name: migration-secret
              key: source-db-url
        - name: TARGET_DB_URL
          valueFrom:
            secretKeyRef:
              name: migration-secret
              key: target-db-url
        - name: START_ID
          valueFrom:
            fieldRef:
              fieldPath: metadata.annotations['batch.kubernetes.io/job-completion-index']
        - name: END_ID
          value: "1000"  # Will be calculated based on job index
      restartPolicy: Never
  backoffLimit: 3
```

### 問題99
Storage monitoring and alerting を実装してください：
- 容量監視
- パフォーマンス監視
- 自動スケーリング

**YAML例**:
```yaml
# Storage monitoring pod
apiVersion: v1
kind: Pod
metadata:
  name: storage-monitor
  annotations:
    prometheus.io/scrape: "true"
    prometheus.io/port: "8080"
spec:
  containers:
  - name: storage-monitor
    image: my-storage-monitor:latest
    ports:
    - containerPort: 8080
      name: metrics
    env:
    - name: MONITOR_INTERVAL
      value: "60s"
    - name: ALERT_THRESHOLD_PERCENT
      value: "85"
    volumeMounts:
    - name: storage-to-monitor
      mountPath: /monitored-storage
    command: ['sh', '-c']
    args:
    - |
      while true; do
        # Check storage usage
        USAGE=$(df /monitored-storage | awk 'NR==2 {print $5}' | sed 's/%//')
        
        # Export metrics for Prometheus
        echo "storage_usage_percent $USAGE" > /tmp/metrics.txt
        
        # Alert if usage is high
        if [ "$USAGE" -gt "$ALERT_THRESHOLD_PERCENT" ]; then
          echo "ALERT: Storage usage is ${USAGE}%"
          # Send alert to webhook
          curl -X POST -H 'Content-Type: application/json' \
            -d '{"text":"Storage usage alert: '${USAGE}'% on '$(hostname)'"}' \
            $WEBHOOK_URL
        fi
        
        sleep $MONITOR_INTERVAL
      done
  volumes:
  - name: storage-to-monitor
    persistentVolumeClaim:
      claimName: app-data-pvc
```

### 問題100
Data lifecycle management を実装してください：
- データアーカイブ
- 自動削除
- 保持ポリシー

**YAML例**:
```yaml
# Data lifecycle management CronJob
apiVersion: batch/v1
kind: CronJob
metadata:
  name: data-lifecycle-manager
spec:
  schedule: "0 3 * * *"  # Daily at 3 AM
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: lifecycle-manager
            image: postgres:13
            command: ['sh', '-c']
            args:
            - |
              echo "Starting data lifecycle management..."
              
              # Archive old data (older than 1 year)
              echo "Archiving old data..."
              psql $DATABASE_URL -c "
                INSERT INTO archived_logs 
                SELECT * FROM logs 
                WHERE created_at < NOW() - INTERVAL '1 year';
              "
              
              # Delete archived data from main table
              echo "Removing archived data from main table..."
              DELETED_COUNT=$(psql $DATABASE_URL -t -c "
                DELETE FROM logs 
                WHERE created_at < NOW() - INTERVAL '1 year';
                SELECT ROW_COUNT();
              ")
              
              echo "Archived and deleted $DELETED_COUNT rows"
              
              # Vacuum and analyze tables
              echo "Optimizing database..."
              psql $DATABASE_URL -c "VACUUM ANALYZE logs;"
              psql $DATABASE_URL -c "VACUUM ANALYZE archived_logs;"
              
              # Delete very old archives (older than 7 years)
              echo "Purging very old archives..."
              PURGED_COUNT=$(psql $DATABASE_URL -t -c "
                DELETE FROM archived_logs 
                WHERE created_at < NOW() - INTERVAL '7 years';
                SELECT ROW_COUNT();
              ")
              
              echo "Purged $PURGED_COUNT very old records"
              
              # Generate report
              CURRENT_LOGS=$(psql $DATABASE_URL -t -c "SELECT COUNT(*) FROM logs;")
              ARCHIVED_LOGS=$(psql $DATABASE_URL -t -c "SELECT COUNT(*) FROM archived_logs;")
              
              echo "Data lifecycle report:"
              echo "Current logs: $CURRENT_LOGS"
              echo "Archived logs: $ARCHIVED_LOGS"
              echo "Data lifecycle management completed"
            env:
            - name: DATABASE_URL
              valueFrom:
                secretKeyRef:
                  name: db-secret
                  key: database-url
          restartPolicy: OnFailure
      successfulJobsHistoryLimit: 3
      failedJobsHistoryLimit: 1

## 📊 実技試験のコツ

### 時間管理
- **120分で100問**: 問題あたり1.2分
- **簡単な問題から**: 確実に点数を取る
- **複雑な問題**: 後回しにして時間配分を調整

### kubectl コマンド効率化
```bash
# エイリアス設定
alias k=kubectl
export do="--dry-run=client -o yaml"
export now="--force --grace-period 0"

# 便利なエイリアス
alias kgp="kubectl get pods"
alias kgs="kubectl get services"
alias kgd="kubectl get deployments"
alias kdp="kubectl describe pod"
alias kds="kubectl describe service"
```

### ショートカット
```bash
# クイック作成
k run nginx --image=nginx $do > pod.yaml
k create deploy nginx --image=nginx $do > deploy.yaml
k expose pod nginx --port=80 $do > service.yaml

# クイック編集
k edit pod nginx
k patch pod nginx -p '{"spec":{"containers":[{"name":"nginx","image":"nginx:1.21"}]}}'

# ログとデバッグ
k logs -f nginx
k exec -it nginx -- /bin/bash
k port-forward nginx 8080:80
```

---

**重要**: CKADは実技試験です。知識だけでなく、制限時間内での実装スピードが合格の鍵となります。継続的な実践練習が必要です。