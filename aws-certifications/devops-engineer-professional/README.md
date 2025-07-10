# AWS Certified DevOps Engineer - Professional (DOP-C02)

## 📋 試験概要

**正式名称**: AWS Certified DevOps Engineer - Professional  
**試験コード**: DOP-C02  
**難易度**: ⭐⭐⭐⭐⭐  
**試験時間**: 180分  
**問題数**: 75問（採点対象65問、評価用10問）  
**費用**: $300 USD  
**合格点**: 750/1000  

### 📊 試験ドメインと配点

1. **Domain 1: SDLC Automation** - 22%
2. **Domain 2: Configuration Management and Infrastructure as Code** - 17%
3. **Domain 3: Resilient Cloud Solutions** - 15%
4. **Domain 4: Monitoring and Logging** - 15%
5. **Domain 5: Incident and Event Response** - 14%
6. **Domain 6: Security and Compliance** - 17%

## 🎯 対象者

- **推奨経験**: DevOps実務経験2年以上
- **AWS経験**: AWS運用経験3年以上
- **前提資格**: Associate レベル推奨（Solutions Architect、SysOps Administrator）

### 必要なスキル
- CI/CD パイプライン設計・運用
- Infrastructure as Code (IaC)
- 監視・ロギング・アラート
- インシデント対応
- セキュリティ・コンプライアンス

## 🗂️ 教材構成

### 📚 基礎教材
- `00-fundamentals.md` - DevOps概念と試験戦略
- `01-exam-guide.md` - 詳細な出題範囲

### 🔬 ハンズオンラボ
- `labs/lab01-cicd-pipeline/` - CI/CDパイプライン構築
- `labs/lab02-infrastructure-as-code/` - CloudFormation/CDK実践
- `labs/lab03-monitoring-logging/` - 包括的監視システム
- `labs/lab04-incident-response/` - 自動復旧システム
- `labs/lab05-security-compliance/` - セキュリティ自動化

### 📝 問題演習
- `practice-exams/` - ドメイン別想定問題
- `troubleshooting/` - 実践的な障害対応

## 🚀 学習順序（推奨）

### Phase 1: 基礎固め（2-3週間）
1. **DevOps理論とAWSサービス概要**
   - DevOpsプラクティスの理解
   - AWS DevOpsサービスマップ
   
2. **CI/CD基礎**
   - CodeCommit, CodeBuild, CodeDeploy, CodePipeline
   - デプロイ戦略（Blue/Green, Canary, Rolling）

### Phase 2: 自動化実装（4-5週間）
3. **Lab 1: CI/CDパイプライン**
   - マルチステージパイプライン
   - 自動テストと品質ゲート
   
4. **Lab 2: Infrastructure as Code**
   - CloudFormation実践
   - AWS CDK開発

### Phase 3: 運用自動化（3-4週間）
5. **Lab 3: 監視・ロギング**
   - CloudWatch, X-Ray, Config
   - カスタムメトリクスとアラート
   
6. **Lab 4: インシデント対応**
   - Systems Manager
   - 自動復旧システム

### Phase 4: セキュリティ・コンプライアンス（2-3週間）
7. **Lab 5: セキュリティ自動化**
   - セキュリティスキャン自動化
   - コンプライアンスチェック

### Phase 5: 試験対策（1-2週間）
8. **問題演習と総復習**
   - ドメイン別問題集
   - 苦手分野の重点学習

## 💰 費用概算

### ハンズオンラボ実行コスト
| ラボ | 推定時間 | 推定コスト |
|------|----------|------------|
| Lab 1 | 6-8時間 | $20-30 |
| Lab 2 | 8-12時間 | $25-40 |
| Lab 3 | 6-10時間 | $15-25 |
| Lab 4 | 4-6時間 | $10-20 |
| Lab 5 | 6-8時間 | $15-25 |

**総計**: $85-140 (全ラボ完了時)

