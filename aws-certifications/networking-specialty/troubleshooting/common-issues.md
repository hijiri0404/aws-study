# ANS-C01 一般的なネットワーク問題とトラブルシューティング

## 🔧 よくある問題と解決策

### 1. VPC接続性問題

#### 問題: EC2インスタンスがインターネットに接続できない

**症状:**
- `ping 8.8.8.8` が失敗
- `curl` コマンドがタイムアウト
- アプリケーションの外部API呼び出しが失敗

**診断手順:**
```bash
# 1. インスタンスの基本情報確認
aws ec2 describe-instances --instance-ids i-1234567890abcdef0 \
  --query 'Reservations[].Instances[].[InstanceId,State.Name,SubnetId,PublicIpAddress,PrivateIpAddress]' \
  --output table

# 2. サブネット設定確認
aws ec2 describe-subnets --subnet-ids subnet-12345678 \
  --query 'Subnets[].[SubnetId,VpcId,CidrBlock,MapPublicIpOnLaunch,AvailabilityZone]' \
  --output table

# 3. ルートテーブル確認
aws ec2 describe-route-tables --filters "Name=association.subnet-id,Values=subnet-12345678" \
  --query 'RouteTables[].Routes[].[DestinationCidrBlock,GatewayId,State]' \
  --output table

# 4. セキュリティグループ確認
aws ec2 describe-security-groups --group-ids sg-12345678 \
  --query 'SecurityGroups[].IpPermissionsEgress[]'
```

**一般的な原因と解決策:**

| 原因 | 確認項目 | 解決策 |
|------|----------|--------|
| Internet Gateway未設定 | IGW存在・アタッチ状況 | IGW作成・VPCアタッチ |
| ルートテーブル設定ミス | 0.0.0.0/0ルート | IGWへのデフォルトルート追加 |
| パブリックIP未割り当て | インスタンスのパブリックIP | Elastic IP割り当て |
| セキュリティグループ制限 | アウトバウンドルール | 必要なポート・プロトコル許可 |
| NACL制限 | Network ACLルール | アウトバウンド許可ルール追加 |

**解決スクリプト例:**
```bash
#!/bin/bash
# internet-connectivity-fix.sh

INSTANCE_ID="i-1234567890abcdef0"

# インスタンス情報取得
SUBNET_ID=$(aws ec2 describe-instances --instance-ids $INSTANCE_ID \
  --query 'Reservations[].Instances[].SubnetId' --output text)

VPC_ID=$(aws ec2 describe-subnets --subnet-ids $SUBNET_ID \
  --query 'Subnets[].VpcId' --output text)

echo "Diagnosing connectivity for instance $INSTANCE_ID in VPC $VPC_ID"

# Internet Gateway確認
IGW_ID=$(aws ec2 describe-internet-gateways \
  --filters "Name=attachment.vpc-id,Values=$VPC_ID" \
  --query 'InternetGateways[].InternetGatewayId' --output text)

if [ -z "$IGW_ID" ]; then
    echo "❌ Internet Gateway not found. Creating..."
    IGW_ID=$(aws ec2 create-internet-gateway \
      --query 'InternetGateway.InternetGatewayId' --output text)
    aws ec2 attach-internet-gateway --internet-gateway-id $IGW_ID --vpc-id $VPC_ID
    echo "✅ Internet Gateway created and attached: $IGW_ID"
fi

# ルートテーブル確認・修正
RT_ID=$(aws ec2 describe-route-tables \
  --filters "Name=association.subnet-id,Values=$SUBNET_ID" \
  --query 'RouteTables[].RouteTableId' --output text)

# デフォルトルート確認
DEFAULT_ROUTE=$(aws ec2 describe-route-tables --route-table-ids $RT_ID \
  --query 'RouteTables[].Routes[?DestinationCidrBlock==`0.0.0.0/0`]' --output text)

if [ -z "$DEFAULT_ROUTE" ]; then
    echo "❌ Default route not found. Adding..."
    aws ec2 create-route --route-table-id $RT_ID \
      --destination-cidr-block 0.0.0.0/0 --gateway-id $IGW_ID
    echo "✅ Default route added to $RT_ID"
fi

echo "🎉 Connectivity diagnosis completed"
```

---

### 2. VPC間通信問題

#### 問題: VPC Peering接続で通信ができない

**症状:**
- Ping が届かない
- アプリケーション間通信が失敗
- DNS解決ができない

