# Lab 1: Pod・Container基礎とアプリケーション開発

## 🎯 学習目標

このラボでは、CKAD試験で最も重要なPodとコンテナの基礎概念を実践的に学習します。単純なコンテナ実行から始まり、複雑なマルチコンテナアプリケーションまで段階的に習得します。

**習得スキル**:
- Pod設計とライフサイクル管理
- マルチコンテナPodパターン
- Init Containersの活用
- ヘルスチェックとプローブ設定
- リソース管理とセキュリティ設定

**所要時間**: 4-6時間  
**推定コスト**: $8-15

## 📋 シナリオ

**企業**: オンライン学習プラットフォーム  
**開発チーム**: フロントエンド・バックエンド・DevOps  
**プロジェクト**: マイクロサービス型ウェブアプリケーション開発  
**要件**: 
- 高可用性フロントエンド
- API サーバー
- データベース接続
- ログ収集・監視システム

## Phase 1: 基本的なPod作成と管理

### 1.1 単一コンテナPodの作成

```yaml
# ファイル: simple-pod.yaml
apiVersion: v1
kind: Pod
metadata:
  name: web-app
  labels:
    app: web-app
    version: v1.0
    environment: development
spec:
  containers:
  - name: nginx
    image: nginx:1.20
    ports:
    - containerPort: 80
      name: http
    resources:
      requests:
        memory: "64Mi"
        cpu: "100m"
      limits:
        memory: "128Mi"
        cpu: "200m"
    env:
    - name: ENVIRONMENT
      value: "development"
    - name: APP_VERSION
      value: "1.0"
```

```bash
#!/bin/bash
# スクリプト: basic-pod-operations.sh

echo "🚀 基本的なPod操作の実践..."

# Pod作成
echo "📦 Pod作成中..."
kubectl apply -f simple-pod.yaml

# Pod起動待機
echo "⏳ Pod起動待機中..."
kubectl wait --for=condition=Ready pod/web-app --timeout=300s

# Pod状態確認
echo "📊 Pod基本情報:"
kubectl get pod web-app -o wide

echo ""
echo "🔍 Pod詳細情報:"
kubectl describe pod web-app

echo ""
echo "🏷️ Podラベル確認:"
kubectl get pod web-app --show-labels

# Pod内での作業
echo ""
echo "💻 Pod内コマンド実行テスト:"
kubectl exec web-app -- nginx -v
kubectl exec web-app -- whoami
kubectl exec web-app -- cat /etc/nginx/nginx.conf | head -10

# ポートフォワーディングテスト
echo ""
echo "🌐 ポートフォワーディングテスト:"
kubectl port-forward pod/web-app 8080:80 &
PF_PID=$!
sleep 5

echo "HTTPリクエストテスト:"
curl -s http://localhost:8080 | head -5
echo ""

# クリーンアップ
kill $PF_PID 2>/dev/null

echo "✅ 基本Pod操作完了!"
```

### 1.2 環境変数とConfigMapの活用

```yaml
# ファイル: app-config.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: app-config
  labels:
    app: web-app
data:
  # 単純なキー・バリュー
  database_host: "db.example.com"
  database_port: "5432"
  log_level: "info"
  
  # 設定ファイル
  app.properties: |
    server.port=8080
    server.servlet.context-path=/api
    spring.datasource.url=jdbc:postgresql://db.example.com:5432/webapp
    spring.datasource.username=${DB_USERNAME}
    spring.datasource.password=${DB_PASSWORD}
    logging.level.root=INFO
    logging.level.com.example=DEBUG
  
  nginx.conf: |
    server {
        listen 80;
        server_name localhost;
        
        location / {
            root /usr/share/nginx/html;
            index index.html;
        }
        
        location /api/ {
            proxy_pass http://backend:8080/;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
        }
        
        location /health {
            access_log off;
            return 200 "healthy\n";
            add_header Content-Type text/plain;
        }
    }
---
apiVersion: v1
kind: Secret
metadata:
  name: app-secrets
  labels:
    app: web-app
type: Opaque
data:
  DB_USERNAME: YWRtaW4=        # admin
  DB_PASSWORD: cGFzc3dvcmQxMjM= # password123
  API_KEY: YWJjZGVmZ2hpams=     # abcdefghijk
```

```yaml
# ファイル: configured-pod.yaml
apiVersion: v1
kind: Pod
metadata:
  name: configured-app
  labels:
    app: configured-app
spec:
  containers:
  - name: web-server
    image: nginx:1.20
    ports:
    - containerPort: 80
    env:
    # ConfigMapから環境変数設定
    - name: DATABASE_HOST
      valueFrom:
        configMapKeyRef:
          name: app-config
          key: database_host
    - name: DATABASE_PORT
      valueFrom:
        configMapKeyRef:
          name: app-config
          key: database_port
    # Secretから環境変数設定
    - name: DB_USERNAME
      valueFrom:
        secretKeyRef:
          name: app-secrets
          key: DB_USERNAME
    - name: DB_PASSWORD
      valueFrom:
        secretKeyRef:
          name: app-secrets
          key: DB_PASSWORD
    volumeMounts:
    # ConfigMapをファイルとしてマウント
    - name: config-volume
      mountPath: /etc/nginx/conf.d/default.conf
      subPath: nginx.conf
    - name: app-config-volume
      mountPath: /etc/app-config
    # Secretをファイルとしてマウント
    - name: secret-volume
      mountPath: /etc/secrets
      readOnly: true
    resources:
      requests:
        memory: "128Mi"
        cpu: "100m"
      limits:
        memory: "256Mi"
        cpu: "200m"
  volumes:
  - name: config-volume
    configMap:
      name: app-config
  - name: app-config-volume
    configMap:
      name: app-config
      items:
      - key: app.properties
        path: application.properties
  - name: secret-volume
    secret:
      secretName: app-secrets
      defaultMode: 0400
```

