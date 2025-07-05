# ANS-C01 想定問題集 01 - VPC設計とネットワーク基盤

## 📋 試験情報

**Domain Focus**: Domain 1 - Network Design (30%)  
**問題数**: 20問  
**制限時間**: 35分  
**合格点**: 14/20 (70%)

---

## 🔧 問題 1

あなたは大手eコマース企業のネットワークアーキテクトです。以下の要件を満たすVPC設計を実装する必要があります：

- アプリケーション層、データベース層、DMZ層の3層構成
- 各層のマルチAZ冗長化
- データベース層は外部からの直接アクセス禁止
- 管理アクセスは特定IPアドレスからのみ

最適なセキュリティグループ構成は？

**A)** 単一のセキュリティグループで全層をカバー、ポート22/80/443/3306を0.0.0.0/0に開放  
**B)** 層ごとにセキュリティグループを分離、各層間は前の層からのアクセスのみ許可  
**C)** パブリックサブネット用とプライベートサブネット用の2つのセキュリティグループ  
**D)** データベース用セキュリティグループのみ作成、他は全てdefaultセキュリティグループを使用

<details>
<summary>解答と解説</summary>

**正解: B**

**解説:**
3層アーキテクチャでは**Defense in Depth (多層防御)**の原則に従い、各層に専用のセキュリティグループを設定します。

**適切な構成:**
```bash
# DMZ層 (Web tier)
- Inbound: HTTP(80), HTTPS(443) from 0.0.0.0/0
- Inbound: SSH(22) from 管理CIDR
- Outbound: アプリケーション層のポート8080

# アプリケーション層
- Inbound: 8080 from DMZ層セキュリティグループ
- Inbound: SSH(22) from 管理セキュリティグループ
- Outbound: データベース層のポート3306

# データベース層
- Inbound: 3306 from アプリケーション層セキュリティグループのみ
- Outbound: なし (必要最小限)
```

**セキュリティ原則:**
1. **最小権限の原則**: 必要最小限のアクセスのみ許可
2. **層間分離**: 各層は隣接する層とのみ通信
3. **管理アクセス制御**: SSH/RDPは管理用SGからのみ

**他の選択肢が不適切な理由:**
- A: 0.0.0.0/0での全ポート開放は重大なセキュリティリスク
- C: 2つのSGでは細かい層間制御が不可能
- D: defaultSGの使用は設定変更時の影響範囲が不明確
</details>

---

## 🔧 問題 2

企業の本社（オンプレミス）とAWS VPCを接続する要件があります。以下の条件があります：

- 帯域幅: 1Gbps以上が必要
- レイテンシ: 10ms以下
- 可用性: 99.9%以上
- セキュリティ: 専用線での接続が必須

最適な接続方法は？

**A)** Site-to-Site VPN with BGP routing  
**B)** AWS Direct Connect with single connection  
**C)** AWS Direct Connect with redundant connections  
**D)** CloudFront + API Gateway configuration

<details>
<summary>解答と解説</summary>

**正解: C**

**解説:**
要件分析から、**AWS Direct Connect の冗長構成**が最適です。

**要件分析:**
- **帯域幅 1Gbps以上**: Direct Connectは1Gbps, 10Gbpsポートを提供
- **レイテンシ 10ms以下**: 専用線なので安定した低レイテンシ
- **可用性 99.9%以上**: 冗長構成が必須
- **専用線接続**: Direct Connectは物理専用線

**冗長構成のベストプラクティス:**
```bash
# 推奨構成
Primary DX: 1Gbps port in AZ-1
Secondary DX: 1Gbps port in AZ-2 (異なるロケーション)

# または
Primary DX: 10Gbps port
Backup VPN: Site-to-Site VPN (コスト効率的な冗長化)
```

**SLA比較:**
- Direct Connect単体: 99.9%
- Direct Connect冗長: 99.99%+
- Site-to-Site VPN: 99.95%

**他の選択肢が不適切な理由:**
- A: VPNは帯域幅制限（1.25Gbps max）とレイテンシ変動あり
- B: 単一接続では可用性要件を満たせない
- D: CloudFrontは接続ソリューションではない
</details>

---

## 🔧 問題 3

