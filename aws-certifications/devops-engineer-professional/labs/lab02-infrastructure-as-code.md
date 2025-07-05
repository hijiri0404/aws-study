# Lab 2: Infrastructure as Code - CloudFormation & CDK 実践

## 🎯 学習目標

このラボでは、企業レベルのInfrastructure as Code (IaC)実装を学習します。CloudFormationとAWS CDKの両方を使用して、本格的なマルチ環境インフラを構築します。

**習得スキル**:
- CloudFormationテンプレートの高度な活用
- AWS CDKによるプログラマティックなインフラ定義
- 環境間でのインフラ管理
- IaCのベストプラクティス実装

**所要時間**: 8-12時間  
**推定コスト**: $25-40

## 📋 シナリオ

**企業**: SaaS企業（顧客管理システム）  
**要件**:
- 開発・ステージング・本番の3環境
- 高可用性とスケーラビリティ
- セキュリティベストプラクティス
- インフラの完全なコード化

## Phase 1: CloudFormation による基盤構築

### 1.1 ネットワーク基盤テンプレート

```bash
#!/bin/bash
# スクリプト: deploy-network-infrastructure.sh

set -e

echo "=== CloudFormation ネットワーク基盤構築開始 ==="

# 変数定義
REGION="ap-northeast-1"
ENVIRONMENT=${1:-"dev"}  # dev, staging, prod
STACK_NAME="saas-network-$ENVIRONMENT"

# CloudFormationテンプレート作成
cat > network-infrastructure.yaml << 'EOF'
AWSTemplateFormatVersion: '2010-09-09'
Description: 'SaaS Application Network Infrastructure'

Parameters:
  Environment:
    Type: String
    Default: dev
    AllowedValues: [dev, staging, prod]
    Description: Deployment environment
  
  VpcCidr:
    Type: String
    Default: 10.0.0.0/16
    Description: CIDR block for VPC

Mappings:
  EnvironmentMap:
    dev:
      VpcCidr: "10.0.0.0/16"
      InstanceType: "t3.micro"
      MinSize: 1
      MaxSize: 3
    staging:
      VpcCidr: "10.1.0.0/16"
      InstanceType: "t3.small"
      MinSize: 2
      MaxSize: 5
    prod:
      VpcCidr: "10.2.0.0/16"
      InstanceType: "t3.medium"
      MinSize: 3
      MaxSize: 10

Resources:
  # VPC
  VPC:
    Type: AWS::EC2::VPC
    Properties:
      CidrBlock: !FindInMap [EnvironmentMap, !Ref Environment, VpcCidr]
      EnableDnsHostnames: true
      EnableDnsSupport: true
      Tags:
        - Key: Name
          Value: !Sub '${Environment}-saas-vpc'
        - Key: Environment
          Value: !Ref Environment

  # Internet Gateway
  InternetGateway:
    Type: AWS::EC2::InternetGateway
    Properties:
      Tags:
        - Key: Name
          Value: !Sub '${Environment}-saas-igw'

  InternetGatewayAttachment:
    Type: AWS::EC2::VPCGatewayAttachment
    Properties:
      InternetGatewayId: !Ref InternetGateway
      VpcId: !Ref VPC

  # Public Subnets
  PublicSubnet1:
    Type: AWS::EC2::Subnet
    Properties:
      VpcId: !Ref VPC
      AvailabilityZone: !Select [0, !GetAZs '']
      CidrBlock: !Select [0, !Cidr [!FindInMap [EnvironmentMap, !Ref Environment, VpcCidr], 6, 8]]
      MapPublicIpOnLaunch: true
      Tags:
        - Key: Name
          Value: !Sub '${Environment}-public-subnet-1'

  PublicSubnet2:
    Type: AWS::EC2::Subnet
    Properties:
      VpcId: !Ref VPC
      AvailabilityZone: !Select [1, !GetAZs '']
      CidrBlock: !Select [1, !Cidr [!FindInMap [EnvironmentMap, !Ref Environment, VpcCidr], 6, 8]]
      MapPublicIpOnLaunch: true
      Tags:
        - Key: Name
          Value: !Sub '${Environment}-public-subnet-2'

  # Private Subnets
  PrivateSubnet1:
    Type: AWS::EC2::Subnet
    Properties:
      VpcId: !Ref VPC
      AvailabilityZone: !Select [0, !GetAZs '']
      CidrBlock: !Select [2, !Cidr [!FindInMap [EnvironmentMap, !Ref Environment, VpcCidr], 6, 8]]
      Tags:
        - Key: Name
          Value: !Sub '${Environment}-private-subnet-1'

  PrivateSubnet2:
    Type: AWS::EC2::Subnet
    Properties:
      VpcId: !Ref VPC
      AvailabilityZone: !Select [1, !GetAZs '']
      CidrBlock: !Select [3, !Cidr [!FindInMap [EnvironmentMap, !Ref Environment, VpcCidr], 6, 8]]
      Tags:
        - Key: Name
          Value: !Sub '${Environment}-private-subnet-2'

  # Database Subnets
  DatabaseSubnet1:
    Type: AWS::EC2::Subnet
    Properties:
      VpcId: !Ref VPC
      AvailabilityZone: !Select [0, !GetAZs '']
      CidrBlock: !Select [4, !Cidr [!FindInMap [EnvironmentMap, !Ref Environment, VpcCidr], 6, 8]]
      Tags:
        - Key: Name
          Value: !Sub '${Environment}-db-subnet-1'

  DatabaseSubnet2:
    Type: AWS::EC2::Subnet
    Properties:
      VpcId: !Ref VPC
      AvailabilityZone: !Select [1, !GetAZs '']
      CidrBlock: !Select [5, !Cidr [!FindInMap [EnvironmentMap, !Ref Environment, VpcCidr], 6, 8]]
      Tags:
        - Key: Name
          Value: !Sub '${Environment}-db-subnet-2'

  # NAT Gateway
  NatGateway1EIP:
    Type: AWS::EC2::EIP
    DependsOn: InternetGatewayAttachment
    Properties:
      Domain: vpc
      Tags:
        - Key: Name
          Value: !Sub '${Environment}-nat-eip-1'

  NatGateway2EIP:
    Type: AWS::EC2::EIP
    DependsOn: InternetGatewayAttachment
    Properties:
      Domain: vpc
      Tags:
        - Key: Name
          Value: !Sub '${Environment}-nat-eip-2'

  NatGateway1:
    Type: AWS::EC2::NatGateway
    Properties:
      AllocationId: !GetAtt NatGateway1EIP.AllocationId
      SubnetId: !Ref PublicSubnet1
      Tags:
        - Key: Name
          Value: !Sub '${Environment}-nat-gateway-1'

  NatGateway2:
    Type: AWS::EC2::NatGateway
    Properties:
      AllocationId: !GetAtt NatGateway2EIP.AllocationId
      SubnetId: !Ref PublicSubnet2
      Tags:
        - Key: Name
          Value: !Sub '${Environment}-nat-gateway-2'

  # Route Tables
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

  PrivateRouteTable1:
    Type: AWS::EC2::RouteTable
    Properties:
      VpcId: !Ref VPC
      Tags:
        - Key: Name
          Value: !Sub '${Environment}-private-rt-1'

  DefaultPrivateRoute1:
    Type: AWS::EC2::Route
    Properties:
      RouteTableId: !Ref PrivateRouteTable1
      DestinationCidrBlock: 0.0.0.0/0
      NatGatewayId: !Ref NatGateway1

  PrivateSubnet1RouteTableAssociation:
    Type: AWS::EC2::SubnetRouteTableAssociation
    Properties:
      RouteTableId: !Ref PrivateRouteTable1
      SubnetId: !Ref PrivateSubnet1

  PrivateRouteTable2:
    Type: AWS::EC2::RouteTable
    Properties:
      VpcId: !Ref VPC
      Tags:
        - Key: Name
          Value: !Sub '${Environment}-private-rt-2'

  DefaultPrivateRoute2:
    Type: AWS::EC2::Route
    Properties:
      RouteTableId: !Ref PrivateRouteTable2
      DestinationCidrBlock: 0.0.0.0/0
      NatGatewayId: !Ref NatGateway2

  PrivateSubnet2RouteTableAssociation:
    Type: AWS::EC2::SubnetRouteTableAssociation
    Properties:
      RouteTableId: !Ref PrivateRouteTable2
      SubnetId: !Ref PrivateSubnet2

  # Database Subnet Group
  DatabaseSubnetGroup:
    Type: AWS::RDS::DBSubnetGroup
    Properties:
      DBSubnetGroupDescription: !Sub '${Environment} database subnet group'
      SubnetIds:
        - !Ref DatabaseSubnet1
        - !Ref DatabaseSubnet2
      Tags:
        - Key: Name
          Value: !Sub '${Environment}-db-subnet-group'

Outputs:
  VPC:
    Description: VPC ID
    Value: !Ref VPC
    Export:
      Name: !Sub '${Environment}-vpc-id'

  PublicSubnets:
    Description: Public subnets
    Value: !Join [',', [!Ref PublicSubnet1, !Ref PublicSubnet2]]
    Export:
      Name: !Sub '${Environment}-public-subnets'

  PrivateSubnets:
    Description: Private subnets
    Value: !Join [',', [!Ref PrivateSubnet1, !Ref PrivateSubnet2]]
    Export:
      Name: !Sub '${Environment}-private-subnets'

  DatabaseSubnetGroup:
    Description: Database subnet group
    Value: !Ref DatabaseSubnetGroup
    Export:
      Name: !Sub '${Environment}-db-subnet-group'
EOF

# CloudFormationスタックのデプロイ
echo "1. ネットワークインフラをデプロイ中..."
aws cloudformation create-stack \
    --stack-name $STACK_NAME \
    --template-body file://network-infrastructure.yaml \
    --parameters ParameterKey=Environment,ParameterValue=$ENVIRONMENT \
    --region $REGION \
    --tags Key=Environment,Value=$ENVIRONMENT Key=Project,Value=SaaS-Platform

# デプロイ完了を待機
echo "   デプロイ完了を待機中..."
aws cloudformation wait stack-create-complete \
    --stack-name $STACK_NAME \
    --region $REGION

echo "✅ ネットワーク基盤デプロイ完了: $STACK_NAME"

# スタック出力の表示
aws cloudformation describe-stacks \
    --stack-name $STACK_NAME \
    --region $REGION \
    --query 'Stacks[0].Outputs'
EOF

chmod +x deploy-network-infrastructure.sh
```

