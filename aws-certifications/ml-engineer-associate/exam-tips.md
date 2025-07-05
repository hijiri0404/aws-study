# AWS Machine Learning Engineer Associate 試験対策のポイント

## 🎯 試験概要と戦略

### 試験の特徴
- **実装重視**: 理論よりも実際のMLワークフローの構築能力
- **SageMaker中心**: AWS SageMakerの深い理解が必要
- **MLOps強化**: 機械学習のDevOps実践が重要
- **時間配分**: 170分で65問（約2.6分/問）

### 効果的な時間配分
```
問題解答フェーズ:
├── 第1回転: 確実に分かる問題 (50分)
├── 第2回転: 考えれば分かる問題 (80分)  
├── 第3回転: 難問・推測問題 (25分)
└── 最終確認: マーク問題の見直し (15分)
```

## 📋 ドメイン別対策

### Domain 1: Data Preparation for Machine Learning (28%)

#### 頻出トピック
1. **データソース統合**
   - S3, Redshift, RDS, DynamoDB からのデータ取得
   - AWS Glue による ETL処理
   - データフォーマット変換

2. **Feature Engineering**
   - SageMaker Processing での前処理
   - 特徴量変換・スケーリング
   - 欠損値処理・外れ値検出

3. **Feature Store**
   - SageMaker Feature Store の活用
   - オンライン・オフライン特徴量ストア
   - 特徴量の versioning

#### 重要なコードパターン
```python
# SageMaker Processing
from sagemaker.processing import ScriptProcessor

processor = ScriptProcessor(
    command=['python3'],
    image_uri='python:3.8-slim',
    role=role,
    instance_count=1,
    instance_type='ml.m5.xlarge'
)

processor.run(
    code='preprocessing.py',
    inputs=[ProcessingInput(
        input_name='raw-data',
        source='s3://bucket/raw-data/',
        destination='/opt/ml/processing/input'
    )],
    outputs=[ProcessingOutput(
        output_name='processed-data',
        source='/opt/ml/processing/output'
    )]
)
```

#### よくある間違い
- ❌ 生データをそのまま学習に使用
- ✅ 適切な前処理・特徴量エンジニアリング
- ❌ 手動でのデータ変換
- ✅ SageMaker Processing による自動化

### Domain 2: ML Model Development (26%)

#### 頻出トピック
1. **SageMaker Studio**
   - Jupyter notebooks
   - SageMaker Experiments
   - Model debugging & profiling

2. **アルゴリズム選択**
   - Built-in algorithms
   - Custom algorithms (BYOC)
   - Hugging Face integration

3. **Hyperparameter Tuning**
   - 自動ハイパーパラメータチューニング
   - 早期停止戦略
   - 並列ジョブ実行

#### SageMaker訓練パターン
```python
# Built-in algorithm
from sagemaker.xgboost import XGBoost

xgb = XGBoost(
    entry_point='train.py',
    role=role,
    instance_count=1,
    instance_type='ml.m5.xlarge',
    framework_version='1.3-1',
    hyperparameters={
        'objective': 'binary:logistic',
        'num_round': 100
    }
)

xgb.fit({'train': train_data, 'validation': val_data})
```

#### よくある間違い
- ❌ 適切な検証データ分割なし
- ✅ train/validation/test の適切な分割
- ❌ ハイパーパラメータの手動調整
- ✅ 自動ハイパーパラメータチューニング

### Domain 3: ML Solution Monitoring, Maintenance, and Security (24%)

#### 頻出トピック
1. **Model Monitor**
   - データドリフト検出
   - モデル品質監視
   - Baseline statistics

2. **Security**
   - IAM roles & policies
   - VPC configuration
   - Encryption at rest/in transit

3. **Model Registry**
   - モデルバージョン管理
   - Model packages
   - Approval workflows

#### Model Monitor設定
```python
# Data Quality Monitor
from sagemaker.model_monitor import DataCaptureConfig, ModelQualityMonitor

data_capture_config = DataCaptureConfig(
    enable_capture=True,
    sampling_percentage=100,
    destination_s3_uri='s3://bucket/data-capture'
)

model_quality_monitor = ModelQualityMonitor(
    role=role,
    instance_count=1,
    instance_type='ml.m5.xlarge',
    volume_size_in_gb=20,
    max_runtime_in_seconds=1800
)
```

