# Lab 3: 包括的監視システム構築

## 🎯 学習目標

このラボでは、AWS DevOpsにおける包括的な監視・ロギングシステムを構築し、以下のスキルを習得します：

- CloudWatch メトリクス・アラーム・ダッシュボードの設定
- X-Ray による分散トレーシングの実装
- AWS Config による構成変更追跡
- カスタムメトリクスとログ分析の実装
- 運用監視のベストプラクティス

## 📋 前提条件

- AWS CLI が設定済み
- 適切なIAM権限（CloudWatch、X-Ray、Config、Lambda、EC2）
- 基本的なAWSサービスの理解
- [Lab 1](./lab01-enterprise-cicd-pipeline.md) の完了推奨

## 🏗️ アーキテクチャ概要

```
┌─────────────────────────────────────────────────────────────┐
│                    監視システム全体図                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐     │
│  │   EC2/ECS   │    │   Lambda    │    │     RDS     │     │
│  │ Application │    │  Functions  │    │  Database   │     │
│  └─────┬───────┘    └─────┬───────┘    └─────┬───────┘     │
│        │                  │                  │             │
│        ▼                  ▼                  ▼             │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐     │
│  │ CloudWatch  │    │   X-Ray     │    │   Config    │     │
│  │   Logs      │    │   Traces    │    │   Rules     │     │
│  └─────┬───────┘    └─────┬───────┘    └─────┬───────┘     │
│        │                  │                  │             │
│        ▼                  ▼                  ▼             │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │              CloudWatch Dashboard                       │ │
│  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐      │ │
│  │  │  Metrics    │ │   Alarms    │ │    Logs     │      │ │
│  │  │ Monitoring  │ │ & Alerts    │ │  Analysis   │      │ │
│  │  └─────────────┘ └─────────────┘ └─────────────┘      │ │
│  └─────────────────────────────────────────────────────────┘ │
│                            │                                 │
│                            ▼                                 │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │                SNS Notifications                        │ │
│  │            Email / Slack / PagerDuty                    │ │
│  └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

## 🚀 Step 1: 基盤環境構築

### 1.1 CloudFormation テンプレート作成

まず、監視対象となるリソースを作成します。

```yaml
# monitoring-infrastructure.yaml
AWSTemplateFormatVersion: '2010-09-09'
Description: 'Comprehensive Monitoring Lab Infrastructure'

Parameters:
  Environment:
    Type: String
    Default: 'lab'
    Description: 'Environment name'
  
  KeyPairName:
    Type: AWS::EC2::KeyPair::KeyName
    Description: 'EC2 Key Pair for instances'