**診断コマンド:**
```bash
# VPC Peering状態確認
aws ec2 describe-vpc-peering-connections \
  --filters "Name=status-code,Values=active" \
  --query 'VpcPeeringConnections[].[VpcPeeringConnectionId,Status.Code,AccepterVpcInfo.VpcId,RequesterVpcInfo.VpcId]' \
  --output table

# ルートテーブルでのピアリング設定確認
aws ec2 describe-route-tables --filters "Name=route.vpc-peering-connection-id,Values=pcx-12345678" \
  --query 'RouteTables[].[RouteTableId,Routes[?VpcPeeringConnectionId==`pcx-12345678`]]' \
  --output table
```

**よくある問題:**
1. **ルートテーブル設定漏れ**
   ```bash
   # 両方向のルート設定が必要
   aws ec2 create-route --route-table-id rtb-vpc-a \
     --destination-cidr-block 10.1.0.0/16 \
     --vpc-peering-connection-id pcx-12345678
   
   aws ec2 create-route --route-table-id rtb-vpc-b \
     --destination-cidr-block 10.0.0.0/16 \
     --vpc-peering-connection-id pcx-12345678
   ```

2. **セキュリティグループの相互参照**
   ```bash
   # VPC-A のセキュリティグループ
   aws ec2 authorize-security-group-ingress \
     --group-id sg-vpc-a \
     --protocol tcp --port 80 \
     --source-group sg-vpc-b \
     --source-group-owner-id 123456789012
   ```

3. **DNS解決設定**
   ```bash
   # DNS解決有効化
   aws ec2 modify-vpc-peering-connection-options \
     --vpc-peering-connection-id pcx-12345678 \
     --accepter-peering-connection-options AllowDnsResolutionFromRemoteVpc=true \
     --requester-peering-connection-options AllowDnsResolutionFromRemoteVpc=true
   ```

---

### 3. Direct Connect問題

#### 問題: Direct Connect接続で通信が不安定

**症状:**
- 帯域幅が期待値に届かない
- 間欠的な接続断
- BGPセッションが不安定

**診断手順:**
```bash
# Direct Connect接続状態確認
aws directconnect describe-connections \
  --query 'connections[].[connectionId,connectionState,bandwidth,location]' \
  --output table

# 仮想インターフェース状態確認
aws directconnect describe-virtual-interfaces \
  --query 'virtualInterfaces[].[virtualInterfaceId,virtualInterfaceState,bgpStatus]' \
  --output table

# BGP セッション詳細
aws directconnect describe-virtual-interfaces \
  --virtual-interface-id dxvif-12345678 \
  --query 'virtualInterfaces[].[bgpStatus,routeFilterPrefixes,amazonSideAsn,customerSideAsn]'
```

**一般的な問題と解決策:**

| 問題 | 診断方法 | 解決策 |
|------|----------|--------|
| BGP設定ミス | BGPステータス確認 | ASN、認証キー、VLAN設定見直し |
| ルートフィルタ問題 | ルートフィルタ確認 | 適切なプレフィックス設定 |
| MTUサイズ問題 | パケットロス確認 | Jumbo Frame設定 (9001 bytes) |
| 冗長性問題 | 接続数確認 | セカンダリ接続追加 |

**BGP設定例:**
```
# Customer側ルーター設定例
router bgp 65001
 bgp log-neighbor-changes
 neighbor 169.254.1.1 remote-as 7224
 neighbor 169.254.1.1 password your-bgp-auth-key
 !
 address-family ipv4
  network 192.168.1.0 mask 255.255.255.0
  neighbor 169.254.1.1 activate
  neighbor 169.254.1.1 soft-reconfiguration inbound
 exit-address-family
```

---

### 4. DNS解決問題

#### 問題: Route 53プライベートホストゾーンで名前解決できない

**症状:**
- `nslookup` で解決できない
- アプリケーションでDNSエラー
- 一部のVPCでのみ問題発生

**診断コマンド:**
```bash
# プライベートホストゾーン設定確認
aws route53 list-hosted-zones-by-vpc --vpc-id vpc-12345678 --vpc-region ap-northeast-1

# VPCのDNS設定確認
aws ec2 describe-vpc-attribute --vpc-id vpc-12345678 --attribute enableDnsSupport
aws ec2 describe-vpc-attribute --vpc-id vpc-12345678 --attribute enableDnsHostnames

# インスタンス内でのDNS確認
dig @169.254.169.253 example.local
nslookup example.local 169.254.169.253
```