大規模なマルチアカウント環境で、以下の要件を満たすネットワーク設計が必要です：

- 50個のVPCを相互接続
- 各VPCは異なるAWSアカウント
- 集中型の接続管理
- オンプレミスとの単一接続点

最適なソリューションは？

**A)** 全VPC間でVPC Peering接続  
**B)** Transit Gateway with Resource Access Manager (RAM)  
**C)** AWS PrivateLink for all connections  
**D)** CloudHub VPN configuration

<details>
<summary>解答と解説</summary>

**正解: B**

**解説:**
大規模マルチアカウント環境では**Transit Gateway + RAM**が最適です。

**スケーラビリティ比較:**
```
VPC Peering: 50 VPCs = 50×49/2 = 1,225接続（管理困難）
Transit Gateway: 50 VPCs = 50接続（集中管理）
```

**Transit Gateway + RAMの利点:**
1. **集中管理**: 単一のTGWで全VPC接続
2. **クロスアカウント**: RAMでリソース共有
3. **オンプレミス接続**: 単一接続点での集約
4. **ルーティング制御**: Route Tableで細かい制御

**実装例:**
```bash
# メインアカウント
aws ec2 create-transit-gateway --description "Central-TGW"

# RAM設定
aws ram create-resource-share \
  --name "TGW-Share" \
  --resource-arns arn:aws:ec2:region:account:transit-gateway/tgw-xxx

# 各アカウントでVPC attachment
aws ec2 create-transit-gateway-vpc-attachment \
  --transit-gateway-id tgw-xxx \
  --vpc-id vpc-xxx
```

**コスト比較（月額）:**
- VPC Peering: $0.01/GB × 通信量
- Transit Gateway: $36/月 + $0.02/GB
- PrivateLink: $7.2/endpoint/月 + $0.01/GB

**他の選択肢が不適切な理由:**
- A: VPC Peeringは大規模環境で管理複雑
- C: PrivateLinkは特定サービス間接続用
- D: CloudHub VPNは主にVPN集約用
</details>

---

## 🔧 問題 4

WebアプリケーションのCDN構成で、以下の要件があります：

- グローバルユーザーへの低レイテンシ配信
- オリジンサーバーはALB（3つのAZ）
- HTTPS通信の完全な暗号化
- カスタムドメイン名の使用

CloudFrontの適切な構成は？

**A)** Origin: ALB DNS name, Viewer Protocol: HTTP only  
**B)** Origin: ALB DNS name, Viewer Protocol: HTTPS redirect, Origin Protocol: HTTPS  
**C)** Origin: EC2 instances directly, Viewer Protocol: HTTPS only  
**D)** Origin: S3 bucket, Viewer Protocol: HTTPS redirect

<details>
<summary>解答と解説</summary>

**正解: B**

**解説:**
HTTPS完全暗号化とALBオリジンの要件から、**HTTPS redirect + HTTPS Origin**が適切です。

**CloudFront + ALB構成:**
```json
{
  "Origins": {
    "DomainName": "my-alb-123456789.ap-northeast-1.elb.amazonaws.com",
    "OriginProtocolPolicy": "https-only",
    "OriginSSLProtocols": ["TLSv1.2"]
  },
  "DefaultCacheBehavior": {
    "ViewerProtocolPolicy": "redirect-to-https",
    "OriginRequestPolicyId": "managed-cors-s3origin"
  }
}
```

**SSL/TLS証明書設定:**
1. **CloudFront**: us-east-1のACM証明書（必須）
2. **ALB**: 任意リージョンのACM証明書
3. **カスタムドメイン**: Route 53 ALIAS レコード

**セキュリティベストプラクティス:**
- **Viewer → CloudFront**: HTTPS必須
- **CloudFront → ALB**: HTTPS必須
- **TLS1.2以上**: 古いプロトコル無効化
- **HSTS**: セキュリティヘッダー追加

**パフォーマンス最適化:**
```
# キャッシュ戦略
Static Content: 1 year TTL
Dynamic Content: 1 minute TTL
API Responses: No cache
```

