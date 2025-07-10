# Lab 02: コンテナオーケストレーション

## 📋 ラボ概要

**目的**: コンテナ技術の深い理解、Dockerの実践的使用、Kubernetesにおけるコンテナオーケストレーションの習得  
**所要時間**: 120-150分  
**前提条件**: Lab 01完了、Docker基礎知識  
**使用環境**: Docker、minikube、kubectl

---

## 🎯 学習目標

このラボ完了後、以下ができるようになります：

1. コンテナとVMの違いの理解と実践的比較
2. Dockerイメージの作成、管理、レジストリへの操作
3. マルチコンテナPodの設計と実装
4. コンテナランタイムとCRIの理解
5. ストレージとネットワークの基本的な管理
6. コンテナのリソース管理と制限
7. コンテナセキュリティの基本原則

---

## 🛠️ 事前準備

### 環境確認

```bash
# Docker動作確認
docker --version
docker ps

# Kubernetes環境確認
kubectl cluster-info
kubectl get nodes

# 作業ディレクトリ作成
mkdir -p ~/kcna-lab02
cd ~/kcna-lab02
```

---

## 🐳 Exercise 1: コンテナ基礎と Docker 実践

### 1.1 コンテナとVMの比較

```bash
# システムリソース使用量確認
free -h
ps aux | wc -l

# Dockerコンテナのリソース使用量確認
docker run --rm alpine:latest free -h
docker run --rm alpine:latest ps aux
```

**理論確認**:
- VM: ハイパーバイザー上で完全なOSを実行
- コンテナ: ホストOSカーネルを共有、プロセス分離

### 1.2 Docker イメージの基本操作

```bash
# 基本的なイメージ操作
docker images
docker pull nginx:1.21
docker pull nginx:alpine

# イメージ詳細情報
docker inspect nginx:1.21
docker history nginx:1.21

# イメージレイヤー確認
docker image inspect nginx:1.21 | jq '.[0].RootFS.Layers'
```

### 1.3 コンテナライフサイクル管理

```bash
# コンテナ作成と実行
docker run -d --name web-server nginx:1.21
docker ps

# コンテナ内部調査
docker exec web-server ps aux
docker exec -it web-server /bin/bash

# コンテナ操作
docker stop web-server
docker start web-server
docker restart web-server

# コンテナ削除
docker rm -f web-server
```

**課題 1.1**: 異なるイメージ（nginx、alpine、ubuntu）でコンテナを起動し、メモリ使用量とプロセス数を比較してください。

---

## 🏗️ Exercise 2: カスタムDockerイメージの作成

### 2.1 単純な Web アプリケーション作成

**ファイル: app.py**
```python
from flask import Flask
import os
import socket

app = Flask(__name__)

@app.route('/')
def hello():
    hostname = socket.gethostname()
    env_var = os.getenv('CUSTOM_MESSAGE', 'Hello from Container!')
    return f'''
    <h1>{env_var}</h1>
    <p>Container Hostname: {hostname}</p>
    <p>Container Technology: Docker</p>
    '''

@app.route('/health')
def health():
    return {'status': 'healthy', 'container': socket.gethostname()}

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
```

**ファイル: requirements.txt**
```
Flask==2.3.2
```

### 2.2 Dockerfile作成

**ファイル: Dockerfile**
```dockerfile
# ベースイメージ指定
FROM python:3.9-slim

# 作業ディレクトリ設定
WORKDIR /app

# 依存関係ファイルコピー
COPY requirements.txt .

# 依存関係インストール
RUN pip install --no-cache-dir -r requirements.txt

# アプリケーションファイルコピー
COPY app.py .

# ポート公開
EXPOSE 5000

# 実行ユーザー設定（セキュリティ）
RUN adduser --disabled-password --gecos '' appuser
USER appuser

# 起動コマンド
CMD ["python", "app.py"]
```

### 2.3 イメージビルドとテスト