**一般的な原因:**
1. **VPCのDNS設定無効**
   ```bash
   aws ec2 modify-vpc-attribute --vpc-id vpc-12345678 --enable-dns-support
   aws ec2 modify-vpc-attribute --vpc-id vpc-12345678 --enable-dns-hostnames
   ```

2. **プライベートホストゾーンのVPC関連付け漏れ**
   ```bash
   aws route53 associate-vpc-with-hosted-zone \
     --hosted-zone-id Z1234567890ABC \
     --vpc VPCRegion=ap-northeast-1,VPCId=vpc-12345678
   ```

3. **セキュリティグループでDNS通信ブロック**
   ```bash
   # DNS通信許可 (UDP/TCP 53)
   aws ec2 authorize-security-group-egress \
     --group-id sg-12345678 \
     --protocol udp --port 53 --cidr 0.0.0.0/0
   ```

---

### 5. Load Balancer問題

#### 問題: ALBでヘルスチェックが失敗する

**症状:**
- ターゲットが常にUnhealthy
- 503エラーの発生
- 接続タイムアウト

**診断手順:**
```bash
# ターゲットグループヘルス状況確認
aws elbv2 describe-target-health --target-group-arn arn:aws:elasticloadbalancing:...

# ALB設定確認
aws elbv2 describe-load-balancers --load-balancer-arns arn:aws:elasticloadbalancing:...

# ターゲットグループ設定確認
aws elbv2 describe-target-groups --target-group-arns arn:aws:elasticloadbalancing:...
```

**ヘルスチェック設定の最適化:**
```json
{
  "HealthCheckEnabled": true,
  "HealthCheckIntervalSeconds": 30,
  "HealthCheckPath": "/health",
  "HealthCheckPort": "traffic-port",
  "HealthCheckProtocol": "HTTP",
  "HealthCheckTimeoutSeconds": 5,
  "HealthyThresholdCount": 2,
  "UnhealthyThresholdCount": 3,
  "Matcher": {
    "HttpCode": "200"
  }
}
```

**よくある問題:**
1. **セキュリティグループ設定**
   ```bash
   # ALBからターゲットへのヘルスチェック許可
   aws ec2 authorize-security-group-ingress \
     --group-id sg-target \
     --protocol tcp --port 80 \
     --source-group sg-alb
   ```

2. **ヘルスチェックパス設定**
   ```bash
   # アプリケーション側でヘルスチェックエンドポイント実装
   # GET /health -> 200 OK
   ```

---

## 🔍 診断ツールとコマンド

### ネットワーク診断用スクリプト

