# Lab 5: セキュリティ自動化とコンプライアンス

## 🎯 学習目標

このラボでは、AWS DevOpsにおけるセキュリティ自動化とコンプライアンスの実装を行い、以下のスキルを習得します：

- AWS Config によるコンプライアンス監視
- AWS Inspector による脆弱性スキャン自動化
- AWS Secrets Manager によるシークレット管理
- AWS WAF と Shield による攻撃防御
- セキュリティイベントの自動対応

## 📋 前提条件

- AWS CLI が設定済み
- 適切なIAM権限（Config、Inspector、WAF、Secrets Manager）
- [Lab 4: インシデント対応](./lab04-incident-response.md) の完了推奨

## 🏗️ アーキテクチャ概要

```
┌─────────────────────────────────────────────────────────────┐
│                  セキュリティ自動化システム                     │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐     │
│  │   AWS WAF   │    │   Config    │    │  Inspector  │     │
│  │   Shield    │    │   Rules     │    │  Scanning   │     │
│  └─────┬───────┘    └─────┬───────┘    └─────┬───────┘     │
│        │                  │                  │             │
│        ▼                  ▼                  ▼             │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │                 EventBridge                             │ │
│  │             Security Event Router                      │ │
│  └─────┬───────────────────────┬───────────────────────────┘ │
│        │                       │                             │
│        ▼                       ▼                             │
│  ┌─────────────┐         ┌─────────────┐                     │
│  │   Lambda    │         │  Secrets    │                     │
│  │ Auto-Remedy │         │  Manager    │                     │
│  │ Functions   │         │ Rotation    │                     │
│  └─────┬───────┘         └─────┬───────┘                     │
│        │                       │                             │
│        ▼                       ▼                             │
│  ┌─────────────┐         ┌─────────────┐                     │
│  │   Security  │         │   Compliance│                     │
│  │   Groups    │         │   Dashboard │                     │
│  │    & NACLs  │         │   Reports   │                     │
│  └─────────────┘         └─────────────┘                     │
└─────────────────────────────────────────────────────────────┘
```

## 🚀 Step 1: セキュリティ基盤構築

### 1.1 セキュリティインフラストラクチャ

