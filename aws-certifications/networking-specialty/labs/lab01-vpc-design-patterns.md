# Lab 1: VPC設計パターンとマルチ層アーキテクチャ

## 🎯 学習目標

このラボでは、企業レベルのVPC設計パターンを実装し、マルチ層アーキテクチャのベストプラクティスを習得します。

**習得スキル**:
- VPC設計パターンの実装
- マルチ層アーキテクチャの構築
- セキュリティグループの詳細設定
- ルーティングテーブルの最適化

**所要時間**: 4-6時間  
**推定コスト**: $15-25

## 📋 シナリオ

**企業**: 金融サービス企業  
**要件**:
- 高いセキュリティ要件（PCI DSS準拠）
- マルチAZ構成での可用性確保
- DMZを含む3層アーキテクチャ
- 本番・ステージング環境の分離

## Phase 1: 基盤VPC設計と実装

### 1.1 VPC基盤作成

```bash
#!/bin/bash
# スクリプト: create-vpc-foundation.sh

set -e

echo "=== VPC基盤作成開始 ==="

# 変数定義
REGION="ap-northeast-1"
VPC_CIDR="10.0.0.0/16"
ENVIRONMENT="production"

# VPC作成
VPC_ID=$(aws ec2 create-vpc \
    --cidr-block $VPC_CIDR \
    --tag-specifications "ResourceType=vpc,Tags=[{Key=Name,Value=${ENVIRONMENT}-vpc},{Key=Environment,Value=${ENVIRONMENT}}]" \
    --query 'Vpc.VpcId' \
    --output text \
    --region $REGION)

echo "✅ VPC作成完了: $VPC_ID"

# DNS解決とDNSホスト名を有効化
aws ec2 modify-vpc-attribute --vpc-id $VPC_ID --enable-dns-support
aws ec2 modify-vpc-attribute --vpc-id $VPC_ID --enable-dns-hostnames

# Internet Gateway作成
IGW_ID=$(aws ec2 create-internet-gateway \
    --tag-specifications "ResourceType=internet-gateway,Tags=[{Key=Name,Value=${ENVIRONMENT}-igw}]" \
    --query 'InternetGateway.InternetGatewayId' \
    --output text \
    --region $REGION)

echo "✅ Internet Gateway作成完了: $IGW_ID"

# Internet GatewayをVPCにアタッチ
aws ec2 attach-internet-gateway \
    --internet-gateway-id $IGW_ID \
    --vpc-id $VPC_ID \
    --region $REGION

echo "✅ Internet Gateway アタッチ完了"

# 変数をファイルに保存（後続スクリプトで使用）
cat > vpc-vars.sh << EOF
export VPC_ID=$VPC_ID
export IGW_ID=$IGW_ID
export REGION=$REGION
export ENVIRONMENT=$ENVIRONMENT
EOF

echo "🎉 VPC基盤作成完了"
echo "   VPC ID: $VPC_ID"
echo "   IGW ID: $IGW_ID"
```

### 1.2 サブネット設計と実装

