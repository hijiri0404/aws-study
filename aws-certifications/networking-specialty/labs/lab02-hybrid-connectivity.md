# Lab 2: ハイブリッド接続

## 🎯 学習目標

このラボでは、オンプレミス環境とAWSクラウドを接続するハイブリッドネットワーキングの実装を行います：

- VPN Gateway によるサイト間接続
- Direct Connect の設定と管理
- Transit Gateway を使った大規模ネットワーク統合
- AWS Client VPN によるリモートアクセス
- ハイブリッド DNS とルーティング

## 📋 前提条件

- AWS CLI が設定済み
- ネットワーキングの基礎知識
- [Lab 1: 高度なVPC設計](./lab01-advanced-vpc.md) の完了推奨

## 🏗️ アーキテクチャ概要

```
┌─────────────────────────────────────────────────────────────┐
│                  ハイブリッドネットワーク                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  On-Premises                     AWS Cloud                  │
│  ┌─────────────┐                ┌─────────────┐             │
│  │   Office    │                │     VPC     │             │
│  │  Network    │◄─────VPN──────►│   Subnets   │             │
│  └─────────────┘                └─────────────┘             │
│                                                             │
│  ┌─────────────┐                ┌─────────────┐             │
│  │  Data       │                │   Transit   │             │
│  │  Center     │◄───DirectConnect──Gateway────┤             │
│  └─────────────┘                └─────────────┘             │
│                                                             │
│  ┌─────────────┐                ┌─────────────┐             │
│  │   Remote    │                │   Client    │             │
│  │   Users     │◄─────VPN──────►│    VPN      │             │
│  └─────────────┘                └─────────────┘             │
└─────────────────────────────────────────────────────────────┘
```

## 🚀 Step 1: VPN Gateway によるサイト間接続

### 1.1 Customer Gateway の作成

```bash
# Customer Gateway の作成
aws ec2 create-customer-gateway \
    --type ipsec.1 \
    --public-ip 203.0.113.12 \
    --bgp-asn 65000 \
    --tag-specifications 'ResourceType=customer-gateway,Tags=[{Key=Name,Value=OnPremises-CGW}]'

# Customer Gateway ID を取得
CUSTOMER_GATEWAY_ID=$(aws ec2 describe-customer-gateways \
    --filters "Name=tag:Name,Values=OnPremises-CGW" \
    --query 'CustomerGateways[0].CustomerGatewayId' \
    --output text)

echo "Customer Gateway ID: $CUSTOMER_GATEWAY_ID"
```

### 1.2 Virtual Private Gateway の作成

```bash
# Virtual Private Gateway の作成
aws ec2 create-vpn-gateway \
    --type ipsec.1 \
    --amazon-side-asn 64512 \
    --tag-specifications 'ResourceType=vpn-gateway,Tags=[{Key=Name,Value=AWS-VGW}]'

# VPN Gateway ID を取得
VPN_GATEWAY_ID=$(aws ec2 describe-vpn-gateways \
    --filters "Name=tag:Name,Values=AWS-VGW" \
    --query 'VpnGateways[0].VpnGatewayId' \
    --output text)

echo "VPN Gateway ID: $VPN_GATEWAY_ID"

# VPC に VPN Gateway をアタッチ
VPC_ID="vpc-12345678"  # 既存のVPC ID
aws ec2 attach-vpn-gateway \
    --vpn-gateway-id $VPN_GATEWAY_ID \
    --vpc-id $VPC_ID
```

### 1.3 VPN Connection の作成

