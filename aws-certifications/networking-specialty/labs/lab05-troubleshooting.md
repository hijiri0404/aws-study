# Lab 5: トラブルシューティング

## 🎯 学習目標

このラボでは、AWSネットワークの包括的なトラブルシューティング手法を学習します：

- ネットワーク接続性の問題診断
- パフォーマンス問題の特定と解決
- DNS解決問題のトラブルシューティング
- ロードバランサーの問題診断
- セキュリティ関連の接続問題解決

## 📋 前提条件

- AWS CLI が設定済み
- ネットワーキングの基礎知識
- [Lab 4: セキュリティ・コンプライアンス](./lab04-security-compliance.md) の完了推奨

## 🏗️ アーキテクチャ概要

```
┌─────────────────────────────────────────────────────────────┐
│                トラブルシューティング環境                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐     │
│  │ Connectivity│    │ Performance │    │     DNS     │     │
│  │   Issues    │    │   Issues    │    │   Issues    │     │
│  │   Testing   │    │   Testing   │    │  Resolution │     │
│  └─────┬───────┘    └─────┬───────┘    └─────┬───────┘     │
│        │                  │                  │             │
│        ▼                  ▼                  ▼             │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │            診断ツールとモニタリング                        │ │
│  │   VPC Flow Logs + CloudWatch + X-Ray                   │ │
│  └─────┬───────────────────────┬───────────────────────────┘ │
│        │                       │                             │
│        ▼                       ▼                             │
│  ┌─────────────┐         ┌─────────────┐                     │
│  │  Automated  │         │   Manual    │                     │
│  │ Diagnosis   │         │  Analysis   │                     │
│  └─────────────┘         └─────────────┘                     │
└─────────────────────────────────────────────────────────────┘
```

## 🚀 Step 1: トラブルシューティング環境のセットアップ

### 1.1 テスト用VPC環境作成

```bash
# トラブルシューティング用VPC作成
TROUBLESHOOT_VPC_ID=$(aws ec2 create-vpc \
    --cidr-block 10.2.0.0/16 \
    --tag-specifications 'ResourceType=vpc,Tags=[{Key=Name,Value=Troubleshoot-VPC}]' \
    --query 'Vpc.VpcId' \
    --output text)

# インターネットゲートウェイ
IGW_ID=$(aws ec2 create-internet-gateway \
    --tag-specifications 'ResourceType=internet-gateway,Tags=[{Key=Name,Value=Troubleshoot-IGW}]' \
    --query 'InternetGateway.InternetGatewayId' \
    --output text)

aws ec2 attach-internet-gateway \
    --vpc-id $TROUBLESHOOT_VPC_ID \
    --internet-gateway-id $IGW_ID

# パブリックサブネット
PUBLIC_SUBNET=$(aws ec2 create-subnet \
    --vpc-id $TROUBLESHOOT_VPC_ID \
    --cidr-block 10.2.1.0/24 \
    --availability-zone us-east-1a \
    --tag-specifications 'ResourceType=subnet,Tags=[{Key=Name,Value=Troubleshoot-Public}]' \
    --query 'Subnet.SubnetId' \
    --output text)

# プライベートサブネット
PRIVATE_SUBNET=$(aws ec2 create-subnet \
    --vpc-id $TROUBLESHOOT_VPC_ID \
    --cidr-block 10.2.2.0/24 \
    --availability-zone us-east-1a \
    --tag-specifications 'ResourceType=subnet,Tags=[{Key=Name,Value=Troubleshoot-Private}]' \
    --query 'Subnet.SubnetId' \
    --output text)

# ルートテーブル設定
PUBLIC_RT=$(aws ec2 create-route-table \
    --vpc-id $TROUBLESHOOT_VPC_ID \
    --tag-specifications 'ResourceType=route-table,Tags=[{Key=Name,Value=Troubleshoot-Public-RT}]' \
    --query 'RouteTable.RouteTableId' \
    --output text)

aws ec2 create-route \
    --route-table-id $PUBLIC_RT \
    --destination-cidr-block 0.0.0.0/0 \
    --gateway-id $IGW_ID

aws ec2 associate-route-table \
    --subnet-id $PUBLIC_SUBNET \
    --route-table-id $PUBLIC_RT

echo "トラブルシューティング環境作成完了"
```

### 1.2 診断用インスタンス作成

```bash
# 診断用セキュリティグループ
DIAG_SG=$(aws ec2 create-security-group \
    --group-name Diagnostic-SG \
    --description "Security group for diagnostic instances" \
    --vpc-id $TROUBLESHOOT_VPC_ID \
    --query 'GroupId' \
    --output text)

# SSH、ICMP、HTTPアクセス許可
aws ec2 authorize-security-group-ingress \
    --group-id $DIAG_SG \
    --protocol tcp \
    --port 22 \
    --cidr 0.0.0.0/0

aws ec2 authorize-security-group-ingress \
    --group-id $DIAG_SG \
    --protocol icmp \
    --port -1 \
    --cidr 0.0.0.0/0

aws ec2 authorize-security-group-ingress \
    --group-id $DIAG_SG \
    --protocol tcp \
    --port 80 \
    --cidr 0.0.0.0/0

# 診断ツールインストール用User Data
cat > diagnostic-userdata.sh << 'EOF'
#!/bin/bash
yum update -y
yum install -y tcpdump nmap telnet nc bind-utils traceroute iperf3 htop

# 簡単なWebサーバー起動
yum install -y httpd
systemctl start httpd
systemctl enable httpd

# 診断用スクリプト作成
cat > /var/www/html/index.html << HTML
<!DOCTYPE html>
<html>
<head><title>Diagnostic Server</title></head>
<body>
    <h1>Network Diagnostic Server</h1>
    <p>Instance ID: $(curl -s http://169.254.169.254/latest/meta-data/instance-id)</p>
    <p>Private IP: $(curl -s http://169.254.169.254/latest/meta-data/local-ipv4)</p>
    <p>Public IP: $(curl -s http://169.254.169.254/latest/meta-data/public-ipv4)</p>
    <p>Availability Zone: $(curl -s http://169.254.169.254/latest/meta-data/placement/availability-zone)</p>
</body>
</html>
HTML

# ネットワーク診断スクリプト
cat > /home/ec2-user/network-diag.sh << 'SCRIPT'
#!/bin/bash
echo "=== Network Diagnostic Script ==="
echo "Hostname: $(hostname)"
echo "Private IP: $(curl -s http://169.254.169.254/latest/meta-data/local-ipv4)"
echo "Public IP: $(curl -s http://169.254.169.254/latest/meta-data/public-ipv4)"
echo ""
echo "=== Network Interfaces ==="
ip addr show
echo ""
echo "=== Routing Table ==="
ip route show
echo ""
echo "=== DNS Configuration ==="
cat /etc/resolv.conf
echo ""
echo "=== Active Connections ==="
netstat -tulpn
SCRIPT

chmod +x /home/ec2-user/network-diag.sh
EOF

# 診断用インスタンス起動
DIAG_INSTANCE_1=$(aws ec2 run-instances \
    --image-id ami-0c02fb55956c7d316 \
    --instance-type t3.micro \
    --key-name your-key-name \
    --security-group-ids $DIAG_SG \
    --subnet-id $PUBLIC_SUBNET \
    --associate-public-ip-address \
    --user-data file://diagnostic-userdata.sh \
    --tag-specifications 'ResourceType=instance,Tags=[{Key=Name,Value=Diag-Instance-1}]' \
    --query 'Instances[0].InstanceId' \
    --output text)

DIAG_INSTANCE_2=$(aws ec2 run-instances \
    --image-id ami-0c02fb55956c7d316 \
    --instance-type t3.micro \
    --key-name your-key-name \
    --security-group-ids $DIAG_SG \
    --subnet-id $PRIVATE_SUBNET \
    --user-data file://diagnostic-userdata.sh \
    --tag-specifications 'ResourceType=instance,Tags=[{Key=Name,Value=Diag-Instance-2}]' \
    --query 'Instances[0].InstanceId' \
    --output text)

echo "診断用インスタンス作成完了"
echo "Public Instance: $DIAG_INSTANCE_1"
echo "Private Instance: $DIAG_INSTANCE_2"
```