```bash
#!/bin/bash
# スクリプト: configuration-management.sh

echo "⚙️ 設定管理の実践..."

# ConfigMapとSecret作成
echo "📋 ConfigMapとSecret作成中..."
kubectl apply -f app-config.yaml

# 設定確認
echo "📊 ConfigMap内容確認:"
kubectl get configmap app-config -o yaml

echo ""
echo "🔐 Secret内容確認:"
kubectl get secret app-secrets -o yaml

# 設定されたPod作成
echo "📦 設定済みPod作成中..."
kubectl apply -f configured-pod.yaml

kubectl wait --for=condition=Ready pod/configured-app --timeout=300s

# 設定確認
echo "🔍 Pod内設定確認:"
echo "環境変数確認:"
kubectl exec configured-app -- env | grep -E "DATABASE|DB_"

echo ""
echo "設定ファイル確認:"
kubectl exec configured-app -- cat /etc/nginx/conf.d/default.conf

echo ""
echo "アプリケーション設定ファイル:"
kubectl exec configured-app -- cat /etc/app-config/application.properties

echo ""
echo "シークレットファイル確認:"
kubectl exec configured-app -- ls -la /etc/secrets/
kubectl exec configured-app -- cat /etc/secrets/DB_USERNAME

echo "✅ 設定管理完了!"
```

## Phase 2: マルチコンテナPodパターン

### 2.1 サイドカーパターン - ログ収集

```yaml
# ファイル: sidecar-logging-pod.yaml
apiVersion: v1
kind: Pod
metadata:
  name: sidecar-logging
  labels:
    app: web-app-with-logging
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
    - name: web-content
      mountPath: /usr/share/nginx/html
    command: ["/bin/bash"]
    args:
    - -c
    - |
      # カスタムログ設定
      cat > /etc/nginx/nginx.conf << 'EOF'
      events {
          worker_connections 1024;
      }
      http {
          access_log /var/log/nginx/access.log;
          error_log /var/log/nginx/error.log;
          
          server {
              listen 80;
              location / {
                  root /usr/share/nginx/html;
                  index index.html;
              }
              location /metrics {
                  access_log /var/log/nginx/metrics.log;
                  return 200 "metrics data\n";
              }
          }
      }
      EOF
      
      # カスタムHTMLページ作成
      echo "<h1>Sidecar Logging Demo</h1><p>Time: $(date)</p>" > /usr/share/nginx/html/index.html
      
      # nginx起動
      nginx -g 'daemon off;'
  
  # ログ収集サイドカー
  - name: log-shipper
    image: busybox:1.35
    command: ["/bin/sh"]
    args:
    - -c
    - |
      # ログファイル作成待機
      while [ ! -f /var/log/nginx/access.log ]; do
        echo "Waiting for log files..."
        sleep 2
      done
      
      echo "Starting log shipping..."
      # アクセスログを継続監視
      tail -f /var/log/nginx/access.log | while read line; do
        echo "[LOG-SHIPPER] ACCESS: $line"
      done &
      
      # エラーログを継続監視
      tail -f /var/log/nginx/error.log | while read line; do
        echo "[LOG-SHIPPER] ERROR: $line"
      done &
      
      wait
    volumeMounts:
    - name: shared-logs
      mountPath: /var/log/nginx
      readOnly: true
  
  # ログ分析サイドカー
  - name: log-analyzer
    image: busybox:1.35
    command: ["/bin/sh"]
    args:
    - -c
    - |
      while true; do
        sleep 30
        if [ -f /var/log/nginx/access.log ]; then
          echo "[ANALYZER] Log statistics:"
          echo "[ANALYZER] Total requests: $(wc -l < /var/log/nginx/access.log 2>/dev/null || echo 0)"
          echo "[ANALYZER] Unique IPs: $(awk '{print $1}' /var/log/nginx/access.log 2>/dev/null | sort -u | wc -l || echo 0)"
        fi
      done
    volumeMounts:
    - name: shared-logs
      mountPath: /var/log/nginx
      readOnly: true
  
  volumes:
  - name: shared-logs
    emptyDir: {}
  - name: web-content
    emptyDir: {}
```

### 2.2 アンバサダーパターン - プロキシコンテナ

