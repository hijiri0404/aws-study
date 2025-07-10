# Lab 5: モデル監視と運用

## 🎯 学習目標

このラボでは、本番環境でのMLモデルの包括的な監視と運用管理を学習します：

- SageMaker Model Monitor による詳細監視
- リアルタイムメトリクス監視とアラート
- データ品質とモデル性能の継続的評価
- A/B テストと段階的デプロイメント
- インシデント対応と自動復旧

## 📋 前提条件

- AWS CLI が設定済み
- CloudWatch、SNS の基本知識
- [Lab 4: MLOpsパイプライン](./lab04-mlops-pipeline.md) の完了推奨

## 🏗️ アーキテクチャ概要

```
┌─────────────────────────────────────────────────────────────┐
│                      モデル監視システム                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐     │
│  │   Data      │    │   Model     │    │ Performance │     │
│  │  Quality    │    │  Monitor    │    │   Monitor   │     │
│  │  Monitor    │    │             │    │             │     │
│  └─────┬───────┘    └─────┬───────┘    └─────┬───────┘     │
│        │                  │                  │             │
│        ▼                  ▼                  ▼             │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │                 CloudWatch                              │ │
│  │            Metrics & Alarms                             │ │
│  └─────┬───────────────────────┬───────────────────────────┘ │
│        │                       │                             │
│        ▼                       ▼                             │
│  ┌─────────────┐         ┌─────────────┐                     │
│  │  Real-time  │         │  Automated  │                     │
│  │   Alerts    │         │  Response   │                     │
│  └─────────────┘         └─────────────┘                     │
└─────────────────────────────────────────────────────────────┘
```

## 🚀 Step 1: 包括的なモデル監視設定

### 1.1 データ品質監視の実装

```python
import boto3
import sagemaker
from sagemaker.model_monitor import DefaultModelMonitor, ModelQualityMonitor
from sagemaker.model_monitor.dataset_format import DatasetFormat
import pandas as pd
import numpy as np

# SageMaker セッション設定
sagemaker_session = sagemaker.Session()
role = sagemaker.get_execution_role()

# データ品質監視の設定
def setup_data_quality_monitoring(endpoint_name, baseline_data_uri):
    """データ品質監視の詳細設定"""
    
    # Data Quality Monitor の作成
    data_quality_monitor = DefaultModelMonitor(
        role=role,
        instance_count=1,
        instance_type='ml.m5.xlarge',
        volume_size_in_gb=20,
        max_runtime_in_seconds=3600,
        env={
            'publish_cloudwatch_metrics': 'Enabled',
            'dataset_format': 'json'
        }
    )
    
    # ベースライン作成
    baseline_job = data_quality_monitor.suggest_baseline(
        baseline_dataset=baseline_data_uri,
        dataset_format=DatasetFormat.csv(header=True),
        output_s3_uri=f's3://your-bucket/baseline-results/{endpoint_name}/',
        wait=True
    )
    
    print(f"Baseline job completed: {baseline_job.baseline_job_name}")
    
    # カスタム制約の追加
    custom_constraints = {
        "features": [
            {
                "name": "feature_1",
                "inferred_type": "Fractional",
                "completeness": {"must_be_present": True},
                "numerical_statistics": {
                    "min": {"must_be_less_than": 10.0},
                    "max": {"must_be_greater_than": -10.0}
                }
            },
            {
                "name": "feature_2", 
                "inferred_type": "Fractional",
                "completeness": {"must_be_present": True},
                "numerical_statistics": {
                    "std_dev": {"must_be_less_than": 5.0}
                }
            }
        ],
        "dataset_statistics": {
            "num_rows": {"must_be_greater_than": 100}
        }
    }
    
    # 監視スケジュール作成
    monitor_schedule = data_quality_monitor.create_monitoring_schedule(
        monitor_schedule_name=f'{endpoint_name}-data-quality',
        endpoint_input=endpoint_name,
        output_s3_uri=f's3://your-bucket/monitoring-results/{endpoint_name}/',
        statistics=baseline_job.baseline_statistics(),
        constraints=baseline_job.suggested_constraints(),
        schedule_cron_expression='cron(0 */6 * * * ?)',  # 6時間毎
        enable_cloudwatch_metrics=True
    )
    
    return monitor_schedule, baseline_job

# 実行
endpoint_name = 'ml-production-endpoint'
baseline_data = 's3://your-bucket/baseline/baseline.csv'
data_monitor, baseline = setup_data_quality_monitoring(endpoint_name, baseline_data)
print(f"Data quality monitoring configured: {data_monitor.monitor_schedule_name}")
```