## 🔍 Step 2: 接続性問題のトラブルシューティング

### 2.1 接続性診断スクリプト

```bash
# 包括的接続性診断スクリプト
cat > connectivity-troubleshoot.sh << 'EOF'
#!/bin/bash

TARGET_IP=$1
TARGET_PORT=${2:-80}

if [ -z "$TARGET_IP" ]; then
    echo "Usage: $0 <target-ip> [port]"
    exit 1
fi

echo "=== Connectivity Troubleshooting to $TARGET_IP:$TARGET_PORT ==="
echo "Timestamp: $(date)"
echo ""

# 1. 基本的なping テスト
echo "1. ICMP Ping Test:"
ping -c 4 $TARGET_IP
PING_RESULT=$?
echo ""

# 2. TCP接続性テスト
echo "2. TCP Connectivity Test to port $TARGET_PORT:"
timeout 10 bash -c "</dev/tcp/$TARGET_IP/$TARGET_PORT" 2>/dev/null
TCP_RESULT=$?
if [ $TCP_RESULT -eq 0 ]; then
    echo "SUCCESS: TCP connection to $TARGET_IP:$TARGET_PORT"
else
    echo "FAILED: Cannot connect to $TARGET_IP:$TARGET_PORT"
fi
echo ""

# 3. Traceroute
echo "3. Traceroute:"
traceroute $TARGET_IP
echo ""

# 4. DNS解決
echo "4. DNS Resolution:"
nslookup $TARGET_IP
echo ""

# 5. ネットワーク設定確認
echo "5. Local Network Configuration:"
echo "Interface Configuration:"
ip addr show | grep -E "(inet |UP)"
echo ""
echo "Routing Table:"
ip route show
echo ""
echo "DNS Configuration:"
cat /etc/resolv.conf
echo ""

# 6. セキュリティグループ情報（EC2メタデータから）
echo "6. Instance Information:"
INSTANCE_ID=$(curl -s http://169.254.169.254/latest/meta-data/instance-id 2>/dev/null)
if [ $? -eq 0 ]; then
    echo "Instance ID: $INSTANCE_ID"
    echo "Private IP: $(curl -s http://169.254.169.254/latest/meta-data/local-ipv4)"
    echo "Public IP: $(curl -s http://169.254.169.254/latest/meta-data/public-ipv4)"
    echo "VPC ID: $(curl -s http://169.254.169.254/latest/meta-data/network/interfaces/macs/$(curl -s http://169.254.169.254/latest/meta-data/mac)/vpc-id)"
    echo "Subnet ID: $(curl -s http://169.254.169.254/latest/meta-data/network/interfaces/macs/$(curl -s http://169.254.169.254/latest/meta-data/mac)/subnet-id)"
fi
echo ""

# 7. ポートスキャン
echo "7. Port Scan (common ports):"
for port in 22 80 443 3389; do
    timeout 3 bash -c "</dev/tcp/$TARGET_IP/$port" 2>/dev/null
    if [ $? -eq 0 ]; then
        echo "Port $port: OPEN"
    else
        echo "Port $port: CLOSED/FILTERED"
    fi
done
echo ""

# 8. 結果サマリー
echo "=== SUMMARY ==="
if [ $PING_RESULT -eq 0 ]; then
    echo "✓ ICMP connectivity: SUCCESS"
else
    echo "✗ ICMP connectivity: FAILED"
fi

if [ $TCP_RESULT -eq 0 ]; then
    echo "✓ TCP connectivity to port $TARGET_PORT: SUCCESS"
else
    echo "✗ TCP connectivity to port $TARGET_PORT: FAILED"
fi

echo ""
echo "=== TROUBLESHOOTING RECOMMENDATIONS ==="
if [ $PING_RESULT -ne 0 ]; then
    echo "- Check Security Groups for ICMP rules"
    echo "- Check Network ACLs for ICMP rules"
    echo "- Verify target instance is running"
    echo "- Check routing tables"
fi

if [ $TCP_RESULT -ne 0 ]; then
    echo "- Check Security Groups for port $TARGET_PORT rules"
    echo "- Check Network ACLs for port $TARGET_PORT rules"
    echo "- Verify service is listening on port $TARGET_PORT"
    echo "- Check local firewall settings"
fi
EOF

chmod +x connectivity-troubleshoot.sh

echo "接続性診断スクリプト作成完了"
```

### 2.2 AWS CLI を使った詳細診断