```yaml
# security-infrastructure.yaml
AWSTemplateFormatVersion: '2010-09-09'
Description: 'Security and Compliance Infrastructure'

Parameters:
  Environment:
    Type: String
    Default: 'security-lab'
    Description: 'Environment name'

Resources:
  # VPC with security-focused configuration
  VPC:
    Type: AWS::EC2::VPC
    Properties:
      CidrBlock: 10.2.0.0/16
      EnableDnsHostnames: true
      EnableDnsSupport: true
      Tags:
        - Key: Name
          Value: !Sub '${Environment}-secure-vpc'

  # Flow Logs for network monitoring
  VPCFlowLogsRole:
    Type: AWS::IAM::Role
    Properties:
      AssumeRolePolicyDocument:
        Version: '2012-10-17'
        Statement:
          - Effect: Allow
            Principal:
              Service: vpc-flow-logs.amazonaws.com
            Action: sts:AssumeRole
      Policies:
        - PolicyName: CloudWatchLogPolicy
          PolicyDocument:
            Version: '2012-10-17'
            Statement:
              - Effect: Allow
                Action:
                  - logs:CreateLogGroup
                  - logs:CreateLogStream
                  - logs:PutLogEvents
                  - logs:DescribeLogGroups
                  - logs:DescribeLogStreams
                Resource: '*'

  VPCFlowLogsGroup:
    Type: AWS::Logs::LogGroup
    Properties:
      LogGroupName: !Sub '/aws/vpc/flowlogs/${Environment}'
      RetentionInDays: 30

  VPCFlowLogs:
    Type: AWS::EC2::FlowLog
    Properties:
      ResourceType: VPC
      ResourceId: !Ref VPC
      TrafficType: ALL
      LogDestinationType: cloud-watch-logs
      LogGroupName: !Ref VPCFlowLogsGroup
      DeliverLogsPermissionArn: !GetAtt VPCFlowLogsRole.Arn

  # Private Subnets for secure deployment
  PrivateSubnet1:
    Type: AWS::EC2::Subnet
    Properties:
      VpcId: !Ref VPC
      AvailabilityZone: !Select [0, !GetAZs '']
      CidrBlock: 10.2.1.0/24
      Tags:
        - Key: Name
          Value: !Sub '${Environment}-private-subnet-1'

  PrivateSubnet2:
    Type: AWS::EC2::Subnet
    Properties:
      VpcId: !Ref VPC
      AvailabilityZone: !Select [1, !GetAZs '']
      CidrBlock: 10.2.2.0/24
      Tags:
        - Key: Name
          Value: !Sub '${Environment}-private-subnet-2'

  # NAT Gateway for outbound internet access
  NATGatewayEIP:
    Type: AWS::EC2::EIP
    Properties:
      Domain: vpc

  PublicSubnet:
    Type: AWS::EC2::Subnet
    Properties:
      VpcId: !Ref VPC
      AvailabilityZone: !Select [0, !GetAZs '']
      CidrBlock: 10.2.100.0/24
      MapPublicIpOnLaunch: true
      Tags:
        - Key: Name
          Value: !Sub '${Environment}-public-subnet'

  InternetGateway:
    Type: AWS::EC2::InternetGateway
    Properties:
      Tags:
        - Key: Name
          Value: !Sub '${Environment}-igw'

  InternetGatewayAttachment:
    Type: AWS::EC2::VPCGatewayAttachment
    Properties:
      InternetGatewayId: !Ref InternetGateway
      VpcId: !Ref VPC

  NATGateway:
    Type: AWS::EC2::NatGateway
    Properties:
      AllocationId: !GetAtt NATGatewayEIP.AllocationId
      SubnetId: !Ref PublicSubnet

  # Route Tables
  PublicRouteTable:
    Type: AWS::EC2::RouteTable
    Properties:
      VpcId: !Ref VPC
      Tags:
        - Key: Name
          Value: !Sub '${Environment}-public-rt'

  PublicRoute:
    Type: AWS::EC2::Route
    DependsOn: InternetGatewayAttachment
    Properties:
      RouteTableId: !Ref PublicRouteTable
      DestinationCidrBlock: 0.0.0.0/0
      GatewayId: !Ref InternetGateway

  PublicSubnetRouteTableAssociation:
    Type: AWS::EC2::SubnetRouteTableAssociation
    Properties:
      RouteTableId: !Ref PublicRouteTable
      SubnetId: !Ref PublicSubnet

  PrivateRouteTable:
    Type: AWS::EC2::RouteTable
    Properties:
      VpcId: !Ref VPC
      Tags:
        - Key: Name
          Value: !Sub '${Environment}-private-rt'

  PrivateRoute:
    Type: AWS::EC2::Route
    Properties:
      RouteTableId: !Ref PrivateRouteTable
      DestinationCidrBlock: 0.0.0.0/0
      NatGatewayId: !Ref NATGateway

  PrivateSubnet1RouteTableAssociation:
    Type: AWS::EC2::SubnetRouteTableAssociation
    Properties:
      RouteTableId: !Ref PrivateRouteTable
      SubnetId: !Ref PrivateSubnet1

  PrivateSubnet2RouteTableAssociation:
    Type: AWS::EC2::SubnetRouteTableAssociation
    Properties:
      RouteTableId: !Ref PrivateRouteTable
      SubnetId: !Ref PrivateSubnet2

  # Security Groups with strict rules
  WebTierSecurityGroup:
    Type: AWS::EC2::SecurityGroup
    Properties:
      GroupName: !Sub '${Environment}-web-tier-sg'
      GroupDescription: 'Security group for web tier'
      VpcId: !Ref VPC
      SecurityGroupIngress:
        - IpProtocol: tcp
          FromPort: 443
          ToPort: 443
          CidrIp: 0.0.0.0/0
          Description: 'HTTPS from anywhere'
        - IpProtocol: tcp
          FromPort: 80
          ToPort: 80
          CidrIp: 0.0.0.0/0
          Description: 'HTTP from anywhere'
      SecurityGroupEgress:
        - IpProtocol: tcp
          FromPort: 443
          ToPort: 443
          CidrIp: 0.0.0.0/0
          Description: 'HTTPS to anywhere'
      Tags:
        - Key: Name
          Value: !Sub '${Environment}-web-tier-sg'

  AppTierSecurityGroup:
    Type: AWS::EC2::SecurityGroup
    Properties:
      GroupName: !Sub '${Environment}-app-tier-sg'
      GroupDescription: 'Security group for application tier'
      VpcId: !Ref VPC
      SecurityGroupIngress:
        - IpProtocol: tcp
          FromPort: 8080
          ToPort: 8080
          SourceSecurityGroupId: !Ref WebTierSecurityGroup
          Description: 'App port from web tier'
      SecurityGroupEgress:
        - IpProtocol: tcp
          FromPort: 443
          ToPort: 443
          CidrIp: 0.0.0.0/0
          Description: 'HTTPS to anywhere'
      Tags:
        - Key: Name
          Value: !Sub '${Environment}-app-tier-sg'

  # KMS Key for encryption
  SecurityKMSKey:
    Type: AWS::KMS::Key
    Properties:
      Description: 'KMS Key for Security Lab encryption'
      KeyPolicy:
        Version: '2012-10-17'
        Statement:
          - Effect: Allow
            Principal:
              AWS: !Sub 'arn:aws:iam::${AWS::AccountId}:root'
            Action: 'kms:*'
            Resource: '*'

  SecurityKMSKeyAlias:
    Type: AWS::KMS::Alias
    Properties:
      AliasName: !Sub 'alias/${Environment}-security-key'
      TargetKeyId: !Ref SecurityKMSKey

Outputs:
  VPCId:
    Description: 'VPC ID'
    Value: !Ref VPC
    Export:
      Name: !Sub '${AWS::StackName}-VPC-ID'
  
  PrivateSubnet1Id:
    Description: 'Private Subnet 1 ID'
    Value: !Ref PrivateSubnet1
    Export:
      Name: !Sub '${AWS::StackName}-PrivateSubnet1-ID'
  
  PrivateSubnet2Id:
    Description: 'Private Subnet 2 ID'
    Value: !Ref PrivateSubnet2
    Export:
      Name: !Sub '${AWS::StackName}-PrivateSubnet2-ID'
  
  WebTierSecurityGroupId:
    Description: 'Web Tier Security Group ID'
    Value: !Ref WebTierSecurityGroup
    Export:
      Name: !Sub '${AWS::StackName}-WebTierSG-ID'
  
  KMSKeyId:
    Description: 'KMS Key ID'
    Value: !Ref SecurityKMSKey
    Export:
      Name: !Sub '${AWS::StackName}-KMSKey-ID'
```

