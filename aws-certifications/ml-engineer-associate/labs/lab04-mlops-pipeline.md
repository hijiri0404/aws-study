# Lab 4: MLOpsパイプライン

## 🎯 学習目標

このラボでは、MLOps（Machine Learning Operations）の包括的なパイプラインを構築し、機械学習のライフサイクル全体を自動化します：

- SageMaker Pipelines による ML ワークフロー自動化
- CI/CD パイプラインの構築
- モデルレジストリとバージョン管理
- モデル監視と自動再学習
- Infrastructure as Code (IaC) の実装

## 📋 前提条件

- AWS CLI が設定済み
- CodeCommit、CodeBuild、CodePipeline の基本知識
- [Lab 3: モデルデプロイメント](./lab03-model-deployment.md) の完了推奨

## 🏗️ アーキテクチャ概要

```
┌─────────────────────────────────────────────────────────────┐
│                        MLOps Pipeline                      │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐     │
│  │   Source    │    │   Build     │    │   Deploy    │     │
│  │ CodeCommit  │───▶│ CodeBuild   │───▶│ CodePipeline│     │
│  │   GitHub    │    │   Testing   │    │  SageMaker  │     │
│  └─────────────┘    └─────────────┘    └─────────────┘     │
│                                                             │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │              SageMaker Pipeline                         │ │
│  │  Data Processing ─▶ Training ─▶ Evaluation ─▶ Deploy  │ │
│  └─────┬───────────────────────┬───────────────────────────┘ │
│        │                       │                             │
│        ▼                       ▼                             │
│  ┌─────────────┐         ┌─────────────┐                     │
│  │   Model     │         │   Monitor   │                     │
│  │  Registry   │         │  & Retrain  │                     │
│  └─────────────┘         └─────────────┘                     │
└─────────────────────────────────────────────────────────────┘
```

## 🚀 Step 1: SageMaker Pipelines の構築

### 1.1 Pipeline 定義とステップ作成

```python
import boto3
import sagemaker
from sagemaker.workflow.pipeline import Pipeline
from sagemaker.workflow.steps import ProcessingStep, TrainingStep
from sagemaker.workflow.step_collections import RegisterModel
from sagemaker.workflow.conditions import ConditionGreaterThanOrEqualTo
from sagemaker.workflow.condition_step import ConditionStep
from sagemaker.workflow.functions import JsonGet
from sagemaker.workflow.properties import PropertyFile
from sagemaker.workflow.parameters import ParameterString, ParameterFloat

# パラメータ定義
input_data = ParameterString(
    name="InputData",
    default_value="s3://your-bucket/input-data/",
    description="Input data location"
)

model_approval_status = ParameterString(
    name="ModelApprovalStatus", 
    default_value="Approved",
    description="Model approval status"
)

accuracy_threshold = ParameterFloat(
    name="AccuracyThreshold",
    default_value=0.8,
    description="Minimum accuracy for model approval"
)

print("Pipeline parameters defined")
```

### 1.2 データ前処理ステップ

