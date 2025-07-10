# Lab 04: クラウドネイティブ可観測性

## 📋 ラボ概要

**目的**: 可観測性の3つの柱（Metrics、Logs、Traces）の理解と実装、Prometheus/Grafana/Jaegerを使用した監視システム構築  
**所要時間**: 120-150分  
**前提条件**: Lab 01-03完了、基本的な監視概念の理解  
**使用環境**: Kubernetes、Prometheus、Grafana、Jaeger

---

## 🎯 学習目標

このラボ完了後、以下ができるようになります：

1. 可観測性の3つの柱（Metrics、Logs、Traces）の理解と実践
2. Prometheusを使用したメトリクス収集と監視
3. Grafanaを使用したダッシュボード作成と可視化
4. 構造化ログの実装とログ管理
5. Jaegerを使用した分散トレーシング
6. アラートルールの設定と通知
7. SLI/SLO/SLAの基本概念
8. 障害対応とトラブルシューティング

---

## 🛠️ 事前準備

### 環境セットアップ

```bash
# 作業ディレクトリ作成
mkdir -p ~/kcna-lab04/{monitoring,apps,configs}
cd ~/kcna-lab04

# 監視用namespace作成
kubectl create namespace monitoring
kubectl create namespace observability-demo

# 現在のコンテキスト確認
kubectl config current-context
```

---

## 📊 Exercise 1: Prometheus による Metrics 収集

### 1.1 Prometheus サーバーのデプロイ

**ファイル: monitoring/prometheus-config.yaml**
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: prometheus-config
  namespace: monitoring
data:
  prometheus.yml: |
    global:
      scrape_interval: 15s
      evaluation_interval: 15s
    
    rule_files:
      - "/etc/prometheus/rules/*.yml"
    
    alerting:
      alertmanagers:
        - static_configs:
            - targets:
              - alertmanager:9093
    
    scrape_configs:
      - job_name: 'prometheus'
        static_configs:
          - targets: ['localhost:9090']
      
      - job_name: 'kubernetes-pods'
        kubernetes_sd_configs:
          - role: pod
        relabel_configs:
          - source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_scrape]
            action: keep
            regex: true
          - source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_path]
            action: replace
            target_label: __metrics_path__
            regex: (.+)
          - source_labels: [__address__, __meta_kubernetes_pod_annotation_prometheus_io_port]
            action: replace
            regex: ([^:]+)(?::\d+)?;(\d+)
            replacement: $1:$2
            target_label: __address__
          - action: labelmap
            regex: __meta_kubernetes_pod_label_(.+)
          - source_labels: [__meta_kubernetes_namespace]
            action: replace
            target_label: kubernetes_namespace
          - source_labels: [__meta_kubernetes_pod_name]
            action: replace
            target_label: kubernetes_pod_name
      
      - job_name: 'kubernetes-nodes'
        kubernetes_sd_configs:
          - role: node
        relabel_configs:
          - action: labelmap
            regex: __meta_kubernetes_node_label_(.+)
          - target_label: __address__
            replacement: kubernetes.default.svc:443
          - source_labels: [__meta_kubernetes_node_name]
            regex: (.+)
            target_label: __metrics_path__
            replacement: /api/v1/nodes/${1}/proxy/metrics
        scheme: https
        tls_config:
          ca_file: /var/run/secrets/kubernetes.io/serviceaccount/ca.crt
        bearer_token_file: /var/run/secrets/kubernetes.io/serviceaccount/token
---
apiVersion: v1
kind: ConfigMap
metadata:
  name: prometheus-rules
  namespace: monitoring
data:
  app-rules.yml: |
    groups:
    - name: application-rules
      rules:
      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.1
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High error rate detected"
          description: "Error rate is {{ $value }} for {{ $labels.job }}"
      
      - alert: HighLatency
        expr: histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) > 0.5
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High latency detected"
          description: "95th percentile latency is {{ $value }}s for {{ $labels.job }}"
      
      - alert: PodCrashLooping
        expr: rate(kube_pod_container_status_restarts_total[15m]) > 0
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "Pod is crash looping"
          description: "Pod {{ $labels.pod }} in namespace {{ $labels.namespace }} is restarting frequently"
```

**ファイル: monitoring/prometheus-deployment.yaml**
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: prometheus
  namespace: monitoring
  labels:
    app: prometheus
spec:
  replicas: 1
  selector:
    matchLabels:
      app: prometheus
  template:
    metadata:
      labels:
        app: prometheus
    spec:
      serviceAccountName: prometheus
      containers:
      - name: prometheus
        image: prom/prometheus:v2.45.0
        args:
          - '--config.file=/etc/prometheus/prometheus.yml'
          - '--storage.tsdb.path=/prometheus/'
          - '--web.console.libraries=/etc/prometheus/console_libraries'
          - '--web.console.templates=/etc/prometheus/consoles'
          - '--web.enable-lifecycle'
          - '--web.enable-admin-api'
        ports:
        - containerPort: 9090
        volumeMounts:
        - name: prometheus-config
          mountPath: /etc/prometheus
        - name: prometheus-rules
          mountPath: /etc/prometheus/rules
        - name: prometheus-storage
          mountPath: /prometheus
        resources:
          requests:
            memory: "400Mi"
            cpu: "200m"
          limits:
            memory: "800Mi"
            cpu: "500m"
      volumes:
      - name: prometheus-config
        configMap:
          name: prometheus-config
      - name: prometheus-rules
        configMap:
          name: prometheus-rules
      - name: prometheus-storage
        emptyDir: {}
---
apiVersion: v1
kind: Service
metadata:
  name: prometheus
  namespace: monitoring
  labels:
    app: prometheus
spec:
  selector:
    app: prometheus
  ports:
  - port: 9090
    targetPort: 9090
    nodePort: 30090
  type: NodePort
---
apiVersion: v1
kind: ServiceAccount
metadata:
  name: prometheus
  namespace: monitoring
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: prometheus
rules:
- apiGroups: [""]
  resources:
  - nodes
  - nodes/proxy
  - services
  - endpoints
  - pods
  verbs: ["get", "list", "watch"]
- apiGroups:
  - extensions
  resources:
  - ingresses
  verbs: ["get", "list", "watch"]
- nonResourceURLs: ["/metrics"]
  verbs: ["get"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: prometheus
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: prometheus
subjects:
- kind: ServiceAccount
  name: prometheus
  namespace: monitoring
```

