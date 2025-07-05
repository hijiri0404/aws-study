# Lab 4: セキュリティ・コンプライアンス

## 🎯 学習目標

このラボでは、AWSネットワークのセキュリティ強化とコンプライアンス対応を学習します：

- VPC セキュリティの包括的な実装
- AWS Security Services の統合
- コンプライアンスフレームワークの実装
- セキュリティ監視とログ分析
- インシデント対応とフォレンジック

## 📋 前提条件

- AWS CLI が設定済み
- セキュリティの基礎知識
- [Lab 3: ロードバランシング](./lab03-load-balancing.md) の完了推奨

## 🏗️ アーキテクチャ概要

```
┌─────────────────────────────────────────────────────────────┐
│                  セキュリティ統合環境                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐     │
│  │     WAF     │    │ Shield DDoS │    │  GuardDuty  │     │
│  │  Protection │    │ Protection  │    │   Threat    │     │
│  │             │    │             │    │ Detection   │     │
│  └─────┬───────┘    └─────┬───────┘    └─────┬───────┘     │
│        │                  │                  │             │
│        ▼                  ▼                  ▼             │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │                VPC Security Hub                         │ │
│  │    Network ACLs + Security Groups + Flow Logs         │ │
│  └─────┬───────────────────────┬───────────────────────────┘ │
│        │                       │                             │
│        ▼                       ▼                             │
│  ┌─────────────┐         ┌─────────────┐                     │
│  │   Config    │         │ CloudTrail  │                     │
│  │ Compliance  │         │ Audit Log   │                     │
│  └─────────────┘         └─────────────┘                     │
└─────────────────────────────────────────────────────────────┘
```

## 🚀 Step 1: VPC セキュリティ基盤構築

### 1.1 セキュアVPC設計

```bash
# セキュリティ専用VPC作成
SECURITY_VPC_ID=$(aws ec2 create-vpc \
    --cidr-block 10.1.0.0/16 \
    --tag-specifications 'ResourceType=vpc,Tags=[{Key=Name,Value=Security-VPC},{Key=Environment,Value=Production},{Key=Compliance,Value=SOC2}]' \
    --query 'Vpc.VpcId' \
    --output text)

# VPC Flow Logs 有効化
FLOW_LOGS_ROLE_ARN="arn:aws:iam::$(aws sts get-caller-identity --query Account --output text):role/flowlogsRole"

aws ec2 create-flow-logs \
    --resource-type VPC \
    --resource-ids $SECURITY_VPC_ID \
    --traffic-type ALL \
    --log-destination-type cloud-watch-logs \
    --log-group-name VPCFlowLogs \
    --deliver-logs-permission-arn $FLOW_LOGS_ROLE_ARN \
    --tag-specifications 'ResourceType=vpc-flow-log,Tags=[{Key=Name,Value=Security-VPC-FlowLogs}]'

echo "セキュアVPC作成完了: $SECURITY_VPC_ID"
```

### 1.2 セグメント化されたサブネット設計

