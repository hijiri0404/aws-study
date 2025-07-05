# Lab 3: ロードバランシング

## 🎯 学習目標

このラボでは、AWSの各種ロードバランサーを用いた高可用性とスケーラビリティの実現を学習します：

- Application Load Balancer (ALB) の高度な設定
- Network Load Balancer (NLB) の実装
- Global Load Balancer (GLB) によるグローバル配信
- Auto Scaling との統合
- セキュリティとパフォーマンス最適化

## 📋 前提条件

- AWS CLI が設定済み
- EC2、VPC の基本知識
- [Lab 2: ハイブリッド接続](./lab02-hybrid-connectivity.md) の完了推奨

## 🏗️ アーキテクチャ概要

```
┌─────────────────────────────────────────────────────────────┐
│                    ロードバランシング環境                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Internet Gateway                                           │
│         │                                                   │
│         ▼                                                   │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐     │
│  │   Global    │    │ Application │    │   Network   │     │
│  │   Load      │    │    Load     │    │    Load     │     │
│  │  Balancer   │    │  Balancer   │    │  Balancer   │     │
│  └─────┬───────┘    └─────┬───────┘    └─────┬───────┘     │
│        │                  │                  │             │
│        ▼                  ▼                  ▼             │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │              Auto Scaling Groups                       │ │
│  │         Multi-AZ Target Instances                      │ │
│  └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

## 🚀 Step 1: Application Load Balancer (ALB)

### 1.1 VPC とサブネット設定

```bash
# VPC 作成
VPC_ID=$(aws ec2 create-vpc \
    --cidr-block 10.0.0.0/16 \
    --tag-specifications 'ResourceType=vpc,Tags=[{Key=Name,Value=LoadBalancer-VPC}]' \
    --query 'Vpc.VpcId' \
    --output text)

# Internet Gateway 作成・アタッチ
IGW_ID=$(aws ec2 create-internet-gateway \
    --tag-specifications 'ResourceType=internet-gateway,Tags=[{Key=Name,Value=LoadBalancer-IGW}]' \
    --query 'InternetGateway.InternetGatewayId' \
    --output text)

aws ec2 attach-internet-gateway \
    --vpc-id $VPC_ID \
    --internet-gateway-id $IGW_ID

# パブリックサブネット作成 (Multi-AZ)
PUBLIC_SUBNET_1=$(aws ec2 create-subnet \
    --vpc-id $VPC_ID \
    --cidr-block 10.0.1.0/24 \
    --availability-zone us-east-1a \
    --tag-specifications 'ResourceType=subnet,Tags=[{Key=Name,Value=Public-Subnet-1a}]' \
    --query 'Subnet.SubnetId' \
    --output text)

PUBLIC_SUBNET_2=$(aws ec2 create-subnet \
    --vpc-id $VPC_ID \
    --cidr-block 10.0.2.0/24 \
    --availability-zone us-east-1b \
    --tag-specifications 'ResourceType=subnet,Tags=[{Key=Name,Value=Public-Subnet-1b}]' \
    --query 'Subnet.SubnetId' \
    --output text)

# プライベートサブネット作成
PRIVATE_SUBNET_1=$(aws ec2 create-subnet \
    --vpc-id $VPC_ID \
    --cidr-block 10.0.11.0/24 \
    --availability-zone us-east-1a \
    --tag-specifications 'ResourceType=subnet,Tags=[{Key=Name,Value=Private-Subnet-1a}]' \
    --query 'Subnet.SubnetId' \
    --output text)

PRIVATE_SUBNET_2=$(aws ec2 create-subnet \
    --vpc-id $VPC_ID \
    --cidr-block 10.0.12.0/24 \
    --availability-zone us-east-1b \
    --tag-specifications 'ResourceType=subnet,Tags=[{Key=Name,Value=Private-Subnet-1b}]' \
    --query 'Subnet.SubnetId' \
    --output text)

echo "VPC設定完了: $VPC_ID"
```

### 1.2 ルートテーブル設定

```bash
# パブリックルートテーブル作成
PUBLIC_RT=$(aws ec2 create-route-table \
    --vpc-id $VPC_ID \
    --tag-specifications 'ResourceType=route-table,Tags=[{Key=Name,Value=Public-RouteTable}]' \
    --query 'RouteTable.RouteTableId' \
    --output text)