```bash
# Dockerイメージビルド
docker build -t kcna-webapp:v1.0 .

# ビルドプロセス確認
docker history kcna-webapp:v1.0

# コンテナ実行テスト
docker run -d -p 8080:5000 --name test-app kcna-webapp:v1.0

# アプリケーションテスト
curl localhost:8080
curl localhost:8080/health

# ログ確認
docker logs test-app

# リソース使用量確認
docker stats test-app --no-stream
```

### 2.4 マルチステージビルド

**ファイル: Dockerfile.multistage**
```dockerfile
# Build Stage
FROM python:3.9 as builder

WORKDIR /app
COPY requirements.txt .
RUN pip install --user -r requirements.txt

# Runtime Stage
FROM python:3.9-slim

WORKDIR /app

# ビルドステージから必要ファイルのみコピー
COPY --from=builder /root/.local /root/.local
COPY app.py .

# PATH更新
ENV PATH=/root/.local/bin:$PATH

EXPOSE 5000

RUN adduser --disabled-password --gecos '' appuser
USER appuser

CMD ["python", "app.py"]
```

```bash
# マルチステージビルド
docker build -f Dockerfile.multistage -t kcna-webapp:v1.1 .

# イメージサイズ比較
docker images | grep kcna-webapp
```

**課題 2.1**: .dockerignoreファイルを作成し、不要なファイルがイメージに含まれないようにしてください。

---

## 📦 Exercise 3: コンテナレジストリ操作

### 3.1 ローカルレジストリの起動

```bash
# ローカルレジストリ起動
docker run -d -p 5000:5000 --name local-registry registry:2

# レジストリ動作確認
curl localhost:5000/v2/_catalog
```

### 3.2 イメージのタグ付けとプッシュ

```bash
# イメージタグ付け
docker tag kcna-webapp:v1.0 localhost:5000/kcna-webapp:v1.0

# ローカルレジストリにプッシュ
docker push localhost:5000/kcna-webapp:v1.0

# レジストリ内容確認
curl localhost:5000/v2/_catalog
curl localhost:5000/v2/kcna-webapp/tags/list
```

### 3.3 プライベートレジストリからのプル

```bash
# ローカルイメージ削除
docker rmi localhost:5000/kcna-webapp:v1.0
docker rmi kcna-webapp:v1.0

# レジストリからプル
docker pull localhost:5000/kcna-webapp:v1.0

# プルしたイメージで実行
docker run -d -p 8081:5000 localhost:5000/kcna-webapp:v1.0
curl localhost:8081
```

---

## 🚀 Exercise 4: Kubernetes でのコンテナオーケストレーション

### 4.1 カスタムイメージをKubernetesで使用

**ファイル: webapp-deployment.yaml**
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: webapp-deployment
  labels:
    app: webapp
spec:
  replicas: 3
  selector:
    matchLabels:
      app: webapp
  template:
    metadata:
      labels:
        app: webapp
    spec:
      containers:
      - name: webapp
        image: localhost:5000/kcna-webapp:v1.0
        ports:
        - containerPort: 5000
        env:
        - name: CUSTOM_MESSAGE
          value: "Hello from Kubernetes!"
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
```

```bash
# Deploymentの作成
kubectl apply -f webapp-deployment.yaml

# Pod状態確認
kubectl get pods -l app=webapp
kubectl describe pod <pod-name>
```

### 4.2 ImagePullPolicy の理解

**ファイル: image-pull-policy-test.yaml**
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: pull-policy-test
spec:
  containers:
  - name: always-pull
    image: nginx:latest
    imagePullPolicy: Always
  - name: ifnotpresent-pull
    image: nginx:1.21
    imagePullPolicy: IfNotPresent
  - name: never-pull
    image: nginx:alpine
    imagePullPolicy: Never
```

```bash
# 異なるPullPolicyテスト
kubectl apply -f image-pull-policy-test.yaml
kubectl describe pod pull-policy-test
```

