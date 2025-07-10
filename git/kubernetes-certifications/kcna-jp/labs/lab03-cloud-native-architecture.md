# Lab 03: クラウドネイティブアーキテクチャ

## 📋 ラボ概要

**目的**: クラウドネイティブアーキテクチャの理解、マイクロサービス設計、12ファクターアプリケーション実装、サービスメッシュ基礎  
**所要時間**: 150-180分  
**前提条件**: Lab 01, 02完了、基本的なAPI設計知識  
**使用環境**: Kubernetes、minikube、kubectl、Docker

---

## 🎯 学習目標

このラボ完了後、以下ができるようになります：

1. 12ファクターアプリケーションの設計と実装
2. マイクロサービスアーキテクチャの構築
3. API-First設計の実践
4. サービス間通信パターンの実装
5. 設定管理とシークレット管理のベストプラクティス
6. サービスディスカバリーとロードバランシング
7. Circuit Breakerパターンの理解
8. Event-Driven Architectureの基礎

---

## 🛠️ 事前準備

### 環境確認とセットアップ

```bash
# 作業ディレクトリ作成
mkdir -p ~/kcna-lab03/{microservices,configs,manifests}
cd ~/kcna-lab03

# Kubernetes環境確認
kubectl cluster-info
kubectl get nodes

# 名前空間作成
kubectl create namespace cloudnative-demo
kubectl config set-context --current --namespace=cloudnative-demo
```

---

## 📜 Exercise 1: 12ファクターアプリケーションの実装

### 1.1 12ファクター準拠のマイクロサービス作成

**ファイル: microservices/user-service/app.py**
```python
import os
import json
import logging
from flask import Flask, jsonify, request
import requests
from datetime import datetime

# ログ設定（Factor XII: ログ）
logging.basicConfig(
    level=os.getenv('LOG_LEVEL', 'INFO'),
    format='{"timestamp": "%(asctime)s", "level": "%(levelname)s", "message": "%(message)s"}'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Factor III: 設定 - 環境変数から設定を読み込み
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///users.db')
SERVICE_NAME = os.getenv('SERVICE_NAME', 'user-service')
SERVICE_VERSION = os.getenv('SERVICE_VERSION', '1.0.0')
PORT = int(os.getenv('PORT', 5000))

# Factor XI: ログ - 構造化ログ
def log_request(endpoint, method, status_code):
    logger.info(json.dumps({
        'service': SERVICE_NAME,
        'endpoint': endpoint,
        'method': method,
        'status_code': status_code,
        'timestamp': datetime.utcnow().isoformat()
    }))

# 簡易ユーザーデータ（Factor IV: バッキングサービス）
users_db = {
    '1': {'id': '1', 'name': 'Alice', 'email': 'alice@example.com'},
    '2': {'id': '2', 'name': 'Bob', 'email': 'bob@example.com'}
}

@app.route('/health')
def health_check():
    """Factor VIII: 並行性 - プロセス管理のヘルスチェック"""
    log_request('/health', 'GET', 200)
    return jsonify({
        'status': 'healthy',
        'service': SERVICE_NAME,
        'version': SERVICE_VERSION,
        'timestamp': datetime.utcnow().isoformat()
    })

@app.route('/users', methods=['GET'])
def get_users():
    """全ユーザー取得"""
    log_request('/users', 'GET', 200)
    return jsonify(list(users_db.values()))

@app.route('/users/<user_id>', methods=['GET'])
def get_user(user_id):
    """特定ユーザー取得"""
    if user_id in users_db:
        log_request(f'/users/{user_id}', 'GET', 200)
        return jsonify(users_db[user_id])
    else:
        log_request(f'/users/{user_id}', 'GET', 404)
        return jsonify({'error': 'User not found'}), 404

@app.route('/users', methods=['POST'])
def create_user():
    """Factor VI: プロセス - ステートレス処理"""
    data = request.get_json()
    user_id = str(len(users_db) + 1)
    new_user = {
        'id': user_id,
        'name': data.get('name'),
        'email': data.get('email')
    }
    users_db[user_id] = new_user
    log_request('/users', 'POST', 201)
    return jsonify(new_user), 201

# Factor IX: 可処分性 - グレースフルシャットダウン
if __name__ == '__main__':
    logger.info(f"Starting {SERVICE_NAME} v{SERVICE_VERSION} on port {PORT}")
    app.run(host='0.0.0.0', port=PORT, debug=False)
```

