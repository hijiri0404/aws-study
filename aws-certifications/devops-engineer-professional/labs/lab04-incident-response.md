# Lab 4: 自動復旧システム構築

## 🎯 学習目標

このラボでは、AWS Systems Managerを中心とした自動復旧システムを構築し、以下のスキルを習得します：

- Systems Manager Automation Documents の作成
- EventBridge による自動イベント処理
- Lambda を使った自動復旧機能
- 段階的エスカレーション機能
- インシデント管理のベストプラクティス

## 📋 前提条件

- AWS CLI が設定済み
- 適切なIAM権限（Systems Manager、EventBridge、Lambda、SNS）
- [Lab 3: 監視システム](./lab03-monitoring-logging.md) の完了推奨

## 🏗️ アーキテクチャ概要

```
┌─────────────────────────────────────────────────────────────┐
│                    自動復旧システム全体図                       │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐     │
│  │ CloudWatch  │    │   Config    │    │  X-Ray      │     │
│  │   Alarms    │    │   Rules     │    │  Anomaly    │     │
│  └─────┬───────┘    └─────┬───────┘    └─────┬───────┘     │
│        │                  │                  │             │
│        ▼                  ▼                  ▼             │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │                  EventBridge                             │ │
│  │              Event Rules & Routing                      │ │
│  └─────┬───────────────────────┬───────────────────────────┘ │
│        │                       │                             │
│        ▼                       ▼                             │
│  ┌─────────────┐         ┌─────────────┐                     │
│  │   Lambda    │         │   Systems   │                     │
│  │ Auto-Heal   │         │  Manager    │                     │
│  │ Functions   │         │ Automation  │                     │
│  └─────┬───────┘         └─────┬───────┘                     │
│        │                       │                             │
│        ▼                       ▼                             │
│  ┌─────────────┐         ┌─────────────┐                     │
│  │   Target    │         │   Target    │                     │
│  │ Resources   │         │ Resources   │                     │
│  │ (EC2, RDS)  │         │ (EC2, ASG)  │                     │
│  └─────────────┘         └─────────────┘                     │
│                                                             │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │                SNS Notifications                        │ │
│  │        Slack/Email/PagerDuty Integration               │ │
│  └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

## 🚀 Step 1: 基盤環境構築

### 1.1 自動復旧インフラストラクチャ

```yaml
# incident-response-infrastructure.yaml
AWSTemplateFormatVersion: '2010-09-09'
Description: 'Incident Response and Auto-Healing Infrastructure'

Parameters:
  Environment:
    Type: String
    Default: 'incident-lab'
    Description: 'Environment name'