```bash
#!/bin/bash
# スクリプト: create-subnets.sh

source vpc-vars.sh
set -e

echo "=== サブネット作成開始 ==="

# AZ取得
AZ1=$(aws ec2 describe-availability-zones --query 'AvailabilityZones[0].ZoneName' --output text --region $REGION)
AZ2=$(aws ec2 describe-availability-zones --query 'AvailabilityZones[1].ZoneName' --output text --region $REGION)

echo "使用AZ: $AZ1, $AZ2"

# パブリックサブネット (DMZ層)
PUBLIC_SUBNET_1=$(aws ec2 create-subnet \
    --vpc-id $VPC_ID \
    --cidr-block 10.0.1.0/24 \
    --availability-zone $AZ1 \
    --tag-specifications "ResourceType=subnet,Tags=[{Key=Name,Value=${ENVIRONMENT}-public-subnet-1},{Key=Type,Value=Public},{Key=Layer,Value=DMZ}]" \
    --query 'Subnet.SubnetId' \
    --output text \
    --region $REGION)

PUBLIC_SUBNET_2=$(aws ec2 create-subnet \
    --vpc-id $VPC_ID \
    --cidr-block 10.0.2.0/24 \
    --availability-zone $AZ2 \
    --tag-specifications "ResourceType=subnet,Tags=[{Key=Name,Value=${ENVIRONMENT}-public-subnet-2},{Key=Type,Value=Public},{Key=Layer,Value=DMZ}]" \
    --query 'Subnet.SubnetId' \
    --output text \
    --region $REGION)

# プライベートサブネット (アプリケーション層)
PRIVATE_SUBNET_1=$(aws ec2 create-subnet \
    --vpc-id $VPC_ID \
    --cidr-block 10.0.11.0/24 \
    --availability-zone $AZ1 \
    --tag-specifications "ResourceType=subnet,Tags=[{Key=Name,Value=${ENVIRONMENT}-private-subnet-1},{Key=Type,Value=Private},{Key=Layer,Value=Application}]" \
    --query 'Subnet.SubnetId' \
    --output text \
    --region $REGION)

PRIVATE_SUBNET_2=$(aws ec2 create-subnet \
    --vpc-id $VPC_ID \
    --cidr-block 10.0.12.0/24 \
    --availability-zone $AZ2 \
    --tag-specifications "ResourceType=subnet,Tags=[{Key=Name,Value=${ENVIRONMENT}-private-subnet-2},{Key=Type,Value=Private},{Key=Layer,Value=Application}]" \
    --query 'Subnet.SubnetId' \
    --output text \
    --region $REGION)

# データベースサブネット (データ層)
DB_SUBNET_1=$(aws ec2 create-subnet \
    --vpc-id $VPC_ID \
    --cidr-block 10.0.21.0/24 \
    --availability-zone $AZ1 \
    --tag-specifications "ResourceType=subnet,Tags=[{Key=Name,Value=${ENVIRONMENT}-db-subnet-1},{Key=Type,Value=Database},{Key=Layer,Value=Data}]" \
    --query 'Subnet.SubnetId' \
    --output text \
    --region $REGION)

DB_SUBNET_2=$(aws ec2 create-subnet \
    --vpc-id $VPC_ID \
    --cidr-block 10.0.22.0/24 \
    --availability-zone $AZ2 \
    --tag-specifications "ResourceType=subnet,Tags=[{Key=Name,Value=${ENVIRONMENT}-db-subnet-2},{Key=Type,Value=Database},{Key=Layer,Value=Data}]" \
    --query 'Subnet.SubnetId' \
    --output text \
    --region $REGION)

# パブリックサブネットで自動IP割り当て有効化
aws ec2 modify-subnet-attribute --subnet-id $PUBLIC_SUBNET_1 --map-public-ip-on-launch
aws ec2 modify-subnet-attribute --subnet-id $PUBLIC_SUBNET_2 --map-public-ip-on-launch

# 変数を更新
cat >> vpc-vars.sh << EOF
export PUBLIC_SUBNET_1=$PUBLIC_SUBNET_1
export PUBLIC_SUBNET_2=$PUBLIC_SUBNET_2
export PRIVATE_SUBNET_1=$PRIVATE_SUBNET_1
export PRIVATE_SUBNET_2=$PRIVATE_SUBNET_2
export DB_SUBNET_1=$DB_SUBNET_1
export DB_SUBNET_2=$DB_SUBNET_2
EOF

echo "✅ サブネット作成完了"
echo "   パブリック: $PUBLIC_SUBNET_1, $PUBLIC_SUBNET_2"
echo "   プライベート: $PRIVATE_SUBNET_1, $PRIVATE_SUBNET_2"
echo "   データベース: $DB_SUBNET_1, $DB_SUBNET_2"
```

### 1.3 NAT Gateway設定