### 4.3 プライベートレジストリでの認証

```bash
# レジストリ認証用Secret作成
kubectl create secret docker-registry registry-secret \
  --docker-server=localhost:5000 \
  --docker-username=user \
  --docker-password=pass \
  --docker-email=user@example.com

# Secretを使用するPod
kubectl run private-app \
  --image=localhost:5000/kcna-webapp:v1.0 \
  --overrides='{"spec":{"imagePullSecrets":[{"name":"registry-secret"}]}}'
```

---

## 🔗 Exercise 5: マルチコンテナPod と通信パターン

### 5.1 サイドカーパターン

**ファイル: sidecar-pod.yaml**
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: sidecar-example
spec:
  containers:
  # メインアプリケーション
  - name: main-app
    image: nginx:1.21
    ports:
    - containerPort: 80
    volumeMounts:
    - name: shared-logs
      mountPath: /var/log/nginx
  
  # ログ収集サイドカー
  - name: log-collector
    image: busybox
    command: ["sh", "-c"]
    args:
    - while true; do
        echo "$(date): Collecting logs..." >> /var/log/collector.log;
        if [ -f /var/log/nginx/access.log ]; then
          tail -n 5 /var/log/nginx/access.log >> /var/log/collector.log;
        fi;
        sleep 30;
      done
    volumeMounts:
    - name: shared-logs
      mountPath: /var/log/nginx
    - name: collector-logs
      mountPath: /var/log
  
  volumes:
  - name: shared-logs
    emptyDir: {}
  - name: collector-logs
    emptyDir: {}
```

```bash
# サイドカーPod作成
kubectl apply -f sidecar-pod.yaml

# 各コンテナの動作確認
kubectl exec sidecar-example -c main-app -- ls /var/log/nginx
kubectl exec sidecar-example -c log-collector -- cat /var/log/collector.log

# アクセステストしてログ生成
kubectl port-forward pod/sidecar-example 8082:80 &
curl localhost:8082

# ログ確認
kubectl exec sidecar-example -c log-collector -- tail /var/log/collector.log
```

### 5.2 アンバサダーパターン

**ファイル: ambassador-pod.yaml**
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: ambassador-example
spec:
  containers:
  # メインアプリケーション
  - name: main-app
    image: curlimages/curl
    command: ["sleep", "3600"]
  
  # アンバサダープロキシ
  - name: ambassador-proxy
    image: nginx:1.21
    ports:
    - containerPort: 80
    volumeMounts:
    - name: nginx-config
      mountPath: /etc/nginx/conf.d
  
  volumes:
  - name: nginx-config
    configMap:
      name: ambassador-config
```

**ファイル: ambassador-config.yaml**
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: ambassador-config
data:
  default.conf: |
    upstream backend {
        server httpbin.org:80;
    }
    
    server {
        listen 80;
        location / {
            proxy_pass http://backend;
            proxy_set_header Host httpbin.org;
        }
    }
```

```bash
# ConfigMapとPod作成
kubectl apply -f ambassador-config.yaml
kubectl apply -f ambassador-pod.yaml

# アンバサダー経由でのアクセステスト
kubectl exec ambassador-example -c main-app -- curl localhost/get
```

### 5.3 アダプターパターン

**ファイル: adapter-pod.yaml**
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: adapter-example
spec:
  containers:
  # メインアプリケーション（独自ログ形式）
  - name: legacy-app
    image: busybox
    command: ["sh", "-c"]
    args:
    - while true; do
        echo "$(date '+%Y%m%d_%H%M%S') [LEGACY] Application running..." >> /var/log/app.log;
        sleep 10;
      done
    volumeMounts:
    - name: log-volume
      mountPath: /var/log
  
  # ログフォーマットアダプター
  - name: log-adapter
    image: busybox
    command: ["sh", "-c"]
    args:
    - while true; do
        if [ -f /var/log/app.log ]; then
          tail -f /var/log/app.log | while read line; do
            echo "{\"timestamp\":\"$(date -Iseconds)\", \"level\":\"INFO\", \"message\":\"$line\"}" >> /var/log/formatted.log;
          done;
        fi;
        sleep 5;
      done
    volumeMounts:
    - name: log-volume
      mountPath: /var/log
  
  volumes:
  - name: log-volume
    emptyDir: {}
```