### 1.2 メトリクス露出アプリケーションの作成

**ファイル: apps/metrics-app/app.py**
```python
import time
import random
import logging
from flask import Flask, jsonify, request
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
import os

app = Flask(__name__)

# Prometheusメトリクス定義
REQUEST_COUNT = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

REQUEST_DURATION = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint']
)

ACTIVE_CONNECTIONS = Gauge(
    'active_connections',
    'Number of active connections'
)

PROCESSING_TIME = Histogram(
    'business_process_duration_seconds',
    'Business process duration in seconds',
    ['process_type']
)

# アプリケーションメトリクス
app_info = Gauge(
    'app_info',
    'Application information',
    ['version', 'environment']
)

# アプリケーション情報設定
SERVICE_VERSION = os.getenv('SERVICE_VERSION', '1.0.0')
ENVIRONMENT = os.getenv('ENVIRONMENT', 'development')
app_info.labels(version=SERVICE_VERSION, environment=ENVIRONMENT).set(1)

def track_metrics(f):
    """メトリクス追跡デコレータ"""
    def wrapper(*args, **kwargs):
        start_time = time.time()
        endpoint = request.endpoint or 'unknown'
        method = request.method
        
        try:
            response = f(*args, **kwargs)
            status = str(response[1]) if isinstance(response, tuple) else '200'
            
            # メトリクス記録
            REQUEST_COUNT.labels(method=method, endpoint=endpoint, status=status).inc()
            REQUEST_DURATION.labels(method=method, endpoint=endpoint).observe(time.time() - start_time)
            
            return response
        except Exception as e:
            REQUEST_COUNT.labels(method=method, endpoint=endpoint, status='500').inc()
            REQUEST_DURATION.labels(method=method, endpoint=endpoint).observe(time.time() - start_time)
            raise e
    
    wrapper.__name__ = f.__name__
    return wrapper

@app.route('/health')
@track_metrics
def health():
    return jsonify({'status': 'healthy'})

@app.route('/metrics')
def metrics():
    """Prometheusメトリクスエンドポイント"""
    return generate_latest(), 200, {'Content-Type': CONTENT_TYPE_LATEST}

@app.route('/api/data')
@track_metrics
def get_data():
    # 処理時間の模擬
    process_start = time.time()
    
    # ランダムな遅延（0.1-2秒）
    delay = random.uniform(0.1, 2.0)
    time.sleep(delay)
    
    # ビジネスプロセス時間を記録
    PROCESSING_TIME.labels(process_type='data_retrieval').observe(time.time() - process_start)
    
    # ランダムエラーの発生（10%の確率）
    if random.random() < 0.1:
        return jsonify({'error': 'Internal server error'}), 500
    
    return jsonify({
        'data': f'Sample data {random.randint(1, 1000)}',
        'timestamp': time.time(),
        'processing_time': delay
    })

@app.route('/api/slow')
@track_metrics
def slow_endpoint():
    """意図的に遅いエンドポイント"""
    time.sleep(random.uniform(2, 5))
    return jsonify({'message': 'Slow operation completed'})

@app.route('/api/error')
@track_metrics
def error_endpoint():
    """エラーを発生させるエンドポイント"""
    return jsonify({'error': 'Intentional error for testing'}), 500

@app.before_request
def before_request():
    ACTIVE_CONNECTIONS.inc()

@app.after_request
def after_request(response):
    ACTIVE_CONNECTIONS.dec()
    return response

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
```

**ファイル: apps/metrics-app/requirements.txt**
```
Flask==2.3.2
prometheus-client==0.17.1
```

**ファイル: apps/metrics-app/Dockerfile**
```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .

RUN adduser --disabled-password --gecos '' appuser
USER appuser

EXPOSE 5000

CMD ["python", "app.py"]
```

### 1.3 メトリクスアプリケーションのデプロイ

```bash
# イメージビルド
cd apps/metrics-app
docker build -t localhost:5000/metrics-app:v1.0 .
docker push localhost:5000/metrics-app:v1.0
cd ../../
```

**ファイル: apps/metrics-app-deployment.yaml**
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: metrics-app
  namespace: observability-demo
  labels:
    app: metrics-app