```bash
# DMZ（非武装地帯）サブネット
DMZ_SUBNET_1=$(aws ec2 create-subnet \
    --vpc-id $SECURITY_VPC_ID \
    --cidr-block 10.1.1.0/24 \
    --availability-zone us-east-1a \
    --tag-specifications 'ResourceType=subnet,Tags=[{Key=Name,Value=DMZ-Subnet-1a},{Key=Tier,Value=DMZ}]' \
    --query 'Subnet.SubnetId' \
    --output text)

DMZ_SUBNET_2=$(aws ec2 create-subnet \
    --vpc-id $SECURITY_VPC_ID \
    --cidr-block 10.1.2.0/24 \
    --availability-zone us-east-1b \
    --tag-specifications 'ResourceType=subnet,Tags=[{Key=Name,Value=DMZ-Subnet-1b},{Key=Tier,Value=DMZ}]' \
    --query 'Subnet.SubnetId' \
    --output text)

# Web Tier サブネット
WEB_SUBNET_1=$(aws ec2 create-subnet \
    --vpc-id $SECURITY_VPC_ID \
    --cidr-block 10.1.11.0/24 \
    --availability-zone us-east-1a \
    --tag-specifications 'ResourceType=subnet,Tags=[{Key=Name,Value=Web-Subnet-1a},{Key=Tier,Value=Web}]' \
    --query 'Subnet.SubnetId' \
    --output text)

WEB_SUBNET_2=$(aws ec2 create-subnet \
    --vpc-id $SECURITY_VPC_ID \
    --cidr-block 10.1.12.0/24 \
    --availability-zone us-east-1b \
    --tag-specifications 'ResourceType=subnet,Tags=[{Key=Name,Value=Web-Subnet-1b},{Key=Tier,Value=Web}]' \
    --query 'Subnet.SubnetId' \
    --output text)

# Application Tier サブネット
APP_SUBNET_1=$(aws ec2 create-subnet \
    --vpc-id $SECURITY_VPC_ID \
    --cidr-block 10.1.21.0/24 \
    --availability-zone us-east-1a \
    --tag-specifications 'ResourceType=subnet,Tags=[{Key=Name,Value=App-Subnet-1a},{Key=Tier,Value=Application}]' \
    --query 'Subnet.SubnetId' \
    --output text)

APP_SUBNET_2=$(aws ec2 create-subnet \
    --vpc-id $SECURITY_VPC_ID \
    --cidr-block 10.1.22.0/24 \
    --availability-zone us-east-1b \
    --tag-specifications 'ResourceType=subnet,Tags=[{Key=Name,Value=App-Subnet-1b},{Key=Tier,Value=Application}]' \
    --query 'Subnet.SubnetId' \
    --output text)

# Database Tier サブネット
DB_SUBNET_1=$(aws ec2 create-subnet \
    --vpc-id $SECURITY_VPC_ID \
    --cidr-block 10.1.31.0/24 \
    --availability-zone us-east-1a \
    --tag-specifications 'ResourceType=subnet,Tags=[{Key=Name,Value=DB-Subnet-1a},{Key=Tier,Value=Database}]' \
    --query 'Subnet.SubnetId' \
    --output text)

DB_SUBNET_2=$(aws ec2 create-subnet \
    --vpc-id $SECURITY_VPC_ID \
    --cidr-block 10.1.32.0/24 \
    --availability-zone us-east-1b \
    --tag-specifications 'ResourceType=subnet,Tags=[{Key=Name,Value=DB-Subnet-1b},{Key=Tier,Value=Database}]' \
    --query 'Subnet.SubnetId' \
    --output text)

echo "セグメント化サブネット作成完了"
```

### 1.3 Network ACLs による厳格な制御

```bash
# DMZ Network ACL
DMZ_NACL=$(aws ec2 create-network-acl \
    --vpc-id $SECURITY_VPC_ID \
    --tag-specifications 'ResourceType=network-acl,Tags=[{Key=Name,Value=DMZ-NACL}]' \
    --query 'NetworkAcl.NetworkAclId' \
    --output text)

# DMZ Ingress Rules
aws ec2 create-network-acl-entry \
    --network-acl-id $DMZ_NACL \
    --rule-number 100 \
    --protocol tcp \
    --port-range From=443,To=443 \
    --cidr-block 0.0.0.0/0 \
    --rule-action allow

aws ec2 create-network-acl-entry \
    --network-acl-id $DMZ_NACL \
    --rule-number 110 \
    --protocol tcp \
    --port-range From=80,To=80 \
    --cidr-block 0.0.0.0/0 \
    --rule-action allow

# DMZ Egress Rules
aws ec2 create-network-acl-entry \
    --network-acl-id $DMZ_NACL \
    --rule-number 100 \
    --protocol tcp \
    --port-range From=1024,To=65535 \
    --cidr-block 0.0.0.0/0 \
    --rule-action allow \
    --egress

# Web Tier Network ACL
WEB_NACL=$(aws ec2 create-network-acl \
    --vpc-id $SECURITY_VPC_ID \
    --tag-specifications 'ResourceType=network-acl,Tags=[{Key=Name,Value=Web-NACL}]' \
    --query 'NetworkAcl.NetworkAclId' \
    --output text)

# Web Tier から DMZ への通信のみ許可
aws ec2 create-network-acl-entry \
    --network-acl-id $WEB_NACL \
    --rule-number 100 \
    --protocol tcp \
    --port-range From=80,To=80 \
    --cidr-block 10.1.1.0/23 \
    --rule-action allow

aws ec2 create-network-acl-entry \
    --network-acl-id $WEB_NACL \
    --rule-number 110 \
    --protocol tcp \
    --port-range From=443,To=443 \
    --cidr-block 10.1.1.0/23 \
    --rule-action allow

# Network ACL をサブネットに関連付け
aws ec2 associate-network-acl --network-acl-id $DMZ_NACL --subnet-id $DMZ_SUBNET_1
aws ec2 associate-network-acl --network-acl-id $DMZ_NACL --subnet-id $DMZ_SUBNET_2
aws ec2 associate-network-acl --network-acl-id $WEB_NACL --subnet-id $WEB_SUBNET_1
aws ec2 associate-network-acl --network-acl-id $WEB_NACL --subnet-id $WEB_SUBNET_2

echo "Network ACLs設定完了"
```