```python
from sagemaker.sklearn.processing import SKLearnProcessor
from sagemaker.processing import ProcessingInput, ProcessingOutput

# 前処理スクリプト
preprocessing_script = """
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
import joblib
import argparse
import os

def preprocess_data():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input-data', type=str, required=True)
    args = parser.parse_args()
    
    # データ読み込み
    print(f"Loading data from {args.input_data}")
    df = pd.read_csv(f"{args.input_data}/data.csv")
    
    # データクリーニング
    df = df.dropna()
    df = df[df['target'].notnull()]
    
    # 特徴量とターゲットの分離
    X = df.drop(['target'], axis=1)
    y = df['target']
    
    # 訓練・検証・テストデータに分割
    X_temp, X_test, y_temp, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    X_train, X_val, y_train, y_val = train_test_split(
        X_temp, y_temp, test_size=0.25, random_state=42, stratify=y_temp
    )
    
    # 特徴量標準化
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_val_scaled = scaler.transform(X_val)
    X_test_scaled = scaler.transform(X_test)
    
    # データ保存
    output_dir = "/opt/ml/processing/output"
    os.makedirs(output_dir, exist_ok=True)
    
    # 訓練データ
    train_df = pd.DataFrame(X_train_scaled)
    train_df['target'] = y_train.values
    train_df.to_csv(f"{output_dir}/train.csv", index=False)
    
    # 検証データ
    val_df = pd.DataFrame(X_val_scaled)
    val_df['target'] = y_val.values
    val_df.to_csv(f"{output_dir}/validation.csv", index=False)
    
    # テストデータ
    test_df = pd.DataFrame(X_test_scaled)
    test_df['target'] = y_test.values
    test_df.to_csv(f"{output_dir}/test.csv", index=False)
    
    # スケーラー保存
    joblib.dump(scaler, f"{output_dir}/scaler.pkl")
    
    print("Data preprocessing completed")

if __name__ == "__main__":
    preprocess_data()
"""

# 前処理ステップの定義
sklearn_processor = SKLearnProcessor(
    framework_version="0.23-1",
    instance_type="ml.m5.large",
    instance_count=1,
    base_job_name="ml-preprocessing",
    role=sagemaker.get_execution_role()
)

processing_step = ProcessingStep(
    name="DataPreprocessing",
    processor=sklearn_processor,
    inputs=[
        ProcessingInput(
            source=input_data,
            destination="/opt/ml/processing/input"
        )
    ],
    outputs=[
        ProcessingOutput(
            output_name="train_data",
            source="/opt/ml/processing/output/train.csv"
        ),
        ProcessingOutput(
            output_name="validation_data", 
            source="/opt/ml/processing/output/validation.csv"
        ),
        ProcessingOutput(
            output_name="test_data",
            source="/opt/ml/processing/output/test.csv"
        ),
        ProcessingOutput(
            output_name="scaler",
            source="/opt/ml/processing/output/scaler.pkl"
        )
    ],
    code="preprocessing.py"
)

print("Data preprocessing step defined")
```

### 1.3 モデル学習ステップ

```python
from sagemaker.sklearn.estimator import SKLearn
from sagemaker.inputs import TrainingInput

# 学習スクリプト
training_script = """
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report
import joblib
import json
import argparse
import os

def train_model():
    parser = argparse.ArgumentParser()
    parser.add_argument('--n-estimators', type=int, default=100)
    parser.add_argument('--max-depth', type=int, default=10)
    parser.add_argument('--min-samples-split', type=int, default=2)
    args = parser.parse_args()
    
    # 訓練データ読み込み
    train_df = pd.read_csv('/opt/ml/input/data/train/train.csv')
    val_df = pd.read_csv('/opt/ml/input/data/validation/validation.csv')
    
    # 特徴量とターゲットの分離
    X_train = train_df.drop(['target'], axis=1)
    y_train = train_df['target']
    X_val = val_df.drop(['target'], axis=1)
    y_val = val_df['target']
    
    # モデル学習
    model = RandomForestClassifier(
        n_estimators=args.n_estimators,
        max_depth=args.max_depth,
        min_samples_split=args.min_samples_split,
        random_state=42
    )
    
    model.fit(X_train, y_train)
    
    # モデル評価
    train_pred = model.predict(X_train)
    val_pred = model.predict(X_val)
    
    train_accuracy = accuracy_score(y_train, train_pred)
    val_accuracy = accuracy_score(y_val, val_pred)
    
    # メトリクス保存
    metrics = {
        'train_accuracy': float(train_accuracy),
        'validation_accuracy': float(val_accuracy),
        'model_parameters': {
            'n_estimators': args.n_estimators,
            'max_depth': args.max_depth,
            'min_samples_split': args.min_samples_split
        }
    }
    
    # モデル保存
    model_dir = '/opt/ml/model'
    os.makedirs(model_dir, exist_ok=True)
    joblib.dump(model, f'{model_dir}/model.pkl')
    
    # メトリクス保存
    with open(f'{model_dir}/metrics.json', 'w') as f:
        json.dump(metrics, f)
    
    print(f"Training completed. Validation accuracy: {val_accuracy}")

if __name__ == "__main__":
    train_model()
"""

# 学習用 Estimator
sklearn_estimator = SKLearn(
    entry_point="training.py",
    framework_version="0.23-1",
    instance_type="ml.m5.large",
    role=sagemaker.get_execution_role(),
    hyperparameters={
        'n-estimators': 100,
        'max-depth': 10
    }
)

# 学習ステップの定義
training_step = TrainingStep(
    name="ModelTraining",
    estimator=sklearn_estimator,
    inputs={
        "train": TrainingInput(
            s3_data=processing_step.properties.ProcessingOutputConfig.Outputs[
                "train_data"
            ].S3Output.S3Uri
        ),
        "validation": TrainingInput(
            s3_data=processing_step.properties.ProcessingOutputConfig.Outputs[
                "validation_data"
            ].S3Output.S3Uri
        )
    }
)

print("Model training step defined")
```