**他の選択肢が不適切な理由:**
- A: HTTP通信はセキュリティ要件に不適合
- C: EC2直接接続は冗長性とスケーラビリティに劣る
- D: S3オリジンはWebアプリケーション用途に不適切
</details>

---

## 🔧 問題 5

Route 53 を使用したDNS設計で、以下の要件があります：

- フェイルオーバー機能
- ヘルスチェック機能
- 地理的ルーティング（日本、アメリカ、ヨーロッパ）
- レイテンシベースルーティング

最適な構成は？

**A)** Simple routing policy only  
**B)** Weighted routing with health checks  
**C)** Geolocation routing with latency-based secondary  
**D)** Multivalue answer routing

<details>
<summary>解答と解説</summary>

**正解: C**

**解説:**
地理的要件と複数の高度機能から、**Geolocation + Latency-based**の組み合わせが最適です。

**階層化DNS設計:**
```
Level 1: Geolocation routing
├── Japan → japan.example.com
├── US → us.example.com  
├── Europe → eu.example.com
└── Default → global.example.com

Level 2: Latency-based routing (各地域内)
japan.example.com:
├── ap-northeast-1 (Primary)
├── ap-southeast-1 (Secondary)
└── Health Check enabled
```

**ヘルスチェック設定:**
```json
{
  "Type": "HTTPS",
  "ResourcePath": "/health",
  "Interval": 30,
  "FailureThreshold": 3,
  "RequestInterval": "Fast"
}
```

**フェイルオーバー戦略:**
1. **地域内フェイルオーバー**: Latency-based + Health Check
2. **地域間フェイルオーバー**: 地域全体がダウン時にDefault regionへ
3. **段階的フェイルオーバー**: Primary → Secondary → Tertiary

**実装例:**
```bash
# Primary record (Japan)
aws route53 change-resource-record-sets --change-batch '{
  "Changes": [{
    "Action": "CREATE",
    "ResourceRecordSet": {
      "Name": "api.example.com",
      "Type": "A",
      "GeoLocation": {"CountryCode": "JP"},
      "SetIdentifier": "Japan-Primary",
      "AliasTarget": {
        "DNSName": "tokyo-alb.elb.amazonaws.com"
      },
      "HealthCheckId": "tokyo-health-check"
    }
  }]
}'
```

**パフォーマンス最適化:**
- **DNS TTL**: 60秒（フェイルオーバー速度）
- **Health Check間隔**: 30秒
- **Resolver Endpoint**: VPC内DNS最適化

**他の選択肢が不適切な理由:**
- A: Simple routingは高度機能なし
- B: Weightedは地理的要件を満たせない
- D: Multivalueは主にランダム分散用
</details>

---

## 🔧 問題 6

VPC内のプライベートサブネットから、特定のAWSサービス（S3、DynamoDB）への接続を最適化したい。インターネットゲートウェイやNATゲートウェイを経由せずに接続する方法は？

**A)** VPC Endpoints (Gateway型) for S3 and DynamoDB  
**B)** VPC Endpoints (Interface型) for all services  
**C)** AWS PrivateLink for S3 and DynamoDB  
**D)** Direct Connect private virtual interface

<details>
<summary>解答と解説</summary>

**正解: A**

**解説:**
S3とDynamoDBは**Gateway型VPC Endpoint**で最適化できます。

**VPC Endpoint種類:**
```
Gateway型 VPC Endpoint:
- S3, DynamoDB (無料)
- ルートテーブルでの設定
- 帯域幅制限なし

Interface型 VPC Endpoint:
- その他のAWSサービス (有料: $7.2/月/endpoint)
- ENI-based接続
- PrivateLink使用
```

**実装手順:**
```bash
# S3 Gateway Endpoint
aws ec2 create-vpc-endpoint \
  --vpc-id vpc-12345678 \
  --service-name com.amazonaws.ap-northeast-1.s3 \
  --vpc-endpoint-type Gateway \
  --route-table-ids rtb-12345678

# DynamoDB Gateway Endpoint  
aws ec2 create-vpc-endpoint \
  --vpc-id vpc-12345678 \
  --service-name com.amazonaws.ap-northeast-1.dynamodb \
  --vpc-endpoint-type Gateway \
  --route-table-ids rtb-12345678
```