```bash
# AWS CLI診断スクリプト
cat > aws-network-diag.sh << 'EOF'
#!/bin/bash

INSTANCE_ID=$1

if [ -z "$INSTANCE_ID" ]; then
    echo "Usage: $0 <instance-id>"
    exit 1
fi

echo "=== AWS Network Diagnostics for $INSTANCE_ID ==="
echo ""

# 1. インスタンス情報
echo "1. Instance Details:"
aws ec2 describe-instances \
    --instance-ids $INSTANCE_ID \
    --query 'Reservations[0].Instances[0].{State:State.Name,VPC:VpcId,Subnet:SubnetId,SecurityGroups:SecurityGroups[*].GroupId,PrivateIP:PrivateIpAddress,PublicIP:PublicIpAddress}' \
    --output table
echo ""

# 2. セキュリティグループ詳細
echo "2. Security Group Rules:"
SG_IDS=$(aws ec2 describe-instances \
    --instance-ids $INSTANCE_ID \
    --query 'Reservations[0].Instances[0].SecurityGroups[*].GroupId' \
    --output text)

for sg in $SG_IDS; do
    echo "Security Group: $sg"
    aws ec2 describe-security-groups \
        --group-ids $sg \
        --query 'SecurityGroups[0].IpPermissions[*].{Protocol:IpProtocol,FromPort:FromPort,ToPort:ToPort,Sources:IpRanges[*].CidrIp}' \
        --output table
    echo ""
done

# 3. サブネット情報
echo "3. Subnet Configuration:"
SUBNET_ID=$(aws ec2 describe-instances \
    --instance-ids $INSTANCE_ID \
    --query 'Reservations[0].Instances[0].SubnetId' \
    --output text)

aws ec2 describe-subnets \
    --subnet-ids $SUBNET_ID \
    --query 'Subnets[0].{SubnetId:SubnetId,CIDR:CidrBlock,AZ:AvailabilityZone,MapPublicIP:MapPublicIpOnLaunch,RouteTable:Tags[?Key==`Name`].Value}' \
    --output table
echo ""

# 4. ルートテーブル確認
echo "4. Route Table:"
RT_ID=$(aws ec2 describe-route-tables \
    --filters "Name=association.subnet-id,Values=$SUBNET_ID" \
    --query 'RouteTables[0].RouteTableId' \
    --output text)

aws ec2 describe-route-tables \
    --route-table-ids $RT_ID \
    --query 'RouteTables[0].Routes[*].{Destination:DestinationCidrBlock,Gateway:GatewayId,State:State}' \
    --output table
echo ""

# 5. Network ACL確認
echo "5. Network ACL Rules:"
VPC_ID=$(aws ec2 describe-instances \
    --instance-ids $INSTANCE_ID \
    --query 'Reservations[0].Instances[0].VpcId' \
    --output text)

NACL_ID=$(aws ec2 describe-network-acls \
    --filters "Name=association.subnet-id,Values=$SUBNET_ID" \
    --query 'NetworkAcls[0].NetworkAclId' \
    --output text)

echo "Inbound Rules:"
aws ec2 describe-network-acls \
    --network-acl-ids $NACL_ID \
    --query 'NetworkAcls[0].Entries[?Egress==`false`].{Rule:RuleNumber,Protocol:Protocol,Port:PortRange.From,CIDR:CidrBlock,Action:RuleAction}' \
    --output table

echo "Outbound Rules:"
aws ec2 describe-network-acls \
    --network-acl-ids $NACL_ID \
    --query 'NetworkAcls[0].Entries[?Egress==`true`].{Rule:RuleNumber,Protocol:Protocol,Port:PortRange.From,CIDR:CidrBlock,Action:RuleAction}' \
    --output table
echo ""

# 6. VPC Flow Logs確認
echo "6. VPC Flow Logs Status:"
aws ec2 describe-flow-logs \
    --filters "Name=resource-id,Values=$VPC_ID" \
    --query 'FlowLogs[*].{Status:FlowLogStatus,LogGroup:LogGroupName,ResourceId:ResourceId}' \
    --output table
EOF

chmod +x aws-network-diag.sh

echo "AWS診断スクリプト作成完了"
```

## 📊 Step 3: パフォーマンス問題のトラブルシューティング

### 3.1 ネットワークパフォーマンステスト

```bash
# パフォーマンステストスクリプト
cat > performance-test.sh << 'EOF'
#!/bin/bash

TARGET_HOST=$1
TEST_DURATION=${2:-30}

if [ -z "$TARGET_HOST" ]; then
    echo "Usage: $0 <target-host> [duration-seconds]"
    exit 1
fi

echo "=== Network Performance Testing to $TARGET_HOST ==="
echo "Test Duration: $TEST_DURATION seconds"
echo "Start Time: $(date)"
echo ""

# 1. レイテンシテスト
echo "1. Latency Test (10 pings):"
ping -c 10 $TARGET_HOST | tail -1
echo ""

# 2. 帯域幅テスト（iperf3が利用可能な場合）
echo "2. Bandwidth Test:"
if command -v iperf3 &> /dev/null; then
    echo "Running iperf3 client test..."
    iperf3 -c $TARGET_HOST -t $TEST_DURATION -f M 2>/dev/null || echo "iperf3 server not available on target"
else
    echo "iperf3 not installed. Installing..."
    if command -v yum &> /dev/null; then
        sudo yum install -y iperf3
    elif command -v apt &> /dev/null; then
        sudo apt update && sudo apt install -y iperf3
    fi
    
    # 代替として wget/curl でHTTPスループットテスト
    echo "HTTP Download Test:"
    time curl -o /dev/null -s $TARGET_HOST/test-file-10mb 2>/dev/null || echo "No test file available"
fi
echo ""

# 3. 継続的な接続性監視
echo "3. Connection Stability Test:"
PACKET_LOSS=0
TOTAL_TESTS=0

for i in $(seq 1 10); do
    ping -c 1 -W 2 $TARGET_HOST > /dev/null 2>&1
    if [ $? -ne 0 ]; then
        ((PACKET_LOSS++))
    fi
    ((TOTAL_TESTS++))
    sleep 1
done

LOSS_PERCENTAGE=$(( PACKET_LOSS * 100 / TOTAL_TESTS ))
echo "Packet Loss: $LOSS_PERCENTAGE% ($PACKET_LOSS/$TOTAL_TESTS)"
echo ""

# 4. DNS解決時間
echo "4. DNS Resolution Time:"
time nslookup $TARGET_HOST > /dev/null 2>&1
echo ""

# 5. TCP接続時間測定
echo "5. TCP Connection Time:"
time timeout 5 bash -c "</dev/tcp/$TARGET_HOST/80" 2>/dev/null
echo ""

# 6. Traceroute with timing
echo "6. Network Path Analysis:"
traceroute -n $TARGET_HOST 2>/dev/null | head -15
echo ""

# 7. パフォーマンス問題の分析
echo "=== Performance Analysis ==="
if [ $LOSS_PERCENTAGE -gt 5 ]; then
    echo "⚠ HIGH PACKET LOSS DETECTED ($LOSS_PERCENTAGE%)"
    echo "  - Check network congestion"
    echo "  - Verify security group rules"
    echo "  - Check target instance CPU/memory usage"
fi

if [ $LOSS_PERCENTAGE -le 1 ]; then
    echo "✓ Network stability: GOOD"
else
    echo "⚠ Network stability: DEGRADED"
fi

echo ""
echo "=== Recommendations ==="
echo "- Monitor CloudWatch metrics for network performance"
echo "- Check EC2 instance types for network performance limits"
echo "- Consider Enhanced Networking for better performance"
echo "- Review security groups and NACLs for unnecessary restrictions"
EOF

chmod +x performance-test.sh

echo "パフォーマンステストスクリプト作成完了"
```

### 3.2 CloudWatch メトリクス分析

