# AWS Certified Advanced Networking - Specialty (ANS-C01)

## 📋 試験概要

**正式名称**: AWS Certified Advanced Networking - Specialty  
**試験コード**: ANS-C01  
**難易度**: ⭐⭐⭐⭐⭐  
**試験時間**: 170分  
**問題数**: 65問（採点対象55問、評価用10問）  
**費用**: $300 USD  
**合格点**: 750/1000  

### 📊 試験ドメインと配点

1. **Domain 1: Network Design** - 30%
2. **Domain 2: Network Implementation** - 26%
3. **Domain 3: Network Management and Operation** - 20%
4. **Domain 4: Network Security, Compliance, and Governance** - 24%

## 🎯 対象者

- **推奨経験**: ネットワーク実務経験5年以上
- **AWS経験**: AWS運用経験3年以上、複雑なネットワーク設計経験
- **前提資格**: Associate レベル推奨（Solutions Architect、SysOps Administrator）

### 必要なスキル
- 複雑なネットワーク設計・実装
- VPC、VPN、Direct Connect
- ハイブリッドネットワーク構成
- ネットワークセキュリティ
- ネットワークトラブルシューティング

## 🗂️ 教材構成

### 📚 基礎教材
- `00-fundamentals.md` - ネットワーク基礎と試験戦略
- `01-exam-guide.md` - 詳細な出題範囲

### 🔬 ハンズオンラボ
- `labs/lab01-vpc-design-patterns/` - VPC設計パターン
- `labs/lab02-hybrid-connectivity/` - ハイブリッド接続
- `labs/lab03-load-balancing/` - 負荷分散とトラフィック制御
- `labs/lab04-security-compliance/` - ネットワークセキュリティ
- `labs/lab05-troubleshooting/` - ネットワークトラブルシューティング

### 📝 問題演習
- `practice-exams/` - ドメイン別想定問題
- `troubleshooting/` - 実践的なネットワーク障害対応

## 🚀 学習順序（推奨）

### Phase 1: 基礎固め（3-4週間）
1. **ネットワーク基礎理論**
   - OSI/TCP IP モデル
   - サブネット、CIDR、BGP
   
2. **AWS ネットワーク基礎**
   - VPC、サブネット、ルートテーブル
   - セキュリティグループ、NACL

### Phase 2: 設計・実装（4-5週間）
3. **Lab 1: VPC設計パターン**
   - 複雑なVPC設計
   - マルチAZ、マルチリージョン
   
4. **Lab 2: ハイブリッド接続**
   - VPN、Direct Connect
   - Transit Gateway

### Phase 3: 運用・管理（3-4週間）
5. **Lab 3: 負荷分散**
   - ELB、ALB、NLB
   - Global Accelerator
   
6. **Lab 4: ネットワークセキュリティ**
   - WAF、Shield、GuardDuty
   - VPC Flow Logs

### Phase 4: トラブルシューティング（2-3週間）
7. **Lab 5: 障害対応**
   - ネットワーク分析
   - パフォーマンス最適化

### Phase 5: 試験対策（1-2週間）
8. **問題演習と総復習**
   - ドメイン別問題集（100問）
   - 苦手分野の重点学習

## 💰 費用概算

### ハンズオンラボ実行コスト
| ラボ | 推定時間 | 推定コスト |
|------|----------|------------|
| Lab 1 | 8-12時間 | $30-50 |
| Lab 2 | 10-15時間 | $40-70 |
| Lab 3 | 6-10時間 | $20-35 |
| Lab 4 | 8-12時間 | $25-45 |
| Lab 5 | 6-8時間 | $15-25 |

**総計**: $130-225 (全ラボ完了時)

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
# Python (boto3用)
sudo apt-get install python3-pip
pip3 install boto3

# jq (JSON処理用)
sudo apt-get install jq

# dig, nslookup (DNS診断用)
sudo apt-get install dnsutils
```

### 権限設定
- NetworkAdministrator（学習用）
- 本番環境では最小権限の原則を適用

## 📊 学習進捗管理

### ドメイン別チェックリスト

#### Domain 1: Network Design (30%)
- [ ] VPC設計原則とベストプラクティス
- [ ] ハイブリッドネットワーク設計
- [ ] 可用性とスケーラビリティ設計
- [ ] 費用対効果の最適化

#### Domain 2: Network Implementation (26%)
- [ ] VPC、サブネット、ルーティング実装
- [ ] VPN、Direct Connect設定
- [ ] Load Balancer設定
- [ ] DNS設定とRoute 53

#### Domain 3: Network Management and Operation (20%)
- [ ] ネットワーク監視とメトリクス
- [ ] ログ分析とトラブルシューティング
- [ ] 自動化とオーケストレーション
- [ ] 容量計画と最適化

#### Domain 4: Network Security, Compliance, and Governance (24%)
- [ ] セキュリティグループとNACL
- [ ] WAF、Shield設定
- [ ] 暗号化とキー管理
- [ ] コンプライアンス要件

## 🎯 試験対策のポイント

### 頻出トピック
1. **複雑なVPC設計**
2. **ハイブリッド接続（VPN、Direct Connect）**
3. **負荷分散とトラフィック制御**
4. **ネットワークセキュリティ**
5. **トラブルシューティング手法**

### 実装重視の学習
- 理論だけでなく実際にハンズオンで構築
- 複数のサービスを組み合わせたソリューション
- 本番運用を想定したベストプラクティス

## 🔗 参考リソース

### AWS公式
- [AWS Well-Architected Framework](https://aws.amazon.com/architecture/well-architected/)
- [AWS Networking Best Practices](https://aws.amazon.com/architecture/networking/)
- [AWS Networking Blog](https://aws.amazon.com/blogs/networking-and-content-delivery/)

### 実践リソース
- [AWS Samples (GitHub)](https://github.com/aws-samples)
- [AWS Workshop Studio](https://workshops.aws/)
- [re:Invent Networking Sessions](https://www.youtube.com/user/AmazonWebServices)

---

**重要**: Specialty レベルの試験は深い専門知識が必要です。各ラボを実際に構築し、運用経験を積むことで合格に近づけます。単なる暗記ではなく、設計判断の根拠を説明できるレベルを目指しましょう。