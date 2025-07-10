# KCNA-JP (Kubernetes and Cloud Native Associate - Japanese) 学習教材

## 📋 概要

このディレクトリには、KCNA-JP（Kubernetes and Cloud Native Associate - Japanese）認定試験の対策教材が含まれています。

**試験概要**:
- **正式名称**: Kubernetes and Cloud Native Associate (KCNA-JP)
- **試験時間**: 90分
- **問題数**: 60問（多肢選択式）
- **合格ライン**: 75%
- **有効期限**: 3年間
- **実施方法**: オンライン監督試験

---

## 📚 教材構成

### 📖 試験ガイド
- **[01-exam-guide.md](01-exam-guide.md)**: 試験概要、ドメイン詳細、8週間学習プラン

### 📝 練習試験
- **[practice-exams/practice-exam-01.md](practice-exams/practice-exam-01.md)**: 100問の包括的練習試験（実試験形式）

### 🧪 実践ラボ
- **[labs/lab01-kubernetes-fundamentals.md](labs/lab01-kubernetes-fundamentals.md)**: Kubernetes基礎（90-120分）
- **[labs/lab02-container-orchestration.md](labs/lab02-container-orchestration.md)**: コンテナオーケストレーション（120-150分）
- **[labs/lab03-cloud-native-architecture.md](labs/lab03-cloud-native-architecture.md)**: クラウドネイティブアーキテクチャ（150-180分）
- **[labs/lab04-cloud-native-observability.md](labs/lab04-cloud-native-observability.md)**: クラウドネイティブ可観測性（120-150分）

---

## 🎯 試験ドメインと配分

| ドメイン | 割合 | 学習内容 |
|---------|------|----------|
| **Kubernetes の基本原則** | 46% | クラスターアーキテクチャ、API、ワークロード、サービス・ネットワーキング |
| **コンテナオーケストレーション** | 22% | コンテナランタイム、セキュリティ、ネットワーキング、サービスメッシュ |
| **クラウドネイティブアーキテクチャ** | 16% | オートスケーリング、サーバーレス、コミュニティ、ロール |
| **クラウドネイティブ可観測性** | 8% | テレメトリー・オブザーバビリティ、Prometheus、コスト管理 |
| **クラウドネイティブアプリケーションデリバリー** | 8% | アプリケーション定義・イメージビルド、GitOps、CI/CD |

---

## 🚀 学習の進め方

### Phase 1: 基礎固め（2-3週間）
1. **01-exam-guide.md** で試験全体を把握
2. **lab01** でKubernetes基礎を実践
3. **lab02** でコンテナ技術を深堀り

### Phase 2: 実践応用（3-4週間）
1. **lab03** でアーキテクチャパターンを学習
2. **lab04** で監視・可観測性を実装
3. 各ドメインの理論と実践を並行学習

### Phase 3: 試験対策（1-2週間）
1. **practice-exam-01** で実力測定
2. 弱点分野の集中学習
3. 最終復習と模擬試験

---

## 🛠️ 必要な環境

### 必須ツール
- **Kubernetes**: minikube または kind
- **Docker**: コンテナ管理
- **kubectl**: Kubernetesクライアント
- **Git**: バージョン管理
- **コードエディター**: VS Code推奨

### 推奨環境
- **OS**: Linux、macOS、Windows（WSL2）
- **メモリ**: 8GB以上
- **ストレージ**: 20GB以上の空き容量
- **ネットワーク**: インターネット接続

### セットアップコマンド
```bash
# minikube起動
minikube start --driver=docker --memory=4096 --cpus=2

# kubectl確認
kubectl cluster-info

# 作業ディレクトリ準備
mkdir -p ~/kcna-labs
cd ~/kcna-labs
```

---

## 📈 学習計画（8週間）

### Week 1-2: Kubernetes基礎
- [ ] クラスターアーキテクチャの理解
- [ ] Pod、Service、Deploymentの基本操作
- [ ] ConfigMap、Secretの管理
- [ ] **実践**: lab01完了

### Week 3-4: コンテナオーケストレーション
- [ ] コンテナランタイムとCRI
- [ ] Docker実践とイメージ管理
- [ ] マルチコンテナパターン
- [ ] **実践**: lab02完了

### Week 5-6: クラウドネイティブアーキテクチャ
- [ ] 12ファクターアプリケーション
- [ ] マイクロサービス設計
- [ ] API Gateway、サービスメッシュ
- [ ] **実践**: lab03完了

### Week 7: 可観測性とデリバリー
- [ ] Prometheus、Grafana実践
- [ ] ログ管理と分散トレーシング
- [ ] GitOps、CI/CDパイプライン
- [ ] **実践**: lab04完了

### Week 8: 試験対策
- [ ] practice-exam-01実施
- [ ] 弱点分野の復習
- [ ] 最終模擬試験

---

## 🎯 学習のポイント