```bash
# CloudWatch メトリクス分析スクリプト
cat > cloudwatch-network-analysis.py << 'EOF'
import boto3
import json
from datetime import datetime, timedelta

class NetworkMetricsAnalyzer:
    def __init__(self):
        self.cloudwatch = boto3.client('cloudwatch')
        self.ec2 = boto3.client('ec2')
    
    def analyze_instance_network_metrics(self, instance_id, hours=1):
        """インスタンスのネットワークメトリクス分析"""
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=hours)
        
        metrics = [
            'NetworkIn',
            'NetworkOut', 
            'NetworkPacketsIn',
            'NetworkPacketsOut'
        ]
        
        results = {}
        
        for metric in metrics:
            response = self.cloudwatch.get_metric_statistics(
                Namespace='AWS/EC2',
                MetricName=metric,
                Dimensions=[
                    {
                        'Name': 'InstanceId',
                        'Value': instance_id
                    }
                ],
                StartTime=start_time,
                EndTime=end_time,
                Period=300,
                Statistics=['Average', 'Maximum', 'Sum']
            )
            
            results[metric] = response['Datapoints']
        
        return results
    
    def analyze_load_balancer_metrics(self, load_balancer_name, hours=1):
        """ロードバランサーメトリクス分析"""
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=hours)
        
        alb_metrics = [
            'TargetResponseTime',
            'RequestCount',
            'HTTPCode_Target_2XX_Count',
            'HTTPCode_Target_4XX_Count',
            'HTTPCode_Target_5XX_Count',
            'HealthyHostCount',
            'UnHealthyHostCount'
        ]
        
        results = {}
        
        for metric in alb_metrics:
            response = self.cloudwatch.get_metric_statistics(
                Namespace='AWS/ApplicationELB',
                MetricName=metric,
                Dimensions=[
                    {
                        'Name': 'LoadBalancer',
                        'Value': load_balancer_name
                    }
                ],
                StartTime=start_time,
                EndTime=end_time,
                Period=300,
                Statistics=['Average', 'Maximum', 'Sum']
            )
            
            results[metric] = response['Datapoints']
        
        return results
    
    def detect_performance_issues(self, metrics):
        """パフォーマンス問題の検出"""
        issues = []
        
        # ネットワーク使用率チェック
        if 'NetworkIn' in metrics:
            max_network_in = max([dp['Maximum'] for dp in metrics['NetworkIn']] or [0])
            if max_network_in > 1000000000:  # 1GB/s
                issues.append("High network input detected")
        
        # パケットロスの推定
        if 'NetworkPacketsIn' in metrics and 'NetworkPacketsOut' in metrics:
            total_in = sum([dp['Sum'] for dp in metrics['NetworkPacketsIn']] or [0])
            total_out = sum([dp['Sum'] for dp in metrics['NetworkPacketsOut']] or [0])
            
            if total_in > 0 and total_out > 0:
                ratio = total_out / total_in
                if ratio < 0.95:  # 5%以上のパケットロス
                    issues.append(f"Potential packet loss detected (ratio: {ratio:.2f})")
        
        return issues
    
    def generate_report(self, instance_id):
        """パフォーマンスレポート生成"""
        print(f"=== Network Performance Report for {instance_id} ===")
        print(f"Analysis time: {datetime.utcnow()}")
        print()
        
        # メトリクス取得
        metrics = self.analyze_instance_network_metrics(instance_id)
        
        # 問題検出
        issues = self.detect_performance_issues(metrics)
        
        if issues:
            print("⚠ ISSUES DETECTED:")
            for issue in issues:
                print(f"  - {issue}")
        else:
            print("✓ No performance issues detected")
        
        print()
        print("=== Metric Summary ===")
        for metric_name, datapoints in metrics.items():
            if datapoints:
                avg_value = sum([dp['Average'] for dp in datapoints]) / len(datapoints)
                max_value = max([dp['Maximum'] for dp in datapoints])
                print(f"{metric_name}:")
                print(f"  Average: {avg_value:.2f}")
                print(f"  Maximum: {max_value:.2f}")
            else:
                print(f"{metric_name}: No data available")
        
        return metrics, issues

# 使用例
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) != 2:
        print("Usage: python cloudwatch-network-analysis.py <instance-id>")
        sys.exit(1)
    
    analyzer = NetworkMetricsAnalyzer()
    instance_id = sys.argv[1]
    
    metrics, issues = analyzer.generate_report(instance_id)
EOF

echo "CloudWatch分析スクリプト作成完了"
```

## 🌐 Step 4: DNS問題のトラブルシューティング

### 4.1 DNS診断スクリプト

```bash
# DNS診断スクリプト
cat > dns-troubleshoot.sh << 'EOF'
#!/bin/bash

DOMAIN=$1

if [ -z "$DOMAIN" ]; then
    echo "Usage: $0 <domain-name>"
    exit 1
fi

echo "=== DNS Troubleshooting for $DOMAIN ==="
echo "Timestamp: $(date)"
echo ""

# 1. 基本的なDNS解決
echo "1. Basic DNS Resolution:"
nslookup $DOMAIN
echo ""

# 2. 各レコードタイプの確認
echo "2. DNS Record Types:"
for record_type in A AAAA CNAME MX TXT NS; do
    echo "$record_type Records:"
    dig $DOMAIN $record_type +short
    echo ""
done

# 3. DNS解決経路の確認
echo "3. DNS Resolution Path:"
dig $DOMAIN +trace +short
echo ""

# 4. 複数のDNSサーバーでテスト
echo "4. Testing Different DNS Servers:"
dns_servers=("8.8.8.8" "1.1.1.1" "169.254.169.253")
for dns in "${dns_servers[@]}"; do
    echo "Testing with DNS: $dns"
    dig @$dns $DOMAIN +short
    echo ""
done

# 5. 逆引きDNS
echo "5. Reverse DNS Lookup:"
IP=$(dig $DOMAIN +short | head -1)
if [[ $IP =~ ^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
    echo "Reverse lookup for $IP:"
    dig -x $IP +short
else
    echo "Could not resolve IP for reverse lookup"
fi
echo ""

# 6. DNS応答時間測定
echo "6. DNS Response Time:"
time dig $DOMAIN > /dev/null 2>&1
echo ""

# 7. ローカルDNS設定確認
echo "7. Local DNS Configuration:"
echo "Current DNS servers:"
cat /etc/resolv.conf
echo ""

# 8. DNS キャッシュの確認と管理
echo "8. DNS Cache Management:"
if command -v systemd-resolve &> /dev/null; then
    echo "systemd-resolved statistics:"
    systemd-resolve --statistics
    echo ""
    echo "Flushing DNS cache..."
    sudo systemd-resolve --flush-caches
elif command -v nscd &> /dev/null; then
    echo "Flushing nscd cache..."
    sudo nscd -i hosts
fi

# 9. Route 53 Resolver の確認（EC2の場合）
echo "9. Route 53 Resolver Check:"
INSTANCE_ID=$(curl -s http://169.254.169.254/latest/meta-data/instance-id 2>/dev/null)
if [ $? -eq 0 ]; then
    VPC_ID=$(curl -s http://169.254.169.254/latest/meta-data/network/interfaces/macs/$(curl -s http://169.254.169.254/latest/meta-data/mac)/vpc-id)
    echo "VPC DNS Resolution: Enabled"
    echo "VPC DNS Hostnames: Check with AWS CLI"
    
    # VPC +2 アドレス（Route 53 Resolver）をテスト
    VPC_CIDR=$(aws ec2 describe-vpcs --vpc-ids $VPC_ID --query 'Vpcs[0].CidrBlock' --output text 2>/dev/null)
    if [ $? -eq 0 ]; then
        VPC_DNS_IP=$(echo $VPC_CIDR | sed 's/\.[0-9]*\/[0-9]*/\.2/')
        echo "Testing VPC DNS Resolver ($VPC_DNS_IP):"
        dig @$VPC_DNS_IP $DOMAIN +short
    fi
fi
echo ""

# 10. DNS問題の診断と推奨事項
echo "=== DNS Troubleshooting Summary ==="
if dig $DOMAIN +short > /dev/null 2>&1; then
    echo "✓ DNS resolution: SUCCESS"
else
    echo "✗ DNS resolution: FAILED"
    echo ""
    echo "Troubleshooting recommendations:"
    echo "- Check /etc/resolv.conf configuration"
    echo "- Verify network connectivity to DNS servers"
    echo "- Check if domain exists and is properly configured"
    echo "- For AWS EC2: Verify VPC DNS resolution settings"
    echo "- Check security groups for UDP port 53"
    echo "- Consider using Route 53 Resolver for hybrid DNS"
fi
EOF

chmod +x dns-troubleshoot.sh

echo "DNS診断スクリプト作成完了"
```