Resources:
  # VPC
  VPC:
    Type: AWS::EC2::VPC
    Properties:
      CidrBlock: 10.1.0.0/16
      EnableDnsHostnames: true
      EnableDnsSupport: true
      Tags:
        - Key: Name
          Value: !Sub '${Environment}-vpc'

  # Public Subnet
  PublicSubnet1:
    Type: AWS::EC2::Subnet
    Properties:
      VpcId: !Ref VPC
      AvailabilityZone: !Select [0, !GetAZs '']
      CidrBlock: 10.1.1.0/24
      MapPublicIpOnLaunch: true
      Tags:
        - Key: Name
          Value: !Sub '${Environment}-public-subnet-1'

  PublicSubnet2:
    Type: AWS::EC2::Subnet
    Properties:
      VpcId: !Ref VPC
      AvailabilityZone: !Select [1, !GetAZs '']
      CidrBlock: 10.1.2.0/24
      MapPublicIpOnLaunch: true
      Tags:
        - Key: Name
          Value: !Sub '${Environment}-public-subnet-2'

  # Internet Gateway
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

  # Route Table
  PublicRouteTable:
    Type: AWS::EC2::RouteTable
    Properties:
      VpcId: !Ref VPC
      Tags:
        - Key: Name
          Value: !Sub '${Environment}-public-rt'

  DefaultPublicRoute:
    Type: AWS::EC2::Route
    DependsOn: InternetGatewayAttachment
    Properties:
      RouteTableId: !Ref PublicRouteTable
      DestinationCidrBlock: 0.0.0.0/0
      GatewayId: !Ref InternetGateway

  PublicSubnet1RouteTableAssociation:
    Type: AWS::EC2::SubnetRouteTableAssociation
    Properties:
      RouteTableId: !Ref PublicRouteTable
      SubnetId: !Ref PublicSubnet1

  PublicSubnet2RouteTableAssociation:
    Type: AWS::EC2::SubnetRouteTableAssociation
    Properties:
      RouteTableId: !Ref PublicRouteTable
      SubnetId: !Ref PublicSubnet2

  # Security Groups
  WebServerSecurityGroup:
    Type: AWS::EC2::SecurityGroup
    Properties:
      GroupName: !Sub '${Environment}-web-sg'
      GroupDescription: 'Security group for web servers'
      VpcId: !Ref VPC
      SecurityGroupIngress:
        - IpProtocol: tcp
          FromPort: 80
          ToPort: 80
          CidrIp: 0.0.0.0/0
        - IpProtocol: tcp
          FromPort: 443
          ToPort: 443
          CidrIp: 0.0.0.0/0

  # Load Balancer
  ApplicationLoadBalancer:
    Type: AWS::ElasticLoadBalancingV2::LoadBalancer
    Properties:
      Name: !Sub '${Environment}-alb'
      Scheme: internet-facing
      Type: application
      Subnets:
        - !Ref PublicSubnet1
        - !Ref PublicSubnet2
      SecurityGroups:
        - !Ref WebServerSecurityGroup

  # Target Group
  TargetGroup:
    Type: AWS::ElasticLoadBalancingV2::TargetGroup
    Properties:
      Name: !Sub '${Environment}-tg'
      Port: 80
      Protocol: HTTP
      VpcId: !Ref VPC
      HealthCheckPath: '/health'
      HealthCheckIntervalSeconds: 30
      HealthCheckTimeoutSeconds: 5
      HealthyThresholdCount: 2
      UnhealthyThresholdCount: 3

  # Listener
  LoadBalancerListener:
    Type: AWS::ElasticLoadBalancingV2::Listener
    Properties:
      DefaultActions:
        - Type: forward
          TargetGroupArn: !Ref TargetGroup
      LoadBalancerArn: !Ref ApplicationLoadBalancer
      Port: 80
      Protocol: HTTP

  # Launch Template
  LaunchTemplate:
    Type: AWS::EC2::LaunchTemplate
    Properties:
      LaunchTemplateName: !Sub '${Environment}-launch-template'
      LaunchTemplateData:
        ImageId: ami-0c02fb55956c7d316  # Amazon Linux 2
        InstanceType: t3.micro
        SecurityGroupIds:
          - !Ref WebServerSecurityGroup
        IamInstanceProfile:
          Name: !Ref InstanceProfile
        UserData:
          Fn::Base64: !Sub |
            #!/bin/bash
            yum update -y
            yum install -y httpd amazon-ssm-agent
            systemctl start httpd
            systemctl enable httpd
            systemctl start amazon-ssm-agent
            systemctl enable amazon-ssm-agent
            
            # Simple web application
            cat > /var/www/html/index.html << 'EOF'
            <!DOCTYPE html>
            <html>
            <head><title>Incident Response Lab</title></head>
            <body>
                <h1>Auto-Healing Application</h1>
                <p>Instance ID: $(curl -s http://169.254.169.254/latest/meta-data/instance-id)</p>
                <p>Timestamp: $(date)</p>
            </body>
            </html>
            EOF
            
            # Health check endpoint
            cat > /var/www/html/health << 'EOF'
            OK
            EOF
            
            # Simulate application issues periodically
            cat > /usr/local/bin/issue-simulator.sh << 'EOF'
            #!/bin/bash
            while true; do
                sleep $((RANDOM % 3600 + 1800))  # 30-90 minutes
                if [ $((RANDOM % 10)) -eq 0 ]; then  # 10% chance
                    echo "Simulating application issue..."
                    systemctl stop httpd
                    sleep 300  # Issue lasts 5 minutes
                    systemctl start httpd
                fi
            done
            EOF
            chmod +x /usr/local/bin/issue-simulator.sh
            nohup /usr/local/bin/issue-simulator.sh &

  # Auto Scaling Group
  AutoScalingGroup:
    Type: AWS::AutoScaling::AutoScalingGroup
    Properties:
      AutoScalingGroupName: !Sub '${Environment}-asg'
      LaunchTemplate:
        LaunchTemplateId: !Ref LaunchTemplate
        Version: !GetAtt LaunchTemplate.LatestVersionNumber
      MinSize: 2
      MaxSize: 6
      DesiredCapacity: 2
      VPCZoneIdentifier:
        - !Ref PublicSubnet1
        - !Ref PublicSubnet2
      TargetGroupARNs:
        - !Ref TargetGroup
      HealthCheckType: ELB
      HealthCheckGracePeriod: 300
      Tags:
        - Key: Name
          Value: !Sub '${Environment}-instance'
          PropagateAtLaunch: true
        - Key: Environment
          Value: !Ref Environment
          PropagateAtLaunch: true

  # IAM Role for EC2 instances
  InstanceRole:
    Type: AWS::IAM::Role
    Properties:
      AssumeRolePolicyDocument:
        Version: '2012-10-17'
        Statement:
          - Effect: Allow
            Principal:
              Service: ec2.amazonaws.com
            Action: sts:AssumeRole
      ManagedPolicyArns:
        - arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore
        - arn:aws:iam::aws:policy/CloudWatchAgentServerPolicy

  InstanceProfile:
    Type: AWS::IAM::InstanceProfile
    Properties:
      Roles:
        - !Ref InstanceRole

  # SNS Topic for notifications
  IncidentNotificationTopic:
    Type: AWS::SNS::Topic
    Properties:
      TopicName: !Sub '${Environment}-incident-notifications'
      DisplayName: 'Incident Response Notifications'

Outputs:
  LoadBalancerDNS:
    Description: 'Application Load Balancer DNS'
    Value: !GetAtt ApplicationLoadBalancer.DNSName
    Export:
      Name: !Sub '${AWS::StackName}-ALB-DNS'
  
  AutoScalingGroupName:
    Description: 'Auto Scaling Group Name'
    Value: !Ref AutoScalingGroup
    Export:
      Name: !Sub '${AWS::StackName}-ASG-Name'
  
  SNSTopicArn:
    Description: 'SNS Topic ARN for notifications'
    Value: !Ref IncidentNotificationTopic
    Export:
      Name: !Sub '${AWS::StackName}-SNS-Topic'
```

### 1.2 インフラストラクチャデプロイ

```bash
# CloudFormation スタック作成
aws cloudformation create-stack \
  --stack-name incident-response-infrastructure \
  --template-body file://incident-response-infrastructure.yaml \
  --capabilities CAPABILITY_IAM

# デプロイ完了待機
aws cloudformation wait stack-create-complete \
  --stack-name incident-response-infrastructure

# 出力値確認
aws cloudformation describe-stacks \
  --stack-name incident-response-infrastructure \
  --query 'Stacks[0].Outputs'
```

## 🔧 Step 2: Lambda 自動復旧機能

### 2.1 インスタンス自動復旧Lambda

```python
# lambda-auto-heal-instance.py
import json
import boto3
import logging
from datetime import datetime

# ログ設定
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# AWS クライアント
ec2 = boto3.client('ec2')
ssm = boto3.client('ssm')
sns = boto3.client('sns')
cloudwatch = boto3.client('cloudwatch')

def lambda_handler(event, context):
    """
    インスタンス自動復旧Lambda関数
    CloudWatch Alarmからの通知を受信してインスタンスの自動復旧を実行
    """
    
    try:
        logger.info(f"Received event: {json.dumps(event)}")
        
        # SNS経由でのアラーム通知の場合
        if 'Records' in event:
            for record in event['Records']:
                if record['EventSource'] == 'aws:sns':
                    message = json.loads(record['Sns']['Message'])
                    process_alarm(message)
        
        # EventBridge経由の場合
        elif 'source' in event:
            process_instance_event(event)
        
        return {
            'statusCode': 200,
            'body': json.dumps('Auto-healing completed successfully')
        }
        
    except Exception as e:
        logger.error(f"Error in auto-healing: {str(e)}")
        send_notification(f"Auto-healing failed: {str(e)}", "ERROR")
        raise

def process_alarm(alarm_message):
    """CloudWatch アラームの処理"""
    
    alarm_name = alarm_message.get('AlarmName', '')
    state = alarm_message.get('NewStateValue', '')
    reason = alarm_message.get('NewStateReason', '')
    
    logger.info(f"Processing alarm: {alarm_name}, State: {state}")
    
    if state == 'ALARM':
        # アラームタイプに応じた復旧処理
        if 'HighCPU' in alarm_name:
            handle_high_cpu_alarm(alarm_message)
        elif 'InstanceDown' in alarm_name:
            handle_instance_down_alarm(alarm_message)
        elif 'HighMemory' in alarm_name:
            handle_high_memory_alarm(alarm_message)
        else:
            logger.info(f"No specific handler for alarm: {alarm_name}")

def process_instance_event(event):
    """EC2インスタンスイベントの処理"""
    
    if event['source'] == 'aws.ec2':
        detail = event['detail']
        state = detail.get('state', '')
        instance_id = detail.get('instance-id', '')
        
        if state == 'stopped':
            restart_instance(instance_id)
        elif state == 'terminated':
            handle_instance_termination(instance_id)

def handle_high_cpu_alarm(alarm_message):
    """高CPU使用率アラームの処理"""
    
    # アラーム詳細から対象インスタンス特定
    dimensions = alarm_message.get('Trigger', {}).get('Dimensions', [])
    instance_id = None
    
    for dimension in dimensions:
        if dimension['name'] == 'InstanceId':
            instance_id = dimension['value']
            break
    
    if not instance_id:
        logger.error("Could not find instance ID in alarm")
        return
    
    logger.info(f"Handling high CPU for instance: {instance_id}")
    
    # 1. CPU使用率詳細チェック
    cpu_stats = get_cpu_statistics(instance_id)
    
    if cpu_stats['average'] > 90:
        # 2. プロセス調査
        investigate_processes(instance_id)
        
        # 3. 自動スケーリング判断
        check_auto_scaling_needed(instance_id)
        
        # 4. 通知送信
        send_notification(
            f"High CPU detected on {instance_id}. Auto-scaling may be triggered.",
            "WARNING"
        )

def handle_instance_down_alarm(alarm_message):
    """インスタンスダウンアラームの処理"""
    
    dimensions = alarm_message.get('Trigger', {}).get('Dimensions', [])
    instance_id = None
    
    for dimension in dimensions:
        if dimension['name'] == 'InstanceId':
            instance_id = dimension['value']
            break
    
    if instance_id:
        logger.info(f"Attempting to restart instance: {instance_id}")
        restart_instance(instance_id)

def handle_high_memory_alarm(alarm_message):
    """高メモリ使用率アラームの処理"""
    
    dimensions = alarm_message.get('Trigger', {}).get('Dimensions', [])
    instance_id = None
    
    for dimension in dimensions:
        if dimension['name'] == 'InstanceId':
            instance_id = dimension['value']
            break
    
    if instance_id:
        logger.info(f"Handling high memory for instance: {instance_id}")
        
        # メモリクリーンアップ実行
        cleanup_memory(instance_id)

def restart_instance(instance_id):
    """インスタンスの再起動"""
    
    try:
        # インスタンス状態確認
        response = ec2.describe_instances(InstanceIds=[instance_id])
        instance = response['Reservations'][0]['Instances'][0]
        current_state = instance['State']['Name']
        
        logger.info(f"Instance {instance_id} current state: {current_state}")
        
        if current_state == 'stopped':
            # インスタンス開始
            ec2.start_instances(InstanceIds=[instance_id])
            logger.info(f"Started instance: {instance_id}")
            
            send_notification(
                f"Auto-recovery: Started instance {instance_id}",
                "INFO"
            )
            
        elif current_state == 'running':
            # 再起動
            ec2.reboot_instances(InstanceIds=[instance_id])
            logger.info(f"Rebooted instance: {instance_id}")
            
            send_notification(
                f"Auto-recovery: Rebooted instance {instance_id}",
                "INFO"
            )
            
    except Exception as e:
        logger.error(f"Failed to restart instance {instance_id}: {str(e)}")
        send_notification(
            f"Failed to restart instance {instance_id}: {str(e)}",
            "ERROR"
        )

def investigate_processes(instance_id):
    """プロセス調査（SSM経由）"""
    
    try:
        # top コマンドでプロセス確認
        response = ssm.send_command(
            InstanceIds=[instance_id],
            DocumentName='AWS-RunShellScript',
            Parameters={
                'commands': [
                    'top -b -n 1 | head -20',
                    'ps aux --sort=-%cpu | head -10',
                    'free -h',
                    'df -h'
                ]
            }
        )
        
        command_id = response['Command']['CommandId']
        logger.info(f"Process investigation command sent: {command_id}")
        
        # カスタムメトリクス送信
        cloudwatch.put_metric_data(
            Namespace='IncidentResponse/AutoHeal',
            MetricData=[
                {
                    'MetricName': 'ProcessInvestigation',
                    'Value': 1,
                    'Unit': 'Count',
                    'Dimensions': [
                        {
                            'Name': 'InstanceId',
                            'Value': instance_id
                        }
                    ]
                }
            ]
        )
        
    except Exception as e:
        logger.error(f"Failed to investigate processes: {str(e)}")

def cleanup_memory(instance_id):
    """メモリクリーンアップ"""
    
    try:
        response = ssm.send_command(
            InstanceIds=[instance_id],
            DocumentName='AWS-RunShellScript',
            Parameters={
                'commands': [
                    'sync',
                    'echo 3 > /proc/sys/vm/drop_caches',
                    'systemctl restart httpd',
                    'free -h'
                ]
            }
        )
        
        command_id = response['Command']['CommandId']
        logger.info(f"Memory cleanup command sent: {command_id}")
        
    except Exception as e:
        logger.error(f"Failed to cleanup memory: {str(e)}")

def get_cpu_statistics(instance_id):
    """CPU統計情報取得"""
    
    from datetime import timedelta
    
    try:
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(minutes=10)
        
        response = cloudwatch.get_metric_statistics(
            Namespace='AWS/EC2',
            MetricName='CPUUtilization',
            Dimensions=[
                {
                    'Name': 'InstanceId',
                    'Value': instance_id
                }
            ],
            StartTime=start_time,
            EndTime=end_time,
            Period=300,
            Statistics=['Average', 'Maximum']
        )
        
        if response['Datapoints']:
            datapoints = response['Datapoints']
            avg_cpu = sum(dp['Average'] for dp in datapoints) / len(datapoints)
            max_cpu = max(dp['Maximum'] for dp in datapoints)
            
            return {
                'average': avg_cpu,
                'maximum': max_cpu,
                'datapoints': len(datapoints)
            }
        
    except Exception as e:
        logger.error(f"Failed to get CPU statistics: {str(e)}")
    
    return {'average': 0, 'maximum': 0, 'datapoints': 0}

def check_auto_scaling_needed(instance_id):
    """オートスケーリング判断"""
    
    try:
        # Auto Scaling Group 情報取得
        autoscaling = boto3.client('autoscaling')
        
        response = ec2.describe_instances(InstanceIds=[instance_id])
        instance = response['Reservations'][0]['Instances'][0]
        
        # ASG名を タグから取得
        asg_name = None
        for tag in instance.get('Tags', []):
            if tag['Key'] == 'aws:autoscaling:groupName':
                asg_name = tag['Value']
                break
        
        if asg_name:
            # ASG 詳細取得
            asg_response = autoscaling.describe_auto_scaling_groups(
                AutoScalingGroupNames=[asg_name]
            )
            
            asg = asg_response['AutoScalingGroups'][0]
            current_capacity = asg['DesiredCapacity']
            max_capacity = asg['MaxSize']
            
            # スケールアウト判断
            if current_capacity < max_capacity:
                new_capacity = min(current_capacity + 1, max_capacity)
                
                autoscaling.set_desired_capacity(
                    AutoScalingGroupName=asg_name,
                    DesiredCapacity=new_capacity,
                    HonorCooldown=True
                )
                
                logger.info(f"Scaled out ASG {asg_name} to {new_capacity} instances")
                
                send_notification(
                    f"Auto-scaled ASG {asg_name} from {current_capacity} to {new_capacity} instances due to high CPU",
                    "INFO"
                )
    
    except Exception as e:
        logger.error(f"Failed to check auto scaling: {str(e)}")

def send_notification(message, level="INFO"):
    """通知送信"""
    
    try:
        topic_arn = "arn:aws:sns:us-east-1:123456789012:incident-response-notifications"  # 実際のARNに変更
        
        subject = f"[{level}] Auto-Healing Notification"
        
        sns.publish(
            TopicArn=topic_arn,
            Message=message,
            Subject=subject
        )
        
        logger.info(f"Notification sent: {message}")
        
    except Exception as e:
        logger.error(f"Failed to send notification: {str(e)}")
```

### 2.2 Lambda関数のデプロイ

```bash
# Lambdaパッケージ作成
mkdir lambda-auto-heal
cd lambda-auto-heal
cp ../lambda-auto-heal-instance.py .
zip -r lambda-auto-heal.zip .

# Lambda関数作成
aws lambda create-function \
  --function-name incident-response-auto-heal \
  --runtime python3.9 \
  --role arn:aws:iam::123456789012:role/lambda-execution-role \
  --handler lambda-auto-heal-instance.lambda_handler \
  --zip-file fileb://lambda-auto-heal.zip \
  --timeout 300 \
  --memory-size 256

# 環境変数設定
aws lambda update-function-configuration \
  --function-name incident-response-auto-heal \
  --environment Variables='{
    "SNS_TOPIC_ARN":"arn:aws:sns:us-east-1:123456789012:incident-response-notifications"
  }'
