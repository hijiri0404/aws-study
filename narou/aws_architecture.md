# 小説家になろう ダウンローダー AWS WEBサービス化 アーキテクチャ

## 🏗️ 推奨アーキテクチャ

### 基本構成（スケーラブル・サーバーレス型）

```
┌─────────────────────────────────────────────────────────────────┐
│                            Frontend                             │
├─────────────────────────────────────────────────────────────────┤
│  CloudFront (CDN) + S3 (Static Website)                        │
│  ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐   │
│  │   React/Vue.js  │ │   HTML/CSS/JS   │ │  SPA Framework  │   │
│  │   Web Interface │ │   Static Assets │ │   Upload Form   │   │
│  └─────────────────┘ └─────────────────┘ └─────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                                   │
                                   │ HTTPS API Calls
                                   ▼
┌─────────────────────────────────────────────────────────────────┐
│                          API Gateway                            │
├─────────────────────────────────────────────────────────────────┤
│  • REST API エンドポイント                                      │
│  • 認証・認可 (Cognito Integration)                             │
│  • リクエスト制限・スロットリング                               │
│  • CORS設定                                                     │
└─────────────────────────────────────────────────────────────────┘
                                   │
                                   │ Lambda Trigger
                                   ▼
┌─────────────────────────────────────────────────────────────────┐
│                        Lambda Functions                         │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐   │
│  │   API Handler   │ │  Download Core  │ │ Status Checker  │   │
│  │   - 作品検索    │ │   - 章取得処理  │ │  - 進捗確認     │   │
│  │   - リクエスト  │ │   - ファイル生成│ │  - 状態管理     │   │
│  │   - レスポンス  │ │   - エラー処理  │ │  - 通知送信     │   │
│  └─────────────────┘ └─────────────────┘ └─────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                   │                              │
                   │                              │ Long Running Tasks
                   ▼                              ▼
┌─────────────────────────────┐ ┌─────────────────────────────────┐
│         DynamoDB            │ │              SQS                │
├─────────────────────────────┤ ├─────────────────────────────────┤
│  • ユーザー管理             │ │  • ダウンロードキュー           │
│  • 作品メタデータ           │ │  • 非同期処理管理               │
│  • ダウンロード履歴         │ │  • デッドレターキュー           │
│  • 進捗状況                 │ │  • バッチ処理トリガー           │
└─────────────────────────────┘ └─────────────────────────────────┘
                   │                              │
                   │                              ▼
                   │                ┌─────────────────────────────────┐
                   │                │           ECS Fargate           │
                   │                ├─────────────────────────────────┤
                   │                │  • 大量章数作品の処理           │
                   │                │  • Python ダウンローダー実行   │
                   │                │  • 自動スケーリング             │
                   │                │  • コンテナ化された処理         │
                   │                └─────────────────────────────────┘
                   │                              │
                   ▼                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                             S3                                 │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐   │
│  │ Generated Files │ │   Temp Storage  │ │    Backups      │   │
│  │  - 完成小説.txt │ │  - 処理中ファイル│ │  - DB バックアップ│   │
│  │  - .epub変換    │ │  - ログファイル  │ │  - 設定ファイル  │   │
│  └─────────────────┘ └─────────────────┘ └─────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                                   │
                                   │ Download Links
                                   ▼
┌─────────────────────────────────────────────────────────────────┐
│                         CloudWatch                             │
├─────────────────────────────────────────────────────────────────┤
│  • ログ監視・集約                                               │
│  • パフォーマンスメトリクス                                     │
│  • アラート・通知                                               │
│  • ダッシュボード                                               │
└─────────────────────────────────────────────────────────────────┘
```

## 🔧 コンポーネント詳細

### 1. Frontend (React/Vue.js + S3 + CloudFront)
```
機能:
- 作品ID入力フォーム
- ダウンロード進捗表示
- ファイル一覧・ダウンロード
- ユーザー認証UI

技術スタック:
- React.js / Vue.js
- Material-UI / Vuetify
- TypeScript
- PWA対応
```

### 2. API Gateway
```
エンドポイント:
- POST /api/download     # ダウンロード開始
- GET  /api/status/{id}  # 進捗確認
- GET  /api/works        # 作品一覧
- GET  /api/files/{id}   # ファイルダウンロード
- POST /api/auth/login   # 認証

設定:
- API キー認証
- レート制限: 100req/min
- CORS有効化
- リクエストバリデーション
```

### 3. Lambda Functions
```python
# api_handler.py
import json
import boto3
from enhanced_downloader import EnhancedNovelDownloader

def lambda_handler(event, context):
    work_id = event['pathParameters']['work_id']
    
    # SQSにダウンロードタスクを送信
    sqs = boto3.client('sqs')
    sqs.send_message(
        QueueUrl=os.environ['DOWNLOAD_QUEUE_URL'],
        MessageBody=json.dumps({
            'work_id': work_id,
            'user_id': event['requestContext']['authorizer']['user_id'],
            'timestamp': datetime.now().isoformat()
        })
    )
    
    return {
        'statusCode': 202,
        'body': json.dumps({'message': 'ダウンロード開始', 'work_id': work_id})
    }
```

