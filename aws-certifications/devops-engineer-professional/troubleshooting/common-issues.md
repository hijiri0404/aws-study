# DevOps Engineer Professional - よくある問題と解決策

## 📋 概要

DOP-C02試験とDevOps実務でよく遭遇する問題とその解決策をまとめています。実際のトラブルシューティング手順と予防策も含めて解説します。

## 🚨 Domain 1: SDLC Automation - CI/CD関連

### 問題1: CodePipelineでビルドが失敗する

#### 症状
```
Build failed with exit code 1
ERROR: Could not find requirements.txt
```

#### 原因分析
- buildspec.ymlのパス指定間違い
- 依存関係ファイルの配置ミス
- 環境変数の設定不備

#### 解決手順
```bash
# 1. buildspec.ymlの確認
cat buildspec.yml
# パスとファイル名の正確性をチェック

# 2. CodeBuildログの詳細確認
aws logs get-log-events \
  --log-group-name /aws/codebuild/project-name \
  --log-stream-name latest-stream

# 3. 修正されたbuildspec.yml例
version: 0.2
phases:
  install:
    runtime-versions:
      python: 3.9
  pre_build:
    commands:
      - echo Logging in to Amazon ECR...
      - aws ecr get-login-password --region $AWS_DEFAULT_REGION | docker login --username AWS --password-stdin $AWS_ACCOUNT_ID.dkr.ecr.$AWS_DEFAULT_REGION.amazonaws.com
  build:
    commands:
      - echo Build started on `date`
      - echo Building the Docker image...
      - docker build -t $IMAGE_TAG .
  post_build:
    commands:
      - echo Build completed on `date`
```

#### 予防策
- buildspec.ymlのテンプレート化
- ローカル環境でのビルドテスト
- 依存関係の明示的管理

### 問題2: CodeDeployでデプロイが Rollback する

#### 症状
```
Deployment failed: The overall deployment failed because too many individual instances failed deployment
```

#### 原因分析
- ヘルスチェックの設定ミス
- アプリケーション起動時間の見積もり不足
- ロードバランサーのタイムアウト設定

#### 解決手順
```bash
# 1. デプロイ履歴の確認
aws deploy get-deployment --deployment-id d-123456789

# 2. インスタンスレベルの詳細確認
aws deploy get-deployment-instance \
  --deployment-id d-123456789 \
  --instance-id i-1234567890abcdef0

# 3. CodeDeploy Agent ログ確認
sudo tail -f /var/log/aws/codedeploy-agent/codedeploy-agent.log

# 4. 修正されたappspec.yml例
version: 0.0
os: linux
files:
  - source: /
    destination: /var/www/html
hooks:
  BeforeInstall:
    - location: scripts/install_dependencies
      timeout: 300
      runas: root
  ApplicationStart:
    - location: scripts/start_server
      timeout: 300
      runas: root
  ApplicationStop:
    - location: scripts/stop_server
      timeout: 300
      runas: root
  ValidateService:
    - location: scripts/validate_service
      timeout: 300
```

#### 予防策
- 段階的デプロイ（10%-50%-100%）
- 十分なヘルスチェック猶予期間
- ロールバック設定の事前テスト

### 問題3: パイプラインが環境変数を認識しない

#### 症状
- Parameter Store の値が取得できない
- 環境固有の設定が反映されない

#### 解決手順
```bash
# 1. IAM権限の確認
aws iam get-role-policy \
  --role-name CodeBuildServiceRole \
  --policy-name ParameterStorePolicy

# 2. Parameter Store の値確認
aws ssm get-parameter --name /myapp/database/url --with-decryption

# 3. buildspec.yml での正しい環境変数設定
version: 0.2
env:
  parameter-store:
    DB_URL: /myapp/database/url
    API_KEY: /myapp/api/key
  variables:
    ENVIRONMENT: production
phases:
  build:
    commands:
      - echo "Database URL: $DB_URL"
      - echo "Environment: $ENVIRONMENT"
```

## 🏗️ Domain 2: Configuration Management and IaC

### 問題4: CloudFormation スタックが UPDATE_ROLLBACK_FAILED 状態

#### 症状
```
Stack is in UPDATE_ROLLBACK_FAILED state and cannot be updated
```

#### 原因分析
- リソースの手動変更による drift
- 削除保護されたリソースの削除試行
- 依存関係の循環参照

#### 解決手順
```bash
# 1. スタックイベントの詳細確認
aws cloudformation describe-stack-events \
  --stack-name problematic-stack

# 2. Drift 検出
aws cloudformation detect-stack-drift --stack-name problematic-stack
aws cloudformation describe-stack-drift-detection-status \
  --stack-drift-detection-id detection-id

# 3. 強制的な続行（注意が必要）
aws cloudformation continue-update-rollback \
  --stack-name problematic-stack \
  --resources-to-skip ResourceLogicalId1,ResourceLogicalId2

# 4. 最終手段：スタック削除と再作成
aws cloudformation delete-stack --stack-name problematic-stack
```

