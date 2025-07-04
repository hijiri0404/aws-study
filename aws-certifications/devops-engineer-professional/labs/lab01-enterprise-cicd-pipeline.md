# Lab 1: エンタープライズ級 CI/CD パイプライン構築

## 🎯 学習目標

このラボでは、実際の企業環境で求められる高度なCI/CDパイプラインを構築します。

**習得スキル**:
- マルチステージCI/CDパイプライン設計
- 自動テスト・品質ゲートの実装
- セキュリティスキャンの統合
- ブルー/グリーンデプロイメント
- ロールバック戦略

**所要時間**: 6-8時間  
**推定コスト**: $20-30

## 📋 シナリオ

**企業**: フィンテック企業（金融サービス）  
**要件**:
- 1日50回以上のデプロイ
- ゼロダウンタイムデプロイ必須
- セキュリティスキャン自動化
- 本番環境への段階的リリース
- 完全な監査ログ

## Phase 1: 基盤環境セットアップ

### 1.1 IAM ロール作成

```bash
#!/bin/bash
# スクリプト: setup-cicd-roles.sh

set -e

echo "=== CI/CD IAM ロール作成開始 ==="

# CodePipeline サービスロール
cat > codepipeline-trust-policy.json << 'EOF'
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Principal": {
                "Service": "codepipeline.amazonaws.com"
            },
            "Action": "sts:AssumeRole"
        }
    ]
}
EOF

aws iam create-role \
    --role-name CodePipelineServiceRole \
    --assume-role-policy-document file://codepipeline-trust-policy.json

# CodePipeline ポリシー
cat > codepipeline-policy.json << 'EOF'
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "s3:GetBucketVersioning",
                "s3:GetObject",
                "s3:GetObjectVersion",
                "s3:PutObject",
                "s3:GetBucketLocation",
                "s3:ListBucket"
            ],
            "Resource": "*"
        },
        {
            "Effect": "Allow",
            "Action": [
                "codecommit:CancelUploadArchive",
                "codecommit:GetBranch",
                "codecommit:GetCommit",
                "codecommit:GetRepository",
                "codecommit:ListBranches",
                "codecommit:ListRepositories"
            ],
            "Resource": "*"
        },
        {
            "Effect": "Allow",
            "Action": [
                "codebuild:BatchGetBuilds",
                "codebuild:StartBuild"
            ],
            "Resource": "*"
        },
        {
            "Effect": "Allow",
            "Action": [
                "codedeploy:CreateDeployment",
                "codedeploy:GetApplication",
                "codedeploy:GetApplicationRevision",
                "codedeploy:GetDeployment",
                "codedeploy:GetDeploymentConfig",
                "codedeploy:RegisterApplicationRevision"
            ],
            "Resource": "*"
        },
        {
            "Effect": "Allow",
            "Action": [
                "ecs:DescribeServices",
                "ecs:DescribeTaskDefinition",
                "ecs:DescribeTasks",
                "ecs:ListTasks",
                "ecs:RegisterTaskDefinition",
                "ecs:UpdateService"
            ],
            "Resource": "*"
        },
        {
            "Effect": "Allow",
            "Action": [
                "elasticbeanstalk:CreateApplicationVersion",
                "elasticbeanstalk:DescribeApplicationVersions",
                "elasticbeanstalk:DescribeEnvironments",
                "elasticbeanstalk:DescribeEvents",
                "elasticbeanstalk:UpdateEnvironment"
            ],
            "Resource": "*"
        },
        {
            "Effect": "Allow",
            "Action": [
                "lambda:InvokeFunction",
                "lambda:ListFunctions"
            ],
            "Resource": "*"
        },
        {
            "Effect": "Allow",
            "Action": [
                "cloudformation:CreateStack",
                "cloudformation:DeleteStack",
                "cloudformation:DescribeStacks",
                "cloudformation:UpdateStack",
                "cloudformation:CreateChangeSet",
                "cloudformation:DeleteChangeSet",
                "cloudformation:DescribeChangeSet",
                "cloudformation:ExecuteChangeSet",
                "cloudformation:SetStackPolicy",
                "cloudformation:ValidateTemplate"
            ],
            "Resource": "*"
        },
        {
            "Effect": "Allow",
            "Action": [
                "iam:PassRole"
            ],
            "Resource": "*"
        }
    ]
}
EOF

aws iam put-role-policy \
    --role-name CodePipelineServiceRole \
    --policy-name CodePipelineServiceRolePolicy \
    --policy-document file://codepipeline-policy.json

# CodeBuild サービスロール
cat > codebuild-trust-policy.json << 'EOF'
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Principal": {
                "Service": "codebuild.amazonaws.com"
            },
            "Action": "sts:AssumeRole"
        }
    ]
}
EOF

aws iam create-role \
    --role-name CodeBuildServiceRole \
    --assume-role-policy-document file://codebuild-trust-policy.json

# CodeBuild ポリシー
cat > codebuild-policy.json << 'EOF'
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "logs:CreateLogGroup",
                "logs:CreateLogStream",
                "logs:PutLogEvents"
            ],
            "Resource": "*"
        },
        {
            "Effect": "Allow",
            "Action": [
                "s3:GetObject",
                "s3:GetObjectVersion",
                "s3:PutObject"
            ],
            "Resource": "*"
        },
        {
            "Effect": "Allow",
            "Action": [
                "ssm:GetParameters",
                "ssm:GetParameter"
            ],
            "Resource": "*"
        },
        {
            "Effect": "Allow",
            "Action": [
                "ecr:BatchCheckLayerAvailability",
                "ecr:GetDownloadUrlForLayer",
                "ecr:BatchGetImage",
                "ecr:GetAuthorizationToken"
            ],
            "Resource": "*"
        },
        {
            "Effect": "Allow",
            "Action": [
                "secretsmanager:GetSecretValue"
            ],
            "Resource": "*"
        }
    ]
}
EOF

aws iam put-role-policy \
    --role-name CodeBuildServiceRole \
    --policy-name CodeBuildServiceRolePolicy \
    --policy-document file://codebuild-policy.json

echo "IAM ロール作成完了"
```

### 1.2 S3 バケットとECRリポジトリ作成