Resources:
  # VPC
  VPC:
    Type: AWS::EC2::VPC
    Properties:
      CidrBlock: 10.0.0.0/16
      EnableDnsHostnames: true
      EnableDnsSupport: true
      Tags:
        - Key: Name
          Value: !Sub '${Environment}-monitoring-vpc'

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

  # Public Subnet
  PublicSubnet:
    Type: AWS::EC2::Subnet
    Properties:
      VpcId: !Ref VPC
      AvailabilityZone: !Select [0, !GetAZs '']
      CidrBlock: 10.0.1.0/24
      MapPublicIpOnLaunch: true
      Tags:
        - Key: Name
          Value: !Sub '${Environment}-public-subnet'

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

  PublicSubnetRouteTableAssociation:
    Type: AWS::EC2::SubnetRouteTableAssociation
    Properties:
      RouteTableId: !Ref PublicRouteTable
      SubnetId: !Ref PublicSubnet

  # Security Group
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
          FromPort: 22
          ToPort: 22
          CidrIp: 0.0.0.0/0
      Tags:
        - Key: Name
          Value: !Sub '${Environment}-web-sg'

  # IAM Role for EC2
  EC2Role:
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
        - arn:aws:iam::aws:policy/CloudWatchAgentServerPolicy
        - arn:aws:iam::aws:policy/AWSXRayDaemonWriteAccess
      Policies:
        - PolicyName: CustomMetricsPolicy
          PolicyDocument:
            Version: '2012-10-17'
            Statement:
              - Effect: Allow
                Action:
                  - cloudwatch:PutMetricData
                  - logs:CreateLogGroup
                  - logs:CreateLogStream
                  - logs:PutLogEvents
                Resource: '*'

  EC2InstanceProfile:
    Type: AWS::IAM::InstanceProfile
    Properties:
      Roles:
        - !Ref EC2Role

  # Web Server Instance
  WebServer:
    Type: AWS::EC2::Instance
    Properties:
      ImageId: ami-0c02fb55956c7d316  # Amazon Linux 2
      InstanceType: t3.micro
      KeyName: !Ref KeyPairName
      SubnetId: !Ref PublicSubnet
      SecurityGroupIds:
        - !Ref WebServerSecurityGroup
      IamInstanceProfile: !Ref EC2InstanceProfile
      UserData:
        Fn::Base64: !Sub |
          #!/bin/bash
          yum update -y
          yum install -y amazon-cloudwatch-agent
          yum install -y httpd
          systemctl start httpd
          systemctl enable httpd
          
          # Create a simple web application
          cat > /var/www/html/index.html << 'EOF'
          <!DOCTYPE html>
          <html>
          <head>
              <title>Monitoring Lab Application</title>
          </head>
          <body>
              <h1>Welcome to Monitoring Lab</h1>
              <p>Current time: <span id="time"></span></p>
              <p>Request count: <span id="count">0</span></p>
              <script>
                  setInterval(() => {
                      document.getElementById('time').textContent = new Date().toLocaleString();
                      let count = parseInt(document.getElementById('count').textContent);
                      document.getElementById('count').textContent = count + 1;
                  }, 1000);
              </script>
          </body>
          </html>
          EOF
          
          # Install X-Ray daemon
          curl https://s3.dualstack.us-east-2.amazonaws.com/aws-xray-assets.us-east-2/xray-daemon/aws-xray-daemon-3.x.rpm -o /tmp/xray.rpm
          yum install -y /tmp/xray.rpm
          systemctl start xray
          systemctl enable xray
      Tags:
        - Key: Name
          Value: !Sub '${Environment}-web-server'
        - Key: Environment
          Value: !Ref Environment

Outputs:
  VPCId:
    Description: 'VPC ID'
    Value: !Ref VPC
    Export:
      Name: !Sub '${AWS::StackName}-VPC-ID'
  
  WebServerInstanceId:
    Description: 'Web Server Instance ID'
    Value: !Ref WebServer
    Export:
      Name: !Sub '${AWS::StackName}-WebServer-ID'
  
  WebServerPublicIP:
    Description: 'Web Server Public IP'
    Value: !GetAtt WebServer.PublicIp
    Export:
      Name: !Sub '${AWS::StackName}-WebServer-IP'
```

### 1.2 インフラストラクチャデプロイ

```bash
# CloudFormation スタック作成
aws cloudformation create-stack \
  --stack-name monitoring-lab-infrastructure \
  --template-body file://monitoring-infrastructure.yaml \
  --parameters ParameterKey=KeyPairName,ParameterValue=your-key-pair \
  --capabilities CAPABILITY_IAM

# デプロイ完了待機
aws cloudformation wait stack-create-complete \
  --stack-name monitoring-lab-infrastructure

# 出力値確認
aws cloudformation describe-stacks \
  --stack-name monitoring-lab-infrastructure \
  --query 'Stacks[0].Outputs'
```

## 🔍 Step 2: CloudWatch 詳細監視設定

### 2.1 CloudWatch Agent設定

EC2インスタンスに詳細監視を設定します。

```bash
# EC2インスタンスにSSH接続
INSTANCE_IP=$(aws cloudformation describe-stacks \
  --stack-name monitoring-lab-infrastructure \
  --query 'Stacks[0].Outputs[?OutputKey==`WebServerPublicIP`].OutputValue' \
  --output text)

