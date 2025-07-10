# Lab 3: モデルデプロイメント

## 🎯 学習目標

このラボでは、機械学習モデルの本番デプロイメントに関する実践的なスキルを習得します：

- SageMaker Endpoint でのリアルタイム推論
- バッチ変換による大量データ処理
- マルチモデルエンドポイントの構築
- A/B テストとカナリアデプロイメント
- Auto Scaling とコスト最適化

## 📋 前提条件

- AWS CLI が設定済み
- SageMaker 実行ロールの作成
- [Lab 2: モデル学習とハイパーパラメータ最適化](./lab02-model-training.md) の完了推奨

## 🏗️ アーキテクチャ概要

```
┌─────────────────────────────────────────────────────────────┐
│                     モデルデプロイメント環境                      │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐     │
│  │   Model     │    │   Batch     │    │   Multi     │     │
│  │   Registry  │    │ Transform   │    │   Model     │     │
│  │             │    │             │    │  Endpoint   │     │
│  └─────┬───────┘    └─────┬───────┘    └─────┬───────┘     │
│        │                  │                  │             │
│        ▼                  ▼                  ▼             │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │                Real-time Endpoint                      │ │
│  │              Auto Scaling & Load Balancing             │ │
│  └─────┬───────────────────────┬───────────────────────────┘ │
│        │                       │                             │
│        ▼                       ▼                             │
│  ┌─────────────┐         ┌─────────────┐                     │
│  │   A/B Test  │         │   Canary    │                     │
│  │  Variants   │         │   Deploy    │                     │
│  └─────────────┘         └─────────────┘                     │
└─────────────────────────────────────────────────────────────┘
```

## 🚀 Step 1: Real-time Endpoint デプロイメント

### 1.1 学習済みモデルの準備

```python
import boto3
import sagemaker
from sagemaker import get_execution_role
from sagemaker.sklearn.model import SKLearnModel
from sagemaker.predictor import Predictor

# SageMaker セッション設定
sagemaker_session = sagemaker.Session()
role = get_execution_role()
region = boto3.Session().region_name

# 学習済みモデルアーティファクトのS3パス
model_artifacts = 's3://your-bucket/sagemaker-models/model.tar.gz'

print(f"Region: {region}")
print(f"Role: {role}")
print(f"Model artifacts: {model_artifacts}")
```

### 1.2 推論コード（inference.py）の作成

```python
# inference.py - カスタム推論ロジック
import json
import joblib
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier

def model_fn(model_dir):
    """モデルの読み込み"""
    try:
        model = joblib.load(f"{model_dir}/model.pkl")
        return model
    except Exception as e:
        raise Exception(f"Failed to load model: {str(e)}")

def input_fn(request_body, request_content_type):
    """入力データの前処理"""
    if request_content_type == 'application/json':
        data = json.loads(request_body)
        
        # DataFrame に変換
        if isinstance(data, dict):
            # 単一の予測の場合
            df = pd.DataFrame([data])
        else:
            # バッチ予測の場合
            df = pd.DataFrame(data)
        
        return df
    
    elif request_content_type == 'text/csv':
        df = pd.read_csv(StringIO(request_body))
        return df
    
    else:
        raise ValueError(f"Unsupported content type: {request_content_type}")

def predict_fn(input_data, model):
    """予測実行"""
    try:
        # 予測確率を取得
        prediction_proba = model.predict_proba(input_data)
        
        # 予測クラスを取得
        prediction = model.predict(input_data)
        
        # 結果をまとめる
        result = {
            'predictions': prediction.tolist(),
            'probabilities': prediction_proba.tolist(),
            'feature_importance': model.feature_importances_.tolist() if hasattr(model, 'feature_importances_') else None
        }
        
        return result
        
    except Exception as e:
        raise Exception(f"Prediction failed: {str(e)}")

def output_fn(prediction, content_type):
    """出力データの後処理"""
    if content_type == 'application/json':
        return json.dumps(prediction)
    else:
        raise ValueError(f"Unsupported content type: {content_type}")
```

### 1.3 モデルデプロイメント