### 4.2 Route 53 DNS診断

```bash
# Route 53 専用診断スクリプト
cat > route53-troubleshoot.sh << 'EOF'
#!/bin/bash

HOSTED_ZONE_ID=$1
DOMAIN_NAME=$2

if [ -z "$HOSTED_ZONE_ID" ] || [ -z "$DOMAIN_NAME" ]; then
    echo "Usage: $0 <hosted-zone-id> <domain-name>"
    exit 1
fi

echo "=== Route 53 DNS Troubleshooting ==="
echo "Hosted Zone: $HOSTED_ZONE_ID"
echo "Domain: $DOMAIN_NAME"
echo ""

# 1. Hosted Zone情報
echo "1. Hosted Zone Information:"
aws route53 get-hosted-zone --id $HOSTED_ZONE_ID
echo ""

# 2. DNS レコード一覧
echo "2. DNS Records in Hosted Zone:"
aws route53 list-resource-record-sets --hosted-zone-id $HOSTED_ZONE_ID --output table
echo ""

# 3. 特定のレコードの詳細
echo "3. Specific Record Details for $DOMAIN_NAME:"
aws route53 list-resource-record-sets \
    --hosted-zone-id $HOSTED_ZONE_ID \
    --query "ResourceRecordSets[?Name=='$DOMAIN_NAME.']" \
    --output table
echo ""

# 4. Health Check 状況
echo "4. Health Checks:"
HEALTH_CHECKS=$(aws route53 list-health-checks --query 'HealthChecks[*].Id' --output text)
if [ -n "$HEALTH_CHECKS" ]; then
    for hc_id in $HEALTH_CHECKS; do
        echo "Health Check ID: $hc_id"
        aws route53 get-health-check-status --health-check-id $hc_id
        echo ""
    done
else
    echo "No health checks configured"
fi
echo ""

# 5. Query Logging設定確認
echo "5. Query Logging Configuration:"
aws route53 list-query-logging-configs \
    --hosted-zone-id $HOSTED_ZONE_ID \
    --output table
echo ""

# 6. DNS解決テスト
echo "6. DNS Resolution Test:"
echo "Testing from different locations..."

# AWS CLI を使用したDNS解決テスト
aws route53 test-dns-answer \
    --hosted-zone-id $HOSTED_ZONE_ID \
    --record-name $DOMAIN_NAME \
    --record-type A \
    --resolver-ip 8.8.8.8
echo ""

# 7. Route 53 Resolver Rules（Private Hosted Zoneの場合）
echo "7. Route 53 Resolver Rules:"
aws route53resolver list-resolver-rules \
    --query 'ResolverRules[*].{Id:Id,DomainName:DomainName,RuleType:RuleType,Status:Status}' \
    --output table
echo ""

# 8. DNS問題の診断
echo "=== Route 53 Diagnostics Summary ==="

# レコード存在確認
RECORD_EXISTS=$(aws route53 list-resource-record-sets \
    --hosted-zone-id $HOSTED_ZONE_ID \
    --query "ResourceRecordSets[?Name=='$DOMAIN_NAME.'].Name" \
    --output text)

if [ -n "$RECORD_EXISTS" ]; then
    echo "✓ DNS record exists in Route 53"
else
    echo "✗ DNS record not found in Route 53"
    echo "  - Check if record was created correctly"
    echo "  - Verify hosted zone ID"
    echo "  - Check record name format (should end with .)"
fi

# Name Server確認
echo ""
echo "Name Server Verification:"
aws route53 get-hosted-zone \
    --id $HOSTED_ZONE_ID \
    --query 'DelegationSet.NameServers' \
    --output table

echo ""
echo "Recommended checks:"
echo "- Verify domain delegation to Route 53 name servers"
echo "- Check TTL values for record updates"
echo "- Review query patterns in CloudWatch metrics"
echo "- Monitor Route 53 health check status"
EOF

chmod +x route53-troubleshoot.sh

echo "Route 53診断スクリプト作成完了"
```

## ⚖️ Step 5: ロードバランサー問題のトラブルシューティング

### 5.1 ALB/NLB診断スクリプト

```bash
# ロードバランサー診断スクリプト
cat > load-balancer-troubleshoot.sh << 'EOF'
#!/bin/bash

LB_ARN=$1

if [ -z "$LB_ARN" ]; then
    echo "Usage: $0 <load-balancer-arn>"
    exit 1
fi

echo "=== Load Balancer Troubleshooting ==="
echo "Load Balancer ARN: $LB_ARN"
echo ""

# 1. ロードバランサー基本情報
echo "1. Load Balancer Information:"
aws elbv2 describe-load-balancers \
    --load-balancer-arns $LB_ARN \
    --query 'LoadBalancers[0].{Name:LoadBalancerName,State:State.Code,Type:Type,Scheme:Scheme,VPC:VpcId,AZ:AvailabilityZones[*].ZoneName}' \
    --output table
echo ""

# 2. リスナー設定
echo "2. Listener Configuration:"
aws elbv2 describe-listeners \
    --load-balancer-arn $LB_ARN \
    --query 'Listeners[*].{Port:Port,Protocol:Protocol,DefaultAction:DefaultActions[0].Type}' \
    --output table
echo ""

# 3. ターゲットグループとヘルス状態
echo "3. Target Groups and Health Status:"
TARGET_GROUPS=$(aws elbv2 describe-target-groups \
    --load-balancer-arn $LB_ARN \
    --query 'TargetGroups[*].TargetGroupArn' \
    --output text)

for tg_arn in $TARGET_GROUPS; do
    echo "Target Group: $(basename $tg_arn)"
    
    # ターゲットグループ詳細
    aws elbv2 describe-target-groups \
        --target-group-arns $tg_arn \
        --query 'TargetGroups[0].{Port:Port,Protocol:Protocol,HealthCheckPath:HealthCheckPath,HealthCheckIntervalSeconds:HealthCheckIntervalSeconds}' \
        --output table
    
    # ターゲットヘルス状態
    echo "Target Health Status:"
    aws elbv2 describe-target-health \
        --target-group-arn $tg_arn \
        --query 'TargetHealthDescriptions[*].{Target:Target.Id,Port:Target.Port,Health:TargetHealth.State,Reason:TargetHealth.Reason}' \
        --output table
    echo ""
done

# 4. セキュリティグループ確認
echo "4. Security Group Analysis:"
SECURITY_GROUPS=$(aws elbv2 describe-load-balancers \
    --load-balancer-arns $LB_ARN \
    --query 'LoadBalancers[0].SecurityGroups' \
    --output text)

for sg in $SECURITY_GROUPS; do
    echo "Security Group: $sg"
    aws ec2 describe-security-groups \
        --group-ids $sg \
        --query 'SecurityGroups[0].IpPermissions[*].{Protocol:IpProtocol,FromPort:FromPort,ToPort:ToPort,Sources:IpRanges[*].CidrIp}' \
        --output table
    echo ""
done

# 5. ロードバランサーアクセスログ設定
echo "5. Access Logs Configuration:"
aws elbv2 describe-load-balancer-attributes \
    --load-balancer-arn $LB_ARN \
    --query 'Attributes[?Key==`access_logs.s3.enabled` || Key==`access_logs.s3.bucket`]' \
    --output table
echo ""

# 6. CloudWatch メトリクス確認
echo "6. CloudWatch Metrics (Last 1 hour):"
LB_NAME=$(aws elbv2 describe-load-balancers \
    --load-balancer-arns $LB_ARN \
    --query 'LoadBalancers[0].LoadBalancerName' \
    --output text)

METRICS=("RequestCount" "TargetResponseTime" "HTTPCode_Target_2XX_Count" "HTTPCode_Target_4XX_Count" "HTTPCode_Target_5XX_Count")

for metric in "${METRICS[@]}"; do
    echo "$metric:"
    aws cloudwatch get-metric-statistics \
        --namespace AWS/ApplicationELB \
        --metric-name $metric \
        --dimensions Name=LoadBalancer,Value=$LB_NAME \
        --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
        --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
        --period 300 \
        --statistics Sum Average \
        --query 'Datapoints[*].{Time:Timestamp,Sum:Sum,Average:Average}' \
        --output table | tail -5
    echo ""
done

# 7. 問題診断と推奨事項
echo "=== Troubleshooting Analysis ==="

# アンヘルシーターゲットの確認
UNHEALTHY_TARGETS=0
for tg_arn in $TARGET_GROUPS; do
    UNHEALTHY=$(aws elbv2 describe-target-health \
        --target-group-arn $tg_arn \
        --query 'TargetHealthDescriptions[?TargetHealth.State!=`healthy`]' \
        --output text | wc -l)
    UNHEALTHY_TARGETS=$((UNHEALTHY_TARGETS + UNHEALTHY))
done

if [ $UNHEALTHY_TARGETS -gt 0 ]; then
    echo "⚠ UNHEALTHY TARGETS DETECTED ($UNHEALTHY_TARGETS)"
    echo "  Common causes and solutions:"
    echo "  - Health check configuration issues"
    echo "  - Target instance not responding on health check port"
    echo "  - Security group blocking health check traffic"
    echo "  - Target instance overloaded or crashed"
    echo "  - Health check path returning non-200 status"
    echo ""
    
    echo "  Recommended actions:"
    echo "  - Check target instance logs"
    echo "  - Verify health check path responds correctly"
    echo "  - Review security group rules for health check port"
    echo "  - Monitor target instance CPU/memory usage"
else
    echo "✓ All targets are healthy"
fi

echo ""
echo "Additional recommendations:"
echo "- Enable access logs for detailed request analysis"
echo "- Monitor CloudWatch metrics for performance issues"
echo "- Check Application Load Balancer request routing rules"
echo "- Verify SSL certificate configuration (for HTTPS)"
echo "- Review target group stickiness settings if needed"
EOF

chmod +x load-balancer-troubleshoot.sh

echo "ロードバランサー診断スクリプト作成完了"
```

