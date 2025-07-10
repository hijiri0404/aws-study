# Lab 01: Kubernetes基礎

## 📋 ラボ概要

**目的**: Kubernetesクラスターの基本操作、主要コンポーネントの理解、基本的なワークロードの作成と管理  
**所要時間**: 90-120分  
**前提条件**: Docker基礎知識、Linux基本コマンド  
**使用環境**: minikube、kubectl

---

## 🎯 学習目標

このラボ完了後、以下ができるようになります：

1. Kubernetesクラスターの起動と基本確認
2. kubectl コマンドラインツールの基本操作
3. Pod、Service、Deploymentの作成と管理
4. ConfigMapとSecretの基本的な使用
5. ラベルとセレクターの活用
6. 基本的なトラブルシューティング

---

## 🛠️ 事前準備

### 必要なツール

```bash
# minikube のインストール確認
minikube version

# kubectl のインストール確認
kubectl version --client

# Docker のインストール確認
docker --version
```

### クラスターの起動

```bash
# minikubeクラスターの起動
minikube start --driver=docker

# クラスター状態の確認
minikube status

# kubectl設定の確認
kubectl cluster-info
```

---

## 🚀 Exercise 1: クラスター探索とコンポーネント理解

### 1.1 クラスター情報の確認

```bash
# クラスター情報の表示
kubectl cluster-info

# ノード一覧の表示
kubectl get nodes

# ノードの詳細情報
kubectl describe node minikube

# API リソース一覧の確認
kubectl api-resources
```

**課題 1.1**: 以下の情報を調べて記録してください
- クラスターのKubernetesバージョン
- ノード名とそのIPアドレス
- 利用可能なCPUとメモリ量

### 1.2 namespace の理解

```bash
# デフォルトnamespace一覧
kubectl get namespaces

# kube-system namespace のポッド確認
kubectl get pods -n kube-system

# Control Plane コンポーネントの確認
kubectl get pods -n kube-system | grep -E "(etcd|api|scheduler|controller)"
```

**課題 1.2**: kube-system namespaceで実行されている主要コンポーネントを特定し、それぞれの役割を説明してください。

### 1.3 kubectl 基本コマンドの練習

```bash
# ヘルプの確認
kubectl help
kubectl get --help

# 短縮形の使用
kubectl get po          # pods
kubectl get svc         # services
kubectl get deploy     # deployments

# 異なる出力形式
kubectl get nodes -o wide
kubectl get nodes -o yaml
kubectl get nodes -o json
```

---

## 🧪 Exercise 2: Pod の作成と管理

### 2.1 簡単なPodの作成

```bash
# nginx Podを直接作成
kubectl run nginx-pod --image=nginx:1.21

# Pod状態の確認
kubectl get pods
kubectl get pods -o wide

# Podの詳細情報
kubectl describe pod nginx-pod

# Podログの確認
kubectl logs nginx-pod
```

### 2.2 YAML マニフェストを使用したPod作成

**ファイル: simple-pod.yaml**
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: simple-web
  labels:
    app: web
    tier: frontend
spec:
  containers:
  - name: web-container
    image: nginx:1.21
    ports:
    - containerPort: 80
    env:
    - name: ENV_VAR
      value: "Hello from Pod"
```

```bash
# マニフェストからPodを作成
kubectl apply -f simple-pod.yaml

# 作成されたPodの確認
kubectl get pod simple-web
kubectl describe pod simple-web
```

### 2.3 Pod への接続とデバッグ

```bash
# Podにシェルで接続
kubectl exec -it simple-web -- /bin/bash

# Pod内でコマンド実行
kubectl exec simple-web -- ls /usr/share/nginx/html

# ポートフォワードで接続テスト
kubectl port-forward pod/simple-web 8080:80

# 別ターミナルでアクセステスト
curl localhost:8080
```

**課題 2.1**: 以下を実行してください
1. 自分でカスタムPod YAML を作成（Apache httpd使用）
2. 環境変数を設定して動作確認
3. ポートフォワードでアクセス確認

---

## 📦 Exercise 3: Deployment の作成と管理

### 3.1 Deployment の作成

```bash
# Deploymentの作成
kubectl create deployment web-app --image=nginx:1.21 --replicas=3

# Deployment状態の確認
kubectl get deployments
kubectl get pods -l app=web-app

# Deployment詳細情報
kubectl describe deployment web-app
```

### 3.2 YAML マニフェストを使用したDeployment

**ファイル: web-deployment.yaml**
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: web-deployment
  labels:
    app: web
spec:
  replicas: 3
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
        image: nginx:1.21
        ports:
        - containerPort: 80
        resources:
          requests:
            memory: "64Mi"
            cpu: "125m"
          limits:
            memory: "128Mi"
            cpu: "250m"
```

```bash
# Deploymentの適用
kubectl apply -f web-deployment.yaml

# ReplicaSetとPodの確認
kubectl get rs
kubectl get pods --show-labels
```

### 3.3 スケーリングと更新