### 1.2 モデル品質監視の実装

```python
def setup_model_quality_monitoring(endpoint_name, ground_truth_data_uri):
    """モデル品質監視の設定"""
    
    # Model Quality Monitor の作成
    model_quality_monitor = ModelQualityMonitor(
        role=role,
        instance_count=1,
        instance_type='ml.m5.xlarge',
        volume_size_in_gb=20,
        max_runtime_in_seconds=3600,
        env={
            'publish_cloudwatch_metrics': 'Enabled'
        }
    )
    
    # 問題タイプ設定（分類の場合）
    problem_type = "BinaryClassification"  # または "MulticlassClassification", "Regression"
    
    # ベースライン作成
    baseline_job = model_quality_monitor.suggest_baseline(
        baseline_dataset=ground_truth_data_uri,
        dataset_format=DatasetFormat.csv(header=True),
        problem_type=problem_type,
        inference_attribute="prediction",
        probability_attribute="probability",
        ground_truth_attribute="ground_truth",
        output_s3_uri=f's3://your-bucket/model-quality-baseline/{endpoint_name}/',
        wait=True
    )
    
    # 監視スケジュール作成
    monitor_schedule = model_quality_monitor.create_monitoring_schedule(
        monitor_schedule_name=f'{endpoint_name}-model-quality',
        endpoint_input=endpoint_name,
        ground_truth_input=ground_truth_data_uri,
        problem_type=problem_type,
        inference_attribute="prediction",
        probability_attribute="probability", 
        ground_truth_attribute="ground_truth",
        output_s3_uri=f's3://your-bucket/model-quality-results/{endpoint_name}/',
        statistics=baseline_job.baseline_statistics(),
        constraints=baseline_job.suggested_constraints(),
        schedule_cron_expression='cron(0 0 * * * ?)',  # 毎日実行
        enable_cloudwatch_metrics=True
    )
    
    return monitor_schedule, baseline_job

# Ground Truthデータの準備（実際の予測結果と正解ラベル）
ground_truth_data = 's3://your-bucket/ground-truth/ground_truth.csv'
model_quality_monitor, quality_baseline = setup_model_quality_monitoring(
    endpoint_name, ground_truth_data
)
print(f"Model quality monitoring configured: {model_quality_monitor.monitor_schedule_name}")
```

### 1.3 バイアス監視の実装

```python
from sagemaker.clarify import BiasConfig, DataConfig, ModelConfig
from sagemaker.model_monitor import BiasMonitor

def setup_bias_monitoring(endpoint_name, bias_analysis_config):
    """バイアス監視の設定"""
    
    # Bias Monitor の作成
    bias_monitor = BiasMonitor(
        role=role,
        instance_count=1,
        instance_type='ml.m5.xlarge',
        volume_size_in_gb=20,
        max_runtime_in_seconds=3600
    )
    
    # データ設定
    data_config = DataConfig(
        s3_data_input_path=bias_analysis_config['data_path'],
        s3_output_path=f's3://your-bucket/bias-analysis/{endpoint_name}/',
        label=bias_analysis_config['label_column'],
        headers=bias_analysis_config['headers'],
        dataset_type='text/csv'
    )
    
    # バイアス設定
    bias_config = BiasConfig(
        label_values_or_threshold=bias_analysis_config['positive_label'],
        facet_name=bias_analysis_config['sensitive_feature'],
        facet_values_or_threshold=bias_analysis_config['sensitive_values']
    )
    
    # モデル設定
    model_config = ModelConfig(
        model_name=bias_analysis_config['model_name'],
        instance_type='ml.m5.large',
        instance_count=1,
        accept_type='text/csv'
    )
    
    # バイアス分析実行
    bias_job = bias_monitor.run_bias_analysis(
        data_config=data_config,
        bias_config=bias_config,
        model_config=model_config,
        job_name=f'{endpoint_name}-bias-analysis',
        wait=True
    )
    
    # 継続的バイアス監視スケジュール
    monitor_schedule = bias_monitor.create_monitoring_schedule(
        monitor_schedule_name=f'{endpoint_name}-bias-monitor',
        endpoint_input=endpoint_name,
        ground_truth_input=bias_analysis_config['data_path'],
        analysis_config=bias_job.latest_job.describe()['ProcessingInputs'][0],
        output_s3_uri=f's3://your-bucket/bias-monitoring/{endpoint_name}/',
        schedule_cron_expression='cron(0 0 * * MON ?)',  # 毎週月曜日
        enable_cloudwatch_metrics=True
    )
    
    return monitor_schedule, bias_job

# バイアス分析設定
bias_config = {
    'data_path': 's3://your-bucket/bias-analysis-data/data.csv',
    'label_column': 'approved',
    'headers': ['age', 'income', 'education', 'gender', 'approved'],
    'positive_label': [1],
    'sensitive_feature': 'gender',
    'sensitive_values': ['female'],
    'model_name': 'ml-production-model'
}

bias_monitor, bias_analysis = setup_bias_monitoring(endpoint_name, bias_config)
print(f"Bias monitoring configured: {bias_monitor.monitor_schedule_name}")
```