spec:
  replicas: 2
  selector:
    matchLabels:
      app: metrics-app
  template:
    metadata:
      labels:
        app: metrics-app
      annotations:
        prometheus.io/scrape: "true"
        prometheus.io/port: "5000"
        prometheus.io/path: "/metrics"
    spec:
      containers:
      - name: metrics-app
        image: localhost:5000/metrics-app:v1.0
        ports:
        - containerPort: 5000
        env:
        - name: SERVICE_VERSION
          value: "1.0.0"
        - name: ENVIRONMENT
          value: "development"
        resources:
          requests:
            memory: "64Mi"
            cpu: "125m"
          limits:
            memory: "128Mi"
            cpu: "250m"
        livenessProbe:
          httpGet:
            path: /health
            port: 5000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 5000
          initialDelaySeconds: 5
          periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: metrics-app
  namespace: observability-demo
  labels:
    app: metrics-app
spec:
  selector:
    app: metrics-app
  ports:
  - port: 5000
    targetPort: 5000
    nodePort: 30500
  type: NodePort
```

### 1.4 Prometheusとアプリケーションのデプロイ

```bash
# Prometheusデプロイ
kubectl apply -f monitoring/prometheus-config.yaml
kubectl apply -f monitoring/prometheus-deployment.yaml

# アプリケーションデプロイ
kubectl apply -f apps/metrics-app-deployment.yaml

# デプロイメント確認
kubectl get pods -n monitoring
kubectl get pods -n observability-demo

# Prometheus UI確認
echo "Prometheus UI: http://$(minikube ip):30090"
echo "Metrics App: http://$(minikube ip):30500"
```

---

## 📈 Exercise 2: Grafana による可視化

### 2.1 Grafana のデプロイ

**ファイル: monitoring/grafana-deployment.yaml**
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: grafana-datasources
  namespace: monitoring
data:
  datasource.yml: |
    apiVersion: 1
    datasources:
    - name: Prometheus
      type: prometheus
      access: proxy
      url: http://prometheus:9090
      isDefault: true
      editable: true
---
apiVersion: v1
kind: ConfigMap
metadata:
  name: grafana-dashboards-config
  namespace: monitoring
data:
  dashboard.yml: |
    apiVersion: 1
    providers:
    - name: 'default'
      orgId: 1
      folder: ''
      type: file
      disableDeletion: false
      updateIntervalSeconds: 10
      allowUiUpdates: true
      options:
        path: /var/lib/grafana/dashboards
---
apiVersion: v1
kind: ConfigMap
metadata:
  name: grafana-dashboard-app-metrics
  namespace: monitoring
data:
  app-metrics.json: |
    {
      "dashboard": {
        "id": null,
        "title": "Application Metrics",
        "tags": ["kubernetes", "monitoring"],
        "style": "dark",
        "timezone": "browser",
        "panels": [
          {
            "id": 1,
            "title": "Request Rate",
            "type": "graph",
            "targets": [
              {
                "expr": "rate(http_requests_total[5m])",
                "legendFormat": "{{method}} {{endpoint}}"
              }
            ],
            "xAxis": {"show": true},
            "yAxis": {"show": true, "label": "Requests/sec"},
            "legend": {"show": true}
          },
          {
            "id": 2,
            "title": "Response Time",
            "type": "graph",
            "targets": [
              {
                "expr": "histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))",
                "legendFormat": "95th percentile"
              },
              {
                "expr": "histogram_quantile(0.50, rate(http_request_duration_seconds_bucket[5m]))",
                "legendFormat": "50th percentile"
              }
            ],
            "yAxis": {"label": "Seconds"}
          },
          {
            "id": 3,
            "title": "Error Rate",
            "type": "stat",
            "targets": [
              {
                "expr": "rate(http_requests_total{status=~\"5..\"}[5m]) / rate(http_requests_total[5m]) * 100",
                "legendFormat": "Error Rate %"
              }
            ]
          }
        ],
        "time": {"from": "now-1h", "to": "now"},
        "refresh": "5s"
      }
    }
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: grafana
  namespace: monitoring
  labels:
    app: grafana
spec:
  replicas: 1
  selector:
    matchLabels:
      app: grafana
  template:
    metadata:
      labels:
        app: grafana
    spec:
      containers:
      - name: grafana
        image: grafana/grafana:10.0.0
        ports:
        - containerPort: 3000
        env:
        - name: GF_SECURITY_ADMIN_PASSWORD
          value: "admin123"
        - name: GF_USERS_ALLOW_SIGN_UP
          value: "false"
        volumeMounts:
        - name: grafana-datasources
          mountPath: /etc/grafana/provisioning/datasources
        - name: grafana-dashboards-config
          mountPath: /etc/grafana/provisioning/dashboards
        - name: grafana-dashboards
          mountPath: /var/lib/grafana/dashboards
        - name: grafana-storage
          mountPath: /var/lib/grafana
        resources:
          requests:
            memory: "100Mi"
            cpu: "100m"
          limits:
            memory: "200Mi"
            cpu: "200m"
      volumes:
      - name: grafana-datasources
        configMap:
          name: grafana-datasources
      - name: grafana-dashboards-config
        configMap:
          name: grafana-dashboards-config
      - name: grafana-dashboards
        configMap:
          name: grafana-dashboard-app-metrics
      - name: grafana-storage
        emptyDir: {}
---
apiVersion: v1
kind: Service
metadata:
  name: grafana
  namespace: monitoring
  labels:
    app: grafana
spec:
  selector:
    app: grafana
  ports:
  - port: 3000
    targetPort: 3000
    nodePort: 30300
  type: NodePort
```