ssh -i your-key.pem ec2-user@$INSTANCE_IP
```

CloudWatch Agent設定ファイルを作成：

```json
# /opt/aws/amazon-cloudwatch-agent/etc/amazon-cloudwatch-agent.json
{
  "agent": {
    "metrics_collection_interval": 60,
    "run_as_user": "root"
  },
  "metrics": {
    "namespace": "MonitoringLab/EC2",
    "metrics_collected": {
      "cpu": {
        "measurement": [
          "cpu_usage_idle",
          "cpu_usage_iowait",
          "cpu_usage_user",
          "cpu_usage_system"
        ],
        "metrics_collection_interval": 60,
        "totalcpu": false
      },
      "disk": {
        "measurement": [
          "used_percent"
        ],
        "metrics_collection_interval": 60,
        "resources": [
          "*"
        ]
      },
      "diskio": {
        "measurement": [
          "io_time",
          "read_bytes",
          "write_bytes",
          "reads",
          "writes"
        ],
        "metrics_collection_interval": 60,
        "resources": [
          "*"
        ]
      },
      "mem": {
        "measurement": [
          "mem_used_percent"
        ],
        "metrics_collection_interval": 60
      },
      "netstat": {
        "measurement": [
          "tcp_established",
          "tcp_time_wait"
        ],
        "metrics_collection_interval": 60
      },
      "swap": {
        "measurement": [
          "swap_used_percent"
        ],
        "metrics_collection_interval": 60
      }
    }
  },
  "logs": {
    "logs_collected": {
      "files": {
        "collect_list": [
          {
            "file_path": "/var/log/httpd/access_log",
            "log_group_name": "/aws/ec2/httpd/access_log",
            "log_stream_name": "{instance_id}",
            "timezone": "UTC"
          },
          {
            "file_path": "/var/log/httpd/error_log",
            "log_group_name": "/aws/ec2/httpd/error_log",
            "log_stream_name": "{instance_id}",
            "timezone": "UTC"
          }
        ]
      }
    }
  }
}
```

CloudWatch Agent開始：

```bash
sudo /opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent-ctl \
  -a fetch-config \
  -m ec2 \
  -c file:/opt/aws/amazon-cloudwatch-agent/etc/amazon-cloudwatch-agent.json \
  -s

# ステータス確認
sudo /opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent-ctl \
  -m ec2 \
  -c file:/opt/aws/amazon-cloudwatch-agent/etc/amazon-cloudwatch-agent.json \
  -a query
```

### 2.2 カスタムメトリクス送信

アプリケーションレベルのメトリクスを送信するスクリプトを作成：

```bash
# /home/ec2-user/send-custom-metrics.py
#!/usr/bin/env python3
import boto3
import time
import random
import psutil
from datetime import datetime

cloudwatch = boto3.client('cloudwatch')

def send_custom_metrics():
    """カスタムメトリクスをCloudWatchに送信"""
    
    # アプリケーション固有のメトリクス
    response_time = random.uniform(50, 500)  # レスポンス時間シミュレーション
    error_rate = random.uniform(0, 5)        # エラー率シミュレーション
    active_users = random.randint(10, 100)   # アクティブユーザー数
    
    # システムメトリクス
    cpu_percent = psutil.cpu_percent()
    memory_percent = psutil.virtual_memory().percent
    disk_percent = psutil.disk_usage('/').percent
    
    metrics_data = [
        {
            'MetricName': 'ResponseTime',
            'Dimensions': [
                {
                    'Name': 'Environment',
                    'Value': 'lab'
                }
            ],
            'Value': response_time,
            'Unit': 'Milliseconds',
            'Timestamp': datetime.utcnow()
        },
        {
            'MetricName': 'ErrorRate',
            'Dimensions': [
                {
                    'Name': 'Environment',
                    'Value': 'lab'
                }
            ],
            'Value': error_rate,
            'Unit': 'Percent',
            'Timestamp': datetime.utcnow()
        },
        {
            'MetricName': 'ActiveUsers',
            'Dimensions': [
                {
                    'Name': 'Environment',
                    'Value': 'lab'
                }
            ],
            'Value': active_users,
            'Unit': 'Count',
            'Timestamp': datetime.utcnow()
        }
    ]
    
    try:
        response = cloudwatch.put_metric_data(
            Namespace='MonitoringLab/Application',
            MetricData=metrics_data
        )
        print(f"Metrics sent successfully: {datetime.now()}")
        print(f"Response Time: {response_time:.2f}ms, Error Rate: {error_rate:.2f}%, Active Users: {active_users}")
    except Exception as e:
        print(f"Error sending metrics: {e}")

if __name__ == "__main__":
    # 継続的にメトリクスを送信
    while True:
        send_custom_metrics()
        time.sleep(60)  # 1分間隔
```

```bash
# 必要なライブラリをインストール
sudo pip3 install psutil boto3