## 📊 Step 2: リアルタイムメトリクス監視

### 2.1 カスタムメトリクス作成

```python
import boto3
from datetime import datetime, timedelta

def create_custom_metrics(endpoint_name):
    """カスタムメトリクスの作成と設定"""
    
    cloudwatch = boto3.client('cloudwatch')
    
    # エンドポイントメトリクスの取得
    def get_endpoint_metrics(metric_name, start_time, end_time):
        response = cloudwatch.get_metric_statistics(
            Namespace='AWS/SageMaker',
            MetricName=metric_name,
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
        return response['Datapoints']
    
    # カスタムメトリクスの計算と送信
    def calculate_and_send_custom_metrics():
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(minutes=5)
        
        # レイテンシメトリクス取得
        model_latency = get_endpoint_metrics('ModelLatency', start_time, end_time)
        overhead_latency = get_endpoint_metrics('OverheadLatency', start_time, end_time)
        
        if model_latency and overhead_latency:
            # 総レイテンシ計算
            total_latency = model_latency[-1]['Average'] + overhead_latency[-1]['Average']
            
            # カスタムメトリクス送信
            cloudwatch.put_metric_data(
                Namespace='Custom/SageMaker',
                MetricData=[
                    {
                        'MetricName': 'TotalLatency',
                        'Dimensions': [
                            {
                                'Name': 'EndpointName',
                                'Value': endpoint_name
                            }
                        ],
                        'Value': total_latency,
                        'Unit': 'Milliseconds',
                        'Timestamp': datetime.utcnow()
                    }
                ]
            )
        
        # エラー率の計算
        invocations = get_endpoint_metrics('Invocations', start_time, end_time)
        invocation_errors = get_endpoint_metrics('InvocationErrors', start_time, end_time)
        
        if invocations and invocation_errors:
            error_rate = (invocation_errors[-1]['Sum'] / invocations[-1]['Sum']) * 100
            
            cloudwatch.put_metric_data(
                Namespace='Custom/SageMaker',
                MetricData=[
                    {
                        'MetricName': 'ErrorRate',
                        'Dimensions': [
                            {
                                'Name': 'EndpointName',
                                'Value': endpoint_name
                            }
                        ],
                        'Value': error_rate,
                        'Unit': 'Percent',
                        'Timestamp': datetime.utcnow()
                    }
                ]
            )
        
        print(f"Custom metrics updated for {endpoint_name}")
    
    return calculate_and_send_custom_metrics

# カスタムメトリクス設定
custom_metrics_func = create_custom_metrics(endpoint_name)
custom_metrics_func()
```

### 2.2 ダッシュボード作成

```python
def create_monitoring_dashboard(endpoint_name):
    """CloudWatch ダッシュボードの作成"""
    
    cloudwatch = boto3.client('cloudwatch')
    
    dashboard_body = {
        "widgets": [
            {
                "type": "metric",
                "x": 0,
                "y": 0,
                "width": 12,
                "height": 6,
                "properties": {
                    "metrics": [
                        ["AWS/SageMaker", "Invocations", "EndpointName", endpoint_name],
                        [".", "InvocationErrors", ".", "."],
                        ["Custom/SageMaker", "ErrorRate", ".", "."]
                    ],
                    "period": 300,
                    "stat": "Sum",
                    "region": "us-east-1",
                    "title": "Endpoint Invocations and Errors",
                    "yAxis": {
                        "left": {
                            "min": 0
                        }
                    }
                }
            },
            {
                "type": "metric",
                "x": 12,
                "y": 0,
                "width": 12,
                "height": 6,
                "properties": {
                    "metrics": [
                        ["AWS/SageMaker", "ModelLatency", "EndpointName", endpoint_name],
                        [".", "OverheadLatency", ".", "."],
                        ["Custom/SageMaker", "TotalLatency", ".", "."]
                    ],
                    "period": 300,
                    "stat": "Average",
                    "region": "us-east-1",
                    "title": "Latency Metrics",
                    "yAxis": {
                        "left": {
                            "min": 0
                        }
                    }
                }
            },
            {
                "type": "metric",
                "x": 0,
                "y": 6,
                "width": 24,
                "height": 6,
                "properties": {
                    "metrics": [
                        ["aws/sagemaker/Endpoints/data-metrics", "feature_baseline_drift_distance", "MonitoringSchedule", f"{endpoint_name}-data-quality"],
                        ["aws/sagemaker/Endpoints/model-metrics", "accuracy", "MonitoringSchedule", f"{endpoint_name}-model-quality"]
                    ],
                    "period": 3600,
                    "stat": "Average",
                    "region": "us-east-1",
                    "title": "Model and Data Quality Metrics"
                }
            }
        ]
    }
    
    # ダッシュボード作成
    response = cloudwatch.put_dashboard(
        DashboardName=f'{endpoint_name}-monitoring',
        DashboardBody=json.dumps(dashboard_body)
    )
    
    print(f"Dashboard created: {endpoint_name}-monitoring")
    return response

# ダッシュボード作成
import json
dashboard_response = create_monitoring_dashboard(endpoint_name)
```