```

## 📋 Step 3: Systems Manager Automation

### 3.1 自動復旧 Automation Document

```yaml
# automation-document-instance-recovery.yaml
schemaVersion: '0.3'
description: 'Automated instance recovery with escalation'
assumeRole: '{{ AutomationAssumeRole }}'

parameters:
  InstanceId:
    type: String
    description: 'ID of the instance to recover'
  
  AutomationAssumeRole:
    type: String
    description: 'IAM role for automation execution'
    default: 'arn:aws:iam::{{global:ACCOUNT_ID}}:role/AutomationServiceRole'
  
  SNSTopicArn:
    type: String
    description: 'SNS topic for notifications'
  
  MaxRetries:
    type: Integer
    description: 'Maximum number of recovery attempts'
    default: 3

mainSteps:
  - name: checkInstanceStatus
    action: 'aws:executeAwsApi'
    description: 'Check current instance status'
    inputs:
      Service: ec2
      Api: DescribeInstances
      InstanceIds:
        - '{{ InstanceId }}'
    outputs:
      - Name: InstanceState
        Selector: '$.Reservations[0].Instances[0].State.Name'
        Type: String
      - Name: InstanceType
        Selector: '$.Reservations[0].Instances[0].InstanceType'
        Type: String

  - name: notifyRecoveryStart
    action: 'aws:executeAwsApi'
    description: 'Notify recovery process start'
    inputs:
      Service: sns
      Api: Publish
      TopicArn: '{{ SNSTopicArn }}'
      Subject: 'Instance Recovery Started'
      Message: 'Starting automated recovery for instance {{ InstanceId }}. Current state: {{ checkInstanceStatus.InstanceState }}'

  - name: attemptSimpleRestart
    action: 'aws:branch'
    description: 'Attempt simple restart if instance is running'
    inputs:
      Choices:
        - NextStep: rebootInstance
          Variable: '{{ checkInstanceStatus.InstanceState }}'
          StringEquals: running
        - NextStep: startInstance  
          Variable: '{{ checkInstanceStatus.InstanceState }}'
          StringEquals: stopped
      Default: checkInstanceHealth

  - name: rebootInstance
    action: 'aws:executeAwsApi'
    description: 'Reboot the instance'
    inputs:
      Service: ec2
      Api: RebootInstances
      InstanceIds:
        - '{{ InstanceId }}'
    nextStep: waitForInstanceRunning

  - name: startInstance
    action: 'aws:executeAwsApi'
    description: 'Start the instance'
    inputs:
      Service: ec2
      Api: StartInstances
      InstanceIds:
        - '{{ InstanceId }}'
    nextStep: waitForInstanceRunning

  - name: waitForInstanceRunning
    action: 'aws:waitForAwsResourceProperty'
    description: 'Wait for instance to be running'
    inputs:
      Service: ec2
      Api: DescribeInstances
      InstanceIds:
        - '{{ InstanceId }}'
      PropertySelector: '$.Reservations[0].Instances[0].State.Name'
      DesiredValues:
        - running
    timeoutSeconds: 600
    onFailure: Abort

  - name: checkInstanceHealth
    action: 'aws:executeAwsApi'
    description: 'Check instance health after restart'
    inputs:
      Service: ec2
      Api: DescribeInstanceStatus
      InstanceIds:
        - '{{ InstanceId }}'
    outputs:
      - Name: SystemStatus
        Selector: '$.InstanceStatuses[0].SystemStatus.Status'
        Type: String
      - Name: InstanceStatus
        Selector: '$.InstanceStatuses[0].InstanceStatus.Status'
        Type: String

  - name: runDiagnostics
    action: 'aws:runCommand'
    description: 'Run diagnostic commands'
    inputs:
      DocumentName: 'AWS-RunShellScript'
      InstanceIds:
        - '{{ InstanceId }}'
      Parameters:
        commands:
          - 'systemctl status httpd'
          - 'curl -s http://localhost/health || echo "Health check failed"'
          - 'top -b -n 1 | head -10'
          - 'free -h'
          - 'df -h'
          - 'journalctl -u httpd --since "5 minutes ago" --no-pager'
    timeoutSeconds: 300

  - name: attemptServiceRestart
    action: 'aws:runCommand'
    description: 'Attempt to restart failed services'
    inputs:
      DocumentName: 'AWS-RunShellScript'
      InstanceIds:
        - '{{ InstanceId }}'
      Parameters:
        commands:
          - 'systemctl restart httpd'
          - 'sleep 10'
          - 'systemctl status httpd'
          - 'curl -s http://localhost/health'
    timeoutSeconds: 180

  - name: verifyRecovery
    action: 'aws:runCommand'
    description: 'Verify recovery was successful'
    inputs:
      DocumentName: 'AWS-RunShellScript'
      InstanceIds:
        - '{{ InstanceId }}'
      Parameters:
        commands:
          - 'health_status=$(curl -s -o /dev/null -w "%{http_code}" http://localhost/health)'
          - 'if [ "$health_status" = "200" ]; then echo "SUCCESS: Health check passed"; else echo "FAILURE: Health check failed"; exit 1; fi'
    timeoutSeconds: 60
    onFailure: Continue

  - name: notifyRecoveryResult
    action: 'aws:executeAwsApi'
    description: 'Notify recovery result'
    inputs:
      Service: sns
      Api: Publish
      TopicArn: '{{ SNSTopicArn }}'
      Subject: 'Instance Recovery Completed'
      Message: 'Automated recovery completed for instance {{ InstanceId }}. System Status: {{ checkInstanceHealth.SystemStatus }}, Instance Status: {{ checkInstanceHealth.InstanceStatus }}'