```bash
# アダプターPod作成
kubectl apply -f adapter-pod.yaml

# 元のログ確認
kubectl exec adapter-example -c legacy-app -- tail /var/log/app.log

# 変換されたログ確認
kubectl exec adapter-example -c log-adapter -- tail /var/log/formatted.log
```

---

## 📊 Exercise 6: コンテナリソース管理

### 6.1 リソース制限の実装

**ファイル: resource-limits-pod.yaml**
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: resource-demo
spec:
  containers:
  - name: cpu-limited
    image: busybox
    command: ["sh", "-c", "while true; do echo 'CPU intensive task'; done"]
    resources:
      requests:
        memory: "64Mi"
        cpu: "125m"
      limits:
        memory: "128Mi"
        cpu: "250m"
  - name: memory-limited
    image: busybox
    command: ["sh", "-c", "dd if=/dev/zero of=/tmp/memory bs=1M count=100; sleep 3600"]
    resources:
      requests:
        memory: "50Mi"
        cpu: "100m"
      limits:
        memory: "100Mi"
        cpu: "200m"
```

```bash
# リソース制限Pod作成
kubectl apply -f resource-limits-pod.yaml

# リソース使用量監視
kubectl top pod resource-demo --containers

# Pod詳細確認
kubectl describe pod resource-demo
```

### 6.2 QoS クラスの理解

```bash
# 異なるQoSクラスのPod作成

# Guaranteed QoS (requests = limits)
kubectl run guaranteed-qos --image=nginx:1.21 \
  --requests='memory=100Mi,cpu=100m' \
  --limits='memory=100Mi,cpu=100m'

# Burstable QoS (requests < limits または requests のみ)
kubectl run burstable-qos --image=nginx:1.21 \
  --requests='memory=50Mi,cpu=50m' \
  --limits='memory=100Mi,cpu=100m'

# BestEffort QoS (制限なし)
kubectl run besteffort-qos --image=nginx:1.21

# QoSクラス確認
kubectl describe pod guaranteed-qos | grep "QoS Class"
kubectl describe pod burstable-qos | grep "QoS Class"
kubectl describe pod besteffort-qos | grep "QoS Class"
```

---

## 💾 Exercise 7: コンテナストレージ管理

### 7.1 Volume の種類と使用

**ファイル: volume-types-pod.yaml**
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: volume-demo
spec:
  containers:
  - name: volume-test
    image: busybox
    command: ["sleep", "3600"]
    volumeMounts:
    - name: empty-dir-vol
      mountPath: /tmp/empty-dir
    - name: host-path-vol
      mountPath: /tmp/host-path
    - name: config-vol
      mountPath: /tmp/config
  
  volumes:
  - name: empty-dir-vol
    emptyDir:
      sizeLimit: "1Gi"
  - name: host-path-vol
    hostPath:
      path: /tmp/k8s-host-data
      type: DirectoryOrCreate
  - name: config-vol
    configMap:
      name: volume-config
```

**ファイル: volume-config.yaml**
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: volume-config
data:
  app.conf: |
    # Application configuration
    debug=true
    log_level=info
  database.conf: |
    host=localhost
    port=5432
```

```bash
# ConfigMapとPod作成
kubectl apply -f volume-config.yaml
kubectl apply -f volume-types-pod.yaml

# Volume動作確認
kubectl exec volume-demo -- ls -la /tmp/empty-dir
kubectl exec volume-demo -- ls -la /tmp/config
kubectl exec volume-demo -- cat /tmp/config/app.conf