#### 予防策
- リソースの手動変更禁止
- Change Sets の活用
- CloudFormation Drift Detection の定期実行

### 問題5: CDK デプロイでエラーが発生

#### 症状
```
Error: Cannot assume role: arn:aws:iam::123456789012:role/cdk-xxxxxx-cfn-exec-role
```

#### 解決手順
```bash
# 1. CDK Bootstrap 状態確認
cdk bootstrap --show-template

# 2. 権限確認
aws sts get-caller-identity
aws iam list-attached-user-policies --user-name current-user

# 3. CDK Bootstrap 実行
cdk bootstrap aws://123456789012/us-east-1

# 4. 依存関係の更新
npm update
```

## 🔄 Domain 3: Resilient Cloud Solutions

### 問題6: Auto Scaling が期待通りに動作しない

#### 症状
- CPU高負荷でもスケールアウトしない
- 不要なスケールインが発生

#### 原因分析と解決
```bash
# 1. Auto Scaling グループの状態確認
aws autoscaling describe-auto-scaling-groups \
  --auto-scaling-group-names my-asg

# 2. スケーリングポリシーの確認
aws autoscaling describe-policies \
  --auto-scaling-group-name my-asg

# 3. CloudWatch メトリクス確認
aws cloudwatch get-metric-statistics \
  --namespace AWS/EC2 \
  --metric-name CPUUtilization \
  --dimensions Name=AutoScalingGroupName,Value=my-asg \
  --start-time 2024-01-01T00:00:00Z \
  --end-time 2024-01-01T12:00:00Z \
  --period 300 \
  --statistics Average

# 4. 修正されたスケーリングポリシー
aws autoscaling put-scaling-policy \
  --auto-scaling-group-name my-asg \
  --policy-name scale-out-policy \
  --policy-type TargetTrackingScaling \
  --target-tracking-configuration '{
    "TargetValue": 70.0,
    "PredefinedMetricSpecification": {
      "PredefinedMetricType": "ASGAverageCPUUtilization"
    }
  }'
```

### 問題7: ELB ヘルスチェック失敗

#### 症状
- インスタンスが健全でもUnHealthy判定
- 頻繁なインスタンス置き換え

#### 解決手順
```bash
# 1. ターゲットグループの状態確認
aws elbv2 describe-target-health \
  --target-group-arn arn:aws:elasticloadbalancing:us-east-1:123456789012:targetgroup/my-targets/73e2d6bc24d8a067

# 2. ヘルスチェック設定確認
aws elbv2 describe-target-groups \
  --target-group-arns arn:aws:elasticloadbalancing:us-east-1:123456789012:targetgroup/my-targets/73e2d6bc24d8a067

# 3. ヘルスチェック設定修正
aws elbv2 modify-target-group \
  --target-group-arn arn:aws:elasticloadbalancing:us-east-1:123456789012:targetgroup/my-targets/73e2d6bc24d8a067 \
  --health-check-interval-seconds 30 \
  --healthy-threshold-count 2 \
  --unhealthy-threshold-count 3 \
  --health-check-timeout-seconds 10
```

## 📊 Domain 4: Monitoring and Logging

### 問題8: CloudWatch Logs が表示されない

#### 症状
- アプリケーションログがCloudWatchに表示されない
- ログの遅延が発生

#### 解決手順
```bash
# 1. CloudWatch Agent 状態確認
sudo /opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent-ctl \
  -m ec2 -c file:/opt/aws/amazon-cloudwatch-agent/etc/amazon-cloudwatch-agent.json \
  -a query

# 2. IAM権限確認
aws iam get-role-policy \
  --role-name CloudWatchAgentServerRole \
  --policy-name CloudWatchAgentServerPolicy

# 3. ログ設定修正例
{
  "logs": {
    "logs_collected": {
      "files": {
        "collect_list": [
          {
            "file_path": "/var/log/myapp/application.log",
            "log_group_name": "/aws/ec2/myapp",
            "log_stream_name": "{instance_id}",
            "timestamp_format": "%Y-%m-%d %H:%M:%S"
          }
        ]
      }
    }
  }
}

# 4. Agent 再起動
sudo systemctl restart amazon-cloudwatch-agent
```

### 問題9: X-Ray トレースが表示されない

#### 症状
- アプリケーションからトレースが送信されない
- X-Ray サービスマップが空

#### 解決手順
```bash
# 1. X-Ray デーモンの状態確認
sudo systemctl status xray

# 2. アプリケーションコードの確認（Python例）
from aws_xray_sdk.core import xray_recorder
from aws_xray_sdk.core import patch_all

# AWS SDK をパッチ
patch_all()

@xray_recorder.capture('my_function')
def my_function():
    # ビジネスロジック
    pass

# 3. X-Ray デーモン設定確認
cat /etc/amazon/xray/cfg.yaml
```

## 🚨 Domain 5: Incident and Event Response

### 問題10: Lambda 関数がタイムアウトする

#### 症状
```
Task timed out after 3.00 seconds
```