```bash
#!/bin/bash
# スクリプト: setup-artifact-storage.sh

set -e

# 変数定義
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
REGION=$(aws configure get region)
BUCKET_NAME="cicd-artifacts-${ACCOUNT_ID}-${REGION}"
REPO_NAME="fintech-app"

echo "=== アーティファクトストレージ作成 ==="

# S3バケット作成
echo "1. S3バケット作成中..."
if [ "$REGION" = "us-east-1" ]; then
    aws s3 mb s3://$BUCKET_NAME
else
    aws s3 mb s3://$BUCKET_NAME --region $REGION
fi

# バケットポリシー設定
cat > bucket-policy.json << EOF
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Principal": {
                "AWS": [
                    "arn:aws:iam::${ACCOUNT_ID}:role/CodePipelineServiceRole",
                    "arn:aws:iam::${ACCOUNT_ID}:role/CodeBuildServiceRole"
                ]
            },
            "Action": [
                "s3:GetObject",
                "s3:GetObjectVersion",
                "s3:PutObject",
                "s3:GetBucketVersioning"
            ],
            "Resource": [
                "arn:aws:s3:::${BUCKET_NAME}",
                "arn:aws:s3:::${BUCKET_NAME}/*"
            ]
        }
    ]
}
EOF

aws s3api put-bucket-policy --bucket $BUCKET_NAME --policy file://bucket-policy.json

# バージョニング有効化
aws s3api put-bucket-versioning \
    --bucket $BUCKET_NAME \
    --versioning-configuration Status=Enabled

echo "S3バケット設定完了: $BUCKET_NAME"

# ECRリポジトリ作成
echo "2. ECRリポジトリ作成中..."
aws ecr create-repository \
    --repository-name $REPO_NAME \
    --image-scanning-configuration scanOnPush=true \
    --encryption-configuration encryptionType=AES256 \
    2>/dev/null || echo "ECRリポジトリは既に存在します"

# ECRライフサイクルポリシー設定
cat > lifecycle-policy.json << 'EOF'
{
    "rules": [
        {
            "rulePriority": 1,
            "description": "Keep last 10 production images",
            "selection": {
                "tagStatus": "tagged",
                "tagPrefixList": ["prod"],
                "countType": "imageCountMoreThan",
                "countNumber": 10
            },
            "action": {
                "type": "expire"
            }
        },
        {
            "rulePriority": 2,
            "description": "Keep last 5 staging images",
            "selection": {
                "tagStatus": "tagged",
                "tagPrefixList": ["staging"],
                "countType": "imageCountMoreThan",
                "countNumber": 5
            },
            "action": {
                "type": "expire"
            }
        },
        {
            "rulePriority": 3,
            "description": "Delete untagged images older than 1 day",
            "selection": {
                "tagStatus": "untagged",
                "countType": "sinceImagePushed",
                "countUnit": "days",
                "countNumber": 1
            },
            "action": {
                "type": "expire"
            }
        }
    ]
}
EOF

aws ecr put-lifecycle-policy \
    --repository-name $REPO_NAME \
    --lifecycle-policy-text file://lifecycle-policy.json

echo "ECRリポジトリ設定完了: $REPO_NAME"

# 設定情報保存
cat > cicd-config.json << EOF
{
    "account_id": "$ACCOUNT_ID",
    "region": "$REGION",
    "artifact_bucket": "$BUCKET_NAME",
    "ecr_repository": "$REPO_NAME",
    "ecr_uri": "${ACCOUNT_ID}.dkr.ecr.${REGION}.amazonaws.com/${REPO_NAME}"
}
EOF

echo "=== ストレージセットアップ完了 ==="
```

## Phase 2: サンプルアプリケーション準備

### 2.1 Node.js Express アプリケーション