### 1.4 セキュリティグループの詳細制御

```bash
# DMZ セキュリティグループ
DMZ_SG=$(aws ec2 create-security-group \
    --group-name DMZ-SecurityGroup \
    --description "DMZ tier security group" \
    --vpc-id $SECURITY_VPC_ID \
    --tag-specifications 'ResourceType=security-group,Tags=[{Key=Name,Value=DMZ-SG}]' \
    --query 'GroupId' \
    --output text)

# Web セキュリティグループ
WEB_SG=$(aws ec2 create-security-group \
    --group-name Web-SecurityGroup \
    --description "Web tier security group" \
    --vpc-id $SECURITY_VPC_ID \
    --tag-specifications 'ResourceType=security-group,Tags=[{Key=Name,Value=Web-SG}]' \
    --query 'GroupId' \
    --output text)

# Application セキュリティグループ
APP_SG=$(aws ec2 create-security-group \
    --group-name App-SecurityGroup \
    --description "Application tier security group" \
    --vpc-id $SECURITY_VPC_ID \
    --tag-specifications 'ResourceType=security-group,Tags=[{Key=Name,Value=App-SG}]' \
    --query 'GroupId' \
    --output text)

# Database セキュリティグループ
DB_SG=$(aws ec2 create-security-group \
    --group-name DB-SecurityGroup \
    --description "Database tier security group" \
    --vpc-id $SECURITY_VPC_ID \
    --tag-specifications 'ResourceType=security-group,Tags=[{Key=Name,Value=DB-SG}]' \
    --query 'GroupId' \
    --output text)

# セキュリティグループルール設定
# Web から App への通信
aws ec2 authorize-security-group-ingress \
    --group-id $APP_SG \
    --protocol tcp \
    --port 8080 \
    --source-group $WEB_SG

# App から DB への通信
aws ec2 authorize-security-group-ingress \
    --group-id $DB_SG \
    --protocol tcp \
    --port 3306 \
    --source-group $APP_SG

echo "セキュリティグループ設定完了"
```

## 🛡️ Step 2: AWS WAF とDDoS保護

### 2.1 AWS WAF Web ACL設定

```bash
# WAF Web ACL 作成
WAF_WEB_ACL_ID=$(aws wafv2 create-web-acl \
    --name "Security-WebACL" \
    --scope REGIONAL \
    --default-action Allow={} \
    --rules file://waf-rules.json \
    --visibility-config SampledRequestsEnabled=true,CloudWatchMetricsEnabled=true,MetricName=SecurityWebACL \
    --query 'Summary.Id' \
    --output text)

# WAF ルール設定ファイル作成
cat > waf-rules.json << 'EOF'
[
    {
        "Name": "SQLInjectionRule",
        "Priority": 1,
        "Statement": {
            "SqliMatchStatement": {
                "FieldToMatch": {
                    "AllQueryArguments": {}
                },
                "TextTransformations": [
                    {
                        "Priority": 0,
                        "Type": "URL_DECODE"
                    },
                    {
                        "Priority": 1,
                        "Type": "HTML_ENTITY_DECODE"
                    }
                ]
            }
        },
        "Action": {
            "Block": {}
        },
        "VisibilityConfig": {
            "SampledRequestsEnabled": true,
            "CloudWatchMetricsEnabled": true,
            "MetricName": "SQLInjectionRule"
        }
    },
    {
        "Name": "XSSRule",
        "Priority": 2,
        "Statement": {
            "XssMatchStatement": {
                "FieldToMatch": {
                    "Body": {}
                },
                "TextTransformations": [
                    {
                        "Priority": 0,
                        "Type": "URL_DECODE"
                    },
                    {
                        "Priority": 1,
                        "Type": "HTML_ENTITY_DECODE"
                    }
                ]
            }
        },
        "Action": {
            "Block": {}
        },
        "VisibilityConfig": {
            "SampledRequestsEnabled": true,
            "CloudWatchMetricsEnabled": true,
            "MetricName": "XSSRule"
        }
    },
    {
        "Name": "RateLimitRule",
        "Priority": 3,
        "Statement": {
            "RateBasedStatement": {
                "Limit": 1000,
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
    },
    {
        "Name": "GeoBlockRule",
        "Priority": 4,
        "Statement": {
            "GeoMatchStatement": {
                "CountryCodes": ["CN", "RU", "KP"]
            }
        },
        "Action": {
            "Block": {}
        },
        "VisibilityConfig": {
            "SampledRequestsEnabled": true,
            "CloudWatchMetricsEnabled": true,
            "MetricName": "GeoBlockRule"
        }
    }
]
EOF

echo "WAF Web ACL作成完了: $WAF_WEB_ACL_ID"
```