# インターネットルート追加
aws ec2 create-route \
    --route-table-id $PUBLIC_RT \
    --destination-cidr-block 0.0.0.0/0 \
    --gateway-id $IGW_ID

# パブリックサブネットを関連付け
aws ec2 associate-route-table \
    --subnet-id $PUBLIC_SUBNET_1 \
    --route-table-id $PUBLIC_RT

aws ec2 associate-route-table \
    --subnet-id $PUBLIC_SUBNET_2 \
    --route-table-id $PUBLIC_RT

# NAT Gateway 作成（プライベートサブネット用）
EIP_ALLOCATION=$(aws ec2 allocate-address \
    --domain vpc \
    --query 'AllocationId' \
    --output text)

NAT_GW=$(aws ec2 create-nat-gateway \
    --subnet-id $PUBLIC_SUBNET_1 \
    --allocation-id $EIP_ALLOCATION \
    --tag-specifications 'ResourceType=nat-gateway,Tags=[{Key=Name,Value=LoadBalancer-NATGW}]' \
    --query 'NatGateway.NatGatewayId' \
    --output text)

# プライベートルートテーブル作成
PRIVATE_RT=$(aws ec2 create-route-table \
    --vpc-id $VPC_ID \
    --tag-specifications 'ResourceType=route-table,Tags=[{Key=Name,Value=Private-RouteTable}]' \
    --query 'RouteTable.RouteTableId' \
    --output text)

# NAT Gatewayルート追加
aws ec2 create-route \
    --route-table-id $PRIVATE_RT \
    --destination-cidr-block 0.0.0.0/0 \
    --nat-gateway-id $NAT_GW

# プライベートサブネットを関連付け
aws ec2 associate-route-table \
    --subnet-id $PRIVATE_SUBNET_1 \
    --route-table-id $PRIVATE_RT

aws ec2 associate-route-table \
    --subnet-id $PRIVATE_SUBNET_2 \
    --route-table-id $PRIVATE_RT

echo "ルーティング設定完了"
```

### 1.3 セキュリティグループ作成

```bash
# ALB用セキュリティグループ
ALB_SG=$(aws ec2 create-security-group \
    --group-name ALB-SecurityGroup \
    --description "Security group for Application Load Balancer" \
    --vpc-id $VPC_ID \
    --query 'GroupId' \
    --output text)

# HTTP/HTTPS アクセス許可
aws ec2 authorize-security-group-ingress \
    --group-id $ALB_SG \
    --protocol tcp \
    --port 80 \
    --cidr 0.0.0.0/0

aws ec2 authorize-security-group-ingress \
    --group-id $ALB_SG \
    --protocol tcp \
    --port 443 \
    --cidr 0.0.0.0/0

# ターゲットインスタンス用セキュリティグループ
TARGET_SG=$(aws ec2 create-security-group \
    --group-name Target-SecurityGroup \
    --description "Security group for target instances" \
    --vpc-id $VPC_ID \
    --query 'GroupId' \
    --output text)

# ALBからのアクセスのみ許可
aws ec2 authorize-security-group-ingress \
    --group-id $TARGET_SG \
    --protocol tcp \
    --port 80 \
    --source-group $ALB_SG

aws ec2 authorize-security-group-ingress \
    --group-id $TARGET_SG \
    --protocol tcp \
    --port 443 \
    --source-group $ALB_SG

echo "セキュリティグループ作成完了"
```

### 1.4 Application Load Balancer 作成

```bash
# ALB 作成
ALB_ARN=$(aws elbv2 create-load-balancer \
    --name "application-load-balancer" \
    --subnets $PUBLIC_SUBNET_1 $PUBLIC_SUBNET_2 \
    --security-groups $ALB_SG \
    --scheme internet-facing \
    --type application \
    --ip-address-type ipv4 \
    --tags Key=Name,Value=Application-LoadBalancer \
    --query 'LoadBalancers[0].LoadBalancerArn' \
    --output text)