```bash
#!/bin/bash
# スクリプト: create-nat-gateways.sh

source vpc-vars.sh
set -e

echo "=== NAT Gateway作成開始 ==="

# Elastic IP作成
EIP_1=$(aws ec2 allocate-address \
    --domain vpc \
    --tag-specifications "ResourceType=elastic-ip,Tags=[{Key=Name,Value=${ENVIRONMENT}-nat-eip-1}]" \
    --query 'AllocationId' \
    --output text \
    --region $REGION)

EIP_2=$(aws ec2 allocate-address \
    --domain vpc \
    --tag-specifications "ResourceType=elastic-ip,Tags=[{Key=Name,Value=${ENVIRONMENT}-nat-eip-2}]" \
    --query 'AllocationId' \
    --output text \
    --region $REGION)

echo "✅ Elastic IP作成完了: $EIP_1, $EIP_2"

# NAT Gateway作成
NAT_GW_1=$(aws ec2 create-nat-gateway \
    --subnet-id $PUBLIC_SUBNET_1 \
    --allocation-id $EIP_1 \
    --tag-specifications "ResourceType=nat-gateway,Tags=[{Key=Name,Value=${ENVIRONMENT}-nat-gw-1}]" \
    --query 'NatGateway.NatGatewayId' \
    --output text \
    --region $REGION)

NAT_GW_2=$(aws ec2 create-nat-gateway \
    --subnet-id $PUBLIC_SUBNET_2 \
    --allocation-id $EIP_2 \
    --tag-specifications "ResourceType=nat-gateway,Tags=[{Key=Name,Value=${ENVIRONMENT}-nat-gw-2}]" \
    --query 'NatGateway.NatGatewayId' \
    --output text \
    --region $REGION)

echo "✅ NAT Gateway作成完了: $NAT_GW_1, $NAT_GW_2"
echo "   作成状況確認中..."

# NAT Gateway作成完了まで待機
aws ec2 wait nat-gateway-available --nat-gateway-ids $NAT_GW_1 --region $REGION
aws ec2 wait nat-gateway-available --nat-gateway-ids $NAT_GW_2 --region $REGION

# 変数を更新
cat >> vpc-vars.sh << EOF
export EIP_1=$EIP_1
export EIP_2=$EIP_2
export NAT_GW_1=$NAT_GW_1
export NAT_GW_2=$NAT_GW_2
EOF

echo "🎉 NAT Gateway設定完了"
```

## Phase 2: ルーティング設定

### 2.1 ルートテーブル作成と設定