```yaml
# ファイル: ambassador-pattern-pod.yaml
apiVersion: v1
kind: Pod
metadata:
  name: ambassador-demo
  labels:
    app: ambassador-pattern
spec:
  containers:
  # メインアプリケーション
  - name: main-app
    image: busybox:1.35
    command: ["/bin/sh"]
    args:
    - -c
    - |
      echo "Main application starting..."
      while true; do
        echo "Connecting to database via localhost:5432..."
        nc -z localhost 5432 && echo "Database connection: OK" || echo "Database connection: Failed"
        
        echo "Connecting to cache via localhost:6379..."
        nc -z localhost 6379 && echo "Cache connection: OK" || echo "Cache connection: Failed"
        
        sleep 30
      done
    resources:
      requests:
        cpu: "50m"
        memory: "32Mi"
  
  # データベースプロキシ（アンバサダー）
  - name: db-proxy
    image: nginx:1.20
    ports:
    - containerPort: 5432
      name: postgres
    command: ["/bin/bash"]
    args:
    - -c
    - |
      # nginx stream module configuration for TCP proxy
      cat > /etc/nginx/nginx.conf << 'EOF'
      events {
          worker_connections 1024;
      }
      stream {
          upstream postgres_backend {
              server external-db.example.com:5432;
              # Fallback servers
              server backup-db.example.com:5432 backup;
          }
          
          server {
              listen 5432;
              proxy_pass postgres_backend;
              proxy_timeout 1s;
              proxy_responses 1;
          }
      }
      EOF
      
      echo "DB Proxy starting on port 5432..."
      nginx -g 'daemon off;'
    resources:
      requests:
        cpu: "50m"
        memory: "32Mi"
  
  # キャッシュプロキシ（アンバサダー）
  - name: cache-proxy
    image: nginx:1.20
    ports:
    - containerPort: 6379
      name: redis
    command: ["/bin/bash"]
    args:
    - -c
    - |
      cat > /etc/nginx/nginx.conf << 'EOF'
      events {
          worker_connections 1024;
      }
      stream {
          upstream redis_backend {
              server external-cache.example.com:6379;
              server backup-cache.example.com:6379 backup;
          }
          
          server {
              listen 6379;
              proxy_pass redis_backend;
              proxy_timeout 1s;
              proxy_responses 1;
          }
      }
      EOF
      
      echo "Cache Proxy starting on port 6379..."
      nginx -g 'daemon off;'
    resources:
      requests:
        cpu: "50m"
        memory: "32Mi"
```

```bash
#!/bin/bash
# スクリプト: multi-container-patterns.sh

echo "🔄 マルチコンテナパターンの実践..."

# サイドカーパターンのデプロイ
echo "📊 サイドカーパターン（ログ収集）デプロイ中..."
kubectl apply -f sidecar-logging-pod.yaml

kubectl wait --for=condition=Ready pod/sidecar-logging --timeout=300s

echo "🌐 ログ収集動作確認:"
# アクセスを生成してログ確認
kubectl port-forward pod/sidecar-logging 8080:80 &
PF_PID1=$!
sleep 5

# 複数回アクセスしてログ生成
for i in {1..5}; do
    curl -s http://localhost:8080/ >/dev/null
    curl -s http://localhost:8080/metrics >/dev/null
    sleep 1
done

# ログシッパーの出力確認
echo "ログシッパーの出力:"
kubectl logs sidecar-logging -c log-shipper --tail=10

echo ""
echo "ログアナライザーの出力:"
kubectl logs sidecar-logging -c log-analyzer --tail=5

kill $PF_PID1 2>/dev/null

# アンバサダーパターンのデプロイ
echo ""
echo "🔗 アンバサダーパターン（プロキシ）デプロイ中..."
kubectl apply -f ambassador-pattern-pod.yaml

kubectl wait --for=condition=Ready pod/ambassador-demo --timeout=300s

echo "🔍 アンバサダー動作確認:"
kubectl logs ambassador-demo -c main-app --tail=5

echo ""
echo "📊 各コンテナの状態:"
kubectl get pod sidecar-logging -o jsonpath='{range .status.containerStatuses[*]}{.name}{"\t"}{.ready}{"\n"}{end}'
kubectl get pod ambassador-demo -o jsonpath='{range .status.containerStatuses[*]}{.name}{"\t"}{.ready}{"\n"}{end}'

echo "✅ マルチコンテナパターン完了!"
```

## Phase 3: Init Containers と起動順序制御

### 3.1 データベース初期化 Init Container