# バックグラウンドで実行
nohup python3 /home/ec2-user/send-custom-metrics.py > /tmp/metrics.log 2>&1 &
```

## 📊 Step 3: CloudWatch ダッシュボード作成

### 3.1 包括的ダッシュボード構築

```python
# create-dashboard.py
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
                    ["AWS/EC2", "CPUUtilization", "InstanceId", "INSTANCE_ID"],
                    ["MonitoringLab/EC2", "cpu_usage_user", "InstanceId", "INSTANCE_ID"],
                    [".", "cpu_usage_system", ".", "."],
                    [".", "mem_used_percent", ".", "."]
                ],
                "view": "timeSeries",
                "stacked": False,
                "region": "us-east-1",
                "title": "System Performance",
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
                    ["MonitoringLab/Application", "ResponseTime", "Environment", "lab"],
                    [".", "ErrorRate", ".", "."],
                    [".", "ActiveUsers", ".", "."]
                ],
                "view": "timeSeries",
                "stacked": False,
                "region": "us-east-1",
                "title": "Application Metrics",
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
                "query": "SOURCE '/aws/ec2/httpd/access_log' | fields @timestamp, @message\\n| filter @message like /GET/\\n| stats count() by bin(5m)",
                "region": "us-east-1",
                "title": "HTTP Access Patterns",
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
                    ["MonitoringLab/EC2", "disk_used_percent", "device", "/dev/xvda1", "fstype", "xfs", "path", "/"],
                    [".", "diskio_read_bytes", "name", "xvda", ".", ".", ".", "."],
                    [".", "diskio_write_bytes", ".", ".", ".", ".", ".", "."]
                ],
                "view": "timeSeries",
                "stacked": False,
                "region": "us-east-1",
                "title": "Disk Performance",
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
                    ["MonitoringLab/EC2", "netstat_tcp_established"],
                    [".", "netstat_tcp_time_wait"]
                ],
                "view": "timeSeries",
                "stacked": False,
                "region": "us-east-1",
                "title": "Network Connections",
                "period": 300
            }
        }
    ]
}

# インスタンスIDを実際の値に置換
import subprocess
instance_id = subprocess.check_output([
    'aws', 'cloudformation', 'describe-stacks',
    '--stack-name', 'monitoring-lab-infrastructure',
    '--query', 'Stacks[0].Outputs[?OutputKey==`WebServerInstanceId`].OutputValue',
    '--output', 'text'
]).decode().strip()

dashboard_json = json.dumps(dashboard_body).replace('INSTANCE_ID', instance_id)

# ダッシュボード作成
response = cloudwatch.put_dashboard(
    DashboardName='MonitoringLabDashboard',
    DashboardBody=dashboard_json
)

print(f"Dashboard created successfully: {response}")
```

```bash
python3 create-dashboard.py
```

## 🚨 Step 4: CloudWatch アラーム設定

### 4.1 重要アラームの設定

```python
# create-alarms.py
import boto3

cloudwatch = boto3.client('cloudwatch')
sns = boto3.client('sns')

# SNS トピック作成
topic_response = sns.create_topic(Name='monitoring-lab-alerts')
topic_arn = topic_response['TopicArn']

# メール通知設定
sns.subscribe(
    TopicArn=topic_arn,
    Protocol='email',
    Endpoint='your-email@example.com'  # 実際のメールアドレスに変更
)

print(f"SNS Topic created: {topic_arn}")
print("Please confirm email subscription")

# インスタンスID取得
import subprocess
instance_id = subprocess.check_output([
    'aws', 'cloudformation', 'describe-stacks',
    '--stack-name', 'monitoring-lab-infrastructure',
    '--query', 'Stacks[0].Outputs[?OutputKey==`WebServerInstanceId`].OutputValue',
    '--output', 'text'
]).decode().strip()