```bash
# VPN Connection の作成
aws ec2 create-vpn-connection \
    --type ipsec.1 \
    --customer-gateway-id $CUSTOMER_GATEWAY_ID \
    --vpn-gateway-id $VPN_GATEWAY_ID \
    --options StaticRoutesOnly=false \
    --tag-specifications 'ResourceType=vpn-connection,Tags=[{Key=Name,Value=OnPremises-VPN}]'

# VPN Connection ID を取得
VPN_CONNECTION_ID=$(aws ec2 describe-vpn-connections \
    --filters "Name=tag:Name,Values=OnPremises-VPN" \
    --query 'VpnConnections[0].VpnConnectionId' \
    --output text)

echo "VPN Connection ID: $VPN_CONNECTION_ID"

# VPN 設定ファイルをダウンロード
aws ec2 describe-vpn-connections \
    --vpn-connection-ids $VPN_CONNECTION_ID \
    --query 'VpnConnections[0].CustomerGatewayConfiguration' \
    --output text > vpn-config.xml

echo "VPN configuration downloaded to vpn-config.xml"
```

### 1.4 オンプレミス機器設定（Cisco ASA例）

```bash
# Cisco ASA 設定例をvpn-config.xmlから抽出して表示
cat > cisco-asa-config.txt << 'EOF'
# Cisco ASA VPN Configuration Template

# Phase 1 IKE Policy
crypto ikev1 policy 1
 authentication pre-share
 encryption aes-256
 hash sha
 group 14
 lifetime 28800

# Phase 2 IPSec Policy  
crypto ipsec ikev1 transform-set AWS-TRANSFORM-SET esp-aes-256 esp-sha-hmac
crypto ipsec security-association pmtu-aging infinite

# Crypto Map
crypto map AWS-VPN-MAP 1 match address VPN-ACL
crypto map AWS-VPN-MAP 1 set peer AWS-TUNNEL-1-IP
crypto map AWS-VPN-MAP 1 set ikev1 transform-set AWS-TRANSFORM-SET
crypto map AWS-VPN-MAP 1 set security-association lifetime seconds 3600

# Tunnel Group
tunnel-group AWS-TUNNEL-1-IP type ipsec-l2l
tunnel-group AWS-TUNNEL-1-IP ipsec-attributes
 ikev1 pre-shared-key AWS-PRE-SHARED-KEY

# Access List
access-list VPN-ACL extended permit ip 192.168.1.0 255.255.255.0 10.0.0.0 255.255.0.0

# Apply crypto map to outside interface
crypto map AWS-VPN-MAP interface outside

# Static Routes
route outside 10.0.0.0 255.255.0.0 AWS-TUNNEL-1-IP
EOF

echo "Cisco ASA configuration template created"
```

### 1.5 ルートテーブル設定

```bash
# VPN 用のルートテーブル設定
ROUTE_TABLE_ID=$(aws ec2 describe-route-tables \
    --filters "Name=vpc-id,Values=$VPC_ID" "Name=association.main,Values=true" \
    --query 'RouteTables[0].RouteTableId' \
    --output text)

# オンプレミスネットワークへのルート追加
aws ec2 create-route \
    --route-table-id $ROUTE_TABLE_ID \
    --destination-cidr-block 192.168.1.0/24 \
    --vpn-gateway-id $VPN_GATEWAY_ID

# ルート伝播を有効化
aws ec2 enable-vgw-route-propagation \
    --route-table-id $ROUTE_TABLE_ID \
    --gateway-id $VPN_GATEWAY_ID

echo "VPN routes configured"
```

## 📡 Step 2: Direct Connect の設定

### 2.1 Direct Connect Gateway の作成

```bash
# Direct Connect Gateway の作成
aws directconnect create-direct-connect-gateway \
    --name "Production-DXGW" \
    --amazon-side-asn 64512

# Direct Connect Gateway ID を取得
DXGW_ID=$(aws directconnect describe-direct-connect-gateways \
    --query 'directConnectGateways[?name==`Production-DXGW`].directConnectGatewayId' \
    --output text)

echo "Direct Connect Gateway ID: $DXGW_ID"
```

### 2.2 Virtual Interface の作成