```bash
#!/bin/bash
# スクリプト: create-sample-app.sh

set -e

echo "=== サンプルアプリケーション作成 ==="

# プロジェクトディレクトリ作成
mkdir -p fintech-app
cd fintech-app

# package.json 作成
cat > package.json << 'EOF'
{
  "name": "fintech-app",
  "version": "1.0.0",
  "description": "Sample fintech application for CI/CD demo",
  "main": "app.js",
  "scripts": {
    "start": "node app.js",
    "test": "jest",
    "test:coverage": "jest --coverage",
    "lint": "eslint .",
    "security": "npm audit"
  },
  "dependencies": {
    "express": "^4.18.2",
    "helmet": "^7.1.0",
    "compression": "^1.7.4",
    "cors": "^2.8.5",
    "morgan": "^1.10.0",
    "uuid": "^9.0.1"
  },
  "devDependencies": {
    "jest": "^29.7.0",
    "supertest": "^6.3.3",
    "eslint": "^8.54.0"
  }
}
EOF

# アプリケーションコード
cat > app.js << 'EOF'
const express = require('express');
const helmet = require('helmet');
const compression = require('compression');
const cors = require('cors');
const morgan = require('morgan');
const { v4: uuidv4 } = require('uuid');

const app = express();
const PORT = process.env.PORT || 3000;

// セキュリティ・パフォーマンス設定
app.use(helmet());
app.use(compression());
app.use(cors());
app.use(morgan('combined'));
app.use(express.json());

// Health Check エンドポイント
app.get('/health', (req, res) => {
    res.status(200).json({
        status: 'healthy',
        timestamp: new Date().toISOString(),
        version: process.env.APP_VERSION || '1.0.0',
        environment: process.env.NODE_ENV || 'development'
    });
});

// 残高照会API（模擬）
app.get('/api/balance/:accountId', (req, res) => {
    const { accountId } = req.params;
    
    if (!accountId || accountId.length < 8) {
        return res.status(400).json({
            error: 'Invalid account ID'
        });
    }
    
    // 模擬データ
    const balance = Math.floor(Math.random() * 1000000) + 10000;
    
    res.json({
        accountId,
        balance,
        currency: 'JPY',
        lastUpdated: new Date().toISOString(),
        transactionId: uuidv4()
    });
});

// 送金API（模擬）
app.post('/api/transfer', (req, res) => {
    const { fromAccount, toAccount, amount } = req.body;
    
    if (!fromAccount || !toAccount || !amount) {
        return res.status(400).json({
            error: 'Missing required fields'
        });
    }
    
    if (amount <= 0 || amount > 1000000) {
        return res.status(400).json({
            error: 'Invalid transfer amount'
        });
    }
    
    res.json({
        status: 'completed',
        transactionId: uuidv4(),
        fromAccount,
        toAccount,
        amount,
        fee: Math.floor(amount * 0.001),
        timestamp: new Date().toISOString()
    });
});

// エラーハンドリング
app.use((err, req, res, next) => {
    console.error(err.stack);
    res.status(500).json({
        error: 'Internal server error',
        timestamp: new Date().toISOString()
    });
});

// 404ハンドリング
app.use('*', (req, res) => {
    res.status(404).json({
        error: 'Endpoint not found',
        path: req.originalUrl
    });
});

const server = app.listen(PORT, () => {
    console.log(`Fintech app running on port ${PORT}`);
});

// Graceful shutdown
process.on('SIGTERM', () => {
    console.log('SIGTERM received, shutting down gracefully');
    server.close(() => {
        console.log('Server closed');
        process.exit(0);
    });
});

module.exports = app;
EOF

# テストコード
mkdir -p __tests__
cat > __tests__/app.test.js << 'EOF'
const request = require('supertest');
const app = require('../app');

describe('Fintech App', () => {
    describe('GET /health', () => {
        it('should return health status', async () => {
            const response = await request(app)
                .get('/health')
                .expect(200);
            
            expect(response.body).toHaveProperty('status', 'healthy');
            expect(response.body).toHaveProperty('timestamp');
        });
    });
    
    describe('GET /api/balance/:accountId', () => {
        it('should return balance for valid account', async () => {
            const response = await request(app)
                .get('/api/balance/12345678')
                .expect(200);
            
            expect(response.body).toHaveProperty('accountId', '12345678');
            expect(response.body).toHaveProperty('balance');
            expect(response.body).toHaveProperty('currency', 'JPY');
        });
        
        it('should return 400 for invalid account ID', async () => {
            await request(app)
                .get('/api/balance/123')
                .expect(400);
        });
    });
    
    describe('POST /api/transfer', () => {
        it('should process valid transfer', async () => {
            const transferData = {
                fromAccount: '12345678',
                toAccount: '87654321',
                amount: 10000
            };
            
            const response = await request(app)
                .post('/api/transfer')
                .send(transferData)
                .expect(200);
            
            expect(response.body).toHaveProperty('status', 'completed');
            expect(response.body).toHaveProperty('transactionId');
        });
        
        it('should reject invalid transfer amount', async () => {
            const transferData = {
                fromAccount: '12345678',
                toAccount: '87654321',
                amount: -1000
            };
            
            await request(app)
                .post('/api/transfer')
                .send(transferData)
                .expect(400);
        });
    });
});
EOF

# ESLint設定
cat > .eslintrc.json << 'EOF'
{
    "env": {
        "node": true,
        "es2021": true,
        "jest": true
    },
    "extends": "eslint:recommended",
    "parserOptions": {
        "ecmaVersion": 12,
        "sourceType": "module"
    },
    "rules": {
        "no-console": "warn",
        "no-unused-vars": "error",
        "semi": ["error", "always"],
        "quotes": ["error", "single"]
    }
}
EOF

# Dockerfile
cat > Dockerfile << 'EOF'
# マルチステージビルド
FROM node:18-alpine AS builder

WORKDIR /app

# パッケージファイルのコピー
COPY package*.json ./

# 依存関係のインストール
RUN npm ci --only=production && npm cache clean --force

# アプリケーションコードのコピー
COPY . .

# 本番用イメージ
FROM node:18-alpine AS production

# セキュリティ更新
RUN apk update && apk upgrade && apk add --no-cache dumb-init

# 非rootユーザー作成
RUN addgroup -g 1001 -S nodejs && adduser -S nodejs -u 1001

WORKDIR /app

# 必要なファイルのコピー
COPY --from=builder --chown=nodejs:nodejs /app/node_modules ./node_modules
COPY --from=builder --chown=nodejs:nodejs /app/package*.json ./
COPY --from=builder --chown=nodejs:nodejs /app/app.js ./

# ユーザー切り替え
USER nodejs

# ヘルスチェック
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD node -e "require('http').get('http://localhost:3000/health', (res) => { process.exit(res.statusCode === 200 ? 0 : 1) })"

EXPOSE 3000

# アプリケーション起動
ENTRYPOINT ["dumb-init", "--"]
CMD ["node", "app.js"]
EOF

# .dockerignore
cat > .dockerignore << 'EOF'
node_modules
npm-debug.log*
.git
.gitignore
README.md
.env
.nyc_output
coverage
.docker
__tests__
EOF

echo "サンプルアプリケーション作成完了"
```

### 2.2 CodeCommit リポジトリ作成とプッシュ

```bash
#!/bin/bash
# スクリプト: setup-codecommit.sh

set -e

REPO_NAME="fintech-app"

echo "=== CodeCommit リポジトリセットアップ ==="

# CodeCommit リポジトリ作成
aws codecommit create-repository \
    --repository-name $REPO_NAME \
    --repository-description "Fintech application for CI/CD pipeline demo" \
    2>/dev/null || echo "リポジトリは既に存在します"

# Git 設定
cd fintech-app
git init
git add .
git commit -m "Initial commit: Fintech application setup

- Express.js application with REST API
- Comprehensive test suite with Jest
- Security headers with Helmet
- Docker containerization
- ESLint configuration
- Health check endpoint"

# リモートリポジトリ設定
REGION=$(aws configure get region)
REPO_URL="https://git-codecommit.${REGION}.amazonaws.com/v1/repos/${REPO_NAME}"

git remote add origin $REPO_URL
git branch -M main
git push -u origin main

echo "CodeCommit リポジトリセットアップ完了"
echo "リポジトリURL: $REPO_URL"
```

## Phase 3: CodeBuild プロジェクト構成

### 3.1 マルチステージビルド設定

