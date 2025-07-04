# AWS ANS-C01 実践トラブルシューティングシナリオ

## 概要

この文書では、AWS Advanced Networking Specialty 試験で出題される可能性のある実践的なトラブルシューティングシナリオを詳細に解説します。各シナリオには症状、原因分析、解決手順、予防策が含まれています。

---

## シナリオ 1: Transit Gateway ルーティングの問題

### 問題発生状況
```
本社 VPC (10.0.0.0/16) から支社 VPC (10.1.0.0/16) への通信が断続的に失敗する。
一部のサブネットからは通信可能だが、他のサブネットからは通信不可。
```

### 症状
- ping が断続的にタイムアウト
- アプリケーションのレスポンスが遅延
- 特定のサブネットからのみ通信可能

### 初期調査コマンド
```bash
# Transit Gateway の状態確認
aws ec2 describe-transit-gateways --transit-gateway-ids tgw-xxxxxxxx

# アタッチメントの状態確認
aws ec2 describe-transit-gateway-attachments --filters "Name=transit-gateway-id,Values=tgw-xxxxxxxx"

# ルートテーブルの確認
aws ec2 describe-transit-gateway-route-tables --transit-gateway-route-table-ids tgw-rtb-xxxxxxxx

# ルートの詳細確認
aws ec2 search-transit-gateway-routes \
  --transit-gateway-route-table-id tgw-rtb-xxxxxxxx \
  --filters "Name=type,Values=static,propagated"
```

### 詳細診断手順

**Step 1: ルート伝播の確認**
```bash
# ルートテーブルの関連付け確認
aws ec2 get-transit-gateway-route-table-associations \
  --transit-gateway-route-table-id tgw-rtb-xxxxxxxx

# ルートの伝播状況確認
aws ec2 get-transit-gateway-route-table-propagations \
  --transit-gateway-route-table-id tgw-rtb-xxxxxxxx

# 特定のプレフィックスのルート確認
aws ec2 search-transit-gateway-routes \
  --transit-gateway-route-table-id tgw-rtb-xxxxxxxx \
  --filters "Name=route-search.exact-match,Values=10.1.0.0/16"
```

**Step 2: VPC ルートテーブルの確認**
```bash
# VPC のルートテーブル一覧
aws ec2 describe-route-tables --filters "Name=vpc-id,Values=vpc-xxxxxxxx"

# 特定のサブネットのルートテーブル確認
aws ec2 describe-route-tables \
  --filters "Name=association.subnet-id,Values=subnet-xxxxxxxx"

# ルートの詳細確認
aws ec2 describe-route-tables \
  --route-table-ids rtb-xxxxxxxx \
  --query 'RouteTables[0].Routes'
```

**Step 3: セキュリティグループとNACLの確認**
```bash
# セキュリティグループのルール確認
aws ec2 describe-security-groups --group-ids sg-xxxxxxxx

# NACL の確認
aws ec2 describe-network-acls --filters "Name=association.subnet-id,Values=subnet-xxxxxxxx"
```

### 根本原因分析

**考えられる原因:**
1. **ルートテーブルの関連付け不備**
   - VPC アタッチメントが正しいルートテーブルに関連付けられていない
   - 複数のルートテーブルが存在し、一部のサブネットが間違ったテーブルを参照

2. **ルート伝播の設定不備**
   - 自動伝播が無効になっている
   - 静的ルートの設定不備

3. **IP アドレス重複**
   - 複数の VPC で同じ CIDR ブロックが使用されている

### 解決手順

**解決案 1: ルートテーブルの再関連付け**
```bash
# 現在の関連付け解除
aws ec2 disassociate-transit-gateway-route-table \
  --transit-gateway-attachment-id tgw-attach-xxxxxxxx \
  --transit-gateway-route-table-id tgw-rtb-xxxxxxxx

# 正しいルートテーブルに関連付け
aws ec2 associate-transit-gateway-route-table \
  --transit-gateway-attachment-id tgw-attach-xxxxxxxx \
  --transit-gateway-route-table-id tgw-rtb-yyyyyyyy
```

**解決案 2: 静的ルートの追加**
```bash
# 静的ルートの追加
aws ec2 create-transit-gateway-route \
  --route-table-id tgw-rtb-xxxxxxxx \
  --destination-cidr-block 10.1.0.0/16 \
  --transit-gateway-attachment-id tgw-attach-xxxxxxxx
```

**解決案 3: VPC ルートテーブルの修正**
```bash
# VPC ルートテーブルに TGW へのルート追加
aws ec2 create-route \
  --route-table-id rtb-xxxxxxxx \
  --destination-cidr-block 10.1.0.0/16 \
  --transit-gateway-id tgw-xxxxxxxx
```

### 予防策と監視

**1. 自動化スクリプト**
```python
import boto3
import json

def validate_tgw_routing():
    ec2 = boto3.client('ec2')
    
    # Transit Gateway の状態確認
    tgws = ec2.describe_transit_gateways()
    
    for tgw in tgws['TransitGateways']:
        if tgw['State'] != 'available':
            print(f"TGW {tgw['TransitGatewayId']} is not available")
            continue
            
        # アタッチメントの確認
        attachments = ec2.describe_transit_gateway_attachments(
            Filters=[
                {'Name': 'transit-gateway-id', 'Values': [tgw['TransitGatewayId']]}
            ]
        )
        
        for attachment in attachments['TransitGatewayAttachments']:
            # ルートテーブルの関連付け確認
            associations = ec2.get_transit_gateway_route_table_associations(
                TransitGatewayRouteTableId=attachment['Association']['TransitGatewayRouteTableId']
            )
            
            if not associations['Associations']:
                print(f"No associations found for attachment {attachment['TransitGatewayAttachmentId']}")

validate_tgw_routing()
```