### 2.2 AWS Shield Advanced設定

```bash
# Shield Advanced サブスクリプション確認
aws shield describe-subscription

# Shield Advanced 保護対象リソース設定
cat > shield-protection.sh << 'EOF'
#!/bin/bash

# ALB ARN（実際の値に置き換え）
ALB_ARN=$1

if [ -z "$ALB_ARN" ]; then
    echo "Usage: $0 <ALB_ARN>"
    exit 1
fi

# Shield Advanced 保護を有効化
aws shield create-protection \
    --name "ALB-Shield-Protection" \
    --resource-arn $ALB_ARN

# DDoS Response Team (DRT) アクセス許可
aws shield associate-drt-role \
    --role-arn "arn:aws:iam::$(aws sts get-caller-identity --query Account --output text):role/DRTAccessRole"

echo "Shield Advanced protection enabled for $ALB_ARN"
EOF

chmod +x shield-protection.sh

echo "Shield Advanced設定スクリプト作成完了"
```

## 🔍 Step 3: 脅威検出とセキュリティ監視

### 3.1 Amazon GuardDuty設定

```bash
# GuardDuty 有効化
DETECTOR_ID=$(aws guardduty create-detector \
    --enable \
    --finding-publishing-frequency FIFTEEN_MINUTES \
    --query 'DetectorId' \
    --output text)

# IP セット作成（信頼できるIPアドレス）
TRUSTED_IP_SET=$(aws guardduty create-ip-set \
    --detector-id $DETECTOR_ID \
    --name "TrustedIPSet" \
    --format TXT \
    --location s3://your-security-bucket/trusted-ips.txt \
    --activate \
    --query 'IpSetId' \
    --output text)

# 脅威インテルジェンスセット作成
THREAT_INTEL_SET=$(aws guardduty create-threat-intel-set \
    --detector-id $DETECTOR_ID \
    --name "ThreatIntelSet" \
    --format TXT \
    --location s3://your-security-bucket/threat-intel.txt \
    --activate \
    --query 'ThreatIntelSetId' \
    --output text)

echo "GuardDuty設定完了: $DETECTOR_ID"
```

### 3.2 AWS Security Hub統合

```bash
# Security Hub 有効化
aws securityhub enable-security-hub \
    --enable-default-standards

# 標準的なセキュリティスタンダード有効化
aws securityhub batch-enable-standards \
    --standards-subscription-requests StandardsArn=arn:aws:securityhub:::ruleset/finding-format/aws-foundational-security-standard/v/1.0.0

# カスタムインサイト作成
aws securityhub create-insight \
    --name "High-Severity-Network-Findings" \
    --filters '{
        "SeverityLabel": [
            {
                "Value": "HIGH",
                "Comparison": "EQUALS"
            }
        ],
        "Type": [
            {
                "Value": "Effects/Network",
                "Comparison": "STARTS_WITH"
            }
        ]
    }' \
    --group-by-attribute "Type"

echo "Security Hub設定完了"
```

### 3.3 AWS Config コンプライアンス監視

```bash
# Config 設定ファイル作成
cat > config-rules.json << 'EOF'
[
    {
        "ConfigRuleName": "vpc-sg-open-only-to-authorized-ports",
        "Source": {
            "Owner": "AWS",
            "SourceIdentifier": "INCOMING_SSH_DISABLED"
        }
    },
    {
        "ConfigRuleName": "vpc-default-security-group-closed",
        "Source": {
            "Owner": "AWS",
            "SourceIdentifier": "VPC_DEFAULT_SECURITY_GROUP_CLOSED"
        }
    },
    {
        "ConfigRuleName": "vpc-flow-logs-enabled",
        "Source": {
            "Owner": "AWS",
            "SourceIdentifier": "VPC_FLOW_LOGS_ENABLED"
        }
    }
]
EOF

# Config ルール適用
for rule in $(cat config-rules.json | jq -r '.[].ConfigRuleName'); do
    aws configservice put-config-rule \
        --config-rule file://config-rules.json
done

echo "AWS Config ルール設定完了"
```