```bash
# Grafanaデプロイ
kubectl apply -f monitoring/grafana-deployment.yaml

# Grafana確認
kubectl get pods -n monitoring
echo "Grafana UI: http://$(minikube ip):30300"
echo "Login: admin / admin123"
```

---

## 📝 Exercise 3: 構造化ログとログ管理

### 3.1 構造化ログアプリケーション

**ファイル: apps/logging-app/app.py**
```python
import json
import logging
import time
import uuid
from datetime import datetime
from flask import Flask, request, jsonify
import os

# 構造化ログ設定
class StructuredLogger:
    def __init__(self, service_name, version):
        self.service_name = service_name
        self.version = version
        self.logger = logging.getLogger(service_name)
        self.logger.setLevel(logging.INFO)
        
        # コンソールハンドラー設定
        handler = logging.StreamHandler()
        handler.setFormatter(self.JsonFormatter())
        self.logger.addHandler(handler)
    
    class JsonFormatter(logging.Formatter):
        def format(self, record):
            log_entry = {
                'timestamp': datetime.utcnow().isoformat() + 'Z',
                'level': record.levelname,
                'message': record.getMessage(),
                'logger': record.name,
                'module': record.module,
                'function': record.funcName,
                'line': record.lineno
            }
            
            # 追加属性があれば含める
            if hasattr(record, 'trace_id'):
                log_entry['trace_id'] = record.trace_id
            if hasattr(record, 'span_id'):
                log_entry['span_id'] = record.span_id
            if hasattr(record, 'user_id'):
                log_entry['user_id'] = record.user_id
            if hasattr(record, 'request_id'):
                log_entry['request_id'] = record.request_id
            if hasattr(record, 'duration'):
                log_entry['duration_ms'] = record.duration
            
            return json.dumps(log_entry)
    
    def info(self, message, **kwargs):
        self.logger.info(message, extra=kwargs)
    
    def warning(self, message, **kwargs):
        self.logger.warning(message, extra=kwargs)
    
    def error(self, message, **kwargs):
        self.logger.error(message, extra=kwargs)
    
    def debug(self, message, **kwargs):
        self.logger.debug(message, extra=kwargs)

app = Flask(__name__)

# 構造化ログインスタンス
logger = StructuredLogger(
    service_name=os.getenv('SERVICE_NAME', 'logging-app'),
    version=os.getenv('SERVICE_VERSION', '1.0.0')
)

@app.before_request
def before_request():
    # リクエストIDの生成
    request.request_id = str(uuid.uuid4())
    request.start_time = time.time()
    
    logger.info(
        "Request started",
        request_id=request.request_id,
        method=request.method,
        path=request.path,
        remote_addr=request.remote_addr,
        user_agent=request.headers.get('User-Agent', '')
    )

@app.after_request
def after_request(response):
    duration = (time.time() - request.start_time) * 1000
    
    logger.info(
        "Request completed",
        request_id=request.request_id,
        method=request.method,
        path=request.path,
        status_code=response.status_code,
        duration_ms=round(duration, 2)
    )
    
    return response

@app.route('/health')
def health():
    logger.info("Health check requested", request_id=request.request_id)
    return jsonify({'status': 'healthy'})

@app.route('/api/process')
def process_data():
    try:
        # 処理開始ログ
        logger.info("Starting data processing", request_id=request.request_id)
        
        # 模擬処理
        processing_time = 0.5
        time.sleep(processing_time)
        
        # 処理完了ログ
        logger.info(
            "Data processing completed",
            request_id=request.request_id,
            processing_time_ms=processing_time * 1000
        )
        
        return jsonify({
            'status': 'success',
            'request_id': request.request_id,
            'data': 'Processed data'
        })
        
    except Exception as e:
        logger.error(
            "Data processing failed",
            request_id=request.request_id,
            error=str(e),
            error_type=type(e).__name__
        )
        return jsonify({'error': 'Processing failed'}), 500

@app.route('/api/user/<user_id>/action')
def user_action(user_id):
    try:
        logger.info(
            "User action started",
            request_id=request.request_id,
            user_id=user_id,
            action='data_access'
        )
        
        # ユーザー検証の模擬
        if user_id == 'invalid':
            logger.warning(
                "Invalid user access attempt",
                request_id=request.request_id,
                user_id=user_id
            )
            return jsonify({'error': 'Invalid user'}), 400
        
        # 正常処理
        result = {
            'user_id': user_id,
            'action': 'completed',
            'timestamp': datetime.utcnow().isoformat()
        }
        
        logger.info(
            "User action completed",
            request_id=request.request_id,
            user_id=user_id,
            action='data_access'
        )
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(
            "User action failed",
            request_id=request.request_id,
            user_id=user_id,
            error=str(e)
        )
        return jsonify({'error': 'Action failed'}), 500

@app.route('/api/simulate-error')
def simulate_error():
    logger.error(
        "Simulated error occurred",
        request_id=request.request_id,
        error_type="SimulatedError",
        severity="high"
    )
    return jsonify({'error': 'Simulated error for testing'}), 500

if __name__ == '__main__':
    logger.info("Application starting", service_version=os.getenv('SERVICE_VERSION', '1.0.0'))
    app.run(host='0.0.0.0', port=5001)
```

### 3.2 ログアプリケーションのデプロイ