# DNS名取得
ALB_DNS=$(aws elbv2 describe-load-balancers \
    --load-balancer-arns $ALB_ARN \
    --query 'LoadBalancers[0].DNSName' \
    --output text)

echo "ALB作成完了: $ALB_DNS"
```

### 1.5 Target Group と Listener 設定

```bash
# Target Group 作成
TARGET_GROUP_ARN=$(aws elbv2 create-target-group \
    --name "web-servers-tg" \
    --protocol HTTP \
    --port 80 \
    --vpc-id $VPC_ID \
    --health-check-protocol HTTP \
    --health-check-path "/" \
    --health-check-interval-seconds 30 \
    --health-check-timeout-seconds 5 \
    --healthy-threshold-count 2 \
    --unhealthy-threshold-count 3 \
    --matcher HttpCode=200 \
    --target-type instance \
    --query 'TargetGroups[0].TargetGroupArn' \
    --output text)

# Listener 作成
LISTENER_ARN=$(aws elbv2 create-listener \
    --load-balancer-arn $ALB_ARN \
    --protocol HTTP \
    --port 80 \
    --default-actions Type=forward,TargetGroupArn=$TARGET_GROUP_ARN \
    --query 'Listeners[0].ListenerArn' \
    --output text)

echo "Target Group と Listener 設定完了"
```

### 1.6 高度なルーティング設定

```bash
# パスベースルーティング用の追加 Target Group
API_TARGET_GROUP_ARN=$(aws elbv2 create-target-group \
    --name "api-servers-tg" \
    --protocol HTTP \
    --port 8080 \
    --vpc-id $VPC_ID \
    --health-check-path "/health" \
    --target-type instance \
    --query 'TargetGroups[0].TargetGroupArn' \
    --output text)

# ルーティングルール作成
cat > listener-rules.json << EOF
[
    {
        "Priority": 100,
        "Conditions": [
            {
                "Field": "path-pattern",
                "Values": ["/api/*"]
            }
        ],
        "Actions": [
            {
                "Type": "forward",
                "TargetGroupArn": "$API_TARGET_GROUP_ARN"
            }
        ]
    },
    {
        "Priority": 200,
        "Conditions": [
            {
                "Field": "host-header",
                "Values": ["api.example.com"]
            }
        ],
        "Actions": [
            {
                "Type": "forward",
                "TargetGroupArn": "$API_TARGET_GROUP_ARN"
            }
        ]
    }
]
EOF

# ルールを適用
aws elbv2 create-rule \
    --listener-arn $LISTENER_ARN \
    --priority 100 \
    --conditions Field=path-pattern,Values="/api/*" \
    --actions Type=forward,TargetGroupArn=$API_TARGET_GROUP_ARN

aws elbv2 create-rule \
    --listener-arn $LISTENER_ARN \
    --priority 200 \
    --conditions Field=host-header,Values="api.example.com" \
    --actions Type=forward,TargetGroupArn=$API_TARGET_GROUP_ARN

echo "高度なルーティング設定完了"
```

## ⚡ Step 2: Network Load Balancer (NLB)

### 2.1 NLB 作成

```bash
# NLB 作成
NLB_ARN=$(aws elbv2 create-load-balancer \
    --name "network-load-balancer" \
    --subnets $PUBLIC_SUBNET_1 $PUBLIC_SUBNET_2 \
    --scheme internet-facing \
    --type network \
    --ip-address-type ipv4 \
    --tags Key=Name,Value=Network-LoadBalancer \
    --query 'LoadBalancers[0].LoadBalancerArn' \
    --output text)

# NLB DNS名取得
NLB_DNS=$(aws elbv2 describe-load-balancers \
    --load-balancer-arns $NLB_ARN \
    --query 'LoadBalancers[0].DNSName' \
    --output text)

echo "NLB作成完了: $NLB_DNS"
```

### 2.2 TCP ターゲットグループ設定

```bash
# TCP Target Group 作成
TCP_TARGET_GROUP_ARN=$(aws elbv2 create-target-group \
    --name "tcp-servers-tg" \
    --protocol TCP \
    --port 80 \
    --vpc-id $VPC_ID \
    --health-check-protocol TCP \
    --health-check-port 80 \
    --health-check-interval-seconds 30 \
    --healthy-threshold-count 3 \
    --unhealthy-threshold-count 3 \
    --target-type instance \
    --query 'TargetGroups[0].TargetGroupArn' \
    --output text)