**ファイル: microservices/user-service/requirements.txt**
```
Flask==2.3.2
requests==2.31.0
```

**ファイル: microservices/user-service/Dockerfile**
```dockerfile
# Factor II: 依存関係 - 明示的に宣言
FROM python:3.9-slim

WORKDIR /app

# Factor V: ビルド、リリース、実行の分離
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .

# Factor XII: 管理プロセス - 非rootユーザーで実行
RUN adduser --disabled-password --gecos '' appuser
USER appuser

# Factor VII: ポートバインディング
EXPOSE 5000

CMD ["python", "app.py"]
```

### 1.2 注文サービス（Order Service）の作成

**ファイル: microservices/order-service/app.py**
```python
import os
import json
import logging
from flask import Flask, jsonify, request
import requests
from datetime import datetime
import uuid

logging.basicConfig(
    level=os.getenv('LOG_LEVEL', 'INFO'),
    format='{"timestamp": "%(asctime)s", "level": "%(levelname)s", "message": "%(message)s"}'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

SERVICE_NAME = os.getenv('SERVICE_NAME', 'order-service')
SERVICE_VERSION = os.getenv('SERVICE_VERSION', '1.0.0')
PORT = int(os.getenv('PORT', 5001))
USER_SERVICE_URL = os.getenv('USER_SERVICE_URL', 'http://user-service:5000')

# 簡易注文データ
orders_db = {}

def log_request(endpoint, method, status_code):
    logger.info(json.dumps({
        'service': SERVICE_NAME,
        'endpoint': endpoint,
        'method': method,
        'status_code': status_code,
        'timestamp': datetime.utcnow().isoformat()
    }))

@app.route('/health')
def health_check():
    return jsonify({
        'status': 'healthy',
        'service': SERVICE_NAME,
        'version': SERVICE_VERSION,
        'dependencies': {
            'user-service': USER_SERVICE_URL
        }
    })

@app.route('/orders', methods=['GET'])
def get_orders():
    log_request('/orders', 'GET', 200)
    return jsonify(list(orders_db.values()))

@app.route('/orders', methods=['POST'])
def create_order():
    data = request.get_json()
    user_id = data.get('user_id')
    
    # Factor IV: バッキングサービス - 外部サービス呼び出し
    try:
        user_response = requests.get(f"{USER_SERVICE_URL}/users/{user_id}", timeout=5)
        if user_response.status_code != 200:
            log_request('/orders', 'POST', 400)
            return jsonify({'error': 'Invalid user'}), 400
            
        user_data = user_response.json()
    except requests.RequestException as e:
        logger.error(f"Failed to fetch user data: {str(e)}")
        log_request('/orders', 'POST', 503)
        return jsonify({'error': 'User service unavailable'}), 503
    
    order_id = str(uuid.uuid4())
    order = {
        'id': order_id,
        'user_id': user_id,
        'user_name': user_data['name'],
        'items': data.get('items', []),
        'total': data.get('total', 0),
        'status': 'pending',
        'created_at': datetime.utcnow().isoformat()
    }
    
    orders_db[order_id] = order
    log_request('/orders', 'POST', 201)
    return jsonify(order), 201

@app.route('/orders/<order_id>', methods=['GET'])
def get_order(order_id):
    if order_id in orders_db:
        log_request(f'/orders/{order_id}', 'GET', 200)
        return jsonify(orders_db[order_id])
    else:
        log_request(f'/orders/{order_id}', 'GET', 404)
        return jsonify({'error': 'Order not found'}), 404

if __name__ == '__main__':
    logger.info(f"Starting {SERVICE_NAME} v{SERVICE_VERSION} on port {PORT}")
    app.run(host='0.0.0.0', port=PORT, debug=False)
```