```bash
# Private Virtual Interface の作成
cat > vif-config.json << EOF
{
    "connectionId": "dxcon-12345678",
    "ownerAccount": "123456789012",
    "vifName": "Production-Private-VIF",
    "vlan": 100,
    "bgpAsn": 65000,
    "authKey": "your-bgp-auth-key",
    "amazonAddress": "192.168.100.1/30",
    "customerAddress": "192.168.100.2/30",
    "directConnectGatewayId": "$DXGW_ID"
}
EOF

aws directconnect create-private-virtual-interface \
    --cli-input-json file://vif-config.json

# Virtual Interface ID を取得
VIF_ID=$(aws directconnect describe-virtual-interfaces \
    --query 'virtualInterfaces[?vifName==`Production-Private-VIF`].virtualInterfaceId' \
    --output text)

echo "Virtual Interface ID: $VIF_ID"
```

### 2.3 VPC Association

```bash
# VPC を Direct Connect Gateway に関連付け
aws directconnect create-direct-connect-gateway-association \
    --direct-connect-gateway-id $DXGW_ID \
    --gateway-id $VPN_GATEWAY_ID \
    --add-allowed-prefixes-to-direct-connect-gateway cidr=10.0.0.0/16

echo "VPC associated with Direct Connect Gateway"
```

### 2.4 BGP 設定確認

```bash
# BGP セッション状態確認
aws directconnect describe-virtual-interfaces \
    --virtual-interface-id $VIF_ID \
    --query 'virtualInterfaces[0].bgpPeers[0].bgpStatus'

# BGP ルート確認
aws directconnect describe-virtual-interfaces \
    --virtual-interface-id $VIF_ID \
    --query 'virtualInterfaces[0].routeFilterPrefixes'
```

## 🌐 Step 3: Transit Gateway 統合

### 3.1 Transit Gateway の作成

```bash
# Transit Gateway の作成
aws ec2 create-transit-gateway \
    --description "Hub for hybrid connectivity" \
    --options AmazonSideAsn=64512,AutoAcceptSharedAttachments=enable,DefaultRouteTableAssociation=enable,DefaultRouteTablePropagation=enable \
    --tag-specifications 'ResourceType=transit-gateway,Tags=[{Key=Name,Value=Hybrid-TGW}]'

# Transit Gateway ID を取得
TGW_ID=$(aws ec2 describe-transit-gateways \
    --filters "Name=tag:Name,Values=Hybrid-TGW" \
    --query 'TransitGateways[0].TransitGatewayId' \
    --output text)

echo "Transit Gateway ID: $TGW_ID"
```

### 3.2 VPC Attachment

```bash
# VPC を Transit Gateway にアタッチ
aws ec2 create-transit-gateway-vpc-attachment \
    --transit-gateway-id $TGW_ID \
    --vpc-id $VPC_ID \
    --subnet-ids subnet-12345678 \
    --tag-specifications 'ResourceType=transit-gateway-attachment,Tags=[{Key=Name,Value=Production-VPC-Attachment}]'

# Attachment ID を取得
TGW_VPC_ATTACHMENT_ID=$(aws ec2 describe-transit-gateway-vpc-attachments \
    --filters "Name=transit-gateway-id,Values=$TGW_ID" "Name=vpc-id,Values=$VPC_ID" \
    --query 'TransitGatewayVpcAttachments[0].TransitGatewayAttachmentId' \
    --output text)

echo "VPC Attachment ID: $TGW_VPC_ATTACHMENT_ID"
```

### 3.3 Direct Connect Gateway 接続

```bash
# Direct Connect Gateway を Transit Gateway に接続
aws ec2 create-transit-gateway-direct-connect-gateway-attachment \
    --transit-gateway-id $TGW_ID \
    --direct-connect-gateway-id $DXGW_ID \
    --tag-specifications 'ResourceType=transit-gateway-attachment,Tags=[{Key=Name,Value=DXGW-Attachment}]'

# Attachment ID を取得
TGW_DXGW_ATTACHMENT_ID=$(aws ec2 describe-transit-gateway-direct-connect-gateway-attachments \
    --filters "Name=transit-gateway-id,Values=$TGW_ID" \
    --query 'TransitGatewayDirectConnectGatewayAttachments[0].TransitGatewayAttachmentId' \
    --output text)

echo "Direct Connect Gateway Attachment ID: $TGW_DXGW_ATTACHMENT_ID"
```