### 1.2 アプリケーション基盤テンプレート

```bash
# 続き: deploy-application-infrastructure.sh

cat > application-infrastructure.yaml << 'EOF'
AWSTemplateFormatVersion: '2010-09-09'
Description: 'SaaS Application Infrastructure'

Parameters:
  Environment:
    Type: String
    Default: dev
    AllowedValues: [dev, staging, prod]

  ImageId:
    Type: AWS::SSM::Parameter::Value<AWS::EC2::Image::Id>
    Default: /aws/service/ami-amazon-linux-latest/amzn2-ami-hvm-x86_64-gp2

Mappings:
  EnvironmentMap:
    dev:
      InstanceType: "t3.micro"
      MinSize: 1
      MaxSize: 3
      DatabaseClass: "db.t3.micro"
    staging:
      InstanceType: "t3.small"
      MinSize: 2
      MaxSize: 5
      DatabaseClass: "db.t3.small"
    prod:
      InstanceType: "t3.medium"
      MinSize: 3
      MaxSize: 10
      DatabaseClass: "db.r5.large"

Resources:
  # Application Load Balancer
  ApplicationLoadBalancer:
    Type: AWS::ElasticLoadBalancingV2::LoadBalancer
    Properties:
      Name: !Sub '${Environment}-saas-alb'
      Scheme: internet-facing
      Type: application
      Subnets:
        - !ImportValue !Sub '${Environment}-public-subnets'
      SecurityGroups:
        - !Ref ALBSecurityGroup
      Tags:
        - Key: Name
          Value: !Sub '${Environment}-saas-alb'

  ALBSecurityGroup:
    Type: AWS::EC2::SecurityGroup
    Properties:
      GroupDescription: Security group for Application Load Balancer
      VpcId: !ImportValue !Sub '${Environment}-vpc-id'
      SecurityGroupIngress:
        - IpProtocol: tcp
          FromPort: 80
          ToPort: 80
          CidrIp: 0.0.0.0/0
        - IpProtocol: tcp
          FromPort: 443
          ToPort: 443
          CidrIp: 0.0.0.0/0
      Tags:
        - Key: Name
          Value: !Sub '${Environment}-alb-sg'

  # Target Group
  ApplicationTargetGroup:
    Type: AWS::ElasticLoadBalancingV2::TargetGroup
    Properties:
      Name: !Sub '${Environment}-saas-tg'
      Port: 80
      Protocol: HTTP
      VpcId: !ImportValue !Sub '${Environment}-vpc-id'
      HealthCheckIntervalSeconds: 30
      HealthCheckPath: /health
      HealthCheckProtocol: HTTP
      HealthCheckTimeoutSeconds: 5
      HealthyThresholdCount: 2
      UnhealthyThresholdCount: 3
      TargetType: instance
      Tags:
        - Key: Name
          Value: !Sub '${Environment}-saas-tg'

  # ALB Listener
  ApplicationListener:
    Type: AWS::ElasticLoadBalancingV2::Listener
    Properties:
      DefaultActions:
        - Type: forward
          TargetGroupArn: !Ref ApplicationTargetGroup
      LoadBalancerArn: !Ref ApplicationLoadBalancer
      Port: 80
      Protocol: HTTP

  # Auto Scaling Group
  LaunchTemplate:
    Type: AWS::EC2::LaunchTemplate
    Properties:
      LaunchTemplateName: !Sub '${Environment}-saas-lt'
      LaunchTemplateData:
        ImageId: !Ref ImageId
        InstanceType: !FindInMap [EnvironmentMap, !Ref Environment, InstanceType]
        SecurityGroupIds:
          - !Ref ApplicationSecurityGroup
        IamInstanceProfile:
          Arn: !GetAtt ApplicationInstanceProfile.Arn
        UserData:
          Fn::Base64: !Sub |
            #!/bin/bash
            yum update -y
            yum install -y docker aws-cli
            systemctl start docker
            systemctl enable docker
            usermod -a -G docker ec2-user
            
            # CloudWatch エージェントインストール
            wget https://s3.amazonaws.com/amazoncloudwatch-agent/amazon_linux/amd64/latest/amazon-cloudwatch-agent.rpm
            rpm -U ./amazon-cloudwatch-agent.rpm
            
            # アプリケーション起動 (サンプル)
            docker run -d -p 80:8080 --name saas-app \
              -e ENVIRONMENT=${Environment} \
              nginx:latest
            
            # ヘルスチェックエンドポイント作成
            echo "OK" > /var/www/html/health
        TagSpecifications:
          - ResourceType: instance
            Tags:
              - Key: Name
                Value: !Sub '${Environment}-saas-instance'
              - Key: Environment
                Value: !Ref Environment

  ApplicationSecurityGroup:
    Type: AWS::EC2::SecurityGroup
    Properties:
      GroupDescription: Security group for application instances
      VpcId: !ImportValue !Sub '${Environment}-vpc-id'
      SecurityGroupIngress:
        - IpProtocol: tcp
          FromPort: 80
          ToPort: 80
          SourceSecurityGroupId: !Ref ALBSecurityGroup
        - IpProtocol: tcp
          FromPort: 22
          ToPort: 22
          CidrIp: 10.0.0.0/8  # VPC内からのSSHアクセス
      Tags:
        - Key: Name
          Value: !Sub '${Environment}-app-sg'

  AutoScalingGroup:
    Type: AWS::AutoScaling::AutoScalingGroup
    Properties:
      AutoScalingGroupName: !Sub '${Environment}-saas-asg'
      LaunchTemplate:
        LaunchTemplateId: !Ref LaunchTemplate
        Version: !GetAtt LaunchTemplate.LatestVersionNumber
      MinSize: !FindInMap [EnvironmentMap, !Ref Environment, MinSize]
      MaxSize: !FindInMap [EnvironmentMap, !Ref Environment, MaxSize]
      DesiredCapacity: !FindInMap [EnvironmentMap, !Ref Environment, MinSize]
      VPCZoneIdentifier:
        - !Select [0, !Split [',', !ImportValue !Sub '${Environment}-private-subnets']]
        - !Select [1, !Split [',', !ImportValue !Sub '${Environment}-private-subnets']]
      TargetGroupARNs:
        - !Ref ApplicationTargetGroup
      HealthCheckType: ELB
      HealthCheckGracePeriod: 300
      Tags:
        - Key: Name
          Value: !Sub '${Environment}-saas-asg'
          PropagateAtLaunch: false

  # IAM Role for EC2 instances
  ApplicationRole:
    Type: AWS::IAM::Role
    Properties:
      RoleName: !Sub '${Environment}-saas-ec2-role'
      AssumeRolePolicyDocument:
        Version: '2012-10-17'
        Statement:
          - Effect: Allow
            Principal:
              Service: ec2.amazonaws.com
            Action: sts:AssumeRole
      ManagedPolicyArns:
        - arn:aws:iam::aws:policy/CloudWatchAgentServerPolicy
        - arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore
      Policies:
        - PolicyName: ApplicationPolicy
          PolicyDocument:
            Version: '2012-10-17'
            Statement:
              - Effect: Allow
                Action:
                  - s3:GetObject
                  - s3:PutObject
                Resource: 
                  - !Sub 'arn:aws:s3:::${Environment}-saas-app-bucket/*'
              - Effect: Allow
                Action:
                  - rds:DescribeDBInstances
                  - rds:DescribeDBClusters
                Resource: '*'

  ApplicationInstanceProfile:
    Type: AWS::IAM::InstanceProfile
    Properties:
      InstanceProfileName: !Sub '${Environment}-saas-ec2-profile'
      Roles:
        - !Ref ApplicationRole

  # RDS Database
  DatabaseSecurityGroup:
    Type: AWS::EC2::SecurityGroup
    Properties:
      GroupDescription: Security group for RDS database
      VpcId: !ImportValue !Sub '${Environment}-vpc-id'
      SecurityGroupIngress:
        - IpProtocol: tcp
          FromPort: 3306
          ToPort: 3306
          SourceSecurityGroupId: !Ref ApplicationSecurityGroup
      Tags:
        - Key: Name
          Value: !Sub '${Environment}-db-sg'

  Database:
    Type: AWS::RDS::DBInstance
    DeletionPolicy: !If [!Equals [!Ref Environment, prod], Snapshot, Delete]
    Properties:
      DBInstanceIdentifier: !Sub '${Environment}-saas-db'
      DBInstanceClass: !FindInMap [EnvironmentMap, !Ref Environment, DatabaseClass]
      Engine: mysql
      EngineVersion: '8.0.35'
      AllocatedStorage: 20
      StorageType: gp2
      StorageEncrypted: true
      MasterUsername: admin
      MasterUserPassword: !Sub '{{resolve:secretsmanager:${Environment}-db-password:SecretString:password}}'
      DBSubnetGroupName: !ImportValue !Sub '${Environment}-db-subnet-group'
      VPCSecurityGroups:
        - !Ref DatabaseSecurityGroup
      BackupRetentionPeriod: !If [!Equals [!Ref Environment, prod], 7, 1]
      MultiAZ: !If [!Equals [!Ref Environment, prod], true, false]
      PubliclyAccessible: false
      Tags:
        - Key: Name
          Value: !Sub '${Environment}-saas-db'

Conditions:
  IsProduction: !Equals [!Ref Environment, prod]

Outputs:
  LoadBalancerDNS:
    Description: Application Load Balancer DNS
    Value: !GetAtt ApplicationLoadBalancer.DNSName
    Export:
      Name: !Sub '${Environment}-alb-dns'

  DatabaseEndpoint:
    Description: RDS Database Endpoint
    Value: !GetAtt Database.Endpoint.Address
    Export:
      Name: !Sub '${Environment}-db-endpoint'
EOF
```