**ルートテーブル自動更新:**
```
Destination: pl-61a54008 (S3 prefix list)
Target: vpce-12345678 (VPC Endpoint)
```

**セキュリティと性能の利点:**
1. **プライベート通信**: インターネット経由なし
2. **コスト削減**: NAT Gateway料金不要
3. **帯域幅向上**: AWS backbone使用
4. **セキュリティ**: VPC内通信のみ

**ポリシー例:**
```json
{
  "Statement": [{
    "Effect": "Allow",
    "Principal": "*",
    "Action": "s3:GetObject",
    "Resource": "arn:aws:s3:::my-bucket/*",
    "Condition": {
      "StringEquals": {
        "aws:sourceVpc": "vpc-12345678"
      }
    }
  }]
}
```

**他の選択肢が不適切な理由:**
- B: Interface型は高コスト、S3/DynamoDBにはGateway型が最適
- C: PrivateLinkはInterface型VPC Endpointの基盤技術
- D: Direct Connectは本問題の要件に過大
</details>

---

## 🔧 問題 7

ネットワークセキュリティ強化のため、VPC Flow Logsを設定して、セキュリティ違反を検出したい。最も効果的な設定は？

**A)** VPC レベルで ACCEPT トラフィックのみログ  
**B)** Subnet レベルで ALL トラフィックをログ  
**C)** ENI レベルで REJECT トラフィックのみログ  
**D)** VPC レベルで ALL トラフィック、CloudWatch Logs + Kinesis Data Firehose

<details>
<summary>解答と解説</summary>

**正解: D**

**解説:**
包括的なセキュリティ監視には**VPC レベル + ALL トラフィック + 高度な分析基盤**が必要です。

**VPC Flow Logs最適設定:**
```bash
aws ec2 create-flow-logs \
  --resource-type VPC \
  --resource-ids vpc-12345678 \
  --traffic-type ALL \
  --log-destination-type cloud-watch-logs \
  --log-destination arn:aws:logs:region:account:log-group:VPCFlowLogs \
  --log-format '${version} ${account-id} ${interface-id} ${srcaddr} ${dstaddr} ${srcport} ${dstport} ${protocol} ${packets} ${bytes} ${windowstart} ${windowend} ${action}'
```

**セキュリティ分析パターン:**
1. **異常なポートスキャン検出**:
   ```sql
   SELECT srcaddr, COUNT(DISTINCT dstport) as port_count 
   FROM flowlogs 
   WHERE action = 'REJECT' 
   GROUP BY srcaddr 
   HAVING port_count > 10
   ```

2. **データ流出検出**:
   ```sql
   SELECT srcaddr, SUM(bytes) as total_bytes
   FROM flowlogs 
   WHERE action = 'ACCEPT' AND protocol = 6
   GROUP BY srcaddr
   HAVING total_bytes > 1000000000  -- 1GB以上
   ```

**分析基盤構成:**
```
VPC Flow Logs 
→ CloudWatch Logs 
→ Kinesis Data Firehose 
→ S3 (長期保存)
→ Amazon Athena (分析)
→ QuickSight (可視化)
```

**アラート設定:**
```json
{
  "MetricFilters": [{
    "filterName": "SecurityViolation",
    "filterPattern": "[version, account_id, interface_id, srcaddr != \"-\", dstaddr, srcport, dstport = \"22\" || dstport = \"3389\", protocol, packets, bytes, windowstart, windowend, action = \"REJECT\"]",
    "metricTransformations": [{
      "metricName": "SSHRDPRejections",
      "metricNamespace": "VPC/Security"
    }]
  }]
}
```

**コスト最適化:**
- S3 Intelligent Tiering使用
- 不要なフィールド除去でログサイズ削減
- ライフサイクルポリシーで自動削除

**他の選択肢が不適切な理由:**
- A: ACCEPTのみでは攻撃検出困難
- B: Subnetレベルは管理が複雑
- C: REJECTのみでは正常通信の異常検出不可
</details>

---

## 🔧 問題 8

AWS の Network Access Analyzer を使用して、意図しないネットワークアクセスを検出したい。最も効果的な使用方法は？