### 1.4 モデル評価ステップ

```python
# 評価スクリプト
evaluation_script = """
import pandas as pd
import numpy as np
import joblib
import json
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
import argparse

def evaluate_model():
    # テストデータ読み込み
    test_df = pd.read_csv('/opt/ml/processing/input/test.csv')
    X_test = test_df.drop(['target'], axis=1)
    y_test = test_df['target']
    
    # モデル読み込み
    model = joblib.load('/opt/ml/processing/model/model.pkl')
    
    # 予測実行
    y_pred = model.predict(X_test)
    
    # メトリクス計算
    accuracy = accuracy_score(y_test, y_pred)
    precision = precision_score(y_test, y_pred, average='weighted')
    recall = recall_score(y_test, y_pred, average='weighted')
    f1 = f1_score(y_test, y_pred, average='weighted')
    
    # 評価結果
    evaluation_result = {
        'classification_metrics': {
            'accuracy': {'value': float(accuracy)},
            'precision': {'value': float(precision)},
            'recall': {'value': float(recall)},
            'f1_score': {'value': float(f1)}
        }
    }
    
    # 結果保存
    output_dir = "/opt/ml/processing/evaluation"
    os.makedirs(output_dir, exist_ok=True)
    
    with open(f"{output_dir}/evaluation.json", "w") as f:
        json.dump(evaluation_result, f)
    
    print(f"Model evaluation completed. Accuracy: {accuracy}")

if __name__ == "__main__":
    evaluate_model()
"""

# 評価ステップの定義
evaluation_step = ProcessingStep(
    name="ModelEvaluation",
    processor=sklearn_processor,
    inputs=[
        ProcessingInput(
            source=processing_step.properties.ProcessingOutputConfig.Outputs[
                "test_data"
            ].S3Output.S3Uri,
            destination="/opt/ml/processing/input"
        ),
        ProcessingInput(
            source=training_step.properties.ModelArtifacts.S3ModelArtifacts,
            destination="/opt/ml/processing/model"
        )
    ],
    outputs=[
        ProcessingOutput(
            output_name="evaluation",
            source="/opt/ml/processing/evaluation"
        )
    ],
    code="evaluation.py"
)

print("Model evaluation step defined")
```

### 1.5 条件付きモデル登録

```python
from sagemaker.workflow.step_collections import RegisterModel

# モデル登録ステップ
register_step = RegisterModel(
    name="RegisterModel",
    estimator=sklearn_estimator,
    model_data=training_step.properties.ModelArtifacts.S3ModelArtifacts,
    content_types=["text/csv"],
    response_types=["text/csv"],
    inference_instances=["ml.t2.medium", "ml.m5.large"],
    transform_instances=["ml.m5.large"],
    model_package_group_name="ml-model-package-group",
    approval_status=model_approval_status
)

# 条件定義（精度しきい値）
accuracy_condition = ConditionGreaterThanOrEqualTo(
    left=JsonGet(
        step_name=evaluation_step.name,
        property_file=PropertyFile(
            name="EvaluationReport",
            output_name="evaluation",
            path="evaluation.json"
        ),
        json_path="classification_metrics.accuracy.value"
    ),
    right=accuracy_threshold
)

# 条件付きステップ
condition_step = ConditionStep(
    name="CheckAccuracy",
    conditions=[accuracy_condition],
    if_steps=[register_step],
    else_steps=[]
)

print("Conditional model registration step defined")
```

### 1.6 Pipeline の作成と実行

```python
# Pipeline の定義
pipeline = Pipeline(
    name="ml-training-pipeline",
    parameters=[
        input_data,
        model_approval_status,
        accuracy_threshold
    ],
    steps=[
        processing_step,
        training_step,
        evaluation_step,
        condition_step
    ],
    sagemaker_session=sagemaker.Session()
)

# Pipeline の作成/更新
pipeline.upsert(role_arn=sagemaker.get_execution_role())

# Pipeline の実行
execution = pipeline.start(
    parameters={
        "InputData": "s3://your-bucket/input-data/",
        "AccuracyThreshold": 0.85
    }
)

print(f"Pipeline execution started: {execution.arn}")

# 実行状況の監視
execution.wait()
print(f"Pipeline execution completed with status: {execution.describe()['PipelineExecutionStatus']}")
```

## 🔄 Step 2: CI/CD パイプラインの構築