```yaml
# buildspec.yml
version: 0.2

env:
  variables:
    NODE_ENV: production
  parameter-store:
    SONAR_TOKEN: /cicd/sonar-token
  secrets-manager:
    DB_PASSWORD: prod/db/password:password

phases:
  install:
    runtime-versions:
      nodejs: 18
      docker: 20
    commands:
      - echo "Installing dependencies..."
      - npm ci
      - echo "Installing security scanning tools..."
      - npm install -g @cyclonedx/cyclonedx-npm
      - curl -sfL https://raw.githubusercontent.com/aquasecurity/trivy/main/contrib/install.sh | sh -s -- -b /usr/local/bin

  pre_build:
    commands:
      - echo "Running pre-build phase..."
      - echo "Linting code..."
      - npm run lint
      - echo "Running unit tests..."
      - npm run test:coverage
      - echo "Security audit..."
      - npm audit --audit-level high
      - echo "Generating SBOM..."
      - cyclonedx-npm --output-file sbom.json
      - echo "Logging in to Amazon ECR..."
      - aws ecr get-login-password --region $AWS_DEFAULT_REGION | docker login --username AWS --password-stdin $ECR_REPOSITORY_URI

  build:
    commands:
      - echo "Build started on `date`"
      - echo "Building the Docker image..."
      - docker build -t $IMAGE_TAG .
      - echo "Tagging Docker image..."
      - docker tag $IMAGE_TAG:$IMAGE_TAG $ECR_REPOSITORY_URI:$IMAGE_TAG
      - docker tag $IMAGE_TAG:$IMAGE_TAG $ECR_REPOSITORY_URI:latest
      - echo "Running container security scan..."
      - trivy image --format json --output container-scan.json $IMAGE_TAG

  post_build:
    commands:
      - echo "Build completed on `date`"
      - echo "Pushing the Docker image..."
      - docker push $ECR_REPOSITORY_URI:$IMAGE_TAG
      - docker push $ECR_REPOSITORY_URI:latest
      - echo "Writing image definitions file..."
      - printf '[{"name":"fintech-app","imageUri":"%s"}]' $ECR_REPOSITORY_URI:$IMAGE_TAG > imagedefinitions.json
      - echo "Generating deployment manifest..."
      - |
        cat > deployment-manifest.json << EOF
        {
          "imageUri": "$ECR_REPOSITORY_URI:$IMAGE_TAG",
          "buildTime": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
          "commitHash": "$CODEBUILD_RESOLVED_SOURCE_VERSION",
          "buildNumber": "$CODEBUILD_BUILD_NUMBER",
          "testResults": {
            "unitTests": "$(cat coverage/coverage-summary.json | jq .total.statements.pct)",
            "securityScan": "$(cat container-scan.json | jq '.Results | length')"
          }
        }
        EOF

artifacts:
  files:
    - imagedefinitions.json
    - deployment-manifest.json
    - cloudformation/*
    - scripts/*
  secondary-artifacts:
    TestResults:
      files:
        - coverage/**/*
        - sbom.json
        - container-scan.json
      name: TestResults
    SecurityResults:
      files:
        - container-scan.json
        - sbom.json
      name: SecurityResults

reports:
  jest_reports:
    files:
      - 'coverage/lcov.info'
    file-format: 'CLOVER'
  security_reports:
    files:
      - 'container-scan.json'
    file-format: 'SARIF'

cache:
  paths:
    - '/root/.npm/**/*'
    - 'node_modules/**/*'
```

### 3.2 CodeBuild プロジェクト作成

```bash
#!/bin/bash
# スクリプト: setup-codebuild.sh

set -e

echo "=== CodeBuild プロジェクト作成 ==="

# 設定読み込み
source cicd-config.json
ECR_URI=$(cat cicd-config.json | jq -r '.ecr_uri')
BUCKET_NAME=$(cat cicd-config.json | jq -r '.artifact_bucket')

# CodeBuild プロジェクト設定
cat > codebuild-project.json << EOF
{
    "name": "fintech-app-build",
    "description": "Build project for fintech application with security scanning",
    "source": {
        "type": "CODECOMMIT",
        "location": "https://git-codecommit.${AWS_DEFAULT_REGION}.amazonaws.com/v1/repos/fintech-app",
        "buildspec": "buildspec.yml"
    },
    "artifacts": {
        "type": "S3",
        "location": "${BUCKET_NAME}/build-artifacts"
    },
    "secondaryArtifacts": [
        {
            "type": "S3",
            "location": "${BUCKET_NAME}/test-results",
            "artifactIdentifier": "TestResults"
        },
        {
            "type": "S3", 
            "location": "${BUCKET_NAME}/security-results",
            "artifactIdentifier": "SecurityResults"
        }
    ],
    "environment": {
        "type": "LINUX_CONTAINER",
        "image": "aws/codebuild/amazonlinux2-x86_64-standard:4.0",
        "computeType": "BUILD_GENERAL1_MEDIUM",
        "privilegedMode": true,
        "environmentVariables": [
            {
                "name": "ECR_REPOSITORY_URI",
                "value": "${ECR_URI}"
            },
            {
                "name": "AWS_DEFAULT_REGION",
                "value": "${AWS_DEFAULT_REGION}"
            },
            {
                "name": "AWS_ACCOUNT_ID",
                "value": "$(aws sts get-caller-identity --query Account --output text)"
            },
            {
                "name": "IMAGE_TAG",
                "value": "fintech-app"
            }
        ]
    },
    "serviceRole": "arn:aws:iam::$(aws sts get-caller-identity --query Account --output text):role/CodeBuildServiceRole",
    "timeoutInMinutes": 30,
    "queuedTimeoutInMinutes": 60,
    "cache": {
        "type": "S3",
        "location": "${BUCKET_NAME}/build-cache"
    },
    "logsConfig": {
        "cloudWatchLogs": {
            "status": "ENABLED",
            "groupName": "/aws/codebuild/fintech-app-build"
        },
        "s3Logs": {
            "status": "ENABLED",
            "location": "${BUCKET_NAME}/build-logs"
        }
    }
}
EOF

aws codebuild create-project --cli-input-json file://codebuild-project.json

echo "CodeBuild プロジェクト作成完了"

# 統合テスト用プロジェクト
cat > codebuild-integration-test.json << EOF
{
    "name": "fintech-app-integration-test",
    "description": "Integration test project for fintech application",
    "source": {
        "type": "CODECOMMIT",
        "location": "https://git-codecommit.${AWS_DEFAULT_REGION}.amazonaws.com/v1/repos/fintech-app",
        "buildspec": "integration-test-buildspec.yml"
    },
    "artifacts": {
        "type": "S3",
        "location": "${BUCKET_NAME}/integration-test-results"
    },
    "environment": {
        "type": "LINUX_CONTAINER",
        "image": "aws/codebuild/amazonlinux2-x86_64-standard:4.0",
        "computeType": "BUILD_GENERAL1_MEDIUM",
        "environmentVariables": [
            {
                "name": "TEST_ENVIRONMENT_URL",
                "value": "https://staging-fintech-app.example.com"
            }
        ]
    },
    "serviceRole": "arn:aws:iam::$(aws sts get-caller-identity --query Account --output text):role/CodeBuildServiceRole",
    "timeoutInMinutes": 20
}
EOF

aws codebuild create-project --cli-input-json file://codebuild-integration-test.json

echo "統合テストプロジェクト作成完了"
```