**2. CloudWatch アラーム**
```bash
# パケットドロップの監視
aws cloudwatch put-metric-alarm \
  --alarm-name "TransitGateway-PacketDrops" \
  --alarm-description "Monitor Transit Gateway packet drops" \
  --metric-name PacketDropCount \
  --namespace AWS/TransitGateway \
  --statistic Sum \
  --period 300 \
  --threshold 100 \
  --comparison-operator GreaterThanThreshold \
  --evaluation-periods 2 \
  --alarm-actions arn:aws:sns:ap-northeast-1:123456789012:network-alerts
```

---

## シナリオ 2: Direct Connect BGP セッションの不安定

### 問題発生状況
```
Direct Connect 経由の BGP セッションが断続的に切断される。
オンプレミスからクラウドへの通信が不安定で、時々 VPN 経由にフェイルオーバーしている。
```

### 症状
- BGP セッションが Up/Down を繰り返す
- ルート広告が不安定
- パフォーマンスが期待値より低い

### 初期調査コマンド
```bash
# Direct Connect 接続の状態確認
aws directconnect describe-connections

# Virtual Interface の状態確認
aws directconnect describe-virtual-interfaces --virtual-interface-id dxvif-xxxxxxxx

# BGP セッションの詳細確認
aws directconnect describe-virtual-interfaces \
  --virtual-interface-id dxvif-xxxxxxxx \
  --query 'virtualInterfaces[0].bgpPeers'
```

### 詳細診断手順

**Step 1: BGP セッションの分析**
```bash
# BGP セッションの状態履歴確認
aws logs filter-log-events \
  --log-group-name /aws/directconnect/flowlogs \
  --filter-pattern "BGP" \
  --start-time 1640995200000 \
  --end-time 1641081600000

# VIF のメトリクス確認
aws cloudwatch get-metric-statistics \
  --namespace AWS/DX \
  --metric-name ConnectionState \
  --dimensions Name=VirtualInterfaceId,Value=dxvif-xxxxxxxx \
  --start-time 2024-01-01T00:00:00Z \
  --end-time 2024-01-01T23:59:59Z \
  --period 300 \
  --statistics Maximum
```

**Step 2: ネットワーク品質の確認**
```bash
# パケットロスの確認
aws cloudwatch get-metric-statistics \
  --namespace AWS/DX \
  --metric-name ConnectionPacketsDropped \
  --dimensions Name=VirtualInterfaceId,Value=dxvif-xxxxxxxx \
  --start-time 2024-01-01T00:00:00Z \
  --end-time 2024-01-01T23:59:59Z \
  --period 300 \
  --statistics Sum

# レイテンシの確認
aws cloudwatch get-metric-statistics \
  --namespace AWS/DX \
  --metric-name ConnectionLatency \
  --dimensions Name=VirtualInterfaceId,Value=dxvif-xxxxxxxx \
  --start-time 2024-01-01T00:00:00Z \
  --end-time 2024-01-01T23:59:59Z \
  --period 300 \
  --statistics Average
```

**Step 3: オンプレミス側の確認**
```cisco
# Cisco デバイスでの BGP セッション確認
show ip bgp summary
show ip bgp neighbors 192.168.1.2
show ip bgp neighbors 192.168.1.2 advertised-routes
show ip bgp neighbors 192.168.1.2 received-routes

# インターフェース統計の確認
show interface gigabitethernet 0/0/0
show interface gigabitethernet 0/0/0 | include error

# BGP ログの確認
show logging | include BGP
```

### 根本原因分析

**考えられる原因:**

1. **BGP タイマー設定の不一致**
   - Keep-alive タイマーと Hold タイマーの設定が適切でない
   - ネットワーク遅延に対してタイマーが短すぎる

2. **物理層の問題**
   - 光ファイバーの品質劣化
   - SFP モジュールの不具合
   - パケットロス率の増加

3. **ルート広告の問題**
   - 過度なルート広告による BGP セッションの負荷
   - ルートフラップの発生

### 解決手順

**解決案 1: BGP タイマーの調整**
```cisco
# オンプレミス側 (Cisco)
router bgp 65001
 neighbor 192.168.1.2 remote-as 64512
 neighbor 192.168.1.2 timers 30 90
 neighbor 192.168.1.2 timers connect 30
```

**解決案 2: BFD (Bidirectional Forwarding Detection) の設定**
```cisco
# BFD の有効化
router bgp 65001
 neighbor 192.168.1.2 fall-over bfd
 
# BFD インターフェース設定
interface GigabitEthernet0/0/0
 bfd interval 300 min_rx 300 multiplier 3
```

**解決案 3: ルートフィルタリングの実装**
```cisco
# ルートマップでの広告制限
ip prefix-list ALLOWED-PREFIXES seq 5 permit 172.16.0.0/16
ip prefix-list ALLOWED-PREFIXES seq 10 permit 172.17.0.0/16

route-map TO-AWS permit 10
 match ip address prefix-list ALLOWED-PREFIXES
 set local-preference 200

router bgp 65001
 neighbor 192.168.1.2 route-map TO-AWS out
```