```bash
# レプリカ数の変更
kubectl scale deployment web-deployment --replicas=5
kubectl get pods

# イメージ更新（ローリングアップデート）
kubectl set image deployment/web-deployment web=nginx:1.22
kubectl rollout status deployment/web-deployment

# 更新履歴の確認
kubectl rollout history deployment/web-deployment

# ロールバック
kubectl rollout undo deployment/web-deployment
```

**課題 3.1**: 以下のシナリオを実行してください
1. Deploymentを2レプリカで作成
2. 5レプリカにスケール
3. イメージをnginx:1.22に更新
4. 元のバージョンにロールバック

---

## 🌐 Exercise 4: Service の作成と通信

### 4.1 ClusterIP Service の作成

```bash
# Serviceの作成
kubectl expose deployment web-deployment --port=80 --target-port=80

# Service確認
kubectl get services
kubectl describe service web-deployment
```

### 4.2 YAML マニフェストを使用したService

**ファイル: web-service.yaml**
```yaml
apiVersion: v1
kind: Service
metadata:
  name: web-service
spec:
  selector:
    app: web
  ports:
  - protocol: TCP
    port: 80
    targetPort: 80
  type: ClusterIP
```

```bash
# Serviceの適用
kubectl apply -f web-service.yaml

# Endpointsの確認
kubectl get endpoints web-service
```

### 4.3 Service への接続テスト

```bash
# 一時的なPodでService接続テスト
kubectl run test-pod --image=curlimages/curl --rm -it -- sh

# Pod内でServiceにアクセス
curl web-service
curl web-service.default.svc.cluster.local

# DNS解決確認
nslookup web-service
```

### 4.4 NodePort Service の作成

**ファイル: nodeport-service.yaml**
```yaml
apiVersion: v1
kind: Service
metadata:
  name: web-nodeport
spec:
  selector:
    app: web
  ports:
  - protocol: TCP
    port: 80
    targetPort: 80
    nodePort: 30080
  type: NodePort
```

```bash
# NodePort Serviceの作成
kubectl apply -f nodeport-service.yaml

# minikube IPアドレス確認
minikube ip

# 外部からのアクセステスト
curl $(minikube ip):30080
```

---

## ⚙️ Exercise 5: ConfigMap と Secret

### 5.1 ConfigMap の作成と使用

```bash
# リテラル値からConfigMap作成
kubectl create configmap app-config \
  --from-literal=database_host=mysql.example.com \
  --from-literal=database_port=3306

# ConfigMap確認
kubectl get configmap
kubectl describe configmap app-config
```

**ファイル: app-configmap.yaml**
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: app-settings
data:
  app.properties: |
    # Application settings
    debug=true
    log_level=info
    max_connections=100
  database.conf: |
    [database]
    host=mysql.example.com
    port=3306
    name=appdb
```

```bash
# ファイルからConfigMap作成
kubectl apply -f app-configmap.yaml
```

### 5.2 ConfigMapをPodで使用

**ファイル: pod-with-configmap.yaml**
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: app-pod
spec:
  containers:
  - name: app-container
    image: nginx:1.21
    env:
    - name: DATABASE_HOST
      valueFrom:
        configMapKeyRef:
          name: app-config
          key: database_host
    volumeMounts:
    - name: config-volume
      mountPath: /etc/config
  volumes:
  - name: config-volume
    configMap:
      name: app-settings
```

```bash
# ConfigMapを使用するPod作成
kubectl apply -f pod-with-configmap.yaml

# 環境変数確認
kubectl exec app-pod -- env | grep DATABASE_HOST

# マウントされたファイル確認
kubectl exec app-pod -- ls /etc/config
kubectl exec app-pod -- cat /etc/config/app.properties
```

### 5.3 Secret の作成と使用

```bash
# Secret作成
kubectl create secret generic app-secret \
  --from-literal=username=admin \
  --from-literal=password=secret123

# Secret確認
kubectl get secrets
kubectl describe secret app-secret

# base64エンコードされた値の確認
kubectl get secret app-secret -o yaml
```

**ファイル: pod-with-secret.yaml**
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: secret-pod
spec:
  containers:
  - name: app-container
    image: nginx:1.21
    env:
    - name: DB_USERNAME
      valueFrom:
        secretKeyRef:
          name: app-secret
          key: username
    - name: DB_PASSWORD
      valueFrom:
        secretKeyRef:
          name: app-secret
          key: password
    volumeMounts:
    - name: secret-volume
      mountPath: /etc/secrets
      readOnly: true
  volumes:
  - name: secret-volume
    secret:
      secretName: app-secret
```

```bash
# Secretを使用するPod作成
kubectl apply -f pod-with-secret.yaml

# 環境変数確認
kubectl exec secret-pod -- env | grep DB_

# マウントされたSecret確認
kubectl exec secret-pod -- ls /etc/secrets
kubectl exec secret-pod -- cat /etc/secrets/username
```

---

## 🏷️ Exercise 6: ラベルとセレクター

### 6.1 ラベルの操作

```bash
# 既存Podにラベル追加
kubectl label pod simple-web version=v1.0
kubectl label pod simple-web environment=development

