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

**重要**: CKADは実技試験です。知識だけでなく、制限時間内での実装スピードが合格の鍵となります。継続的な実践練習が必要です。