# アラーム設定リスト
alarms = [
    {
        'AlarmName': 'HighCPUUtilization',
        'ComparisonOperator': 'GreaterThanThreshold',
        'EvaluationPeriods': 2,
        'MetricName': 'CPUUtilization',
        'Namespace': 'AWS/EC2',
        'Period': 300,
        'Statistic': 'Average',
        'Threshold': 80.0,
        'ActionsEnabled': True,
        'AlarmActions': [topic_arn],
        'AlarmDescription': 'Alert when CPU exceeds 80%',
        'Dimensions': [
            {
                'Name': 'InstanceId',
                'Value': instance_id
            }
        ],
        'Unit': 'Percent'
    },
    {
        'AlarmName': 'HighMemoryUtilization',
        'ComparisonOperator': 'GreaterThanThreshold',
        'EvaluationPeriods': 2,
        'MetricName': 'mem_used_percent',
        'Namespace': 'MonitoringLab/EC2',
        'Period': 300,
        'Statistic': 'Average',
        'Threshold': 90.0,
        'ActionsEnabled': True,
        'AlarmActions': [topic_arn],
        'AlarmDescription': 'Alert when Memory exceeds 90%',
        'Dimensions': [
            {
                'Name': 'InstanceId',
                'Value': instance_id
            }
        ],
        'Unit': 'Percent'
    },
    {
        'AlarmName': 'HighResponseTime',
        'ComparisonOperator': 'GreaterThanThreshold',
        'EvaluationPeriods': 3,
        'MetricName': 'ResponseTime',
        'Namespace': 'MonitoringLab/Application',
        'Period': 300,
        'Statistic': 'Average',
        'Threshold': 400.0,
        'ActionsEnabled': True,
        'AlarmActions': [topic_arn],
        'AlarmDescription': 'Alert when Response Time exceeds 400ms',
        'Dimensions': [
            {
                'Name': 'Environment',
                'Value': 'lab'
            }
        ],
        'Unit': 'Milliseconds'
    },
    {
        'AlarmName': 'HighErrorRate',
        'ComparisonOperator': 'GreaterThanThreshold',
        'EvaluationPeriods': 2,
        'MetricName': 'ErrorRate',
        'Namespace': 'MonitoringLab/Application',
        'Period': 300,
        'Statistic': 'Average',
        'Threshold': 3.0,
        'ActionsEnabled': True,
        'AlarmActions': [topic_arn],
        'AlarmDescription': 'Alert when Error Rate exceeds 3%',
        'Dimensions': [
            {
                'Name': 'Environment',
                'Value': 'lab'
            }
        ],
        'Unit': 'Percent'
    }
]

# アラーム作成
for alarm in alarms:
    response = cloudwatch.put_metric_alarm(**alarm)
    print(f"Alarm created: {alarm['AlarmName']}")

print("All alarms created successfully!")
```

```bash
python3 create-alarms.py
```

## 🔄 Step 5: X-Ray 分散トレーシング

### 5.1 X-Ray対応アプリケーション作成

```python
# /var/www/html/app.py
from flask import Flask, request, jsonify
import time
import random
import requests
from aws_xray_sdk.core import xray_recorder
from aws_xray_sdk.core import patch_all
from aws_xray_sdk.ext.flask.middleware import XRayMiddleware

# AWS X-Ray SDKでライブラリをパッチ
patch_all()

app = Flask(__name__)

# X-Ray設定
xray_recorder.configure(
    context_missing='LOG_ERROR',
    plugins=('EC2Plugin',),
    daemon_address='127.0.0.1:2000'
)

XRayMiddleware(app, xray_recorder)

@app.route('/api/users/<user_id>')
@xray_recorder.capture('get_user')
def get_user(user_id):
    """ユーザー情報取得API（X-Rayトレーシング付き）"""
    
    # データベース呼び出しシミュレーション
    subsegment = xray_recorder.begin_subsegment('database_query')
    try:
        subsegment.put_annotation('user_id', user_id)
        subsegment.put_metadata('query', f'SELECT * FROM users WHERE id = {user_id}')
        
        # クエリ実行時間シミュレーション
        query_time = random.uniform(0.1, 0.5)
        time.sleep(query_time)
        
        user_data = {
            'id': user_id,
            'name': f'User {user_id}',
            'email': f'user{user_id}@example.com',
            'status': 'active'
        }
        
        subsegment.put_metadata('result', user_data)
        
    except Exception as e:
        subsegment.add_exception(e)
        raise
    finally:
        xray_recorder.end_subsegment()
    
    return jsonify(user_data)

@app.route('/api/orders/<user_id>')
@xray_recorder.capture('get_user_orders')
def get_user_orders(user_id):
    """ユーザー注文履歴取得API"""
    
    # 外部API呼び出しシミュレーション
    subsegment = xray_recorder.begin_subsegment('external_api_call')
    try:
        subsegment.put_annotation('user_id', user_id)
        subsegment.put_annotation('api_type', 'orders')
        
        # 外部API呼び出し時間シミュレーション
        api_call_time = random.uniform(0.2, 1.0)
        time.sleep(api_call_time)
        
        # ランダムにエラーを発生させる
        if random.random() < 0.1:  # 10%の確率でエラー
            raise Exception("External API timeout")
        
        orders = [
            {
                'id': f'order_{i}',
                'user_id': user_id,
                'amount': random.randint(100, 1000),
                'status': random.choice(['pending', 'completed', 'cancelled'])
            }
            for i in range(random.randint(1, 5))
        ]
        
        subsegment.put_metadata('orders_count', len(orders))
        
    except Exception as e:
        subsegment.add_exception(e)
        return jsonify({'error': 'Failed to fetch orders'}), 500
    finally:
        xray_recorder.end_subsegment()
    
    return jsonify(orders)