## 🚨 Step 3: アラートシステムの構築

### 3.1 多段階アラート設定

```python
def setup_multi_tier_alerts(endpoint_name):
    """多段階アラートシステムの設定"""
    
    cloudwatch = boto3.client('cloudwatch')
    sns = boto3.client('sns')
    
    # SNS トピック作成
    topics = {
        'critical': sns.create_topic(Name=f'{endpoint_name}-critical-alerts')['TopicArn'],
        'warning': sns.create_topic(Name=f'{endpoint_name}-warning-alerts')['TopicArn'],
        'info': sns.create_topic(Name=f'{endpoint_name}-info-alerts')['TopicArn']
    }
    
    # アラーム設定リスト
    alarms = [
        {
            'name': 'HighErrorRate',
            'metric_name': 'ErrorRate',
            'namespace': 'Custom/SageMaker',
            'threshold': 5.0,  # 5%
            'comparison': 'GreaterThanThreshold',
            'severity': 'critical',
            'description': 'High error rate detected'
        },
        {
            'name': 'HighLatency',
            'metric_name': 'TotalLatency',
            'namespace': 'Custom/SageMaker',
            'threshold': 1000.0,  # 1秒
            'comparison': 'GreaterThanThreshold',
            'severity': 'warning',
            'description': 'High latency detected'
        },
        {
            'name': 'DataDrift',
            'metric_name': 'feature_baseline_drift_distance',
            'namespace': 'aws/sagemaker/Endpoints/data-metrics',
            'threshold': 0.1,
            'comparison': 'GreaterThanThreshold',
            'severity': 'warning',
            'description': 'Data drift detected'
        },
        {
            'name': 'ModelAccuracyDrop',
            'metric_name': 'accuracy',
            'namespace': 'aws/sagemaker/Endpoints/model-metrics',
            'threshold': 0.8,
            'comparison': 'LessThanThreshold',
            'severity': 'critical',
            'description': 'Model accuracy below threshold'
        }
    ]
    
    # アラーム作成
    for alarm in alarms:
        dimensions = [{'Name': 'EndpointName', 'Value': endpoint_name}]
        if 'MonitoringSchedule' in alarm['namespace']:
            dimensions = [{'Name': 'MonitoringSchedule', 'Value': f"{endpoint_name}-data-quality"}]
        
        cloudwatch.put_metric_alarm(
            AlarmName=f"{endpoint_name}-{alarm['name']}",
            ComparisonOperator=alarm['comparison'],
            EvaluationPeriods=2,
            MetricName=alarm['metric_name'],
            Namespace=alarm['namespace'],
            Period=300,
            Statistic='Average',
            Threshold=alarm['threshold'],
            ActionsEnabled=True,
            AlarmActions=[topics[alarm['severity']]],
            AlarmDescription=alarm['description'],
            Dimensions=dimensions,
            TreatMissingData='notBreaching'
        )
    
    print(f"Multi-tier alerts configured for {endpoint_name}")
    return topics

# アラート設定
alert_topics = setup_multi_tier_alerts(endpoint_name)
```

### 3.2 自動対応システム

