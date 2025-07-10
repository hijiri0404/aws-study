# Certified Kubernetes Administrator (CKA)

## 📋 試験概要

**正式名称**: Certified Kubernetes Administrator  
**試験コード**: CKA  
**難易度**: ⭐⭐⭐⭐  
**試験時間**: 120分  
**問題数**: 15-20問（実技試験）  
**費用**: $395 USD  
**合格点**: 66%  

### 📊 試験ドメインと配点

1. **Storage (10%)** - ストレージ管理
2. **Troubleshooting (30%)** - トラブルシューティング
3. **Workloads & Scheduling (15%)** - ワークロードとスケジューリング
4. **Cluster Architecture, Installation & Configuration (25%)** - クラスターアーキテクチャ・インストール・設定
5. **Services & Networking (20%)** - サービスとネットワーク

## 🎯 対象者

- **推奨経験**: Kubernetes運用経験1年以上
- **前提知識**: Linux システム管理、Docker、ネットワーク基礎
- **実務経験**: Kubernetesクラスター管理経験

### 必要なスキル
- Kubernetesクラスター構築・運用
- システム管理・トラブルシューティング
- ネットワーク設定・管理
- セキュリティ管理
- バックアップ・リストア

## 🗂️ 教材構成

### 📚 基礎教材
- `00-fundamentals.md` - CKA基礎知識
- `exam-tips.md` - 試験対策のポイント

### 🔬 ハンズオンラボ
- `labs/lab01-cluster-setup/` - クラスター構築
- `labs/lab02-cluster-management/` - クラスター管理
- `labs/lab03-scheduling/` - スケジューリング
- `labs/lab04-networking/` - ネットワーク管理
- `labs/lab05-storage/` - ストレージ管理
- `labs/lab06-security/` - セキュリティ管理
- `labs/lab07-maintenance/` - メンテナンス・アップグレード
- `labs/lab08-troubleshooting/` - トラブルシューティング

### 📝 問題演習
- `practice-exams/` - 実技想定問題集（100問）
- `troubleshooting/` - トラブルシューティング

## 🚀 学習順序（推奨）

### Phase 1: 基礎固め（3週間）
1. **Kubernetes基礎**
   - アーキテクチャ理解
   - コンポーネント概要
   - kubectl 基本操作

2. **クラスター構築**
   - kubeadm によるクラスター構築
   - ネットワーク設定
   - Node 参加・削除

### Phase 2: 管理スキル（4週間）
3. **Lab 1: クラスター構築**
   - kubeadm init/join
   - CNI プラグイン設定
   - クラスター検証

4. **Lab 2: クラスター管理**
   - Node 管理
   - リソース監視
   - ログ管理

5. **Lab 3: スケジューリング**
   - Taints と Tolerations
   - Node Affinity
   - Pod 優先度

6. **Lab 4: ネットワーク管理**
   - Service 詳細設定
   - Ingress 管理
   - NetworkPolicy

### Phase 3: 高度な運用（3週間）
7. **Lab 5: ストレージ管理**
   - PersistentVolume 管理
   - StorageClass 設定
   - バックアップ・リストア

8. **Lab 6: セキュリティ管理**
   - RBAC 設定
   - Service Account 管理
   - Certificate 管理

9. **Lab 7: メンテナンス・アップグレード**
   - クラスターアップグレード
   - Node メンテナンス
   - etcd バックアップ

### Phase 4: トラブルシューティング（2週間）
10. **Lab 8: トラブルシューティング**
    - クラスター障害対応
    - アプリケーション障害対応
    - パフォーマンス問題解決

### Phase 5: 試験対策（1週間）
11. **実技問題演習**
    - 制限時間内での作業
    - 効率的なkubectl操作
    - 総合的なトラブルシューティング

## 💰 費用概算

### 学習環境構築コスト
| 項目 | 推定コスト |
|------|------------|
| Cloud環境 (3ヶ月) | $150-200 |
| 複数Node環境 | $80-120 |
| 試験受験料 | $395 |
| 再試験（必要時） | $395 |

**総計**: $625-715

### コスト削減のコツ
- ローカル環境でのVirtualBox/VMware使用
- 学習時のみクラウド環境を起動
- 無料のKubernetes学習リソース活用

## 🛠️ 事前準備

### 必要な環境
```bash
# kubectl インストール
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
chmod +x kubectl
sudo mv kubectl /usr/local/bin/

# kubeadm, kubelet, kubectl インストール
sudo apt-get update
sudo apt-get install -y apt-transport-https ca-certificates curl
sudo curl -fsSLo /usr/share/keyrings/kubernetes-archive-keyring.gpg https://packages.cloud.google.com/apt/doc/apt-key.gpg
echo "deb [signed-by=/usr/share/keyrings/kubernetes-archive-keyring.gpg] https://apt.kubernetes.io/ kubernetes-xenial main" | sudo tee /etc/apt/sources.list.d/kubernetes.list
sudo apt-get update
sudo apt-get install -y kubelet kubeadm kubectl
sudo apt-mark hold kubelet kubeadm kubectl

# Docker インストール
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh
```