### 1.2 インフラストラクチャデプロイ

```bash
# CloudFormation スタック作成
aws cloudformation create-stack \
  --stack-name security-compliance-infrastructure \
  --template-body file://security-infrastructure.yaml \
  --capabilities CAPABILITY_IAM

# デプロイ完了待機
aws cloudformation wait stack-create-complete \
  --stack-name security-compliance-infrastructure
```

## 🔒 Step 2: AWS Secrets Manager 実装

### 2.1 シークレット管理の自動化

```python
# setup-secrets-manager.py
import boto3
import json
import time
from datetime import datetime

secrets_manager = boto3.client('secretsmanager')
lambda_client = boto3.client('lambda')
iam = boto3.client('iam')

def create_database_secret():
    """データベースシークレットの作成"""
    
    secret_value = {
        "username": "admin",
        "password": "TempPassword123!",
        "engine": "mysql",
        "host": "mysql.example.com",
        "port": 3306,
        "dbname": "production"
    }
    
    try:
        response = secrets_manager.create_secret(
            Name='security-lab/database/credentials',
            Description='Database credentials for security lab',
            SecretString=json.dumps(secret_value),
            KmsKeyId='alias/security-lab-security-key'
        )
        
        print(f"Secret created: {response['ARN']}")
        return response['ARN']
        
    except secrets_manager.exceptions.ResourceExistsException:
        print("Secret already exists")
        response = secrets_manager.describe_secret(
            SecretId='security-lab/database/credentials'
        )
        return response['ARN']

def create_api_key_secret():
    """API キーシークレットの作成"""
    
    secret_value = {
        "api_key": "sk-1234567890abcdef",
        "api_secret": "abcdef1234567890",
        "endpoint": "https://api.example.com"
    }
    
    try:
        response = secrets_manager.create_secret(
            Name='security-lab/api/credentials',
            Description='API credentials for security lab',
            SecretString=json.dumps(secret_value),
            KmsKeyId='alias/security-lab-security-key'
        )
        
        print(f"API Secret created: {response['ARN']}")
        return response['ARN']
        
    except secrets_manager.exceptions.ResourceExistsException:
        print("API Secret already exists")
        response = secrets_manager.describe_secret(
            SecretId='security-lab/api/credentials'
        )
        return response['ARN']

def setup_automatic_rotation():
    """自動ローテーションの設定"""
    
    # Lambda実行ロール作成
    trust_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": {
                    "Service": "lambda.amazonaws.com"
                },
                "Action": "sts:AssumeRole"
            }
        ]
    }
    
    try:
        role_response = iam.create_role(
            RoleName='SecretsManagerRotationRole',
            AssumeRolePolicyDocument=json.dumps(trust_policy),
            Description='Role for Secrets Manager rotation function'
        )
        
        # 必要なポリシーをアタッチ
        iam.attach_role_policy(
            RoleName='SecretsManagerRotationRole',
            PolicyArn='arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole'
        )
        
        rotation_policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Action": [
                        "secretsmanager:DescribeSecret",
                        "secretsmanager:GetSecretValue",
                        "secretsmanager:PutSecretValue",
                        "secretsmanager:UpdateSecretVersionStage"
                    ],
                    "Resource": "*"
                }
            ]
        }
        
        iam.put_role_policy(
            RoleName='SecretsManagerRotationRole',
            PolicyName='SecretsManagerRotationPolicy',
            PolicyDocument=json.dumps(rotation_policy)
        )
        
        role_arn = role_response['Role']['Arn']
        
    except iam.exceptions.EntityAlreadyExistsException:
        role_arn = iam.get_role(RoleName='SecretsManagerRotationRole')['Role']['Arn']
    
    # ローテーション Lambda 関数
    rotation_function_code = '''
import json
import boto3
import random
import string

def lambda_handler(event, context):
    """Secrets Manager rotation function"""
    
    client = boto3.client('secretsmanager')
    service = boto3.client('rds')
    
    arn = event['Step1']['SecretArn']
    token = event['Step1']['ClientRequestToken']
    step = event['Step1']['Step']
    
    if step == "createSecret":
        create_secret(client, arn, token)
    elif step == "setSecret":
        set_secret(client, service, arn, token)
    elif step == "testSecret":
        test_secret(client, service, arn, token)
    elif step == "finishSecret":
        finish_secret(client, arn, token)
    else:
        raise ValueError(f"Invalid step parameter: {step}")

def create_secret(client, arn, token):
    """Generate new secret version"""
    try:
        current_secret = client.get_secret_value(SecretArn=arn, VersionStage="AWSCURRENT")
        current_password = json.loads(current_secret['SecretString'])
        
        # Generate new password
        new_password = ''.join(random.choices(string.ascii_letters + string.digits + '!@#$%^&*', k=16))
        current_password['password'] = new_password
        
        client.put_secret_value(
            SecretArn=arn,
            ClientRequestToken=token,
            SecretString=json.dumps(current_password),
            VersionStages=['AWSPENDING']
        )
        
    except client.exceptions.ResourceExistsException:
        pass

def set_secret(client, service, arn, token):
    """Set secret in database"""
    pending_secret = client.get_secret_value(SecretArn=arn, VersionId=token, VersionStage="AWSPENDING")
    pending_dict = json.loads(pending_secret['SecretString'])
    
    # In production, update database user password here
    print(f"Would update database password for user: {pending_dict['username']}")

def test_secret(client, service, arn, token):
    """Test new secret"""
    pending_secret = client.get_secret_value(SecretArn=arn, VersionId=token, VersionStage="AWSPENDING")
    pending_dict = json.loads(pending_secret['SecretString'])
    
    # In production, test database connection here
    print(f"Would test database connection for user: {pending_dict['username']}")

def finish_secret(client, arn, token):
    """Finalize secret rotation"""
    metadata = client.describe_secret(SecretArn=arn)
    
    for version in metadata['VersionIdsToStages']:
        if 'AWSCURRENT' in metadata['VersionIdsToStages'][version]:
            if version == token:
                return
            client.update_secret_version_stage(
                SecretArn=arn,
                VersionStage='AWSCURRENT',
                MoveToVersionId=token,
                RemoveFromVersionId=version
            )
            break
'''
    
    # Lambda 関数作成
    try:
        lambda_response = lambda_client.create_function(
            FunctionName='secrets-manager-rotation',
            Runtime='python3.9',
            Role=role_arn,
            Handler='index.lambda_handler',
            Code={'ZipFile': rotation_function_code},
            Description='Secrets Manager rotation function',
            Timeout=60
        )
        
        function_arn = lambda_response['FunctionArn']
        
    except lambda_client.exceptions.ResourceConflictException:
        function_arn = lambda_client.get_function(
            FunctionName='secrets-manager-rotation'
        )['Configuration']['FunctionArn']
    
    print(f"Rotation function created: {function_arn}")
    
    # 自動ローテーション有効化
    try:
        secrets_manager.rotate_secret(
            SecretId='security-lab/database/credentials',
            RotationLambdaARN=function_arn,
            RotationRules={
                'AutomaticallyAfterDays': 30
            }
        )
        
        print("Automatic rotation enabled for database credentials")
        
    except Exception as e:
        print(f"Error setting up rotation: {e}")

if __name__ == "__main__":
    print("Setting up Secrets Manager...")
    
    db_secret_arn = create_database_secret()
    api_secret_arn = create_api_key_secret()
    
    time.sleep(10)  # IAM権限伝播待機
    
    setup_automatic_rotation()
    
    print("Secrets Manager setup completed")
```