```python
def create_auto_response_system(endpoint_name, alert_topics):
    """自動対応システムの作成"""
    
    # Lambda 関数コード
    lambda_code = f"""
import json
import boto3
import os
from datetime import datetime

def lambda_handler(event, context):
    try:
        # SNS メッセージから情報取得
        message = json.loads(event['Records'][0]['Sns']['Message'])
        alarm_name = message['AlarmName']
        alarm_state = message['NewStateValue']
        
        if alarm_state != 'ALARM':
            return {{'statusCode': 200, 'body': 'Alarm not in ALARM state'}}
        
        # 対応アクション決定
        response_action = determine_response_action(alarm_name)
        
        if response_action:
            result = execute_response_action(response_action, alarm_name)
            
            # 対応結果を通知
            notify_response_result(alarm_name, response_action, result)
            
            return {{
                'statusCode': 200,
                'body': json.dumps({{
                    'alarm': alarm_name,
                    'action': response_action,
                    'result': result
                }})
            }}
        
    except Exception as e:
        print(f"Error in auto-response: {{str(e)}}")
        return {{'statusCode': 500, 'body': str(e)}}

def determine_response_action(alarm_name):
    '''アラームに応じた対応アクションを決定'''
    actions = {{
        'HighErrorRate': 'scale_up',
        'HighLatency': 'scale_up', 
        'DataDrift': 'trigger_retraining',
        'ModelAccuracyDrop': 'rollback_model'
    }}
    
    for alarm_type, action in actions.items():
        if alarm_type in alarm_name:
            return action
    return None

def execute_response_action(action, alarm_name):
    '''対応アクションを実行'''
    sagemaker = boto3.client('sagemaker')
    autoscaling = boto3.client('application-autoscaling')
    
    if action == 'scale_up':
        # Auto Scaling 設定更新
        resource_id = f"endpoint/{endpoint_name}/variant/primary"
        try:
            autoscaling.put_scaling_policy(
                PolicyName=f'{{endpoint_name}}-emergency-scale',
                ServiceNamespace='sagemaker',
                ResourceId=resource_id,
                ScalableDimension='sagemaker:variant:DesiredInstanceCount',
                PolicyType='StepScaling',
                StepScalingPolicyConfiguration={{
                    'AdjustmentType': 'ChangeInCapacity',
                    'StepAdjustments': [
                        {{
                            'MetricIntervalLowerBound': 0,
                            'ScalingAdjustment': 2
                        }}
                    ]
                }}
            )
            return 'Scaling policy updated'
        except Exception as e:
            return f'Scaling failed: {{str(e)}}'
    
    elif action == 'trigger_retraining':
        # パイプライン実行
        try:
            response = sagemaker.start_pipeline_execution(
                PipelineName='ml-training-pipeline',
                PipelineParameters=[
                    {{'Name': 'InputData', 'Value': 's3://your-bucket/retrain-data/'}},
                    {{'Name': 'AccuracyThreshold', 'Value': '0.85'}}
                ]
            )
            return f'Retraining started: {{response["PipelineExecutionArn"]}}'
        except Exception as e:
            return f'Retraining failed: {{str(e)}}'
    
    elif action == 'rollback_model':
        # モデルロールバック（前のバージョンに戻す）
        try:
            # 実装: 前のモデルバージョンを取得してデプロイ
            return 'Model rollback initiated'
        except Exception as e:
            return f'Rollback failed: {{str(e)}}'
    
    return 'No action taken'

def notify_response_result(alarm_name, action, result):
    '''対応結果を通知'''
    sns = boto3.client('sns')
    
    message = f'''
    自動対応システムが作動しました
    
    アラーム: {{alarm_name}}
    実行アクション: {{action}}
    結果: {{result}}
    時刻: {{datetime.now().isoformat()}}
    '''
    
    sns.publish(
        TopicArn='{alert_topics["info"]}',
        Subject=f'自動対応実行 - {{alarm_name}}',
        Message=message
    )
"""
    
    # Lambda 関数作成（実際にはCloudFormation/CDKを使用推奨）
    print("Auto-response Lambda function code generated")
    print("Deploy this using CloudFormation or CDK for production use")
    
    return lambda_code

# 自動対応システム作成
auto_response_code = create_auto_response_system(endpoint_name, alert_topics)
```

## 🔄 Step 4: A/B テストと段階的デプロイメント

### 4.1 A/B テスト監視