### 3.4 Route Table 設定

```bash
# カスタム Route Table の作成
aws ec2 create-transit-gateway-route-table \
    --transit-gateway-id $TGW_ID \
    --tag-specifications 'ResourceType=transit-gateway-route-table,Tags=[{Key=Name,Value=Production-Routes}]'

# Route Table ID を取得
TGW_ROUTE_TABLE_ID=$(aws ec2 describe-transit-gateway-route-tables \
    --filters "Name=transit-gateway-id,Values=$TGW_ID" "Name=tag:Name,Values=Production-Routes" \
    --query 'TransitGatewayRouteTables[0].TransitGatewayRouteTableId' \
    --output text)

# Attachment を Route Table に関連付け
aws ec2 associate-transit-gateway-route-table \
    --transit-gateway-attachment-id $TGW_VPC_ATTACHMENT_ID \
    --transit-gateway-route-table-id $TGW_ROUTE_TABLE_ID

aws ec2 associate-transit-gateway-route-table \
    --transit-gateway-attachment-id $TGW_DXGW_ATTACHMENT_ID \
    --transit-gateway-route-table-id $TGW_ROUTE_TABLE_ID

# 静的ルートの追加
aws ec2 create-transit-gateway-route \
    --destination-cidr-block 192.168.0.0/16 \
    --transit-gateway-route-table-id $TGW_ROUTE_TABLE_ID \
    --transit-gateway-attachment-id $TGW_DXGW_ATTACHMENT_ID

echo "Transit Gateway routes configured"
```

## 🔐 Step 4: AWS Client VPN

### 4.1 Certificate Authority 設定

```bash
# OpenVPN Easy-RSA を使用した証明書生成
mkdir -p ~/client-vpn-certs
cd ~/client-vpn-certs

# Easy-RSA のダウンロード
curl -L https://github.com/OpenVPN/easy-rsa/releases/download/v3.0.8/EasyRSA-3.0.8.tgz | tar xz
cd EasyRSA-3.0.8

# PKI 初期化
./easyrsa init-pki

# CA 証明書作成
./easyrsa build-ca nopass

# サーバー証明書作成
./easyrsa build-server-full server nopass

# クライアント証明書作成
./easyrsa build-client-full client1.domain.tld nopass

echo "Certificates generated successfully"
```

### 4.2 ACM への証明書インポート

```bash
# サーバー証明書をACMにインポート
SERVER_CERT_ARN=$(aws acm import-certificate \
    --certificate fileb://pki/issued/server.crt \
    --private-key fileb://pki/private/server.key \
    --certificate-chain fileb://pki/ca.crt \
    --query 'CertificateArn' \
    --output text)

# クライアント証明書をACMにインポート
CLIENT_CERT_ARN=$(aws acm import-certificate \
    --certificate fileb://pki/issued/client1.domain.tld.crt \
    --private-key fileb://pki/private/client1.domain.tld.key \
    --certificate-chain fileb://pki/ca.crt \
    --query 'CertificateArn' \
    --output text)

echo "Server Certificate ARN: $SERVER_CERT_ARN"
echo "Client Certificate ARN: $CLIENT_CERT_ARN"
```

### 4.3 Client VPN Endpoint 作成