### コスト削減のコツ
- 開発環境では小さいインスタンスを使用
- 不要なリソースは即座に削除
- CloudFormation でリソース管理
- AWS Free Tier の活用

## 🛠️ 事前準備

### 必要な環境
```bash
# AWS CLI インストール・設定
aws configure
aws sts get-caller-identity

# 必要なツールのインストール
# Node.js (CDK用)
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs

# AWS CDK
npm install -g aws-cdk

# Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# Terraform (オプション)
wget https://releases.hashicorp.com/terraform/1.6.0/terraform_1.6.0_linux_amd64.zip
unzip terraform_1.6.0_linux_amd64.zip
sudo mv terraform /usr/local/bin/
```

### 権限設定
- AdministratorAccess（学習用）
- 本番環境では最小権限の原則を適用

## 📊 学習進捗管理

### ドメイン別チェックリスト

#### Domain 1: SDLC Automation (22%)
- [ ] CodeCommit でのソース管理
- [ ] CodeBuild での自動ビルド
- [ ] CodeDeploy でのデプロイ自動化
- [ ] CodePipeline でのパイプライン構築
- [ ] テスト自動化の実装

#### Domain 2: Configuration Management and IaC (17%)
- [ ] CloudFormation テンプレート作成
- [ ] AWS CDK による開発
- [ ] Systems Manager でのConfigMgmt
- [ ] OpsWorks での構成管理

#### Domain 3: Resilient Cloud Solutions (15%)
- [ ] Auto Scaling の設定
- [ ] Elastic Load Balancer の構成
- [ ] Multi-AZ/Multi-Region 構成
- [ ] 災害復旧計画の実装

#### Domain 4: Monitoring and Logging (15%)
- [ ] CloudWatch メトリクス・ログ
- [ ] X-Ray による分散トレーシング
- [ ] Config による構成管理
- [ ] カスタムメトリクスの実装

#### Domain 5: Incident and Event Response (14%)
- [ ] Systems Manager の活用
- [ ] Lambda による自動復旧
- [ ] EventBridge でのイベント処理
- [ ] SNS/SQS での通知システム

#### Domain 6: Security and Compliance (17%)
- [ ] IAM ロール・ポリシー管理
- [ ] Secrets Manager でのシークレット管理
- [ ] Inspector でのセキュリティ評価
- [ ] Config Rules でのコンプライアンス

## 🎯 試験対策のポイント

### 頻出トピック
1. **CI/CD パイプライン設計**
2. **CloudFormation/CDK による IaC**
3. **監視・アラート戦略**
4. **自動復旧機能の実装**
5. **セキュリティベストプラクティス**

### 実装重視の学習
- 理論だけでなく実際にハンズオンで構築
- 複数のサービスを組み合わせたソリューション
- 本番運用を想定したベストプラクティス

## 🔗 参考リソース

### AWS公式
- [AWS Well-Architected Framework](https://aws.amazon.com/architecture/well-architected/)
- [DevOps Best Practices](https://aws.amazon.com/devops/)
- [AWS DevOps Blog](https://aws.amazon.com/blogs/devops/)

### 実践リソース
- [AWS Samples (GitHub)](https://github.com/aws-samples)
- [AWS Workshop Studio](https://workshops.aws/)
- [re:Invent DevOps Sessions](https://www.youtube.com/user/AmazonWebServices)

## ⚡ DOP-C01 からの変更点

### 新機能・サービス
- AWS Backup
- Amazon FSx
- AWS Fault Injection Simulator
- Aurora Serverless
- DocumentDB
- ElastiCache
- Redshift

### 重要度変更
- **セキュリティ・コンプライアンス**: 10% → 17% (大幅増加)
- **インシデント対応**: 18% → 14% (減少)
- **設定管理・IaC**: 19% → 17% (減少)

---

**重要**: Professional レベルの試験は実践経験が重要です。各ラボを実際に構築し、運用経験を積むことで合格に近づけます。単なる暗記ではなく、設計判断の根拠を説明できるレベルを目指しましょう。