```python
#!/usr/bin/env python3
# network_diagnostics.py

import boto3
import subprocess
import json
from datetime import datetime

class NetworkDiagnostics:
    def __init__(self, region='ap-northeast-1'):
        self.ec2 = boto3.client('ec2', region_name=region)
        self.elbv2 = boto3.client('elbv2', region_name=region)
        
    def diagnose_instance_connectivity(self, instance_id):
        """インスタンス接続性の包括的診断"""
        print(f"🔍 診断開始: {instance_id}")
        
        # インスタンス情報取得
        instance = self.ec2.describe_instances(InstanceIds=[instance_id])
        inst_data = instance['Reservations'][0]['Instances'][0]
        
        subnet_id = inst_data['SubnetId']
        vpc_id = inst_data['VpcId']
        security_groups = [sg['GroupId'] for sg in inst_data['SecurityGroups']]
        
        # 診断結果
        results = {
            'timestamp': datetime.now().isoformat(),
            'instance_id': instance_id,
            'diagnostics': {}
        }
        
        # 1. VPC/Subnet基本設定確認
        results['diagnostics']['vpc_config'] = self._check_vpc_config(vpc_id, subnet_id)
        
        # 2. ルーティング確認  
        results['diagnostics']['routing'] = self._check_routing(subnet_id)
        
        # 3. セキュリティグループ確認
        results['diagnostics']['security_groups'] = self._check_security_groups(security_groups)
        
        # 4. NACL確認
        results['diagnostics']['nacl'] = self._check_nacl(subnet_id)
        
        return results
    
    def _check_vpc_config(self, vpc_id, subnet_id):
        """VPC基本設定確認"""
        vpc_attrs = {}
        
        # DNS設定確認
        dns_support = self.ec2.describe_vpc_attribute(
            VpcId=vpc_id, Attribute='enableDnsSupport'
        )
        dns_hostnames = self.ec2.describe_vpc_attribute(
            VpcId=vpc_id, Attribute='enableDnsHostnames'
        )
        
        vpc_attrs['dns_support'] = dns_support['EnableDnsSupport']['Value']
        vpc_attrs['dns_hostnames'] = dns_hostnames['EnableDnsHostnames']['Value']
        
        # サブネット設定確認
        subnet = self.ec2.describe_subnets(SubnetIds=[subnet_id])['Subnets'][0]
        vpc_attrs['auto_assign_public_ip'] = subnet['MapPublicIpOnLaunch']
        vpc_attrs['availability_zone'] = subnet['AvailabilityZone']
        
        return vpc_attrs
    
    def _check_routing(self, subnet_id):
        """ルーティング設定確認"""
        route_tables = self.ec2.describe_route_tables(
            Filters=[{'Name': 'association.subnet-id', 'Values': [subnet_id]}]
        )
        
        routing_info = []
        for rt in route_tables['RouteTables']:
            rt_info = {
                'route_table_id': rt['RouteTableId'],
                'routes': []
            }
            
            for route in rt['Routes']:
                route_info = {
                    'destination': route.get('DestinationCidrBlock', 'N/A'),
                    'target': route.get('GatewayId', route.get('NatGatewayId', 'local')),
                    'state': route.get('State', 'active')
                }
                rt_info['routes'].append(route_info)
            
            routing_info.append(rt_info)
        
        return routing_info
    
    def _check_security_groups(self, sg_ids):
        """セキュリティグループ確認"""
        sgs = self.ec2.describe_security_groups(GroupIds=sg_ids)
        
        sg_info = []
        for sg in sgs['SecurityGroups']:
            sg_data = {
                'group_id': sg['GroupId'],
                'group_name': sg['GroupName'],
                'inbound_rules': len(sg['IpPermissions']),
                'outbound_rules': len(sg['IpPermissionsEgress']),
                'has_ssh_access': self._check_ssh_access(sg['IpPermissions']),
                'has_http_access': self._check_http_access(sg['IpPermissions'])
            }
            sg_info.append(sg_data)
        
        return sg_info
    
    def _check_ssh_access(self, rules):
        """SSH(22)アクセス確認"""
        for rule in rules:
            if rule.get('FromPort') == 22 and rule.get('ToPort') == 22:
                return True
        return False
    
    def _check_http_access(self, rules):
        """HTTP(80/443)アクセス確認"""
        for rule in rules:
            if rule.get('FromPort') in [80, 443]:
                return True
        return False
    
    def _check_nacl(self, subnet_id):
        """Network ACL確認"""
        nacls = self.ec2.describe_network_acls(
            Filters=[{'Name': 'association.subnet-id', 'Values': [subnet_id]}]
        )
        
        nacl_info = []
        for nacl in nacls['NetworkAcls']:
            nacl_data = {
                'nacl_id': nacl['NetworkAclId'],
                'is_default': nacl['IsDefault'],
                'inbound_entries': len([e for e in nacl['Entries'] if not e['Egress']]),
                'outbound_entries': len([e for e in nacl['Entries'] if e['Egress']])
            }
            nacl_info.append(nacl_data)
        
        return nacl_info

# 使用例
if __name__ == "__main__":
    diagnostics = NetworkDiagnostics()
    result = diagnostics.diagnose_instance_connectivity('i-1234567890abcdef0')
    print(json.dumps(result, indent=2))
```

### 自動修復スクリプト