```bash
# イメージビルド
cd apps
mkdir -p logging-app
cd logging-app
# app.pyファイルを作成
cp ../metrics-app/requirements.txt .
echo "Flask==2.3.2" > requirements.txt

cat > Dockerfile << 'EOF'
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .

RUN adduser --disabled-password --gecos '' appuser
USER appuser

EXPOSE 5001

CMD ["python", "app.py"]
EOF

docker build -t localhost:5000/logging-app:v1.0 .
docker push localhost:5000/logging-app:v1.0
cd ../../
```

**ファイル: apps/logging-app-deployment.yaml**
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: logging-app
  namespace: observability-demo
  labels:
    app: logging-app
spec:
  replicas: 2
  selector:
    matchLabels:
      app: logging-app
  template:
    metadata:
      labels:
        app: logging-app
    spec:
      containers:
      - name: logging-app
        image: localhost:5000/logging-app:v1.0
        ports:
        - containerPort: 5001
        env:
        - name: SERVICE_NAME
          value: "logging-app"
        - name: SERVICE_VERSION
          value: "1.0.0"
        resources:
          requests:
            memory: "64Mi"
            cpu: "125m"
          limits:
            memory: "128Mi"
            cpu: "250m"
---
apiVersion: v1
kind: Service
metadata:
  name: logging-app
  namespace: observability-demo
  labels:
    app: logging-app
spec:
  selector:
    app: logging-app
  ports:
  - port: 5001
    targetPort: 5001
    nodePort: 30501
  type: NodePort
```

```bash
# デプロイ実行
kubectl apply -f apps/logging-app-deployment.yaml

# ログアプリケーション確認
kubectl get pods -n observability-demo
echo "Logging App: http://$(minikube ip):30501"
```

---

## 🔍 Exercise 4: 分散トレーシング（Jaeger）

### 4.1 Jaeger のデプロイ

**ファイル: monitoring/jaeger-deployment.yaml**
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: jaeger
  namespace: monitoring
  labels:
    app: jaeger
spec:
  replicas: 1
  selector:
    matchLabels:
      app: jaeger
  template:
    metadata:
      labels:
        app: jaeger
    spec:
      containers:
      - name: jaeger
        image: jaegertracing/all-in-one:1.47
        ports:
        - containerPort: 16686  # UI
        - containerPort: 14268  # HTTP collector
        - containerPort: 6831   # UDP jaeger.thrift
        - containerPort: 6832   # UDP jaeger.thrift binary
        env:
        - name: COLLECTOR_OTLP_ENABLED
          value: "true"
        - name: COLLECTOR_ZIPKIN_HOST_PORT
          value: ":9411"
        resources:
          requests:
            memory: "100Mi"
            cpu: "100m"
          limits:
            memory: "300Mi"
            cpu: "300m"
---
apiVersion: v1
kind: Service
metadata:
  name: jaeger
  namespace: monitoring
  labels:
    app: jaeger
spec:
  selector:
    app: jaeger
  ports:
  - name: ui
    port: 16686
    targetPort: 16686
    nodePort: 30686
  - name: collector
    port: 14268
    targetPort: 14268
  - name: agent-binary
    port: 6832
    targetPort: 6832
    protocol: UDP
  - name: agent-compact
    port: 6831
    targetPort: 6831
    protocol: UDP
  type: NodePort
```

### 4.2 トレーシング対応アプリケーション