```bash
python3 setup-secrets-manager.py
```

## 🛡️ Step 3: AWS Config コンプライアンス監視

### 3.1 Config Rules の設定

```python
# setup-config-compliance.py
import boto3
import json
import time

config = boto3.client('config')
iam = boto3.client('iam')
s3 = boto3.client('s3')

def setup_config_service():
    """AWS Config サービスの設定"""
    
    # Config用のサービスロール作成
    trust_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": {
                    "Service": "config.amazonaws.com"
                },
                "Action": "sts:AssumeRole"
            }
        ]
    }
    
    try:
        role_response = iam.create_role(
            RoleName='AWSConfigServiceRole',
            AssumeRolePolicyDocument=json.dumps(trust_policy),
            Description='Service role for AWS Config'
        )
        
        # 必要なポリシーをアタッチ
        iam.attach_role_policy(
            RoleName='AWSConfigServiceRole',
            PolicyArn='arn:aws:iam::aws:policy/service-role/ConfigRole'
        )
        
        role_arn = role_response['Role']['Arn']
        
    except iam.exceptions.EntityAlreadyExistsException:
        role_arn = iam.get_role(RoleName='AWSConfigServiceRole')['Role']['Arn']
    
    # S3バケット作成（Config記録用）
    import random
    bucket_name = f'aws-config-security-lab-{random.randint(1000, 9999)}'
    
    try:
        s3.create_bucket(
            Bucket=bucket_name,
            CreateBucketConfiguration={'LocationConstraint': 'us-west-2'}
        )
        
        # バケットポリシー設定
        bucket_policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": {
                        "Service": "config.amazonaws.com"
                    },
                    "Action": "s3:GetBucketAcl",
                    "Resource": f"arn:aws:s3:::{bucket_name}"
                },
                {
                    "Effect": "Allow",
                    "Principal": {
                        "Service": "config.amazonaws.com"
                    },
                    "Action": "s3:PutObject",
                    "Resource": f"arn:aws:s3:::{bucket_name}/AWSLogs/*",
                    "Condition": {
                        "StringEquals": {
                            "s3:x-amz-acl": "bucket-owner-full-control"
                        }
                    }
                }
            ]
        }
        
        s3.put_bucket_policy(
            Bucket=bucket_name,
            Policy=json.dumps(bucket_policy)
        )
        
    except s3.exceptions.BucketAlreadyExists:
        bucket_name = 'aws-config-security-lab-existing'
    
    # Configuration Recorder設定
    try:
        config.put_configuration_recorder(
            ConfigurationRecorder={
                'name': 'security-lab-recorder',
                'roleARN': role_arn,
                'recordingGroup': {
                    'allSupported': True,
                    'includeGlobalResourceTypes': True
                }
            }
        )
        
        # Delivery Channel設定
        config.put_delivery_channel(
            DeliveryChannel={
                'name': 'security-lab-delivery',
                's3BucketName': bucket_name,
                'configSnapshotDeliveryProperties': {
                    'deliveryFrequency': 'TwentyFour_Hours'
                }
            }
        )
        
        # Configuration Recorder開始
        config.start_configuration_recorder(
            ConfigurationRecorderName='security-lab-recorder'
        )
        
        print(f"AWS Config setup completed. S3 bucket: {bucket_name}")
        
    except Exception as e:
        print(f"Config setup error: {e}")
    
    return bucket_name

def create_security_config_rules():
    """セキュリティ関連のConfig Rules作成"""
    
    security_rules = [
        {
            'ConfigRuleName': 'encrypted-volumes',
            'Source': {
                'Owner': 'AWS',
                'SourceIdentifier': 'ENCRYPTED_VOLUMES'
            },
            'Description': 'EBS volumes must be encrypted'
        },
        {
            'ConfigRuleName': 'security-group-ssh-check',
            'Source': {
                'Owner': 'AWS',
                'SourceIdentifier': 'INCOMING_SSH_DISABLED'
            },
            'Description': 'Security groups should not allow unrestricted SSH access'
        },
        {
            'ConfigRuleName': 'root-access-key-check',
            'Source': {
                'Owner': 'AWS',
                'SourceIdentifier': 'ROOT_ACCESS_KEY_CHECK'
            },
            'Description': 'Root user should not have access keys'
        },
        {
            'ConfigRuleName': 'iam-password-policy',
            'Source': {
                'Owner': 'AWS',
                'SourceIdentifier': 'IAM_PASSWORD_POLICY'
            },
            'InputParameters': json.dumps({
                'RequireUppercaseCharacters': 'true',
                'RequireLowercaseCharacters': 'true',
                'RequireNumbers': 'true',
                'RequireSymbols': 'true',
                'MinimumPasswordLength': '14'
            }),
            'Description': 'IAM password policy should meet requirements'
        },
        {
            'ConfigRuleName': 's3-bucket-public-read-prohibited',
            'Source': {
                'Owner': 'AWS',
                'SourceIdentifier': 'S3_BUCKET_PUBLIC_READ_PROHIBITED'
            },
            'Description': 'S3 buckets should not allow public read access'
        },
        {
            'ConfigRuleName': 's3-bucket-ssl-requests-only',
            'Source': {
                'Owner': 'AWS',
                'SourceIdentifier': 'S3_BUCKET_SSL_REQUESTS_ONLY'
            },
            'Description': 'S3 buckets should require SSL requests'
        }
    ]
    
    for rule in security_rules:
        try:
            config.put_config_rule(ConfigRule=rule)
            print(f"Config rule created: {rule['ConfigRuleName']}")
            
        except Exception as e:
            print(f"Error creating rule {rule['ConfigRuleName']}: {e}")

def create_remediation_configurations():
    """自動修復設定の作成"""
    
    remediation_configs = [
        {
            'ConfigRuleName': 'security-group-ssh-check',
            'TargetType': 'SSM_DOCUMENT',
            'TargetId': 'AWS-RemoveUnrestrictedSourceInSecurityGroup',
            'TargetVersion': '1',
            'Parameters': {
                'AutomationAssumeRole': {
                    'StaticValue': {
                        'Values': ['arn:aws:iam::123456789012:role/ConfigRemediationRole']
                    }
                },
                'GroupId': {
                    'ResourceValue': {
                        'Value': 'RESOURCE_ID'
                    }
                },
                'IpProtocol': {
                    'StaticValue': {
                        'Values': ['tcp']
                    }
                },
                'FromPort': {
                    'StaticValue': {
                        'Values': ['22']
                    }
                }
            },
            'Automatic': True,
            'MaximumAutomaticAttempts': 3
        }
    ]
    
    for remediation_config in remediation_configs:
        try:
            config.put_remediation_configurations(
                RemediationConfigurations=[remediation_config]
            )
            print(f"Remediation configuration created: {remediation_config['ConfigRuleName']}")
            
        except Exception as e:
            print(f"Error creating remediation: {e}")

if __name__ == "__main__":
    print("Setting up AWS Config compliance monitoring...")
    
    bucket_name = setup_config_service()
    time.sleep(30)  # Config service初期化待機
    
    create_security_config_rules()
    create_remediation_configurations()
    
    print("AWS Config compliance monitoring setup completed")
```