## 📋 Step 4: コンプライアンスフレームワーク実装

### 4.1 SOC 2 コンプライアンス

```bash
# SOC 2 要件に対応したタグ付け戦略
cat > soc2-tagging.sh << 'EOF'
#!/bin/bash

# データ分類タグ
RESOURCE_ID=$1
DATA_CLASSIFICATION=$2  # Public, Internal, Confidential, Restricted

aws ec2 create-tags \
    --resources $RESOURCE_ID \
    --tags Key=DataClassification,Value=$DATA_CLASSIFICATION \
           Key=SOC2Compliance,Value=Required \
           Key=DataRetention,Value=7Years \
           Key=EncryptionRequired,Value=Yes

echo "SOC 2 compliance tags applied to $RESOURCE_ID"
EOF

chmod +x soc2-tagging.sh

# 暗号化要件の実装
cat > encryption-compliance.sh << 'EOF'
#!/bin/bash

echo "=== Encryption Compliance Check ==="

# EBS 暗号化確認
echo "Checking EBS encryption..."
aws ec2 describe-volumes \
    --query 'Volumes[?Encrypted==`false`].{VolumeId:VolumeId,State:State}' \
    --output table

# S3 暗号化確認
echo "Checking S3 bucket encryption..."
for bucket in $(aws s3 ls | awk '{print $3}'); do
    encryption=$(aws s3api get-bucket-encryption --bucket $bucket 2>/dev/null)
    if [ $? -ne 0 ]; then
        echo "Bucket $bucket: No encryption configured"
    else
        echo "Bucket $bucket: Encryption enabled"
    fi
done

# RDS 暗号化確認
echo "Checking RDS encryption..."
aws rds describe-db-instances \
    --query 'DBInstances[?StorageEncrypted==`false`].{DBInstanceIdentifier:DBInstanceIdentifier,Engine:Engine}' \
    --output table
EOF

chmod +x encryption-compliance.sh

echo "SOC 2 コンプライアンススクリプト作成完了"
```

### 4.2 GDPR コンプライアンス

```bash
# GDPR データ保護要件実装
cat > gdpr-compliance.py << 'EOF'
import boto3
import json
from datetime import datetime, timedelta

class GDPRCompliance:
    def __init__(self):
        self.ec2 = boto3.client('ec2')
        self.s3 = boto3.client('s3')
        self.cloudtrail = boto3.client('cloudtrail')
    
    def data_mapping(self):
        """個人データの場所を特定"""
        # S3バケット内の個人データ検索
        buckets = self.s3.list_buckets()
        
        personal_data_locations = []
        for bucket in buckets['Buckets']:
            # タグ確認
            try:
                tags = self.s3.get_bucket_tagging(Bucket=bucket['Name'])
                for tag in tags['TagSet']:
                    if tag['Key'] == 'PersonalData' and tag['Value'] == 'Yes':
                        personal_data_locations.append(bucket['Name'])
            except:
                pass
        
        return personal_data_locations
    
    def audit_data_access(self, start_date, end_date):
        """個人データアクセスの監査"""
        events = self.cloudtrail.lookup_events(
            LookupAttributes=[
                {
                    'AttributeKey': 'EventName',
                    'AttributeValue': 'GetObject'
                }
            ],
            StartTime=start_date,
            EndTime=end_date
        )
        
        return events['Events']
    
    def data_retention_check(self):
        """データ保持期間の確認"""
        # S3 ライフサイクルポリシー確認
        buckets = self.s3.list_buckets()
        retention_violations = []
        
        for bucket in buckets['Buckets']:
            try:
                lifecycle = self.s3.get_bucket_lifecycle_configuration(
                    Bucket=bucket['Name']
                )
                # 保持期間チェックロジック
            except:
                retention_violations.append(bucket['Name'])
        
        return retention_violations

# 使用例
gdpr = GDPRCompliance()
personal_data = gdpr.data_mapping()
print(f"Personal data locations: {personal_data}")
EOF

echo "GDPR コンプライアンスツール作成完了"
```

### 4.3 PCI DSS コンプライアンス