```yaml
# ファイル: init-container-demo.yaml
apiVersion: v1
kind: Pod
metadata:
  name: web-app-with-init
  labels:
    app: web-app-with-init
spec:
  initContainers:
  # データベース接続確認
  - name: wait-for-db
    image: busybox:1.35
    command: ['sh', '-c']
    args:
    - |
      echo "Waiting for database to be ready..."
      until nc -z db-service 5432; do
        echo "Database not ready, waiting..."
        sleep 5
      done
      echo "Database is ready!"
  
  # データベース初期化
  - name: db-migration
    image: postgres:13
    env:
    - name: PGHOST
      value: "db-service"
    - name: PGPORT
      value: "5432"
    - name: PGUSER
      value: "admin"
    - name: PGPASSWORD
      value: "password"
    - name: PGDATABASE
      value: "webapp"
    command: ["/bin/bash"]
    args:
    - -c
    - |
      echo "Running database migration..."
      
      # テーブル作成SQL
      cat > /tmp/init.sql << 'EOF'
      CREATE TABLE IF NOT EXISTS users (
          id SERIAL PRIMARY KEY,
          username VARCHAR(50) UNIQUE NOT NULL,
          email VARCHAR(100) UNIQUE NOT NULL,
          created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
      );
      
      CREATE TABLE IF NOT EXISTS posts (
          id SERIAL PRIMARY KEY,
          title VARCHAR(200) NOT NULL,
          content TEXT,
          user_id INTEGER REFERENCES users(id),
          created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
      );
      
      INSERT INTO users (username, email) VALUES 
      ('admin', 'admin@example.com'),
      ('user1', 'user1@example.com')
      ON CONFLICT (username) DO NOTHING;
      EOF
      
      # マイグレーション実行
      psql -f /tmp/init.sql
      echo "Database migration completed!"
  
  # 静的ファイル準備
  - name: setup-content
    image: busybox:1.35
    command: ["/bin/sh"]
    args:
    - -c
    - |
      echo "Setting up web content..."
      
      # HTMLファイル作成
      cat > /shared-data/index.html << 'EOF'
      <!DOCTYPE html>
      <html>
      <head>
          <title>Web App with Init Containers</title>
          <style>
              body { font-family: Arial, sans-serif; margin: 40px; }
              .header { background: #007bff; color: white; padding: 20px; }
              .content { padding: 20px; }
          </style>
      </head>
      <body>
          <div class="header">
              <h1>Web Application</h1>
              <p>Initialized with Init Containers</p>
          </div>
          <div class="content">
              <h2>Application Status</h2>
              <p>✅ Database migration completed</p>
              <p>✅ Static content deployed</p>
              <p>✅ Application ready to serve</p>
              <p><strong>Startup Time:</strong> <span id="time"></span></p>
          </div>
          <script>
              document.getElementById('time').innerText = new Date().toLocaleString();
          </script>
      </body>
      </html>
      EOF
      
      # API エンドポイント用JSON
      cat > /shared-data/api.json << 'EOF'
      {
          "status": "healthy",
          "version": "1.0.0",
          "database": "connected",
          "features": ["user_management", "content_management"],
          "initialized_at": "TIMESTAMP_PLACEHOLDER"
      }
      EOF
      
      # タイムスタンプ置換
      sed -i "s/TIMESTAMP_PLACEHOLDER/$(date -Iseconds)/" /shared-data/api.json
      
      echo "Content setup completed!"
    volumeMounts:
    - name: shared-content
      mountPath: /shared-data
  
  containers:
  # メインウェブアプリケーション
  - name: web-server
    image: nginx:1.20
    ports:
    - containerPort: 80
    volumeMounts:
    - name: shared-content
      mountPath: /usr/share/nginx/html
    - name: nginx-config
      mountPath: /etc/nginx/conf.d/default.conf
      subPath: nginx.conf
    livenessProbe:
      httpGet:
        path: /health
        port: 80
      initialDelaySeconds: 10
      periodSeconds: 10
    readinessProbe:
      httpGet:
        path: /
        port: 80
      initialDelaySeconds: 5
      periodSeconds: 5
    resources:
      requests:
        memory: "64Mi"
        cpu: "100m"
      limits:
        memory: "128Mi"
        cpu: "200m"
  
  volumes:
  - name: shared-content
    emptyDir: {}
  - name: nginx-config
    configMap:
      name: nginx-config
---
apiVersion: v1
kind: ConfigMap
metadata:
  name: nginx-config
data:
  nginx.conf: |
    server {
        listen 80;
        server_name localhost;
        
        location / {
            root /usr/share/nginx/html;
            index index.html;
        }
        
        location /api/status {
            alias /usr/share/nginx/html/api.json;
            add_header Content-Type application/json;
        }
        
        location /health {
            access_log off;
            return 200 "healthy\n";
            add_header Content-Type text/plain;
        }
    }
```

```bash
#!/bin/bash
# スクリプト: init-containers-demo.sh

echo "🚀 Init Containers デモンストレーション..."

# 模擬データベースサービス作成
echo "🗃️ 模擬データベースサービス作成中..."
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: mock-database
  labels:
    app: mock-db
spec:
  containers:
  - name: postgres
    image: postgres:13
    env:
    - name: POSTGRES_DB
      value: webapp
    - name: POSTGRES_USER
      value: admin
    - name: POSTGRES_PASSWORD
      value: password
    ports:
    - containerPort: 5432
    resources:
      requests:
        memory: "256Mi"
        cpu: "200m"
---
apiVersion: v1
kind: Service
metadata:
  name: db-service
spec:
  selector:
    app: mock-db
  ports:
  - port: 5432
    targetPort: 5432
EOF

# データベース起動待機
echo "⏳ データベース起動待機中..."
kubectl wait --for=condition=Ready pod/mock-database --timeout=300s

# nginx設定用ConfigMap作成
kubectl apply -f - <<EOF
apiVersion: v1
kind: ConfigMap
metadata:
  name: nginx-config
data:
  nginx.conf: |
    server {
        listen 80;
        server_name localhost;
        
        location / {
            root /usr/share/nginx/html;
            index index.html;
        }
        
        location /api/status {
            alias /usr/share/nginx/html/api.json;
            add_header Content-Type application/json;
        }
        
        location /health {
            access_log off;
            return 200 "healthy\\n";
            add_header Content-Type text/plain;
        }
    }
EOF

# Init Container付きアプリケーションデプロイ
echo "📦 Init Container付きアプリケーションデプロイ中..."
kubectl apply -f init-container-demo.yaml

# Init Container実行監視
echo "👀 Init Container実行状況監視:"
for i in {1..30}; do
    STATUS=$(kubectl get pod web-app-with-init -o jsonpath='{.status.phase}')
    INIT_STATUS=$(kubectl get pod web-app-with-init -o jsonpath='{.status.initContainerStatuses[*].state.*.reason}' 2>/dev/null || echo "")
    
    echo "[$i] Pod Status: $STATUS, Init Status: $INIT_STATUS"
    
    if [ "$STATUS" = "Running" ]; then
        break
    fi
    
    sleep 10
done

# アプリケーション動作確認
kubectl wait --for=condition=Ready pod/web-app-with-init --timeout=300s

echo ""
echo "📊 Init Container ログ確認:"
echo "=== wait-for-db ==="
kubectl logs web-app-with-init -c wait-for-db

echo ""
echo "=== db-migration ==="
kubectl logs web-app-with-init -c db-migration

echo ""
echo "=== setup-content ==="
kubectl logs web-app-with-init -c setup-content

# アプリケーションテスト
echo ""
echo "🌐 アプリケーション動作テスト:"
kubectl port-forward pod/web-app-with-init 8080:80 &
PF_PID=$!
sleep 5

echo "メインページ確認:"
curl -s http://localhost:8080/ | grep -o '<title>.*</title>'

echo ""
echo "APIエンドポイント確認:"
curl -s http://localhost:8080/api/status | python3 -m json.tool

echo ""
echo "ヘルスチェック確認:"
curl -s http://localhost:8080/health

kill $PF_PID 2>/dev/null

echo ""
echo "✅ Init Container デモ完了!"
```

