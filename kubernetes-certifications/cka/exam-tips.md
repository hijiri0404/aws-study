# CKA 試験対策と実技のコツ

## 🎯 試験直前チェックリスト

### 📋 技術要件の最終確認

#### Domain 1: Cluster Architecture, Installation & Configuration (25%)
- [ ] **kubeadm**: クラスター初期化・ノード追加・リセット
- [ ] **etcd**: バックアップ・復元手順
- [ ] **証明書管理**: 有効期限確認・更新
- [ ] **ノード管理**: cordon、drain、uncordon
- [ ] **kubeconfig**: 設定・切り替え・認証

#### Domain 2: Workloads & Scheduling (15%)  
- [ ] **Deployments**: 作成・更新・ロールバック・スケーリング
- [ ] **DaemonSets**: 全ノード展開・tolerations設定
- [ ] **StatefulSets**: 順序付きデプロイ・永続ストレージ
- [ ] **Jobs/CronJobs**: バッチ処理・定期実行
- [ ] **Pod Scheduling**: nodeSelector、affinity、taints

#### Domain 3: Services & Networking (20%)
- [ ] **Services**: ClusterIP、NodePort、LoadBalancer、Headless
- [ ] **Ingress**: HTTP/HTTPSルーティング
- [ ] **NetworkPolicies**: 通信制御・セキュリティ
- [ ] **DNS**: 名前解決・CoreDNS設定
- [ ] **CNI**: ネットワークプラグイン設定

#### Domain 4: Storage (10%)
- [ ] **PersistentVolumes**: 作成・設定・ライフサイクル
- [ ] **PersistentVolumeClaims**: 要求・バインディング
- [ ] **StorageClasses**: 動的プロビジョニング
- [ ] **Volume Types**: emptyDir、hostPath、configMap、secret

#### Domain 5: Troubleshooting (30%)
- [ ] **ログ分析**: Pod・ノード・クラスターレベル
- [ ] **リソース監視**: CPU・メモリ・ディスク使用量
- [ ] **ネットワーク診断**: 接続性・DNS・Service疎通
- [ ] **クラスター修復**: API Server・etcd・kubelet問題

---

## ⏰ 試験当日の戦略

### 時間配分 (120分)
```
問題読み込み・全体把握: 5分
問題解答 (17問): 100分 (約6分/問)
見直し・修正: 10分
最終確認: 5分
```

### 解答順序の推奨
1. **確実に分かる問題**: 設定変更・基本操作（2-3分）
2. **中程度の問題**: ワークロード管理・Service作成（4-6分）
3. **複雑な問題**: トラブルシューティング・クラスター管理（8-12分）
4. **時間のかかる問題**: 後回しにしてマーキング

---

## 🛠️ 実技試験の効率化テクニック

### 1. 環境設定の最適化

```bash
# ~/.bashrc に追加（試験開始直後に設定）
export do="--dry-run=client -o yaml"
export now="--force --grace-period 0"

# kubectl エイリアス
alias k=kubectl
alias kg='kubectl get'
alias kd='kubectl describe'
alias kdel='kubectl delete'
alias kl='kubectl logs'
alias ke='kubectl exec -it'

# 補完設定
source <(kubectl completion bash)
complete -F __start_kubectl k
```

### 2. YAML生成の高速化

```bash
# Deployment作成テンプレート
kubectl create deployment nginx --image=nginx:1.20 $do > deployment.yaml

# Service作成テンプレート  
kubectl expose deployment nginx --port=80 --target-port=80 $do > service.yaml

# Pod作成テンプレート
kubectl run test-pod --image=busybox:1.35 --command $do -- sleep 3600 > pod.yaml

# Job作成テンプレート
kubectl create job test-job --image=busybox:1.35 $do -- echo "Hello" > job.yaml

# ConfigMap作成
kubectl create configmap app-config --from-literal=key1=value1 $do > configmap.yaml
```

### 3. よく使うワンライナー

```bash
# 全namespaceのPod一覧
kubectl get pods -A

# 指定ラベルのPod削除
kubectl delete pods -l app=nginx

# ノードのPod一覧
kubectl get pods -A -o wide | grep worker-node-1

# 最新のイベント表示
kubectl get events --sort-by=.metadata.creationTimestamp

# リソース使用量確認
kubectl top nodes; kubectl top pods -A

# マルチコンテナPodのログ
kubectl logs pod-name -c container-name

# Pod内でのコマンド実行
kubectl exec pod-name -c container-name -- command

# ポートフォワーディング
kubectl port-forward pod/nginx 8080:80 &
```

---

## 📊 頻出問題パターンと対策

### 1. etcdバックアップ・復元 (必出)

**パターン例:**
> "etcdクラスターのスナップショットを `/opt/etcd-backup.db` に作成してください"

