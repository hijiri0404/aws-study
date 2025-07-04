# AWS Advanced Networking Specialty (ANS-C01) 実践ハンズオン教材

## 教材概要

この教材は、AWS Certified Advanced Networking - Specialty (ANS-C01) 試験に向けた実践的なハンズオンガイドです。試験の4つの主要ドメインに対応した実習を通じて、AWS の高度なネットワーキング機能を体験できます。

## 試験概要

- **試験時間**: 170分
- **問題数**: 65問 (選択/複数選択)
- **費用**: $300 USD
- **推奨経験**: ネットワーキング5年以上、クラウド・ハイブリッドネットワーキング2年以上

## 試験ドメインと配点

1. **Domain 1: Network Design** - 30%
2. **Domain 2: Network Implementation** - 26%
3. **Domain 3: Network Management and Operation** - 20%
4. **Domain 4: Network Security, Compliance, and Governance** - 24%

## ハンズオン教材の構成

### 事前準備

#### 必要なツール
- AWS CLI (最新版)
- AWS Management Console アクセス
- Terraform (オプション)
- Python 3.8+ (スクリプト実行用)

#### 権限設定
- VPC、EC2、Route 53、Direct Connect、Transit Gateway等の作成権限
- CloudFormation、CloudWatch、AWS Config への読み取り/書き込み権限

---

## Domain 1: Network Design (30%)

### Lab 1-1: 企業向けマルチアカウント VPC 設計

**学習目標**: 企業環境を想定したスケーラブルなネットワーク設計

**シナリオ**: 
本社、支社、リモートワーカー環境を持つ企業のネットワーク設計

#### 詳細な設計要件
- **本社**: 東京リージョン、従業員5000名、帯域要件 10Gbps
- **支社**: 大阪・名古屋・福岡、各500名、帯域要件 1Gbps
- **リモートワーカー**: 全国1000名、VPN接続
- **システム要件**: 24時間365日稼働、RTO < 1時間、RPO < 15分

#### 実習内容

**Phase 1: アーキテクチャ設計**
```
組織構造:
├── Security Account (セキュリティログ集約)
├── Shared Services Account (DNS、監視)
├── Production Account (本社システム)
├── Development Account (開発環境)
└── DR Account (災害復旧)
```

**Phase 2: IP アドレス設計**
```
本社 VPC:     10.0.0.0/16
├── Public:   10.0.1.0/24, 10.0.2.0/24 (Multi-AZ)
├── Private:  10.0.10.0/24, 10.0.11.0/24 (Application)
├── DB:       10.0.20.0/24, 10.0.21.0/24 (Database)
└── Mgmt:     10.0.100.0/24 (Management)

支社 VPC (大阪): 10.1.0.0/16
支社 VPC (名古屋): 10.2.0.0/16
支社 VPC (福岡): 10.3.0.0/16
```

**Phase 3: 実装手順**

1. **Organizations セットアップ**
```bash
# Organizations 作成
aws organizations create-organization --feature-set ALL

# アカウント作成
aws organizations create-account \
  --email security@company.com \
  --account-name "Security-Account"

# SCP (Service Control Policy) 適用
aws organizations create-policy \
  --name "DenyHighRiskActions" \
  --description "Deny high-risk actions" \
  --type SERVICE_CONTROL_POLICY \
  --content file://scp-policy.json
```

2. **VPC 作成と設定**
```bash
# 本社 VPC 作成
aws ec2 create-vpc \
  --cidr-block 10.0.0.0/16 \
  --tag-specifications 'ResourceType=vpc,Tags=[{Key=Name,Value=HQ-Production-VPC},{Key=Environment,Value=Production}]'

# サブネット作成 (複数AZ)
for az in a c; do
  aws ec2 create-subnet \
    --vpc-id $VPC_ID \
    --cidr-block 10.0.1${az/a/0}${az/c/1}.0/24 \
    --availability-zone ap-northeast-1${az}
done

# インターネットゲートウェイ
aws ec2 create-internet-gateway
aws ec2 attach-internet-gateway --internet-gateway-id $IGW_ID --vpc-id $VPC_ID

# NAT ゲートウェイ (Multi-AZ)
aws ec2 create-nat-gateway \
  --subnet-id $PUBLIC_SUBNET_1A \
  --allocation-id $EIP_1A
```