### 必要な知識
- **Linux システム管理**: 中級レベル
- **ネットワーク**: TCP/IP、DNS、ロードバランサー
- **コンテナ**: Docker使用経験
- **セキュリティ**: 認証・認可、TLS

## 📊 学習進捗管理

### ドメイン別チェックリスト

#### Storage (10%)
- [ ] PersistentVolume 作成・管理
- [ ] PersistentVolumeClaim 設定
- [ ] StorageClass 設定
- [ ] Volume 種類と用途

#### Troubleshooting (30%)
- [ ] クラスター障害診断
- [ ] Node 障害対応
- [ ] ネットワーク問題解決
- [ ] アプリケーション障害対応

#### Workloads & Scheduling (15%)
- [ ] Deployment 管理
- [ ] DaemonSet 運用
- [ ] Static Pod 管理
- [ ] スケジューリング制御

#### Cluster Architecture, Installation & Configuration (25%)
- [ ] kubeadm でのクラスター構築
- [ ] etcd バックアップ・リストア
- [ ] クラスターアップグレード
- [ ] Node 管理

#### Services & Networking (20%)
- [ ] Service 作成・管理
- [ ] Ingress 設定
- [ ] NetworkPolicy 実装
- [ ] DNS 設定

## 🎯 試験対策のポイント

### 頻出トピック
1. **クラスター構築**: kubeadm init/join
2. **トラブルシューティング**: 障害原因特定・解決
3. **RBAC**: Role, ClusterRole, RoleBinding
4. **ネットワーク**: Service, Ingress, NetworkPolicy
5. **ストレージ**: PV, PVC, StorageClass

### 実技重視の準備
- 制限時間内での作業スピード
- kubectl コマンドの効率化
- YAML マニフェストの高速作成
- systemctl, journalctl の活用

### 重要なコマンド
```bash
# クラスター管理
kubeadm init --pod-network-cidr=10.244.0.0/16
kubeadm join <control-plane-host>:<control-plane-port> --token <token> --discovery-token-ca-cert-hash sha256:<hash>

# Node 管理
kubectl get nodes
kubectl describe node <node-name>
kubectl drain <node-name> --ignore-daemonsets
kubectl uncordon <node-name>

# etcd バックアップ
ETCDCTL_API=3 etcdctl snapshot save /backup/etcd-snapshot.db
ETCDCTL_API=3 etcdctl snapshot restore /backup/etcd-snapshot.db

# トラブルシューティング
kubectl logs <pod-name> -n <namespace>
kubectl describe pod <pod-name> -n <namespace>
journalctl -u kubelet
systemctl status kubelet
```

### 時間節約のエイリアス
```bash
# .bashrc に追加
alias k=kubectl
alias kgp='kubectl get pods'
alias kgn='kubectl get nodes'
alias kdp='kubectl describe pod'
alias kdn='kubectl describe node'
export do='--dry-run=client -o yaml'
export now='--force --grace-period=0'
```

## 🔗 参考リソース

### 公式リソース
- [CKA試験ガイド](https://training.linuxfoundation.org/certification/certified-kubernetes-administrator-cka/)
- [Kubernetes Documentation](https://kubernetes.io/docs/)
- [kubeadm Documentation](https://kubernetes.io/docs/setup/production-environment/tools/kubeadm/)

### 学習リソース
- [Kubernetes the Hard Way](https://github.com/kelseyhightower/kubernetes-the-hard-way)
- [CKA Practice Environment](https://github.com/arush-sal/cka-practice-environment)
- [Kubernetes Troubleshooting Guide](https://kubernetes.io/docs/tasks/debug-application-cluster/)

### 実践環境
- [Killer.sh CKA Simulator](https://killer.sh/cka)
- [KodeKloud CKA Course](https://kodekloud.com/courses/certified-kubernetes-administrator-cka/)

## 📝 学習のコツ

### 効率的な学習方法
1. **実際のクラスター構築**: 理論だけでなく実際の構築経験
2. **障害対応練習**: 意図的に障害を作り対応練習
3. **時間を意識**: 制限時間内での作業練習
4. **ドキュメント活用**: 試験中に参照可能なリソース

### 試験当日の戦略
1. **時間配分**: トラブルシューティング問題は時間をかけすぎない
2. **確実な問題から**: 分かる問題から解く
3. **検証**: 作成したリソースの動作確認
4. **ログ活用**: systemctl, journalctl でのログ確認

## 🚨 よくある失敗パターン

### 技術的な失敗
1. **CNI未設定**: Pod が起動しない
2. **firewall設定**: ポート疎通不可
3. **etcd設定**: バックアップ・リストア失敗
4. **RBAC設定**: 権限不足

### 試験での失敗
1. **時間不足**: 1問に時間をかけすぎる
2. **検証不足**: 作成したリソースが動作しない
3. **コマンド忘れ**: 基本的なkubectlコマンドの忘れ
4. **慌てすぎ**: 落ち着いて問題を読まない

---

**重要**: CKAは実技試験で、特にトラブルシューティング能力が重要です。実際にクラスターを構築・運用し、様々な障害パターンを経験することが合格への近道です。継続的な実践と障害対応経験が成功の鍵となります。