@app.route('/health')
def health_check():
    """ヘルスチェックエンドポイント"""
    return jsonify({'status': 'healthy', 'timestamp': time.time()})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
```

### 5.2 Flask アプリケーション起動

```bash
# 必要なライブラリインストール
sudo pip3 install flask aws-xray-sdk

# アプリケーション起動
sudo python3 /var/www/html/app.py &

# 負荷生成スクリプト作成
cat > /home/ec2-user/generate_load.py << 'EOF'
#!/usr/bin/env python3
import requests
import time
import random
import threading

def generate_requests():
    """継続的にAPIリクエストを生成"""
    base_url = 'http://localhost:5000'
    
    while True:
        try:
            user_id = random.randint(1, 100)
            
            # ユーザー情報取得
            response = requests.get(f'{base_url}/api/users/{user_id}')
            print(f"User API: {response.status_code}")
            
            # 注文履歴取得
            response = requests.get(f'{base_url}/api/orders/{user_id}')
            print(f"Orders API: {response.status_code}")
            
            time.sleep(random.uniform(1, 3))
            
        except Exception as e:
            print(f"Request error: {e}")
            time.sleep(5)

# 複数スレッドで負荷生成
for i in range(3):
    thread = threading.Thread(target=generate_requests)
    thread.daemon = True
    thread.start()

# メインスレッドを維持
while True:
    time.sleep(60)
EOF

# 負荷生成開始
nohup python3 /home/ec2-user/generate_load.py > /tmp/load.log 2>&1 &
```

## 📋 Step 6: AWS Config 設定

### 6.1 Config Rules 設定

```python
# setup-config.py
import boto3

config = boto3.client('config')
iam = boto3.client('iam')

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
        RoleName='ConfigServiceRole',
        AssumeRolePolicyDocument=json.dumps(trust_policy),
        Description='Service role for AWS Config'
    )
    
    # 必要なポリシーをアタッチ
    iam.attach_role_policy(
        RoleName='ConfigServiceRole',
        PolicyArn='arn:aws:iam::aws:policy/service-role/ConfigRole'
    )
    
    iam.attach_role_policy(
        RoleName='ConfigServiceRole',
        PolicyArn='arn:aws:iam::aws:policy/service-role/AWS_ConfigServiceRolePolicy'
    )
    
    role_arn = role_response['Role']['Arn']
    
except iam.exceptions.EntityAlreadyExistsException:
    role_arn = iam.get_role(RoleName='ConfigServiceRole')['Role']['Arn']

# S3バケット作成（Config記録用）
s3 = boto3.client('s3')
bucket_name = f'config-bucket-{int(time.time())}'

s3.create_bucket(
    Bucket=bucket_name,
    CreateBucketConfiguration={'LocationConstraint': 'us-west-2'}  # リージョンに応じて変更
)

# Configuration Recorder設定
config.put_configuration_recorder(
    ConfigurationRecorder={
        'name': 'default',
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
        'name': 'default',
        's3BucketName': bucket_name,
        'configSnapshotDeliveryProperties': {
            'deliveryFrequency': 'TwentyFour_Hours'
        }
    }
)

# Configuration Recorder開始
config.start_configuration_recorder(
    ConfigurationRecorderName='default'
)

print(f"AWS Config setup completed. S3 bucket: {bucket_name}")

# Config Rules設定
rules = [
    {
        'ConfigRuleName': 'root-access-key-check',
        'Source': {
            'Owner': 'AWS',
            'SourceIdentifier': 'ROOT_ACCESS_KEY_CHECK'
        }
    },
    {
        'ConfigRuleName': 'encrypted-volumes',
        'Source': {
            'Owner': 'AWS',
            'SourceIdentifier': 'ENCRYPTED_VOLUMES'
        }
    },
    {
        'ConfigRuleName': 'security-group-ssh-check',
        'Source': {
            'Owner': 'AWS',
            'SourceIdentifier': 'INCOMING_SSH_DISABLED'
        }
    }
]