### 💡 効果的な学習方法
1. **理論と実践の並行**: 各トピックで理論学習後、必ず実践ラボを実施
2. **反復学習**: 重要概念は複数回異なる角度から学習
3. **コミュニティ活用**: Kubernetes Slack、フォーラムでの質疑応答
4. **公式ドキュメント**: 最新情報は[Kubernetes公式ドキュメント](https://kubernetes.io/docs/)で確認

### ⚠️ 注意点
- **実際の操作経験が重要**: 理論だけでなく、必ず手を動かして学習
- **クラウドネイティブの思想理解**: 技術的な操作だけでなく、思想・哲学も理解
- **最新トレンドの把握**: 急速に進化する分野のため、最新情報の収集が重要
- **英語リソースの活用**: 最新情報や詳細な技術情報は英語で提供されることが多い

---

## 📚 参考資料

### 公式リソース
- [Cloud Native Computing Foundation (CNCF)](https://www.cncf.io/)
- [Kubernetes公式ドキュメント](https://kubernetes.io/docs/)
- [KCNA試験詳細](https://www.cncf.io/certification/kcna/)
- [CNCF Landscape](https://landscape.cncf.io/)

### 技術ドキュメント
- [Docker公式ドキュメント](https://docs.docker.com/)
- [Prometheus公式ドキュメント](https://prometheus.io/docs/)
- [12-Factor App](https://12factor.net/)
- [CNCF GitOps Working Group](https://github.com/cncf/tag-app-delivery/tree/main/gitops-wg)

### 学習リソース
- [Kubernetes Academy](https://kubernetes.academy/)
- [CNCF Learning Paths](https://github.com/cncf/curriculum)
- [Kubernetes Patterns Book](https://k8spatterns.io/)
- [Cloud Native DevOps with Kubernetes](https://www.nginx.com/resources/library/cloud-native-devops-with-kubernetes/)

---

## 🤝 コミュニティとサポート

### オンラインコミュニティ
- **Kubernetes Slack**: [kubernetes.slack.com](https://kubernetes.slack.com/)
- **CNCF Slack**: [cloud-native.slack.com](https://cloud-native.slack.com/)
- **Reddit**: r/kubernetes
- **Stack Overflow**: kubernetes タグ

### 日本語コミュニティ
- **Japan Container Days**: 年次カンファレンス
- **Kubernetes Meetup Tokyo**: 定期勉強会
- **CNCF Tokyo**: 地域コミュニティ

---

## 📊 進捗管理

### 学習進捗チェックリスト

#### 基礎レベル（Week 1-2）
- [ ] Kubernetesアーキテクチャの説明ができる
- [ ] kubectl基本コマンドを操作できる
- [ ] Pod、Service、Deploymentを作成・管理できる
- [ ] ConfigMapとSecretを適切に使用できる

#### 中級レベル（Week 3-6）
- [ ] コンテナランタイムの違いを理解している
- [ ] Dockerfileとマルチステージビルドを書ける
- [ ] マイクロサービスアーキテクチャを設計できる
- [ ] 12ファクターアプリケーションを実装できる

#### 上級レベル（Week 7-8）
- [ ] 監視・可観測性システムを構築できる
- [ ] GitOpsワークフローを実装できる
- [ ] 性能問題をトラブルシューティングできる
- [ ] セキュリティベストプラクティスを適用できる

### 模擬試験スコア記録
| 実施日 | スコア | 苦手分野 | 対策 |
|--------|-------|----------|------|
| Week 6 | ___% | _______ | _____ |
| Week 7 | ___% | _______ | _____ |
| Week 8 | ___% | _______ | _____ |

---

## ✅ 最終チェックリスト

### 試験前の確認事項
- [ ] 全ラボ（lab01-04）を完了している
- [ ] practice-exam-01で75%以上のスコアを安定して取得
- [ ] 各ドメインの重要概念を説明できる
- [ ] 実際のKubernetesクラスターでの操作に慣れている
- [ ] クラウドネイティブの思想・原則を理解している

### 試験当日の準備
- [ ] 安定したインターネット接続
- [ ] 静かな受験環境
- [ ] 身分証明書の準備
- [ ] ブラウザとシステムの動作確認
- [ ] 十分な休息と体調管理

---

## 🎉 合格後のステップ

### 次のレベルの認定試験
1. **CKA (Certified Kubernetes Administrator)**: Kubernetesクラスター管理
2. **CKAD (Certified Kubernetes Application Developer)**: アプリケーション開発
3. **CKS (Certified Kubernetes Security Specialist)**: セキュリティ特化

### キャリア発展
- **Site Reliability Engineer (SRE)**: システム運用・信頼性エンジニア
- **DevOps Engineer**: 開発・運用統合エンジニア
- **Cloud Architect**: クラウドアーキテクト
- **Platform Engineer**: プラットフォームエンジニア

---

**🌟 頑張って学習し、KCNA-JP認定を取得しましょう！**

*この教材は継続的に更新されます。最新版は常にGitリポジトリで確認してください。*