```bash
# Client VPN Endpoint の作成
aws ec2 create-client-vpn-endpoint \
    --client-cidr-block 172.16.0.0/16 \
    --server-certificate-arn $SERVER_CERT_ARN \
    --authentication-options Type=certificate-authentication,MutualAuthentication={ClientRootCertificateChainArn=$CLIENT_CERT_ARN} \
    --connection-log-options Enabled=true,CloudwatchLogGroup=ClientVPN-ConnectionLogs \
    --dns-servers 10.0.0.2 \
    --transport-protocol udp \
    --split-tunnel \
    --tag-specifications 'ResourceType=client-vpn-endpoint,Tags=[{Key=Name,Value=Remote-Access-VPN}]'

# Client VPN Endpoint ID を取得
CLIENT_VPN_ENDPOINT_ID=$(aws ec2 describe-client-vpn-endpoints \
    --filters "Name=tag:Name,Values=Remote-Access-VPN" \
    --query 'ClientVpnEndpoints[0].ClientVpnEndpointId' \
    --output text)

echo "Client VPN Endpoint ID: $CLIENT_VPN_ENDPOINT_ID"
```

### 4.4 Network Association

```bash
# サブネットをClient VPN Endpointに関連付け
aws ec2 associate-client-vpn-target-network \
    --client-vpn-endpoint-id $CLIENT_VPN_ENDPOINT_ID \
    --subnet-id subnet-12345678

# Authorization Rule の追加
aws ec2 authorize-client-vpn-ingress \
    --client-vpn-endpoint-id $CLIENT_VPN_ENDPOINT_ID \
    --target-network-cidr 10.0.0.0/16 \
    --authorize-all-groups

# インターネットアクセス用のルート追加
aws ec2 create-client-vpn-route \
    --client-vpn-endpoint-id $CLIENT_VPN_ENDPOINT_ID \
    --destination-cidr-block 0.0.0.0/0 \
    --target-vpc-subnet-id subnet-12345678 \
    --description "Internet access"

echo "Client VPN network associations configured"
```

## 🌍 Step 5: ハイブリッド DNS

### 5.1 Route 53 Resolver Endpoints

```bash
# Inbound Resolver Endpoint 作成
SECURITY_GROUP_ID=$(aws ec2 create-security-group \
    --group-name Route53-Resolver-SG \
    --description "Security group for Route53 Resolver" \
    --vpc-id $VPC_ID \
    --query 'GroupId' \
    --output text)

# DNS トラフィック許可
aws ec2 authorize-security-group-ingress \
    --group-id $SECURITY_GROUP_ID \
    --protocol tcp \
    --port 53 \
    --cidr 192.168.0.0/16

aws ec2 authorize-security-group-ingress \
    --group-id $SECURITY_GROUP_ID \
    --protocol udp \
    --port 53 \
    --cidr 192.168.0.0/16

# Inbound Endpoint 作成
aws route53resolver create-resolver-endpoint \
    --creator-request-id $(uuidgen) \
    --name "Inbound-Resolver" \
    --security-group-ids $SECURITY_GROUP_ID \
    --direction INBOUND \
    --ip-addresses SubnetId=subnet-12345678,Ip=10.0.1.100 SubnetId=subnet-87654321,Ip=10.0.2.100

# Outbound Endpoint 作成
aws route53resolver create-resolver-endpoint \
    --creator-request-id $(uuidgen) \
    --name "Outbound-Resolver" \
    --security-group-ids $SECURITY_GROUP_ID \
    --direction OUTBOUND \
    --ip-addresses SubnetId=subnet-12345678,Ip=10.0.1.200 SubnetId=subnet-87654321,Ip=10.0.2.200
```

### 5.2 Resolver Rules

```bash
# Outbound Resolver Endpoint ID を取得
OUTBOUND_RESOLVER_ID=$(aws route53resolver list-resolver-endpoints \
    --filters Name=Direction,Values=OUTBOUND \
    --query 'ResolverEndpoints[0].Id' \
    --output text)

# Resolver Rule 作成（オンプレミスドメイン用）
aws route53resolver create-resolver-rule \
    --creator-request-id $(uuidgen) \
    --name "OnPremises-Domain-Rule" \
    --rule-type FORWARD \
    --domain-name corp.example.com \
    --resolver-endpoint-id $OUTBOUND_RESOLVER_ID \
    --target-ips Ip=192.168.1.10,Port=53 Ip=192.168.1.11,Port=53

# Resolver Rule ID を取得
RESOLVER_RULE_ID=$(aws route53resolver list-resolver-rules \
    --filters Name=Name,Values=OnPremises-Domain-Rule \
    --query 'ResolverRules[0].Id' \
    --output text)

# VPC に Resolver Rule を関連付け
aws route53resolver associate-resolver-rule \
    --resolver-rule-id $RESOLVER_RULE_ID \
    --vpc-id $VPC_ID

echo "DNS resolution rules configured"
```