### 1.3 イメージビルドとレジストリ準備

```bash
# ローカルレジストリ起動（ない場合）
docker run -d -p 5000:5000 --name local-registry registry:2

# ユーザーサービスビルド
cd microservices/user-service
docker build -t localhost:5000/user-service:v1.0 .
docker push localhost:5000/user-service:v1.0

# 注文サービスビルド
cd ../order-service
cp ../user-service/requirements.txt .
docker build -t localhost:5000/order-service:v1.0 .
docker push localhost:5000/order-service:v1.0

cd ../../
```

---

## 🏗️ Exercise 2: マイクロサービスのKubernetesデプロイメント

### 2.1 設定管理（Factor III: 設定）

**ファイル: manifests/configmap.yaml**
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: microservices-config
  namespace: cloudnative-demo
data:
  # 共通設定
  LOG_LEVEL: "INFO"
  
  # ユーザーサービス設定
  USER_SERVICE_NAME: "user-service"
  USER_SERVICE_VERSION: "1.0.0"
  USER_SERVICE_PORT: "5000"
  
  # 注文サービス設定
  ORDER_SERVICE_NAME: "order-service"
  ORDER_SERVICE_VERSION: "1.0.0"
  ORDER_SERVICE_PORT: "5001"
  USER_SERVICE_URL: "http://user-service:5000"
---
apiVersion: v1
kind: Secret
metadata:
  name: microservices-secrets
  namespace: cloudnative-demo
type: Opaque
data:
  # base64エンコードされた値
  DATABASE_PASSWORD: cGFzc3dvcmQxMjM=  # password123
  API_KEY: YWJjZGVmZ2hpams=  # abcdefghijk
```

### 2.2 ユーザーサービスデプロイメント

**ファイル: manifests/user-service.yaml**
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: user-service
  namespace: cloudnative-demo
  labels:
    app: user-service
    tier: backend
    version: v1.0
spec:
  replicas: 2
  selector:
    matchLabels:
      app: user-service
  template:
    metadata:
      labels:
        app: user-service
        tier: backend
        version: v1.0
    spec:
      containers:
      - name: user-service
        image: localhost:5000/user-service:v1.0
        ports:
        - containerPort: 5000
        env:
        - name: SERVICE_NAME
          valueFrom:
            configMapKeyRef:
              name: microservices-config
              key: USER_SERVICE_NAME
        - name: SERVICE_VERSION
          valueFrom:
            configMapKeyRef:
              name: microservices-config
              key: USER_SERVICE_VERSION
        - name: PORT
          valueFrom:
            configMapKeyRef:
              name: microservices-config
              key: USER_SERVICE_PORT
        - name: LOG_LEVEL
          valueFrom:
            configMapKeyRef:
              name: microservices-config
              key: LOG_LEVEL
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
  name: user-service
  namespace: cloudnative-demo
  labels:
    app: user-service
spec:
  selector:
    app: user-service
  ports:
  - protocol: TCP
    port: 5000
    targetPort: 5000
  type: ClusterIP
```

### 2.3 注文サービスデプロイメント

**ファイル: manifests/order-service.yaml**
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: order-service
  namespace: cloudnative-demo
  labels:
    app: order-service
    tier: backend
    version: v1.0
