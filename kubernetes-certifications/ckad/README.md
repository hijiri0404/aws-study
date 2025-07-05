# Certified Kubernetes Application Developer (CKAD)

## 📋 試験概要

**正式名称**: Certified Kubernetes Application Developer  
**試験コード**: CKAD  
**難易度**: ⭐⭐⭐⭐  
**試験時間**: 120分  
**問題数**: 15-20問（実技試験）  
**費用**: $395 USD  
**合格点**: 66%  

### 📊 試験ドメインと配点

1. **Application Design and Build (20%)** - アプリケーション設計と構築
2. **Application Environment, Configuration and Security (25%)** - 環境・設定・セキュリティ
3. **Application Deployment (20%)** - アプリケーションデプロイメント
4. **Services and Networking (20%)** - サービスとネットワーク
5. **Application Observability and Maintenance (15%)** - 監視と保守

## 🎯 対象者

- **推奨経験**: Kubernetes開発経験6ヶ月以上
- **前提知識**: Docker、コンテナ基礎知識
- **実務経験**: Kubernetesアプリケーション開発経験

### 必要なスキル
- Kubernetesリソース管理
- コンテナアプリケーション開発
- YAML マニフェスト作成
- kubectl コマンド操作
- トラブルシューティング

## 🗂️ 教材構成

### 📚 基礎教材
- `00-fundamentals.md` - CKAD基礎知識
- `exam-tips.md` - 試験対策のポイント

### 🔬 ハンズオンラボ
- `labs/lab01-core-concepts/` - コア概念
- `labs/lab02-configuration/` - 設定管理
- `labs/lab03-multi-container-pods/` - マルチコンテナPod
- `labs/lab04-observability/` - 監視・ロギング
- `labs/lab05-pod-design/` - Pod設計
- `labs/lab06-services-networking/` - サービス・ネットワーク
- `labs/lab07-state-persistence/` - データ永続化

### 📝 問題演習
- `practice-exams/` - 実技想定問題集（100問）
- `troubleshooting/` - トラブルシューティング

## 🚀 学習順序（推奨）

### Phase 1: 基礎固め（2週間）
1. **Kubernetes基礎**
   - Pod、Service、Deployment の理解
   - kubectl 基本操作
   - YAML マニフェスト作成

2. **コア概念**
   - コンテナとイメージ
   - Namespace とラベル
   - リソース管理

### Phase 2: 実践演習（4週間）
3. **Lab 1: コア概念**
   - Pod作成・管理
   - ReplicaSet と Deployment
   - Service の基本

4. **Lab 2: 設定管理**
   - ConfigMap と Secret
   - 環境変数設定
   - ボリュームマウント

5. **Lab 3: マルチコンテナPod**
   - Sidecar パターン
   - Init Containers
   - 共有ボリューム

### Phase 3: 高度な機能（2週間）
6. **Lab 4: 監視・ロギング**
   - Liveness/Readiness Probe
   - ログ収集
   - メトリクス監視

7. **Lab 5: Pod設計**
   - Job と CronJob
   - Deployment 戦略
   - リソース制限

8. **Lab 6: サービス・ネットワーク**
   - Service タイプ
   - Ingress
   - NetworkPolicy

9. **Lab 7: データ永続化**
   - PersistentVolume
   - PersistentVolumeClaim
   - StorageClass

### Phase 4: 試験対策（1週間）
10. **実技問題演習**
    - 制限時間内での作業
    - 効率的なkubectl操作
    - トラブルシューティング

## 💰 費用概算

### 学習環境構築コスト
| 項目 | 推定コスト |
|------|------------|
| Cloud環境 (2ヶ月) | $50-80 |
| 学習リソース | $20-40 |
| 試験受験料 | $395 |
| 再試験（必要時） | $395 |

**総計**: $465-515

### コスト削減のコツ
- ローカル環境でのminikube/kind使用
- 無料のKubernetes学習リソース活用
- 練習環境は必要時のみ起動

## 🛠️ 事前準備

### 必要な環境
```bash
# kubectl インストール
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
chmod +x kubectl
sudo mv kubectl /usr/local/bin/

# minikube インストール (ローカル検証用)
curl -LO https://storage.googleapis.com/minikube/releases/latest/minikube-linux-amd64
sudo install minikube-linux-amd64 /usr/local/bin/minikube

# kind インストール
go install sigs.k8s.io/kind@v0.20.0
```