3. **Transit Gateway 設計**
```bash
# Transit Gateway 作成
aws ec2 create-transit-gateway \
  --description "Enterprise Hub TGW" \
  --options 'AmazonSideAsn=64512,AutoAcceptSharedAttachments=disable,DefaultRouteTableAssociation=disable,DefaultRouteTablePropagation=disable'

# カスタムルートテーブル作成
aws ec2 create-transit-gateway-route-table --transit-gateway-id $TGW_ID

# セグメント化のためのルートテーブル
# Production Segment
aws ec2 create-transit-gateway-route-table \
  --transit-gateway-id $TGW_ID \
  --tag-specifications 'ResourceType=transit-gateway-route-table,Tags=[{Key=Name,Value=Production-RT}]'

# Development Segment
aws ec2 create-transit-gateway-route-table \
  --transit-gateway-id $TGW_ID \
  --tag-specifications 'ResourceType=transit-gateway-route-table,Tags=[{Key=Name,Value=Development-RT}]'
```

4. **高度なルーティング設定**
```bash
# VPC アタッチメント
aws ec2 create-transit-gateway-vpc-attachment \
  --transit-gateway-id $TGW_ID \
  --vpc-id $VPC_ID \
  --subnet-ids $PRIVATE_SUBNET_1A $PRIVATE_SUBNET_1C

# ルートテーブル関連付け
aws ec2 associate-transit-gateway-route-table \
  --transit-gateway-attachment-id $TGW_ATTACHMENT_ID \
  --transit-gateway-route-table-id $PROD_RT_ID

# 静的ルート追加
aws ec2 create-transit-gateway-route \
  --route-table-id $PROD_RT_ID \
  --destination-cidr-block 10.1.0.0/16 \
  --transit-gateway-attachment-id $BRANCH_ATTACHMENT_ID
```

**Phase 4: 冗長化とフェイルオーバー**

1. **Multi-AZ 設計**
```bash
# Application Load Balancer (Multi-AZ)
aws elbv2 create-load-balancer \
  --name enterprise-alb \
  --subnets $PUBLIC_SUBNET_1A $PUBLIC_SUBNET_1C \
  --security-groups $ALB_SG_ID \
  --scheme internet-facing \
  --type application

# Auto Scaling Group (Multi-AZ)
aws autoscaling create-auto-scaling-group \
  --auto-scaling-group-name enterprise-asg \
  --launch-template 'LaunchTemplateId=lt-xxx,Version=1' \
  --min-size 2 \
  --max-size 10 \
  --desired-capacity 4 \
  --vpc-zone-identifier "$PRIVATE_SUBNET_1A,$PRIVATE_SUBNET_1C"
```

2. **Database 冗長化**
```bash
# RDS Multi-AZ
aws rds create-db-instance \
  --db-instance-identifier enterprise-db \
  --db-instance-class db.r5.xlarge \
  --engine mysql \
  --master-username admin \
  --master-user-password SecurePassword123! \
  --allocated-storage 100 \
  --vpc-security-group-ids $DB_SG_ID \
  --db-subnet-group-name enterprise-db-subnet-group \
  --multi-az \
  --backup-retention-period 30

# Read Replica (別リージョン)
aws rds create-db-instance-read-replica \
  --db-instance-identifier enterprise-db-replica \
  --source-db-instance-identifier enterprise-db \
  --db-instance-class db.r5.large
```

**Phase 5: 監視とアラート**

1. **CloudWatch 設定**
```bash
# VPC Flow Logs
aws ec2 create-flow-logs \
  --resource-type VPC \
  --resource-ids $VPC_ID \
  --traffic-type ALL \
  --log-destination-type cloud-watch-logs \
  --log-group-name /aws/vpc/flowlogs \
  --deliver-logs-permission-arn $FLOW_LOGS_ROLE_ARN

# Transit Gateway メトリクス
aws logs create-log-group --log-group-name /aws/transitgateway/flowlogs
```

2. **カスタムメトリクス**
```python
# Python スクリプト例
import boto3
import json

def lambda_handler(event, context):
    ec2 = boto3.client('ec2')
    cloudwatch = boto3.client('cloudwatch')
    
    # Transit Gateway の使用量監視
    response = ec2.describe_transit_gateway_attachments()
    
    for attachment in response['TransitGatewayAttachments']:
        if attachment['State'] == 'available':
            cloudwatch.put_metric_data(
                Namespace='Custom/TransitGateway',
                MetricData=[
                    {
                        'MetricName': 'ActiveAttachments',
                        'Value': 1,
                        'Unit': 'Count',
                        'Dimensions': [
                            {
                                'Name': 'TransitGatewayId',
                                'Value': attachment['TransitGatewayId']
                            }
                        ]
                    }
                ]
            )
```