spec:
  replicas: 2
  selector:
    matchLabels:
      app: order-service
  template:
    metadata:
      labels:
        app: order-service
        tier: backend
        version: v1.0
    spec:
      containers:
      - name: order-service
        image: localhost:5000/order-service:v1.0
        ports:
        - containerPort: 5001
        env:
        - name: SERVICE_NAME
          valueFrom:
            configMapKeyRef:
              name: microservices-config
              key: ORDER_SERVICE_NAME
        - name: SERVICE_VERSION
          valueFrom:
            configMapKeyRef:
              name: microservices-config
              key: ORDER_SERVICE_VERSION
        - name: PORT
          valueFrom:
            configMapKeyRef:
              name: microservices-config
              key: ORDER_SERVICE_PORT
        - name: USER_SERVICE_URL
          valueFrom:
            configMapKeyRef:
              name: microservices-config
              key: USER_SERVICE_URL
        - name: LOG_LEVEL
          valueFrom:
            configMapKeyRef:
              name: microservices-config
              key: LOG_LEVEL
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
            port: 5001
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 5001
          initialDelaySeconds: 5
          periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: order-service
  namespace: cloudnative-demo
  labels:
    app: order-service
spec:
  selector:
    app: order-service
  ports:
  - protocol: TCP
    port: 5001
    targetPort: 5001
  type: ClusterIP
```

### 2.4 デプロイメント実行

```bash
# 設定とシークレット適用
kubectl apply -f manifests/configmap.yaml

# サービスデプロイメント
kubectl apply -f manifests/user-service.yaml
kubectl apply -f manifests/order-service.yaml

# デプロイメント確認
kubectl get pods -n cloudnative-demo
kubectl get services -n cloudnative-demo

# ヘルスチェック
kubectl get pods -n cloudnative-demo -w
```

---

## 🌐 Exercise 3: API Gateway とサービス公開

### 3.1 API Gateway の実装

**ファイル: microservices/api-gateway/app.py**
```python
import os
import json
import logging
from flask import Flask, jsonify, request, make_response
import requests
from datetime import datetime