```bash
python3 setup-config-compliance.py
```

## 🔍 Step 4: AWS Inspector 脆弱性スキャン

### 4.1 Inspector V2 の設定

```python
# setup-inspector-scanning.py
import boto3
import json
import time

inspector = boto3.client('inspector2')
ec2 = boto3.client('ec2')
events = boto3.client('events')
lambda_client = boto3.client('lambda')

def enable_inspector():
    """Inspector V2 を有効化"""
    
    try:
        # Inspector V2 有効化
        response = inspector.enable(
            accountIds=[boto3.client('sts').get_caller_identity()['Account']],
            resourceTypes=['ECR', 'EC2']
        )
        
        print("Inspector V2 enabled successfully")
        print(f"Response: {response}")
        
    except Exception as e:
        print(f"Error enabling Inspector: {e}")

def create_inspector_findings_processor():
    """Inspector findings を処理するLambda関数"""
    
    findings_processor_code = '''
import json
import boto3
from datetime import datetime

def lambda_handler(event, context):
    """Process Inspector findings and take action"""
    
    print(f"Received event: {json.dumps(event)}")
    
    # EventBridge経由でのInspector findings
    if 'source' in event and event['source'] == 'aws.inspector2':
        process_inspector_finding(event)
    
    return {
        'statusCode': 200,
        'body': json.dumps('Inspector findings processed')
    }

def process_inspector_finding(event):
    """Inspector finding の処理"""
    
    detail = event.get('detail', {})
    finding_arn = detail.get('findingArn', '')
    severity = detail.get('severity', '')
    title = detail.get('title', '')
    
    print(f"Processing finding: {title}")
    print(f"Severity: {severity}")
    print(f"ARN: {finding_arn}")
    
    # 重要度に応じた処理
    if severity in ['CRITICAL', 'HIGH']:
        handle_critical_finding(detail)
    elif severity in ['MEDIUM']:
        handle_medium_finding(detail)
    else:
        handle_low_finding(detail)

def handle_critical_finding(detail):
    """重要な脆弱性への対応"""
    
    print("CRITICAL/HIGH severity finding detected")
    
    # SNS通知
    sns = boto3.client('sns')
    
    message = f"""
    CRITICAL Security Finding Detected!
    
    Title: {detail.get('title', 'N/A')}
    Severity: {detail.get('severity', 'N/A')}
    Resource: {detail.get('resources', [{}])[0].get('id', 'N/A')}
    Description: {detail.get('description', 'N/A')}
    
    Please investigate immediately.
    """
    
    try:
        sns.publish(
            TopicArn='arn:aws:sns:us-east-1:123456789012:security-alerts',
            Subject='CRITICAL Security Finding',
            Message=message
        )
        
        print("Critical finding notification sent")
        
    except Exception as e:
        print(f"Error sending notification: {e}")
    
    # 重要な場合は自動的にインスタンス隔離
    if should_isolate_resource(detail):
        isolate_resource(detail)

def handle_medium_finding(detail):
    """中程度の脆弱性への対応"""
    
    print("MEDIUM severity finding detected")
    
    # ログ記録
    import boto3
    
    cloudwatch = boto3.client('logs')
    
    log_entry = {
        'timestamp': datetime.utcnow().isoformat(),
        'finding': detail,
        'action': 'logged_for_review'
    }
    
    try:
        cloudwatch.put_log_events(
            logGroupName='/aws/security/inspector-findings',
            logStreamName=datetime.utcnow().strftime('%Y/%m/%d'),
            logEvents=[
                {
                    'timestamp': int(time.time() * 1000),
                    'message': json.dumps(log_entry)
                }
            ]
        )
        
    except Exception as e:
        print(f"Error logging finding: {e}")

def handle_low_finding(detail):
    """軽微な脆弱性への対応"""
    
    print("LOW severity finding detected - monitoring only")

def should_isolate_resource(detail):
    """リソース隔離が必要かの判断"""
    
    # 例: 実行中の悪意のあるプロセスが検出された場合
    title = detail.get('title', '').lower()
    
    dangerous_indicators = [
        'malware', 'backdoor', 'trojan', 'rootkit',
        'cryptominer', 'botnet', 'command and control'
    ]
    
    return any(indicator in title for indicator in dangerous_indicators)

def isolate_resource(detail):
    """リソースの隔離"""
    
    print("Isolating resource due to critical security finding")
    
    try:
        resources = detail.get('resources', [])
        
        for resource in resources:
            resource_type = resource.get('type', '')
            resource_id = resource.get('id', '')
            
            if resource_type == 'AWS_EC2_INSTANCE':
                isolate_ec2_instance(resource_id)
            elif resource_type == 'AWS_ECR_CONTAINER_IMAGE':
                quarantine_container_image(resource_id)
                
    except Exception as e:
        print(f"Error isolating resource: {e}")

def isolate_ec2_instance(instance_id):
    """EC2インスタンスの隔離"""
    
    ec2 = boto3.client('ec2')
    
    # 隔離用セキュリティグループ作成
    try:
        # インスタンス情報取得
        response = ec2.describe_instances(InstanceIds=[instance_id])
        instance = response['Reservations'][0]['Instances'][0]
        vpc_id = instance['VpcId']
        
        # 隔離用セキュリティグループ作成
        sg_response = ec2.create_security_group(
            GroupName=f'quarantine-{instance_id}',
            Description='Quarantine security group for compromised instance',
            VpcId=vpc_id
        )
        
        quarantine_sg_id = sg_response['GroupId']
        
        # インスタンスのセキュリティグループを隔離用に変更
        ec2.modify_instance_attribute(
            InstanceId=instance_id,
            Groups=[quarantine_sg_id]
        )
        
        print(f"Instance {instance_id} isolated with security group {quarantine_sg_id}")
        
    except Exception as e:
        print(f"Error isolating instance {instance_id}: {e}")

def quarantine_container_image(image_arn):
    """コンテナイメージの隔離"""
    
    print(f"Quarantining container image: {image_arn}")
    
    # ECRリポジトリポリシー更新でpull禁止
    # 実装は環境に応じて調整
'''
    
    # Lambda関数作成
    try:
        lambda_response = lambda_client.create_function(
            FunctionName='inspector-findings-processor',
            Runtime='python3.9',
            Role='arn:aws:iam::123456789012:role/lambda-execution-role',  # 実際のロールARNに変更
            Handler='index.lambda_handler',
            Code={'ZipFile': findings_processor_code},
            Description='Process Inspector findings and take automated action',
            Timeout=300,
            Environment={
                'Variables': {
                    'SNS_TOPIC_ARN': 'arn:aws:sns:us-east-1:123456789012:security-alerts'
                }
            }
        )
        
        function_arn = lambda_response['FunctionArn']
        print(f"Inspector findings processor created: {function_arn}")
        
    except lambda_client.exceptions.ResourceConflictException:
        function_arn = lambda_client.get_function(
            FunctionName='inspector-findings-processor'
        )['Configuration']['FunctionArn']
        print(f"Inspector findings processor already exists: {function_arn}")
    
    return function_arn

def setup_findings_eventbridge_rule(lambda_arn):
    """Inspector findings用のEventBridgeルール設定"""
    
    # EventBridge ルール作成
    rule_response = events.put_rule(
        Name='inspector-findings-rule',
        EventPattern=json.dumps({
            "source": ["aws.inspector2"],
            "detail-type": ["Inspector2 Finding"],
            "detail": {
                "severity": ["CRITICAL", "HIGH", "MEDIUM"]
            }
        }),
        State='ENABLED',
        Description='Route Inspector findings to processing function'
    )
    
    # Lambda ターゲット追加
    events.put_targets(
        Rule='inspector-findings-rule',
        Targets=[
            {
                'Id': '1',
                'Arn': lambda_arn
            }
        ]
    )
    
    # Lambda に EventBridge からの実行権限を付与
    try:
        lambda_client.add_permission(
            FunctionName='inspector-findings-processor',
            StatementId='AllowEventBridgeInvoke',
            Action='lambda:InvokeFunction',
            Principal='events.amazonaws.com',
            SourceArn=rule_response['RuleArn']
        )
        
    except lambda_client.exceptions.ResourceConflictException:
        print("Permission already exists")
    
    print("EventBridge rule for Inspector findings created")

if __name__ == "__main__":
    print("Setting up Inspector V2 scanning...")
    
    enable_inspector()
    
    time.sleep(10)  # Inspector初期化待機
    
    lambda_arn = create_inspector_findings_processor()
    setup_findings_eventbridge_rule(lambda_arn)
    
    print("Inspector V2 scanning setup completed")
```