# NLB Listener 作成
NLB_LISTENER_ARN=$(aws elbv2 create-listener \
    --load-balancer-arn $NLB_ARN \
    --protocol TCP \
    --port 80 \
    --default-actions Type=forward,TargetGroupArn=$TCP_TARGET_GROUP_ARN \
    --query 'Listeners[0].ListenerArn' \
    --output text)

echo "NLB TCP設定完了"
```

### 2.3 TLS Termination 設定

```bash
# ACM証明書のARN（事前に作成されている想定）
# CERTIFICATE_ARN="arn:aws:acm:us-east-1:123456789012:certificate/12345678-1234-1234-1234-123456789012"

# TLS Listener 作成（証明書がある場合）
cat > tls-listener-config.json << EOF
{
    "LoadBalancerArn": "$NLB_ARN",
    "Protocol": "TLS",
    "Port": 443,
    "DefaultActions": [
        {
            "Type": "forward",
            "TargetGroupArn": "$TCP_TARGET_GROUP_ARN"
        }
    ]
}
EOF

# TLS設定は証明書がある場合のみ実行
echo "TLS設定は証明書準備後に実行してください"
```

## 🌍 Step 3: Global Load Balancer (CloudFront + GLB)

### 3.1 CloudFront Distribution 作成

```bash
# CloudFront Distribution 設定
cat > cloudfront-config.json << EOF
{
    "CallerReference": "$(date +%s)",
    "Comment": "Global Load Balancer Distribution",
    "DefaultCacheBehavior": {
        "TargetOriginId": "ALB-Origin",
        "ViewerProtocolPolicy": "redirect-to-https",
        "TrustedSigners": {
            "Enabled": false,
            "Quantity": 0
        },
        "ForwardedValues": {
            "QueryString": true,
            "Cookies": {
                "Forward": "none"
            },
            "Headers": {
                "Quantity": 1,
                "Items": ["Host"]
            }
        },
        "MinTTL": 0,
        "DefaultTTL": 300,
        "MaxTTL": 31536000
    },
    "Origins": {
        "Quantity": 1,
        "Items": [
            {
                "Id": "ALB-Origin",
                "DomainName": "$ALB_DNS",
                "CustomOriginConfig": {
                    "HTTPPort": 80,
                    "HTTPSPort": 443,
                    "OriginProtocolPolicy": "http-only"
                }
            }
        ]
    },
    "Enabled": true,
    "PriceClass": "PriceClass_All"
}
EOF

# CloudFront Distribution 作成
DISTRIBUTION_ID=$(aws cloudfront create-distribution \
    --distribution-config file://cloudfront-config.json \
    --query 'Distribution.Id' \
    --output text)

echo "CloudFront Distribution作成完了: $DISTRIBUTION_ID"
```

### 3.2 Global Load Balancer 設定

```bash
# Global Load Balancer 作成（Gateway Load Balancer）
GLB_ARN=$(aws elbv2 create-load-balancer \
    --name "gateway-load-balancer" \
    --subnets $PRIVATE_SUBNET_1 $PRIVATE_SUBNET_2 \
    --scheme internal \
    --type gateway \
    --tags Key=Name,Value=Gateway-LoadBalancer \
    --query 'LoadBalancers[0].LoadBalancerArn' \
    --output text)

# Gateway Target Group 作成
GATEWAY_TARGET_GROUP_ARN=$(aws elbv2 create-target-group \
    --name "gateway-targets-tg" \
    --protocol GENEVE \
    --port 6081 \
    --vpc-id $VPC_ID \
    --health-check-protocol HTTP \
    --health-check-path "/health" \
    --health-check-port 80 \
    --target-type instance \
    --query 'TargetGroups[0].TargetGroupArn' \
    --output text)