```python
from sagemaker.sklearn.model import SKLearnModel

# SKLearn モデルの定義
sklearn_model = SKLearnModel(
    model_data=model_artifacts,
    role=role,
    entry_point='inference.py',
    framework_version='0.23-1',
    py_version='py3',
    name='ml-model-deployment'
)

# Real-time Endpoint のデプロイ
predictor = sklearn_model.deploy(
    initial_instance_count=1,
    instance_type='ml.m5.large',
    endpoint_name='ml-realtime-endpoint',
    wait=True
)

print(f"Endpoint deployed: {predictor.endpoint_name}")
```

### 1.4 推論テスト

```python
# テストデータの準備
test_data = {
    'feature_1': 5.1,
    'feature_2': 3.5,
    'feature_3': 1.4,
    'feature_4': 0.2
}

# 推論実行
result = predictor.predict(test_data)
print(f"Prediction result: {result}")

# バッチ推論テスト
batch_data = [
    {'feature_1': 5.1, 'feature_2': 3.5, 'feature_3': 1.4, 'feature_4': 0.2},
    {'feature_1': 4.9, 'feature_2': 3.0, 'feature_3': 1.4, 'feature_4': 0.2},
    {'feature_1': 4.7, 'feature_2': 3.2, 'feature_3': 1.3, 'feature_4': 0.2}
]

batch_result = predictor.predict(batch_data)
print(f"Batch prediction result: {batch_result}")
```

## 📊 Step 2: バッチ変換によるデータ処理

### 2.1 バッチ変換ジョブの設定

```python
from sagemaker.transformer import Transformer

# Transformer の作成
transformer = sklearn_model.transformer(
    instance_count=1,
    instance_type='ml.m5.large',
    output_path='s3://your-bucket/batch-transform-output/',
    accept='application/json',
    assemble_with='Line'
)

# バッチ変換の実行
input_data = 's3://your-bucket/batch-input/data.csv'

transformer.transform(
    data=input_data,
    content_type='text/csv',
    split_type='Line',
    job_name='batch-transform-job'
)

# ジョブの監視
transformer.wait()
print(f"Batch transform completed: {transformer.output_path}")
```

### 2.2 大量データ処理の最適化

```python
# 大規模データセット用の設定
large_transformer = sklearn_model.transformer(
    instance_count=3,  # 複数インスタンスで並列処理
    instance_type='ml.m5.2xlarge',
    max_payload=100,  # MB単位
    max_concurrent_transforms=3,
    output_path='s3://your-bucket/large-batch-output/',
    accept='application/json'
)

# データの分割処理
large_input_data = 's3://your-bucket/large-dataset/'

large_transformer.transform(
    data=large_input_data,
    content_type='text/csv',
    split_type='Line',
    job_name='large-batch-transform'
)
```

## 🔄 Step 3: マルチモデルエンドポイント

### 3.1 マルチモデルエンドポイントの構築

```python
from sagemaker.multidatamodel import MultiDataModel

# マルチモデルエンドポイント用のモデル準備
model_data_prefix = 's3://your-bucket/multi-models/'

# 複数のモデルアーティファクトを配置
models = {
    'model-v1': 's3://your-bucket/models/model-v1.tar.gz',
    'model-v2': 's3://your-bucket/models/model-v2.tar.gz',
    'model-v3': 's3://your-bucket/models/model-v3.tar.gz'
}

# MultiDataModel の作成
multi_model = MultiDataModel(
    name='multi-model-endpoint',
    model_data_prefix=model_data_prefix,
    model=sklearn_model,
    sagemaker_session=sagemaker_session
)

# エンドポイントのデプロイ
multi_predictor = multi_model.deploy(
    initial_instance_count=1,
    instance_type='ml.m5.large',
    endpoint_name='multi-model-endpoint'
)
```

### 3.2 動的モデル追加・削除