## 🔒 Step 6: セキュリティ問題のトラブルシューティング

### 6.1 セキュリティ関連接続問題診断

```bash
# セキュリティ接続問題診断スクリプト
cat > security-connectivity-troubleshoot.sh << 'EOF'
#!/bin/bash

SOURCE_IP=$1
TARGET_IP=$2
TARGET_PORT=$3

if [ -z "$SOURCE_IP" ] || [ -z "$TARGET_IP" ] || [ -z "$TARGET_PORT" ]; then
    echo "Usage: $0 <source-ip> <target-ip> <target-port>"
    exit 1
fi

echo "=== Security Connectivity Troubleshooting ==="
echo "Source: $SOURCE_IP"
echo "Target: $TARGET_IP:$TARGET_PORT"
echo ""

# 1. 基本的な接続テスト
echo "1. Basic Connectivity Test:"
timeout 10 bash -c "</dev/tcp/$TARGET_IP/$TARGET_PORT" 2>/dev/null
CONNECT_RESULT=$?
if [ $CONNECT_RESULT -eq 0 ]; then
    echo "✓ TCP connection successful"
else
    echo "✗ TCP connection failed"
fi
echo ""

# 2. Security Group分析
echo "2. Security Group Analysis:"

# ソースインスタンスのセキュリティグループ確認
echo "Analyzing source instance security groups..."
SOURCE_INSTANCE=$(aws ec2 describe-instances \
    --filters "Name=private-ip-address,Values=$SOURCE_IP" \
    --query 'Reservations[0].Instances[0].InstanceId' \
    --output text 2>/dev/null)

if [ "$SOURCE_INSTANCE" != "None" ] && [ -n "$SOURCE_INSTANCE" ]; then
    echo "Source Instance: $SOURCE_INSTANCE"
    
    SOURCE_SGS=$(aws ec2 describe-instances \
        --instance-ids $SOURCE_INSTANCE \
        --query 'Reservations[0].Instances[0].SecurityGroups[*].GroupId' \
        --output text)
    
    echo "Source Security Groups: $SOURCE_SGS"
    
    # Egress rules確認
    for sg in $SOURCE_SGS; do
        echo "Egress rules for $sg:"
        aws ec2 describe-security-groups \
            --group-ids $sg \
            --query 'SecurityGroups[0].IpPermissionsEgress[*].{Protocol:IpProtocol,FromPort:FromPort,ToPort:ToPort,Destinations:IpRanges[*].CidrIp}' \
            --output table
    done
fi

# ターゲットインスタンスのセキュリティグループ確認
echo "Analyzing target instance security groups..."
TARGET_INSTANCE=$(aws ec2 describe-instances \
    --filters "Name=private-ip-address,Values=$TARGET_IP" \
    --query 'Reservations[0].Instances[0].InstanceId' \
    --output text 2>/dev/null)

if [ "$TARGET_INSTANCE" != "None" ] && [ -n "$TARGET_INSTANCE" ]; then
    echo "Target Instance: $TARGET_INSTANCE"
    
    TARGET_SGS=$(aws ec2 describe-instances \
        --instance-ids $TARGET_INSTANCE \
        --query 'Reservations[0].Instances[0].SecurityGroups[*].GroupId' \
        --output text)
    
    echo "Target Security Groups: $TARGET_SGS"
    
    # Ingress rules確認
    for sg in $TARGET_SGS; do
        echo "Ingress rules for $sg:"
        aws ec2 describe-security-groups \
            --group-ids $sg \
            --query 'SecurityGroups[0].IpPermissions[*].{Protocol:IpProtocol,FromPort:FromPort,ToPort:ToPort,Sources:IpRanges[*].CidrIp}' \
            --output table
    done
fi
echo ""

# 3. Network ACL分析
echo "3. Network ACL Analysis:"
if [ -n "$TARGET_INSTANCE" ]; then
    TARGET_SUBNET=$(aws ec2 describe-instances \
        --instance-ids $TARGET_INSTANCE \
        --query 'Reservations[0].Instances[0].SubnetId' \
        --output text)
    
    NACL_ID=$(aws ec2 describe-network-acls \
        --filters "Name=association.subnet-id,Values=$TARGET_SUBNET" \
        --query 'NetworkAcls[0].NetworkAclId' \
        --output text)
    
    echo "Target Subnet: $TARGET_SUBNET"
    echo "Network ACL: $NACL_ID"
    
    echo "Inbound NACL Rules:"
    aws ec2 describe-network-acls \
        --network-acl-ids $NACL_ID \
        --query 'NetworkAcls[0].Entries[?Egress==`false`].{Rule:RuleNumber,Protocol:Protocol,Port:PortRange.From,CIDR:CidrBlock,Action:RuleAction}' \
        --output table
    
    echo "Outbound NACL Rules:"
    aws ec2 describe-network-acls \
        --network-acl-ids $NACL_ID \
        --query 'NetworkAcls[0].Entries[?Egress==`true`].{Rule:RuleNumber,Protocol:Protocol,Port:PortRange.From,CIDR:CidrBlock,Action:RuleAction}' \
        --output table
fi
echo ""

# 4. VPC Flow Logs 分析
echo "4. VPC Flow Logs Analysis (if available):"
if [ -n "$TARGET_INSTANCE" ]; then
    VPC_ID=$(aws ec2 describe-instances \
        --instance-ids $TARGET_INSTANCE \
        --query 'Reservations[0].Instances[0].VpcId' \
        --output text)
    
    echo "Checking for VPC Flow Logs..."
    FLOW_LOGS=$(aws ec2 describe-flow-logs \
        --filters "Name=resource-id,Values=$VPC_ID" \
        --query 'FlowLogs[*].LogGroupName' \
        --output text)
    
    if [ -n "$FLOW_LOGS" ]; then
        echo "Flow Logs available in: $FLOW_LOGS"
        echo "Use CloudWatch Logs Insights to analyze traffic patterns"
        
        # サンプルクエリ提供
        cat > flow-logs-query.txt << QUERY
# CloudWatch Logs Insights Query for connection analysis
fields @timestamp, srcaddr, dstaddr, srcport, dstport, protocol, action
| filter dstaddr like "$TARGET_IP" and dstport = $TARGET_PORT
| filter srcaddr like "$SOURCE_IP"
| sort @timestamp desc
| limit 100
QUERY
        echo "Sample query saved to flow-logs-query.txt"
    else
        echo "No VPC Flow Logs configured"
    fi
fi
echo ""

# 5. セキュリティ問題診断
echo "=== Security Analysis Summary ==="

if [ $CONNECT_RESULT -eq 0 ]; then
    echo "✓ Connection successful - no security blocking detected"
else
    echo "✗ Connection failed - analyzing potential security blocks..."
    echo ""
    
    echo "Potential causes:"
    echo "1. Security Group Issues:"
    echo "   - Source instance egress rules may not allow outbound to $TARGET_PORT"
    echo "   - Target instance ingress rules may not allow inbound from $SOURCE_IP"
    echo "   - Check for overly restrictive security group rules"
    echo ""
    
    echo "2. Network ACL Issues:"
    echo "   - Network ACL may be blocking the connection"
    echo "   - Check both inbound and outbound ACL rules"
    echo "   - Ensure stateless nature of ACLs is handled correctly"
    echo ""
    
    echo "3. Target Service Issues:"
    echo "   - Target service may not be listening on port $TARGET_PORT"
    echo "   - Target instance may be stopped or crashed"
    echo "   - Local firewall on target instance may be blocking"
    echo ""
    
    echo "Recommended troubleshooting steps:"
    echo "1. Test with wider security group rules temporarily"
    echo "2. Check target instance system logs"
    echo "3. Verify service is running: netstat -tlnp | grep $TARGET_PORT"
    echo "4. Use VPC Flow Logs to see if packets are reaching target"
    echo "5. Check CloudTrail logs for any security changes"
fi
EOF

chmod +x security-connectivity-troubleshoot.sh

echo "セキュリティ接続診断スクリプト作成完了"
```