### 予防策と監視

**1. 自動監視スクリプト**
```python
import boto3
import time
from datetime import datetime, timedelta

def monitor_dx_bgp():
    dx = boto3.client('directconnect')
    cloudwatch = boto3.client('cloudwatch')
    
    # Virtual Interface の一覧取得
    vifs = dx.describe_virtual_interfaces()
    
    for vif in vifs['virtualInterfaces']:
        vif_id = vif['virtualInterfaceId']
        
        # BGP セッションの状態確認
        for bgp_peer in vif.get('bgpPeers', []):
            bgp_status = bgp_peer.get('bgpStatus', 'unknown')
            
            # メトリクスの送信
            cloudwatch.put_metric_data(
                Namespace='Custom/DirectConnect',
                MetricData=[
                    {
                        'MetricName': 'BGPSessionState',
                        'Value': 1 if bgp_status == 'up' else 0,
                        'Unit': 'Count',
                        'Dimensions': [
                            {'Name': 'VirtualInterfaceId', 'Value': vif_id},
                            {'Name': 'BGPPeerIP', 'Value': bgp_peer.get('customerAddress', 'unknown')}
                        ]
                    }
                ]
            )
            
            # BGP セッションダウンの場合、アラート
            if bgp_status != 'up':
                print(f"BGP session down for VIF {vif_id}")
                # SNS 通知などの処理を追加

monitor_dx_bgp()
```

**2. CloudWatch ダッシュボード**
```json
{
  "widgets": [
    {
      "type": "metric",
      "properties": {
        "metrics": [
          ["AWS/DX", "ConnectionState", "VirtualInterfaceId", "dxvif-xxxxxxxx"],
          [".", "ConnectionPacketsDropped", ".", "."],
          [".", "ConnectionLatency", ".", "."]
        ],
        "period": 300,
        "stat": "Average",
        "region": "ap-northeast-1",
        "title": "Direct Connect Metrics"
      }
    }
  ]
}
```

---

## シナリオ 3: VPC Peering 接続の解決不可

### 問題発生状況
```
VPC A (10.0.0.0/16) と VPC B (10.1.0.0/16) 間でピアリング接続を設定したが、
特定のサブネットからの通信のみ失敗する。
```

### 症状
- 一部のサブネットからは通信可能
- 特定の EC2 インスタンスからの通信が失敗
- DNS 解決が正常に動作しない

### 初期調査コマンド
```bash
# VPC Peering 接続の状態確認
aws ec2 describe-vpc-peering-connections --vpc-peering-connection-ids pcx-xxxxxxxx

# ルートテーブルの確認
aws ec2 describe-route-tables --filters "Name=vpc-id,Values=vpc-xxxxxxxx"

# DNS 解決の確認
aws ec2 describe-vpc-attribute --vpc-id vpc-xxxxxxxx --attribute enableDnsHostnames
aws ec2 describe-vpc-attribute --vpc-id vpc-xxxxxxxx --attribute enableDnsSupport
```

### 詳細診断手順

**Step 1: ピアリング接続の詳細確認**
```bash
# ピアリング接続の詳細情報
aws ec2 describe-vpc-peering-connections \
  --vpc-peering-connection-ids pcx-xxxxxxxx \
  --query 'VpcPeeringConnections[0].{State:Status.Code,RequesterVpc:RequesterVpcInfo.VpcId,AccepterVpc:AccepterVpcInfo.VpcId}'

# DNS 解決オプションの確認
aws ec2 describe-vpc-peering-connections \
  --vpc-peering-connection-ids pcx-xxxxxxxx \
  --query 'VpcPeeringConnections[0].{RequesterDnsResolution:RequesterVpcInfo.PeeringOptions.AllowDnsResolutionFromRemoteVpc,AccepterDnsResolution:AccepterVpcInfo.PeeringOptions.AllowDnsResolutionFromRemoteVpc}'
```

**Step 2: ルーティングの詳細確認**
```bash
# 各サブネットのルートテーブル確認
aws ec2 describe-route-tables \
  --filters "Name=association.subnet-id,Values=subnet-xxxxxxxx" \
  --query 'RouteTables[0].Routes[?DestinationCidrBlock==`10.1.0.0/16`]'

# ルートテーブルの関連付け確認
aws ec2 describe-route-tables \
  --filters "Name=vpc-id,Values=vpc-xxxxxxxx" \
  --query 'RouteTables[*].{RouteTableId:RouteTableId,Associations:Associations[*].SubnetId,Routes:Routes[?DestinationCidrBlock==`10.1.0.0/16`]}'
```

**Step 3: セキュリティ設定の確認**
```bash
# セキュリティグループの確認
aws ec2 describe-security-groups --group-ids sg-xxxxxxxx \
  --query 'SecurityGroups[0].IpPermissions[?FromPort==`80`]'

# NACL の確認
aws ec2 describe-network-acls \
  --filters "Name=association.subnet-id,Values=subnet-xxxxxxxx" \
  --query 'NetworkAcls[0].Entries[?RuleNumber==`100`]'
```

### 根本原因分析

**考えられる原因:**

1. **ルートテーブルの設定不備**
   - 一部のサブネットのルートテーブルにピアリング接続のルートが設定されていない
   - メインルートテーブルとカスタムルートテーブルの設定差異