outputs:
  - InstanceId: '{{ InstanceId }}'
  - FinalState: '{{ checkInstanceStatus.InstanceState }}'
  - SystemStatus: '{{ checkInstanceHealth.SystemStatus }}'
  - InstanceStatus: '{{ checkInstanceHealth.InstanceStatus }}'
```

### 3.2 Automation Document の作成

```bash
# Systems Manager Automation Document作成
aws ssm create-document \
  --name "IncidentResponse-InstanceRecovery" \
  --document-type "Automation" \
  --document-format YAML \
  --content file://automation-document-instance-recovery.yaml

# Document実行テスト
INSTANCE_ID=$(aws ec2 describe-instances \
  --filters "Name=tag:Name,Values=incident-lab-instance" \
  --query 'Reservations[0].Instances[0].InstanceId' \
  --output text)

aws ssm start-automation-execution \
  --document-name "IncidentResponse-InstanceRecovery" \
  --parameters "InstanceId=$INSTANCE_ID,SNSTopicArn=arn:aws:sns:us-east-1:123456789012:incident-response-notifications"
```

## 🔔 Step 4: EventBridge イベント処理

### 4.1 EventBridge Rules設定

```python
# setup-eventbridge-rules.py
import boto3
import json

events = boto3.client('events')

# Rule 1: EC2 Instance State Changes
rule1_response = events.put_rule(
    Name='EC2InstanceStateChanges',
    EventPattern=json.dumps({
        "source": ["aws.ec2"],
        "detail-type": ["EC2 Instance State-change Notification"],
        "detail": {
            "state": ["stopped", "terminated", "stopping"]
        }
    }),
    State='ENABLED',
    Description='Detect EC2 instance state changes for auto-recovery'
)