## Phase 4: ヘルスチェックとプローブ設定

### 4.1 包括的なヘルスチェック実装

```yaml
# ファイル: health-check-pod.yaml
apiVersion: v1
kind: Pod
metadata:
  name: health-check-demo
  labels:
    app: health-check-demo
spec:
  containers:
  - name: web-app
    image: nginx:1.20
    ports:
    - containerPort: 80
      name: http
    # Startup Probe - 初期起動時のチェック
    startupProbe:
      httpGet:
        path: /startup
        port: 80
      initialDelaySeconds: 10
      periodSeconds: 5
      timeoutSeconds: 3
      failureThreshold: 6  # 30秒まで待機
      successThreshold: 1
    
    # Liveness Probe - アプリケーション生存チェック
    livenessProbe:
      httpGet:
        path: /health
        port: 80
      initialDelaySeconds: 30
      periodSeconds: 10
      timeoutSeconds: 5
      failureThreshold: 3
      successThreshold: 1
    
    # Readiness Probe - トラフィック受信準備チェック
    readinessProbe:
      httpGet:
        path: /ready
        port: 80
      initialDelaySeconds: 5
      periodSeconds: 5
      timeoutSeconds: 3
      failureThreshold: 2
      successThreshold: 1
    
    volumeMounts:
    - name: health-check-scripts
      mountPath: /usr/share/nginx/html
    - name: nginx-config
      mountPath: /etc/nginx/conf.d/default.conf
      subPath: default.conf
    
    resources:
      requests:
        memory: "64Mi"
        cpu: "100m"
      limits:
        memory: "128Mi"
        cpu: "200m"
    
    # 環境変数でアプリケーション状態制御
    env:
    - name: APP_HEALTH
      value: "healthy"
    - name: APP_READY
      value: "true"
  
  volumes:
  - name: health-check-scripts
    configMap:
      name: health-check-scripts
      defaultMode: 0755
  - name: nginx-config
    configMap:
      name: nginx-health-config
---
apiVersion: v1
kind: ConfigMap
metadata:
  name: health-check-scripts
data:
  index.html: |
    <!DOCTYPE html>
    <html>
    <head><title>Health Check Demo</title></head>
    <body>
        <h1>Health Check Demonstration</h1>
        <p>Application is running with comprehensive health checks.</p>
        <ul>
            <li><a href="/startup">Startup Check</a></li>
            <li><a href="/health">Liveness Check</a></li>
            <li><a href="/ready">Readiness Check</a></li>
        </ul>
    </body>
    </html>
  
  startup: |
    #!/bin/bash
    # Startup check - simulate slow initialization
    STARTUP_FILE="/tmp/startup_complete"
    
    if [ ! -f "$STARTUP_FILE" ]; then
        # Simulate startup delay
        sleep 15
        touch "$STARTUP_FILE"
    fi
    
    echo "Content-Type: text/plain"
    echo ""
    echo "startup: OK"
  
  health: |
    #!/bin/bash
    # Liveness check - simulate periodic health check
    HEALTH_STATUS=${APP_HEALTH:-healthy}
    
    if [ "$HEALTH_STATUS" = "healthy" ]; then
        echo "Content-Type: text/plain"
        echo ""
        echo "health: OK"
        exit 0
    else
        echo "Content-Type: text/plain"
        echo ""
        echo "health: FAILED"
        exit 1
    fi
  
  ready: |
    #!/bin/bash
    # Readiness check - check if app is ready to serve traffic
    READY_STATUS=${APP_READY:-true}
    
    # Check dependencies (simulate)
    if [ "$READY_STATUS" = "true" ] && [ -f "/tmp/startup_complete" ]; then
        echo "Content-Type: text/plain"
        echo ""
        echo "ready: OK"
        exit 0
    else
        echo "Content-Type: text/plain"
        echo ""
        echo "ready: NOT_READY"
        exit 1
    fi
---
apiVersion: v1
kind: ConfigMap
metadata:
  name: nginx-health-config
data:
  default.conf: |
    server {
        listen 80;
        server_name localhost;
        
        location / {
            root /usr/share/nginx/html;
            index index.html;
        }
        
        location /startup {
            fastcgi_pass unix:/does/not/exist;
            access_log off;
            return 200 "startup: OK\n";
            add_header Content-Type text/plain;
        }
        
        location /health {
            access_log off;
            return 200 "health: OK\n";
            add_header Content-Type text/plain;
        }
        
        location /ready {
            access_log off;
            return 200 "ready: OK\n";
            add_header Content-Type text/plain;
        }
    }
```

### 4.2 カスタムヘルスチェックアプリケーション