### 2.1 CodeCommit リポジトリの設定

```python
import boto3

# CodeCommit クライアント
codecommit = boto3.client('codecommit')

# リポジトリ作成
try:
    response = codecommit.create_repository(
        repositoryName='ml-ops-repository',
        repositoryDescription='MLOps pipeline source code'
    )
    repo_url = response['repositoryMetadata']['cloneUrlHttp']
    print(f"Repository created: {repo_url}")
except codecommit.exceptions.RepositoryNameExistsException:
    print("Repository already exists")
```

### 2.2 buildspec.yml の作成

```yaml
# buildspec.yml - CodeBuild 設定
version: 0.2

phases:
  install:
    runtime-versions:
      python: 3.8
    commands:
      - echo Installing dependencies...
      - pip install --upgrade pip
      - pip install boto3 sagemaker scikit-learn pandas numpy

  pre_build:
    commands:
      - echo Logging in to Amazon ECR...
      - aws ecr get-login-password --region $AWS_DEFAULT_REGION | docker login --username AWS --password-stdin $AWS_ACCOUNT_ID.dkr.ecr.$AWS_DEFAULT_REGION.amazonaws.com

  build:
    commands:
      - echo Build started on `date`
      - echo Running tests...
      - python -m pytest tests/ -v
      - echo Building and running SageMaker Pipeline...
      - python scripts/run_pipeline.py

  post_build:
    commands:
      - echo Build completed on `date`
      - echo Checking pipeline execution status...
      - python scripts/check_pipeline_status.py

artifacts:
  files:
    - '**/*'
  name: ml-ops-artifacts
```

### 2.3 自動テストスクリプト

```python
# tests/test_model.py - モデルのユニットテスト
import pytest
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score

class TestMLModel:
    def setup_method(self):
        """テスト用データの準備"""
        np.random.seed(42)
        n_samples = 1000
        n_features = 4
        
        # ダミーデータ生成
        X = np.random.randn(n_samples, n_features)
        y = (X[:, 0] + X[:, 1] > 0).astype(int)
        
        self.X_train, self.X_test, self.y_train, self.y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )
    
    def test_model_training(self):
        """モデル学習のテスト"""
        model = RandomForestClassifier(n_estimators=10, random_state=42)
        model.fit(self.X_train, self.y_train)
        
        # 学習後のモデルが予測可能であることを確認
        predictions = model.predict(self.X_test)
        assert len(predictions) == len(self.y_test)
        assert all(pred in [0, 1] for pred in predictions)
    
    def test_model_accuracy(self):
        """モデル精度のテスト"""
        model = RandomForestClassifier(n_estimators=50, random_state=42)
        model.fit(self.X_train, self.y_train)
        
        predictions = model.predict(self.X_test)
        accuracy = accuracy_score(self.y_test, predictions)
        
        # 最低限の精度を確保
        assert accuracy > 0.7, f"Model accuracy {accuracy} is below threshold"
    
    def test_data_validation(self):
        """データ検証のテスト"""
        # データ形状の確認
        assert self.X_train.shape[1] == 4, "Feature count mismatch"
        assert len(self.X_train) > 0, "Training data is empty"
        assert len(self.y_train) == len(self.X_train), "Target length mismatch"
        
        # データ値の確認
        assert not np.isnan(self.X_train).any(), "Training data contains NaN"
        assert not np.isnan(self.y_train).any(), "Target data contains NaN"

# tests/test_pipeline.py - パイプラインのテスト
import boto3
import pytest
from moto import mock_s3

class TestPipelineComponents:
    @mock_s3
    def test_s3_data_access(self):
        """S3データアクセスのテスト"""
        # Mock S3 setup
        s3 = boto3.client('s3', region_name='us-east-1')
        bucket_name = 'test-ml-bucket'
        s3.create_bucket(Bucket=bucket_name)
        
        # テストデータをアップロード
        test_data = "feature1,feature2,target\n1,2,0\n3,4,1\n"
        s3.put_object(Bucket=bucket_name, Key='data/test.csv', Body=test_data)
        
        # データ取得テスト
        response = s3.get_object(Bucket=bucket_name, Key='data/test.csv')
        content = response['Body'].read().decode('utf-8')
        
        assert 'feature1,feature2,target' in content
        assert len(content.split('\n')) >= 3
```

### 2.4 Pipeline 実行スクリプト