# Gateway Listener 作成
GATEWAY_LISTENER_ARN=$(aws elbv2 create-listener \
    --load-balancer-arn $GLB_ARN \
    --default-actions Type=forward,TargetGroupArn=$GATEWAY_TARGET_GROUP_ARN \
    --query 'Listeners[0].ListenerArn' \
    --output text)

echo "Gateway Load Balancer設定完了"
```

## 📈 Step 4: Auto Scaling 統合

### 4.1 Launch Template 作成

```bash
# User Data スクリプト作成
cat > user-data.sh << 'EOF'
#!/bin/bash
yum update -y
yum install -y httpd
systemctl start httpd
systemctl enable httpd

# インスタンス識別用のページ作成
INSTANCE_ID=$(curl -s http://169.254.169.254/latest/meta-data/instance-id)
AZ=$(curl -s http://169.254.169.254/latest/meta-data/placement/availability-zone)
cat > /var/www/html/index.html << HTML
<!DOCTYPE html>
<html>
<head>
    <title>Load Balancer Test</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; }
        .info { background-color: #f0f0f0; padding: 20px; border-radius: 5px; }
    </style>
</head>
<body>
    <h1>Load Balancer Test Server</h1>
    <div class="info">
        <h2>Instance Information</h2>
        <p><strong>Instance ID:</strong> $INSTANCE_ID</p>
        <p><strong>Availability Zone:</strong> $AZ</p>
        <p><strong>Time:</strong> $(date)</p>
    </div>
</body>
</html>
HTML

# Health Check エンドポイント
echo "OK" > /var/www/html/health
EOF

# Launch Template 作成
LAUNCH_TEMPLATE_ID=$(aws ec2 create-launch-template \
    --launch-template-name "web-server-template" \
    --launch-template-data '{
        "ImageId": "ami-0c02fb55956c7d316",
        "InstanceType": "t3.micro",
        "SecurityGroupIds": ["'$TARGET_SG'"],
        "UserData": "'$(base64 -w 0 user-data.sh)'",
        "TagSpecifications": [
            {
                "ResourceType": "instance",
                "Tags": [
                    {"Key": "Name", "Value": "WebServer-AutoScale"}
                ]
            }
        ]
    }' \
    --query 'LaunchTemplate.LaunchTemplateId' \
    --output text)

echo "Launch Template作成完了: $LAUNCH_TEMPLATE_ID"
```

### 4.2 Auto Scaling Group 作成

```bash
# Auto Scaling Group 作成
aws autoscaling create-auto-scaling-group \
    --auto-scaling-group-name "web-servers-asg" \
    --launch-template LaunchTemplateId=$LAUNCH_TEMPLATE_ID,Version='$Latest' \
    --min-size 2 \
    --max-size 10 \
    --desired-capacity 4 \
    --vpc-zone-identifier "$PRIVATE_SUBNET_1,$PRIVATE_SUBNET_2" \
    --target-group-arns $TARGET_GROUP_ARN $TCP_TARGET_GROUP_ARN \
    --health-check-type ELB \
    --health-check-grace-period 300 \
    --tags Key=Name,Value=WebServer-ASG,PropagateAtLaunch=true

echo "Auto Scaling Group作成完了"
```

### 4.3 Auto Scaling Policy 設定

```bash
# スケールアップポリシー
SCALE_UP_POLICY=$(aws autoscaling put-scaling-policy \
    --auto-scaling-group-name "web-servers-asg" \
    --policy-name "scale-up-policy" \
    --policy-type "StepScaling" \
    --adjustment-type "ChangeInCapacity" \
    --step-adjustments MetricIntervalLowerBound=0,MetricIntervalUpperBound=50,ScalingAdjustment=1 \
    --step-adjustments MetricIntervalLowerBound=50,ScalingAdjustment=2 \
    --metric-aggregation-type "Average" \
    --query 'PolicyARN' \
    --output text)

# スケールダウンポリシー
SCALE_DOWN_POLICY=$(aws autoscaling put-scaling-policy \
    --auto-scaling-group-name "web-servers-asg" \
    --policy-name "scale-down-policy" \
    --policy-type "StepScaling" \
    --adjustment-type "ChangeInCapacity" \
    --step-adjustments MetricIntervalUpperBound=0,MetricIntervalLowerBound=-50,ScalingAdjustment=-1 \
    --step-adjustments MetricIntervalUpperBound=-50,ScalingAdjustment=-2 \
    --metric-aggregation-type "Average" \
    --query 'PolicyARN' \
    --output text)

echo "Auto Scaling Policy設定完了"
```

### 4.4 CloudWatch Alarms 設定

```bash
# CPU高使用率アラーム
aws cloudwatch put-metric-alarm \
    --alarm-name "HighCPUUtilization" \
    --alarm-description "Alarm when CPU exceeds 70%" \
    --metric-name CPUUtilization \
    --namespace AWS/EC2 \
    --statistic Average \
    --period 300 \
    --threshold 70 \
    --comparison-operator GreaterThanThreshold \
    --evaluation-periods 2 \
    --alarm-actions $SCALE_UP_POLICY \
    --dimensions Name=AutoScalingGroupName,Value=web-servers-asg

# CPU低使用率アラーム
aws cloudwatch put-metric-alarm \
    --alarm-name "LowCPUUtilization" \
    --alarm-description "Alarm when CPU falls below 30%" \
    --metric-name CPUUtilization \
    --namespace AWS/EC2 \
    --statistic Average \
    --period 300 \
    --threshold 30 \
    --comparison-operator LessThanThreshold \
    --evaluation-periods 2 \
    --alarm-actions $SCALE_DOWN_POLICY \
    --dimensions Name=AutoScalingGroupName,Value=web-servers-asg

echo "CloudWatch Alarms設定完了"
```

## 🔒 Step 5: セキュリティとパフォーマンス最適化

### 5.1 WAF 設定

```bash
# WAF Web ACL 作成
WAF_WEB_ACL_ID=$(aws wafv2 create-web-acl \
    --name "LoadBalancer-WebACL" \
    --scope REGIONAL \
    --default-action Allow={} \
    --rules '[
        {
            "Name": "RateLimitRule",
            "Priority": 1,
            "Statement": {
                "RateBasedStatement": {
                    "Limit": 2000,
                    "AggregateKeyType": "IP"
                }
            },
            "Action": {
                "Block": {}
            },
            "VisibilityConfig": {
                "SampledRequestsEnabled": true,
                "CloudWatchMetricsEnabled": true,
                "MetricName": "RateLimitRule"
            }
        }
    ]' \
    --visibility-config SampledRequestsEnabled=true,CloudWatchMetricsEnabled=true,MetricName=LoadBalancerWebACL \
    --query 'Summary.Id' \
    --output text)

# WAF を ALB に関連付け
aws wafv2 associate-web-acl \
    --web-acl-arn $(aws wafv2 get-web-acl --scope REGIONAL --id $WAF_WEB_ACL_ID --query 'WebACL.ARN' --output text) \
    --resource-arn $ALB_ARN

echo "WAF設定完了"
```

### 5.2 SSL/TLS 証明書設定

```bash
# ACM証明書要求（DNS検証）
CERTIFICATE_ARN=$(aws acm request-certificate \
    --domain-name "example.com" \
    --subject-alternative-names "*.example.com" \
    --validation-method DNS \
    --query 'CertificateArn' \
    --output text)

# HTTPS Listener 作成（証明書検証後）
cat > https-listener-config.json << EOF
{
    "LoadBalancerArn": "$ALB_ARN",
    "Protocol": "HTTPS",
    "Port": 443,
    "Certificates": [
        {
            "CertificateArn": "$CERTIFICATE_ARN"
        }
    ],
    "SslPolicy": "ELBSecurityPolicy-TLS-1-2-2017-01",
    "DefaultActions": [
        {
            "Type": "forward",
            "TargetGroupArn": "$TARGET_GROUP_ARN"
        }
    ]
}
EOF

echo "SSL/TLS証明書設定準備完了（DNS検証が必要）"
```

### 5.3 セッション親和性設定

```bash
# セッション親和性の有効化
aws elbv2 modify-target-group-attributes \
    --target-group-arn $TARGET_GROUP_ARN \
    --attributes Key=stickiness.enabled,Value=true \
                Key=stickiness.type,Value=lb_cookie \
                Key=stickiness.lb_cookie.duration_seconds,Value=86400

echo "セッション親和性設定完了"
```

## 📊 Step 6: 監視とロギング

### 6.1 Access Logs 設定

```bash
# S3バケット作成（Access Logs用）
LOG_BUCKET="elb-access-logs-$(date +%s)"
aws s3 mb s3://$LOG_BUCKET

# バケットポリシー設定
cat > bucket-policy.json << EOF
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Principal": {
                "AWS": "arn:aws:iam::127311923021:root"
            },
            "Action": "s3:PutObject",
            "Resource": "arn:aws:s3:::$LOG_BUCKET/AWSLogs/$(aws sts get-caller-identity --query Account --output text)/*"
        }
    ]
}
EOF