## 📊 Step 7: 総合診断ダッシュボード

### 7.1 自動診断スクリプト

```bash
# 総合自動診断スクリプト
cat > comprehensive-network-diagnosis.sh << 'EOF'
#!/bin/bash

echo "=== Comprehensive Network Diagnosis ==="
echo "Timestamp: $(date)"
echo "User: $(whoami)"
echo ""

# 診断結果保存ディレクトリ
REPORT_DIR="/tmp/network-diagnosis-$(date +%Y%m%d-%H%M%S)"
mkdir -p $REPORT_DIR

# 1. システム情報収集
echo "1. Collecting System Information..."
{
    echo "=== System Information ==="
    echo "Hostname: $(hostname)"
    echo "OS: $(cat /etc/os-release | grep PRETTY_NAME)"
    echo "Kernel: $(uname -r)"
    echo "Uptime: $(uptime)"
    echo ""
    
    echo "=== Network Interfaces ==="
    ip addr show
    echo ""
    
    echo "=== Routing Table ==="
    ip route show
    echo ""
    
    echo "=== DNS Configuration ==="
    cat /etc/resolv.conf
    echo ""
} > $REPORT_DIR/system-info.txt

# 2. AWS環境情報収集
echo "2. Collecting AWS Environment Information..."
{
    echo "=== AWS Instance Metadata ==="
    INSTANCE_ID=$(curl -s http://169.254.169.254/latest/meta-data/instance-id 2>/dev/null)
    if [ $? -eq 0 ]; then
        echo "Instance ID: $INSTANCE_ID"
        echo "AMI ID: $(curl -s http://169.254.169.254/latest/meta-data/ami-id)"
        echo "Instance Type: $(curl -s http://169.254.169.254/latest/meta-data/instance-type)"
        echo "Private IP: $(curl -s http://169.254.169.254/latest/meta-data/local-ipv4)"
        echo "Public IP: $(curl -s http://169.254.169.254/latest/meta-data/public-ipv4)"
        echo "Availability Zone: $(curl -s http://169.254.169.254/latest/meta-data/placement/availability-zone)"
        echo "VPC ID: $(curl -s http://169.254.169.254/latest/meta-data/network/interfaces/macs/$(curl -s http://169.254.169.254/latest/meta-data/mac)/vpc-id)"
        echo "Subnet ID: $(curl -s http://169.254.169.254/latest/meta-data/network/interfaces/macs/$(curl -s http://169.254.169.254/latest/meta-data/mac)/subnet-id)"
        
        echo ""
        echo "=== Security Groups ==="
        aws ec2 describe-instances --instance-ids $INSTANCE_ID \
            --query 'Reservations[0].Instances[0].SecurityGroups' \
            --output table 2>/dev/null
    else
        echo "Not running on EC2 instance"
    fi
} > $REPORT_DIR/aws-info.txt

# 3. 接続性テスト
echo "3. Running Connectivity Tests..."
{
    echo "=== Connectivity Tests ==="
    
    # 基本的な接続テスト先
    TEST_HOSTS=("8.8.8.8" "1.1.1.1" "amazon.com" "aws.amazon.com")
    
    for host in "${TEST_HOSTS[@]}"; do
        echo "Testing connectivity to $host:"
        ping -c 3 $host 2>&1
        echo ""
    done
    
    # ポートテスト
    echo "=== Port Connectivity Tests ==="
    TEST_PORTS=("amazon.com:443" "aws.amazon.com:443" "8.8.8.8:53")
    
    for endpoint in "${TEST_PORTS[@]}"; do
        host=$(echo $endpoint | cut -d: -f1)
        port=$(echo $endpoint | cut -d: -f2)
        echo "Testing $host:$port:"
        timeout 5 bash -c "</dev/tcp/$host/$port" 2>/dev/null
        if [ $? -eq 0 ]; then
            echo "✓ SUCCESS"
        else
            echo "✗ FAILED"
        fi
        echo ""
    done
} > $REPORT_DIR/connectivity-tests.txt

# 4. DNS診断
echo "4. Running DNS Diagnostics..."
{
    echo "=== DNS Diagnostics ==="
    
    DNS_TEST_DOMAINS=("amazon.com" "aws.amazon.com" "google.com")
    
    for domain in "${DNS_TEST_DOMAINS[@]}"; do
        echo "DNS test for $domain:"
        nslookup $domain 2>&1
        echo ""
        
        echo "Dig test for $domain:"
        dig $domain +short 2>&1
        echo ""
    done
} > $REPORT_DIR/dns-tests.txt

# 5. パフォーマンス測定
echo "5. Running Performance Tests..."
{
    echo "=== Performance Tests ==="
    
    # レイテンシテスト
    echo "Latency tests:"
    for host in "8.8.8.8" "1.1.1.1"; do
        echo "Ping to $host:"
        ping -c 5 $host | tail -1
        echo ""
    done
    
    # DNS解決時間
    echo "DNS resolution time:"
    time nslookup amazon.com > /dev/null 2>&1
    echo ""
} > $REPORT_DIR/performance-tests.txt

# 6. セキュリティチェック
echo "6. Running Security Checks..."
{
    echo "=== Security Checks ==="
    
    # 開いているポート
    echo "Open ports:"
    netstat -tulpn 2>/dev/null | grep LISTEN
    echo ""
    
    # プロセス確認
    echo "Network-related processes:"
    ps aux | grep -E "(ssh|http|nginx|apache)" | grep -v grep
    echo ""
    
    # ファイアウォール状態
    echo "Firewall status:"
    if command -v ufw &> /dev/null; then
        ufw status
    elif command -v firewall-cmd &> /dev/null; then
        firewall-cmd --list-all
    elif command -v iptables &> /dev/null; then
        iptables -L -n | head -20
    fi
} > $REPORT_DIR/security-checks.txt

# 7. CloudWatch メトリクス収集（可能な場合）
echo "7. Collecting CloudWatch Metrics..."
if [ -n "$INSTANCE_ID" ] && command -v aws &> /dev/null; then
    {
        echo "=== CloudWatch Metrics ==="
        
        # ネットワークメトリクス
        echo "Network metrics for last hour:"
        aws cloudwatch get-metric-statistics \
            --namespace AWS/EC2 \
            --metric-name NetworkIn \
            --dimensions Name=InstanceId,Value=$INSTANCE_ID \
            --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
            --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
            --period 300 \
            --statistics Average Maximum \
            --output table 2>/dev/null | tail -10
    } > $REPORT_DIR/cloudwatch-metrics.txt
fi

# 8. レポート生成
echo "8. Generating Summary Report..."
{
    echo "=== Network Diagnosis Summary Report ==="
    echo "Generated: $(date)"
    echo "Instance: $(hostname)"
    if [ -n "$INSTANCE_ID" ]; then
        echo "AWS Instance ID: $INSTANCE_ID"
    fi
    echo ""
    
    echo "=== Test Results Summary ==="
    
    # 接続性テスト結果サマリー
    echo "Connectivity Tests:"
    if grep -q "✓ SUCCESS" $REPORT_DIR/connectivity-tests.txt; then
        echo "  ✓ Basic connectivity: PASSED"
    else
        echo "  ✗ Basic connectivity: FAILED"
    fi
    
    # DNS テスト結果
    if grep -q "amazon.com" $REPORT_DIR/dns-tests.txt; then
        echo "  ✓ DNS resolution: WORKING"
    else
        echo "  ✗ DNS resolution: ISSUES DETECTED"
    fi
    
    echo ""
    echo "=== Recommendations ==="
    
    # 問題に基づく推奨事項
    if grep -q "FAILED" $REPORT_DIR/connectivity-tests.txt; then
        echo "⚠ Connectivity Issues Detected:"
        echo "  - Check security group configurations"
        echo "  - Verify network ACL settings"
        echo "  - Review routing table entries"
        echo "  - Confirm target services are running"
    fi
    
    if ! grep -q "amazon.com" $REPORT_DIR/dns-tests.txt; then
        echo "⚠ DNS Issues Detected:"
        echo "  - Check /etc/resolv.conf configuration"
        echo "  - Verify DNS server connectivity"
        echo "  - Review VPC DNS settings"
    fi
    
    echo ""
    echo "Report files saved to: $REPORT_DIR"
    echo "For detailed analysis, review individual test files."
    
} > $REPORT_DIR/summary-report.txt

# レポート表示
echo ""
echo "=== Diagnosis Complete ==="
echo "Report saved to: $REPORT_DIR"
echo ""
echo "Summary:"
cat $REPORT_DIR/summary-report.txt | tail -20

echo ""
echo "Available report files:"
ls -la $REPORT_DIR
EOF

chmod +x comprehensive-network-diagnosis.sh

echo "総合診断スクリプト作成完了"
```