**使用サービス**: VPC, Transit Gateway, Route 53, AWS Organizations, CloudWatch, Lambda

### Lab 1-2: ハイブリッドクラウド接続設計

**学習目標**: オンプレミスとクラウドの統合設計

**シナリオ**: 
既存のオンプレミスデータセンターとAWSクラウドを統合

#### 詳細な環境要件
- **オンプレミス**: 東京データセンター、大阪データセンター
- **AS番号**: オンプレミス 65001、AWS 65000
- **帯域要件**: 本番 10Gbps、開発 1Gbps
- **レイテンシ要件**: < 5ms (東京), < 10ms (大阪)
- **可用性要件**: 99.99%

#### Phase 1: 接続方式の詳細分析

**1. Direct Connect vs VPN 比較分析**

| 項目 | Direct Connect | Site-to-Site VPN | Direct Connect + VPN |
|------|----------------|------------------|-----------------------|
| 帯域幅 | 1Gbps-100Gbps | 1.25Gbps (max) | Primary/Backup |
| レイテンシ | 一定 | 変動あり | 一定 |
| 可用性 | 99.9% | 99.95% | 99.99% |
| 月額コスト | $2,000-$10,000 | $50-$200 | $2,050-$10,200 |
| セットアップ時間 | 2-4週間 | 即時 | 2-4週間 |

**2. 推奨アーキテクチャ**
```
東京DC ──── Direct Connect (Primary) ──── AWS Tokyo
  │                                         │
  └──── Site-to-Site VPN (Backup) ─────────┘

大阪DC ──── Site-to-Site VPN ──── AWS Osaka
```

#### Phase 2: Direct Connect 実装

**1. Direct Connect Gateway 設計**
```bash
# Direct Connect Gateway 作成
aws directconnect create-direct-connect-gateway \
  --name "Enterprise-DXGW" \
  --amazon-side-asn 64512

# Virtual Interface 作成
aws directconnect create-private-virtual-interface \
  --connection-id dxcon-xxxxxxxx \
  --new-private-virtual-interface '{
    "virtualInterfaceName": "Enterprise-VIF",
    "vlan": 100,
    "asn": 65001,
    "mtu": 9000,
    "authKey": "BGP-Auth-Key-123",
    "customerAddress": "192.168.1.1/30",
    "amazonAddress": "192.168.1.2/30",
    "addressFamily": "ipv4",
    "directConnectGatewayId": "dxgw-xxxxxxxx"
  }'
```

**2. BGP 設定詳細**

**オンプレミス側 (Cisco ASR 例)**
```cisco
! BGP 設定
router bgp 65001
 bgp router-id 192.168.1.1
 bgp log-neighbor-changes
 neighbor 192.168.1.2 remote-as 64512
 neighbor 192.168.1.2 password BGP-Auth-Key-123
 neighbor 192.168.1.2 soft-reconfiguration inbound
 neighbor 192.168.1.2 route-map AWS-IN in
 neighbor 192.168.1.2 route-map AWS-OUT out
 !
 address-family ipv4
  neighbor 192.168.1.2 activate
  network 172.16.0.0 mask 255.255.0.0
  network 172.17.0.0 mask 255.255.0.0
 exit-address-family
!
! Route Maps
route-map AWS-OUT permit 10
 match ip address prefix-list ON-PREM-NETWORKS
 set local-preference 200
 set med 100
!
route-map AWS-IN permit 10
 match ip address prefix-list AWS-NETWORKS
 set local-preference 150
!
! Prefix Lists
ip prefix-list ON-PREM-NETWORKS permit 172.16.0.0/16
ip prefix-list ON-PREM-NETWORKS permit 172.17.0.0/16
ip prefix-list AWS-NETWORKS permit 10.0.0.0/8
```

**3. AWS側 Transit Gateway 統合**
```bash
# Transit Gateway と Direct Connect Gateway の関連付け
aws ec2 create-transit-gateway-direct-connect-gateway-attachment \
  --transit-gateway-id $TGW_ID \
  --direct-connect-gateway-id $DXGW_ID \
  --tag-specifications 'ResourceType=transit-gateway-attachment,Tags=[{Key=Name,Value=DX-Attachment}]'

# ルーティング設定
aws ec2 create-transit-gateway-route \
  --route-table-id $TGW_RT_ID \
  --destination-cidr-block 172.16.0.0/16 \
  --transit-gateway-attachment-id $DX_ATTACHMENT_ID
```