## 📊 Step 6: 監視とトラブルシューティング

### 6.1 VPN 接続監視

```bash
# CloudWatch メトリクス設定
cat > vpn-monitoring.json << EOF
{
    "MetricName": "TunnelState",
    "Namespace": "AWS/VPN",
    "MetricData": [
        {
            "MetricName": "TunnelState",
            "Dimensions": [
                {
                    "Name": "VpnId",
                    "Value": "$VPN_CONNECTION_ID"
                },
                {
                    "Name": "TunnelIpAddress",
                    "Value": "TUNNEL_1_IP"
                }
            ],
            "Unit": "None",
            "Value": 1
        }
    ]
}
EOF

# VPN 接続状態確認スクリプト
cat > check-vpn-status.sh << 'EOF'
#!/bin/bash

VPN_CONNECTION_ID=$1

echo "Checking VPN Connection Status..."
aws ec2 describe-vpn-connections \
    --vpn-connection-ids $VPN_CONNECTION_ID \
    --query 'VpnConnections[0].VgwTelemetry[*].{Tunnel:OutsideIpAddress,Status:Status,StatusMessage:StatusMessage}'

echo "Checking VPN Connection Routes..."
aws ec2 describe-vpn-connections \
    --vpn-connection-ids $VPN_CONNECTION_ID \
    --query 'VpnConnections[0].Routes[*].{Destination:DestinationCidrBlock,State:State,Source:Source}'
EOF

chmod +x check-vpn-status.sh
./check-vpn-status.sh $VPN_CONNECTION_ID
```

### 6.2 Direct Connect 監視

```bash
# Direct Connect 接続状態確認
cat > check-dx-status.sh << 'EOF'
#!/bin/bash

CONNECTION_ID=$1
VIF_ID=$2

echo "Checking Direct Connect Connection Status..."
aws directconnect describe-connections \
    --connection-id $CONNECTION_ID \
    --query 'connections[0].{State:connectionState,Bandwidth:bandwidth,Location:location}'

echo "Checking Virtual Interface Status..."
aws directconnect describe-virtual-interfaces \
    --virtual-interface-id $VIF_ID \
    --query 'virtualInterfaces[0].{State:virtualInterfaceState,BGP:bgpPeers[0].bgpStatus,VLAN:vlan}'

echo "Checking BGP Routes..."
aws directconnect describe-virtual-interfaces \
    --virtual-interface-id $VIF_ID \
    --query 'virtualInterfaces[0].routeFilterPrefixes[*].cidr'
EOF

chmod +x check-dx-status.sh
# ./check-dx-status.sh dxcon-12345678 $VIF_ID
```

### 6.3 ネットワーク接続テスト

```bash
# 接続テストスクリプト
cat > network-connectivity-test.sh << 'EOF'
#!/bin/bash

echo "=== Network Connectivity Test ==="

# AWS から オンプレミスへのテスト
echo "Testing connectivity from AWS to On-Premises..."
INSTANCE_ID=$(aws ec2 describe-instances \
    --filters "Name=instance-state-name,Values=running" \
    --query 'Reservations[0].Instances[0].InstanceId' \
    --output text)

if [ "$INSTANCE_ID" != "None" ]; then
    # SSM Session Manager を使用したテスト
    aws ssm send-command \
        --instance-ids $INSTANCE_ID \
        --document-name "AWS-RunShellScript" \
        --parameters 'commands=["ping -c 4 192.168.1.10", "traceroute 192.168.1.10"]'
else
    echo "No running instances found for testing"
fi

# DNS解決テスト
echo "Testing DNS resolution..."
aws ssm send-command \
    --instance-ids $INSTANCE_ID \
    --document-name "AWS-RunShellScript" \
    --parameters 'commands=["nslookup corp.example.com", "nslookup internal.corp.example.com"]'

echo "Connectivity test commands sent"
EOF

chmod +x network-connectivity-test.sh
./network-connectivity-test.sh
```