```bash
# PCI DSS 要件実装
cat > pci-dss-compliance.sh << 'EOF'
#!/bin/bash

echo "=== PCI DSS Compliance Check ==="

# 要件 1: ファイアウォール設定
echo "1. Checking firewall configuration..."
aws ec2 describe-security-groups \
    --query 'SecurityGroups[?IpPermissions[?IpRanges[?CidrIp==`0.0.0.0/0`]]]' \
    --output table

# 要件 2: デフォルトパスワード変更
echo "2. Checking for default configurations..."
aws ec2 describe-instances \
    --query 'Reservations[].Instances[?KeyName==`default-key`]' \
    --output table

# 要件 3: カード会員データ保護
echo "3. Checking data protection..."
aws s3api list-buckets --query 'Buckets[*].Name' | \
    xargs -I {} sh -c 'echo "Bucket: {}"; aws s3api get-bucket-encryption --bucket {} 2>/dev/null || echo "No encryption"'

# 要件 4: 暗号化通信
echo "4. Checking encrypted transmission..."
aws elbv2 describe-listeners \
    --query 'Listeners[?Protocol!=`HTTPS`]' \
    --output table

# 要件 10: ログ監視
echo "10. Checking logging configuration..."
aws logs describe-log-groups \
    --query 'logGroups[*].{LogGroup:logGroupName,RetentionInDays:retentionInDays}' \
    --output table
EOF

chmod +x pci-dss-compliance.sh

echo "PCI DSS コンプライアンススクリプト作成完了"
```

## 📊 Step 5: セキュリティ監視とログ分析

### 5.1 CloudTrail 高度な設定

```bash
# CloudTrail 詳細設定
aws cloudtrail create-trail \
    --name "SecurityAuditTrail" \
    --s3-bucket-name "security-audit-logs-$(date +%s)" \
    --include-global-service-events \
    --is-multi-region-trail \
    --enable-log-file-validation \
    --event-selectors '[
        {
            "ReadWriteType": "All",
            "IncludeManagementEvents": true,
            "DataResources": [
                {
                    "Type": "AWS::S3::Object",
                    "Values": ["arn:aws:s3:::sensitive-bucket/*"]
                }
            ]
        }
    ]'

# CloudTrail Insights 有効化
aws cloudtrail put-insight-selectors \
    --trail-name "SecurityAuditTrail" \
    --insight-selectors '[
        {
            "InsightType": "ApiCallRateInsight"
        }
    ]'

echo "CloudTrail高度設定完了"
```

### 5.2 カスタムセキュリティメトリクス

```bash
# CloudWatch カスタムメトリクス作成
cat > security-metrics.py << 'EOF'
import boto3
import json
from datetime import datetime, timedelta

def create_security_metrics():
    cloudwatch = boto3.client('cloudwatch')
    ec2 = boto3.client('ec2')
    
    # 未使用セキュリティグループの検出
    unused_sgs = []
    security_groups = ec2.describe_security_groups()['SecurityGroups']
    
    for sg in security_groups:
        if sg['GroupName'] != 'default':
            # セキュリティグループの使用状況確認
            instances = ec2.describe_instances(
                Filters=[
                    {
                        'Name': 'instance.group-id',
                        'Values': [sg['GroupId']]
                    }
                ]
            )
            
            if not instances['Reservations']:
                unused_sgs.append(sg['GroupId'])
    
    # メトリクス送信
    cloudwatch.put_metric_data(
        Namespace='Custom/Security',
        MetricData=[
            {
                'MetricName': 'UnusedSecurityGroups',
                'Value': len(unused_sgs),
                'Unit': 'Count',
                'Timestamp': datetime.utcnow()
            }
        ]
    )
    
    return len(unused_sgs)

# セキュリティアラーム作成
def create_security_alarms():
    cloudwatch = boto3.client('cloudwatch')
    
    # 異常なAPI呼び出し数アラーム
    cloudwatch.put_metric_alarm(
        AlarmName='AbnormalAPICallRate',
        ComparisonOperator='GreaterThanThreshold',
        EvaluationPeriods=2,
        MetricName='CallCount',
        Namespace='CloudTrailMetrics',
        Period=300,
        Statistic='Sum',
        Threshold=1000.0,
        ActionsEnabled=True,
        AlarmActions=[
            'arn:aws:sns:us-east-1:123456789012:security-alerts'
        ],
        AlarmDescription='Abnormal API call rate detected'
    )

if __name__ == "__main__":
    unused_count = create_security_metrics()
    create_security_alarms()
    print(f"Unused security groups: {unused_count}")
EOF

echo "セキュリティメトリクススクリプト作成完了"
```