#### Phase 3: VPN バックアップ設定

**1. Customer Gateway 設定**
```bash
# Customer Gateway 作成
aws ec2 create-customer-gateway \
  --type ipsec.1 \
  --public-ip 203.0.113.1 \
  --bgp-asn 65001 \
  --tag-specifications 'ResourceType=customer-gateway,Tags=[{Key=Name,Value=Tokyo-CGW}]'

# VPN Gateway 作成
aws ec2 create-vpn-gateway \
  --type ipsec.1 \
  --amazon-side-asn 64512

# VPN Connection 作成
aws ec2 create-vpn-connection \
  --type ipsec.1 \
  --customer-gateway-id $CGW_ID \
  --vpn-gateway-id $VGW_ID \
  --options StaticRoutesOnly=false
```

**2. 冗長化設定**
```bash
# 複数トンネルの設定
aws ec2 describe-vpn-connections --vpn-connection-ids $VPN_ID

# BGP セッション確認
aws ec2 describe-vpn-connections \
  --vpn-connection-ids $VPN_ID \
  --query 'VpnConnections[0].BgpAsn'
```

#### Phase 4: 高度なルーティング制御

**1. AS Path Prepending**
```cisco
! VPN 経由のルートを Direct Connect より優先度を下げる
route-map VPN-OUT permit 10
 match ip address prefix-list ON-PREM-NETWORKS
 set as-path prepend 65001 65001 65001
 set local-preference 100
```

**2. MED 値による制御**
```cisco
! Direct Connect 経由を優先
route-map DX-OUT permit 10
 match ip address prefix-list ON-PREM-NETWORKS
 set med 50
 set local-preference 200
```

#### Phase 5: 監視とトラブルシューティング

**1. CloudWatch メトリクス**
```python
# Lambda 関数でカスタムメトリクス
import boto3
import json

def lambda_handler(event, context):
    dx_client = boto3.client('directconnect')
    cloudwatch = boto3.client('cloudwatch')
    
    # Virtual Interface 状態監視
    vifs = dx_client.describe_virtual_interfaces()
    
    for vif in vifs['virtualInterfaces']:
        state = 1 if vif['virtualInterfaceState'] == 'available' else 0
        
        cloudwatch.put_metric_data(
            Namespace='Custom/DirectConnect',
            MetricData=[
                {
                    'MetricName': 'VirtualInterfaceState',
                    'Value': state,
                    'Unit': 'Count',
                    'Dimensions': [
                        {'Name': 'VirtualInterfaceId', 'Value': vif['virtualInterfaceId']}
                    ]
                }
            ]
        )

# BGP セッション監視
def monitor_bgp_sessions():
    ec2 = boto3.client('ec2')
    
    vpn_connections = ec2.describe_vpn_connections()
    
    for vpn in vpn_connections['VpnConnections']:
        for tunnel in vpn['VgwTelemetry']:
            status = 1 if tunnel['Status'] == 'UP' else 0
            
            cloudwatch.put_metric_data(
                Namespace='Custom/VPN',
                MetricData=[
                    {
                        'MetricName': 'TunnelState',
                        'Value': status,
                        'Unit': 'Count',
                        'Dimensions': [
                            {'Name': 'VpnConnectionId', 'Value': vpn['VpnConnectionId']},
                            {'Name': 'TunnelIpAddress', 'Value': tunnel['OutsideIpAddress']}
                        ]
                    }
                ]
            )
```

**2. 自動フェイルオーバー**
```python
# EventBridge と Lambda による自動フェイルオーバー
def handle_dx_failure(event, context):
    if event['detail']['state'] == 'down':
        # VPN 経由にトラフィックを切り替え
        ec2 = boto3.client('ec2')
        
        # ルートテーブル更新
        ec2.replace_route(
            RouteTableId='rtb-xxxxxxxx',
            DestinationCidrBlock='172.16.0.0/16',
            VpnConnectionId='vpn-xxxxxxxx'
        )
        
        # SNS 通知
        sns = boto3.client('sns')
        sns.publish(
            TopicArn='arn:aws:sns:ap-northeast-1:123456789012:network-alerts',
            Message='Direct Connect failure detected. Traffic switched to VPN backup.',
            Subject='Network Failover Alert'
        )
```