# ラベル確認
kubectl get pods --show-labels

# ラベルでフィルタリング
kubectl get pods -l app=web
kubectl get pods -l environment=development
kubectl get pods -l 'app in (web,nginx)'
```

### 6.2 セレクターを使用したリソース管理

```bash
# ラベルセレクターでPod削除
kubectl delete pods -l version=v1.0

# 複数条件でのセレクション
kubectl get pods -l app=web,environment=production
```

### 6.3 アノテーションの使用

```bash
# アノテーション追加
kubectl annotate pod simple-web description="Test pod for learning"
kubectl annotate pod simple-web maintainer="team-alpha"

# アノテーション確認
kubectl describe pod simple-web | grep Annotations
```

---

## 🔍 Exercise 7: 基本的なトラブルシューティング

### 7.1 Pod障害の診断

```bash
# 意図的に失敗するPodを作成
kubectl run failing-pod --image=nginx:invalid-tag

# Pod状態確認
kubectl get pods
kubectl describe pod failing-pod

# イベント確認
kubectl get events --sort-by=.metadata.creationTimestamp
```

### 7.2 リソース不足の模擬

**ファイル: resource-heavy-pod.yaml**
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: resource-heavy
spec:
  containers:
  - name: heavy-container
    image: nginx:1.21
    resources:
      requests:
        memory: "10Gi"
        cpu: "4"
```

```bash
# リソース不足Podの作成
kubectl apply -f resource-heavy-pod.yaml

# スケジューリング失敗の確認
kubectl describe pod resource-heavy
kubectl get events | grep resource-heavy
```

### 7.3 ログとイベントを使用したデバッグ

```bash
# アプリケーションログの確認
kubectl logs web-deployment-<pod-id>

# 前回のコンテナログ（再起動時）
kubectl logs web-deployment-<pod-id> --previous

# 複数コンテナPodの特定コンテナログ
kubectl logs <pod-name> -c <container-name>

# リアルタイムログ監視
kubectl logs -f web-deployment-<pod-id>
```

---

## 🧹 リソースクリーンアップ

### 作成したリソースの削除

```bash
# 個別削除
kubectl delete pod simple-web
kubectl delete pod app-pod
kubectl delete pod secret-pod
kubectl delete deployment web-deployment
kubectl delete service web-service
kubectl delete service web-nodeport
kubectl delete configmap app-config
kubectl delete configmap app-settings
kubectl delete secret app-secret

# または、ラベルで一括削除
kubectl delete pods -l lab=01

# 失敗したリソースの削除
kubectl delete pod failing-pod
kubectl delete pod resource-heavy
```

### クラスターの停止（必要に応じて）

```bash
# minikubeクラスターの停止
minikube stop

# minikubeクラスターの削除
minikube delete
```

---

## 📚 復習課題

### 総合演習

以下の要件を満たすアプリケーションを作成してください：

1. **Web Tier**: nginx デプロイメント（3レプリカ）
2. **Config**: アプリケーション設定をConfigMapで管理
3. **Secret**: データベース接続情報をSecretで管理
4. **Service**: ClusterIPとNodePortの両方で公開
5. **Labels**: tier=frontend, app=webapp, version=v1.0

```yaml
# your-webapp.yaml として実装
```

### チェックリスト

このラボ完了後、以下ができることを確認してください：

- [ ] Kubernetesクラスターの起動と基本操作
- [ ] kubectl コマンドでのリソース管理
- [ ] Pod、Deployment、Serviceの作成と管理
- [ ] YAML マニフェストファイルの作成と適用
- [ ] ConfigMapとSecretの作成と使用
- [ ] ラベルとセレクターを使ったリソースフィルタリング
- [ ] 基本的なトラブルシューティング手法
- [ ] ポートフォワードとService接続の理解
- [ ] ローリングアップデートとロールバック
- [ ] リソースの削除とクリーンアップ

---

## 🎯 次のステップ

### 学習内容の発展

1. **Volume とストレージ**: PersistentVolumeとPersistentVolumeClaim
2. **ネットワーク**: Ingress、NetworkPolicy
3. **セキュリティ**: RBAC、ServiceAccount
4. **モニタリング**: ヘルスチェック、メトリクス

### 推奨練習

- 実際のアプリケーション（WordPress、データベース）のデプロイ
- 複数のnamespaceを使った環境分離
- kubectl aliasとshortcutの設定
- Kubernetesダッシュボードの利用

### 参考資料

- [Kubernetes公式ドキュメント](https://kubernetes.io/docs/)
- [kubectl Cheat Sheet](https://kubernetes.io/docs/reference/kubectl/cheatsheet/)
- [Kubernetes Concepts](https://kubernetes.io/docs/concepts/)

---

**重要**: このラボはKCNA-JP試験のKubernetes基本原則ドメイン（46%）をカバーしています。実際に手を動かして操作することで、概念の理解を深めてください。不明な点があれば、公式ドキュメントを参照しながら学習を進めてください。