## 🚨 Step 6: インシデント対応とフォレンジック

### 6.1 自動インシデント対応

```bash
# インシデント対応Lambda関数
cat > incident-response.py << 'EOF'
import boto3
import json
import os

def lambda_handler(event, context):
    """
    セキュリティインシデント自動対応
    """
    
    # GuardDuty findings 処理
    if 'detail-type' in event and event['detail-type'] == 'GuardDuty Finding':
        finding = event['detail']
        severity = finding['severity']
        finding_type = finding['type']
        
        if severity >= 7.0:  # High severity
            response = handle_high_severity_incident(finding)
        elif severity >= 4.0:  # Medium severity
            response = handle_medium_severity_incident(finding)
        else:
            response = handle_low_severity_incident(finding)
        
        return response
    
    return {'statusCode': 200, 'body': 'No action required'}

def handle_high_severity_incident(finding):
    """高重要度インシデント対応"""
    ec2 = boto3.client('ec2')
    sns = boto3.client('sns')
    
    # 影響を受けたインスタンスを隔離
    if 'instanceDetails' in finding['service']:
        instance_id = finding['service']['instanceDetails']['instanceId']
        
        # セキュリティグループを隔離用に変更
        quarantine_sg = 'sg-quarantine123456'
        
        ec2.modify_instance_attribute(
            InstanceId=instance_id,
            Groups=[quarantine_sg]
        )
        
        # スナップショット作成（フォレンジック用）
        volumes = ec2.describe_volumes(
            Filters=[
                {
                    'Name': 'attachment.instance-id',
                    'Values': [instance_id]
                }
            ]
        )
        
        for volume in volumes['Volumes']:
            ec2.create_snapshot(
                VolumeId=volume['VolumeId'],
                Description=f'Forensic snapshot for incident {finding["id"]}'
            )
    
    # 緊急通知送信
    sns.publish(
        TopicArn=os.environ['EMERGENCY_TOPIC_ARN'],
        Subject='HIGH SEVERITY SECURITY INCIDENT',
        Message=json.dumps(finding, indent=2)
    )
    
    return {'statusCode': 200, 'body': 'High severity incident handled'}

def handle_medium_severity_incident(finding):
    """中重要度インシデント対応"""
    # CloudWatch Logs にログ出力
    import logging
    logging.warning(f"Medium severity incident: {finding['type']}")
    
    return {'statusCode': 200, 'body': 'Medium severity incident logged'}

def handle_low_severity_incident(finding):
    """低重要度インシデント対応"""
    # メトリクス更新のみ
    cloudwatch = boto3.client('cloudwatch')
    
    cloudwatch.put_metric_data(
        Namespace='Security/Incidents',
        MetricData=[
            {
                'MetricName': 'LowSeverityIncidents',
                'Value': 1,
                'Unit': 'Count'
            }
        ]
    )
    
    return {'statusCode': 200, 'body': 'Low severity incident recorded'}
EOF

echo "インシデント対応Lambda作成完了"
```

### 6.2 フォレンジック分析ツール