# データ永続性テスト
kubectl exec volume-demo -- echo "Test data" > /tmp/empty-dir/test.txt
kubectl exec volume-demo -- echo "Host data" > /tmp/host-path/test.txt

# Pod削除・再作成後の確認
kubectl delete pod volume-demo
kubectl apply -f volume-types-pod.yaml
kubectl exec volume-demo -- ls /tmp/empty-dir    # 空になる
kubectl exec volume-demo -- ls /tmp/host-path    # データ残存
```

### 7.2 Init Container を使用したデータ準備

**ファイル: init-container-pod.yaml**
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: init-demo
spec:
  initContainers:
  - name: data-initializer
    image: busybox
    command: ["sh", "-c"]
    args:
    - echo "Initializing data...";
      echo "Database initialized at $(date)" > /shared-data/init.log;
      echo "Config prepared" > /shared-data/config.txt;
      echo "Init completed successfully"
    volumeMounts:
    - name: shared-data
      mountPath: /shared-data
  
  - name: permission-setter
    image: busybox
    command: ["sh", "-c"]
    args:
    - echo "Setting permissions...";
      chmod 755 /shared-data/config.txt;
      echo "Permissions set" >> /shared-data/init.log
    volumeMounts:
    - name: shared-data
      mountPath: /shared-data
  
  containers:
  - name: main-app
    image: nginx:1.21
    volumeMounts:
    - name: shared-data
      mountPath: /usr/share/nginx/html
  
  volumes:
  - name: shared-data
    emptyDir: {}
```

```bash
# Init Container Pod作成
kubectl apply -f init-container-pod.yaml

# 初期化プロセス確認
kubectl get pod init-demo -w

# 初期化されたデータ確認
kubectl exec init-demo -- ls -la /usr/share/nginx/html
kubectl exec init-demo -- cat /usr/share/nginx/html/init.log
```

---

## 🔒 Exercise 8: コンテナセキュリティ基礎

### 8.1 Security Context の設定

**ファイル: security-context-pod.yaml**
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: security-demo
spec:
  securityContext:
    runAsUser: 1000
    runAsGroup: 1000
    fsGroup: 1000
    seccompProfile:
      type: RuntimeDefault
  
  containers:
  - name: secure-container
    image: nginx:1.21
    securityContext:
      allowPrivilegeEscalation: false
      readOnlyRootFilesystem: false
      runAsNonRoot: true
      capabilities:
        drop:
        - ALL
        add:
        - NET_BIND_SERVICE
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
```

```bash
# セキュアPod作成
kubectl apply -f security-context-pod.yaml

# セキュリティ設定確認
kubectl exec security-demo -- id
kubectl exec security-demo -- ps aux

# 権限テスト（失敗するはず）
kubectl exec security-demo -- touch /etc/test.txt
```

### 8.2 ネットワークセキュリティ基礎

**ファイル: network-policy.yaml**
```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: deny-all
spec:
  podSelector: {}
  policyTypes:
  - Ingress
  - Egress
---
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-webapp
spec:
  podSelector:
    matchLabels:
      app: webapp
  policyTypes:
  - Ingress
  ingress:
  - from:
    - podSelector:
        matchLabels:
          role: client
    ports:
    - protocol: TCP
      port: 5000
```

```bash
# NetworkPolicy適用（CNIがサポートしている場合）
kubectl apply -f network-policy.yaml

# テスト用Pod作成
kubectl run client --image=curlimages/curl --labels="role=client" -- sleep 3600
kubectl run attacker --image=curlimages/curl -- sleep 3600

# 接続テスト
kubectl exec client -- curl webapp-service:5000        # 成功するはず
kubectl exec attacker -- curl webapp-service:5000      # 失敗するはず
```

---

## 🔧 Exercise 9: Container Runtime Interface (CRI)

### 9.1 コンテナランタイム確認

```bash
# ノードのコンテナランタイム確認
kubectl get nodes -o wide
kubectl describe node minikube | grep "Container Runtime"