```bash
python3 setup-inspector-scanning.py
```

## 🚨 Step 5: セキュリティダッシュボード

### 5.1 セキュリティ監視ダッシュボード

```python
# create-security-dashboard.py
import boto3
import json

cloudwatch = boto3.client('cloudwatch')

def create_security_dashboard():
    """セキュリティ監視ダッシュボード作成"""
    
    dashboard_body = {
        "widgets": [
            {
                "type": "metric",
                "x": 0,
                "y": 0,
                "width": 12,
                "height": 6,
                "properties": {
                    "metrics": [
                        ["AWS/Events", "SuccessfulInvocations", "RuleName", "inspector-findings-rule"],
                        [".", "FailedInvocations", ".", "."],
                        ["AWS/Config", "ComplianceByConfigRule", "ConfigRuleName", "encrypted-volumes"],
                        [".", ".", ".", "security-group-ssh-check"]
                    ],
                    "view": "timeSeries",
                    "stacked": False,
                    "region": "us-east-1",
                    "title": "Security Events & Compliance",
                    "period": 300
                }
            },
            {
                "type": "metric",
                "x": 12,
                "y": 0,
                "width": 12,
                "height": 6,
                "properties": {
                    "metrics": [
                        ["AWS/VpcFlowLogs", "PacketsReceived"],
                        [".", "PacketsDropped"],
                        ["AWS/WAF", "BlockedRequests", "WebACL", "SecurityLabWebACL"],
                        [".", "AllowedRequests", ".", "."]
                    ],
                    "view": "timeSeries",
                    "stacked": False,
                    "region": "us-east-1",
                    "title": "Network Security",
                    "period": 300
                }
            },
            {
                "type": "log",
                "x": 0,
                "y": 6,
                "width": 24,
                "height": 6,
                "properties": {
                    "query": "SOURCE '/aws/lambda/inspector-findings-processor' | fields @timestamp, @message\n| filter @message like /CRITICAL/\n| sort @timestamp desc\n| limit 20",
                    "region": "us-east-1",
                    "title": "Critical Security Findings",
                    "view": "table"
                }
            },
            {
                "type": "metric",
                "x": 0,
                "y": 12,
                "width": 12,
                "height": 6,
                "properties": {
                    "metrics": [
                        ["AWS/Lambda", "Invocations", "FunctionName", "inspector-findings-processor"],
                        [".", "Errors", ".", "."],
                        [".", "Duration", ".", "."]
                    ],
                    "view": "timeSeries",
                    "stacked": False,
                    "region": "us-east-1",
                    "title": "Security Automation Functions",
                    "period": 300
                }
            },
            {
                "type": "metric",
                "x": 12,
                "y": 12,
                "width": 12,
                "height": 6,
                "properties": {
                    "metrics": [
                        ["AWS/SecretsManager", "RotationScheduled"],
                        [".", "RotationSucceeded"],
                        [".", "RotationFailed"]
                    ],
                    "view": "timeSeries",
                    "stacked": False,
                    "region": "us-east-1",
                    "title": "Secrets Management",
                    "period": 300
                }
            }
        ]
    }
    
    # ダッシュボード作成
    response = cloudwatch.put_dashboard(
        DashboardName='SecurityComplianceDashboard',
        DashboardBody=json.dumps(dashboard_body)
    )
    
    print(f"Security Dashboard created successfully")
    
    return response

if __name__ == "__main__":
    create_security_dashboard()
```

