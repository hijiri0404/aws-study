# AWS Transit Gateway VPC Infrastructure

このプロジェクトは、AWS Transit Gatewayを使用してVPC-A、VPC-B、VPC-Cを中継接続する構成をCloudFormationで構築します。

## 構成概要

- **VPC-A**: 10.1.0.0/16 - EC2インスタンスを含む
- **VPC-B**: 10.2.0.0/16 - Transit Gatewayハブとして機能
- **VPC-C**: 10.3.0.0/16 - EC2インスタンスを含む
- **Transit Gateway**: VPC-BにてVPC-AとVPC-Cを中継

## ファイル構成

```
├── aws-transit-gateway-infra.yaml    # CloudFormationテンプレート
├── deploy-stack.sh                   # デプロイメントスクリプト
├── test-ping-connectivity.sh         # 接続テストスクリプト
└── AWS-Transit-Gateway-README.md     # このファイル
```

## 前提条件

1. AWS CLIがインストールされ、適切に設定されている
2. EC2 Key Pairが作成されている（デフォルト名: `my-key-pair`）
3. 適切なIAM権限が設定されている（VPC、EC2、Transit Gateway、CloudFormationの操作権限）

## デプロイメント手順

### 1. スタックのデプロイ

```bash
./deploy-stack.sh
```

このスクリプトは以下を実行します：
- CloudFormationテンプレートの検証
- スタックの作成または更新
- リソースの作成状況の監視

### 2. 接続テストの実行

```bash
./test-ping-connectivity.sh
```

このスクリプトは以下を実行します：
- EC2インスタンスの状態確認
- VPC-AからVPC-Cへのping接続テスト
- VPC-CからVPC-Aへのping接続テスト
- Transit Gatewayルートテーブルの確認

## 手動テスト手順

AWS Systems Manager Session Managerを使用して手動でテストする場合：

1. **VPC-AのEC2インスタンスに接続**
   ```bash
   aws ssm start-session --target <EC2-A-INSTANCE-ID> --region us-east-1
   ```

2. **VPC-CのIPアドレスにping**
   ```bash
   ping <VPC-C-INSTANCE-IP>
   ```

3. **同様にVPC-CからVPC-Aへもテスト**

## 設定のカスタマイズ

### Key Pairの変更

`deploy-stack.sh`内の`KEY_PAIR_NAME`変数を変更：
```bash
KEY_PAIR_NAME="your-key-pair-name"
```

### リージョンの変更

`deploy-stack.sh`と`test-ping-connectivity.sh`内の`REGION`変数を変更：
```bash
REGION="ap-northeast-1"
```

### CIDR範囲の変更

`aws-transit-gateway-infra.yaml`内のCidrBlock値を変更：
```yaml
VpcCidrBlock: 10.1.0.0/16  # VPC-A
VpcCidrBlock: 10.2.0.0/16  # VPC-B
VpcCidrBlock: 10.3.0.0/16  # VPC-C
```

## トラブルシューティング

### 接続テストが失敗する場合

1. **セキュリティグループの確認**
   - ICMPプロトコルが許可されているか確認
   - 10.0.0.0/8からのトラフィックが許可されているか確認

2. **ルートテーブルの確認**
   - Transit Gatewayへのルートが正しく設定されているか確認

3. **Transit Gatewayアタッチメントの確認**
   - 全てのVPCがTransit Gatewayに正しくアタッチされているか確認

### インスタンスに接続できない場合

1. **Systems Manager Session Managerの設定**
   - EC2インスタンスにSSM Agentがインストールされているか確認
   - Session Manager plugin がローカルマシンにインストールされているか確認

2. **IAMロールの確認**
   - EC2インスタンスに適切なIAMロールが付与されているか確認

## クリーンアップ

作成したリソースを削除する場合：

```bash
aws cloudformation delete-stack --stack-name transit-gateway-vpc-stack --region us-east-1
```

## 注意事項

- このインフラストラクチャの運用にはAWS料金が発生します
- 不要になったリソースは適切に削除してください
- 本番環境での使用前には、セキュリティグループやNACLの設定を適切に見直してください