for rule in rules:
    config.put_config_rule(ConfigRule=rule)
    print(f"Config rule created: {rule['ConfigRuleName']}")
```

```bash
python3 setup-config.py
```

## 📊 Step 7: ログ分析とインサイト

### 7.1 CloudWatch Insights クエリ

```python
# log-analysis.py
import boto3
import time
from datetime import datetime, timedelta

logs = boto3.client('logs')

# 分析クエリリスト
queries = [
    {
        'name': 'Top Error Messages',
        'query': '''
        fields @timestamp, @message
        | filter @message like /ERROR/
        | stats count() by @message
        | sort count desc
        | limit 10
        ''',
        'log_groups': ['/aws/ec2/httpd/error_log']
    },
    {
        'name': 'Request Rate by Hour',
        'query': '''
        fields @timestamp, @message
        | filter @message like /GET/
        | stats count() by bin(1h)
        | sort @timestamp desc
        ''',
        'log_groups': ['/aws/ec2/httpd/access_log']
    },
    {
        'name': 'Response Status Codes',
        'query': '''
        fields @timestamp, @message
        | parse @message /(?<ip>\S+) \S+ \S+ \[(?<time>[^\]]+)\] "(?<method>\S+) (?<path>\S+) \S+" (?<status>\d+) (?<size>\S+)/
        | stats count() by status
        | sort count desc
        ''',
        'log_groups': ['/aws/ec2/httpd/access_log']
    }
]

# 時間範囲設定（過去1時間）
end_time = int(time.time())
start_time = end_time - 3600

for query_info in queries:
    print(f"\n=== {query_info['name']} ===")
    
    try:
        response = logs.start_query(
            logGroupNames=query_info['log_groups'],
            startTime=start_time,
            endTime=end_time,
            queryString=query_info['query']
        )
        
        query_id = response['queryId']
        
        # クエリ完了待機
        while True:
            result = logs.get_query_results(queryId=query_id)
            if result['status'] == 'Complete':
                break
            time.sleep(1)
        
        # 結果表示
        for record in result['results']:
            row_data = {field['field']: field['value'] for field in record}
            print(row_data)
            
    except Exception as e:
        print(f"Query failed: {e}")
```

```bash
python3 log-analysis.py
```

## 🧪 Step 8: 監視システムのテスト

### 8.1 負荷テストと障害シミュレーション

```bash
# CPU負荷生成
stress --cpu 2 --timeout 300s &

# メモリ負荷生成  
stress --vm 1 --vm-bytes 1G --timeout 300s &

# ディスク負荷生成
dd if=/dev/zero of=/tmp/testfile bs=1M count=1000

# ネットワーク負荷生成
curl -s "http://localhost:5000/api/users/1" &
```

### 8.2 アラーム動作確認

```python
# test-alarms.py
import boto3
import time

cloudwatch = boto3.client('cloudwatch')

def trigger_alarm_test():
    """アラームテスト用のメトリクスを送信"""
    
    # 高CPU使用率をシミュレート
    cloudwatch.put_metric_data(
        Namespace='MonitoringLab/Test',
        MetricData=[
            {
                'MetricName': 'CPUUtilization',
                'Value': 95.0,
                'Unit': 'Percent',
                'Dimensions': [
                    {
                        'Name': 'Environment',
                        'Value': 'lab'
                    }
                ]
            }
        ]
    )
    
    # 高レスポンス時間をシミュレート
    cloudwatch.put_metric_data(
        Namespace='MonitoringLab/Application',
        MetricData=[
            {
                'MetricName': 'ResponseTime',
                'Value': 450.0,
                'Unit': 'Milliseconds',
                'Dimensions': [
                    {
                        'Name': 'Environment',
                        'Value': 'lab'
                    }
                ]
            }
        ]
    )
    
    print("Test metrics sent. Check alarms in 5-10 minutes.")

trigger_alarm_test()
```

## 📈 Step 9: 運用ベストプラクティス

### 9.1 自動化されたレポート生成

```python
# generate-report.py
import boto3
import json
from datetime import datetime, timedelta