**A)** Security Groups の設定ミスのみチェック  
**B)** Network paths analysis with compliance requirements  
**C)** VPC Peering connections validation only  
**D)** Route table configuration verification

<details>
<summary>解答と解説</summary>

**正解: B**

**解説:**
**Network Access Analyzer**は包括的なネットワークパス分析とコンプライアンス要件検証に最適です。

**Network Access Analyzer機能:**
1. **経路分析**: 送信元から宛先までの全経路解析
2. **コンプライアンス検証**: セキュリティ要件との照合
3. **設定検証**: SG, NACL, Route Tableの総合判定
4. **意図しないアクセス検出**: 設定ミスや過剰権限の発見

**実装例:**
```bash
# ネットワークアクセススコープ作成
aws ec2 create-network-insights-access-scope \
  --cli-input-json '{
    "MatchPaths": [{
      "Source": {
        "ResourceStatement": {
          "Resources": ["subnet-12345678"],
          "ResourceTypes": ["AWS::EC2::Subnet"]
        }
      },
      "Destination": {
        "ResourceStatement": {
          "Resources": ["0.0.0.0/0"],
          "ResourceTypes": ["AWS::EC2::Internet"]
        }
      }
    }],
    "ExcludePaths": [{
      "Source": {
        "ResourceStatement": {
          "Resources": ["sg-authorized"],
          "ResourceTypes": ["AWS::EC2::SecurityGroup"]
        }
      }
    }]
  }'

# 分析実行
aws ec2 start-network-insights-access-scope-analysis \
  --network-insights-access-scope-id nis-scope-12345678
```

**コンプライアンス要件例:**
```json
{
  "ComplianceRequirements": {
    "NoDirectInternetAccess": {
      "Description": "データベースサブネットから直接インターネットアクセス禁止",
      "Source": "subnet-database-*",
      "Destination": "0.0.0.0/0",
      "ExpectedResult": "NO_ACCESS"
    },
    "ManagementAccessOnly": {
      "Description": "SSH/RDPアクセスは管理セグメントからのみ",
      "Source": "!subnet-management-*",
      "Destination": "*:22,*:3389",
      "ExpectedResult": "NO_ACCESS"
    }
  }
}
```

**検出可能な問題:**
- 意図しないパブリックアクセス
- 過度に緩いセキュリティグループ
- ルーティング設定ミス
- NACL設定の競合

**自動化と継続監視:**
```python
import boto3

def automated_compliance_check():
    ec2 = boto3.client('ec2')
    
    # 週次コンプライアンス検証
    response = ec2.start_network_insights_access_scope_analysis(
        NetworkInsightsAccessScopeId='nis-scope-compliance',
        DryRun=False
    )
    
    # 結果をCloudWatchメトリクスに送信
    cloudwatch = boto3.client('cloudwatch')
    cloudwatch.put_metric_data(
        Namespace='Network/Compliance',
        MetricData=[{
            'MetricName': 'ComplianceViolations',
            'Value': len(violations),
            'Unit': 'Count'
        }]
    )
```

**他の選択肢が不適切な理由:**
- A: SGチェックのみでは全体的な経路分析不可
- C: VPC Peeringのみは分析範囲が限定的
- D: Route Table検証のみでは不十分
</details>

---

## 🔧 問題 9

大規模環境での DNS クエリパフォーマンス最適化のため、Route 53 Resolver のカスタム設定が必要です。以下の要件があります：

- オンプレミス DNS との統合
- VPC 間でのDNS解決
- 条件付きフォワーディング
- DNS クエリログ

最適な構成は？

**A)** Default VPC DNS resolver のみ使用  
**B)** Route 53 Resolver Rules with Outbound Endpoints  
**C)** EC2-based DNS servers in each VPC  
**D)** AWS Directory Service DNS delegation

<details>
<summary>解答と解説</summary>

**正解: B**

**解説:**
複雑なDNS要件には**Route 53 Resolver Rules + Outbound Endpoints**が最適です。