### 4. ECS Fargate (重い処理用)
```dockerfile
# Dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY enhanced_downloader.py requirements.txt ./
RUN pip install -r requirements.txt

CMD ["python", "batch_processor.py"]
```

### 5. データベース設計 (DynamoDB)
```
# Works Table
PK: work_id (String)
SK: metadata
attributes:
  - title (String)
  - author (String)
  - total_chapters (Number)
  - last_updated (String)
  - status (String): active, completed, error

# Downloads Table  
PK: user_id (String)
SK: work_id#timestamp
attributes:
  - status (String): pending, processing, completed, failed
  - progress (Number): 0-100
  - file_url (String)
  - error_message (String)

# Users Table
PK: user_id (String)
attributes:
  - email (String)
  - created_at (String)
  - subscription_tier (String)
  - usage_count (Number)
```

## 🚀 デプロイ方法

### CDK/CloudFormation テンプレート
```typescript
// lib/novel-downloader-stack.ts
import * as cdk from 'aws-cdk-lib';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import * as apigateway from 'aws-cdk-lib/aws-apigateway';
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';

export class NovelDownloaderStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    // DynamoDB Tables
    const worksTable = new dynamodb.Table(this, 'WorksTable', {
      partitionKey: { name: 'work_id', type: dynamodb.AttributeType.STRING },
      billingMode: dynamodb.BillingMode.PAY_PER_REQUEST,
    });

    // Lambda Functions
    const apiHandler = new lambda.Function(this, 'ApiHandler', {
      runtime: lambda.Runtime.PYTHON_3_9,
      code: lambda.Code.fromAsset('lambda'),
      handler: 'api_handler.lambda_handler',
      environment: {
        WORKS_TABLE_NAME: worksTable.tableName,
      },
    });

    // API Gateway
    const api = new apigateway.RestApi(this, 'NovelDownloaderApi', {
      restApiName: 'Novel Downloader Service',
      description: 'API for novel downloading service',
    });

    const downloadResource = api.root.addResource('download');
    downloadResource.addMethod('POST', new apigateway.LambdaIntegration(apiHandler));
  }
}
```

### Terraform版
```hcl
# main.tf
terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

# DynamoDB
resource "aws_dynamodb_table" "works" {
  name           = "novel-works"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "work_id"

  attribute {
    name = "work_id"
    type = "S"
  }

  tags = {
    Environment = "production"
    Service     = "novel-downloader"
  }
}

# Lambda Function
resource "aws_lambda_function" "api_handler" {
  filename         = "lambda_function.zip"
  function_name    = "novel-downloader-api"
  role            = aws_iam_role.lambda_role.arn
  handler         = "api_handler.lambda_handler"
  runtime         = "python3.9"
  timeout         = 30

  environment {
    variables = {
      WORKS_TABLE_NAME = aws_dynamodb_table.works.name
    }
  }
}
```

## 💰 コスト概算

### 月間利用量想定
- ユーザー数: 1,000人
- 平均ダウンロード: 3作品/月/人
- 平均作品サイズ: 500章 (5MB)

### AWS料金試算
```
API Gateway:     $5   (1M requests)
Lambda:          $10  (compute time)
DynamoDB:        $25  (read/write units)
S3:              $15  (storage + transfer)
ECS Fargate:     $30  (container hours)
CloudFront:      $10  (CDN transfer)
CloudWatch:      $5   (logs + metrics)
─────────────────────
合計:            $100/月
```

## 🔒 セキュリティ考慮事項

### 1. 認証・認可
```
- AWS Cognito User Pools
- JWT トークンベース認証
- API キー + レート制限
- IAM ロール最小権限
```

### 2. データ保護
```
- S3 バケット暗号化 (AES-256)
- DynamoDB 暗号化有効
- VPC エンドポイント使用
- WAF + CloudFront
```

### 3. 監査・ログ
```
- CloudTrail 有効化
- CloudWatch Logs 集約
- X-Ray トレーシング
- AWS Config コンプライアンス
```

## 📊 運用・監視

### CloudWatch ダッシュボード
```
メトリクス:
- API レスポンス時間
- Lambda エラー率
- DynamoDB スループット
- S3 ストレージ使用量
- ダウンロード成功率

アラート:
- エラー率 > 5%
- レスポンス時間 > 30秒
- ストレージ容量 > 80%
```

### 自動運用
```
- Auto Scaling (ECS)
- Dead Letter Queue処理
- 古いファイル自動削除
- バックアップ自動化
```

## 🎯 段階的移行戦略

### Phase 1: MVP版
- Lambda + API Gateway + S3
- 基本的なダウンロード機能
- 簡単なWeb UI

### Phase 2: スケール対応
- ECS Fargate 追加
- DynamoDB導入
- 進捗表示機能

### Phase 3: エンタープライズ版
- ユーザー認証
- サブスクリプション
- 高度な監視・分析

この構成により、スケーラブルで運用しやすいWebサービスとして展開可能です。