## Phase 4: CodeDeploy アプリケーション設定

### 4.1 Blue/Green デプロイメント設定

```bash
#!/bin/bash
# スクリプト: setup-codedeploy.sh

set -e

echo "=== CodeDeploy アプリケーション設定 ==="

# CodeDeploy アプリケーション作成
aws deploy create-application \
    --application-name fintech-app \
    --compute-platform ECS

# デプロイメント設定（Blue/Green）
aws deploy create-deployment-config \
    --deployment-config-name FinTechBlueGreenDeployment \
    --compute-platform ECS \
    --blue-green-deployment-configuration '{
        "deploymentReadyOption": {
            "actionOnTimeout": "CONTINUE_DEPLOYMENT"
        },
        "terminateBlueInstancesOnDeploymentSuccess": {
            "action": "TERMINATE",
            "terminationWaitTimeInMinutes": 5
        },
        "greenFleetProvisioningOption": {
            "action": "COPY_AUTO_SCALING_GROUP"
        }
    }'

# CodeDeploy サービスロール
cat > codedeploy-trust-policy.json << 'EOF'
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Principal": {
                "Service": "codedeploy.amazonaws.com"
            },
            "Action": "sts:AssumeRole"
        }
    ]
}
EOF

aws iam create-role \
    --role-name CodeDeployServiceRole \
    --assume-role-policy-document file://codedeploy-trust-policy.json

aws iam attach-role-policy \
    --role-name CodeDeployServiceRole \
    --policy-arn arn:aws:iam::aws:policy/service-role/AWSCodeDeployRoleForECS

echo "CodeDeploy アプリケーション設定完了"
```

### 4.2 ECS クラスター設定