```python
# scripts/run_pipeline.py - Pipeline実行スクリプト
import boto3
import os
import json
from sagemaker.workflow.pipeline import Pipeline
from sagemaker import get_execution_role

def run_pipeline():
    """SageMaker Pipeline を実行"""
    
    # 環境変数から設定取得
    bucket_name = os.environ.get('ML_BUCKET', 'default-ml-bucket')
    pipeline_name = os.environ.get('PIPELINE_NAME', 'ml-training-pipeline')
    
    try:
        # SageMaker クライアント
        sagemaker_client = boto3.client('sagemaker')
        
        # Pipeline の存在確認
        try:
            pipeline_desc = sagemaker_client.describe_pipeline(PipelineName=pipeline_name)
            print(f"Pipeline {pipeline_name} found")
        except sagemaker_client.exceptions.ResourceNotFound:
            print(f"Pipeline {pipeline_name} not found. Creating new pipeline...")
            # 新しいパイプラインの作成ロジックをここに追加
            return
        
        # Pipeline 実行
        response = sagemaker_client.start_pipeline_execution(
            PipelineName=pipeline_name,
            PipelineParameters=[
                {
                    'Name': 'InputData',
                    'Value': f's3://{bucket_name}/input-data/'
                },
                {
                    'Name': 'AccuracyThreshold',
                    'Value': '0.85'
                }
            ]
        )
        
        execution_arn = response['PipelineExecutionArn']
        print(f"Pipeline execution started: {execution_arn}")
        
        # 実行ARNを出力ファイルに保存
        with open('pipeline_execution.json', 'w') as f:
            json.dump({'execution_arn': execution_arn}, f)
        
        return execution_arn
        
    except Exception as e:
        print(f"Error running pipeline: {str(e)}")
        raise

if __name__ == "__main__":
    run_pipeline()
```

### 2.5 CodePipeline の設定

```python
# Pipeline 定義（CloudFormation Template）
pipeline_template = {
    "AWSTemplateFormatVersion": "2010-09-09",
    "Description": "MLOps CI/CD Pipeline",
    "Resources": {
        "CodePipelineServiceRole": {
            "Type": "AWS::IAM::Role",
            "Properties": {
                "AssumeRolePolicyDocument": {
                    "Version": "2012-10-17",
                    "Statement": [
                        {
                            "Effect": "Allow",
                            "Principal": {"Service": "codepipeline.amazonaws.com"},
                            "Action": "sts:AssumeRole"
                        }
                    ]
                },
                "Policies": [
                    {
                        "PolicyName": "CodePipelinePolicy",
                        "PolicyDocument": {
                            "Version": "2012-10-17",
                            "Statement": [
                                {
                                    "Effect": "Allow",
                                    "Action": [
                                        "codecommit:GetBranch",
                                        "codecommit:GetCommit",
                                        "codebuild:BatchGetBuilds",
                                        "codebuild:StartBuild",
                                        "s3:GetObject",
                                        "s3:PutObject",
                                        "sagemaker:*"
                                    ],
                                    "Resource": "*"
                                }
                            ]
                        }
                    }
                ]
            }
        },
        "MLOpsPipeline": {
            "Type": "AWS::CodePipeline::Pipeline",
            "Properties": {
                "Name": "MLOpsPipeline",
                "RoleArn": {"Fn::GetAtt": ["CodePipelineServiceRole", "Arn"]},
                "ArtifactStore": {
                    "Type": "S3",
                    "Location": {"Ref": "ArtifactBucket"}
                },
                "Stages": [
                    {
                        "Name": "Source",
                        "Actions": [
                            {
                                "Name": "Source",
                                "ActionTypeId": {
                                    "Category": "Source",
                                    "Owner": "AWS",
                                    "Provider": "CodeCommit",
                                    "Version": "1"
                                },
                                "Configuration": {
                                    "RepositoryName": "ml-ops-repository",
                                    "BranchName": "main"
                                },
                                "OutputArtifacts": [{"Name": "SourceOutput"}]
                            }
                        ]
                    },
                    {
                        "Name": "Build",
                        "Actions": [
                            {
                                "Name": "Build",
                                "ActionTypeId": {
                                    "Category": "Build",
                                    "Owner": "AWS", 
                                    "Provider": "CodeBuild",
                                    "Version": "1"
                                },
                                "Configuration": {
                                    "ProjectName": {"Ref": "CodeBuildProject"}
                                },
                                "InputArtifacts": [{"Name": "SourceOutput"}],
                                "OutputArtifacts": [{"Name": "BuildOutput"}]
                            }
                        ]
                    }
                ]
            }
        }
    }
}
```