#### Phase 6: DNS 解決とルーティング

**1. Route 53 Resolver 設定**
```bash
# Resolver Endpoint 作成
aws route53resolver create-resolver-endpoint \
  --creator-request-id $(date +%s) \
  --security-group-ids sg-xxxxxxxx \
  --direction INBOUND \
  --ip-addresses 'SubnetId=subnet-xxxxxxxx,Ip=10.0.100.10' 'SubnetId=subnet-yyyyyyyy,Ip=10.0.101.10'

# Resolver Rule 作成
aws route53resolver create-resolver-rule \
  --creator-request-id $(date +%s) \
  --rule-type FORWARD \
  --domain-name corp.example.com \
  --resolver-endpoint-id rslvr-in-xxxxxxxx \
  --target-ips 'Ip=172.16.1.10,Port=53' 'Ip=172.16.1.11,Port=53'
```

**使用サービス**: Direct Connect, VPN, BGP, Route 53 Resolver, Transit Gateway, EventBridge, Lambda

---

## Domain 2: Network Implementation (26%)

### Lab 2-1: Transit Gateway を使用したハブ&スポーク構成

**学習目標**: 複雑なネットワーク接続の実装

**実習手順**:

#### Step 1: 環境準備
```bash
# VPC 作成
aws ec2 create-vpc --cidr-block 10.0.0.0/16 --tag-specifications 'ResourceType=vpc,Tags=[{Key=Name,Value=Hub-VPC}]'

# サブネット作成 (複数AZ)
aws ec2 create-subnet --vpc-id vpc-xxx --cidr-block 10.0.1.0/24 --availability-zone ap-northeast-1a
aws ec2 create-subnet --vpc-id vpc-xxx --cidr-block 10.0.2.0/24 --availability-zone ap-northeast-1c
```

#### Step 2: Transit Gateway 設定
```bash
# Transit Gateway 作成
aws ec2 create-transit-gateway --description "Hub-and-Spoke TGW" --options=AmazonSideAsn=64512,AutoAcceptSharedAttachments=enable,DefaultRouteTableAssociation=enable
```

#### Step 3: ルーティング設定
```bash
# ルートテーブル作成と設定
aws ec2 create-route-table --vpc-id vpc-xxx
aws ec2 create-route --route-table-id rtb-xxx --destination-cidr-block 0.0.0.0/0 --transit-gateway-id tgw-xxx
```

### Lab 2-2: Direct Connect ゲートウェイ実装

**学習目標**: 専用線接続の実装と設定

**実習内容**:
1. Virtual Interface (VIF) 設定
2. BGP セッション確立
3. ルーティング優先度設定
4. 冗長化設定

---

## Domain 3: Network Management and Operation (20%)

### Lab 3-1: CloudWatch を使用したネットワーク監視

**学習目標**: ネットワークパフォーマンスの監視と最適化

**実習内容**:
1. VPC Flow Logs の設定と分析
2. CloudWatch メトリクスの設定
3. カスタムダッシュボード作成
4. アラート設定

**実習手順**:

#### Step 1: VPC Flow Logs 有効化
```bash
# Flow Logs 作成
aws ec2 create-flow-logs \
  --resource-type VPC \
  --resource-ids vpc-xxx \
  --traffic-type ALL \
  --log-destination-type cloud-watch-logs \
  --log-group-name VPCFlowLogs
```

#### Step 2: CloudWatch ダッシュボード作成
```json
{
  "widgets": [
    {
      "type": "metric",
      "properties": {
        "metrics": [
          ["AWS/VPC", "PacketsDropped", "VpcId", "vpc-xxx"],
          ["AWS/VPC", "BytesIn", "VpcId", "vpc-xxx"],
          ["AWS/VPC", "BytesOut", "VpcId", "vpc-xxx"]
        ],
        "period": 300,
        "stat": "Sum",
        "region": "ap-northeast-1",
        "title": "VPC Network Metrics"
      }
    }
  ]
}
```

### Lab 3-2: Network Automation with AWS CLI/SDK

**学習目標**: ネットワーク運用の自動化

**実習内容**:
1. Python SDK を使用したネットワーク設定自動化
2. CloudFormation テンプレート作成
3. 障害時の自動復旧スクリプト

---

## Domain 4: Network Security, Compliance, and Governance (24%)

### Lab 4-1: セキュリティグループとNACLの最適化

**学習目標**: ネットワークセキュリティの階層化