## Phase 2: AWS CDK による高度なインフラ構築

### 2.1 CDK プロジェクト初期化

```bash
#!/bin/bash
# CDK環境セットアップ

echo "=== AWS CDK 環境セットアップ開始 ==="

# CDKインストール確認
if ! command -v cdk &> /dev/null; then
    echo "CDKをインストール中..."
    npm install -g aws-cdk
fi

# CDKプロジェクト作成
mkdir saas-cdk-infrastructure
cd saas-cdk-infrastructure

# TypeScript CDKアプリ初期化
cdk init app --language typescript

# 必要な依存関係インストール
npm install @aws-cdk/aws-ec2 @aws-cdk/aws-ecs @aws-cdk/aws-ecs-patterns \
  @aws-cdk/aws-rds @aws-cdk/aws-elasticloadbalancingv2 @aws-cdk/aws-autoscaling \
  @aws-cdk/aws-route53 @aws-cdk/aws-certificatemanager @aws-cdk/aws-s3 \
  @aws-cdk/aws-cloudfront @aws-cdk/aws-iam @aws-cdk/aws-logs

echo "✅ CDK環境セットアップ完了"
```

### 2.2 CDK スタック実装

```typescript
// lib/saas-infrastructure-stack.ts
import * as cdk from '@aws-cdk/core';
import * as ec2 from '@aws-cdk/aws-ec2';
import * as ecs from '@aws-cdk/aws-ecs';
import * as ecsPatterns from '@aws-cdk/aws-ecs-patterns';
import * as rds from '@aws-cdk/aws-rds';
import * as s3 from '@aws-cdk/aws-s3';
import * as cloudfront from '@aws-cdk/aws-cloudfront';
import * as route53 from '@aws-cdk/aws-route53';
import * as acm from '@aws-cdk/aws-certificatemanager';
import * as logs from '@aws-cdk/aws-logs';

export interface SaasInfrastructureStackProps extends cdk.StackProps {
  environment: string;
  domainName?: string;
}

export class SaasInfrastructureStack extends cdk.Stack {
  public readonly vpc: ec2.Vpc;
  public readonly cluster: ecs.Cluster;
  public readonly database: rds.DatabaseInstance;

  constructor(scope: cdk.Construct, id: string, props: SaasInfrastructureStackProps) {
    super(scope, id, props);

    const { environment } = props;

    // VPC作成
    this.vpc = new ec2.Vpc(this, 'SaasVpc', {
      cidr: this.getCidrForEnvironment(environment),
      maxAzs: 2,
      natGateways: environment === 'prod' ? 2 : 1,
      subnetConfiguration: [
        {
          cidrMask: 24,
          name: 'public',
          subnetType: ec2.SubnetType.PUBLIC,
        },
        {
          cidrMask: 24,
          name: 'private',
          subnetType: ec2.SubnetType.PRIVATE_WITH_NAT,
        },
        {
          cidrMask: 24,
          name: 'isolated',
          subnetType: ec2.SubnetType.ISOLATED,
        },
      ],
    });

    // ECS クラスター
    this.cluster = new ecs.Cluster(this, 'SaasCluster', {
      vpc: this.vpc,
      clusterName: `${environment}-saas-cluster`,
      containerInsights: environment === 'prod',
    });

    // Auto Scaling Group
    this.cluster.addCapacity('DefaultAutoScalingGroup', {
      instanceType: this.getInstanceTypeForEnvironment(environment),
      minCapacity: this.getMinCapacityForEnvironment(environment),
      maxCapacity: this.getMaxCapacityForEnvironment(environment),
      vpcSubnets: {
        subnetType: ec2.SubnetType.PRIVATE_WITH_NAT,
      },
    });

    // RDS データベース
    this.database = new rds.DatabaseInstance(this, 'SaasDatabase', {
      engine: rds.DatabaseInstanceEngine.mysql({
        version: rds.MysqlEngineVersion.VER_8_0_35,
      }),
      instanceType: this.getDatabaseInstanceTypeForEnvironment(environment),
      vpc: this.vpc,
      vpcSubnets: {
        subnetType: ec2.SubnetType.ISOLATED,
      },
      multiAz: environment === 'prod',
      storageEncrypted: true,
      backupRetention: environment === 'prod' ? cdk.Duration.days(7) : cdk.Duration.days(1),
      deletionProtection: environment === 'prod',
      databaseName: 'saasapp',
      credentials: rds.Credentials.fromGeneratedSecret('admin'),
    });

    // S3 バケット (アプリケーションデータ用)
    const applicationBucket = new s3.Bucket(this, 'ApplicationBucket', {
      bucketName: `${environment}-saas-app-data-${this.account}`,
      versioned: environment === 'prod',
      encryption: s3.BucketEncryption.S3_MANAGED,
      blockPublicAccess: s3.BlockPublicAccess.BLOCK_ALL,
      removalPolicy: environment === 'prod' ? cdk.RemovalPolicy.RETAIN : cdk.RemovalPolicy.DESTROY,
    });

    // CloudWatch Log Group
    const logGroup = new logs.LogGroup(this, 'ApplicationLogGroup', {
      logGroupName: `/aws/ecs/${environment}-saas`,
      retention: environment === 'prod' ? logs.RetentionDays.SIX_MONTHS : logs.RetentionDays.ONE_WEEK,
    });

    // ECS サービス (Fargate)
    const fargateService = new ecsPatterns.ApplicationLoadBalancedFargateService(this, 'SaasService', {
      cluster: this.cluster,
      taskImageOptions: {
        image: ecs.ContainerImage.fromRegistry('nginx:latest'), // 実際のアプリケーションイメージに置換
        containerPort: 80,
        environment: {
          ENVIRONMENT: environment,
          DATABASE_HOST: this.database.instanceEndpoint.hostname,
          S3_BUCKET: applicationBucket.bucketName,
        },
        logDriver: ecs.LogDrivers.awsLogs({
          streamPrefix: 'ecs',
          logGroup: logGroup,
        }),
      },
      memoryLimitMiB: this.getMemoryForEnvironment(environment),
      cpu: this.getCpuForEnvironment(environment),
      desiredCount: this.getDesiredCountForEnvironment(environment),
      publicLoadBalancer: true,
      listenerPort: 80,
    });

    // データベースアクセス許可
    this.database.connections.allowDefaultPortFrom(fargateService.service);

    // S3アクセス許可
    applicationBucket.grantReadWrite(fargateService.taskDefinition.taskRole);

    // Auto Scaling設定
    const scaling = fargateService.service.autoScaleTaskCount({
      minCapacity: this.getDesiredCountForEnvironment(environment),
      maxCapacity: this.getMaxTaskCountForEnvironment(environment),
    });

    scaling.scaleOnCpuUtilization('CpuScaling', {
      targetUtilizationPercent: 70,
      scaleInCooldown: cdk.Duration.minutes(5),
      scaleOutCooldown: cdk.Duration.minutes(2),
    });

    scaling.scaleOnMemoryUtilization('MemoryScaling', {
      targetUtilizationPercent: 80,
    });

    // CloudFront (本番環境のみ)
    if (environment === 'prod' && props.domainName) {
      const certificate = new acm.Certificate(this, 'Certificate', {
        domainName: props.domainName,
        validation: acm.CertificateValidation.fromDns(),
      });

      const distribution = new cloudfront.CloudFrontWebDistribution(this, 'Distribution', {
        originConfigs: [
          {
            customOriginSource: {
              domainName: fargateService.loadBalancer.loadBalancerDnsName,
              httpPort: 80,
            },
            behaviors: [{ isDefaultBehavior: true }],
          },
        ],
        viewerCertificate: cloudfront.ViewerCertificate.fromAcmCertificate(certificate, {
          aliases: [props.domainName],
        }),
      });

      // Route53 レコード
      const hostedZone = route53.HostedZone.fromLookup(this, 'HostedZone', {
        domainName: props.domainName,
      });

      new route53.ARecord(this, 'ARecord', {
        zone: hostedZone,
        target: route53.RecordTarget.fromAlias(new targets.CloudFrontTarget(distribution)),
      });
    }

    // 出力
    new cdk.CfnOutput(this, 'LoadBalancerDNS', {
      value: fargateService.loadBalancer.loadBalancerDnsName,
      exportName: `${environment}-saas-alb-dns`,
    });

    new cdk.CfnOutput(this, 'DatabaseEndpoint', {
      value: this.database.instanceEndpoint.hostname,
      exportName: `${environment}-saas-db-endpoint`,
    });

    new cdk.CfnOutput(this, 'ClusterName', {
      value: this.cluster.clusterName,
      exportName: `${environment}-saas-cluster-name`,
    });
  }

  private getCidrForEnvironment(environment: string): string {
    const cidrMap: { [key: string]: string } = {
      dev: '10.0.0.0/16',
      staging: '10.1.0.0/16',
      prod: '10.2.0.0/16',
    };
    return cidrMap[environment] || '10.0.0.0/16';
  }

  private getInstanceTypeForEnvironment(environment: string): ec2.InstanceType {
    const typeMap: { [key: string]: ec2.InstanceType } = {
      dev: new ec2.InstanceType('t3.micro'),
      staging: new ec2.InstanceType('t3.small'),
      prod: new ec2.InstanceType('t3.medium'),
    };
    return typeMap[environment] || new ec2.InstanceType('t3.micro');
  }

  private getMinCapacityForEnvironment(environment: string): number {
    const capacityMap: { [key: string]: number } = {
      dev: 1,
      staging: 2,
      prod: 3,
    };
    return capacityMap[environment] || 1;
  }

  private getMaxCapacityForEnvironment(environment: string): number {
    const capacityMap: { [key: string]: number } = {
      dev: 3,
      staging: 5,
      prod: 10,
    };
    return capacityMap[environment] || 3;
  }

  private getDatabaseInstanceTypeForEnvironment(environment: string): ec2.InstanceType {
    const typeMap: { [key: string]: ec2.InstanceType } = {
      dev: new ec2.InstanceType('db.t3.micro'),
      staging: new ec2.InstanceType('db.t3.small'),
      prod: new ec2.InstanceType('db.r5.large'),
    };
    return typeMap[environment] || new ec2.InstanceType('db.t3.micro');
  }

  private getMemoryForEnvironment(environment: string): number {
    const memoryMap: { [key: string]: number } = {
      dev: 512,
      staging: 1024,
      prod: 2048,
    };
    return memoryMap[environment] || 512;
  }

  private getCpuForEnvironment(environment: string): number {
    const cpuMap: { [key: string]: number } = {
      dev: 256,
      staging: 512,
      prod: 1024,
    };
    return cpuMap[environment] || 256;
  }

  private getDesiredCountForEnvironment(environment: string): number {
    const countMap: { [key: string]: number } = {
      dev: 1,
      staging: 2,
      prod: 3,
    };
    return countMap[environment] || 1;
  }

  private getMaxTaskCountForEnvironment(environment: string): number {
    const maxCountMap: { [key: string]: number } = {
      dev: 3,
      staging: 6,
      prod: 12,
    };
    return maxCountMap[environment] || 3;
  }
}
```