**ファイル: apps/tracing-app/app.py**
```python
import os
import time
import random
import requests
from flask import Flask, jsonify, request
from jaeger_client import Config
from opentracing.propagation import Format
from opentracing.ext import tags
import opentracing

app = Flask(__name__)

# Jaeger設定
def init_tracer(service):
    config = Config(
        config={
            'sampler': {
                'type': 'const',
                'param': 1,
            },
            'logging': True,
            'local_agent': {
                'reporting_host': os.getenv('JAEGER_AGENT_HOST', 'jaeger'),
                'reporting_port': int(os.getenv('JAEGER_AGENT_PORT', '6831')),
            }
        },
        service_name=service,
    )
    return config.initialize_tracer()

tracer = init_tracer('tracing-app')

def trace_request(operation_name):
    """リクエストトレーシングデコレータ"""
    def decorator(f):
        def wrapper(*args, **kwargs):
            # 親スパンの抽出
            span_ctx = tracer.extract(
                Format.HTTP_HEADERS,
                dict(request.headers)
            )
            
            # 新しいスパン開始
            with tracer.start_span(
                operation_name,
                child_of=span_ctx
            ) as span:
                # HTTPタグ設定
                span.set_tag(tags.HTTP_METHOD, request.method)
                span.set_tag(tags.HTTP_URL, request.url)
                span.set_tag(tags.COMPONENT, 'flask')
                span.set_tag('service.name', 'tracing-app')
                
                try:
                    result = f(span, *args, **kwargs)
                    span.set_tag(tags.HTTP_STATUS_CODE, 200)
                    return result
                except Exception as e:
                    span.set_tag(tags.ERROR, True)
                    span.set_tag(tags.HTTP_STATUS_CODE, 500)
                    span.log_kv({'error': str(e)})
                    raise e
        
        wrapper.__name__ = f.__name__
        return wrapper
    return decorator

def make_traced_request(url, span, operation_name):
    """トレース情報を伝播する外部リクエスト"""
    headers = {}
    
    # スパンコンテキストをHTTPヘッダーに注入
    tracer.inject(
        span_context=span.context,
        format=Format.HTTP_HEADERS,
        carrier=headers
    )
    
    with tracer.start_span(operation_name, child_of=span) as child_span:
        child_span.set_tag(tags.HTTP_METHOD, 'GET')
        child_span.set_tag(tags.HTTP_URL, url)
        child_span.set_tag(tags.SPAN_KIND, tags.SPAN_KIND_RPC_CLIENT)
        
        try:
            response = requests.get(url, headers=headers, timeout=5)
            child_span.set_tag(tags.HTTP_STATUS_CODE, response.status_code)
            return response
        except Exception as e:
            child_span.set_tag(tags.ERROR, True)
            child_span.log_kv({'error': str(e)})
            raise e

@app.route('/health')
@trace_request('health-check')
def health(span):
    span.set_tag('health.status', 'ok')
    return jsonify({'status': 'healthy'})

@app.route('/api/chain')
@trace_request('service-chain')
def service_chain(span):
    """複数サービスの呼び出しチェーン"""
    results = []
    
    # データベース操作の模擬
    with tracer.start_span('database-query', child_of=span) as db_span:
        db_span.set_tag('db.type', 'postgresql')
        db_span.set_tag('db.statement', 'SELECT * FROM users')
        time.sleep(random.uniform(0.1, 0.3))
        results.append('db_data')
    
    # 外部API呼び出しの模擬
    with tracer.start_span('external-api-call', child_of=span) as api_span:
        api_span.set_tag(tags.SPAN_KIND, tags.SPAN_KIND_RPC_CLIENT)
        api_span.set_tag('api.name', 'user-service')
        
        # ランダムで成功/失敗
        if random.random() > 0.8:
            api_span.set_tag(tags.ERROR, True)
            api_span.log_kv({'error': 'External API timeout'})
            results.append('api_error')
        else:
            time.sleep(random.uniform(0.2, 0.5))
            results.append('api_data')
    
    # キャッシュアクセスの模擬
    with tracer.start_span('cache-access', child_of=span) as cache_span:
        cache_span.set_tag('cache.type', 'redis')
        cache_span.set_tag('cache.key', 'user:123')
        
        if random.random() > 0.7:  # キャッシュミス
            cache_span.set_tag('cache.hit', False)
            time.sleep(0.05)
        else:  # キャッシュヒット
            cache_span.set_tag('cache.hit', True)
            time.sleep(0.01)
        
        results.append('cache_data')
    
    span.set_tag('results.count', len(results))
    span.log_kv({'operation': 'service-chain', 'results': results})
    
    return jsonify({
        'results': results,
        'trace_id': f"{span.context.trace_id:x}",
        'span_id': f"{span.context.span_id:x}"
    })

@app.route('/api/distributed')
@trace_request('distributed-call')
def distributed_call(span):
    """他のサービスを呼び出す分散処理"""
    try:
        # logging-appを呼び出し
        logging_url = 'http://logging-app:5001/api/process'
        logging_response = make_traced_request(logging_url, span, 'call-logging-service')
        
        span.log_kv({'logging_service': 'success'})
        
        return jsonify({
            'status': 'success',
            'logging_service': logging_response.json() if logging_response.status_code == 200 else 'error',
            'trace_id': f"{span.context.trace_id:x}"
        })
        
    except Exception as e:
        span.set_tag(tags.ERROR, True)
        span.log_kv({'error': str(e)})
        return jsonify({'error': 'Distributed call failed'}), 500

@app.route('/api/error')
@trace_request('error-simulation')
def error_simulation(span):
    """エラー発生の模擬"""
    span.set_tag('test.type', 'error_simulation')
    
    error_type = random.choice(['timeout', 'invalid_data', 'service_unavailable'])
    span.set_tag('error.type', error_type)
    
    if error_type == 'timeout':
        time.sleep(2)  # タイムアウト模擬
        span.log_kv({'error': 'Operation timeout'})
    elif error_type == 'invalid_data':
        span.log_kv({'error': 'Invalid input data', 'data': 'malformed_json'})
    else:
        span.log_kv({'error': 'Service unavailable', 'service': 'external_api'})
    
    span.set_tag(tags.ERROR, True)
    return jsonify({'error': f'Simulated {error_type} error'}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5002)
```

### 4.3 トレーシングアプリケーションのデプロイ

```bash
# 必要な依存関係ファイル作成
cd apps
mkdir -p tracing-app
cd tracing-app

cat > requirements.txt << 'EOF'
Flask==2.3.2
jaeger-client==4.8.0
opentracing==2.4.0
requests==2.31.0
EOF

cat > Dockerfile << 'EOF'
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .

RUN adduser --disabled-password --gecos '' appuser
USER appuser

EXPOSE 5002

CMD ["python", "app.py"]
EOF

docker build -t localhost:5000/tracing-app:v1.0 .
docker push localhost:5000/tracing-app:v1.0
cd ../../
```

**ファイル: apps/tracing-app-deployment.yaml**
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: tracing-app
  namespace: observability-demo
  labels:
    app: tracing-app