## 🧹 Step 7: リソースクリーンアップ

### 7.1 VPN リソース削除

```bash
# VPN 接続削除
aws ec2 delete-vpn-connection --vpn-connection-id $VPN_CONNECTION_ID

# VPN Gateway をVPCからデタッチ
aws ec2 detach-vpn-gateway --vpn-gateway-id $VPN_GATEWAY_ID --vpc-id $VPC_ID

# VPN Gateway 削除
aws ec2 delete-vpn-gateway --vpn-gateway-id $VPN_GATEWAY_ID

# Customer Gateway 削除
aws ec2 delete-customer-gateway --customer-gateway-id $CUSTOMER_GATEWAY_ID

echo "VPN resources cleaned up"
```

### 7.2 Direct Connect リソース削除

```bash
# Virtual Interface 削除
aws directconnect delete-virtual-interface --virtual-interface-id $VIF_ID

# Direct Connect Gateway 削除
aws directconnect delete-direct-connect-gateway --direct-connect-gateway-id $DXGW_ID

echo "Direct Connect resources cleaned up"
```

### 7.3 Transit Gateway リソース削除

```bash
# Transit Gateway Attachments 削除
aws ec2 delete-transit-gateway-vpc-attachment --transit-gateway-attachment-id $TGW_VPC_ATTACHMENT_ID
aws ec2 delete-transit-gateway-direct-connect-gateway-attachment --transit-gateway-attachment-id $TGW_DXGW_ATTACHMENT_ID

# Transit Gateway Route Table 削除
aws ec2 delete-transit-gateway-route-table --transit-gateway-route-table-id $TGW_ROUTE_TABLE_ID

# Transit Gateway 削除
aws ec2 delete-transit-gateway --transit-gateway-id $TGW_ID

echo "Transit Gateway resources cleaned up"
```

### 7.4 Client VPN リソース削除

```bash
# Client VPN Endpoint 削除
aws ec2 delete-client-vpn-endpoint --client-vpn-endpoint-id $CLIENT_VPN_ENDPOINT_ID

# ACM 証明書削除
aws acm delete-certificate --certificate-arn $SERVER_CERT_ARN
aws acm delete-certificate --certificate-arn $CLIENT_CERT_ARN

echo "Client VPN resources cleaned up"
```

## 💰 コスト計算

### 推定コスト（月額）
- **VPN Gateway**: $36.00/月
- **VPN Connection**: $36.00/月  
- **Direct Connect (1Gbps)**: $216.00/月
- **Direct Connect Gateway**: 無料
- **Transit Gateway**: $36.00/月 + データ処理料金
- **Client VPN**: $72.00/月 + 接続時間料金
- **合計**: 約 $396.00/月（基本料金）

## 📚 学習ポイント

### 重要な概念
1. **VPN vs Direct Connect**: 用途と特性の違い
2. **Transit Gateway**: 大規模ネットワーク統合
3. **BGP ルーティング**: 動的ルート交換
4. **DNS フォワーディング**: ハイブリッドDNS
5. **冗長性設計**: 複数接続による高可用性

### 実践的なスキル
- サイト間VPN設定と管理
- Direct Connect の設計と実装
- Transit Gateway による統合
- Client VPN によるリモートアクセス
- ハイブリッドDNS設定

---

**次のステップ**: [Lab 3: ロードバランシング](./lab03-load-balancing.md) では、高可用性とスケーラビリティを実現するロードバランシング技術を学習します。