#### 解決手順
```bash
# 1. 詳細なロギング追加
import logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    logger.info(f"Processing event: {event}")
    start_time = time.time()
    
    # 処理実行
    
    execution_time = time.time() - start_time
    logger.info(f"Execution time: {execution_time} seconds")

# 2. タイムアウト設定調整
aws lambda update-function-configuration \
  --function-name my-function \
  --timeout 30

# 3. メモリ増加（処理速度向上）
aws lambda update-function-configuration \
  --function-name my-function \
  --memory-size 512
```

### 問題11: Systems Manager Automation が失敗

#### 症状
- Automation Document の実行が途中で停止
- 権限エラーが発生

#### 解決手順
```bash
# 1. 実行履歴の確認
aws ssm describe-automation-executions \
  --filters Key=DocumentName,Values=AWS-RestartEC2Instance

# 2. 特定実行の詳細確認
aws ssm get-automation-execution \
  --automation-execution-id 12345678-1234-1234-1234-123456789012

# 3. IAM権限の修正
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "ec2:DescribeInstances",
        "ec2:RebootInstances",
        "ec2:StartInstances",
        "ec2:StopInstances"
      ],
      "Resource": "*"
    }
  ]
}
```

## 🔐 Domain 6: Security and Compliance

### 問題12: IAM 権限が複雑で管理困難

#### 症状
- 権限過多または不足
- ポリシーの重複
- セキュリティリスクの発生

#### 解決手順
```bash
# 1. IAM Access Analyzer 使用
aws accessanalyzer create-analyzer \
  --analyzer-name security-analyzer \
  --type ACCOUNT

# 2. 未使用の権限特定
aws iam generate-credential-report
aws iam get-credential-report

# 3. 最小権限ポリシーの例
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject"
      ],
      "Resource": "arn:aws:s3:::my-bucket/logs/*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "s3:ListBucket"
      ],
      "Resource": "arn:aws:s3:::my-bucket",
      "Condition": {
        "StringLike": {
          "s3:prefix": "logs/*"
        }
      }
    }
  ]
}
```

### 問題13: Secrets Manager のローテーションが失敗

#### 症状
- シークレットローテーションが完了しない
- アプリケーションが古いシークレットを使用

#### 解決手順
```bash
# 1. ローテーション状態確認
aws secretsmanager describe-secret \
  --secret-id my-database-secret

# 2. ローテーション Lambda ログ確認
aws logs filter-log-events \
  --log-group-name /aws/lambda/rotation-function \
  --start-time 1609459200000

# 3. 手動ローテーション実行
aws secretsmanager rotate-secret \
  --secret-id my-database-secret \
  --force-rotate-immediately
```

## 🛠️ 一般的なトラブルシューティング手法

### デバッグのベストプラクティス

#### 1. ログ分析の体系的アプローチ
```bash
# CloudWatch Insights でのログ分析
aws logs start-query \
  --log-group-names "/aws/lambda/my-function" \
  --start-time 1609459200 \
  --end-time 1609462800 \
  --query-string 'fields @timestamp, @message | filter @message like /ERROR/ | sort @timestamp desc'
```

#### 2. メトリクス監視
```bash
# 異常なメトリクスの特定
aws cloudwatch get-metric-statistics \
  --namespace AWS/Lambda \
  --metric-name Errors \
  --dimensions Name=FunctionName,Value=my-function \
  --start-time 2024-01-01T00:00:00Z \
  --end-time 2024-01-01T12:00:00Z \
  --period 300 \
  --statistics Sum
```

#### 3. タグベースでのリソース管理
```bash
# 問題のあるリソースを特定
aws resourcegroupstaggingapi get-resources \
  --tag-filters Key=Environment,Values=production \
  --resource-type-filters "AWS::EC2::Instance"
```

## 📚 予防策とベストプラクティス

### 1. 事前検証
- CloudFormation Change Sets
- terraform plan
- CDK diff

### 2. 段階的デプロイ
- Canary デプロイメント
- Blue/Green デプロイメント
- Feature flags

### 3. 監視の充実
- Proactive monitoring
- Anomaly detection
- Automated remediation

### 4. ドキュメント化
- Runbook の作成
- トラブルシューティングガイド
- ポストモルテムの実施

## 🎯 試験対策のポイント

### よく出題される問題パターン
1. **CI/CD パイプライン障害**: buildspec.yml、権限、環境変数
2. **Auto Scaling 問題**: ポリシー設定、ヘルスチェック
3. **監視設定ミス**: CloudWatch Agent、X-Ray設定
4. **権限問題**: IAM ポリシー、Cross-account アクセス
5. **Infrastructure as Code**: CloudFormation エラー、CDK 問題

### 重要な診断コマンド
```bash
# AWS CLI による診断
aws sts get-caller-identity
aws iam list-attached-user-policies --user-name username
aws logs describe-log-groups
aws cloudformation describe-stacks
aws ec2 describe-instances --filters Name=instance-state-name,Values=running
```

---

**重要**: 実際のトラブルシューティングでは、ログの詳細確認と段階的な問題の切り分けが重要です。本番環境では慎重に操作し、必要に応じてAWSサポートに相談してください。