2. **DNS 解決の設定不備**
   - DNS 解決オプションが有効になっていない
   - VPC の DNS 設定が無効

3. **セキュリティグループの設定不備**
   - 相手側 VPC からの通信を許可していない
   - NACL でブロックされている

### 解決手順

**解決案 1: ルートテーブルの統一**
```bash
# 不足しているルートの追加
aws ec2 create-route \
  --route-table-id rtb-xxxxxxxx \
  --destination-cidr-block 10.1.0.0/16 \
  --vpc-peering-connection-id pcx-xxxxxxxx

# 全てのルートテーブルに適用
for rtb in $(aws ec2 describe-route-tables --filters "Name=vpc-id,Values=vpc-xxxxxxxx" --query 'RouteTables[*].RouteTableId' --output text); do
  aws ec2 create-route \
    --route-table-id $rtb \
    --destination-cidr-block 10.1.0.0/16 \
    --vpc-peering-connection-id pcx-xxxxxxxx
done
```

**解決案 2: DNS 解決の有効化**
```bash
# DNS 解決オプションの有効化
aws ec2 modify-vpc-peering-connection-options \
  --vpc-peering-connection-id pcx-xxxxxxxx \
  --requester-peering-connection-options AllowDnsResolutionFromRemoteVpc=true \
  --accepter-peering-connection-options AllowDnsResolutionFromRemoteVpc=true

# VPC の DNS 設定確認・有効化
aws ec2 modify-vpc-attribute --vpc-id vpc-xxxxxxxx --enable-dns-hostnames
aws ec2 modify-vpc-attribute --vpc-id vpc-xxxxxxxx --enable-dns-support
```

**解決案 3: セキュリティグループの修正**
```bash
# セキュリティグループルールの追加
aws ec2 authorize-security-group-ingress \
  --group-id sg-xxxxxxxx \
  --protocol tcp \
  --port 80 \
  --source-group sg-yyyyyyyy

# CIDR ブロックでの許可
aws ec2 authorize-security-group-ingress \
  --group-id sg-xxxxxxxx \
  --protocol tcp \
  --port 80 \
  --cidr 10.1.0.0/16
```

### 予防策と監視

**1. 接続性テストスクリプト**
```python
import boto3
import subprocess
import socket

def test_vpc_peering_connectivity():
    ec2 = boto3.client('ec2')
    
    # VPC Peering 接続の一覧取得
    peering_connections = ec2.describe_vpc_peering_connections(
        Filters=[{'Name': 'status-code', 'Values': ['active']}]
    )
    
    for pcx in peering_connections['VpcPeeringConnections']:
        pcx_id = pcx['VpcPeeringConnectionId']
        requester_vpc = pcx['RequesterVpcInfo']['VpcId']
        accepter_vpc = pcx['AccepterVpcInfo']['VpcId']
        
        print(f"Testing connectivity for peering connection {pcx_id}")
        
        # 両方向のルートテーブルチェック
        check_routes(requester_vpc, pcx['AccepterVpcInfo']['CidrBlock'], pcx_id)
        check_routes(accepter_vpc, pcx['RequesterVpcInfo']['CidrBlock'], pcx_id)

def check_routes(vpc_id, destination_cidr, pcx_id):
    ec2 = boto3.client('ec2')
    
    route_tables = ec2.describe_route_tables(
        Filters=[{'Name': 'vpc-id', 'Values': [vpc_id]}]
    )
    
    for rt in route_tables['RouteTables']:
        rt_id = rt['RouteTableId']
        routes = rt['Routes']
        
        # 該当するルートが存在するかチェック
        peering_route_exists = any(
            route.get('DestinationCidrBlock') == destination_cidr and
            route.get('VpcPeeringConnectionId') == pcx_id
            for route in routes
        )
        
        if not peering_route_exists:
            print(f"Missing route in route table {rt_id} for destination {destination_cidr}")

test_vpc_peering_connectivity()
```

**2. 自動修復スクリプト**
```python
def auto_fix_peering_routes():
    ec2 = boto3.client('ec2')
    
    peering_connections = ec2.describe_vpc_peering_connections(
        Filters=[{'Name': 'status-code', 'Values': ['active']}]
    )
    
    for pcx in peering_connections['VpcPeeringConnections']:
        pcx_id = pcx['VpcPeeringConnectionId']
        
        # Requester 側のルート修正
        fix_missing_routes(
            pcx['RequesterVpcInfo']['VpcId'],
            pcx['AccepterVpcInfo']['CidrBlock'],
            pcx_id
        )
        
        # Accepter 側のルート修正
        fix_missing_routes(
            pcx['AccepterVpcInfo']['VpcId'],
            pcx['RequesterVpcInfo']['CidrBlock'],
            pcx_id
        )

def fix_missing_routes(vpc_id, destination_cidr, pcx_id):
    ec2 = boto3.client('ec2')
    
    route_tables = ec2.describe_route_tables(
        Filters=[{'Name': 'vpc-id', 'Values': [vpc_id]}]
    )
    
    for rt in route_tables['RouteTables']:
        try:
            ec2.create_route(
                RouteTableId=rt['RouteTableId'],
                DestinationCidrBlock=destination_cidr,
                VpcPeeringConnectionId=pcx_id
            )
            print(f"Added route to {rt['RouteTableId']}")
        except Exception as e:
            if "RouteAlreadyExists" not in str(e):
                print(f"Error adding route to {rt['RouteTableId']}: {str(e)}")

auto_fix_peering_routes()
```