# Rule 2: CloudWatch Alarm State Changes  
rule2_response = events.put_rule(
    Name='CloudWatchAlarmStateChanges',
    EventPattern=json.dumps({
        "source": ["aws.cloudwatch"],
        "detail-type": ["CloudWatch Alarm State Change"],
        "detail": {
            "state": {
                "value": ["ALARM"]
            }
        }
    }),
    State='ENABLED',
    Description='Detect CloudWatch alarm state changes'
)

# Rule 3: Auto Scaling Events
rule3_response = events.put_rule(
    Name='AutoScalingEvents',
    EventPattern=json.dumps({
        "source": ["aws.autoscaling"],
        "detail-type": [
            "EC2 Instance Launch Unsuccessful",
            "EC2 Instance Terminate Unsuccessful"
        ]
    }),
    State='ENABLED',
    Description='Detect Auto Scaling issues'
)

# Lambda function ARN
lambda_function_arn = "arn:aws:lambda:us-east-1:123456789012:function:incident-response-auto-heal"

# Targets設定
targets = [
    {
        'rule_name': 'EC2InstanceStateChanges',
        'target_id': '1',
        'arn': lambda_function_arn
    },
    {
        'rule_name': 'CloudWatchAlarmStateChanges', 
        'target_id': '2',
        'arn': lambda_function_arn
    },
    {
        'rule_name': 'AutoScalingEvents',
        'target_id': '3', 
        'arn': lambda_function_arn
    }
]