```python
# 新しいモデルの追加
multi_model.add_model(
    model_data_source='s3://your-bucket/models/model-v4.tar.gz',
    model_data_path='model-v4.tar.gz'
)

# モデルのリスト表示
models_list = multi_model.list_models()
print(f"Available models: {models_list}")

# 特定モデルでの推論
test_data = {'feature_1': 5.1, 'feature_2': 3.5}

# model-v2 を使用して推論
result_v2 = multi_predictor.predict(
    data=test_data,
    target_model='model-v2.tar.gz'
)
print(f"Model v2 result: {result_v2}")

# モデルの削除
multi_model.delete_model('model-v1.tar.gz')
```

## ⚖️ Step 4: A/B テストとカナリアデプロイメント

### 4.1 A/B テスト環境の構築

```python
from sagemaker.model import Model

# モデルA（既存）とモデルB（新バージョン）の準備
model_a = SKLearnModel(
    model_data='s3://your-bucket/models/model-a.tar.gz',
    role=role,
    entry_point='inference.py',
    framework_version='0.23-1',
    name='model-a'
)

model_b = SKLearnModel(
    model_data='s3://your-bucket/models/model-b.tar.gz',
    role=role,
    entry_point='inference.py',
    framework_version='0.23-1',
    name='model-b'
)

# Production Variant の設定
from sagemaker.model import Model

# A/B テスト用エンドポイント設定
ab_test_config = [
    {
        'VariantName': 'model-a-variant',
        'ModelName': model_a.name,
        'InitialInstanceCount': 1,
        'InstanceType': 'ml.m5.large',
        'InitialVariantWeight': 70  # 70%のトラフィック
    },
    {
        'VariantName': 'model-b-variant',
        'ModelName': model_b.name,
        'InitialInstanceCount': 1,
        'InstanceType': 'ml.m5.large',
        'InitialVariantWeight': 30  # 30%のトラフィック
    }
]

# エンドポイント作成（低レベルAPI使用）
sagemaker_client = boto3.client('sagemaker')

endpoint_config_name = 'ab-test-endpoint-config'
endpoint_name = 'ab-test-endpoint'

# エンドポイント設定の作成
sagemaker_client.create_endpoint_config(
    EndpointConfigName=endpoint_config_name,
    ProductionVariants=ab_test_config
)

# エンドポイントの作成
sagemaker_client.create_endpoint(
    EndpointName=endpoint_name,
    EndpointConfigName=endpoint_config_name
)
```

### 4.2 トラフィック配分の動的変更

```python
# トラフィック配分の更新
def update_traffic_distribution(endpoint_name, variant_weights):
    """
    エンドポイントのトラフィック配分を更新
    
    Args:
        endpoint_name: エンドポイント名
        variant_weights: バリアント重み {'variant_name': weight}
    """
    sagemaker_client = boto3.client('sagemaker')
    
    # 現在のエンドポイント設定を取得
    response = sagemaker_client.describe_endpoint(EndpointName=endpoint_name)
    
    # 新しいバリアント設定
    updated_variants = []
    for variant in response['ProductionVariants']:
        variant_name = variant['VariantName']
        if variant_name in variant_weights:
            variant['CurrentWeight'] = variant_weights[variant_name]
        updated_variants.append({
            'VariantName': variant_name,
            'CurrentWeight': variant.get('CurrentWeight', 0)
        })
    
    # エンドポイント設定を更新
    sagemaker_client.update_endpoint_weights_and_capacities(
        EndpointName=endpoint_name,
        DesiredWeightsAndCapacities=updated_variants
    )
    
    print(f"Traffic distribution updated for {endpoint_name}")

# カナリアデプロイメント（段階的な配分変更）
# Stage 1: 10% to new model
update_traffic_distribution(endpoint_name, {
    'model-a-variant': 90,
    'model-b-variant': 10
})

# メトリクス監視後、Stage 2: 50% to new model
update_traffic_distribution(endpoint_name, {
    'model-a-variant': 50,
    'model-b-variant': 50
})

# 最終的に新モデルに完全移行
update_traffic_distribution(endpoint_name, {
    'model-a-variant': 0,
    'model-b-variant': 100
})
```

## 📈 Step 5: Auto Scaling とコスト最適化

### 5.1 Auto Scaling の設定