```bash
#!/bin/bash
# スクリプト: configure-routing.sh

source vpc-vars.sh
set -e

echo "=== ルーティング設定開始 ==="

# パブリックルートテーブル作成
PUBLIC_RT=$(aws ec2 create-route-table \
    --vpc-id $VPC_ID \
    --tag-specifications "ResourceType=route-table,Tags=[{Key=Name,Value=${ENVIRONMENT}-public-rt}]" \
    --query 'RouteTable.RouteTableId' \
    --output text \
    --region $REGION)

# プライベートルートテーブル作成
PRIVATE_RT_1=$(aws ec2 create-route-table \
    --vpc-id $VPC_ID \
    --tag-specifications "ResourceType=route-table,Tags=[{Key=Name,Value=${ENVIRONMENT}-private-rt-1}]" \
    --query 'RouteTable.RouteTableId' \
    --output text \
    --region $REGION)

PRIVATE_RT_2=$(aws ec2 create-route-table \
    --vpc-id $VPC_ID \
    --tag-specifications "ResourceType=route-table,Tags=[{Key=Name,Value=${ENVIRONMENT}-private-rt-2}]" \
    --query 'RouteTable.RouteTableId' \
    --output text \
    --region $REGION)

# データベースルートテーブル作成
DB_RT=$(aws ec2 create-route-table \
    --vpc-id $VPC_ID \
    --tag-specifications "ResourceType=route-table,Tags=[{Key=Name,Value=${ENVIRONMENT}-db-rt}]" \
    --query 'RouteTable.RouteTableId' \
    --output text \
    --region $REGION)

echo "✅ ルートテーブル作成完了"

# パブリックルートテーブルにインターネットゲートウェイルート追加
aws ec2 create-route \
    --route-table-id $PUBLIC_RT \
    --destination-cidr-block 0.0.0.0/0 \
    --gateway-id $IGW_ID \
    --region $REGION

# プライベートルートテーブルにNATゲートウェイルート追加
aws ec2 create-route \
    --route-table-id $PRIVATE_RT_1 \
    --destination-cidr-block 0.0.0.0/0 \
    --nat-gateway-id $NAT_GW_1 \
    --region $REGION

aws ec2 create-route \
    --route-table-id $PRIVATE_RT_2 \
    --destination-cidr-block 0.0.0.0/0 \
    --nat-gateway-id $NAT_GW_2 \
    --region $REGION

echo "✅ ルート設定完了"

# サブネット関連付け
aws ec2 associate-route-table --subnet-id $PUBLIC_SUBNET_1 --route-table-id $PUBLIC_RT --region $REGION
aws ec2 associate-route-table --subnet-id $PUBLIC_SUBNET_2 --route-table-id $PUBLIC_RT --region $REGION

aws ec2 associate-route-table --subnet-id $PRIVATE_SUBNET_1 --route-table-id $PRIVATE_RT_1 --region $REGION
aws ec2 associate-route-table --subnet-id $PRIVATE_SUBNET_2 --route-table-id $PRIVATE_RT_2 --region $REGION

aws ec2 associate-route-table --subnet-id $DB_SUBNET_1 --route-table-id $DB_RT --region $REGION
aws ec2 associate-route-table --subnet-id $DB_SUBNET_2 --route-table-id $DB_RT --region $REGION

# 変数を更新
cat >> vpc-vars.sh << EOF
export PUBLIC_RT=$PUBLIC_RT
export PRIVATE_RT_1=$PRIVATE_RT_1
export PRIVATE_RT_2=$PRIVATE_RT_2
export DB_RT=$DB_RT
EOF

echo "🎉 ルーティング設定完了"
```

## Phase 3: セキュリティグループ設計

### 3.1 セキュリティグループ作成