### 2.3 CDK アプリケーション設定

```typescript
// bin/saas-cdk-infrastructure.ts
#!/usr/bin/env node
import 'source-map-support/register';
import * as cdk from '@aws-cdk/core';
import { SaasInfrastructureStack } from '../lib/saas-infrastructure-stack';

const app = new cdk.App();

// 環境設定
const environments = ['dev', 'staging', 'prod'];

environments.forEach(environment => {
  new SaasInfrastructureStack(app, `SaasInfrastructureStack-${environment}`, {
    environment,
    domainName: environment === 'prod' ? 'api.example.com' : undefined,
    env: {
      account: process.env.CDK_DEFAULT_ACCOUNT,
      region: process.env.CDK_DEFAULT_REGION || 'ap-northeast-1',
    },
    tags: {
      Environment: environment,
      Project: 'SaaS-Platform',
      ManagedBy: 'CDK',
    },
  });
});
```

## Phase 3: デプロイメントと検証

### 3.1 デプロイメントスクリプト

```bash
#!/bin/bash
# deploy-all-environments.sh

set -e

echo "=== 全環境デプロイメント開始 ===="

ENVIRONMENTS=("dev" "staging" "prod")

# CloudFormation デプロイ
for env in "${ENVIRONMENTS[@]}"; do
    echo "🚀 $env 環境のCloudFormationデプロイ開始..."
    
    # ネットワーク基盤
    ./deploy-network-infrastructure.sh $env
    
    # アプリケーション基盤
    aws cloudformation create-stack \
        --stack-name "saas-app-$env" \
        --template-body file://application-infrastructure.yaml \
        --parameters ParameterKey=Environment,ParameterValue=$env \
        --capabilities CAPABILITY_IAM \
        --region ap-northeast-1
    
    aws cloudformation wait stack-create-complete \
        --stack-name "saas-app-$env" \
        --region ap-northeast-1
    
    echo "✅ $env 環境のCloudFormationデプロイ完了"
done

# CDK デプロイ
echo "🚀 CDKスタックデプロイ開始..."
cd saas-cdk-infrastructure

# CDK bootstrap (初回のみ)
cdk bootstrap

# 全環境デプロイ
for env in "${ENVIRONMENTS[@]}"; do
    echo "   $env 環境のCDKデプロイ中..."
    cdk deploy "SaasInfrastructureStack-$env" --require-approval never
done

echo "✅ 全環境デプロイ完了"

# 結果サマリー
echo "=== デプロイ結果サマリー ==="
for env in "${ENVIRONMENTS[@]}"; do
    echo "📋 $env 環境:"
    
    # CloudFormation出力
    echo "  CloudFormation ALB DNS:"
    aws cloudformation describe-stacks \
        --stack-name "saas-app-$env" \
        --query 'Stacks[0].Outputs[?OutputKey==`LoadBalancerDNS`].OutputValue' \
        --output text
    
    # CDK出力
    echo "  CDK Cluster:"
    aws cloudformation describe-stacks \
        --stack-name "SaasInfrastructureStack-$env" \
        --query 'Stacks[0].Outputs[?OutputKey==`ClusterName`].OutputValue' \
        --output text
    
    echo ""
done
```

