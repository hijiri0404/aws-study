# AWS Certified Machine Learning Engineer - Associate (MLA-C01)

## 📋 試験概要

**正式名称**: AWS Certified Machine Learning Engineer - Associate  
**試験コード**: MLA-C01  
**難易度**: ⭐⭐⭐⭐  
**試験時間**: 170分  
**問題数**: 65問  
**費用**: $150 USD  
**合格点**: 720/1000  

### 📊 試験ドメインと配点

1. **Domain 1: Data Preparation for Machine Learning** - 28%
2. **Domain 2: ML Model Development** - 26% 
3. **Domain 3: ML Solution Monitoring, Maintenance, and Security** - 24%
4. **Domain 4: Deployment and Orchestration of ML Workflows** - 22%

## 🎯 対象者

- **推奨経験**: ML エンジニアリング 1年以上
- **AWS経験**: AWS サービス 1年以上
- **前提資格**: なし（ただし Associate レベル推奨）

### 必要なスキル
- Python プログラミング
- 機械学習の基礎知識
- SageMaker の実務経験
- MLOps の理解

## 🗂️ 教材構成

### 📚 基礎教材
- `00-fundamentals.md` - 試験概要と学習戦略
- `01-exam-guide.md` - 詳細な出題範囲

### 🔬 ハンズオンラボ
- `labs/lab01-data-preparation/` - データ準備とFeature Store
- `labs/lab02-model-development/` - SageMakerでのモデル開発
- `labs/lab03-model-deployment/` - モデルデプロイメント
- `labs/lab04-mlops-pipeline/` - MLOpsパイプライン構築
- `labs/lab05-monitoring/` - モデル監視とメンテナンス

### 📝 問題演習
- `practice-exams/` - 想定問題集
- `troubleshooting/` - よくある問題と解決策

## 🚀 学習順序（推奨）

### Phase 1: 基礎固め（1-2週間）
1. **基礎教材の学習**
   - AWS ML サービス概要
   - SageMaker の基本操作
   - MLライフサイクルの理解

### Phase 2: ハンズオン実践（3-4週間）  
2. **Lab 1: データ準備**
   - Feature Store の構築
   - データ前処理パイプライン
   
3. **Lab 2: モデル開発**
   - SageMaker Studio での開発
   - ビルトインアルゴリズムの使用
   
4. **Lab 3: モデルデプロイメント**
   - リアルタイム推論エンドポイント
   - バッチ変換ジョブ

### Phase 3: MLOps 実装（2-3週間）
5. **Lab 4: MLOpsパイプライン**
   - SageMaker Pipelines
   - Model Registry の活用
   
6. **Lab 5: 監視とメンテナンス**
   - Model Monitor の設定
   - データドリフト検出

### Phase 4: 試験対策（1週間）
7. **問題演習**
   - 想定問題集で実力確認
   - 苦手分野の復習

## 💰 費用概算

### ハンズオンラボ実行コスト
| ラボ | 推定時間 | 推定コスト |
|------|----------|------------|
| Lab 1 | 4-6時間 | $15-25 |
| Lab 2 | 8-12時間 | $30-50 |
| Lab 3 | 6-8時間 | $20-35 |
| Lab 4 | 10-15時間 | $40-60 |
| Lab 5 | 4-6時間 | $15-25 |

**総計**: $120-195 (全ラボ完了時)

### コスト削減のコツ
- SageMaker Studio Lab の無料枠を活用
- ml.t3.medium インスタンスを使用
- 不要なリソースは即座に削除
- スポットインスタンスの活用

## 🛠️ 事前準備

### 必要な環境
```bash
# AWS CLI インストール・設定
aws configure
aws sts get-caller-identity

# Python 環境セットアップ
pip install sagemaker pandas scikit-learn matplotlib
```

### 権限設定
- SageMaker FullAccess
- S3 読み書き権限
- IAM ロール作成権限
- CloudWatch ログ読み取り権限

## 📊 学習進捗管理

### チェックリスト
- [ ] 基礎教材完了
- [ ] Lab 1: データ準備完了
- [ ] Lab 2: モデル開発完了  
- [ ] Lab 3: デプロイメント完了
- [ ] Lab 4: MLOpsパイプライン完了
- [ ] Lab 5: 監視設定完了
- [ ] 想定問題集 80%以上正解

### 学習記録
```
Week 1: 基礎固め
Week 2-3: Lab 1-2 実践
Week 4-5: Lab 3-4 実践  
Week 6: Lab 5 + 問題演習
Week 7: 最終調整 + 受験
```

## 🔗 参考リソース

### AWS公式
- [AWS Skill Builder](https://skillbuilder.aws/)
- [SageMaker Examples](https://github.com/aws/amazon-sagemaker-examples)
- [SageMaker Developer Guide](https://docs.aws.amazon.com/sagemaker/)

### コミュニティ
- AWS MLコミュニティ
- SageMaker公式ブログ
- re:Invent セッション動画

---

**重要**: この試験は実践重視です。単なる暗記ではなく、実際にSageMakerを操作してMLワークフローを構築できることが求められます。