# minikube内でのランタイム確認
minikube ssh
docker --version
containerd --version
exit
```

### 9.2 CRI-O との比較（理論）

**比較ポイント**:
1. **Docker**: 開発・テスト環境で広く使用、Docker Desktop
2. **containerd**: Kubernetesで標準、軽量、本番環境向け
3. **CRI-O**: Kubernetes専用、OCI準拠、セキュリティ重視

```bash
# CRIエンドポイント確認
kubectl get nodes -o jsonpath='{.items[0].status.nodeInfo.containerRuntimeVersion}'
```

---

## 🧹 リソースクリーンアップ

```bash
# Pod削除
kubectl delete pod sidecar-example
kubectl delete pod ambassador-example
kubectl delete pod adapter-example
kubectl delete pod resource-demo
kubectl delete pod volume-demo
kubectl delete pod init-demo
kubectl delete pod security-demo

# QoSテストPod削除
kubectl delete pod guaranteed-qos
kubectl delete pod burstable-qos
kubectl delete pod besteffort-qos

# Deployment削除
kubectl delete deployment webapp-deployment

# ConfigMapとSecret削除
kubectl delete configmap ambassador-config
kubectl delete configmap volume-config
kubectl delete secret registry-secret

# NetworkPolicy削除
kubectl delete networkpolicy deny-all
kubectl delete networkpolicy allow-webapp

# Dockerリソース削除
docker rm -f test-app
docker rm -f local-registry
docker rmi localhost:5000/kcna-webapp:v1.0
docker rmi kcna-webapp:v1.0
docker rmi kcna-webapp:v1.1

# 作業ディレクトリクリーンアップ
cd ~
rm -rf ~/kcna-lab02
```

---

## 📚 復習課題

### 総合演習

以下の要件を満たすマルチコンテナアプリケーションを作成してください：

1. **メインアプリ**: Python Flask アプリケーション
2. **サイドカー**: ログ収集・フォーマット変換
3. **Init Container**: データベース接続確認
4. **セキュリティ**: 非root実行、最小権限
5. **リソース制限**: 適切なrequests/limits設定
6. **ストレージ**: 永続ログ保存

### チェックリスト

このラボ完了後、以下ができることを確認してください：

- [ ] コンテナとVMの違いの説明
- [ ] Dockerfileの作成とベストプラクティス
- [ ] マルチステージビルドの実装
- [ ] コンテナレジストリの操作
- [ ] ImagePullPolicyの使い分け
- [ ] マルチコンテナPodの設計パターン
- [ ] リソース制限とQoSクラスの理解
- [ ] Volume types の使い分け
- [ ] Init Container の活用
- [ ] セキュリティコンテキストの設定
- [ ] CRI と コンテナランタイムの理解

---

## 🎯 次のステップ

### 高度なトピック

1. **OCI準拠**: Open Container Initiative標準
2. **BuildKit**: 高速・セキュアなDockerビルド
3. **Distroless**: 最小限のコンテナイメージ
4. **Pod Security Standards**: セキュリティポリシー

### 実践的学習

- 本格的なマイクロサービスアプリケーションのコンテナ化
- Helm Chartでのマルチコンテナアプリケーション管理
- セキュリティスキャンツールの使用
- パフォーマンス最適化とモニタリング

### 参考資料

- [Docker Best Practices](https://docs.docker.com/develop/dev-best-practices/)
- [Kubernetes Container Patterns](https://kubernetes.io/blog/2015/06/the-distributed-system-toolkit-patterns/)
- [OCI Specifications](https://opencontainers.org/)

---

**重要**: このラボはKCNA-JP試験のコンテナオーケストレーションドメイン（22%）をカバーしています。コンテナ技術の基礎から実践的なオーケストレーションまで、幅広い知識と経験を身につけることで、クラウドネイティブアプリケーションの理解が深まります。