**高速解答テンプレート:**
```bash
# バックアップ作成
ETCDCTL_API=3 etcdctl snapshot save /opt/etcd-backup.db \
  --endpoints=https://127.0.0.1:2379 \
  --cacert=/etc/kubernetes/pki/etcd/ca.crt \
  --cert=/etc/kubernetes/pki/etcd/server.crt \
  --key=/etc/kubernetes/pki/etcd/server.key

# バックアップ検証
ETCDCTL_API=3 etcdctl snapshot status /opt/etcd-backup.db --write-out=table
```

### 2. ノード管理 (高頻度)

**パターン例:**
> "worker-node-1をメンテナンスのためにドレインしてください"

**解答手順:**
```bash
# 1. ノードをスケジュール不可に
kubectl cordon worker-node-1

# 2. Podを安全に移行
kubectl drain worker-node-1 --ignore-daemonsets --delete-emptydir-data --force

# 3. メンテナンス後に復帰
kubectl uncordon worker-node-1
```

### 3. ワークロード作成 (基本)

**パターン例:**
> "nginx Deploymentを作成し、3レプリカで実行してください"

**効率的な解答:**
```bash
# 1. 基本Deployment作成
kubectl create deployment nginx --image=nginx:1.20 --replicas=3

# 2. 必要に応じてYAMLで詳細設定
kubectl get deployment nginx -o yaml > nginx-deployment.yaml
# 編集後
kubectl apply -f nginx-deployment.yaml
```

### 4. トラブルシューティング (最重要)

**問題パターン:**
- "Pod が Pending 状態です。修正してください"
- "Service に接続できません。原因を特定してください"

**体系的アプローチ:**
```bash
# Step 1: 症状確認
kubectl get pods/services -o wide

# Step 2: 詳細調査
kubectl describe pod/service <name>

# Step 3: ログ確認
kubectl logs <pod-name>
kubectl get events --sort-by=.metadata.creationTimestamp

# Step 4: 設定確認
kubectl get pod <name> -o yaml
kubectl get endpoints <service-name>

# Step 5: 修正・確認
# 問題に応じた修正実行
kubectl get pods/services # 動作確認
```

---

## 🎯 試験でのミス回避ポイント

### 1. namespace指定忘れ

**❌ よくあるミス:**
```bash
kubectl get pods  # default namespaceのみ表示
```

**✅ 正しい方法:**
```bash
kubectl get pods -n target-namespace
# または
kubectl config set-context --current --namespace=target-namespace
```

### 2. YAML編集ミス

**❌ よくあるミス:**
- インデントの不整合
- 不要な行の残存
- 文字列の引用符忘れ

**✅ 対策:**
```bash
# YAML検証
kubectl apply -f file.yaml --dry-run=client

# vim設定（試験環境で）
:set paste
:set number
:set expandtab
:set tabstop=2
```

### 3. リソース削除忘れ

**問題例:** "Podを削除してから新しいDeploymentを作成してください"

**確実な削除:**
```bash
# 強制削除（必要な場合）
kubectl delete pod <name> --grace-period=0 --force

# 完了確認
kubectl get pods | grep <name>
```

### 4. 設定変更の反映確認忘れ

**✅ 必ず実行:**
```bash
# Deployment更新後
kubectl rollout status deployment/<name>

# Pod再作成後
kubectl wait --for=condition=Ready pod/<name> --timeout=300s

# Service作成後
kubectl get endpoints <service-name>
```

---

## 📝 暗記必須事項

### 1. ポート番号
```
API Server: 6443
etcd: 2379, 2380  
kubelet: 10250
kube-scheduler: 10259
kube-controller-manager: 10257
NodePort range: 30000-32767
```

### 2. 重要なファイルパス
```
# Kubernetes設定
/etc/kubernetes/manifests/      # 静的Pod定義
/etc/kubernetes/pki/            # 証明書
/etc/kubernetes/admin.conf      # kubeconfig

# kubelet設定
/var/lib/kubelet/config.yaml
/etc/systemd/system/kubelet.service.d/

# etcd
/var/lib/etcd/                  # データディレクトリ

# CNI
/etc/cni/net.d/                 # ネットワーク設定
```

### 3. よく使うkubectl オプション
```bash
--dry-run=client -o yaml        # YAML生成
--all-namespaces               # 全namespace
--show-labels                  # ラベル表示
--sort-by=.metadata.creationTimestamp  # 時刻順ソート
--selector="app=nginx"         # ラベルセレクター
--grace-period=0 --force       # 強制削除
```

---

## 🔧 実技演習での重要コマンド