**Route 53 Resolver 構成:**
```bash
# Outbound Endpoint作成
aws route53resolver create-resolver-endpoint \
  --creation-request-id $(uuidgen) \
  --name "onprem-dns-outbound" \
  --direction OUTBOUND \
  --ip-addresses SubnetId=subnet-12345678,Ip=10.0.1.10 \
  --security-group-ids sg-12345678

# Inbound Endpoint作成  
aws route53resolver create-resolver-endpoint \
  --creation-request-id $(uuidgen) \
  --name "vpc-dns-inbound" \
  --direction INBOUND \
  --ip-addresses SubnetId=subnet-87654321,Ip=10.0.2.10 \
  --security-group-ids sg-87654321
```

**条件付きフォワーディングルール:**
```bash
# オンプレミスドメイン向けルール
aws route53resolver create-resolver-rule \
  --creation-request-id $(uuidgen) \
  --name "onprem-forward-rule" \
  --rule-type FORWARD \
  --domain-name "corp.example.com" \
  --resolver-endpoint-id rslvr-out-12345678 \
  --target-ips Ip=192.168.1.10,Port=53

# VPC間共有ルール
aws route53resolver associate-resolver-rule \
  --resolver-rule-id rslvr-rr-12345678 \
  --vpc-id vpc-target-12345678
```

**DNSクエリログ設定:**
```bash
# Query Logging設定
aws route53resolver create-resolver-query-log-config \
  --name "dns-query-logs" \
  --destination-arn "arn:aws:s3:::dns-logs-bucket" \
  --creation-request-id $(uuidgen)

# VPCに関連付け
aws route53resolver associate-resolver-query-log-config \
  --resolver-query-log-config-id rqlc-12345678 \
  --resource-id vpc-12345678
```

**DNS解決フロー:**
```
1. VPC内クエリ → Route 53 Resolver
2. corp.example.com → Outbound Endpoint → オンプレミスDNS
3. aws.example.com → Route 53 Private Hosted Zone  
4. public domain → Route 53 Public DNS
```

**パフォーマンス最適化:**
- **リージョン内Endpoint**: レイテンシ最小化
- **キャッシュ設定**: TTL値の最適化
- **冗長性**: マルチAZ Endpoint配置

**セキュリティ設定:**
```json
{
  "SecurityGroupRules": [
    {
      "Type": "Outbound Endpoint",
      "Protocol": "UDP",
      "Port": 53,
      "Destination": "オンプレミスDNS CIDR"
    },
    {
      "Type": "Inbound Endpoint", 
      "Protocol": "UDP",
      "Port": 53,
      "Source": "VPC CIDR ranges"
    }
  ]
}
```

**コスト試算（月額）:**
- Outbound Endpoint: $4.5
- Inbound Endpoint: $4.5  
- DNS クエリ: $0.4/million queries
- 合計: ~$10-20/月

**他の選択肢が不適切な理由:**
- A: Default resolverは高度な機能なし
- C: EC2ベースは運用負荷が高い
- D: Directory Serviceは限定的なDNS機能
</details>

---

## 🔧 問題 10

ネットワークパフォーマンスの詳細分析のため、Enhanced networking と SR-IOV を活用したい。適切な設定は？

**A)** すべてのEC2インスタンスでEnhanced networking有効化  
**B)** Placement GroupsとEnhanced networking、instance typeの最適化  
**C)** Single Root I/O Virtualization のみ設定  
**D)** Default networking設定で十分

<details>
<summary>解答と解説</summary>

**正解: B**

**解説:**
高性能ネットワーキングには**Placement Groups + Enhanced Networking + 適切なInstance Type**の組み合わせが重要です。

**Enhanced Networking対応確認:**
```bash
# インスタンスの現在設定確認
aws ec2 describe-instance-attribute \
  --instance-id i-1234567890abcdef0 \
  --attribute sriovNetSupport

aws ec2 describe-instance-attribute \
  --instance-id i-1234567890abcdef0 \
  --attribute enaSupport
```

**最適なインスタンス設定:**
```bash
# Enhanced networking有効化
aws ec2 modify-instance-attribute \
  --instance-id i-1234567890abcdef0 \
  --ena-support

# SR-IOV有効化  
aws ec2 modify-instance-attribute \
  --instance-id i-1234567890abcdef0 \
  --sriov-net-support simple
```