---

## シナリオ 4: DNS 解決とRoute 53 の問題

### 問題発生状況
```
ハイブリッドクラウド環境でオンプレミスの DNS 名前解決が失敗する。
AWS リソースからオンプレミスの FQDN を解決できない。
```

### 症状
- `nslookup` や `dig` コマンドが失敗
- アプリケーションが内部ホスト名を解決できない
- 間欠的な DNS 解決の失敗

### 初期調査コマンド
```bash
# Route 53 Resolver の状態確認
aws route53resolver list-resolver-endpoints

# Resolver Rule の確認
aws route53resolver list-resolver-rules

# VPC の DNS 設定確認
aws ec2 describe-vpc-attribute --vpc-id vpc-xxxxxxxx --attribute enableDnsHostnames
aws ec2 describe-vpc-attribute --vpc-id vpc-xxxxxxxx --attribute enableDnsSupport
```

### 詳細診断手順

**Step 1: DNS 解決経路の確認**
```bash
# EC2 インスタンスでの DNS 設定確認
# インスタンスにSSH接続後
cat /etc/resolv.conf
systemd-resolve --status
dig @169.254.169.253 example.com

# Route 53 Resolver Endpoint の詳細確認
aws route53resolver get-resolver-endpoint --resolver-endpoint-id rslvr-in-xxxxxxxx
```

**Step 2: ネットワーク接続の確認**
```bash
# Resolver Endpoint への接続確認
aws ec2 describe-network-interfaces \
  --filters "Name=description,Values=*Route 53 Resolver*" \
  --query 'NetworkInterfaces[*].{NetworkInterfaceId:NetworkInterfaceId,PrivateIpAddress:PrivateIpAddress,SubnetId:SubnetId,SecurityGroups:Groups[*].GroupId}'

# セキュリティグループの確認
aws ec2 describe-security-groups --group-ids sg-xxxxxxxx \
  --query 'SecurityGroups[0].IpPermissions[?FromPort==`53`]'
```

**Step 3: Route 53 Resolver Rule の確認**
```bash
# Rule の詳細確認
aws route53resolver get-resolver-rule --resolver-rule-id rslvr-rr-xxxxxxxx

# Rule の関連付け確認
aws route53resolver list-resolver-rule-associations \
  --filters "Name=resolver-rule-id,Values=rslvr-rr-xxxxxxxx"
```

### 根本原因分析

**考えられる原因:**

1. **Resolver Rule の設定不備**
   - ドメイン名の指定が間違っている
   - ターゲット IP アドレスが不正

2. **ネットワーク接続の問題**
   - セキュリティグループが DNS トラフィック(53番ポート)を許可していない
   - NACL で DNS トラフィックがブロックされている

3. **VPC の DNS 設定**
   - DNS 解決と DNS ホスト名が無効
   - DHCP オプションセットの設定不備

### 解決手順

**解決案 1: Resolver Rule の修正**
```bash
# 新しい Resolver Rule の作成
aws route53resolver create-resolver-rule \
  --creator-request-id $(date +%s) \
  --rule-type FORWARD \
  --domain-name corp.example.com \
  --resolver-endpoint-id rslvr-out-xxxxxxxx \
  --target-ips 'Ip=172.16.1.10,Port=53' 'Ip=172.16.1.11,Port=53'

# Rule の VPC への関連付け
aws route53resolver associate-resolver-rule \
  --resolver-rule-id rslvr-rr-xxxxxxxx \
  --vpc-id vpc-xxxxxxxx
```

**解決案 2: セキュリティグループの修正**
```bash
# DNS トラフィックを許可するセキュリティグループルール
aws ec2 authorize-security-group-ingress \
  --group-id sg-xxxxxxxx \
  --protocol udp \
  --port 53 \
  --cidr 10.0.0.0/8

aws ec2 authorize-security-group-ingress \
  --group-id sg-xxxxxxxx \
  --protocol tcp \
  --port 53 \
  --cidr 10.0.0.0/8
```

**解決案 3: DHCP オプションセットの設定**
```bash
# DHCP オプションセットの作成
aws ec2 create-dhcp-options \
  --dhcp-configurations "Key=domain-name,Values=corp.example.com" \
  "Key=domain-name-servers,Values=10.0.100.10,10.0.100.11"

# VPC への関連付け
aws ec2 associate-dhcp-options \
  --dhcp-options-id dopt-xxxxxxxx \
  --vpc-id vpc-xxxxxxxx
```

### 予防策と監視

**1. DNS 解決テストスクリプト**
```python
import boto3
import socket
import dns.resolver

def test_dns_resolution():
    # テスト対象のドメイン一覧
    test_domains = [
        'app1.corp.example.com',
        'db1.corp.example.com',
        'mail.corp.example.com'
    ]
    
    for domain in test_domains:
        try:
            # DNS 解決テスト
            result = socket.gethostbyname(domain)
            print(f"✓ {domain} -> {result}")
            
            # より詳細な DNS 解決テスト
            resolver = dns.resolver.Resolver()
            resolver.nameservers = ['169.254.169.253']  # VPC DNS
            answer = resolver.resolve(domain, 'A')
            
            for record in answer:
                print(f"  DNS Record: {record}")
                
        except Exception as e:
            print(f"✗ {domain} -> Error: {str(e)}")
            
            # CloudWatch にメトリクス送信
            cloudwatch = boto3.client('cloudwatch')
            cloudwatch.put_metric_data(
                Namespace='Custom/DNS',
                MetricData=[
                    {
                        'MetricName': 'DNSResolutionFailure',
                        'Value': 1,
                        'Unit': 'Count',
                        'Dimensions': [
                            {'Name': 'Domain', 'Value': domain}
                        ]
                    }
                ]
            )

test_dns_resolution()
```