### クラスター管理
```bash
# クラスター情報
kubectl cluster-info
kubectl get componentstatuses

# ノード管理
kubectl get nodes -o wide
kubectl describe node <name>
kubectl cordon/uncordon/drain <node>

# 証明書管理
kubeadm certs check-expiration
kubeadm certs renew apiserver
```

### ワークロード管理
```bash
# Pod管理
kubectl get pods -o wide
kubectl describe pod <name>
kubectl logs <pod> -c <container>
kubectl exec -it <pod> -- /bin/bash

# Deployment管理
kubectl create deployment <name> --image=<image>
kubectl scale deployment <name> --replicas=<count>
kubectl rollout status deployment/<name>
kubectl rollout undo deployment/<name>
```

### Service・ネットワーク
```bash
# Service作成
kubectl expose deployment <name> --port=80 --target-port=80 --type=ClusterIP

# 接続確認
kubectl get endpoints <service>
kubectl run test --image=busybox:1.35 --rm -it -- wget -qO- <service>:<port>

# DNS確認
kubectl exec -it <pod> -- nslookup <service>
```

### ストレージ
```bash
# PV/PVC確認
kubectl get pv,pvc
kubectl describe pv <name>
kubectl describe pvc <name>

# StorageClass確認
kubectl get storageclass
```

---

## 📊 時間管理のコツ

### 1. 問題の優先度判定 (30秒)

**高優先度 (即座に着手)**
- 基本的なYAML作成問題
- 既知の手順問題（etcdバックアップなど）

**中優先度 (標準的な時間配分)**
- ワークロード管理問題
- Service・ネットワーク設定

**低優先度 (時間があれば)**
- 複雑なトラブルシューティング
- 初見の設定問題

### 2. 作業効率化

```bash
# 複数コマンドの並列実行
kubectl get pods & kubectl get services & wait

# 長時間のコマンドはバックグラウンド実行
kubectl wait --for=condition=Ready pod/<name> --timeout=300s &

# タブ補完の活用
kubectl get po<TAB> -n ku<TAB>
```

### 3. 途中での見切り

- **5分ルール**: 5分で解決の見込みがない場合は次へ
- **マーキング**: `# TODO: 後で確認` をコメントで残す
- **部分点狙い**: 完全でなくても動作する状態まで作成

---

## 🎯 試験前日の最終準備

### 1. 環境確認
- [ ] 試験環境（オンライン/テストセンター）の確認
- [ ] 身分証明書の準備
- [ ] システム要件の確認（オンライン試験の場合）
- [ ] kubectl バージョンの確認（v1.28系）

### 2. 知識の最終確認
- [ ] この資料の重要ポイント再読
- [ ] Practice Exam の再実施（時間測定）
- [ ] よく間違える問題の復習
- [ ] kubectl チートシートの確認

### 3. 体調・メンタル準備
- [ ] 十分な睡眠（最低7時間）
- [ ] 軽い運動と栄養バランス
- [ ] 緊張緩和のためのリラックス時間

---

## 🏆 合格後のキャリアパス

### 関連資格の推奨順序
1. **CKAD (Certified Kubernetes Application Developer)**: アプリケーション開発視点
2. **CKS (Certified Kubernetes Security Specialist)**: セキュリティ専門性
3. **AWS/Azure/GCP Kubernetes certifications**: クラウド特化認定

### 実務での活用領域
- **クラスター運用**: 本番環境の構築・運用・監視
- **コンテナ戦略**: 組織のコンテナ化推進
- **DevOps**: CI/CDパイプラインの構築
- **クラウドネイティブ**: マイクロサービス・12-Factor App

---

## 📚 継続学習リソース

### CNCF公式リソース
- [CNCF Landscape](https://landscape.cncf.io/): エコシステム全体の把握
- [Kubernetes Blog](https://kubernetes.io/blog/): 最新動向
- [CNCF Webinars](https://www.cncf.io/webinars/): 技術セミナー

### コミュニティ
- Kubernetes Slack: リアルタイム情報交換
- CNCF Meetups: 地域別技術交流
- KubeCon + CloudNativeCon: 最大級の技術カンファレンス

### 実践プラットフォーム
- [Katacoda](https://www.katacoda.com/courses/kubernetes): ブラウザ内実習
- [Play with Kubernetes](https://labs.play-with-k8s.com/): 無料実験環境
- [Kubernetes the Hard Way](https://github.com/kelseyhightower/kubernetes-the-hard-way): 基礎理解

---

**🎉 頑張って！** CKAは実技重視の試験です。理論だけでなく、実際に手を動かした経験が合格の鍵となります。

**最後のアドバイス**: 
- 焦らず、問題文を正確に読む
- 基本に忠実な解答を心がける  
- 部分点を積み重ねる意識
- 最後まで諦めない姿勢

あなたのKubernetesエンジニアとしての成功を願っています！