## 📊 Step 3: モデル監視と自動再学習

### 3.1 Model Monitor の設定

```python
from sagemaker.model_monitor import DefaultModelMonitor
from sagemaker.model_monitor.dataset_format import DatasetFormat

def setup_model_monitoring(endpoint_name, baseline_data_uri):
    """モデル監視の設定"""
    
    # Model Monitor の作成
    model_monitor = DefaultModelMonitor(
        role=get_execution_role(),
        instance_count=1,
        instance_type='ml.m5.xlarge',
        volume_size_in_gb=20,
        max_runtime_in_seconds=3600
    )
    
    # ベースライン作成
    baseline_job = model_monitor.suggest_baseline(
        baseline_dataset=baseline_data_uri,
        dataset_format=DatasetFormat.csv(header=True),
        output_s3_uri='s3://your-bucket/baseline-results/'
    )
    
    # 監視スケジュール作成
    monitor_schedule = model_monitor.create_monitoring_schedule(
        monitor_schedule_name=f'{endpoint_name}-monitor',
        endpoint_input=endpoint_name,
        output_s3_uri='s3://your-bucket/monitoring-results/',
        statistics=baseline_job.baseline_statistics(),
        constraints=baseline_job.suggested_constraints(),
        schedule_cron_expression='cron(0 * * * * ?)',  # 毎時実行
        enable_cloudwatch_metrics=True
    )
    
    return monitor_schedule

# 監視設定の実行
endpoint_name = 'ml-production-endpoint'
baseline_data = 's3://your-bucket/baseline/baseline.csv'
monitor_schedule = setup_model_monitoring(endpoint_name, baseline_data)
print(f"Model monitoring configured: {monitor_schedule.monitor_schedule_name}")
```

### 3.2 ドリフト検出とアラート

```python
import boto3

def setup_drift_alerts(monitor_schedule_name):
    """ドリフト検出アラートの設定"""
    
    cloudwatch = boto3.client('cloudwatch')
    sns = boto3.client('sns')
    
    # SNS トピック作成
    topic_response = sns.create_topic(Name='model-drift-alerts')
    topic_arn = topic_response['TopicArn']
    
    # CloudWatch アラーム作成
    cloudwatch.put_metric_alarm(
        AlarmName='ModelDriftAlert',
        ComparisonOperator='GreaterThanThreshold',
        EvaluationPeriods=1,
        MetricName='feature_baseline_drift_distance',
        Namespace='aws/sagemaker/Endpoints/data-metrics',
        Period=3600,  # 1時間
        Statistic='Average',
        Threshold=0.1,  # ドリフト閾値
        ActionsEnabled=True,
        AlarmActions=[topic_arn],
        AlarmDescription='Model data drift detected',
        Dimensions=[
            {
                'Name': 'MonitoringSchedule',
                'Value': monitor_schedule_name
            }
        ]
    )
    
    print(f"Drift alert configured with topic: {topic_arn}")
    return topic_arn

# アラート設定
topic_arn = setup_drift_alerts(monitor_schedule.monitor_schedule_name)
```

### 3.3 自動再学習の実装

```python
import json

def create_retraining_lambda():
    """自動再学習 Lambda 関数"""
    
    lambda_code = """
import json
import boto3
import os

def lambda_handler(event, context):
    try:
        # SNS メッセージからアラート情報を取得
        message = json.loads(event['Records'][0]['Sns']['Message'])
        alarm_name = message['AlarmName']
        
        if 'ModelDriftAlert' in alarm_name:
            # SageMaker Pipeline を実行して再学習
            sagemaker_client = boto3.client('sagemaker')
            
            pipeline_name = os.environ['PIPELINE_NAME']
            
            response = sagemaker_client.start_pipeline_execution(
                PipelineName=pipeline_name,
                PipelineParameters=[
                    {
                        'Name': 'InputData',
                        'Value': os.environ['RETRAIN_DATA_PATH']
                    },
                    {
                        'Name': 'AccuracyThreshold',
                        'Value': '0.85'
                    }
                ]
            )
            
            execution_arn = response['PipelineExecutionArn']
            
            # 実行通知
            sns = boto3.client('sns')
            sns.publish(
                TopicArn=os.environ['NOTIFICATION_TOPIC'],
                Subject='Model Retraining Started',
                Message=f'Automatic retraining triggered due to drift detection.\\nExecution ARN: {execution_arn}'
            )
            
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'message': 'Retraining pipeline started',
                    'execution_arn': execution_arn
                })
            }
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }
    """
    
    return lambda_code

# Lambda 関数デプロイ（CloudFormation/CDK使用推奨）
print("Lambda function code generated for automatic retraining")
```