```python
import boto3

# Application Auto Scaling の設定
autoscaling_client = boto3.client('application-autoscaling')

# Scalable Target の登録
resource_id = f"endpoint/{endpoint_name}/variant/model-variant"

autoscaling_client.register_scalable_target(
    ServiceNamespace='sagemaker',
    ResourceId=resource_id,
    ScalableDimension='sagemaker:variant:DesiredInstanceCount',
    MinCapacity=1,
    MaxCapacity=10,
    RoleArn='arn:aws:iam::account:role/application-autoscaling-sagemaker-role'
)

# スケーリングポリシーの作成
policy_name = 'sagemaker-scaling-policy'

autoscaling_client.put_scaling_policy(
    PolicyName=policy_name,
    ServiceNamespace='sagemaker',
    ResourceId=resource_id,
    ScalableDimension='sagemaker:variant:DesiredInstanceCount',
    PolicyType='TargetTrackingScaling',
    TargetTrackingScalingPolicyConfiguration={
        'TargetValue': 70.0,  # 70% CPU使用率を目標
        'PredefinedMetricSpecification': {
            'PredefinedMetricType': 'SageMakerVariantInvocationsPerInstance'
        },
        'ScaleOutCooldown': 300,  # 5分
        'ScaleInCooldown': 300
    }
)

print(f"Auto scaling configured for {endpoint_name}")
```

### 5.2 Serverless Inference の利用

```python
from sagemaker.serverless import ServerlessInferenceConfig

# Serverless 設定
serverless_config = ServerlessInferenceConfig(
    memory_size_in_mb=3008,  # 最大6008MB
    max_concurrency=10       # 最大同時実行数
)

# Serverless Endpoint のデプロイ
serverless_predictor = sklearn_model.deploy(
    serverless_inference_config=serverless_config,
    endpoint_name='serverless-ml-endpoint'
)

print(f"Serverless endpoint deployed: {serverless_predictor.endpoint_name}")

# Serverless での推論テスト
test_result = serverless_predictor.predict(test_data)
print(f"Serverless prediction: {test_result}")
```

### 5.3 コスト監視とアラート

```python
import boto3

def setup_cost_monitoring(endpoint_name):
    """コスト監視とアラートの設定"""
    
    cloudwatch = boto3.client('cloudwatch')
    
    # コストアラームの作成
    cloudwatch.put_metric_alarm(
        AlarmName=f'{endpoint_name}-cost-alarm',
        ComparisonOperator='GreaterThanThreshold',
        EvaluationPeriods=1,
        MetricName='EstimatedCharges',
        Namespace='AWS/Billing',
        Period=86400,  # 1日
        Statistic='Maximum',
        Threshold=100.0,  # $100/日
        ActionsEnabled=True,
        AlarmActions=[
            'arn:aws:sns:region:account:cost-alarm-topic'
        ],
        AlarmDescription=f'Cost alarm for {endpoint_name}',
        Dimensions=[
            {
                'Name': 'Currency',
                'Value': 'USD'
            }
        ]
    )
    
    # 推論回数のアラーム
    cloudwatch.put_metric_alarm(
        AlarmName=f'{endpoint_name}-invocation-alarm',
        ComparisonOperator='GreaterThanThreshold',
        EvaluationPeriods=2,
        MetricName='Invocations',
        Namespace='AWS/SageMaker',
        Period=300,
        Statistic='Sum',
        Threshold=1000.0,  # 5分間で1000回以上
        ActionsEnabled=True,
        AlarmActions=[
            'arn:aws:sns:region:account:invocation-alarm-topic'
        ],
        AlarmDescription=f'High invocation rate for {endpoint_name}',
        Dimensions=[
            {
                'Name': 'EndpointName',
                'Value': endpoint_name
            }
        ]
    )
    
    print(f"Cost monitoring configured for {endpoint_name}")

# モニタリング設定の実行
setup_cost_monitoring(endpoint_name)
```

## 🔍 Step 6: モニタリングとロギング

### 6.1 CloudWatch メトリクスの監視