```yaml
# ファイル: custom-health-app.yaml
apiVersion: v1
kind: Pod
metadata:
  name: custom-health-app
  labels:
    app: custom-health-app
spec:
  containers:
  - name: health-aware-app
    image: python:3.9-slim
    ports:
    - containerPort: 8080
    command: ["python3"]
    args:
    - -c
    - |
      import http.server
      import socketserver
      import json
      import time
      import os
      import threading
      from datetime import datetime
      
      class HealthHandler(http.server.BaseHTTPRequestHandler):
          def do_GET(self):
              if self.path == '/startup':
                  self.startup_check()
              elif self.path == '/health':
                  self.health_check()
              elif self.path == '/ready':
                  self.readiness_check()
              elif self.path == '/metrics':
                  self.metrics()
              else:
                  self.send_response(404)
                  self.end_headers()
          
          def startup_check(self):
              # Simulate slow startup
              startup_file = '/tmp/app_started'
              if not os.path.exists(startup_file):
                  time.sleep(20)  # Simulate startup time
                  with open(startup_file, 'w') as f:
                      f.write(str(time.time()))
              
              self.send_response(200)
              self.send_header('Content-Type', 'application/json')
              self.end_headers()
              response = {"status": "started", "timestamp": datetime.now().isoformat()}
              self.wfile.write(json.dumps(response).encode())
          
          def health_check(self):
              # Check application health
              health_status = os.environ.get('HEALTH_STATUS', 'healthy')
              
              if health_status == 'healthy':
                  self.send_response(200)
                  response = {"status": "healthy", "uptime": time.time() - start_time}
              else:
                  self.send_response(503)
                  response = {"status": "unhealthy", "reason": "simulated failure"}
              
              self.send_header('Content-Type', 'application/json')
              self.end_headers()
              self.wfile.write(json.dumps(response).encode())
          
          def readiness_check(self):
              # Check if app is ready to serve traffic
              startup_file = '/tmp/app_started'
              ready_status = os.environ.get('READY_STATUS', 'true')
              
              if os.path.exists(startup_file) and ready_status == 'true':
                  self.send_response(200)
                  response = {"status": "ready", "connections": 0}
              else:
                  self.send_response(503)
                  response = {"status": "not_ready", "reason": "dependencies not available"}
              
              self.send_header('Content-Type', 'application/json')
              self.end_headers()
              self.wfile.write(json.dumps(response).encode())
          
          def metrics(self):
              self.send_response(200)
              self.send_header('Content-Type', 'application/json')
              self.end_headers()
              
              metrics = {
                  "uptime_seconds": time.time() - start_time,
                  "memory_usage": "64MB",
                  "cpu_usage": "15%",
                  "requests_total": 42,
                  "last_check": datetime.now().isoformat()
              }
              self.wfile.write(json.dumps(metrics, indent=2).encode())
      
      start_time = time.time()
      PORT = 8080
      
      with socketserver.TCPServer(("", PORT), HealthHandler) as httpd:
          print(f"Health-aware application serving at port {PORT}")
          httpd.serve_forever()
    
    # カスタムヘルスチェック設定
    startupProbe:
      httpGet:
        path: /startup
        port: 8080
      initialDelaySeconds: 5
      periodSeconds: 5
      timeoutSeconds: 10
      failureThreshold: 6
    
    livenessProbe:
      httpGet:
        path: /health
        port: 8080
      initialDelaySeconds: 30
      periodSeconds: 15
      timeoutSeconds: 5
      failureThreshold: 3
    
    readinessProbe:
      httpGet:
        path: /ready
        port: 8080
      initialDelaySeconds: 5
      periodSeconds: 10
      timeoutSeconds: 5
      failureThreshold: 2
    
    env:
    - name: HEALTH_STATUS
      value: "healthy"
    - name: READY_STATUS
      value: "true"
    
    resources:
      requests:
        memory: "128Mi"
        cpu: "100m"
      limits:
        memory: "256Mi"
        cpu: "200m"
```

```bash
#!/bin/bash
# スクリプト: health-check-demo.sh

echo "❤️ ヘルスチェック総合デモンストレーション..."

# ConfigMapとPod作成
echo "📋 ヘルスチェック設定作成中..."
kubectl apply -f health-check-pod.yaml

# カスタムヘルスチェックアプリケーション作成
echo "🏥 カスタムヘルスチェックアプリケーション作成中..."
kubectl apply -f custom-health-app.yaml

# 起動プロセス監視
echo "👀 Pod起動プロセス監視:"
for i in {1..60}; do
    echo "=== Check $i ==="
    kubectl get pods health-check-demo custom-health-app
    
    # Startup probe 状況確認
    echo "Startup probe status:"
    kubectl describe pod health-check-demo | grep -A 5 "Startup:"
    
    # Ready状態チェック
    READY1=$(kubectl get pod health-check-demo -o jsonpath='{.status.conditions[?(@.type=="Ready")].status}')
    READY2=$(kubectl get pod custom-health-app -o jsonpath='{.status.conditions[?(@.type=="Ready")].status}')
    
    echo "health-check-demo Ready: $READY1"
    echo "custom-health-app Ready: $READY2"
    
    if [ "$READY1" = "True" ] && [ "$READY2" = "True" ]; then
        echo "✅ 両方のPodがReady状態になりました!"
        break
    fi
    
    sleep 10
done

# ヘルスチェックエンドポイントテスト
echo ""
echo "🔍 ヘルスチェックエンドポイントテスト:"

# health-check-demo テスト
kubectl port-forward pod/health-check-demo 8081:80 &
PF_PID1=$!
sleep 3

echo "=== Basic Health Check Pod ==="
echo "Startup endpoint:"
curl -s http://localhost:8081/startup

echo ""
echo "Health endpoint:"
curl -s http://localhost:8081/health

echo ""
echo "Ready endpoint:"
curl -s http://localhost:8081/ready

kill $PF_PID1 2>/dev/null

# custom-health-app テスト
kubectl port-forward pod/custom-health-app 8082:8080 &
PF_PID2=$!
sleep 3

echo ""
echo "=== Custom Health Check App ==="
echo "Startup check:"
curl -s http://localhost:8082/startup | python3 -m json.tool

echo ""
echo "Health check:"
curl -s http://localhost:8082/health | python3 -m json.tool

echo ""
echo "Readiness check:"
curl -s http://localhost:8082/ready | python3 -m json.tool

echo ""
echo "Metrics:"
curl -s http://localhost:8082/metrics | python3 -m json.tool

kill $PF_PID2 2>/dev/null

# 失敗シナリオのテスト
echo ""
echo "🚨 失敗シナリオテスト:"
echo "ヘルスチェック失敗をシミュレート..."

# 環境変数を変更してヘルスチェック失敗をシミュレート
kubectl patch pod custom-health-app -p '{"spec":{"containers":[{"name":"health-aware-app","env":[{"name":"HEALTH_STATUS","value":"unhealthy"}]}]}}'

echo "30秒後にヘルスチェック状態を確認..."
sleep 30

kubectl describe pod custom-health-app | grep -A 10 "Liveness:"

echo ""
echo "✅ ヘルスチェックデモ完了!"
```