```bash
#!/bin/bash
# スクリプト: create-security-groups.sh

source vpc-vars.sh
set -e

echo "=== セキュリティグループ作成開始 ==="

# ウェブ層セキュリティグループ
WEB_SG=$(aws ec2 create-security-group \
    --group-name "${ENVIRONMENT}-web-sg" \
    --description "Security group for web servers" \
    --vpc-id $VPC_ID \
    --tag-specifications "ResourceType=security-group,Tags=[{Key=Name,Value=${ENVIRONMENT}-web-sg},{Key=Layer,Value=Web}]" \
    --query 'GroupId' \
    --output text \
    --region $REGION)

# アプリケーション層セキュリティグループ
APP_SG=$(aws ec2 create-security-group \
    --group-name "${ENVIRONMENT}-app-sg" \
    --description "Security group for application servers" \
    --vpc-id $VPC_ID \
    --tag-specifications "ResourceType=security-group,Tags=[{Key=Name,Value=${ENVIRONMENT}-app-sg},{Key=Layer,Value=Application}]" \
    --query 'GroupId' \
    --output text \
    --region $REGION)

# データベース層セキュリティグループ
DB_SG=$(aws ec2 create-security-group \
    --group-name "${ENVIRONMENT}-db-sg" \
    --description "Security group for database servers" \
    --vpc-id $VPC_ID \
    --tag-specifications "ResourceType=security-group,Tags=[{Key=Name,Value=${ENVIRONMENT}-db-sg},{Key=Layer,Value=Database}]" \
    --query 'GroupId' \
    --output text \
    --region $REGION)

# 管理用セキュリティグループ
MGMT_SG=$(aws ec2 create-security-group \
    --group-name "${ENVIRONMENT}-mgmt-sg" \
    --description "Security group for management access" \
    --vpc-id $VPC_ID \
    --tag-specifications "ResourceType=security-group,Tags=[{Key=Name,Value=${ENVIRONMENT}-mgmt-sg},{Key=Layer,Value=Management}]" \
    --query 'GroupId' \
    --output text \
    --region $REGION)

echo "✅ セキュリティグループ作成完了"

# ウェブ層ルール設定
aws ec2 authorize-security-group-ingress \
    --group-id $WEB_SG \
    --protocol tcp \
    --port 80 \
    --cidr 0.0.0.0/0 \
    --region $REGION

aws ec2 authorize-security-group-ingress \
    --group-id $WEB_SG \
    --protocol tcp \
    --port 443 \
    --cidr 0.0.0.0/0 \
    --region $REGION

# SSH管理アクセス (管理SGからのみ)
aws ec2 authorize-security-group-ingress \
    --group-id $WEB_SG \
    --protocol tcp \
    --port 22 \
    --source-group $MGMT_SG \
    --region $REGION

# アプリケーション層ルール設定
aws ec2 authorize-security-group-ingress \
    --group-id $APP_SG \
    --protocol tcp \
    --port 8080 \
    --source-group $WEB_SG \
    --region $REGION

aws ec2 authorize-security-group-ingress \
    --group-id $APP_SG \
    --protocol tcp \
    --port 22 \
    --source-group $MGMT_SG \
    --region $REGION

# データベース層ルール設定
aws ec2 authorize-security-group-ingress \
    --group-id $DB_SG \
    --protocol tcp \
    --port 3306 \
    --source-group $APP_SG \
    --region $REGION

# 管理層ルール設定（会社IPアドレスから）
COMPANY_IP="203.0.113.0/24"  # 実際の会社IPに変更
aws ec2 authorize-security-group-ingress \
    --group-id $MGMT_SG \
    --protocol tcp \
    --port 22 \
    --cidr $COMPANY_IP \
    --region $REGION

# 変数を更新
cat >> vpc-vars.sh << EOF
export WEB_SG=$WEB_SG
export APP_SG=$APP_SG
export DB_SG=$DB_SG
export MGMT_SG=$MGMT_SG
EOF

echo "🎉 セキュリティグループ設定完了"
```

## Phase 4: 検証とテスト

### 4.1 ネットワーク接続性テスト