```yaml
# cloudformation/ecs-cluster.yml
AWSTemplateFormatVersion: '2010-09-09'
Description: 'ECS Cluster for Fintech Application'

Parameters:
  EnvironmentName:
    Type: String
    Default: production
    Description: Environment name prefix

  VpcCIDR:
    Type: String
    Default: 10.0.0.0/16
    Description: CIDR block for VPC

  PublicSubnet1CIDR:
    Type: String
    Default: 10.0.1.0/24
    Description: CIDR block for public subnet in AZ1

  PublicSubnet2CIDR:
    Type: String
    Default: 10.0.2.0/24
    Description: CIDR block for public subnet in AZ2

  PrivateSubnet1CIDR:
    Type: String
    Default: 10.0.3.0/24
    Description: CIDR block for private subnet in AZ1

  PrivateSubnet2CIDR:
    Type: String
    Default: 10.0.4.0/24
    Description: CIDR block for private subnet in AZ2

Resources:
  # VPC Configuration
  VPC:
    Type: AWS::EC2::VPC
    Properties:
      CidrBlock: !Ref VpcCIDR
      EnableDnsHostnames: true
      EnableDnsSupport: true
      Tags:
        - Key: Name
          Value: !Sub ${EnvironmentName}-VPC

  InternetGateway:
    Type: AWS::EC2::InternetGateway
    Properties:
      Tags:
        - Key: Name
          Value: !Sub ${EnvironmentName}-IGW

  InternetGatewayAttachment:
    Type: AWS::EC2::VPCGatewayAttachment
    Properties:
      InternetGatewayId: !Ref InternetGateway
      VpcId: !Ref VPC

  # Public Subnets
  PublicSubnet1:
    Type: AWS::EC2::Subnet
    Properties:
      VpcId: !Ref VPC
      AvailabilityZone: !Select [0, !GetAZs '']
      CidrBlock: !Ref PublicSubnet1CIDR
      MapPublicIpOnLaunch: true
      Tags:
        - Key: Name
          Value: !Sub ${EnvironmentName}-Public-Subnet-AZ1

  PublicSubnet2:
    Type: AWS::EC2::Subnet
    Properties:
      VpcId: !Ref VPC
      AvailabilityZone: !Select [1, !GetAZs '']
      CidrBlock: !Ref PublicSubnet2CIDR
      MapPublicIpOnLaunch: true
      Tags:
        - Key: Name
          Value: !Sub ${EnvironmentName}-Public-Subnet-AZ2

  # Private Subnets
  PrivateSubnet1:
    Type: AWS::EC2::Subnet
    Properties:
      VpcId: !Ref VPC
      AvailabilityZone: !Select [0, !GetAZs '']
      CidrBlock: !Ref PrivateSubnet1CIDR
      Tags:
        - Key: Name
          Value: !Sub ${EnvironmentName}-Private-Subnet-AZ1

  PrivateSubnet2:
    Type: AWS::EC2::Subnet
    Properties:
      VpcId: !Ref VPC
      AvailabilityZone: !Select [1, !GetAZs '']
      CidrBlock: !Ref PrivateSubnet2CIDR
      Tags:
        - Key: Name
          Value: !Sub ${EnvironmentName}-Private-Subnet-AZ2

  # NAT Gateways
  NatGateway1EIP:
    Type: AWS::EC2::EIP
    DependsOn: InternetGatewayAttachment
    Properties:
      Domain: vpc

  NatGateway2EIP:
    Type: AWS::EC2::EIP
    DependsOn: InternetGatewayAttachment
    Properties:
      Domain: vpc

  NatGateway1:
    Type: AWS::EC2::NatGateway
    Properties:
      AllocationId: !GetAtt NatGateway1EIP.AllocationId
      SubnetId: !Ref PublicSubnet1

  NatGateway2:
    Type: AWS::EC2::NatGateway
    Properties:
      AllocationId: !GetAtt NatGateway2EIP.AllocationId
      SubnetId: !Ref PublicSubnet2

  # Route Tables
  PublicRouteTable:
    Type: AWS::EC2::RouteTable
    Properties:
      VpcId: !Ref VPC
      Tags:
        - Key: Name
          Value: !Sub ${EnvironmentName}-Public-Routes

  DefaultPublicRoute:
    Type: AWS::EC2::Route
    DependsOn: InternetGatewayAttachment
    Properties:
      RouteTableId: !Ref PublicRouteTable
      DestinationCidrBlock: 0.0.0.0/0
      GatewayId: !Ref InternetGateway

  PublicSubnet1RouteTableAssociation:
    Type: AWS::EC2::SubnetRouteTableAssociation
    Properties:
      RouteTableId: !Ref PublicRouteTable
      SubnetId: !Ref PublicSubnet1

  PublicSubnet2RouteTableAssociation:
    Type: AWS::EC2::SubnetRouteTableAssociation
    Properties:
      RouteTableId: !Ref PublicRouteTable
      SubnetId: !Ref PublicSubnet2

  PrivateRouteTable1:
    Type: AWS::EC2::RouteTable
    Properties:
      VpcId: !Ref VPC
      Tags:
        - Key: Name
          Value: !Sub ${EnvironmentName}-Private-Routes-AZ1

  DefaultPrivateRoute1:
    Type: AWS::EC2::Route
    Properties:
      RouteTableId: !Ref PrivateRouteTable1
      DestinationCidrBlock: 0.0.0.0/0
      NatGatewayId: !Ref NatGateway1

  PrivateSubnet1RouteTableAssociation:
    Type: AWS::EC2::SubnetRouteTableAssociation
    Properties:
      RouteTableId: !Ref PrivateRouteTable1
      SubnetId: !Ref PrivateSubnet1

  PrivateRouteTable2:
    Type: AWS::EC2::RouteTable
    Properties:
      VpcId: !Ref VPC
      Tags:
        - Key: Name
          Value: !Sub ${EnvironmentName}-Private-Routes-AZ2

  DefaultPrivateRoute2:
    Type: AWS::EC2::Route
    Properties:
      RouteTableId: !Ref PrivateRouteTable2
      DestinationCidrBlock: 0.0.0.0/0
      NatGatewayId: !Ref NatGateway2

  PrivateSubnet2RouteTableAssociation:
    Type: AWS::EC2::SubnetRouteTableAssociation
    Properties:
      RouteTableId: !Ref PrivateRouteTable2
      SubnetId: !Ref PrivateSubnet2

  # Security Groups
  ALBSecurityGroup:
    Type: AWS::EC2::SecurityGroup
    Properties:
      GroupDescription: Security group for Application Load Balancer
      VpcId: !Ref VPC
      SecurityGroupIngress:
        - IpProtocol: tcp
          FromPort: 80
          ToPort: 80
          CidrIp: 0.0.0.0/0
        - IpProtocol: tcp
          FromPort: 443
          ToPort: 443
          CidrIp: 0.0.0.0/0
      Tags:
        - Key: Name
          Value: !Sub ${EnvironmentName}-ALB-SecurityGroup

  ECSSecurityGroup:
    Type: AWS::EC2::SecurityGroup
    Properties:
      GroupDescription: Security group for ECS tasks
      VpcId: !Ref VPC
      SecurityGroupIngress:
        - IpProtocol: tcp
          FromPort: 3000
          ToPort: 3000
          SourceSecurityGroupId: !Ref ALBSecurityGroup
      Tags:
        - Key: Name
          Value: !Sub ${EnvironmentName}-ECS-SecurityGroup

  # Application Load Balancer
  ApplicationLoadBalancer:
    Type: AWS::ElasticLoadBalancingV2::LoadBalancer
    Properties:
      Name: !Sub ${EnvironmentName}-ALB
      Scheme: internet-facing
      Type: application
      Subnets:
        - !Ref PublicSubnet1
        - !Ref PublicSubnet2
      SecurityGroups:
        - !Ref ALBSecurityGroup
      Tags:
        - Key: Name
          Value: !Sub ${EnvironmentName}-ALB

  # Target Groups for Blue/Green Deployment
  BlueTargetGroup:
    Type: AWS::ElasticLoadBalancingV2::TargetGroup
    Properties:
      Name: !Sub ${EnvironmentName}-Blue-TG
      Port: 3000
      Protocol: HTTP
      VpcId: !Ref VPC
      TargetType: ip
      HealthCheckPath: /health
      HealthCheckIntervalSeconds: 30
      HealthCheckTimeoutSeconds: 5
      HealthyThresholdCount: 2
      UnhealthyThresholdCount: 3
      Matcher:
        HttpCode: 200

  GreenTargetGroup:
    Type: AWS::ElasticLoadBalancingV2::TargetGroup
    Properties:
      Name: !Sub ${EnvironmentName}-Green-TG
      Port: 3000
      Protocol: HTTP
      VpcId: !Ref VPC
      TargetType: ip
      HealthCheckPath: /health
      HealthCheckIntervalSeconds: 30
      HealthCheckTimeoutSeconds: 5
      HealthyThresholdCount: 2
      UnhealthyThresholdCount: 3
      Matcher:
        HttpCode: 200

  # ALB Listener
  ALBListener:
    Type: AWS::ElasticLoadBalancingV2::Listener
    Properties:
      DefaultActions:
        - Type: forward
          TargetGroupArn: !Ref BlueTargetGroup
      LoadBalancerArn: !Ref ApplicationLoadBalancer
      Port: 80
      Protocol: HTTP

  # ECS Cluster
  ECSCluster:
    Type: AWS::ECS::Cluster
    Properties:
      ClusterName: !Sub ${EnvironmentName}-cluster
      CapacityProviders:
        - FARGATE
        - FARGATE_SPOT
      DefaultCapacityProviderStrategy:
        - CapacityProvider: FARGATE
          Weight: 1
        - CapacityProvider: FARGATE_SPOT
          Weight: 4
      ClusterSettings:
        - Name: containerInsights
          Value: enabled

  # ECS Task Execution Role
  ECSTaskExecutionRole:
    Type: AWS::IAM::Role
    Properties:
      AssumeRolePolicyDocument:
        Statement:
          - Effect: Allow
            Principal:
              Service: ecs-tasks.amazonaws.com
            Action: sts:AssumeRole
      ManagedPolicyArns:
        - arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy
      Policies:
        - PolicyName: SecretsManagerAccess
          PolicyDocument:
            Statement:
              - Effect: Allow
                Action:
                  - secretsmanager:GetSecretValue
                Resource: '*'

  # ECS Task Role
  ECSTaskRole:
    Type: AWS::IAM::Role
    Properties:
      AssumeRolePolicyDocument:
        Statement:
          - Effect: Allow
            Principal:
              Service: ecs-tasks.amazonaws.com
            Action: sts:AssumeRole
      Policies:
        - PolicyName: CloudWatchAccess
          PolicyDocument:
            Statement:
              - Effect: Allow
                Action:
                  - logs:CreateLogGroup
                  - logs:CreateLogStream
                  - logs:PutLogEvents
                  - cloudwatch:PutMetricData
                Resource: '*'

  # ECS Task Definition
  TaskDefinition:
    Type: AWS::ECS::TaskDefinition
    Properties:
      Family: !Sub ${EnvironmentName}-fintech-app
      Cpu: 256
      Memory: 512
      NetworkMode: awsvpc
      RequiresCompatibilities:
        - FARGATE
      ExecutionRoleArn: !Ref ECSTaskExecutionRole
      TaskRoleArn: !Ref ECSTaskRole
      ContainerDefinitions:
        - Name: fintech-app
          Image: !Sub ${AWS::AccountId}.dkr.ecr.${AWS::Region}.amazonaws.com/fintech-app:latest
          PortMappings:
            - ContainerPort: 3000
              Protocol: tcp
          LogConfiguration:
            LogDriver: awslogs
            Options:
              awslogs-group: !Sub /ecs/${EnvironmentName}-fintech-app
              awslogs-region: !Ref AWS::Region
              awslogs-stream-prefix: ecs
          Environment:
            - Name: NODE_ENV
              Value: production
            - Name: APP_VERSION
              Value: '1.0.0'
          HealthCheck:
            Command:
              - CMD-SHELL
              - 'curl -f http://localhost:3000/health || exit 1'
            Interval: 30
            Timeout: 5
            Retries: 3
            StartPeriod: 60

  # CloudWatch Log Group
  LogGroup:
    Type: AWS::Logs::LogGroup
    Properties:
      LogGroupName: !Sub /ecs/${EnvironmentName}-fintech-app
      RetentionInDays: 30

  # ECS Service
  ECSService:
    Type: AWS::ECS::Service
    DependsOn: ALBListener
    Properties:
      ServiceName: !Sub ${EnvironmentName}-fintech-app
      Cluster: !Ref ECSCluster
      TaskDefinition: !Ref TaskDefinition
      DesiredCount: 2
      LaunchType: FARGATE
      NetworkConfiguration:
        AwsvpcConfiguration:
          SecurityGroups:
            - !Ref ECSSecurityGroup
          Subnets:
            - !Ref PrivateSubnet1
            - !Ref PrivateSubnet2
          AssignPublicIp: DISABLED
      LoadBalancers:
        - ContainerName: fintech-app
          ContainerPort: 3000
          TargetGroupArn: !Ref BlueTargetGroup
      DeploymentConfiguration:
        MaximumPercent: 200
        MinimumHealthyPercent: 100
        DeploymentCircuitBreaker:
          Enable: true
          Rollback: true

Outputs:
  VPC:
    Description: VPC ID
    Value: !Ref VPC
    Export:
      Name: !Sub ${EnvironmentName}-VPC-ID

  PublicSubnets:
    Description: Public subnet IDs
    Value: !Join [',', [!Ref PublicSubnet1, !Ref PublicSubnet2]]
    Export:
      Name: !Sub ${EnvironmentName}-Public-Subnets

  PrivateSubnets:
    Description: Private subnet IDs
    Value: !Join [',', [!Ref PrivateSubnet1, !Ref PrivateSubnet2]]
    Export:
      Name: !Sub ${EnvironmentName}-Private-Subnets

  ALBEndpoint:
    Description: Application Load Balancer endpoint
    Value: !GetAtt ApplicationLoadBalancer.DNSName
    Export:
      Name: !Sub ${EnvironmentName}-ALB-Endpoint

  ECSCluster:
    Description: ECS Cluster name
    Value: !Ref ECSCluster
    Export:
      Name: !Sub ${EnvironmentName}-ECS-Cluster

  BlueTargetGroup:
    Description: Blue target group ARN
    Value: !Ref BlueTargetGroup
    Export:
      Name: !Sub ${EnvironmentName}-Blue-TargetGroup

  GreenTargetGroup:
    Description: Green target group ARN
    Value: !Ref GreenTargetGroup
    Export:
      Name: !Sub ${EnvironmentName}-Green-TargetGroup
```