#### セキュリティベストプラクティス
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "sagemaker:CreateTrainingJob",
        "sagemaker:DescribeTrainingJob"
      ],
      "Resource": "*",
      "Condition": {
        "StringEquals": {
          "sagemaker:VolumeKmsKey": "arn:aws:kms:region:account:key/key-id"
        }
      }
    }
  ]
}
```

### Domain 4: Deployment and Orchestration of ML Workflows (22%)

#### 頻出トピック
1. **Inference Endpoints**
   - Real-time endpoints
   - Batch transform jobs
   - Multi-model endpoints
   - Serverless inference

2. **SageMaker Pipelines**
   - ワークフロー定義
   - 条件分岐
   - 並列処理

3. **Edge Deployment**
   - SageMaker Edge Manager
   - IoT Greengrass integration
   - Model optimization

#### SageMaker Pipelines例
```python
from sagemaker.workflow.pipeline import Pipeline
from sagemaker.workflow.steps import ProcessingStep, TrainingStep

# Processing Step
processing_step = ProcessingStep(
    name='PreprocessData',
    processor=processor,
    inputs=[ProcessingInput(
        input_name='raw-data',
        source='s3://bucket/raw-data/'
    )],
    outputs=[ProcessingOutput(
        output_name='processed-data',
        source='/opt/ml/processing/output'
    )]
)

# Training Step
training_step = TrainingStep(
    name='TrainModel',
    estimator=xgb,
    inputs={'train': processing_step.properties.ProcessingOutputConfig.Outputs['processed-data'].S3Output.S3Uri}
)

# Pipeline
pipeline = Pipeline(
    name='MLPipeline',
    steps=[processing_step, training_step]
)
```

## 🔧 試験テクニック

### 問題解答のコツ

#### 1. SageMaker機能の使い分け
- **Training Jobs**: 一回限りの学習
- **Processing Jobs**: データ前処理
- **Transform Jobs**: バッチ推論
- **Endpoints**: リアルタイム推論

#### 2. コスト最適化の選択
- **Spot Training**: 学習コスト削減
- **Multi-Model Endpoints**: 推論コスト削減
- **Serverless Inference**: 使用量が少ない場合

#### 3. スケーリング戦略
- **Auto Scaling**: トラフィック変動対応
- **Multi-AZ**: 高可用性
- **Distributed Training**: 大規模データ

### MLワークフロー設計パターン

#### 1. データ準備パターン
```
S3 Raw Data → Glue ETL → SageMaker Processing → Feature Store → Training Data
```

#### 2. 学習パターン
```
Training Data → SageMaker Training → Model Registry → Model Approval → Deployment
```

#### 3. 推論パターン
```
Input Data → Preprocessing → Model Inference → Postprocessing → Output
```

## 📚 重要なMLコンセプト

### 評価指標の理解
```python
# 分類問題
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score

# 回帰問題
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score

# 使い分け
accuracy = accuracy_score(y_true, y_pred)      # バランスの取れたデータ
precision = precision_score(y_true, y_pred)    # 偽陽性を減らしたい
recall = recall_score(y_true, y_pred)          # 偽陰性を減らしたい
f1 = f1_score(y_true, y_pred)                 # 総合的な評価
```

### データ分割戦略
```python
# 時系列データ
train_data = data[data['date'] < '2023-01-01']
val_data = data[(data['date'] >= '2023-01-01') & (data['date'] < '2023-07-01')]
test_data = data[data['date'] >= '2023-07-01']

# 通常のデータ
from sklearn.model_selection import train_test_split
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
```

## 🎯 最終確認チェックリスト

### 1週間前
- [ ] SageMaker全機能の理解
- [ ] MLワークフローの設計能力
- [ ] 模擬試験で700点以上

### 前日
- [ ] 試験時間・会場の確認
- [ ] ML評価指標の復習
- [ ] SageMaker制限値の確認

### 当日朝
- [ ] 実践的な問題への準備
- [ ] SageMaker SDK の理解確認
- [ ] リラックスして集中力を維持

## 🔍 よくある間違いと対策

### 1. データ漏洩の回避
- ❌ 前処理でテストデータを使用
- ✅ 学習データのみで前処理パラメータ決定

### 2. 過学習の防止
- ❌ 訓練データの精度のみで評価
- ✅ 検証データで早期停止

### 3. 本番環境考慮
- ❌ 学習環境でのみ動作するモデル
- ✅ 本番環境でのスケーラビリティ考慮

## 💡 合格のための最終アドバイス

### 実践の重要性
- 理論だけでなく実際にSageMakerで構築
- エラーやトラブルシューティング経験
- 複数のMLプロジェクトの完遂

### 学習のコツ
1. **手を動かす**: 実際にコードを書いて実行
2. **ドキュメント活用**: SageMaker Developer Guide
3. **サンプル活用**: SageMaker Examples
4. **コミュニティ**: AWS ML Community

### 試験当日の心構え
- **実装経験を活かす**: 実際の経験から判断
- **SageMaker優先**: AWS managed serviceを選択
- **コスト効率**: 最適なインスタンス選択
- **スケーラビリティ**: 本番運用を考慮

---

**頑張れ！** 機械学習エンジニアとしての実践力が試される試験です。あなたの学習努力と実装経験が必ず合格につながります。