for target in targets:
    events.put_targets(
        Rule=target['rule_name'],
        Targets=[
            {
                'Id': target['target_id'],
                'Arn': target['arn']
            }
        ]
    )

print("EventBridge rules and targets created successfully")

# Lambda permission for EventBridge
lambda_client = boto3.client('lambda')

for i, target in enumerate(targets, 1):
    try:
        lambda_client.add_permission(
            FunctionName='incident-response-auto-heal',
            StatementId=f'AllowEventBridge{i}',
            Action='lambda:InvokeFunction',
            Principal='events.amazonaws.com',
            SourceArn=f"arn:aws:events:us-east-1:123456789012:rule/{target['rule_name']}"
        )
    except lambda_client.exceptions.ResourceConflictException:
        print(f"Permission already exists for {target['rule_name']}")
```

```bash
python3 setup-eventbridge-rules.py
```

## 📊 Step 5: 高度な監視とアラート

### 5.1 予測アラームの設定

```python
# setup-predictive-alarms.py
import boto3

cloudwatch = boto3.client('cloudwatch')

# 予測アラーム設定
predictive_alarms = [
    {
        'AlarmName': 'PredictiveHighCPU',
        'ComparisonOperator': 'GreaterThanThreshold',
        'EvaluationPeriods': 2,
        'MetricName': 'CPUUtilization',
        'Namespace': 'AWS/EC2',
        'Period': 300,
        'Statistic': 'Average',
        'Threshold': 70.0,
        'ActionsEnabled': True,
        'AlarmActions': [
            'arn:aws:lambda:us-east-1:123456789012:function:incident-response-auto-heal'
        ],
        'AlarmDescription': 'Predictive alarm for high CPU - triggers before critical threshold',
        'TreatMissingData': 'notBreaching'
    },
    {
        'AlarmName': 'ApplicationResponseTimeAnomaly',
        'ComparisonOperator': 'LessThanLowerOrGreaterThanUpperThreshold',
        'EvaluationPeriods': 2,
        'Metrics': [
            {
                'Id': 'm1',
                'MetricStat': {
                    'Metric': {
                        'MetricName': 'ResponseTime',
                        'Namespace': 'AWS/ApplicationELB',
                        'Dimensions': [
                            {
                                'Name': 'LoadBalancer',
                                'Value': 'app/incident-lab-alb/1234567890123456'
                            }
                        ]
                    },
                    'Period': 300,
                    'Stat': 'Average'
                }
            },
            {
                'Id': 'ad1',
                'AnomalyDetector': {
                    'MetricMathAnomalyDetector': {
                        'MetricDataQueries': [
                            {
                                'Id': 'm1',
                                'MetricStat': {
                                    'Metric': {
                                        'MetricName': 'ResponseTime',
                                        'Namespace': 'AWS/ApplicationELB'
                                    },
                                    'Period': 300,
                                    'Stat': 'Average'
                                }
                            }
                        ]
                    }
                }
            }
        ],
        'ThresholdMetricId': 'ad1',
        'ActionsEnabled': True,
        'AlarmActions': [
            'arn:aws:lambda:us-east-1:123456789012:function:incident-response-auto-heal'
        ],
        'AlarmDescription': 'Anomaly detection for application response time'
    }
]