## 🏗️ Step 4: Infrastructure as Code

### 4.1 CloudFormation テンプレート

```yaml
# mlops-infrastructure.yaml
AWSTemplateFormatVersion: '2010-09-09'
Description: 'MLOps Infrastructure Stack'

Parameters:
  ProjectName:
    Type: String
    Default: 'mlops-project'
    Description: 'Name of the MLOps project'

Resources:
  # S3 Bucket for ML artifacts
  MLArtifactsBucket:
    Type: AWS::S3::Bucket
    Properties:
      BucketName: !Sub '${ProjectName}-ml-artifacts-${AWS::AccountId}'
      VersioningConfiguration:
        Status: Enabled
      PublicAccessBlockConfiguration:
        BlockPublicAcls: true
        BlockPublicPolicy: true
        IgnorePublicAcls: true
        RestrictPublicBuckets: true

  # IAM Role for SageMaker
  SageMakerExecutionRole:
    Type: AWS::IAM::Role
    Properties:
      RoleName: !Sub '${ProjectName}-SageMakerRole'
      AssumeRolePolicyDocument:
        Version: '2012-10-17'
        Statement:
          - Effect: Allow
            Principal:
              Service: sagemaker.amazonaws.com
            Action: sts:AssumeRole
      ManagedPolicyArns:
        - arn:aws:iam::aws:policy/AmazonSageMakerFullAccess
      Policies:
        - PolicyName: S3Access
          PolicyDocument:
            Version: '2012-10-17'
            Statement:
              - Effect: Allow
                Action:
                  - s3:GetObject
                  - s3:PutObject
                  - s3:DeleteObject
                  - s3:ListBucket
                Resource:
                  - !Sub '${MLArtifactsBucket}/*'
                  - !GetAtt MLArtifactsBucket.Arn

  # CodeCommit Repository
  MLOpsRepository:
    Type: AWS::CodeCommit::Repository
    Properties:
      RepositoryName: !Sub '${ProjectName}-repository'
      RepositoryDescription: 'MLOps source code repository'

  # CodeBuild Project
  MLOpsBuildProject:
    Type: AWS::CodeBuild::Project
    Properties:
      Name: !Sub '${ProjectName}-build'
      ServiceRole: !GetAtt CodeBuildRole.Arn
      Artifacts:
        Type: CODEPIPELINE
      Environment:
        Type: LINUX_CONTAINER
        ComputeType: BUILD_GENERAL1_MEDIUM
        Image: aws/codebuild/amazonlinux2-x86_64-standard:3.0
        EnvironmentVariables:
          - Name: ML_BUCKET
            Value: !Ref MLArtifactsBucket
          - Name: SAGEMAKER_ROLE
            Value: !GetAtt SageMakerExecutionRole.Arn
      Source:
        Type: CODEPIPELINE
        BuildSpec: |
          version: 0.2
          phases:
            install:
              runtime-versions:
                python: 3.8
              commands:
                - pip install boto3 sagemaker scikit-learn pandas numpy pytest
            build:
              commands:
                - python -m pytest tests/ -v
                - python scripts/run_pipeline.py
          artifacts:
            files:
              - '**/*'

Outputs:
  ArtifactsBucket:
    Description: 'S3 bucket for ML artifacts'
    Value: !Ref MLArtifactsBucket
    Export:
      Name: !Sub '${ProjectName}-ArtifactsBucket'
  
  SageMakerRole:
    Description: 'SageMaker execution role ARN'
    Value: !GetAtt SageMakerExecutionRole.Arn
    Export:
      Name: !Sub '${ProjectName}-SageMakerRole'
```

### 4.2 デプロイメント自動化