## 🧹 Step 8: リソースクリーンアップ

### 8.1 診断環境削除

```bash
# 診断環境クリーンアップ
aws ec2 terminate-instances --instance-ids $DIAG_INSTANCE_1 $DIAG_INSTANCE_2

# セキュリティグループ削除
aws ec2 delete-security-group --group-id $DIAG_SG

# ルートテーブル削除
aws ec2 delete-route-table --route-table-id $PUBLIC_RT

# サブネット削除
aws ec2 delete-subnet --subnet-id $PUBLIC_SUBNET
aws ec2 delete-subnet --subnet-id $PRIVATE_SUBNET

# Internet Gateway削除
aws ec2 detach-internet-gateway --vpc-id $TROUBLESHOOT_VPC_ID --internet-gateway-id $IGW_ID
aws ec2 delete-internet-gateway --internet-gateway-id $IGW_ID

# VPC削除
aws ec2 delete-vpc --vpc-id $TROUBLESHOOT_VPC_ID

echo "診断環境削除完了"
```

## 💰 コスト計算

### 推定コスト（診断実行1回あたり）
- **診断用インスタンス (t3.micro x2)**: $0.02/時間
- **診断実行時間**: 約30分
- **一回あたりのコスト**: 約 $0.01

## 📚 学習ポイント

### 重要な概念
1. **体系的診断**: ステップバイステップの問題特定
2. **ツール活用**: 複数の診断ツールの組み合わせ
3. **ログ分析**: VPC Flow Logs, CloudWatch の活用
4. **自動化**: 診断プロセスの自動化
5. **ドキュメント化**: 問題と解決策の記録

### 実践的なスキル
- ネットワーク問題の体系的診断手法
- AWS CLI を使った効率的な問題分析
- パフォーマンス問題の特定と解決
- セキュリティ設定の確認と修正
- 総合的な診断レポート作成

---

**完了**: この Lab 5 で、AWS ネットワークの包括的なトラブルシューティング手法を習得しました。実際の問題対応時にこれらのスクリプトとプロセスを活用してください。