# 複合アラーム（複数条件の組み合わせ）
composite_alarm = {
    'AlarmName': 'SystemHealthComposite',
    'AlarmRule': '(ALARM("PredictiveHighCPU") OR ALARM("HighMemoryUtilization")) AND ALARM("ApplicationResponseTimeAnomaly")',
    'ActionsEnabled': True,
    'AlarmActions': [
        'arn:aws:sns:us-east-1:123456789012:incident-response-notifications'
    ],
    'AlarmDescription': 'Composite alarm for overall system health'
}

# アラーム作成
for alarm in predictive_alarms:
    if 'Metrics' in alarm:
        # 異常検知アラーム
        cloudwatch.put_anomaly_alarm(**alarm)
    else:
        # 通常のアラーム
        cloudwatch.put_metric_alarm(**alarm)
    
    print(f"Created alarm: {alarm['AlarmName']}")

# 複合アラーム作成
cloudwatch.put_composite_alarm(**composite_alarm)
print(f"Created composite alarm: {composite_alarm['AlarmName']}")
```

## 🧪 Step 6: 自動復旧システムのテスト

### 6.1 障害シミュレーション

```bash
# テスト用スクリプト作成
cat > test-incident-response.sh << 'EOF'
#!/bin/bash

echo "=== Incident Response System Test ==="

# Load Balancer DNS取得
ALB_DNS=$(aws cloudformation describe-stacks \
  --stack-name incident-response-infrastructure \
  --query 'Stacks[0].Outputs[?OutputKey==`LoadBalancerDNS`].OutputValue' \
  --output text)

echo "Testing endpoint: http://$ALB_DNS"

# 1. 正常動作確認
echo "1. Normal operation test..."
curl -s http://$ALB_DNS/health
echo

# 2. インスタンス停止テスト
echo "2. Instance stop test..."
INSTANCE_ID=$(aws ec2 describe-instances \
  --filters "Name=tag:Name,Values=incident-lab-instance" "Name=instance-state-name,Values=running" \
  --query 'Reservations[0].Instances[0].InstanceId' \
  --output text)

if [ "$INSTANCE_ID" != "None" ]; then
    echo "Stopping instance: $INSTANCE_ID"
    aws ec2 stop-instances --instance-ids $INSTANCE_ID
    
    # 復旧待機
    echo "Waiting for auto-recovery..."
    sleep 300
    
    # 結果確認
    echo "Checking recovery result..."
    curl -s http://$ALB_DNS/health
else
    echo "No running instance found"
fi

# 3. 高負荷シミュレーション
echo "3. High load simulation..."
for i in {1..100}; do
    curl -s http://$ALB_DNS > /dev/null &
done
wait

echo "Test completed"
EOF

chmod +x test-incident-response.sh
./test-incident-response.sh
```

### 6.2 負荷テストとスケーリング検証

```python
# load-test-auto-scaling.py
import concurrent.futures
import requests
import time
import boto3
from datetime import datetime

def send_request(url):
    """単一リクエスト送信"""
    try:
        response = requests.get(url, timeout=10)
        return {
            'status_code': response.status_code,
            'response_time': response.elapsed.total_seconds(),
            'timestamp': datetime.now()
        }
    except Exception as e:
        return {
            'status_code': 0,
            'response_time': 0,
            'error': str(e),
            'timestamp': datetime.now()
        }

def load_test(url, concurrent_users=50, duration_minutes=10):
    """負荷テスト実行"""
    
    print(f"Starting load test: {concurrent_users} users for {duration_minutes} minutes")
    
    end_time = time.time() + (duration_minutes * 60)
    results = []
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=concurrent_users) as executor:
        while time.time() < end_time:
            # 同時リクエスト送信
            futures = [executor.submit(send_request, url) for _ in range(concurrent_users)]
            
            for future in concurrent.futures.as_completed(futures):
                result = future.result()
                results.append(result)
                
                if len(results) % 100 == 0:
                    print(f"Completed {len(results)} requests")
            
            time.sleep(1)  # 1秒間隔
    
    return results

def analyze_results(results):
    """結果分析"""
    
    total_requests = len(results)
    successful_requests = sum(1 for r in results if r['status_code'] == 200)
    failed_requests = total_requests - successful_requests
    
    response_times = [r['response_time'] for r in results if r['response_time'] > 0]
    avg_response_time = sum(response_times) / len(response_times) if response_times else 0
    
    print(f"\n=== Load Test Results ===")
    print(f"Total Requests: {total_requests}")
    print(f"Successful: {successful_requests}")
    print(f"Failed: {failed_requests}")
    print(f"Success Rate: {(successful_requests/total_requests)*100:.2f}%")
    print(f"Average Response Time: {avg_response_time:.3f}s")

def monitor_auto_scaling():
    """オートスケーリング監視"""
    
    autoscaling = boto3.client('autoscaling')
    cloudwatch = boto3.client('cloudwatch')
    
    asg_name = "incident-lab-asg"  # 実際のASG名に変更
    
    print(f"\n=== Monitoring Auto Scaling Group: {asg_name} ===")
    
    for i in range(20):  # 20分間監視
        try:
            # ASG状態取得
            response = autoscaling.describe_auto_scaling_groups(
                AutoScalingGroupNames=[asg_name]
            )
            
            if response['AutoScalingGroups']:
                asg = response['AutoScalingGroups'][0]
                desired = asg['DesiredCapacity']
                instances = len(asg['Instances'])
                
                print(f"Time: {datetime.now().strftime('%H:%M:%S')} - Desired: {desired}, Running: {instances}")
            
            time.sleep(60)  # 1分間隔
            
        except Exception as e:
            print(f"Error monitoring ASG: {e}")