```bash
#!/bin/bash
# deploy.sh - インフラストラクチャデプロイスクリプト

PROJECT_NAME="mlops-project"
REGION="us-east-1"
STACK_NAME="${PROJECT_NAME}-infrastructure"

echo "Deploying MLOps infrastructure..."

# CloudFormation スタックのデプロイ
aws cloudformation deploy \
  --template-file mlops-infrastructure.yaml \
  --stack-name $STACK_NAME \
  --parameter-overrides ProjectName=$PROJECT_NAME \
  --capabilities CAPABILITY_NAMED_IAM \
  --region $REGION

if [ $? -eq 0 ]; then
    echo "Infrastructure deployment completed successfully"
    
    # 出力値を取得
    BUCKET_NAME=$(aws cloudformation describe-stacks \
      --stack-name $STACK_NAME \
      --region $REGION \
      --query 'Stacks[0].Outputs[?OutputKey==`ArtifactsBucket`].OutputValue' \
      --output text)
    
    SAGEMAKER_ROLE=$(aws cloudformation describe-stacks \
      --stack-name $STACK_NAME \
      --region $REGION \
      --query 'Stacks[0].Outputs[?OutputKey==`SageMakerRole`].OutputValue' \
      --output text)
    
    echo "Artifacts bucket: $BUCKET_NAME"
    echo "SageMaker role: $SAGEMAKER_ROLE"
    
    # 環境変数ファイル作成
    cat > .env << EOF
ML_BUCKET=$BUCKET_NAME
SAGEMAKER_ROLE=$SAGEMAKER_ROLE
REGION=$REGION
EOF
    
    echo "Environment variables saved to .env file"
else
    echo "Infrastructure deployment failed"
    exit 1
fi
```

## 🧹 Step 5: リソースクリーンアップ

### 5.1 Pipeline とモニタリングのクリーンアップ

```python
def cleanup_mlops_resources():
    """MLOps リソースのクリーンアップ"""
    
    sagemaker_client = boto3.client('sagemaker')
    
    try:
        # Pipeline 削除
        pipeline_name = 'ml-training-pipeline'
        sagemaker_client.delete_pipeline(PipelineName=pipeline_name)
        print(f"Pipeline {pipeline_name} deleted")
        
        # モニタリングスケジュール削除
        monitor_schedule_name = 'ml-production-endpoint-monitor'
        sagemaker_client.delete_monitoring_schedule(
            MonitoringScheduleName=monitor_schedule_name
        )
        print(f"Monitoring schedule {monitor_schedule_name} deleted")
        
        # エンドポイント削除
        endpoint_name = 'ml-production-endpoint'
        sagemaker_client.delete_endpoint(EndpointName=endpoint_name)
        print(f"Endpoint {endpoint_name} deleted")
        
    except Exception as e:
        print(f"Error during cleanup: {str(e)}")

# クリーンアップ実行
cleanup_mlops_resources()
```

### 5.2 CloudFormation スタック削除

```bash
#!/bin/bash
# cleanup.sh - リソースクリーンアップスクリプト

PROJECT_NAME="mlops-project"
REGION="us-east-1"
STACK_NAME="${PROJECT_NAME}-infrastructure"

echo "Cleaning up MLOps infrastructure..."

# S3 バケットの内容を削除
BUCKET_NAME=$(aws cloudformation describe-stacks \
  --stack-name $STACK_NAME \
  --region $REGION \
  --query 'Stacks[0].Outputs[?OutputKey==`ArtifactsBucket`].OutputValue' \
  --output text)

if [ ! -z "$BUCKET_NAME" ]; then
    echo "Emptying S3 bucket: $BUCKET_NAME"
    aws s3 rm s3://$BUCKET_NAME --recursive
fi

# CloudFormation スタック削除
aws cloudformation delete-stack \
  --stack-name $STACK_NAME \
  --region $REGION

echo "CloudFormation stack deletion initiated"
echo "Cleanup completed"
```

## 💰 コスト計算

### 推定コスト（1日のパイプライン実行）
- **SageMaker Pipeline実行**: $2.00
- **Model Monitor**: $1.50
- **CodeBuild**: $0.50
- **S3ストレージ**: $0.30
- **その他AWSサービス**: $0.70
- **合計**: 約 $5.00/日

## 📚 学習ポイント

### 重要な概念
1. **MLOps Pipeline**: データ処理→学習→評価→デプロイの自動化
2. **CI/CD Integration**: コード変更からデプロイまでの自動化
3. **Model Monitoring**: ドリフト検出と自動再学習
4. **Infrastructure as Code**: 再現可能なインフラ管理
5. **Cost Optimization**: リソース効率化とコスト管理

### 実践的なスキル
- SageMaker Pipelines の設計・実装
- CI/CD パイプラインの構築
- モデル監視とアラート設定
- 自動化スクリプトの作成
- Infrastructure as Code の実装

---

**次のステップ**: [Lab 5: モデル監視](./lab05-monitoring.md) では、より詳細なモデル監視と運用について学習します。