```bash
python3 create-security-dashboard.py
```

## 🧪 Step 6: セキュリティテスト

### 6.1 セキュリティ設定の検証

```bash
# security-validation-test.sh
#!/bin/bash

echo "=== Security Configuration Validation ==="

# 1. Secrets Manager テスト
echo "1. Testing Secrets Manager..."
aws secretsmanager get-secret-value --secret-id security-lab/database/credentials --query 'SecretString' --output text | jq .

# 2. Config Rules 状態確認
echo "2. Checking Config Rules compliance..."
aws configservice get-compliance-details-by-config-rule --config-rule-name encrypted-volumes
aws configservice get-compliance-details-by-config-rule --config-rule-name security-group-ssh-check

# 3. Inspector 状態確認
echo "3. Checking Inspector status..."
aws inspector2 get-inspector-status

# 4. VPC Flow Logs 確認
echo "4. Checking VPC Flow Logs..."
aws logs describe-log-groups --log-group-name-prefix "/aws/vpc/flowlogs"

# 5. セキュリティグループ監査
echo "5. Auditing Security Groups..."
aws ec2 describe-security-groups --query 'SecurityGroups[?IpPermissions[?IpRanges[?CidrIp==`0.0.0.0/0`]]].[GroupId,GroupName]' --output table

# 6. IAM ユーザーのアクセスキー確認
echo "6. Checking IAM users with access keys..."
aws iam list-users --query 'Users[*].[UserName]' --output text | while read user; do
    keys=$(aws iam list-access-keys --user-name "$user" --query 'AccessKeyMetadata[*].AccessKeyId' --output text)
    if [ ! -z "$keys" ]; then
        echo "User $user has access keys: $keys"
    fi
done

echo "Security validation completed"
```