aws s3api put-bucket-policy \
    --bucket $LOG_BUCKET \
    --policy file://bucket-policy.json

# ALB Access Logs 有効化
aws elbv2 modify-load-balancer-attributes \
    --load-balancer-arn $ALB_ARN \
    --attributes Key=access_logs.s3.enabled,Value=true \
                Key=access_logs.s3.bucket,Value=$LOG_BUCKET \
                Key=access_logs.s3.prefix,Value=alb-logs

echo "Access Logs設定完了: s3://$LOG_BUCKET"
```

### 6.2 CloudWatch メトリクス監視

```bash
# カスタムメトリクス収集用Lambda関数（概念的例）
cat > monitoring-script.py << 'EOF'
import boto3
import json
from datetime import datetime, timedelta

def lambda_handler(event, context):
    elbv2 = boto3.client('elbv2')
    cloudwatch = boto3.client('cloudwatch')
    
    # ターゲットヘルス状態取得
    response = elbv2.describe-target-health(
        TargetGroupArn=TARGET_GROUP_ARN
    )
    
    healthy_targets = len([t for t in response['TargetHealthDescriptions'] 
                          if t['TargetHealth']['State'] == 'healthy'])
    
    # カスタムメトリクス送信
    cloudwatch.put_metric_data(
        Namespace='Custom/LoadBalancer',
        MetricData=[
            {
                'MetricName': 'HealthyTargets',
                'Value': healthy_targets,
                'Unit': 'Count',
                'Timestamp': datetime.utcnow()
            }
        ]
    )
    
    return {
        'statusCode': 200,
        'body': json.dumps(f'Healthy targets: {healthy_targets}')
    }