spec:
  replicas: 2
  selector:
    matchLabels:
      app: tracing-app
  template:
    metadata:
      labels:
        app: tracing-app
    spec:
      containers:
      - name: tracing-app
        image: localhost:5000/tracing-app:v1.0
        ports:
        - containerPort: 5002
        env:
        - name: JAEGER_AGENT_HOST
          value: "jaeger.monitoring.svc.cluster.local"
        - name: JAEGER_AGENT_PORT
          value: "6831"
        resources:
          requests:
            memory: "64Mi"
            cpu: "125m"
          limits:
            memory: "128Mi"
            cpu: "250m"
---
apiVersion: v1
kind: Service
metadata:
  name: tracing-app
  namespace: observability-demo
  labels:
    app: tracing-app
spec:
  selector:
    app: tracing-app
  ports:
  - port: 5002
    targetPort: 5002
    nodePort: 30502
  type: NodePort
```

```bash
# Jaegerとトレーシングアプリのデプロイ
kubectl apply -f monitoring/jaeger-deployment.yaml
kubectl apply -f apps/tracing-app-deployment.yaml

# 確認
kubectl get pods -n monitoring
kubectl get pods -n observability-demo

echo "Jaeger UI: http://$(minikube ip):30686"
echo "Tracing App: http://$(minikube ip):30502"
```

---

## ⚠️ Exercise 5: アラートとSLI/SLO

### 5.1 AlertManager の設定

**ファイル: monitoring/alertmanager-config.yaml**
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: alertmanager-config
  namespace: monitoring
data:
  alertmanager.yml: |
    global:
      smtp_smarthost: 'localhost:587'
      smtp_from: 'alertmanager@company.com'
    
    route:
      group_by: ['alertname']
      group_wait: 10s
      group_interval: 10s
      repeat_interval: 1h
      receiver: 'web.hook'
    
    receivers:
    - name: 'web.hook'
      webhook_configs:
      - url: 'http://webhook-receiver:5003/webhook'
        send_resolved: true
        http_config:
          basic_auth:
            username: 'admin'
            password: 'password'
        title: 'Alert: {{ .GroupLabels.alertname }}'
        text: |
          {{ range .Alerts }}
          Alert: {{ .Annotations.summary }}
          Description: {{ .Annotations.description }}
          Status: {{ .Status }}
          {{ end }}
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: alertmanager
  namespace: monitoring
  labels:
    app: alertmanager
spec:
  replicas: 1
  selector:
    matchLabels:
      app: alertmanager
  template:
    metadata:
      labels:
        app: alertmanager
    spec:
      containers:
      - name: alertmanager
        image: prom/alertmanager:v0.25.0
        args:
          - '--config.file=/etc/alertmanager/alertmanager.yml'
          - '--storage.path=/alertmanager'
          - '--web.external-url=http://localhost:9093'
        ports:
        - containerPort: 9093
        volumeMounts:
        - name: alertmanager-config
          mountPath: /etc/alertmanager
        - name: alertmanager-storage
          mountPath: /alertmanager
        resources:
          requests:
            memory: "100Mi"
            cpu: "100m"
          limits:
            memory: "200Mi"
            cpu: "200m"
      volumes:
      - name: alertmanager-config
        configMap:
          name: alertmanager-config
      - name: alertmanager-storage
        emptyDir: {}
---
apiVersion: v1
kind: Service
metadata:
  name: alertmanager
  namespace: monitoring
  labels:
    app: alertmanager
spec:
  selector:
    app: alertmanager
  ports:
  - port: 9093
    targetPort: 9093
    nodePort: 30093
  type: NodePort
```

### 5.2 SLI/SLO ダッシュボード

**ファイル: monitoring/sli-slo-dashboard.yaml**
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: sli-slo-dashboard
  namespace: monitoring
data:
  sli-slo.json: |
    {
      "dashboard": {
        "id": null,
        "title": "SLI/SLO Dashboard",
        "tags": ["sli", "slo", "reliability"],
        "style": "dark",
        "timezone": "browser",
        "panels": [
          {
            "id": 1,
            "title": "Availability SLI",
            "type": "stat",
            "targets": [
              {
                "expr": "(1 - (rate(http_requests_total{status=~\"5..\"}[5m]) / rate(http_requests_total[5m]))) * 100",
                "legendFormat": "Availability %"
              }
            ],
            "fieldConfig": {
              "defaults": {
                "unit": "percent",
                "min": 95,
                "max": 100,
                "thresholds": {
                  "steps": [
                    {"color": "red", "value": 95},
                    {"color": "yellow", "value": 99},
                    {"color": "green", "value": 99.9}
                  ]
                }
              }
            }
          },
          {
            "id": 2,
            "title": "Latency SLI (95th percentile)",
            "type": "stat",
            "targets": [
              {
                "expr": "histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) * 1000",
                "legendFormat": "95th percentile latency"
              }
            ],
            "fieldConfig": {
              "defaults": {
                "unit": "ms",
                "thresholds": {
                  "steps": [
                    {"color": "green", "value": 0},
                    {"color": "yellow", "value": 500},
                    {"color": "red", "value": 1000}
                  ]
                }
              }
            }
          },
          {
            "id": 3,
            "title": "Error Budget Remaining",
            "type": "gauge",
            "targets": [
              {
                "expr": "100 - ((rate(http_requests_total{status=~\"5..\"}[30d]) / rate(http_requests_total[30d])) * 100 / 0.1) * 100",
                "legendFormat": "Error Budget %"
              }
            ],
            "fieldConfig": {
              "defaults": {
                "unit": "percent",
                "min": 0,
                "max": 100
              }
            }
          }
        ],
        "time": {"from": "now-1h", "to": "now"},
        "refresh": "30s"
      }
    }