```python
def get_endpoint_metrics(endpoint_name, start_time, end_time):
    """エンドポイントのメトリクスを取得"""
    
    cloudwatch = boto3.client('cloudwatch')
    
    metrics = [
        'Invocations',
        'InvocationsPerInstance', 
        'ModelLatency',
        'OverheadLatency'
    ]
    
    results = {}
    
    for metric in metrics:
        response = cloudwatch.get_metric_statistics(
            Namespace='AWS/SageMaker',
            MetricName=metric,
            Dimensions=[
                {
                    'Name': 'EndpointName',
                    'Value': endpoint_name
                }
            ],
            StartTime=start_time,
            EndTime=end_time,
            Period=300,  # 5分間隔
            Statistics=['Average', 'Maximum', 'Sum']
        )
        
        results[metric] = response['Datapoints']
    
    return results

# メトリクス取得例
from datetime import datetime, timedelta

end_time = datetime.utcnow()
start_time = end_time - timedelta(hours=1)

metrics = get_endpoint_metrics(endpoint_name, start_time, end_time)
print(f"Endpoint metrics: {metrics}")
```

### 6.2 Data Capture の設定

```python
from sagemaker.model_monitor import DataCaptureConfig

# Data Capture 設定
data_capture_config = DataCaptureConfig(
    enable_capture=True,
    sampling_percentage=100,  # 100%のリクエストをキャプチャ
    destination_s3_uri='s3://your-bucket/data-capture/',
    capture_options=["REQUEST", "RESPONSE"]
)

# Data Capture 有効化でのデプロイ
predictor_with_capture = sklearn_model.deploy(
    initial_instance_count=1,
    instance_type='ml.m5.large',
    endpoint_name='ml-endpoint-with-capture',
    data_capture_config=data_capture_config
)

print(f"Endpoint with data capture deployed: {predictor_with_capture.endpoint_name}")
```

## 🧹 Step 7: リソースクリーンアップ

### 7.1 エンドポイントの削除

```python
# リアルタイムエンドポイントの削除
predictor.delete_endpoint()
print(f"Endpoint {predictor.endpoint_name} deleted")

# マルチモデルエンドポイントの削除
multi_predictor.delete_endpoint()
print(f"Multi-model endpoint {multi_predictor.endpoint_name} deleted")

# Serverless エンドポイントの削除
serverless_predictor.delete_endpoint()
print(f"Serverless endpoint {serverless_predictor.endpoint_name} deleted")
```

### 7.2 モデルとエンドポイント設定の削除

```python
sagemaker_client = boto3.client('sagemaker')

# エンドポイント設定の削除
try:
    sagemaker_client.delete_endpoint_config(
        EndpointConfigName=endpoint_config_name
    )
    print(f"Endpoint config {endpoint_config_name} deleted")
except Exception as e:
    print(f"Error deleting endpoint config: {e}")

# モデルの削除
try:
    sagemaker_client.delete_model(ModelName=sklearn_model.name)
    print(f"Model {sklearn_model.name} deleted")
except Exception as e:
    print(f"Error deleting model: {e}")
```

## 💰 コスト計算

### 推定コスト
- **ml.m5.large インスタンス**: $0.115/時間
- **データ転送**: $0.09/GB
- **ストレージ**: $0.023/GB/月

### 1時間の実習コスト
- リアルタイムエンドポイント: $0.115
- バッチ変換: $0.115
- データ転送・ストレージ: $0.05
- **合計**: 約 $0.28/時間

## 📚 学習ポイント

### 重要な概念
1. **デプロイメント戦略**: リアルタイム vs バッチ vs マルチモデル
2. **スケーリング**: Auto Scaling とServerless
3. **A/B テスト**: 段階的デプロイメント
4. **監視**: CloudWatch メトリクスとData Capture
5. **コスト最適化**: 適切なインスタンスタイプ選択

### 実践的なスキル
- エンドポイントのデプロイと管理
- トラフィック配分の制御
- 性能監視とアラート設定
- コスト効果的なデプロイメント戦略

---

**次のステップ**: [Lab 4: MLOpsパイプライン](./lab04-mlops-pipeline.md) では、継続的インテグレーション・デプロイメント（CI/CD）パイプラインの構築を学習します。