### 3.2 コスト計算スクリプト

```python
#!/usr/bin/env python3
# cost-calculator.py

import boto3
import json
from datetime import datetime, timedelta

def calculate_infrastructure_costs():
    """
    インフラストラクチャコストの計算
    """
    
    # 料金定義 (ap-northeast-1)
    costs = {
        'dev': {
            'ec2_hours': 24 * 30,  # t3.micro
            'ec2_rate': 0.0116,
            'rds_hours': 24 * 30,  # db.t3.micro
            'rds_rate': 0.022,
            'nat_gateway_hours': 24 * 30,
            'nat_gateway_rate': 0.062,
            'alb_hours': 24 * 30,
            'alb_rate': 0.0243,
            'eip_hours': 24 * 30,
            'eip_rate': 0.005,
        },
        'staging': {
            'ec2_hours': 24 * 30 * 2,  # t3.small x2
            'ec2_rate': 0.0232,
            'rds_hours': 24 * 30,  # db.t3.small
            'rds_rate': 0.044,
            'nat_gateway_hours': 24 * 30,
            'nat_gateway_rate': 0.062,
            'alb_hours': 24 * 30,
            'alb_rate': 0.0243,
            'eip_hours': 24 * 30,
            'eip_rate': 0.005,
        },
        'prod': {
            'ec2_hours': 24 * 30 * 3,  # t3.medium x3
            'ec2_rate': 0.0464,
            'rds_hours': 24 * 30,  # db.r5.large + Multi-AZ
            'rds_rate': 0.24 * 2,  # Multi-AZ
            'nat_gateway_hours': 24 * 30 * 2,  # 2 NAT Gateways
            'nat_gateway_rate': 0.062,
            'alb_hours': 24 * 30,
            'alb_rate': 0.0243,
            'eip_hours': 24 * 30 * 2,  # 2 EIPs
            'eip_rate': 0.005,
            'cloudfront_requests': 1000000,  # 1M requests
            'cloudfront_rate': 0.012,
        }
    }
    
    print("=== AWS インフラストラクチャ月額コスト試算 ===\n")
    
    total_all_environments = 0
    
    for env, cost_data in costs.items():
        print(f"🏗️  {env.upper()} 環境:")
        
        ec2_cost = cost_data['ec2_hours'] * cost_data['ec2_rate']
        rds_cost = cost_data['rds_hours'] * cost_data['rds_rate']
        nat_cost = cost_data['nat_gateway_hours'] * cost_data['nat_gateway_rate']
        alb_cost = cost_data['alb_hours'] * cost_data['alb_rate']
        eip_cost = cost_data['eip_hours'] * cost_data['eip_rate']
        
        total_env = ec2_cost + rds_cost + nat_cost + alb_cost + eip_cost
        
        print(f"  EC2 Instances: ${ec2_cost:.2f}")
        print(f"  RDS Database:  ${rds_cost:.2f}")
        print(f"  NAT Gateway:   ${nat_cost:.2f}")
        print(f"  Load Balancer: ${alb_cost:.2f}")
        print(f"  Elastic IPs:   ${eip_cost:.2f}")
        
        if env == 'prod' and 'cloudfront_requests' in cost_data:
            cloudfront_cost = (cost_data['cloudfront_requests'] / 10000) * cost_data['cloudfront_rate']
            total_env += cloudfront_cost
            print(f"  CloudFront:    ${cloudfront_cost:.2f}")
        
        print(f"  💰 {env} 合計: ${total_env:.2f}/月\n")
        
        total_all_environments += total_env
    
    print(f"🎯 全環境合計: ${total_all_environments:.2f}/月")
    print(f"📊 年間推定:   ${total_all_environments * 12:.2f}/年")
    
    # コスト削減提案
    print("\n💡 コスト最適化提案:")
    print("- 開発環境は夜間・週末停止で70%削減可能")
    print("- Spot Instancesで最大90%削減")
    print("- Reserved Instancesで最大72%削減")
    print("- 不要なリソースの定期クリーンアップ")

if __name__ == "__main__":
    calculate_infrastructure_costs()
```