logging.basicConfig(
    level=os.getenv('LOG_LEVEL', 'INFO'),
    format='{"timestamp": "%(asctime)s", "level": "%(levelname)s", "message": "%(message)s"}'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

SERVICE_NAME = os.getenv('SERVICE_NAME', 'api-gateway')
SERVICE_VERSION = os.getenv('SERVICE_VERSION', '1.0.0')
PORT = int(os.getenv('PORT', 8080))

# バックエンドサービスURL
USER_SERVICE_URL = os.getenv('USER_SERVICE_URL', 'http://user-service:5000')
ORDER_SERVICE_URL = os.getenv('ORDER_SERVICE_URL', 'http://order-service:5001')

def log_request(endpoint, method, status_code, response_time=None):
    log_data = {
        'service': SERVICE_NAME,
        'endpoint': endpoint,
        'method': method,
        'status_code': status_code,
        'timestamp': datetime.utcnow().isoformat()
    }
    if response_time:
        log_data['response_time_ms'] = response_time
    logger.info(json.dumps(log_data))

def proxy_request(service_url, path, method='GET', data=None):
    """サービスへのプロキシリクエスト"""
    url = f"{service_url}{path}"
    try:
        if method == 'GET':
            response = requests.get(url, timeout=10)
        elif method == 'POST':
            response = requests.post(url, json=data, timeout=10)
        else:
            return None, 405
        
        return response.json(), response.status_code
    except requests.RequestException as e:
        logger.error(f"Service request failed: {str(e)}")
        return {'error': 'Service unavailable'}, 503

@app.route('/health')
def health_check():
    """API Gateway ヘルスチェック"""
    # 依存サービスのヘルスチェック
    services_health = {}
    
    try:
        user_health = requests.get(f"{USER_SERVICE_URL}/health", timeout=5)
        services_health['user-service'] = 'healthy' if user_health.status_code == 200 else 'unhealthy'
    except:
        services_health['user-service'] = 'unhealthy'
    
    try:
        order_health = requests.get(f"{ORDER_SERVICE_URL}/health", timeout=5)
        services_health['order-service'] = 'healthy' if order_health.status_code == 200 else 'unhealthy'
    except:
        services_health['order-service'] = 'unhealthy'
    
    overall_status = 'healthy' if all(status == 'healthy' for status in services_health.values()) else 'degraded'
    
    return jsonify({
        'status': overall_status,
        'service': SERVICE_NAME,
        'version': SERVICE_VERSION,
        'dependencies': services_health,
        'timestamp': datetime.utcnow().isoformat()
    })

# ユーザーサービスプロキシ
@app.route('/api/v1/users', methods=['GET', 'POST'])
def users():
    start_time = datetime.utcnow()
    data, status_code = proxy_request(USER_SERVICE_URL, '/users', request.method, request.get_json())
    end_time = datetime.utcnow()
    response_time = (end_time - start_time).total_seconds() * 1000
    
    log_request('/api/v1/users', request.method, status_code, response_time)
    return jsonify(data), status_code

@app.route('/api/v1/users/<user_id>', methods=['GET'])
def user_detail(user_id):
    start_time = datetime.utcnow()
    data, status_code = proxy_request(USER_SERVICE_URL, f'/users/{user_id}', 'GET')
    end_time = datetime.utcnow()
    response_time = (end_time - start_time).total_seconds() * 1000
    
    log_request(f'/api/v1/users/{user_id}', 'GET', status_code, response_time)
    return jsonify(data), status_code

# 注文サービスプロキシ
@app.route('/api/v1/orders', methods=['GET', 'POST'])
def orders():
    start_time = datetime.utcnow()
    data, status_code = proxy_request(ORDER_SERVICE_URL, '/orders', request.method, request.get_json())
    end_time = datetime.utcnow()
    response_time = (end_time - start_time).total_seconds() * 1000
    
    log_request('/api/v1/orders', request.method, status_code, response_time)
    return jsonify(data), status_code

@app.route('/api/v1/orders/<order_id>', methods=['GET'])
def order_detail(order_id):
    start_time = datetime.utcnow()
    data, status_code = proxy_request(ORDER_SERVICE_URL, f'/orders/{order_id}', 'GET')
    end_time = datetime.utcnow()
    response_time = (end_time - start_time).total_seconds() * 1000
    
    log_request(f'/api/v1/orders/{order_id}', 'GET', status_code, response_time)
    return jsonify(data), status_code

# CORS対応
@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response

if __name__ == '__main__':
    logger.info(f"Starting {SERVICE_NAME} v{SERVICE_VERSION} on port {PORT}")
    app.run(host='0.0.0.0', port=PORT, debug=False)
```

### 3.2 API Gateway デプロイメント

```bash
# API Gatewayイメージビルド
cd microservices/api-gateway
cp ../user-service/requirements.txt .
docker build -t localhost:5000/api-gateway:v1.0 .
docker push localhost:5000/api-gateway:v1.0
cd ../../
```

**ファイル: manifests/api-gateway.yaml**
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: api-gateway
  namespace: cloudnative-demo
  labels:
    app: api-gateway
    tier: frontend
    version: v1.0
spec:
  replicas: 2
  selector:
    matchLabels:
      app: api-gateway
  template:
    metadata:
      labels:
        app: api-gateway
        tier: frontend
        version: v1.0
    spec:
      containers:
      - name: api-gateway
        image: localhost:5000/api-gateway:v1.0
        ports:
        - containerPort: 8080
        env:
        - name: SERVICE_NAME
          value: "api-gateway"
        - name: SERVICE_VERSION
          value: "1.0.0"
        - name: PORT
          value: "8080"
        - name: USER_SERVICE_URL
          value: "http://user-service:5000"
        - name: ORDER_SERVICE_URL
          value: "http://order-service:5001"
        - name: LOG_LEVEL
          valueFrom:
            configMapKeyRef:
              name: microservices-config
              key: LOG_LEVEL
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
            port: 8080
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 5
          periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: api-gateway
  namespace: cloudnative-demo
  labels:
    app: api-gateway
spec:
  selector:
    app: api-gateway
  ports:
  - protocol: TCP
    port: 8080
    targetPort: 8080
    nodePort: 30080
  type: NodePort
```

```bash
# API Gateway デプロイ
kubectl apply -f manifests/api-gateway.yaml

# 外部アクセス確認
minikube ip
curl $(minikube ip):30080/health
```

---

## 🔄 Exercise 4: Circuit Breaker パターンの実装

### 4.1 Circuit Breaker 機能付きサービス

**ファイル: microservices/circuit-breaker/app.py**
```python
import os
import time
import logging
from enum import Enum
from flask import Flask, jsonify
import requests
from datetime import datetime, timedelta

class CircuitState(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"

class CircuitBreaker:
    def __init__(self, failure_threshold=5, recovery_timeout=60, expected_exception=Exception):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        
        self.failure_count = 0
        self.last_failure_time = None
        self.state = CircuitState.CLOSED
        
    def call(self, func, *args, **kwargs):
        if self.state == CircuitState.OPEN:
            if self._should_attempt_reset():
                self.state = CircuitState.HALF_OPEN
            else:
                raise Exception("Circuit breaker is OPEN")
        
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except self.expected_exception as e:
            self._on_failure()
            raise e
    
    def _should_attempt_reset(self):
        return (self.last_failure_time and 
                datetime.now() >= self.last_failure_time + timedelta(seconds=self.recovery_timeout))
    
    def _on_success(self):
        self.failure_count = 0
        self.state = CircuitState.CLOSED
    
    def _on_failure(self):
        self.failure_count += 1
        self.last_failure_time = datetime.now()
        
        if self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 外部サービス用Circuit Breaker
external_service_cb = CircuitBreaker(failure_threshold=3, recovery_timeout=30)

def call_external_service():
    """外部サービス呼び出しの模擬"""
    # 50%の確率で失敗する模擬
    import random
    if random.random() < 0.5:
        raise requests.RequestException("Service unavailable")
    return {"data": "success", "timestamp": datetime.utcnow().isoformat()}

@app.route('/health')
def health():
    return jsonify({
        "status": "healthy",
        "circuit_breaker_state": external_service_cb.state.value,
        "failure_count": external_service_cb.failure_count
    })

@app.route('/external-call')
def external_call():
    try:
        result = external_service_cb.call(call_external_service)
        return jsonify({
            "status": "success",
            "data": result,
            "circuit_state": external_service_cb.state.value
        })
    except Exception as e:
        logger.error(f"Circuit breaker prevented call: {str(e)}")
        return jsonify({
            "status": "error",
            "message": "Service temporarily unavailable",
            "circuit_state": external_service_cb.state.value,
            "failure_count": external_service_cb.failure_count
        }), 503

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5002)
```

---

## 📊 Exercise 5: Event-Driven Architecture の基礎

### 5.1 Event Publisher Service

**ファイル: microservices/event-publisher/app.py**
```python
import os
import json
import logging
from flask import Flask, request, jsonify
import requests
from datetime import datetime
import uuid

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 簡易イベントストア
event_store = []

# イベント購読者（Webhook）
subscribers = {
    'user.created': ['http://notification-service:5003/webhook'],
    'order.created': ['http://notification-service:5003/webhook'],
    'order.updated': ['http://inventory-service:5004/webhook']
}

def publish_event(event_type, data):
    """イベント発行"""
    event = {
        'id': str(uuid.uuid4()),
        'type': event_type,
        'data': data,
        'timestamp': datetime.utcnow().isoformat(),
        'version': '1.0'
    }
    
    # イベント保存
    event_store.append(event)
    logger.info(f"Event published: {event_type}")
    
    # 購読者に通知
    if event_type in subscribers:
        for webhook_url in subscribers[event_type]:
            try:
                requests.post(webhook_url, json=event, timeout=5)
                logger.info(f"Event sent to {webhook_url}")
            except requests.RequestException as e:
                logger.error(f"Failed to send event to {webhook_url}: {str(e)}")
    
    return event

@app.route('/health')
def health():
    return jsonify({
        'status': 'healthy',
        'events_published': len(event_store),
        'subscribers': len(subscribers)
    })

@app.route('/events', methods=['POST'])
def create_event():
    """イベント作成エンドポイント"""
    data = request.get_json()
    event_type = data.get('type')
    event_data = data.get('data', {})
    
    if not event_type:
        return jsonify({'error': 'Event type is required'}), 400
    
    event = publish_event(event_type, event_data)
    return jsonify(event), 201

@app.route('/events', methods=['GET'])
def get_events():
    """イベント履歴取得"""
    return jsonify(event_store)

@app.route('/subscribe', methods=['POST'])
def subscribe():
    """イベント購読登録"""
    data = request.get_json()
    event_type = data.get('event_type')
    webhook_url = data.get('webhook_url')
    
    if event_type not in subscribers:
        subscribers[event_type] = []
    
    if webhook_url not in subscribers[event_type]:
        subscribers[event_type].append(webhook_url)
    
    return jsonify({'message': f'Subscribed to {event_type}'}), 201

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5005)
```

### 5.2 Notification Service（イベント購読者）

**ファイル: microservices/notification-service/app.py**
```python
import os
import json
import logging
from flask import Flask, request, jsonify
from datetime import datetime

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 通知履歴
notifications = []

def send_notification(event):
    """通知送信の模擬"""
    notification = {
        'id': len(notifications) + 1,
        'event_id': event.get('id'),
        'event_type': event.get('type'),
        'message': f"Notification for {event.get('type')}: {event.get('data')}",
        'timestamp': datetime.utcnow().isoformat(),
        'status': 'sent'
    }
    
    notifications.append(notification)
    logger.info(f"Notification sent: {notification['message']}")
    return notification

@app.route('/health')
def health():
    return jsonify({
        'status': 'healthy',
        'notifications_sent': len(notifications)
    })

@app.route('/webhook', methods=['POST'])
def webhook():
    """イベント受信Webhook"""
    event = request.get_json()
    logger.info(f"Received event: {event.get('type')}")
    
    # イベントタイプに応じた処理
    if event.get('type') in ['user.created', 'order.created', 'order.updated']:
        notification = send_notification(event)
        return jsonify({'status': 'processed', 'notification': notification}), 200
    
    return jsonify({'status': 'ignored'}), 200

@app.route('/notifications', methods=['GET'])
def get_notifications():
    """通知履歴取得"""
    return jsonify(notifications)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5003)
```

---

## 🧪 Exercise 6: サービス間通信テストと検証

### 6.1 統合テストの実行

```bash
# 全サービスデプロイメント状態確認
kubectl get pods -n cloudnative-demo
kubectl get services -n cloudnative-demo

# API Gateway経由でのテスト
GATEWAY_URL=$(minikube ip):30080

# ヘルスチェック
curl $GATEWAY_URL/health

# ユーザー作成
curl -X POST $GATEWAY_URL/api/v1/users \
  -H "Content-Type: application/json" \
  -d '{"name":"Charlie","email":"charlie@example.com"}'

# ユーザー一覧取得
curl $GATEWAY_URL/api/v1/users

# 注文作成
curl -X POST $GATEWAY_URL/api/v1/orders \
  -H "Content-Type: application/json" \
  -d '{"user_id":"1","items":[{"name":"Product A","price":100}],"total":100}'

# 注文一覧取得
curl $GATEWAY_URL/api/v1/orders
```

### 6.2 サービス間通信の観察

```bash
# 各サービスのログ確認
kubectl logs -n cloudnative-demo deployment/user-service -f &
kubectl logs -n cloudnative-demo deployment/order-service -f &
kubectl logs -n cloudnative-demo deployment/api-gateway -f &

# リアルタイムでの動作確認
watch kubectl get pods -n cloudnative-demo
```

### 6.3 負荷テストによる12ファクター検証

```bash
# Factor VIII: 並行性のテスト
kubectl scale deployment user-service --replicas=4 -n cloudnative-demo
kubectl scale deployment order-service --replicas=4 -n cloudnative-demo

# Factor IX: 可処分性のテスト
kubectl delete pod -l app=user-service -n cloudnative-demo

# サービス復旧確認
kubectl get pods -n cloudnative-demo -w

# Factor VI: プロセス（ステートレス）の確認
# 異なるPodで同じリクエストを実行
for i in {1..10}; do
  curl $GATEWAY_URL/api/v1/users/1
  sleep 1
done
```

---

## 📈 Exercise 7: サービスディスカバリーとロードバランシング

### 7.1 DNS ベースのサービスディスカバリー

```bash
# DNS解決テスト用Pod作成
kubectl run dns-test --image=busybox -n cloudnative-demo --rm -it -- sh

# Pod内でDNS解決テスト
nslookup user-service
nslookup order-service.cloudnative-demo.svc.cluster.local

# Serviceによるロードバランシングテスト
for i in {1..10}; do
  wget -qO- user-service:5000/health | grep hostname
  sleep 1
done
```

### 7.2 Headless Service によるディスカバリー

**ファイル: manifests/headless-service.yaml**
```yaml
apiVersion: v1
kind: Service
metadata:
  name: user-service-headless
  namespace: cloudnative-demo
spec:
  clusterIP: None  # Headless Service
  selector:
    app: user-service
  ports:
  - port: 5000
    targetPort: 5000
```

```bash
# Headless Service作成
kubectl apply -f manifests/headless-service.yaml

# DNS レコード確認
kubectl run dns-debug --image=busybox -n cloudnative-demo --rm -it -- nslookup user-service-headless
```

---

## 🧹 リソースクリーンアップ

```bash
# namespace内の全リソース削除
kubectl delete namespace cloudnative-demo

# Dockerリソース削除
docker rm -f local-registry
docker system prune -f

# 作業ディレクトリクリーンアップ
cd ~
rm -rf ~/kcna-lab03
```

---

## 📚 復習課題

### 総合演習

以下の要件を満たすクラウドネイティブアプリケーションを設計・実装してください：

1. **12ファクター準拠**: 全ての原則を適用
2. **マイクロサービス**: 最低3つのサービス
3. **API Gateway**: 統一エントリーポイント
4. **Event-Driven**: 非同期通信の実装
5. **Circuit Breaker**: 障害耐性の実装
6. **Observability**: 構造化ログと監視

### チェックリスト

このラボ完了後、以下ができることを確認してください：

- [ ] 12ファクターアプリケーションの設計と実装
- [ ] マイクロサービス間の通信設計
- [ ] API-First設計の実践
- [ ] 設定管理のベストプラクティス
- [ ] サービスディスカバリーとDNS解決
- [ ] Event-Driven Architectureの基礎実装
- [ ] Circuit Breakerパターンの理解
- [ ] Kubernetesでのマイクロサービス管理
- [ ] ロードバランシングと可用性設計
- [ ] 障害分離とレジリエンス設計

---

## 🎯 次のステップ

### 高度なトピック

1. **Service Mesh**: Istio、Linkerd
2. **API Management**: 認証、認可、レート制限
3. **Distributed Tracing**: Jaeger、Zipkin
4. **Message Broker**: RabbitMQ、Apache Kafka
5. **CQRS/Event Sourcing**: 高度なイベント設計

### 実践的学習

- Istio を使用したサービスメッシュ実装
- Prometheus/Grafana によるマイクロサービス監視
- ArgoCD を使用したGitOps実装
- Helm Chart によるマイクロサービス管理

### 参考資料

- [12-Factor App](https://12factor.net/)
- [Microservices Patterns](https://microservices.io/)
- [Cloud Native Architecture](https://landscape.cncf.io/)

---

**重要**: このラボはKCNA-JP試験のクラウドネイティブアーキテクチャドメイン（16%）をカバーしています。実際のマイクロサービス設計と実装を通じて、クラウドネイティブアプリケーションの設計原則とパターンを深く理解することができます。