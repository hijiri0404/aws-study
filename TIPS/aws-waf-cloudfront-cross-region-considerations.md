# AWS WAF v2 + CloudFront クロスリージョン運用の考慮事項

## 概要

AWS WAF v2とCloudFrontを組み合わせる際、WAFはUS East (N. Virginia)リージョンでの作成が必須となります。
東京リージョンで他のリソースを運用する場合の構築・運用における考慮事項をまとめました。

## リージョン制約

### CloudFront
- **グローバルサービス**: リージョン指定なしで作成
- 世界中のエッジロケーションにデプロイ

### AWS WAF v2
- **CloudFront用**: **US East (N. Virginia)** での作成が必須
- コンソールでは「Global (CloudFront)」として表示
- Web ACL、ルールグループ、IPセット等すべて us-east-1 に配置

## 📊 監視・運用面の考慮事項

### CloudWatchメトリクス
- **配置場所**: WAFメトリクスはバージニアリージョンのCloudWatchに記録
- **課題**: 東京リージョンのダッシュボードでは直接表示不可
- **対応**: クロスリージョンでのメトリクス監視設定が必要

### ログ管理
- **配置場所**: WAFログはバージニアリージョンのCloudWatch Logsに送信
- **課題**: 東京リージョンのログ集約システムと分離
- **対応**: ログ転送の仕組みを構築

## 🔧 運用面の課題

### 1. 管理コンソールの切り替え
- **課題**: WAF設定変更時はバージニアリージョンに切り替えが必要
- **影響**: 他のリソース（東京）との操作が分散

### 2. アラート・通知
- **課題**: WAFアラートはバージニアリージョンのSNSトピックに配信
- **影響**: 東京リージョンの運用チームへの通知連携が複雑

### 3. 自動化・CI/CD
- **課題**: Infrastructure as Code（CloudFormation/Terraform）でリージョン指定の管理が必要
- **影響**: デプロイスクリプトで複数リージョンへの配慮が必要

## 💰 コスト面の考慮

### データ転送費用
- **発生要因**: バージニア→東京間でのログ転送
- **影響**: データ転送料金が発生する可能性
- **追加費用**: CloudWatchメトリクスのクロスリージョン参照

## ✅ 推奨される対策

### 1. 統合監視の設定
```bash
# バージニアリージョンのWAFメトリクスを東京リージョンに転送
# 統合ダッシュボードでの可視化を実現
```

- CloudWatch Cross-Region Dashboardの活用
- メトリクスストリームでのデータ転送設定

### 2. ログ集約の仕組み
```bash
# Kinesis Data Firehoseを使用してログを東京リージョンに転送
# S3での統合ログ管理
```

- WAFログ → Kinesis Data Firehose → S3 (東京リージョン)
- 統合ログ分析基盤の構築

### 3. 運用手順の標準化
- **WAF設定変更時の手順書作成**
  - リージョン切り替え手順
  - 設定変更チェックリスト
  
- **緊急時対応のリージョン切り替え手順**
  - 障害発生時の対応フロー
  - 責任者・連絡先の明確化

### 4. Infrastructure as Code対応
```yaml
# CloudFormation例
# WAF用テンプレート (us-east-1)
AWSTemplateFormatVersion: '2010-09-09'
Parameters:
  Environment:
    Type: String
    Default: prod
Resources:
  WebACL:
    Type: AWS::WAFv2::WebACL
    Properties:
      Name: !Sub '${Environment}-cloudfront-waf'
      Scope: CLOUDFRONT
      # ... 他の設定
```

```hcl
# Terraform例
# WAF用設定 (us-east-1)
provider "aws" {
  alias  = "us-east-1"
  region = "us-east-1"
}

resource "aws_wafv2_web_acl" "cloudfront_waf" {
  provider = aws.us-east-1
  name     = "${var.environment}-cloudfront-waf"
  scope    = "CLOUDFRONT"
  # ... 他の設定
}
```

## 📋 チェックリスト

### 構築時
- [ ] WAF Web ACLをus-east-1で作成
- [ ] CloudFrontディストリビューションの作成
- [ ] WAFとCloudFrontの関連付け
- [ ] ログ転送設定の構築
- [ ] 監視ダッシュボードの設定

### 運用時
- [ ] WAF設定変更手順の確立
- [ ] クロスリージョン監視の実装
- [ ] アラート通知の統合
- [ ] 定期的なログ確認プロセス
- [ ] 緊急時対応手順の整備

## まとめ

AWS WAF v2とCloudFrontのクロスリージョン運用では、監視・ログ管理・運用手順の標準化が重要です。
事前に適切な対策を講じることで、運用面の課題を最小限に抑え、効率的なセキュリティ運用を実現できます。

## 関連リンク

- [AWS WAF Developer Guide](https://docs.aws.amazon.com/waf/latest/developerguide/)
- [CloudFront Developer Guide](https://docs.aws.amazon.com/cloudfront/latest/developerguide/)
- [AWS WAF Pricing](https://aws.amazon.com/waf/pricing/)