### 必要な知識
- **コンテナ基礎**: Docker使用経験
- **Linux基礎**: コマンドライン操作
- **YAML**: 基本的な記述方法
- **ネットワーク**: 基本的な概念

## 📊 学習進捗管理

### ドメイン別チェックリスト

#### Application Design and Build (20%)
- [ ] コンテナイメージの作成
- [ ] Pod作成とライフサイクル
- [ ] Job と CronJob
- [ ] マルチコンテナPod設計

#### Application Environment, Configuration and Security (25%)
- [ ] ConfigMap と Secret
- [ ] Security Context
- [ ] Service Account
- [ ] リソース制限

#### Application Deployment (20%)
- [ ] Deployment作成・更新
- [ ] Rolling Update
- [ ] Rollback
- [ ] Scaling

#### Services and Networking (20%)
- [ ] Service タイプ（ClusterIP, NodePort, LoadBalancer）
- [ ] Ingress設定
- [ ] NetworkPolicy
- [ ] DNS解決

#### Application Observability and Maintenance (15%)
- [ ] Liveness/Readiness Probe
- [ ] ログ収集・分析
- [ ] メトリクス監視
- [ ] トラブルシューティング

## 🎯 試験対策のポイント

### 頻出トピック
1. **Pod設計**: Multi-container, Init containers
2. **設定管理**: ConfigMap, Secret の使い分け
3. **サービス**: Service types, Ingress
4. **監視**: Probes, logging
5. **デプロイメント**: Rolling updates, scaling

### 実技重視の準備
- 制限時間内での作業スピード
- kubectl コマンドの効率化
- YAML マニフェストの高速作成
- vim/nano エディタの習熟

### 重要なコマンド
```bash
# 基本操作
kubectl run nginx --image=nginx --dry-run=client -o yaml > pod.yaml
kubectl create deployment nginx --image=nginx --dry-run=client -o yaml > deployment.yaml
kubectl expose deployment nginx --port=80 --dry-run=client -o yaml > service.yaml

# 設定管理
kubectl create configmap app-config --from-literal=key1=value1
kubectl create secret generic app-secret --from-literal=password=secret123

# 監視・デバッグ
kubectl logs pod-name -c container-name
kubectl exec -it pod-name -- /bin/bash
kubectl describe pod pod-name
```

### 時間節約のエイリアス
```bash
# .bashrc に追加
alias k=kubectl
alias krun='kubectl run'
alias kget='kubectl get'
alias kdesc='kubectl describe'
alias kdel='kubectl delete'
export do='--dry-run=client -o yaml'
export now='--force --grace-period=0'
```

## 🔗 参考リソース

### 公式リソース
- [CKAD試験ガイド](https://training.linuxfoundation.org/certification/certified-kubernetes-application-developer-ckad/)
- [Kubernetes Documentation](https://kubernetes.io/docs/)
- [kubectl チートシート](https://kubernetes.io/docs/reference/kubectl/cheatsheet/)

### 学習リソース
- [Kubernetes by Example](https://kubernetesbyexample.com/)
- [Play with Kubernetes](https://labs.play-with-k8s.com/)
- [Katacoda Kubernetes](https://www.katacoda.com/courses/kubernetes)

### 実践環境
- [Killer.sh CKAD Simulator](https://killer.sh/ckad)
- [KodeKloud CKAD Course](https://kodekloud.com/courses/certified-kubernetes-application-developer-ckad/)

## 📝 学習のコツ

### 効率的な学習方法
1. **実際に手を動かす**: 理論だけでなく実際の操作
2. **エラーから学ぶ**: 失敗の原因を分析
3. **時間を意識**: 制限時間内での作業練習
4. **ドキュメント活用**: 試験中に参照可能なリソース

### 試験当日の戦略
1. **時間配分**: 問題の難易度に応じた時間配分
2. **確実な問題から**: 分かる問題から解く
3. **検証**: 作成したリソースの動作確認
4. **冷静な判断**: 分からない問題は飛ばす

---

**重要**: CKADは実技試験です。理論知識だけでなく、実際にkubectlコマンドを使って短時間でアプリケーションを構築・デプロイする能力が評価されます。継続的な実践が合格への鍵となります。