## Phase 5: CodePipeline 構築

### 5.1 パイプライン設定

```json
{
    "pipeline": {
        "name": "fintech-app-pipeline",
        "roleArn": "arn:aws:iam::ACCOUNT_ID:role/CodePipelineServiceRole",
        "artifactStore": {
            "type": "S3",
            "location": "BUCKET_NAME"
        },
        "stages": [
            {
                "name": "Source",
                "actions": [
                    {
                        "name": "SourceAction",
                        "actionTypeId": {
                            "category": "Source",
                            "owner": "AWS",
                            "provider": "CodeCommit",
                            "version": "1"
                        },
                        "configuration": {
                            "RepositoryName": "fintech-app",
                            "BranchName": "main",
                            "PollForSourceChanges": "false"
                        },
                        "outputArtifacts": [
                            {
                                "name": "SourceOutput"
                            }
                        ]
                    }
                ]
            },
            {
                "name": "Build",
                "actions": [
                    {
                        "name": "Build",
                        "actionTypeId": {
                            "category": "Build",
                            "owner": "AWS",
                            "provider": "CodeBuild",
                            "version": "1"
                        },
                        "configuration": {
                            "ProjectName": "fintech-app-build"
                        },
                        "inputArtifacts": [
                            {
                                "name": "SourceOutput"
                            }
                        ],
                        "outputArtifacts": [
                            {
                                "name": "BuildOutput"
                            }
                        ]
                    },
                    {
                        "name": "SecurityScan",
                        "actionTypeId": {
                            "category": "Build",
                            "owner": "AWS",
                            "provider": "CodeBuild",
                            "version": "1"
                        },
                        "configuration": {
                            "ProjectName": "fintech-app-security-scan"
                        },
                        "inputArtifacts": [
                            {
                                "name": "SourceOutput"
                            }
                        ],
                        "outputArtifacts": [
                            {
                                "name": "SecurityOutput"
                            }
                        ],
                        "runOrder": 1
                    }
                ]
            },
            {
                "name": "Deploy-Staging",
                "actions": [
                    {
                        "name": "Deploy",
                        "actionTypeId": {
                            "category": "Deploy",
                            "owner": "AWS",
                            "provider": "ECS",
                            "version": "1"
                        },
                        "configuration": {
                            "ClusterName": "staging-cluster",
                            "ServiceName": "staging-fintech-app",
                            "FileName": "imagedefinitions.json"
                        },
                        "inputArtifacts": [
                            {
                                "name": "BuildOutput"
                            }
                        ],
                        "region": "us-east-1"
                    }
                ]
            },
            {
                "name": "Integration-Test",
                "actions": [
                    {
                        "name": "IntegrationTest",
                        "actionTypeId": {
                            "category": "Build",
                            "owner": "AWS",
                            "provider": "CodeBuild",
                            "version": "1"
                        },
                        "configuration": {
                            "ProjectName": "fintech-app-integration-test"
                        },
                        "inputArtifacts": [
                            {
                                "name": "SourceOutput"
                            }
                        ],
                        "outputArtifacts": [
                            {
                                "name": "TestOutput"
                            }
                        ]
                    }
                ]
            },
            {
                "name": "Manual-Approval",
                "actions": [
                    {
                        "name": "ManualApproval",
                        "actionTypeId": {
                            "category": "Approval",
                            "owner": "AWS",
                            "provider": "Manual",
                            "version": "1"
                        },
                        "configuration": {
                            "NotificationArn": "arn:aws:sns:us-east-1:ACCOUNT_ID:pipeline-notifications",
                            "CustomData": "Please review staging deployment and security scan results before proceeding to production"
                        }
                    }
                ]
            },
            {
                "name": "Deploy-Production",
                "actions": [
                    {
                        "name": "Deploy",
                        "actionTypeId": {
                            "category": "Deploy",
                            "owner": "AWS",
                            "provider": "CodeDeployToECS",
                            "version": "1"
                        },
                        "configuration": {
                            "ApplicationName": "fintech-app",
                            "DeploymentGroupName": "production-deployment-group"
                        },
                        "inputArtifacts": [
                            {
                                "name": "BuildOutput"
                            }
                        ],
                        "region": "us-east-1"
                    }
                ]
            }
        ]
    }
}
```