EOF

echo "監視スクリプト作成完了"
```

## 🧪 Step 7: 負荷テストと検証

### 7.1 負荷テスト設定

```bash
# 負荷テスト用スクリプト
cat > load-test.sh << 'EOF'
#!/bin/bash

ALB_DNS=$1
DURATION=${2:-300}  # 5分間のテスト
CONCURRENT_USERS=${3:-50}

echo "Starting load test against $ALB_DNS"
echo "Duration: $DURATION seconds"
echo "Concurrent users: $CONCURRENT_USERS"

# Apache Bench を使用した負荷テスト
ab -n 10000 -c $CONCURRENT_USERS -t $DURATION http://$ALB_DNS/

# curl を使用した継続的なリクエスト
for i in {1..100}; do
    curl -s -w "%{http_code} %{time_total}s\n" http://$ALB_DNS/ >> load_test_results.txt
    sleep 1
done

echo "Load test completed. Results in load_test_results.txt"
EOF

chmod +x load-test.sh

# 使用例
# ./load-test.sh $ALB_DNS 300 50

echo "負荷テストスクリプト作成完了"
```

### 7.2 ヘルスチェック検証

```bash
# ヘルスチェック状態確認
cat > health-check.sh << 'EOF'
#!/bin/bash

TARGET_GROUP_ARN=$1

echo "=== Target Health Check Status ==="
aws elbv2 describe-target-health \
    --target-group-arn $TARGET_GROUP_ARN \
    --query 'TargetHealthDescriptions[*].{Target:Target.Id,Health:TargetHealth.State,Reason:TargetHealth.Reason}' \
    --output table