```bash
chmod +x security-validation-test.sh
./security-validation-test.sh
```

## 🔧 Step 7: クリーンアップ

### 7.1 リソース削除

```bash
# セキュリティリソースのクリーンアップ
echo "Cleaning up security resources..."

# Lambda関数削除
aws lambda delete-function --function-name inspector-findings-processor
aws lambda delete-function --function-name secrets-manager-rotation

# EventBridge ルール削除
aws events remove-targets --rule inspector-findings-rule --ids 1
aws events delete-rule --name inspector-findings-rule

# Config設定削除
aws configservice stop-configuration-recorder --configuration-recorder-name security-lab-recorder
aws configservice delete-configuration-recorder --configuration-recorder-name security-lab-recorder
aws configservice delete-delivery-channel --delivery-channel-name security-lab-delivery

# Secrets削除
aws secretsmanager delete-secret --secret-id security-lab/database/credentials --force-delete-without-recovery
aws secretsmanager delete-secret --secret-id security-lab/api/credentials --force-delete-without-recovery

# Inspector無効化
aws inspector2 disable --resource-types ECR EC2

# CloudWatch ダッシュボード削除
aws cloudwatch delete-dashboard --dashboard-name SecurityComplianceDashboard

# CloudFormation スタック削除
aws cloudformation delete-stack --stack-name security-compliance-infrastructure

echo "Security cleanup completed"
```

## 📚 学習のまとめ

このラボで学習した内容：

### 技術的スキル
- ✅ Secrets Manager による自動ローテーション
- ✅ Config Rules によるコンプライアンス監視
- ✅ Inspector による脆弱性スキャン自動化
- ✅ EventBridge によるセキュリティイベント処理
- ✅ 自動修復とインシデント対応

### セキュリティベストプラクティス
- ✅ 多層防御の実装
- ✅ 継続的なコンプライアンス監視
- ✅ 自動化されたセキュリティ対応
- ✅ セキュリティインシデントの可視化

### ビジネス価値
- ✅ セキュリティリスクの早期発見
- ✅ コンプライアンス違反の防止
- ✅ セキュリティ運用の効率化
- ✅ 監査対応の簡素化

## 🎯 次のステップ

1. **高度なセキュリティ**: AWS Security Hub 統合
2. **脅威検知**: Amazon GuardDuty 活用
3. **データ保護**: AWS Macie による機密データ検出
4. **ゼロトラスト**: IAM Identity Center 実装

---

**素晴らしい！** 包括的なセキュリティ自動化システムを構築できました。これらのスキルは現代のクラウドセキュリティ運用に不可欠です。