## Phase 5: リソース管理とセキュリティ

### 5.1 リソース制限と QoS クラス

```yaml
# ファイル: resource-qos-demo.yaml
# Guaranteed QoS Class
apiVersion: v1
kind: Pod
metadata:
  name: guaranteed-qos-pod
  labels:
    qos-class: guaranteed
spec:
  containers:
  - name: app
    image: nginx:1.20
    resources:
      requests:
        memory: "256Mi"
        cpu: "500m"
      limits:
        memory: "256Mi"  # requests と同じ値
        cpu: "500m"      # requests と同じ値
---
# Burstable QoS Class
apiVersion: v1
kind: Pod
metadata:
  name: burstable-qos-pod
  labels:
    qos-class: burstable
spec:
  containers:
  - name: app
    image: nginx:1.20
    resources:
      requests:
        memory: "128Mi"
        cpu: "200m"
      limits:
        memory: "512Mi"  # requests より大きい
        cpu: "1000m"     # requests より大きい
---
# BestEffort QoS Class
apiVersion: v1
kind: Pod
metadata:
  name: besteffort-qos-pod
  labels:
    qos-class: besteffort
spec:
  containers:
  - name: app
    image: nginx:1.20
    # リソース指定なし
```

### 5.2 セキュリティコンテキスト

```yaml
# ファイル: security-context-demo.yaml
apiVersion: v1
kind: Pod
metadata:
  name: secure-pod
  labels:
    app: secure-pod
spec:
  # Pod レベルのセキュリティコンテキスト
  securityContext:
    runAsUser: 1000
    runAsGroup: 1000
    runAsNonRoot: true
    fsGroup: 1000
    seccompProfile:
      type: RuntimeDefault
  
  containers:
  - name: secure-app
    image: nginx:1.20
    # コンテナレベルのセキュリティコンテキスト
    securityContext:
      allowPrivilegeEscalation: false
      readOnlyRootFilesystem: true
      capabilities:
        drop:
        - ALL
        add:
        - NET_BIND_SERVICE  # nginx が80番ポートにバインドするため
    
    ports:
    - containerPort: 8080  # 非特権ポート使用
    
    volumeMounts:
    - name: nginx-config
      mountPath: /etc/nginx/nginx.conf
      subPath: nginx.conf
      readOnly: true
    - name: tmp-volume
      mountPath: /tmp
    - name: var-cache-nginx
      mountPath: /var/cache/nginx
    - name: var-run
      mountPath: /var/run
    
    resources:
      requests:
        memory: "64Mi"
        cpu: "100m"
      limits:
        memory: "128Mi"
        cpu: "200m"
  
  volumes:
  - name: nginx-config
    configMap:
      name: secure-nginx-config
  - name: tmp-volume
    emptyDir: {}
  - name: var-cache-nginx
    emptyDir: {}
  - name: var-run
    emptyDir: {}
---
apiVersion: v1
kind: ConfigMap
metadata:
  name: secure-nginx-config
data:
  nginx.conf: |
    user nginx;
    worker_processes auto;
    pid /var/run/nginx.pid;
    
    events {
        worker_connections 1024;
    }
    
    http {
        include /etc/nginx/mime.types;
        default_type application/octet-stream;
        
        # セキュリティヘッダー
        add_header X-Frame-Options DENY;
        add_header X-Content-Type-Options nosniff;
        add_header X-XSS-Protection "1; mode=block";
        
        server {
            listen 8080;
            server_name localhost;
            
            location / {
                return 200 "Secure NGINX Server\nRunning as non-root user\nRead-only filesystem\n";
                add_header Content-Type text/plain;
            }
            
            location /health {
                return 200 "healthy\n";
                add_header Content-Type text/plain;
            }
        }
    }
```

```bash
#!/bin/bash
# スクリプト: resource-security-demo.sh

echo "🔒 リソース管理とセキュリティデモンストレーション..."

# QoS クラスのデモ
echo "📊 QoS クラスデモンストレーション..."
kubectl apply -f resource-qos-demo.yaml

# Pod起動待機
for pod in guaranteed-qos-pod burstable-qos-pod besteffort-qos-pod; do
    kubectl wait --for=condition=Ready pod/$pod --timeout=300s
done

# QoS クラス確認
echo "QoS クラス確認:"
for pod in guaranteed-qos-pod burstable-qos-pod besteffort-qos-pod; do
    QOS=$(kubectl get pod $pod -o jsonpath='{.status.qosClass}')
    echo "$pod: $QOS"
done

# セキュリティコンテキストのデモ
echo ""
echo "🛡️ セキュリティコンテキストデモンストレーション..."
kubectl apply -f security-context-demo.yaml

kubectl wait --for=condition=Ready pod/secure-pod --timeout=300s

# セキュリティ設定確認
echo "セキュリティ設定確認:"
kubectl describe pod secure-pod | grep -A 20 "Security Context:"

# Pod内でのユーザー確認
echo ""
echo "Pod内ユーザー確認:"
kubectl exec secure-pod -- whoami
kubectl exec secure-pod -- id

# ファイルシステム確認
echo ""
echo "ファイルシステム確認:"
kubectl exec secure-pod -- ls -la /
kubectl exec secure-pod -- mount | grep "ro\|rw" | head -5

# セキュアアプリケーション動作確認
echo ""
echo "🌐 セキュアアプリケーション動作確認:"
kubectl port-forward pod/secure-pod 8080:8080 &
PF_PID=$!
sleep 3

curl -s http://localhost:8080/
curl -s http://localhost:8080/health

kill $PF_PID 2>/dev/null

# リソース使用量確認
echo ""
echo "📈 リソース使用量確認:"
kubectl top pods 2>/dev/null || echo "メトリクスサーバーが利用できません"

echo ""
echo "✅ リソース管理とセキュリティデモ完了!"
```