### 3.3 クリーンアップスクリプト

```bash
#!/bin/bash
# cleanup-all-environments.sh

set -e

echo "=== 全環境クリーンアップ開始 ==="

ENVIRONMENTS=("dev" "staging" "prod")

read -p "全ての環境を削除しますか？ (yes/no): " confirm
if [ "$confirm" != "yes" ]; then
    echo "キャンセルされました"
    exit 1
fi

# CDKスタック削除
echo "🗑️  CDKスタック削除中..."
cd saas-cdk-infrastructure

for env in "${ENVIRONMENTS[@]}"; do
    echo "   $env 環境のCDKスタック削除中..."
    cdk destroy "SaasInfrastructureStack-$env" --force
done

cd ..

# CloudFormationスタック削除
for env in "${ENVIRONMENTS[@]}"; do
    echo "🗑️  $env 環境のCloudFormationスタック削除中..."
    
    # アプリケーションスタック削除
    aws cloudformation delete-stack --stack-name "saas-app-$env"
    aws cloudformation wait stack-delete-complete --stack-name "saas-app-$env"
    
    # ネットワークスタック削除
    aws cloudformation delete-stack --stack-name "saas-network-$env"
    aws cloudformation wait stack-delete-complete --stack-name "saas-network-$env"
    
    echo "✅ $env 環境削除完了"
done

echo "🎉 全環境クリーンアップ完了"

# 削除確認
echo "=== 削除確認 ==="
remaining_stacks=$(aws cloudformation list-stacks \
    --stack-status-filter CREATE_COMPLETE UPDATE_COMPLETE \
    --query 'StackSummaries[?contains(StackName, `saas`)].StackName' \
    --output text)

if [ -z "$remaining_stacks" ]; then
    echo "✅ 全てのスタックが正常に削除されました"
else
    echo "⚠️  以下のスタックが残っています:"
    echo "$remaining_stacks"
fi
```

## 📊 学習ポイントと検証

### 重要な概念
1. **Infrastructure as Code**: インフラをコードで管理する利点
2. **環境分離**: dev/staging/prod の適切な分離方法
3. **スケーラビリティ**: Auto Scaling の設計パターン
4. **セキュリティ**: セキュリティグループとIAMの最小権限
5. **コスト最適化**: 環境ごとのリソースサイジング

### 実践で学ぶスキル
- CloudFormationテンプレートの実装
- AWS CDKによるプログラマティックなインフラ構築
- 複数環境でのリソース管理
- コスト計算と最適化戦略

### 次のステップ
このLabが完了したら、[Lab 3: 包括的監視・ロギングシステム](./lab03-monitoring-logging.md) に進んでください。

---

**⚠️ 重要**: 学習後は必ずクリーンアップスクリプトを実行してコストを抑制してください。