if __name__ == "__main__":
    # Load Balancer URL設定
    ALB_DNS = "your-alb-dns-name.us-east-1.elb.amazonaws.com"  # 実際のDNS名に変更
    url = f"http://{ALB_DNS}"
    
    # 並行して負荷テストとモニタリング実行
    import threading
    
    # モニタリング開始
    monitoring_thread = threading.Thread(target=monitor_auto_scaling)
    monitoring_thread.daemon = True
    monitoring_thread.start()
    
    # 負荷テスト実行
    results = load_test(url, concurrent_users=30, duration_minutes=15)
    analyze_results(results)
```

## 📊 Step 7: 運用ダッシュボード

### 7.1 インシデント対応ダッシュボード

```python
# create-incident-dashboard.py
import boto3
import json

cloudwatch = boto3.client('cloudwatch')

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
                    ["IncidentResponse/AutoHeal", "ProcessInvestigation"],
                    [".", "MemoryCleanup"],
                    [".", "InstanceRestart"],
                    [".", "ServiceRestart"]
                ],
                "view": "timeSeries",
                "stacked": False,
                "region": "us-east-1",
                "title": "Auto-Healing Actions",
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
                    ["AWS/AutoScaling", "GroupDesiredCapacity", "AutoScalingGroupName", "incident-lab-asg"],
                    [".", "GroupInServiceInstances", ".", "."],
                    [".", "GroupTotalInstances", ".", "."]
                ],
                "view": "timeSeries",
                "stacked": False,
                "region": "us-east-1",
                "title": "Auto Scaling Metrics",
                "period": 300
            }
        },
        {
            "type": "metric",
            "x": 0,
            "y": 6,
            "width": 24,
            "height": 6,
            "properties": {
                "metrics": [
                    ["AWS/ApplicationELB", "TargetResponseTime", "LoadBalancer", "app/incident-lab-alb/xxxxx"],
                    [".", "HTTPCode_Target_2XX_Count", ".", "."],
                    [".", "HTTPCode_Target_4XX_Count", ".", "."],
                    [".", "HTTPCode_Target_5XX_Count", ".", "."]
                ],
                "view": "timeSeries",
                "stacked": False,
                "region": "us-east-1",
                "title": "Application Performance",
                "period": 300
            }
        },
        {
            "type": "log",
            "x": 0,
            "y": 12,
            "width": 24,
            "height": 6,
            "properties": {
                "query": "SOURCE '/aws/lambda/incident-response-auto-heal' | fields @timestamp, @message\\n| filter @message like /ERROR/ or @message like /Auto-healing/\\n| sort @timestamp desc\\n| limit 20",
                "region": "us-east-1",
                "title": "Recent Auto-Healing Activities",
                "view": "table"
            }
        }
    ]
}

# ダッシュボード作成
response = cloudwatch.put_dashboard(
    DashboardName='IncidentResponseDashboard',
    DashboardBody=json.dumps(dashboard_body)
)

print(f"Incident Response Dashboard created successfully")
```

## 🔧 Step 8: クリーンアップ

### 8.1 リソース削除

```bash
# EventBridge ルール削除
aws events list-targets-by-rule --rule EC2InstanceStateChanges --query 'Targets[*].Id' --output text | \
xargs -r aws events remove-targets --rule EC2InstanceStateChanges --ids

aws events delete-rule --name EC2InstanceStateChanges
aws events delete-rule --name CloudWatchAlarmStateChanges  
aws events delete-rule --name AutoScalingEvents

# Lambda関数削除
aws lambda delete-function --function-name incident-response-auto-heal

# Systems Manager Document削除
aws ssm delete-document --name "IncidentResponse-InstanceRecovery"

# CloudWatch ダッシュボード削除
aws cloudwatch delete-dashboard --dashboard-name IncidentResponseDashboard

# CloudWatch アラーム削除
aws cloudwatch delete-alarms --alarm-names \
  PredictiveHighCPU \
  ApplicationResponseTimeAnomaly \
  SystemHealthComposite

# CloudFormation スタック削除
aws cloudformation delete-stack --stack-name incident-response-infrastructure

# 削除完了確認
aws cloudformation wait stack-delete-complete --stack-name incident-response-infrastructure
```

## 📚 学習のまとめ

このラボで学習した内容：

### 技術的スキル
- ✅ Systems Manager Automation Documents
- ✅ EventBridge による イベント駆動自動化
- ✅ Lambda ベースの自動復旧システム
- ✅ 予測アラームと異常検知
- ✅ 複合アラームの活用

### 運用ベストプラクティス
- ✅ 段階的エスカレーション
- ✅ 自動診断と復旧
- ✅ 包括的な通知システム
- ✅ 障害の予防的検知

### ビジネス価値
- ✅ MTTR (平均復旧時間) の大幅短縮
- ✅ 自動化による運用負荷軽減
- ✅ システム可用性の向上
- ✅ 人的エラーの削減

## 🎯 次のステップ

1. **[Lab 5: セキュリティ自動化](./lab05-security-compliance.md)** - セキュリティ監視
2. **高度な自動化**: Step Functions による複雑なワークフロー
3. **機械学習活用**: 異常検知の精度向上
4. **クロスアカウント**: マルチアカウント環境での自動復旧

---

**素晴らしい！** 本格的な自動復旧システムを構築できました。この仕組みは本番環境での安定運用に大きく貢献します。