**2. Route 53 Resolver の監視**
```python
def monitor_resolver_endpoints():
    route53resolver = boto3.client('route53resolver')
    cloudwatch = boto3.client('cloudwatch')
    
    # Resolver Endpoint の状態確認
    endpoints = route53resolver.list_resolver_endpoints()
    
    for endpoint in endpoints['ResolverEndpoints']:
        endpoint_id = endpoint['Id']
        status = endpoint['Status']
        
        # 状態をメトリクスとして送信
        status_value = 1 if status == 'OPERATIONAL' else 0
        
        cloudwatch.put_metric_data(
            Namespace='Custom/Route53Resolver',
            MetricData=[
                {
                    'MetricName': 'EndpointStatus',
                    'Value': status_value,
                    'Unit': 'Count',
                    'Dimensions': [
                        {'Name': 'EndpointId', 'Value': endpoint_id}
                    ]
                }
            ]
        )
        
        # IP アドレスの確認
        for ip_address in endpoint['IpAddresses']:
            ip_status = 1 if ip_address['Status'] == 'ATTACHED' else 0
            
            cloudwatch.put_metric_data(
                Namespace='Custom/Route53Resolver',
                MetricData=[
                    {
                        'MetricName': 'IPAddressStatus',
                        'Value': ip_status,
                        'Unit': 'Count',
                        'Dimensions': [
                            {'Name': 'EndpointId', 'Value': endpoint_id},
                            {'Name': 'IPAddress', 'Value': ip_address['Ip']}
                        ]
                    }
                ]
            )

monitor_resolver_endpoints()
```

---

## 包括的なトラブルシューティング手順

### 1. 問題の切り分け手順

**レイヤー別診断アプローチ**
```bash
# Layer 1: 物理層
aws directconnect describe-connections
aws ec2 describe-vpn-connections

# Layer 2: データリンク層
aws ec2 describe-network-interfaces
aws ec2 describe-vpc-peering-connections

# Layer 3: ネットワーク層
aws ec2 describe-route-tables
aws ec2 search-transit-gateway-routes

# Layer 4: トランスポート層
aws ec2 describe-security-groups
aws ec2 describe-network-acls

# Layer 7: アプリケーション層
aws route53resolver list-resolver-rules
aws elbv2 describe-load-balancers
```

### 2. 自動診断スクリプト