```python
#!/usr/bin/env python3
# スクリプト: network-connectivity-test.py

import boto3
import subprocess
import os
import time

def test_vpc_connectivity():
    """
    VPC接続性テストの実行
    """
    # 環境変数読み込み
    vpc_id = os.environ.get('VPC_ID')
    region = os.environ.get('REGION', 'ap-northeast-1')
    
    print("=== VPCネットワーク接続性テスト開始 ===")
    
    ec2 = boto3.client('ec2', region_name=region)
    
    # VPC情報取得
    vpc_info = ec2.describe_vpcs(VpcIds=[vpc_id])
    print(f"🔍 テスト対象VPC: {vpc_id}")
    print(f"   CIDR: {vpc_info['Vpcs'][0]['CidrBlock']}")
    
    # サブネット情報取得
    subnets = ec2.describe_subnets(
        Filters=[{'Name': 'vpc-id', 'Values': [vpc_id]}]
    )
    
    print(f"\n📊 サブネット一覧:")
    for subnet in subnets['Subnets']:
        subnet_name = next((tag['Value'] for tag in subnet.get('Tags', []) if tag['Key'] == 'Name'), 'N/A')
        print(f"   {subnet_name}: {subnet['SubnetId']} ({subnet['CidrBlock']})")
    
    # ルートテーブル検証
    print(f"\n🛣️  ルートテーブル検証:")
    route_tables = ec2.describe_route_tables(
        Filters=[{'Name': 'vpc-id', 'Values': [vpc_id]}]
    )
    
    for rt in route_tables['RouteTables']:
        rt_name = next((tag['Value'] for tag in rt.get('Tags', []) if tag['Key'] == 'Name'), 'Main')
        print(f"   {rt_name} ({rt['RouteTableId']}):")
        
        for route in rt['Routes']:
            destination = route.get('DestinationCidrBlock', route.get('DestinationIpv6CidrBlock', 'N/A'))
            target = route.get('GatewayId', route.get('NatGatewayId', route.get('InstanceId', 'local')))
            status = route.get('State', 'active')
            print(f"     {destination} -> {target} ({status})")
    
    # セキュリティグループ検証
    print(f"\n🔒 セキュリティグループ検証:")
    security_groups = ec2.describe_security_groups(
        Filters=[{'Name': 'vpc-id', 'Values': [vpc_id]}]
    )
    
    for sg in security_groups['SecurityGroups']:
        if sg['GroupName'] != 'default':
            print(f"   {sg['GroupName']} ({sg['GroupId']}):")
            
            # Ingressルール
            for rule in sg['IpPermissions']:
                protocol = rule.get('IpProtocol', 'N/A')
                from_port = rule.get('FromPort', 'All')
                to_port = rule.get('ToPort', 'All')
                
                sources = []
                for ip_range in rule.get('IpRanges', []):
                    sources.append(ip_range['CidrIp'])
                for sg_ref in rule.get('UserIdGroupPairs', []):
                    sources.append(f"sg-{sg_ref['GroupId']}")
                
                source_str = ', '.join(sources) if sources else 'None'
                print(f"     IN: {protocol}:{from_port}-{to_port} from {source_str}")
    
    print(f"\n✅ ネットワーク接続性テスト完了")

def test_internet_connectivity():
    """
    インターネット接続性テスト（テストインスタンス使用）
    """
    print(f"\n=== インターネット接続性テスト ===")
    
    # 注意: 実際のテストにはEC2インスタンスが必要
    print("⚠️  このテストには実際のEC2インスタンスが必要です")
    print("   手動で以下を確認してください:")
    print("   1. パブリックサブネットのインスタンスからインターネットアクセス")
    print("   2. プライベートサブネットのインスタンスからNAT経由でのアウトバウンドアクセス")
    print("   3. データベースサブネットのインスタンスが外部アクセス不可であること")

if __name__ == "__main__":
    test_vpc_connectivity()
    test_internet_connectivity()
```

### 4.2 コスト計算スクリプト

```python
#!/usr/bin/env python3
# cost-calculator.py

def calculate_vpc_costs():
    """
    VPC構成のコスト計算
    """
    
    # 東京リージョンの料金 (USD)
    costs = {
        'nat_gateway_hour': 0.062,
        'nat_gateway_data_gb': 0.062,
        'eip_hour': 0.005,
        'data_transfer_out_gb': 0.114,  # 最初の10TB
    }
    
    # 月間稼働時間
    hours_per_month = 24 * 30
    
    print("=== VPC構成月額コスト試算 ===")
    
    # NAT Gateway (2台)
    nat_cost = 2 * costs['nat_gateway_hour'] * hours_per_month
    print(f"NAT Gateway (2台): ${nat_cost:.2f}")
    
    # Elastic IP (2個、NAT Gateway使用中のため課金なし)
    eip_cost = 0  # NAT Gatewayに関連付けられているため無料
    print(f"Elastic IP (2個): ${eip_cost:.2f} (NAT Gateway使用中)")
    
    # データ転送費用（仮定: 月100GB）
    data_transfer_gb = 100
    data_transfer_cost = data_transfer_gb * costs['data_transfer_out_gb']
    print(f"データ転送 ({data_transfer_gb}GB): ${data_transfer_cost:.2f}")
    
    total_cost = nat_cost + eip_cost + data_transfer_cost
    print(f"\n💰 合計月額: ${total_cost:.2f}")
    
    # コスト削減提案
    print(f"\n💡 コスト最適化提案:")
    print(f"- NAT Gateway 1台構成: ${(total_cost - costs['nat_gateway_hour'] * hours_per_month):.2f}/月 (可用性は下がる)")
    print(f"- NAT Instance使用: 約60-70%のコスト削減可能")
    print(f"- VPC Endpointsの活用でデータ転送費削減")

if __name__ == "__main__":
    calculate_vpc_costs()
```