def generate_monitoring_report():
    """日次監視レポート生成"""
    
    cloudwatch = boto3.client('cloudwatch')
    
    # 過去24時間の期間
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(hours=24)
    
    report = {
        'timestamp': end_time.isoformat(),
        'period': '24 hours',
        'metrics': {}
    }
    
    # 主要メトリクスの統計取得
    metrics_to_check = [
        ('AWS/EC2', 'CPUUtilization'),
        ('MonitoringLab/Application', 'ResponseTime'),
        ('MonitoringLab/Application', 'ErrorRate'),
        ('MonitoringLab/Application', 'ActiveUsers')
    ]
    
    for namespace, metric_name in metrics_to_check:
        try:
            response = cloudwatch.get_metric_statistics(
                Namespace=namespace,
                MetricName=metric_name,
                StartTime=start_time,
                EndTime=end_time,
                Period=3600,  # 1時間間隔
                Statistics=['Average', 'Maximum', 'Minimum']
            )
            
            if response['Datapoints']:
                datapoints = sorted(response['Datapoints'], key=lambda x: x['Timestamp'])
                
                report['metrics'][metric_name] = {
                    'average': sum(dp['Average'] for dp in datapoints) / len(datapoints),
                    'maximum': max(dp['Maximum'] for dp in datapoints),
                    'minimum': min(dp['Minimum'] for dp in datapoints),
                    'datapoints_count': len(datapoints)
                }
        
        except Exception as e:
            report['metrics'][metric_name] = {'error': str(e)}
    
    # アラーム状態確認
    alarms_response = cloudwatch.describe_alarms()
    alarm_summary = {}
    
    for alarm in alarms_response['MetricAlarms']:
        alarm_summary[alarm['AlarmName']] = {
            'state': alarm['StateValue'],
            'reason': alarm['StateReason']
        }
    
    report['alarms'] = alarm_summary
    
    # レポート保存
    report_filename = f"monitoring-report-{end_time.strftime('%Y%m%d-%H%M%S')}.json"
    with open(report_filename, 'w') as f:
        json.dump(report, f, indent=2, default=str)
    
    print(f"Report generated: {report_filename}")
    print(json.dumps(report, indent=2, default=str))
    
    return report

generate_monitoring_report()
```

## 🔧 Step 10: クリーンアップ

### 10.1 リソース削除

```bash
# アプリケーション停止
sudo pkill -f "python3.*app.py"
sudo pkill -f "python3.*generate_load.py"
sudo pkill -f "python3.*send-custom-metrics.py"

# CloudWatch リソース削除
aws cloudwatch delete-dashboard --dashboard-name MonitoringLabDashboard

# アラーム削除
aws cloudwatch delete-alarms --alarm-names \
  HighCPUUtilization \
  HighMemoryUtilization \
  HighResponseTime \
  HighErrorRate

# Config設定削除
aws configservice stop-configuration-recorder --configuration-recorder-name default
aws configservice delete-configuration-recorder --configuration-recorder-name default
aws configservice delete-delivery-channel --delivery-channel-name default

# CloudFormation スタック削除
aws cloudformation delete-stack --stack-name monitoring-lab-infrastructure

# Config用S3バケット削除（手動で確認して削除）
aws s3 ls | grep config-bucket
```

## 📚 学習のまとめ

このラボで学習した内容：

### 技術的スキル
- ✅ CloudWatch Agent の詳細設定
- ✅ カスタムメトリクスの実装
- ✅ X-Ray分散トレーシングの設定
- ✅ CloudWatch Insights による ログ分析
- ✅ 包括的なダッシュボード構築
- ✅ プロアクティブなアラーム設定

### 運用ベストプラクティス
- ✅ 多層監視アーキテクチャ
- ✅ 自動化されたアラート
- ✅ データドリブンな運用判断
- ✅ 継続的な監視改善

### ビジネス価値
- ✅ システムの可視性向上
- ✅ 障害の早期検知
- ✅ パフォーマンス最適化
- ✅ 運用コスト削減

## 🎯 次のステップ

1. **[Lab 4: インシデント対応](./lab04-incident-response.md)** - 自動復旧システム
2. **[Lab 5: セキュリティ自動化](./lab05-security-compliance.md)** - セキュリティ監視
3. **高度な監視**: Prometheus, Grafana との統合
4. **機械学習監視**: CloudWatch Anomaly Detection

---

**素晴らしい！** 包括的な監視システムを構築できました。この知識は本番環境での安定運用に直結します。