echo ""
echo "=== Load Balancer Metrics ==="
aws cloudwatch get-metric-statistics \
    --namespace AWS/ApplicationELB \
    --metric-name TargetResponseTime \
    --dimensions Name=LoadBalancer,Value=$(basename $ALB_ARN) \
    --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
    --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
    --period 300 \
    --statistics Average \
    --query 'Datapoints[*].{Time:Timestamp,AvgResponseTime:Average}' \
    --output table
EOF

chmod +x health-check.sh

echo "ヘルスチェック検証スクリプト作成完了"
```

## 🧹 Step 8: リソースクリーンアップ

### 8.1 ロードバランサー削除

```bash
# Auto Scaling Group 削除
aws autoscaling delete-auto-scaling-group \
    --auto-scaling-group-name "web-servers-asg" \
    --force-delete

# Launch Template 削除
aws ec2 delete-launch-template \
    --launch-template-id $LAUNCH_TEMPLATE_ID

# Load Balancer 削除
aws elbv2 delete-load-balancer --load-balancer-arn $ALB_ARN
aws elbv2 delete-load-balancer --load-balancer-arn $NLB_ARN
aws elbv2 delete-load-balancer --load-balancer-arn $GLB_ARN

# Target Group 削除
aws elbv2 delete-target-group --target-group-arn $TARGET_GROUP_ARN
aws elbv2 delete-target-group --target-group-arn $API_TARGET_GROUP_ARN
aws elbv2 delete-target-group --target-group-arn $TCP_TARGET_GROUP_ARN
aws elbv2 delete-target-group --target-group-arn $GATEWAY_TARGET_GROUP_ARN

echo "ロードバランサーリソース削除完了"
```

### 8.2 ネットワークリソース削除

```bash
# NAT Gateway 削除
aws ec2 delete-nat-gateway --nat-gateway-id $NAT_GW

# Elastic IP 解放
aws ec2 release-address --allocation-id $EIP_ALLOCATION

# Security Group 削除
aws ec2 delete-security-group --group-id $ALB_SG
aws ec2 delete-security-group --group-id $TARGET_SG

# Route Table 削除
aws ec2 delete-route-table --route-table-id $PUBLIC_RT
aws ec2 delete-route-table --route-table-id $PRIVATE_RT

# Subnet 削除
aws ec2 delete-subnet --subnet-id $PUBLIC_SUBNET_1
aws ec2 delete-subnet --subnet-id $PUBLIC_SUBNET_2
aws ec2 delete-subnet --subnet-id $PRIVATE_SUBNET_1
aws ec2 delete-subnet --subnet-id $PRIVATE_SUBNET_2

# Internet Gateway デタッチ・削除
aws ec2 detach-internet-gateway --vpc-id $VPC_ID --internet-gateway-id $IGW_ID
aws ec2 delete-internet-gateway --internet-gateway-id $IGW_ID

# VPC 削除
aws ec2 delete-vpc --vpc-id $VPC_ID

echo "ネットワークリソース削除完了"
```

## 💰 コスト計算

### 推定コスト（月額）
- **Application Load Balancer**: $22.50/月
- **Network Load Balancer**: $22.50/月
- **Gateway Load Balancer**: $36.00/月
- **Auto Scaling インスタンス (t3.micro x4)**: $33.12/月
- **CloudFront**: $1.00/月（基本料金）
- **データ転送**: $20.00/月（想定）
- **合計**: 約 $135.12/月

## 📚 学習ポイント

### 重要な概念
1. **ロードバランサータイプ**: ALB vs NLB vs GLB の使い分け
2. **Auto Scaling**: 自動スケーリングの設計と実装
3. **ヘルスチェック**: 各種ヘルスチェック方式
4. **セキュリティ**: WAF、SSL/TLS、セキュリティグループ
5. **監視**: CloudWatch、Access Logs

### 実践的なスキル
- 高可用性アーキテクチャの設計
- パフォーマンス最適化の実装
- セキュリティベストプラクティス
- 運用監視の設定
- 負荷テストと検証

---

**次のステップ**: [Lab 4: セキュリティ・コンプライアンス](./lab04-security-compliance.md) では、ネットワークセキュリティの高度な実装を学習します。