## Phase 5: クリーンアップ

### 5.1 リソース削除スクリプト

```bash
#!/bin/bash
# スクリプト: cleanup-vpc-resources.sh

source vpc-vars.sh
set -e

echo "=== VPCリソースクリーンアップ開始 ==="

read -p "全てのVPCリソースを削除しますか？ (yes/no): " confirm
if [ "$confirm" != "yes" ]; then
    echo "キャンセルされました"
    exit 1
fi

# NAT Gateway削除
echo "🗑️  NAT Gateway削除中..."
aws ec2 delete-nat-gateway --nat-gateway-id $NAT_GW_1 --region $REGION
aws ec2 delete-nat-gateway --nat-gateway-id $NAT_GW_2 --region $REGION

# NAT Gateway削除完了まで待機
echo "   NAT Gateway削除完了を待機中..."
aws ec2 wait nat-gateway-deleted --nat-gateway-ids $NAT_GW_1 $NAT_GW_2 --region $REGION

# Elastic IP解放
echo "🗑️  Elastic IP解放中..."
aws ec2 release-address --allocation-id $EIP_1 --region $REGION
aws ec2 release-address --allocation-id $EIP_2 --region $REGION

# Internet Gateway切断・削除
echo "🗑️  Internet Gateway削除中..."
aws ec2 detach-internet-gateway --internet-gateway-id $IGW_ID --vpc-id $VPC_ID --region $REGION
aws ec2 delete-internet-gateway --internet-gateway-id $IGW_ID --region $REGION

# サブネット削除
echo "🗑️  サブネット削除中..."
aws ec2 delete-subnet --subnet-id $PUBLIC_SUBNET_1 --region $REGION
aws ec2 delete-subnet --subnet-id $PUBLIC_SUBNET_2 --region $REGION
aws ec2 delete-subnet --subnet-id $PRIVATE_SUBNET_1 --region $REGION
aws ec2 delete-subnet --subnet-id $PRIVATE_SUBNET_2 --region $REGION
aws ec2 delete-subnet --subnet-id $DB_SUBNET_1 --region $REGION
aws ec2 delete-subnet --subnet-id $DB_SUBNET_2 --region $REGION

# ルートテーブル削除
echo "🗑️  ルートテーブル削除中..."
aws ec2 delete-route-table --route-table-id $PUBLIC_RT --region $REGION
aws ec2 delete-route-table --route-table-id $PRIVATE_RT_1 --region $REGION
aws ec2 delete-route-table --route-table-id $PRIVATE_RT_2 --region $REGION
aws ec2 delete-route-table --route-table-id $DB_RT --region $REGION

# セキュリティグループ削除
echo "🗑️  セキュリティグループ削除中..."
aws ec2 delete-security-group --group-id $WEB_SG --region $REGION
aws ec2 delete-security-group --group-id $APP_SG --region $REGION
aws ec2 delete-security-group --group-id $DB_SG --region $REGION
aws ec2 delete-security-group --group-id $MGMT_SG --region $REGION

# VPC削除
echo "🗑️  VPC削除中..."
aws ec2 delete-vpc --vpc-id $VPC_ID --region $REGION

echo "🎉 クリーンアップ完了"

# 変数ファイル削除
rm -f vpc-vars.sh

echo "✅ 全てのリソースが削除されました"
```

## 📊 学習成果と評価

### 習得したスキル
1. **VPC設計パターン**: 3層アーキテクチャの実装
2. **セキュリティ設計**: セキュリティグループの詳細設定
3. **ルーティング設計**: 複数ルートテーブルの管理
4. **高可用性設計**: マルチAZ構成の実装

### 次のステップ
このラボが完了したら、[Lab 2: Transit GatewayとVPC Peering](./lab02-transit-gateway-vpc-peering.md) に進んでください。

---

**⚠️ 重要**: 学習完了後は必ずクリーンアップスクリプトを実行してください。NAT Gatewayの削除を忘れると継続的な課金が発生します。