```bash
# フォレンジック分析スクリプト
cat > forensic-analysis.sh << 'EOF'
#!/bin/bash

INSTANCE_ID=$1
SNAPSHOT_ID=$2

if [ -z "$INSTANCE_ID" ] || [ -z "$SNAPSHOT_ID" ]; then
    echo "Usage: $0 <instance-id> <snapshot-id>"
    exit 1
fi

echo "=== Starting Forensic Analysis ==="
echo "Instance: $INSTANCE_ID"
echo "Snapshot: $SNAPSHOT_ID"

# フォレンジック用インスタンス起動
FORENSIC_INSTANCE=$(aws ec2 run-instances \
    --image-id ami-0c02fb55956c7d316 \
    --instance-type m5.large \
    --key-name forensic-key \
    --security-group-ids sg-forensic-analysis \
    --subnet-id subnet-forensic \
    --tag-specifications 'ResourceType=instance,Tags=[{Key=Name,Value=Forensic-Analysis},{Key=Purpose,Value=Security-Investigation}]' \
    --query 'Instances[0].InstanceId' \
    --output text)

# スナップショットからボリューム作成
FORENSIC_VOLUME=$(aws ec2 create-volume \
    --snapshot-id $SNAPSHOT_ID \
    --availability-zone us-east-1a \
    --tag-specifications 'ResourceType=volume,Tags=[{Key=Name,Value=Forensic-Evidence}]' \
    --query 'VolumeId' \
    --output text)

# フォレンジックインスタンスにボリュームアタッチ
aws ec2 attach-volume \
    --volume-id $FORENSIC_VOLUME \
    --instance-id $FORENSIC_INSTANCE \
    --device /dev/sdf

echo "Forensic environment prepared:"
echo "  Instance: $FORENSIC_INSTANCE"
echo "  Evidence volume: $FORENSIC_VOLUME"

# 分析コマンド生成
cat > forensic-commands.txt << FORENSIC
# フォレンジック分析コマンド例

# 1. ボリュームマウント（読み取り専用）
sudo mkdir /mnt/evidence
sudo mount -o ro /dev/xvdf1 /mnt/evidence

# 2. ファイルシステム分析
sudo find /mnt/evidence -type f -name "*.log" -exec ls -la {} \;
sudo find /mnt/evidence -type f -mtime -1 -exec ls -la {} \;

# 3. ネットワーク接続履歴
sudo cat /mnt/evidence/var/log/auth.log | grep "Accepted"
sudo cat /mnt/evidence/var/log/syslog | grep "connection"

# 4. プロセス実行履歴
sudo cat /mnt/evidence/var/log/audit/audit.log | grep "EXECVE"

# 5. ハッシュ値計算
sudo find /mnt/evidence -type f -exec md5sum {} \; > evidence-hashes.txt

# 6. メモリダンプ分析（if available）
sudo cat /mnt/evidence/proc/kcore > memory-dump.raw
FORENSIC

echo "Forensic analysis commands saved to forensic-commands.txt"
EOF

chmod +x forensic-analysis.sh

echo "フォレンジック分析ツール作成完了"
```

## 🧹 Step 7: リソースクリーンアップ

### 7.1 セキュリティリソース削除

```bash
# GuardDuty 無効化
aws guardduty delete-detector --detector-id $DETECTOR_ID

# Security Hub 無効化
aws securityhub disable-security-hub

# WAF Web ACL 削除
aws wafv2 delete-web-acl \
    --scope REGIONAL \
    --id $WAF_WEB_ACL_ID \
    --lock-token $(aws wafv2 get-web-acl --scope REGIONAL --id $WAF_WEB_ACL_ID --query 'LockToken' --output text)

echo "セキュリティサービス削除完了"
```

### 7.2 ネットワークリソース削除

```bash
# セキュリティグループ削除
aws ec2 delete-security-group --group-id $DMZ_SG
aws ec2 delete-security-group --group-id $WEB_SG
aws ec2 delete-security-group --group-id $APP_SG
aws ec2 delete-security-group --group-id $DB_SG

# Network ACL 削除
aws ec2 delete-network-acl --network-acl-id $DMZ_NACL
aws ec2 delete-network-acl --network-acl-id $WEB_NACL

# サブネット削除
for subnet in $DMZ_SUBNET_1 $DMZ_SUBNET_2 $WEB_SUBNET_1 $WEB_SUBNET_2 $APP_SUBNET_1 $APP_SUBNET_2 $DB_SUBNET_1 $DB_SUBNET_2; do
    aws ec2 delete-subnet --subnet-id $subnet
done

# VPC削除
aws ec2 delete-vpc --vpc-id $SECURITY_VPC_ID

echo "ネットワークリソース削除完了"
```

## 💰 コスト計算

### 推定コスト（月額）
- **GuardDuty**: $3.50/月（基本料金）
- **Security Hub**: $1.20/月（基本料金）
- **WAF**: $5.00/月（基本料金）
- **Config**: $2.00/月（基本料金）
- **CloudTrail**: $2.00/月（基本料金）
- **VPC Flow Logs**: $10.00/月（想定）
- **合計**: 約 $23.70/月

## 📚 学習ポイント

### 重要な概念
1. **多層防御**: Defense in Depth の実装
2. **ゼロトラスト**: 信頼しない前提でのセキュリティ設計
3. **コンプライアンス**: 各種規制への対応
4. **インシデント対応**: 自動化された対応システム
5. **継続的監視**: リアルタイムセキュリティ監視

### 実践的なスキル
- セキュリティアーキテクチャの設計
- 脅威検出システムの構築
- コンプライアンス要件の実装
- インシデント対応プロセスの自動化
- フォレンジック分析手法

---

**次のステップ**: [Lab 5: トラブルシューティング](./lab05-troubleshooting.md) では、ネットワーク問題の診断と解決を学習します。