## Phase 6: クリーンアップとベストプラクティス

### 6.1 総合クリーンアップ

```bash
#!/bin/bash
# スクリプト: comprehensive-cleanup.sh

echo "🧹 Pod・Container実習の総合クリーンアップ..."

# 作成したPodを削除
echo "🗑️ 作成したPodの削除中..."
kubectl delete pod --ignore-not-found \
    web-app \
    configured-app \
    sidecar-logging \
    ambassador-demo \
    web-app-with-init \
    mock-database \
    health-check-demo \
    custom-health-app \
    guaranteed-qos-pod \
    burstable-qos-pod \
    besteffort-qos-pod \
    secure-pod

# ConfigMapとSecretの削除
echo "📋 ConfigMapとSecretの削除中..."
kubectl delete configmap --ignore-not-found \
    app-config \
    nginx-config \
    health-check-scripts \
    nginx-health-config \
    secure-nginx-config

kubectl delete secret --ignore-not-found \
    app-secrets

# Serviceの削除
echo "🌐 Serviceの削除中..."
kubectl delete service --ignore-not-found \
    db-service

# 残存リソース確認
echo ""
echo "📊 残存リソース確認:"
echo "Pods:"
kubectl get pods | grep -E "(web-app|configured|sidecar|ambassador|init|health|qos|secure)" || echo "No related pods found"

echo ""
echo "ConfigMaps:"
kubectl get configmaps | grep -E "(app-config|nginx-config|health)" || echo "No related configmaps found"

echo ""
echo "Secrets:"
kubectl get secrets | grep app-secrets || echo "No related secrets found"

echo ""
echo "Services:"
kubectl get services | grep db-service || echo "No related services found"

echo ""
echo "✅ クリーンアップ完了!"

# コスト確認
echo ""
echo "💰 本ラボの推定コスト："
echo "   - minikube (ローカル): 無料"
echo "   - Google GKE: ~$2-3 (6時間実行)"
echo "   - AWS EKS: ~$3-4 (6時間実行)"
echo "   - Azure AKS: ~$2-3 (6時間実行)"
```

### 6.2 学習成果の確認

```bash
#!/bin/bash
# スクリプト: learning-assessment.sh

echo "📚 学習成果確認チェックリスト..."

echo ""
echo "✅ 完了した学習項目："
echo "[ ] 基本的なPod作成・管理"
echo "[ ] ConfigMap・Secret活用"
echo "[ ] マルチコンテナPodパターン"
echo "[ ] Init Containers実装"
echo "[ ] ヘルスチェック・プローブ設定"
echo "[ ] リソース管理・QoSクラス"
echo "[ ] セキュリティコンテキスト設定"

echo ""
echo "🎯 CKAD試験対策ポイント："
echo "1. Pod YAML作成の高速化"
echo "2. マルチコンテナ設計パターンの理解"
echo "3. トラブルシューティング手順の習得"
echo "4. セキュリティベストプラクティスの実装"

echo ""
echo "📈 次のステップ："
echo "- Lab 2: Application Deployment でDeployment管理を学習"
echo "- Practice Exam での実技演習"
echo "- 時間制限での問題解決練習"
```

## 📚 学習のポイント

### CKAD試験でのPod・Container要点

1. **高速YAML作成**
   ```bash
   kubectl run pod-name --image=image:tag --dry-run=client -o yaml > pod.yaml
   kubectl create configmap name --from-literal=key=value --dry-run=client -o yaml
   kubectl create secret generic name --from-literal=key=value --dry-run=client -o yaml
   ```

2. **マルチコンテナパターン**
   - **Sidecar**: ログ収集・監視エージェント
   - **Ambassador**: プロキシ・負荷分散
   - **Adapter**: データ変換・フォーマット統一

3. **ヘルスチェックベストプラクティス**
   - Startup Probe: 初期化に時間がかかるアプリ
   - Liveness Probe: アプリケーション生存確認
   - Readiness Probe: トラフィック受信準備確認

4. **セキュリティ考慮事項**
   - 非rootユーザーでの実行
   - 読み取り専用ファイルシステム
   - 最小権限の原則
   - リソース制限の設定

## 🎯 次のステップ

**完了したスキル:**
- [x] Pod基本操作とライフサイクル
- [x] マルチコンテナアプリケーション設計
- [x] Init Containers活用
- [x] ヘルスチェック実装
- [x] リソース管理とセキュリティ設定

**次のラボ:** [Lab 2: Application Deployment と管理](./lab02-application-deployment.md)

**重要な注意:**
CKAD試験では、Pod関連の問題が基礎となります。このラボで学んだパターンと技術を確実にマスターすることで、より高度なアプリケーション管理タスクに進む準備が整います。