```python
#!/usr/bin/env python3
"""
AWS Network Diagnostic Tool
包括的なネットワーク診断を実行
"""

import boto3
import json
import sys
from datetime import datetime

class NetworkDiagnostics:
    def __init__(self):
        self.ec2 = boto3.client('ec2')
        self.dx = boto3.client('directconnect')
        self.route53resolver = boto3.client('route53resolver')
        self.elbv2 = boto3.client('elbv2')
        
    def run_full_diagnostics(self, vpc_id=None):
        """完全な診断を実行"""
        print("=== AWS Network Diagnostics ===")
        print(f"Started at: {datetime.now()}")
        
        # 基本的なネットワーク情報の収集
        self.check_vpc_configuration(vpc_id)
        self.check_route_tables(vpc_id)
        self.check_security_groups(vpc_id)
        self.check_network_acls(vpc_id)
        
        # 接続性のチェック
        self.check_peering_connections(vpc_id)
        self.check_transit_gateway_attachments(vpc_id)
        self.check_direct_connect()
        self.check_vpn_connections()
        
        # 高度な診断
        self.check_dns_resolution()
        self.check_load_balancers()
        
        print("=== Diagnostics Complete ===")
        
    def check_vpc_configuration(self, vpc_id=None):
        """VPC の基本設定をチェック"""
        print("\n--- VPC Configuration Check ---")
        
        if vpc_id:
            vpcs = self.ec2.describe_vpcs(VpcIds=[vpc_id])['Vpcs']
        else:
            vpcs = self.ec2.describe_vpcs()['Vpcs']
            
        for vpc in vpcs:
            vpc_id = vpc['VpcId']
            cidr = vpc['CidrBlock']
            
            # DNS 設定の確認
            dns_hostnames = self.ec2.describe_vpc_attribute(
                VpcId=vpc_id, Attribute='enableDnsHostnames'
            )['EnableDnsHostnames']['Value']
            
            dns_support = self.ec2.describe_vpc_attribute(
                VpcId=vpc_id, Attribute='enableDnsSupport'
            )['EnableDnsSupport']['Value']
            
            print(f"VPC {vpc_id}: {cidr}")
            print(f"  DNS Hostnames: {dns_hostnames}")
            print(f"  DNS Support: {dns_support}")
            
            if not dns_hostnames or not dns_support:
                print(f"  ⚠️  DNS settings may cause issues")
                
    def check_route_tables(self, vpc_id=None):
        """ルートテーブルをチェック"""
        print("\n--- Route Tables Check ---")
        
        filters = [{'Name': 'vpc-id', 'Values': [vpc_id]}] if vpc_id else []
        route_tables = self.ec2.describe_route_tables(Filters=filters)['RouteTables']
        
        for rt in route_tables:
            rt_id = rt['RouteTableId']
            vpc_id = rt['VpcId']
            
            print(f"Route Table {rt_id} (VPC: {vpc_id})")
            
            # ルートの確認
            for route in rt['Routes']:
                destination = route.get('DestinationCidrBlock', route.get('DestinationPrefixListId', 'N/A'))
                target = route.get('GatewayId', route.get('TransitGatewayId', route.get('VpcPeeringConnectionId', 'N/A')))
                state = route.get('State', 'N/A')
                
                print(f"  {destination} -> {target} ({state})")
                
                if state == 'blackhole':
                    print(f"  ⚠️  Blackhole route detected")
                    
    def check_security_groups(self, vpc_id=None):
        """セキュリティグループをチェック"""
        print("\n--- Security Groups Check ---")
        
        filters = [{'Name': 'vpc-id', 'Values': [vpc_id]}] if vpc_id else []
        security_groups = self.ec2.describe_security_groups(Filters=filters)['SecurityGroups']
        
        for sg in security_groups:
            sg_id = sg['GroupId']
            sg_name = sg['GroupName']
            
            print(f"Security Group {sg_id} ({sg_name})")
            
            # 過度に緩い設定のチェック
            for rule in sg['IpPermissions']:
                for ip_range in rule.get('IpRanges', []):
                    if ip_range.get('CidrIp') == '0.0.0.0/0':
                        protocol = rule.get('IpProtocol', 'N/A')
                        from_port = rule.get('FromPort', 'N/A')
                        to_port = rule.get('ToPort', 'N/A')
                        print(f"  ⚠️  Open to 0.0.0.0/0: {protocol}:{from_port}-{to_port}")
                        
    def check_network_acls(self, vpc_id=None):
        """Network ACL をチェック"""
        print("\n--- Network ACLs Check ---")
        
        filters = [{'Name': 'vpc-id', 'Values': [vpc_id]}] if vpc_id else []
        network_acls = self.ec2.describe_network_acls(Filters=filters)['NetworkAcls']
        
        for nacl in network_acls:
            nacl_id = nacl['NetworkAclId']
            is_default = nacl['IsDefault']
            
            print(f"Network ACL {nacl_id} (Default: {is_default})")
            
            # DENY ルールの確認
            for entry in nacl['Entries']:
                if entry['RuleAction'] == 'deny':
                    rule_number = entry['RuleNumber']
                    cidr = entry.get('CidrBlock', 'N/A')
                    protocol = entry.get('Protocol', 'N/A')
                    print(f"  DENY Rule {rule_number}: {cidr} (Protocol: {protocol})")
                    
    def check_peering_connections(self, vpc_id=None):
        """VPC Peering をチェック"""
        print("\n--- VPC Peering Connections Check ---")
        
        filters = []
        if vpc_id:
            filters = [
                {'Name': 'requester-vpc-info.vpc-id', 'Values': [vpc_id]},
                {'Name': 'accepter-vpc-info.vpc-id', 'Values': [vpc_id]}
            ]
            
        peering_connections = self.ec2.describe_vpc_peering_connections(Filters=filters)['VpcPeeringConnections']
        
        for pcx in peering_connections:
            pcx_id = pcx['VpcPeeringConnectionId']
            status = pcx['Status']['Code']
            
            requester_vpc = pcx['RequesterVpcInfo']['VpcId']
            accepter_vpc = pcx['AccepterVpcInfo']['VpcId']
            
            print(f"Peering Connection {pcx_id}: {requester_vpc} <-> {accepter_vpc} ({status})")
            
            if status != 'active':
                print(f"  ⚠️  Connection is not active")
                
    def check_transit_gateway_attachments(self, vpc_id=None):
        """Transit Gateway Attachment をチェック"""
        print("\n--- Transit Gateway Attachments Check ---")
        
        filters = [{'Name': 'vpc-id', 'Values': [vpc_id]}] if vpc_id else []
        attachments = self.ec2.describe_transit_gateway_attachments(Filters=filters)['TransitGatewayAttachments']
        
        for attachment in attachments:
            attachment_id = attachment['TransitGatewayAttachmentId']
            tgw_id = attachment['TransitGatewayId']
            state = attachment['State']
            resource_type = attachment['ResourceType']
            
            print(f"TGW Attachment {attachment_id}: {tgw_id} ({resource_type}) - {state}")
            
            if state != 'available':
                print(f"  ⚠️  Attachment is not available")
                
    def check_direct_connect(self):
        """Direct Connect をチェック"""
        print("\n--- Direct Connect Check ---")
        
        try:
            connections = self.dx.describe_connections()['connections']
            
            for conn in connections:
                conn_id = conn['connectionId']
                conn_state = conn['connectionState']
                bandwidth = conn['bandwidth']
                location = conn['location']
                
                print(f"DX Connection {conn_id}: {bandwidth} at {location} ({conn_state})")
                
                if conn_state != 'available':
                    print(f"  ⚠️  Connection is not available")
                    
            # Virtual Interface の確認
            vifs = self.dx.describe_virtual_interfaces()['virtualInterfaces']
            
            for vif in vifs:
                vif_id = vif['virtualInterfaceId']
                vif_state = vif['virtualInterfaceState']
                vif_type = vif['virtualInterfaceType']
                
                print(f"VIF {vif_id}: {vif_type} ({vif_state})")
                
                if vif_state != 'available':
                    print(f"  ⚠️  VIF is not available")
                    
        except Exception as e:
            print(f"Error checking Direct Connect: {str(e)}")
            
    def check_vpn_connections(self):
        """VPN Connection をチェック"""
        print("\n--- VPN Connections Check ---")
        
        try:
            vpn_connections = self.ec2.describe_vpn_connections()['VpnConnections']
            
            for vpn in vpn_connections:
                vpn_id = vpn['VpnConnectionId']
                state = vpn['State']
                type_val = vpn['Type']
                
                print(f"VPN Connection {vpn_id}: {type_val} ({state})")
                
                if state != 'available':
                    print(f"  ⚠️  VPN is not available")
                    
                # トンネルの状態確認
                for tunnel in vpn.get('VgwTelemetry', []):
                    tunnel_ip = tunnel['OutsideIpAddress']
                    tunnel_state = tunnel['Status']
                    
                    print(f"  Tunnel {tunnel_ip}: {tunnel_state}")
                    
                    if tunnel_state != 'UP':
                        print(f"    ⚠️  Tunnel is down")
                        
        except Exception as e:
            print(f"Error checking VPN connections: {str(e)}")
            
    def check_dns_resolution(self):
        """DNS 解決をチェック"""
        print("\n--- DNS Resolution Check ---")
        
        try:
            # Route 53 Resolver Endpoint の確認
            endpoints = self.route53resolver.list_resolver_endpoints()['ResolverEndpoints']
            
            for endpoint in endpoints:
                endpoint_id = endpoint['Id']
                status = endpoint['Status']
                direction = endpoint['Direction']
                
                print(f"Resolver Endpoint {endpoint_id}: {direction} ({status})")
                
                if status != 'OPERATIONAL':
                    print(f"  ⚠️  Endpoint is not operational")
                    
            # Resolver Rule の確認
            rules = self.route53resolver.list_resolver_rules()['ResolverRules']
            
            for rule in rules:
                rule_id = rule['Id']
                status = rule['Status']
                domain_name = rule.get('DomainName', 'N/A')
                rule_type = rule.get('RuleType', 'N/A')
                
                print(f"Resolver Rule {rule_id}: {domain_name} ({rule_type}) - {status}")
                
                if status != 'COMPLETE':
                    print(f"  ⚠️  Rule is not complete")
                    
        except Exception as e:
            print(f"Error checking DNS resolution: {str(e)}")
            
    def check_load_balancers(self):
        """Load Balancer をチェック"""
        print("\n--- Load Balancers Check ---")
        
        try:
            load_balancers = self.elbv2.describe_load_balancers()['LoadBalancers']
            
            for lb in load_balancers:
                lb_name = lb['LoadBalancerName']
                state = lb['State']['Code']
                lb_type = lb['Type']
                scheme = lb['Scheme']
                
                print(f"Load Balancer {lb_name}: {lb_type} ({scheme}) - {state}")
                
                if state != 'active':
                    print(f"  ⚠️  Load Balancer is not active")
                    
                # ターゲットグループの確認
                target_groups = self.elbv2.describe_target_groups(
                    LoadBalancerArn=lb['LoadBalancerArn']
                )['TargetGroups']
                
                for tg in target_groups:
                    tg_name = tg['TargetGroupName']
                    
                    # ターゲットの健全性確認
                    target_health = self.elbv2.describe_target_health(
                        TargetGroupArn=tg['TargetGroupArn']
                    )['TargetHealthDescriptions']
                    
                    healthy_count = sum(1 for target in target_health if target['TargetHealth']['State'] == 'healthy')
                    total_count = len(target_health)
                    
                    print(f"  Target Group {tg_name}: {healthy_count}/{total_count} healthy")
                    
                    if healthy_count < total_count:
                        print(f"    ⚠️  Some targets are unhealthy")
                        
        except Exception as e:
            print(f"Error checking load balancers: {str(e)}")

if __name__ == "__main__":
    diagnostics = NetworkDiagnostics()
    
    # 引数で VPC ID を指定可能
    vpc_id = sys.argv[1] if len(sys.argv) > 1 else None
    
    diagnostics.run_full_diagnostics(vpc_id)
```

このスクリプトを使用することで、包括的なネットワーク診断が可能になります：

```bash
# 全体の診断
python network_diagnostics.py

# 特定の VPC の診断
python network_diagnostics.py vpc-xxxxxxxx
```

---

## まとめ

このドキュメントでは、AWS Advanced Networking Specialty 試験で出題される可能性のある実践的なトラブルシューティングシナリオを詳細に解説しました。

**重要なポイント:**

1. **体系的なアプローチ** - 問題を段階的に切り分ける
2. **自動化の活用** - 監視と自動修復スクリプトの実装
3. **予防的メンテナンス** - 問題を未然に防ぐ仕組みの構築
4. **包括的な診断** - 複数のレイヤーを横断した原因分析

これらのスキルを身につけることで、実際の本番環境でのネットワーク問題にも対応できるようになります。