```

---

## 🧪 Exercise 6: 統合テストとシナリオ実行

### 6.1 負荷生成とテストシナリオ

```bash
# 負荷生成スクリプト作成
cat > load-test.sh << 'EOF'
#!/bin/bash

METRICS_APP_URL="http://$(minikube ip):30500"
LOGGING_APP_URL="http://$(minikube ip):30501"
TRACING_APP_URL="http://$(minikube ip):30502"

echo "Starting load test..."

# 正常なリクエスト
for i in {1..50}; do
  curl -s "$METRICS_APP_URL/api/data" > /dev/null &
  curl -s "$LOGGING_APP_URL/api/process" > /dev/null &
  curl -s "$TRACING_APP_URL/api/chain" > /dev/null &
  
  # 一部エラーリクエスト
  if [ $((i % 10)) -eq 0 ]; then
    curl -s "$METRICS_APP_URL/api/error" > /dev/null &
    curl -s "$LOGGING_APP_URL/api/simulate-error" > /dev/null &
    curl -s "$TRACING_APP_URL/api/error" > /dev/null &
  fi
  
  sleep 0.1
done

wait
echo "Load test completed"
EOF

chmod +x load-test.sh
```

### 6.2 監視データの確認

```bash
# アラートマネージャーデプロイ
kubectl apply -f monitoring/alertmanager-config.yaml

# 全体状況確認
kubectl get pods -n monitoring
kubectl get pods -n observability-demo

echo "=== 監視システムアクセス ==="
echo "Prometheus: http://$(minikube ip):30090"
echo "Grafana: http://$(minikube ip):30300 (admin/admin123)"
echo "Jaeger: http://$(minikube ip):30686"
echo "AlertManager: http://$(minikube ip):30093"

echo ""
echo "=== アプリケーションアクセス ==="
echo "Metrics App: http://$(minikube ip):30500"
echo "Logging App: http://$(minikube ip):30501"
echo "Tracing App: http://$(minikube ip):30502"

# 負荷テスト実行
./load-test.sh
```

### 6.3 可観測性データの分析

```bash
# ログの確認
echo "=== Structured Logs ==="
kubectl logs -n observability-demo deployment/logging-app | tail -5

# メトリクスの確認
echo "=== Metrics Endpoint ==="
curl "http://$(minikube ip):30500/metrics" | grep -E "(http_requests_total|http_request_duration)"

# トレースの確認（Jaeger UIで確認）
echo "=== 分散トレーシング ==="
echo "Jaeger UIでトレースを確認: http://$(minikube ip):30686"
echo "Service: tracing-app"
echo "Operation: service-chain"
```

---

## 🧹 リソースクリーンアップ

```bash
# namespace削除
kubectl delete namespace monitoring
kubectl delete namespace observability-demo

# Dockerイメージクリーンアップ
docker rmi localhost:5000/metrics-app:v1.0
docker rmi localhost:5000/logging-app:v1.0
docker rmi localhost:5000/tracing-app:v1.0

# 作業ディレクトリクリーンアップ
cd ~
rm -rf ~/kcna-lab04
```

---

## 📚 復習課題

### 総合演習

以下の要件を満たすエンドツーエンド可観測性システムを構築してください：

1. **メトリクス**: カスタムビジネスメトリクスの実装
2. **ログ**: 構造化ログとコンテキスト伝播
3. **トレース**: マルチサービス分散トレーシング
4. **ダッシュボード**: SLI/SLOベースの監視
5. **アラート**: 障害予兆検知とエスカレーション

### チェックリスト

このラボ完了後、以下ができることを確認してください：

- [ ] 可観測性の3つの柱の理解と実装
- [ ] Prometheusメトリクス設計と収集
- [ ] Grafanaダッシュボード作成と可視化
- [ ] 構造化ログの実装とコンテキスト管理
- [ ] Jaeger分散トレーシングの設定
- [ ] アラートルールの作成と通知設定
- [ ] SLI/SLO設計と監視
- [ ] パフォーマンス問題の特定と分析
- [ ] 障害対応とトラブルシューティング
- [ ] 監視データの相関分析

---

## 🎯 次のステップ

### 高度なトピック

1. **OpenTelemetry**: 統一的な可観測性計装
2. **Distributed Tracing**: 複雑なマイクロサービス追跡
3. **AIOps**: 機械学習による異常検知
4. **Chaos Engineering**: 障害耐性テスト
5. **Site Reliability Engineering**: SRE実践

### 実践的学習

- ELKスタック（Elasticsearch/Logstash/Kibana）による統合ログ管理
- OpenTelemetryによる統一計装
- Chaos Monkey等を使用した障害テスト
- 本格的なSLI/SLO運用

### 参考資料

- [Prometheus Documentation](https://prometheus.io/docs/)
- [Grafana Documentation](https://grafana.com/docs/)
- [Jaeger Documentation](https://www.jaegertracing.io/docs/)
- [OpenTelemetry](https://opentelemetry.io/)

---

**重要**: このラボはKCNA-JP試験のクラウドネイティブ可観測性ドメイン（8%）をカバーしています。3つの柱（Metrics、Logs、Traces）を実際に実装・操作することで、現代的な監視とトラブルシューティングの手法を身につけることができます。