```bash
#!/bin/bash
# auto_network_fix.sh

INSTANCE_ID=$1

if [ -z "$INSTANCE_ID" ]; then
    echo "Usage: $0 <instance-id>"
    exit 1
fi

echo "🔧 自動ネットワーク修復開始: $INSTANCE_ID"

# 1. インスタンス情報取得
INSTANCE_DATA=$(aws ec2 describe-instances --instance-ids $INSTANCE_ID)
SUBNET_ID=$(echo $INSTANCE_DATA | jq -r '.Reservations[].Instances[].SubnetId')
VPC_ID=$(echo $INSTANCE_DATA | jq -r '.Reservations[].Instances[].VpcId')

echo "📍 対象リソース: VPC=$VPC_ID, Subnet=$SUBNET_ID"

# 2. DNS設定確認・修正
echo "🔍 DNS設定確認中..."
DNS_SUPPORT=$(aws ec2 describe-vpc-attribute --vpc-id $VPC_ID --attribute enableDnsSupport \
    --query 'EnableDnsSupport.Value' --output text)

if [ "$DNS_SUPPORT" = "False" ]; then
    echo "⚡ DNS Support有効化中..."
    aws ec2 modify-vpc-attribute --vpc-id $VPC_ID --enable-dns-support
fi

DNS_HOSTNAMES=$(aws ec2 describe-vpc-attribute --vpc-id $VPC_ID --attribute enableDnsHostnames \
    --query 'EnableDnsHostnames.Value' --output text)

if [ "$DNS_HOSTNAMES" = "False" ]; then
    echo "⚡ DNS Hostnames有効化中..."
    aws ec2 modify-vpc-attribute --vpc-id $VPC_ID --enable-dns-hostnames
fi

# 3. Internet Gateway確認・作成
echo "🔍 Internet Gateway確認中..."
IGW_ID=$(aws ec2 describe-internet-gateways \
    --filters "Name=attachment.vpc-id,Values=$VPC_ID" \
    --query 'InternetGateways[].InternetGatewayId' --output text)

if [ -z "$IGW_ID" ] || [ "$IGW_ID" = "None" ]; then
    echo "⚡ Internet Gateway作成中..."
    IGW_ID=$(aws ec2 create-internet-gateway \
        --query 'InternetGateway.InternetGatewayId' --output text)
    aws ec2 attach-internet-gateway --internet-gateway-id $IGW_ID --vpc-id $VPC_ID
    echo "✅ Internet Gateway作成完了: $IGW_ID"
fi

# 4. ルートテーブル確認・修正
echo "🔍 ルートテーブル確認中..."
RT_ID=$(aws ec2 describe-route-tables \
    --filters "Name=association.subnet-id,Values=$SUBNET_ID" \
    --query 'RouteTables[].RouteTableId' --output text)

DEFAULT_ROUTE_EXISTS=$(aws ec2 describe-route-tables --route-table-ids $RT_ID \
    --query 'RouteTables[].Routes[?DestinationCidrBlock==`0.0.0.0/0`]' --output text)

if [ -z "$DEFAULT_ROUTE_EXISTS" ]; then
    echo "⚡ デフォルトルート追加中..."
    aws ec2 create-route --route-table-id $RT_ID \
        --destination-cidr-block 0.0.0.0/0 --gateway-id $IGW_ID
    echo "✅ デフォルトルート追加完了"
fi

# 5. セキュリティグループ確認
echo "🔍 セキュリティグループ確認中..."
SG_IDS=$(echo $INSTANCE_DATA | jq -r '.Reservations[].Instances[].SecurityGroups[].GroupId')

for SG_ID in $SG_IDS; do
    echo "   チェック中: $SG_ID"
    
    # アウトバウンドHTTPS許可確認
    HTTPS_OUTBOUND=$(aws ec2 describe-security-groups --group-ids $SG_ID \
        --query 'SecurityGroups[].IpPermissionsEgress[?FromPort==`443`]' --output text)
    
    if [ -z "$HTTPS_OUTBOUND" ]; then
        echo "⚡ HTTPSアウトバウンド許可追加中..."
        aws ec2 authorize-security-group-egress \
            --group-id $SG_ID --protocol tcp --port 443 --cidr 0.0.0.0/0
    fi
done

echo "🎉 自動修復完了"
echo "📋 修復内容:"
echo "   - DNS Support: 有効化"
echo "   - DNS Hostnames: 有効化"  
echo "   - Internet Gateway: 確認・作成"
echo "   - デフォルトルート: 確認・追加"
echo "   - セキュリティグループ: HTTPS許可"
```

## 📚 追加リソース

### 公式ドキュメント
- [VPC Troubleshooting](https://docs.aws.amazon.com/vpc/latest/userguide/troubleshooting.html)
- [Direct Connect Troubleshooting](https://docs.aws.amazon.com/directconnect/latest/UserGuide/troubleshooting.html)
- [Route 53 Troubleshooting](https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/troubleshooting.html)

### 診断ツール
- **AWS VPC Reachability Analyzer**: パス分析
- **AWS Network Access Analyzer**: アクセス分析
- **VPC Flow Logs**: 詳細なトラフィック分析
- **CloudWatch Network Insights**: パフォーマンス監視

---

**重要**: トラブルシューティングは体系的なアプローチが重要です。問題を切り分け、一つずつ確認・修正することで効率的な解決が可能です。