**実習内容**:
1. 最小権限の原則に基づくセキュリティグループ設計
2. NACL によるサブネットレベル制御
3. AWS WAF との統合
4. VPC Endpoint セキュリティ

**実習手順**:

#### Step 1: セキュリティグループ作成
```bash
# Web tier セキュリティグループ
aws ec2 create-security-group \
  --group-name web-tier-sg \
  --description "Web tier security group" \
  --vpc-id vpc-xxx

# ルール追加
aws ec2 authorize-security-group-ingress \
  --group-id sg-xxx \
  --protocol tcp \
  --port 80 \
  --cidr 0.0.0.0/0
```

#### Step 2: NACL 設定
```bash
# NACL 作成
aws ec2 create-network-acl --vpc-id vpc-xxx

# インバウンドルール
aws ec2 create-network-acl-entry \
  --network-acl-id acl-xxx \
  --rule-number 100 \
  --protocol tcp \
  --port-range From=80,To=80 \
  --cidr-block 0.0.0.0/0
```

### Lab 4-2: AWS WAF と Shield による DDoS 対策

**学習目標**: アプリケーションレイヤーの保護

**実習内容**:
1. AWS WAF ルール作成
2. Rate limiting 設定
3. Geographic blocking
4. AWS Shield Advanced 設定

---

## 実践シナリオ

### シナリオ 1: 金融機関のマルチリージョン展開

**要件**:
- 東京とオレゴンリージョンでの冗長化
- 超低レイテンシ要件 (< 10ms)
- 高可用性 (99.99%)
- 厳格なセキュリティ要件

**実装課題**:
1. リージョン間接続最適化
2. DNS フェイルオーバー設定
3. 暗号化通信の実装
4. コンプライアンス要件への対応

### シナリオ 2: グローバル e-commerce プラットフォーム

**要件**:
- 世界5リージョンでの展開
- CDN 統合
- 動的なトラフィック分散
- コスト最適化

**実装課題**:
1. CloudFront 統合設計
2. Global Load Balancer 設定
3. 地理的ルーティング
4. 帯域幅コスト最適化

---

## 検証とトラブルシューティング

### 一般的な問題と解決策

#### 1. 接続性の問題
```bash
# 接続テスト
aws ec2 describe-route-tables --route-table-ids rtb-xxx
aws ec2 describe-security-groups --group-ids sg-xxx

# トレースルート相当
aws ec2 describe-vpc-peering-connections
aws ec2 describe-transit-gateway-route-tables
```

#### 2. パフォーマンス問題
```bash
# メトリクス確認
aws cloudwatch get-metric-statistics \
  --namespace AWS/EC2 \
  --metric-name NetworkIn \
  --dimensions Name=InstanceId,Value=i-xxx \
  --start-time 2024-01-01T00:00:00Z \
  --end-time 2024-01-01T23:59:59Z \
  --period 3600 \
  --statistics Average
```

#### 3. セキュリティ問題
```bash
# VPC Flow Logs 分析
aws logs filter-log-events \
  --log-group-name VPCFlowLogs \
  --filter-pattern "{ $.action = \"REJECT\" }"
```

---

## 試験対策のポイント

### 重要な覚えておくべき数値
- VPC CIDR: /16 - /28
- Direct Connect: 1Gbps, 10Gbps, 100Gbps
- Transit Gateway: 帯域幅上限 50Gbps
- VPC Peering: 単一 AZ 間 10Gbps

### よく出る設定パターン
1. ハブ&スポークトポロジー
2. フルメッシュ接続
3. 階層化セキュリティ
4. 冗長化パターン

### 試験本番での注意点
1. 最小権限の原則
2. コスト効率
3. 運用性
4. スケーラビリティ

---

## 参考資料

- [AWS VPC ユーザーガイド](https://docs.aws.amazon.com/vpc/)
- [AWS Transit Gateway ガイド](https://docs.aws.amazon.com/transit-gateway/)
- [AWS Direct Connect ユーザーガイド](https://docs.aws.amazon.com/directconnect/)
- [AWS セキュリティベストプラクティス](https://docs.aws.amazon.com/security/)

---

## まとめ

この教材を通じて、AWS Advanced Networking Specialty 試験に必要な実践的スキルを習得できます。各ラボを順序立てて実施し、理解を深めながら進めてください。

実際の試験では、設計判断の根拠や最適化のポイントが重要になります。各シナリオで「なぜその設計を選択したか」を説明できるよう準備しましょう。