```python
def setup_ab_test_monitoring(endpoint_name, variant_names):
    """A/B テスト用の監視設定"""
    
    cloudwatch = boto3.client('cloudwatch')
    
    # 各バリアント用のメトリクス監視
    for variant in variant_names:
        # バリアント固有のアラーム作成
        cloudwatch.put_metric_alarm(
            AlarmName=f"{endpoint_name}-{variant}-ErrorRate",
            ComparisonOperator='GreaterThanThreshold',
            EvaluationPeriods=3,
            MetricName='Invocation4XXErrors',
            Namespace='AWS/SageMaker',
            Period=300,
            Statistic='Sum',
            Threshold=10.0,
            ActionsEnabled=True,
            AlarmActions=[alert_topics['warning']],
            AlarmDescription=f'High error rate for variant {variant}',
            Dimensions=[
                {'Name': 'EndpointName', 'Value': endpoint_name},
                {'Name': 'VariantName', 'Value': variant}
            ]
        )
        
        # レイテンシアラーム
        cloudwatch.put_metric_alarm(
            AlarmName=f"{endpoint_name}-{variant}-Latency",
            ComparisonOperator='GreaterThanThreshold',
            EvaluationPeriods=2,
            MetricName='ModelLatency',
            Namespace='AWS/SageMaker',
            Period=300,
            Statistic='Average',
            Threshold=500.0,  # 500ms
            ActionsEnabled=True,
            AlarmActions=[alert_topics['warning']],
            AlarmDescription=f'High latency for variant {variant}',
            Dimensions=[
                {'Name': 'EndpointName', 'Value': endpoint_name},
                {'Name': 'VariantName', 'Value': variant}
            ]
        )
    
    print(f"A/B test monitoring configured for variants: {variant_names}")

# A/B テスト監視設定
variant_names = ['model-a', 'model-b']
setup_ab_test_monitoring(endpoint_name, variant_names)
```

### 4.2 段階的デプロイメント監視

```python
def create_canary_deployment_monitor(endpoint_name):
    """カナリアデプロイメント監視システム"""
    
    def monitor_canary_metrics(canary_variant, primary_variant, duration_minutes=30):
        """カナリアメトリクスの監視"""
        
        cloudwatch = boto3.client('cloudwatch')
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(minutes=duration_minutes)
        
        # メトリクス取得
        def get_variant_metrics(variant_name, metric_name):
            response = cloudwatch.get_metric_statistics(
                Namespace='AWS/SageMaker',
                MetricName=metric_name,
                Dimensions=[
                    {'Name': 'EndpointName', 'Value': endpoint_name},
                    {'Name': 'VariantName', 'Value': variant_name}
                ],
                StartTime=start_time,
                EndTime=end_time,
                Period=300,
                Statistics=['Average', 'Sum']
            )
            return response['Datapoints']
        
        # カナリアとプライマリの比較
        canary_errors = get_variant_metrics(canary_variant, 'Invocation4XXErrors')
        primary_errors = get_variant_metrics(primary_variant, 'Invocation4XXErrors')
        
        canary_latency = get_variant_metrics(canary_variant, 'ModelLatency')
        primary_latency = get_variant_metrics(primary_variant, 'ModelLatency')
        
        # 比較分析
        analysis_result = {
            'canary_healthy': True,
            'error_rate_comparison': 'unknown',
            'latency_comparison': 'unknown',
            'recommendation': 'continue'
        }
        
        if canary_errors and primary_errors:
            canary_error_rate = sum([d['Sum'] for d in canary_errors]) / len(canary_errors)
            primary_error_rate = sum([d['Sum'] for d in primary_errors]) / len(primary_errors)
            
            if canary_error_rate > primary_error_rate * 1.5:  # 50%以上悪い
                analysis_result['canary_healthy'] = False
                analysis_result['error_rate_comparison'] = 'worse'
                analysis_result['recommendation'] = 'rollback'
        
        if canary_latency and primary_latency:
            canary_avg_latency = sum([d['Average'] for d in canary_latency]) / len(canary_latency)
            primary_avg_latency = sum([d['Average'] for d in primary_latency]) / len(primary_latency)
            
            if canary_avg_latency > primary_avg_latency * 1.2:  # 20%以上遅い
                analysis_result['latency_comparison'] = 'worse'
                if analysis_result['recommendation'] != 'rollback':
                    analysis_result['recommendation'] = 'hold'
        
        return analysis_result
    
    def execute_canary_decision(analysis_result, canary_variant):
        """カナリア分析結果に基づくアクション実行"""
        
        sagemaker = boto3.client('sagemaker')
        
        if analysis_result['recommendation'] == 'rollback':
            # カナリアを0%に戻す
            sagemaker.update_endpoint_weights_and_capacities(
                EndpointName=endpoint_name,
                DesiredWeightsAndCapacities=[
                    {
                        'VariantName': canary_variant,
                        'CurrentWeight': 0
                    }
                ]
            )
            print(f"Canary rolled back: {canary_variant}")
            
        elif analysis_result['recommendation'] == 'continue':
            # カナリアトラフィックを段階的に増加
            current_weight = 10  # 現在の重み（実際は取得）
            new_weight = min(current_weight + 10, 50)  # 10%ずつ増加、最大50%
            
            sagemaker.update_endpoint_weights_and_capacities(
                EndpointName=endpoint_name,
                DesiredWeightsAndCapacities=[
                    {
                        'VariantName': canary_variant,
                        'CurrentWeight': new_weight
                    }
                ]
            )
            print(f"Canary traffic increased to {new_weight}%")
        
        return analysis_result['recommendation']
    
    return monitor_canary_metrics, execute_canary_decision

# カナリアデプロイメント監視
canary_monitor, canary_executor = create_canary_deployment_monitor(endpoint_name)

# 実行例
canary_analysis = canary_monitor('model-v2', 'model-v1', 30)
action_taken = canary_executor(canary_analysis, 'model-v2')
print(f"Canary analysis: {canary_analysis}")
print(f"Action taken: {action_taken}")
```