**Placement Groups種類と用途:**
```
Cluster Placement Group:
- 用途: HPC、低レイテンシ通信
- 配置: 同一AZ内の近接配置
- 性能: 10Gbps+ network performance

Partition Placement Group:
- 用途: 分散システム、可用性重視
- 配置: 異なるハードウェア分散
- 性能: バランス型

Spread Placement Group:
- 用途: 小規模クリティカルアプリ
- 配置: 最大分散（7インスタンス/AZ）
- 性能: 可用性最優先
```

**実装例:**
```bash
# Cluster Placement Group作成
aws ec2 create-placement-group \
  --group-name hpc-cluster \
  --strategy cluster

# 高性能インスタンス起動
aws ec2 run-instances \
  --image-id ami-12345678 \
  --instance-type c5n.18xlarge \
  --placement "GroupName=hpc-cluster" \
  --ena-support \
  --sriov-net-support simple
```

**ネットワーク性能比較:**
```
Instance Type | Network Performance | Enhanced Support
c5n.18xlarge  | 100 Gbps           | ENA + SR-IOV
m5n.24xlarge  | 100 Gbps           | ENA + SR-IOV  
r5n.24xlarge  | 100 Gbps           | ENA + SR-IOV
c5.xlarge     | Up to 10 Gbps      | ENA only
t3.medium     | Up to 5 Gbps       | ENA only
```

**最適化チェック:**
```python
# パフォーマンステスト
import subprocess

def network_performance_test():
    # iperf3でスループットテスト
    result = subprocess.run([
        'iperf3', '-c', 'target-ip', 
        '-t', '60', '-P', '8', '-f', 'g'
    ], capture_output=True, text=True)
    
    # 結果解析
    throughput = extract_throughput(result.stdout)
    print(f"Network Throughput: {throughput} Gbps")
    
    # レイテンシテスト
    ping_result = subprocess.run([
        'ping', '-c', '100', 'target-ip'
    ], capture_output=True, text=True)
    
    latency = extract_latency(ping_result.stdout)
    print(f"Average Latency: {latency} ms")
```

**監視とアラート:**
```json
{
  "CloudWatchMetrics": [
    "NetworkIn", "NetworkOut", 
    "NetworkLatency", "NetworkPacketsIn", "NetworkPacketsOut"
  ],
  "Thresholds": {
    "NetworkUtilization": "> 80%",
    "Latency": "> 1ms"
  }
}
```

**他の選択肢が不適切な理由:**
- A: 全インスタンスで有効化は不要（コスト増）
- C: SR-IOVのみでは最適化不十分
- D: 高性能要件では不適切
</details>

---

## 📊 解答一覧

| 問題 | 正解 | Domain | 重要度 |
|------|------|--------|--------|
| 1 | B | Network Design | ⭐⭐⭐⭐ |
| 2 | C | Network Implementation | ⭐⭐⭐⭐ |
| 3 | B | Network Design | ⭐⭐⭐⭐ |
| 4 | B | Network Design | ⭐⭐⭐ |
| 5 | C | Network Management | ⭐⭐⭐⭐ |
| 6 | A | Network Implementation | ⭐⭐⭐ |
| 7 | D | Network Security | ⭐⭐⭐⭐ |
| 8 | B | Network Security | ⭐⭐⭐ |
| 9 | B | Network Management | ⭐⭐⭐ |
| 10 | B | Network Management | ⭐⭐ |

## 🎯 学習のポイント

### 高得点のコツ
1. **アーキテクチャパターン**: 各サービスの適用場面を正確に理解
2. **セキュリティ設計**: 多層防御の原則を常に適用
3. **パフォーマンス最適化**: 帯域幅とレイテンシの要件分析
4. **コスト最適化**: サービス選択時のコスト影響を考慮

### 復習すべき領域
- **70%未満の場合**: ネットワーキング基礎から再学習
- **70-85%の場合**: 実装詳細と最適化手法を重点的に
- **85%以上の場合**: Domain 2の学習へ進む

### 次のステップ
Domain 1で8割以上正解できたら、**Domain 2: Network Implementation** の問題集に進んでください。

---

**注意**: この問題集はANS-C01試験の出題傾向を基に作成されており、実際の試験問題とは異なります。AWS公式の練習問題も併用することを推奨します。