このLab 1では、エンタープライズ級のCI/CDパイプラインの構築方法を詳細に学習できます。次のLab 2では、Infrastructure as Codeを使用したより高度な自動化を実装します。

<function_calls>
<invoke name="TodoWrite">
<parameter name="todos">[{"id": "19", "content": "MLE-A\u8a66\u9a13\u306e\u6700\u65b0\u60c5\u5831\u3068\u51fa\u984c\u7bc4\u56f2\u3092\u8abf\u67fb", "status": "completed", "priority": "high"}, {"id": "20", "content": "AWS ML\u30b5\u30fc\u30d3\u30b9\u306e\u6700\u65b0\u30c9\u30ad\u30e5\u30e1\u30f3\u30c8\u3092MCP\u30b5\u30fc\u30d0\u3067\u53c2\u7167", "status": "completed", "priority": "high"}, {"id": "21", "content": "ML\u30a8\u30f3\u30b8\u30cb\u30a2\u5411\u3051\u30cf\u30f3\u30ba\u30aa\u30f3\u6559\u6750\u306e\u69cb\u6210\u8a2d\u8a08", "status": "completed", "priority": "high"}, {"id": "22", "content": "\u5b9f\u8df5\u7684\u306aML\u30d1\u30a4\u30d7\u30e9\u30a4\u30f3\u30e9\u30dc\u306e\u4f5c\u6210", "status": "completed", "priority": "medium"}, {"id": "23", "content": "SageMaker\u3068\u95a2\u9023\u30b5\u30fc\u30d3\u30b9\u306e\u5b9f\u8df5\u30e9\u30dc", "status": "pending", "priority": "medium"}, {"id": "24", "content": "MLOps\u3068\u30e2\u30c7\u30eb\u30c7\u30d7\u30ed\u30a4\u306e\u30e9\u30dc", "status": "pending", "priority": "medium"}, {"id": "25", "content": "MLE-A\u8a66\u9a13\u60f3\u5b9a\u554f\u984c\u96c6\u306e\u4f5c\u6210", "status": "completed", "priority": "medium"}, {"id": "26", "content": "\u6559\u6750\u306e\u691c\u8a3c\u3068\u6700\u7d42\u8abf\u6574", "status": "pending", "priority": "low"}, {"id": "27", "content": "DevOps Pro\u8a66\u9a13\u306e\u6700\u65b0\u60c5\u5831\u3068\u51fa\u984c\u7bc4\u56f2\u3092\u8abf\u67fb", "status": "completed", "priority": "medium"}, {"id": "28", "content": "DevOps\u5411\u3051\u30cf\u30f3\u30ba\u30aa\u30f3\u6559\u6750\u306e\u4f5c\u6210", "status": "completed", "priority": "medium"}, {"id": "29", "content": "\u6559\u6750\u7528\u30d5\u30a9\u30eb\u30c0\u69cb\u9020\u306e\u6574\u7406\u3068\u4f5c\u6210", "status": "completed", "priority": "high"}]