## 📈 Step 5: パフォーマンス分析とレポート

### 5.1 自動レポート生成

```python
def create_monitoring_report(endpoint_name, report_period_hours=24):
    """監視レポートの自動生成"""
    
    cloudwatch = boto3.client('cloudwatch')
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(hours=report_period_hours)
    
    # メトリクス収集
    metrics_to_collect = [
        'Invocations',
        'InvocationErrors', 
        'ModelLatency',
        'OverheadLatency'
    ]
    
    report_data = {}
    
    for metric in metrics_to_collect:
        response = cloudwatch.get_metric_statistics(
            Namespace='AWS/SageMaker',
            MetricName=metric,
            Dimensions=[
                {'Name': 'EndpointName', 'Value': endpoint_name}
            ],
            StartTime=start_time,
            EndTime=end_time,
            Period=3600,  # 1時間毎
            Statistics=['Average', 'Maximum', 'Sum']
        )
        report_data[metric] = response['Datapoints']
    
    # レポート分析
    def analyze_metrics(data):
        analysis = {}
        
        # 総呼び出し数
        if 'Invocations' in data:
            total_invocations = sum([d['Sum'] for d in data['Invocations']])
            analysis['total_invocations'] = total_invocations
        
        # エラー率
        if 'InvocationErrors' in data and 'Invocations' in data:
            total_errors = sum([d['Sum'] for d in data['InvocationErrors']])
            error_rate = (total_errors / total_invocations * 100) if total_invocations > 0 else 0
            analysis['error_rate_percent'] = error_rate
        
        # 平均レイテンシ
        if 'ModelLatency' in data:
            avg_latency = sum([d['Average'] for d in data['ModelLatency']]) / len(data['ModelLatency'])
            analysis['average_latency_ms'] = avg_latency
        
        # パフォーマンス評価
        analysis['performance_grade'] = 'A'
        if analysis.get('error_rate_percent', 0) > 1:
            analysis['performance_grade'] = 'B'
        if analysis.get('error_rate_percent', 0) > 5:
            analysis['performance_grade'] = 'C'
        if analysis.get('average_latency_ms', 0) > 1000:
            analysis['performance_grade'] = 'C'
        
        return analysis
    
    analysis = analyze_metrics(report_data)
    
    # HTML レポート生成
    html_report = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Model Monitoring Report - {endpoint_name}</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 40px; }}
            .header {{ background-color: #f0f0f0; padding: 20px; }}
            .metric {{ margin: 20px 0; padding: 15px; border-left: 4px solid #007cba; }}
            .grade-A {{ color: green; }}
            .grade-B {{ color: orange; }}
            .grade-C {{ color: red; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>Model Monitoring Report</h1>
            <p>Endpoint: {endpoint_name}</p>
            <p>Period: {start_time.strftime('%Y-%m-%d %H:%M')} - {end_time.strftime('%Y-%m-%d %H:%M')}</p>
        </div>
        
        <div class="metric">
            <h2>Performance Summary</h2>
            <p><strong>Overall Grade:</strong> 
            <span class="grade-{analysis['performance_grade']}">{analysis['performance_grade']}</span></p>
        </div>
        
        <div class="metric">
            <h3>Key Metrics</h3>
            <ul>
                <li>Total Invocations: {analysis.get('total_invocations', 'N/A'):,}</li>
                <li>Error Rate: {analysis.get('error_rate_percent', 'N/A'):.2f}%</li>
                <li>Average Latency: {analysis.get('average_latency_ms', 'N/A'):.2f} ms</li>
            </ul>
        </div>
        
        <div class="metric">
            <h3>Recommendations</h3>
            <ul>
    """
    
    # 推奨事項追加
    if analysis.get('error_rate_percent', 0) > 1:
        html_report += "<li>Error rate is elevated. Consider investigating root causes.</li>"
    
    if analysis.get('average_latency_ms', 0) > 500:
        html_report += "<li>Latency is high. Consider scaling up or optimizing the model.</li>"
    
    if analysis.get('total_invocations', 0) < 100:
        html_report += "<li>Low traffic volume. Monitor for sufficient load testing.</li>"
    
    html_report += """
            </ul>
        </div>
    </body>
    </html>
    """
    
    # S3にレポート保存
    s3 = boto3.client('s3')
    report_key = f"monitoring-reports/{endpoint_name}/{end_time.strftime('%Y-%m-%d-%H')}-report.html"
    
    s3.put_object(
        Bucket='your-monitoring-bucket',
        Key=report_key,
        Body=html_report,
        ContentType='text/html'
    )
    
    print(f"Monitoring report generated: s3://your-monitoring-bucket/{report_key}")
    return analysis, f"s3://your-monitoring-bucket/{report_key}"

# レポート生成実行
report_analysis, report_url = create_monitoring_report(endpoint_name, 24)
print(f"Report analysis: {report_analysis}")
```

## 🧹 Step 6: リソースクリーンアップ

### 6.1 監視リソースの削除

```python
def cleanup_monitoring_resources(endpoint_name):
    """監視関連リソースのクリーンアップ"""
    
    sagemaker_client = boto3.client('sagemaker')
    cloudwatch = boto3.client('cloudwatch')
    sns = boto3.client('sns')
    
    try:
        # 監視スケジュールの削除
        schedules = [
            f'{endpoint_name}-data-quality',
            f'{endpoint_name}-model-quality',
            f'{endpoint_name}-bias-monitor'
        ]
        
        for schedule in schedules:
            try:
                sagemaker_client.delete_monitoring_schedule(
                    MonitoringScheduleName=schedule
                )
                print(f"Monitoring schedule deleted: {schedule}")
            except Exception as e:
                print(f"Error deleting schedule {schedule}: {e}")
        
        # CloudWatch アラームの削除
        alarm_names = [
            f'{endpoint_name}-HighErrorRate',
            f'{endpoint_name}-HighLatency',
            f'{endpoint_name}-DataDrift',
            f'{endpoint_name}-ModelAccuracyDrop'
        ]
        
        for alarm_name in alarm_names:
            try:
                cloudwatch.delete_alarms(AlarmNames=[alarm_name])
                print(f"Alarm deleted: {alarm_name}")
            except Exception as e:
                print(f"Error deleting alarm {alarm_name}: {e}")
        
        # ダッシュボードの削除
        try:
            cloudwatch.delete_dashboards(
                DashboardNames=[f'{endpoint_name}-monitoring']
            )
            print(f"Dashboard deleted: {endpoint_name}-monitoring")
        except Exception as e:
            print(f"Error deleting dashboard: {e}")
        
        # SNS トピックの削除
        topic_names = [
            f'{endpoint_name}-critical-alerts',
            f'{endpoint_name}-warning-alerts',
            f'{endpoint_name}-info-alerts'
        ]
        
        for topic_name in topic_names:
            try:
                # トピックARNを取得して削除
                topics = sns.list_topics()
                for topic in topics['Topics']:
                    if topic_name in topic['TopicArn']:
                        sns.delete_topic(TopicArn=topic['TopicArn'])
                        print(f"SNS topic deleted: {topic_name}")
                        break
            except Exception as e:
                print(f"Error deleting topic {topic_name}: {e}")
        
    except Exception as e:
        print(f"Error during cleanup: {str(e)}")

# クリーンアップ実行
cleanup_monitoring_resources(endpoint_name)
```

## 💰 コスト計算

### 推定コスト（1日あたり）
- **Model Monitor**: $5.00/日
- **CloudWatch メトリクス**: $1.50/日
- **CloudWatch アラーム**: $0.30/日
- **SNS通知**: $0.10/日
- **Lambda実行**: $0.20/日
- **S3ストレージ**: $0.50/日
- **合計**: 約 $7.60/日

## 📚 学習ポイント

### 重要な概念
1. **包括的監視**: データ品質・モデル品質・バイアス監視
2. **リアルタイムアラート**: 多段階アラートと自動対応
3. **A/B テスト監視**: バリアント間の性能比較
4. **自動レポート**: 定期的な性能分析
5. **コスト効率**: 監視レベルとコストのバランス

### 実践的なスキル
- SageMaker Model Monitor の活用
- CloudWatch メトリクスとアラーム設定
- 自動対応システムの構築
- カナリアデプロイメント監視
- パフォーマンス分析とレポート生成

---

**完了**: この Lab 5 で、本格的なMLモデル監視と運用システムの構築スキルを習得しました。次は実際のプロジェクトでこれらの技術を活用してください。