# Lab 1: SageMaker 基礎とデータ準備

## 🎯 学習目標

このラボでは、AWS SageMaker の基本操作とデータ準備のベストプラクティスを実践的に学習します。

**習得スキル**:
- SageMaker Studio の操作
- Feature Store の構築と活用
- データ前処理パイプラインの実装
- S3 との連携

**所要時間**: 4-6時間  
**推定コスト**: $15-25

## 📋 前提条件

### 必要な権限
```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "sagemaker:*",
                "s3:GetObject",
                "s3:PutObject",
                "s3:DeleteObject",
                "s3:ListBucket",
                "iam:ListRoles",
                "iam:PassRole"
            ],
            "Resource": "*"
        }
    ]
}
```

### 事前準備
```bash
# Python ライブラリインストール
pip install sagemaker pandas scikit-learn matplotlib seaborn

# AWS CLI 設定確認
aws sts get-caller-identity
```

## Phase 1: SageMaker Studio 環境セットアップ

### 1.1 SageMaker Studio ドメイン作成

```bash
#!/bin/bash
# スクリプト: setup-sagemaker-studio.sh

set -e

echo "=== SageMaker Studio セットアップ開始 ==="

# 変数定義
REGION="ap-northeast-1"
DOMAIN_NAME="ml-engineer-lab-domain"
EXECUTION_ROLE_NAME="SageMaker-ExecutionRole"

# IAM ロール作成
echo "1. IAM ロール作成中..."

# 信頼ポリシー作成
cat > trust-policy.json << 'EOF'
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Principal": {
                "Service": "sagemaker.amazonaws.com"
            },
            "Action": "sts:AssumeRole"
        }
    ]
}
EOF

# IAM ロール作成
ROLE_ARN=$(aws iam create-role \
    --role-name $EXECUTION_ROLE_NAME \
    --assume-role-policy-document file://trust-policy.json \
    --query 'Role.Arn' \
    --output text 2>/dev/null || \
    aws iam get-role --role-name $EXECUTION_ROLE_NAME --query 'Role.Arn' --output text)

echo "   IAM ロール: $ROLE_ARN"

# 必要なポリシーをアタッチ
aws iam attach-role-policy \
    --role-name $EXECUTION_ROLE_NAME \
    --policy-arn arn:aws:iam::aws:policy/AmazonSageMakerFullAccess

aws iam attach-role-policy \
    --role-name $EXECUTION_ROLE_NAME \
    --policy-arn arn:aws:iam::aws:policy/AmazonS3FullAccess

# カスタムポリシー作成
cat > custom-policy.json << 'EOF'
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "logs:CreateLogGroup",
                "logs:CreateLogStream",
                "logs:PutLogEvents"
            ],
            "Resource": "*"
        },
        {
            "Effect": "Allow",
            "Action": [
                "ecr:GetAuthorizationToken",
                "ecr:BatchCheckLayerAvailability",
                "ecr:GetDownloadUrlForLayer",
                "ecr:BatchGetImage"
            ],
            "Resource": "*"
        }
    ]
}
EOF

aws iam put-role-policy \
    --role-name $EXECUTION_ROLE_NAME \
    --policy-name "SageMakerCustomPolicy" \
    --policy-document file://custom-policy.json

echo "   IAM ポリシー設定完了"

# デフォルト VPC 取得
echo "2. ネットワーク設定取得中..."
VPC_ID=$(aws ec2 describe-vpcs \
    --filters "Name=is-default,Values=true" \
    --query 'Vpcs[0].VpcId' \
    --output text \
    --region $REGION)

SUBNET_IDS=$(aws ec2 describe-subnets \
    --filters "Name=vpc-id,Values=$VPC_ID" \
    --query 'Subnets[*].SubnetId' \
    --output text \
    --region $REGION | tr '\t' ',')

echo "   VPC ID: $VPC_ID"
echo "   Subnet IDs: $SUBNET_IDS"

# SageMaker Studio ドメイン作成
echo "3. SageMaker Studio ドメイン作成中..."

DOMAIN_ID=$(aws sagemaker create-domain \
    --domain-name $DOMAIN_NAME \
    --auth-mode IAM \
    --default-user-settings '{
        "ExecutionRole": "'$ROLE_ARN'",
        "SecurityGroups": [],
        "SharingSettings": {
            "NotebookOutputOption": "Disabled"
        }
    }' \
    --subnet-ids $(echo $SUBNET_IDS | tr ',' ' ') \
    --vpc-id $VPC_ID \
    --region $REGION \
    --query 'DomainArn' \
    --output text 2>/dev/null || echo "EXISTS")

if [ "$DOMAIN_ID" = "EXISTS" ]; then
    echo "   SageMaker Studio ドメインは既に存在します"
    DOMAIN_ID=$(aws sagemaker list-domains \
        --query 'Domains[0].DomainId' \
        --output text \
        --region $REGION)
else
    # ドメイン ID の抽出
    DOMAIN_ID=$(echo $DOMAIN_ID | sed 's/.*domain\///')
    echo "   SageMaker Studio ドメイン作成完了: $DOMAIN_ID"
    
    echo "   ドメインが利用可能になるまで待機中..."
    aws sagemaker wait domain-in-service \
        --domain-id $DOMAIN_ID \
        --region $REGION
fi

# ユーザープロファイル作成
echo "4. ユーザープロファイル作成中..."
USER_PROFILE_NAME="ml-engineer-user"

aws sagemaker create-user-profile \
    --domain-id $DOMAIN_ID \
    --user-profile-name $USER_PROFILE_NAME \
    --user-settings '{
        "ExecutionRole": "'$ROLE_ARN'"
    }' \
    --region $REGION 2>/dev/null || echo "   ユーザープロファイルは既に存在します"

echo "   ユーザープロファイル作成完了: $USER_PROFILE_NAME"

# 設定情報保存
cat > sagemaker-config.json << EOF
{
    "region": "$REGION",
    "domain_id": "$DOMAIN_ID",
    "user_profile_name": "$USER_PROFILE_NAME",
    "execution_role_arn": "$ROLE_ARN",
    "vpc_id": "$VPC_ID"
}
EOF

echo "=== SageMaker Studio セットアップ完了 ==="
echo "設定情報が sagemaker-config.json に保存されました"
echo ""
echo "SageMaker Studio へのアクセス:"
echo "1. AWS Console > SageMaker > Studio"
echo "2. ドメイン: $DOMAIN_ID"
echo "3. ユーザー: $USER_PROFILE_NAME でログイン"
echo ""
echo "推定セットアップ時間: 10-15分"
echo "推定月額コスト: ドメイン維持費 $0 (使用時のみ課金)"
```

### 1.2 S3 バケット準備

```python
#!/usr/bin/env python3
"""
S3 バケットとサンプルデータの準備
"""

import boto3
import pandas as pd
import numpy as np
import json
from datetime import datetime, timedelta
import os

class S3DataPreparation:
    def __init__(self, region='ap-northeast-1'):
        self.region = region
        self.s3 = boto3.client('s3', region_name=region)
        self.bucket_name = f"sagemaker-lab-{boto3.session.Session().region_name}-{boto3.sts.StsClient().get_caller_identity()['Account']}"
        
    def create_bucket(self):
        """S3バケット作成"""
        print("1. S3バケット作成中...")
        
        try:
            if self.region == 'us-east-1':
                self.s3.create_bucket(Bucket=self.bucket_name)
            else:
                self.s3.create_bucket(
                    Bucket=self.bucket_name,
                    CreateBucketConfiguration={'LocationConstraint': self.region}
                )
            print(f"   S3バケット作成完了: {self.bucket_name}")
        except self.s3.exceptions.BucketAlreadyOwnedByYou:
            print(f"   S3バケットは既に存在します: {self.bucket_name}")
        except Exception as e:
            print(f"   エラー: S3バケット作成失敗 - {str(e)}")
            return False
            
        # バケットポリシー設定（SageMaker アクセス用）
        bucket_policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": {
                        "Service": "sagemaker.amazonaws.com"
                    },
                    "Action": [
                        "s3:GetObject",
                        "s3:PutObject",
                        "s3:DeleteObject",
                        "s3:ListBucket"
                    ],
                    "Resource": [
                        f"arn:aws:s3:::{self.bucket_name}",
                        f"arn:aws:s3:::{self.bucket_name}/*"
                    ]
                }
            ]
        }
        
        try:
            self.s3.put_bucket_policy(
                Bucket=self.bucket_name,
                Policy=json.dumps(bucket_policy)
            )
            print("   バケットポリシー設定完了")
        except Exception as e:
            print(f"   警告: バケットポリシー設定失敗 - {str(e)}")
            
        return True
    
    def generate_sample_data(self):
        """サンプルデータ生成"""
        print("2. サンプルデータ生成中...")
        
        # 顧客データ生成
        np.random.seed(42)
        n_customers = 10000
        
        customers = pd.DataFrame({
            'customer_id': range(1, n_customers + 1),
            'age': np.random.normal(35, 12, n_customers).astype(int),
            'income': np.random.lognormal(10.5, 0.5, n_customers).astype(int),
            'credit_score': np.random.normal(650, 100, n_customers).astype(int),
            'account_balance': np.random.exponential(5000, n_customers),
            'years_with_bank': np.random.exponential(3, n_customers),
            'num_products': np.random.poisson(2, n_customers) + 1,
            'has_cr_card': np.random.choice([0, 1], n_customers, p=[0.3, 0.7]),
            'is_active_member': np.random.choice([0, 1], n_customers, p=[0.2, 0.8]),
            'geography': np.random.choice(['France', 'Germany', 'Spain'], n_customers, p=[0.5, 0.25, 0.25])
        })
        
        # クレジットカード退会予測のターゲット変数
        # ロジスティック回帰的な関係性を作成
        logit = (
            -2.0 + 
            -0.01 * customers['age'] +
            -0.00001 * customers['income'] +
            -0.005 * customers['credit_score'] +
            -0.0001 * customers['account_balance'] +
            -0.3 * customers['years_with_bank'] +
            -0.2 * customers['num_products'] +
            -0.5 * customers['has_cr_card'] +
            -1.0 * customers['is_active_member'] +
            0.2 * (customers['geography'] == 'Germany').astype(int)
        )
        
        probability = 1 / (1 + np.exp(-logit))
        customers['churned'] = np.random.binomial(1, probability, n_customers)
        
        print(f"   顧客データ生成完了: {len(customers):,} 件")
        print(f"   解約率: {customers['churned'].mean():.2%}")
        
        return customers
    
    def generate_time_series_data(self):
        """時系列データ生成（商品売上予測用）"""
        print("3. 時系列データ生成中...")
        
        # 2年間の日次データ
        start_date = datetime.now() - timedelta(days=730)
        dates = [start_date + timedelta(days=x) for x in range(730)]
        
        # 複数商品の売上データ
        products = ['Product_A', 'Product_B', 'Product_C', 'Product_D', 'Product_E']
        
        sales_data = []
        for product in products:
            # 商品ごとに異なるトレンドと季節性
            base_sales = np.random.normal(1000, 200, 730)
            
            # トレンド（線形 + ノイズ）
            trend = np.linspace(0, 300, 730) + np.random.normal(0, 50, 730)
            
            # 季節性（年次 + 週次）
            days_from_start = np.arange(730)
            yearly_seasonal = 200 * np.sin(2 * np.pi * days_from_start / 365)
            weekly_seasonal = 50 * np.sin(2 * np.pi * days_from_start / 7)
            
            # 特別イベント（ブラックフライデー、年末年始など）
            event_boost = np.zeros(730)
            for i, date in enumerate(dates):
                if date.month == 11 and date.day >= 25:  # ブラックフライデー期間
                    event_boost[i] = 500
                elif date.month == 12 and date.day >= 20:  # 年末商戦
                    event_boost[i] = 300
                elif date.month == 1 and date.day <= 5:   # 新年セール
                    event_boost[i] = 200
            
            # 最終売上計算
            sales = np.maximum(0, base_sales + trend + yearly_seasonal + weekly_seasonal + event_boost)
            
            for i, (date, sale) in enumerate(zip(dates, sales)):
                sales_data.append({
                    'date': date.strftime('%Y-%m-%d'),
                    'product': product,
                    'sales': int(sale),
                    'day_of_week': date.weekday(),
                    'month': date.month,
                    'is_weekend': 1 if date.weekday() >= 5 else 0,
                    'is_holiday': 1 if (date.month == 12 and date.day >= 24) or (date.month == 1 and date.day <= 2) else 0
                })
        
        sales_df = pd.DataFrame(sales_data)
        print(f"   売上データ生成完了: {len(sales_df):,} 件")
        
        return sales_df
    
    def upload_datasets(self, customers_df, sales_df):
        """データセットをS3にアップロード"""
        print("4. データセットS3アップロード中...")
        
        # 顧客データのアップロード
        customers_csv = customers_df.to_csv(index=False)
        self.s3.put_object(
            Bucket=self.bucket_name,
            Key='datasets/customers/customer_churn.csv',
            Body=customers_csv
        )
        
        # 訓練・テスト分割版もアップロード
        train_customers = customers_df.sample(frac=0.8, random_state=42)
        test_customers = customers_df.drop(train_customers.index)
        
        self.s3.put_object(
            Bucket=self.bucket_name,
            Key='datasets/customers/train/customer_churn_train.csv',
            Body=train_customers.to_csv(index=False)
        )
        
        self.s3.put_object(
            Bucket=self.bucket_name,
            Key='datasets/customers/test/customer_churn_test.csv',
            Body=test_customers.to_csv(index=False)
        )
        
        # 売上データのアップロード
        sales_csv = sales_df.to_csv(index=False)
        self.s3.put_object(
            Bucket=self.bucket_name,
            Key='datasets/sales/sales_forecast.csv',
            Body=sales_csv
        )
        
        # 時系列分割版
        train_sales = sales_df[sales_df['date'] < '2024-06-01']
        test_sales = sales_df[sales_df['date'] >= '2024-06-01']
        
        self.s3.put_object(
            Bucket=self.bucket_name,
            Key='datasets/sales/train/sales_train.csv',
            Body=train_sales.to_csv(index=False)
        )
        
        self.s3.put_object(
            Bucket=self.bucket_name,
            Key='datasets/sales/test/sales_test.csv',
            Body=test_sales.to_csv(index=False)
        )
        
        print("   データセットアップロード完了")
        print(f"   - 顧客データ: {len(customers_df):,} 件")
        print(f"   - 売上データ: {len(sales_df):,} 件")
        
        # データカタログ作成
        catalog = {
            "datasets": {
                "customer_churn": {
                    "description": "銀行顧客の退会予測データセット",
                    "path": f"s3://{self.bucket_name}/datasets/customers/",
                    "target": "churned",
                    "features": list(customers_df.columns[:-1]),
                    "task_type": "binary_classification",
                    "rows": len(customers_df)
                },
                "sales_forecast": {
                    "description": "商品売上予測用時系列データ",
                    "path": f"s3://{self.bucket_name}/datasets/sales/",
                    "target": "sales",
                    "features": ["product", "day_of_week", "month", "is_weekend", "is_holiday"],
                    "task_type": "regression",
                    "rows": len(sales_df)
                }
            },
            "bucket_name": self.bucket_name,
            "region": self.region,
            "created_at": datetime.now().isoformat()
        }
        
        # カタログをS3に保存
        self.s3.put_object(
            Bucket=self.bucket_name,
            Key='metadata/data_catalog.json',
            Body=json.dumps(catalog, indent=2)
        )
        
        # ローカルにも保存
        with open('data_catalog.json', 'w') as f:
            json.dump(catalog, f, indent=2)
        
        print("   データカタログ作成完了")
        return catalog
    
    def run_setup(self):
        """完全なデータ準備セットアップ"""
        print("=== S3 データ準備セットアップ開始 ===")
        
        # S3バケット作成
        if not self.create_bucket():
            return False
        
        # サンプルデータ生成
        customers_df = self.generate_sample_data()
        sales_df = self.generate_time_series_data()
        
        # データアップロード
        catalog = self.upload_datasets(customers_df, sales_df)
        
        print("=== S3 データ準備完了 ===")
        print(f"S3バケット: {self.bucket_name}")
        print("推定実行時間: 5-10分")
        print("推定コスト: $0.10-0.50 (データストレージ費用)")
        
        return True

if __name__ == "__main__":
    data_prep = S3DataPreparation()
    success = data_prep.run_setup()
    
    if success:
        print("\nデータ準備が完了しました。")
        print("次のステップ: SageMaker Studio でデータ探索を開始してください。")
    else:
        print("\nデータ準備中にエラーが発生しました。")
```

## Phase 2: データ探索と Feature Store 構築

### 2.1 SageMaker Studio でのデータ探索

SageMaker Studio で以下のJupyterノートブックを作成します：

```python
# ノートブック: data_exploration.ipynb

import sagemaker
import boto3
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sagemaker.feature_store.feature_group import FeatureGroup
from sagemaker.feature_store.feature_definition import FeatureDefinition, FeatureTypeEnum
import json
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# SageMaker セッション初期化
sagemaker_session = sagemaker.Session()
role = sagemaker.get_execution_role()
region = sagemaker_session.boto_region_name
s3_client = boto3.client('s3')

print(f"SageMaker Role: {role}")
print(f"Region: {region}")

# データカタログ読み込み
with open('data_catalog.json', 'r') as f:
    catalog = json.load(f)

bucket_name = catalog['bucket_name']
print(f"S3 Bucket: {bucket_name}")
```

```python
# セクション 1: 顧客データの探索

# データ読み込み
customers_df = pd.read_csv(f's3://{bucket_name}/datasets/customers/customer_churn.csv')

print("=== 顧客データ概要 ===")
print(f"データ形状: {customers_df.shape}")
print(f"解約率: {customers_df['churned'].mean():.2%}")
print()

# 基本統計
print("=== 基本統計量 ===")
print(customers_df.describe())
print()

# データ品質チェック
print("=== データ品質チェック ===")
print("欠損値:")
print(customers_df.isnull().sum())
print()

print("重複データ:")
print(f"重複行数: {customers_df.duplicated().sum()}")
print()

# カテゴリカル変数の分布
print("=== カテゴリカル変数の分布 ===")
categorical_cols = ['geography', 'has_cr_card', 'is_active_member', 'churned']
for col in categorical_cols:
    print(f"\n{col}:")
    print(customers_df[col].value_counts())
```

```python
# セクション 2: 可視化によるデータ理解

# 図のサイズ設定
plt.style.use('seaborn-v0_8')
fig, axes = plt.subplots(2, 3, figsize=(18, 12))

# 年齢分布
axes[0, 0].hist(customers_df['age'], bins=30, alpha=0.7, color='skyblue')
axes[0, 0].set_title('年齢分布')
axes[0, 0].set_xlabel('年齢')
axes[0, 0].set_ylabel('頻度')

# 収入分布（対数スケール）
axes[0, 1].hist(np.log10(customers_df['income']), bins=30, alpha=0.7, color='lightgreen')
axes[0, 1].set_title('収入分布（log10）')
axes[0, 1].set_xlabel('log10(収入)')
axes[0, 1].set_ylabel('頻度')

# クレジットスコア分布
axes[0, 2].hist(customers_df['credit_score'], bins=30, alpha=0.7, color='orange')
axes[0, 2].set_title('クレジットスコア分布')
axes[0, 2].set_xlabel('クレジットスコア')
axes[0, 2].set_ylabel('頻度')

# 地域別解約率
churn_by_geo = customers_df.groupby('geography')['churned'].mean()
axes[1, 0].bar(churn_by_geo.index, churn_by_geo.values, color='lightcoral')
axes[1, 0].set_title('地域別解約率')
axes[1, 0].set_xlabel('地域')
axes[1, 0].set_ylabel('解約率')
axes[1, 0].tick_params(axis='x', rotation=45)

# アクティブメンバー別解約率
churn_by_active = customers_df.groupby('is_active_member')['churned'].mean()
axes[1, 1].bar(['非アクティブ', 'アクティブ'], churn_by_active.values, color='gold')
axes[1, 1].set_title('アクティブメンバー別解約率')
axes[1, 1].set_xlabel('アクティブ状態')
axes[1, 1].set_ylabel('解約率')

# 商品数別解約率
churn_by_products = customers_df.groupby('num_products')['churned'].mean()
axes[1, 2].bar(churn_by_products.index, churn_by_products.values, color='mediumpurple')
axes[1, 2].set_title('商品数別解約率')
axes[1, 2].set_xlabel('保有商品数')
axes[1, 2].set_ylabel('解約率')

plt.tight_layout()
plt.show()
```

```python
# セクション 3: 相関分析

# 数値変数の相関行列
numeric_cols = ['age', 'income', 'credit_score', 'account_balance', 'years_with_bank', 'num_products']
correlation_matrix = customers_df[numeric_cols + ['churned']].corr()

plt.figure(figsize=(10, 8))
sns.heatmap(correlation_matrix, annot=True, cmap='coolwarm', center=0, 
            square=True, linewidths=0.5)
plt.title('特徴量とターゲット変数の相関行列')
plt.tight_layout()
plt.show()

# 解約に最も影響する要因
churn_correlation = correlation_matrix['churned'].drop('churned').sort_values(key=abs, ascending=False)
print("=== 解約との相関が高い特徴量 ===")
for feature, corr in churn_correlation.items():
    print(f"{feature}: {corr:.3f}")
```

### 2.2 Feature Store の構築

```python
# セクション 4: Feature Store 構築

def create_feature_group(df, feature_group_name, record_identifier, event_time_feature):
    """
    Feature Group を作成する関数
    """
    
    # Feature Definition の作成
    feature_definitions = []
    
    for column in df.columns:
        if column in [record_identifier, event_time_feature]:
            feature_type = FeatureTypeEnum.STRING
        elif df[column].dtype == 'object':
            feature_type = FeatureTypeEnum.STRING
        elif df[column].dtype in ['int64', 'int32']:
            feature_type = FeatureTypeEnum.INTEGRAL
        else:
            feature_type = FeatureTypeEnum.FRACTIONAL
        
        feature_definitions.append(
            FeatureDefinition(
                feature_name=column, 
                feature_type=feature_type
            )
        )
    
    # Feature Group の設定
    feature_group = FeatureGroup(
        name=feature_group_name,
        sagemaker_session=sagemaker_session
    )
    
    return feature_group, feature_definitions

# 顧客特徴量用の Feature Group 作成
print("=== Feature Store セットアップ ===")

# イベント時間の追加（現在時刻）
customers_with_time = customers_df.copy()
customers_with_time['event_time'] = datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ')
customers_with_time['customer_id'] = customers_with_time['customer_id'].astype(str)

# Feature Group 作成
customer_feature_group, customer_feature_definitions = create_feature_group(
    customers_with_time,
    'customer-features-lab1',
    'customer_id',
    'event_time'
)

print(f"Feature Group名: customer-features-lab1")
print(f"特徴量数: {len(customer_feature_definitions)}")
```

```python
# Feature Group の実際の作成と設定

try:
    customer_feature_group.create(
        s3_uri=f's3://{bucket_name}/feature-store/customer-features',
        record_identifier_name='customer_id',
        event_time_feature_name='event_time',
        role_arn=role,
        enable_online_store=True,
        feature_definitions=customer_feature_definitions,
        description='顧客の基本情報と行動データ'
    )
    
    print("Feature Group 作成要求送信完了")
    print("作成完了まで約10-15分かかります...")
    
except Exception as e:
    print(f"Feature Group 作成エラー: {str(e)}")
    if "already exists" in str(e):
        print("Feature Group は既に存在します")

# 作成状況の確認
import time

def wait_for_feature_group_creation(feature_group, max_wait_time=900):
    """Feature Group の作成完了を待機"""
    start_time = time.time()
    
    while time.time() - start_time < max_wait_time:
        try:
            status = feature_group.describe()['FeatureGroupStatus']
            print(f"Feature Group ステータス: {status}")
            
            if status == 'Created':
                print("✅ Feature Group 作成完了!")
                return True
            elif status == 'CreateFailed':
                print("❌ Feature Group 作成失敗")
                return False
                
        except Exception as e:
            print(f"ステータス確認エラー: {str(e)}")
        
        print("待機中... (30秒後に再確認)")
        time.sleep(30)
    
    print("⏰ タイムアウト: Feature Group 作成に時間がかかっています")
    return False

# 作成完了待機（バックグラウンドで実行される場合はスキップ可能）
print("Feature Group 作成状況を確認します...")
creation_success = wait_for_feature_group_creation(customer_feature_group)
```

```python
# セクション 5: データの取り込み

if creation_success:
    print("=== Feature Store データ取り込み ===")
    
    # バッチでのデータ取り込み
    batch_size = 1000
    total_rows = len(customers_with_time)
    
    for i in range(0, total_rows, batch_size):
        batch_df = customers_with_time.iloc[i:i+batch_size]
        
        try:
            customer_feature_group.ingest(
                data_frame=batch_df,
                max_workers=3,
                wait=True
            )
            
            print(f"バッチ {i//batch_size + 1}/{(total_rows + batch_size - 1)//batch_size} 完了 "
                  f"({len(batch_df)} 件)")
            
        except Exception as e:
            print(f"バッチ {i//batch_size + 1} でエラー: {str(e)}")
            break
    
    print("✅ 全データの取り込み完了!")
    
else:
    print("⚠️ Feature Group の作成が完了していないため、データ取り込みをスキップします")
    print("Feature Group 作成完了後に、再度データ取り込みを実行してください")
```

### 2.3 Feature Store からのデータ取得

```python
# セクション 6: Feature Store からのデータ取得テスト

from sagemaker.feature_store.feature_store import FeatureStore

def test_feature_store_queries():
    """Feature Store のクエリ機能テスト"""
    
    print("=== Feature Store クエリテスト ===")
    
    # Athena クエリによるオフラインストア検索
    feature_store = FeatureStore(sagemaker_session=sagemaker_session)
    
    try:
        # テーブル名取得
        athena_query = f"""
        SELECT customer_id, age, income, credit_score, churned, event_time
        FROM "sagemaker_featurestore"."customer_features_lab1_{int(time.time())}"
        WHERE age > 40 AND income > 50000
        LIMIT 10
        """
        
        print("Athena クエリ実行中...")
        query_results = feature_store.athena_query(
            query=athena_query,
            output_location=f's3://{bucket_name}/athena-results/'
        )
        
        print("✅ Athena クエリ成功")
        print("結果のサンプル:")
        print(query_results.head())
        
    except Exception as e:
        print(f"⚠️ Athena クエリエラー: {str(e)}")
        print("オフラインストアの準備に時間がかかることがあります")
    
    # オンラインストアからのリアルタイム取得テスト
    try:
        print("\n=== オンラインストア取得テスト ===")
        
        # 特定の顧客データを取得
        test_customer_id = "1"
        
        online_response = customer_feature_group.get_record(
            record_identifier_value_as_string=test_customer_id
        )
        
        print(f"✅ 顧客ID {test_customer_id} のデータ取得成功:")
        for record in online_response.record:
            print(f"  {record.feature_name}: {record.value_as_string}")
            
    except Exception as e:
        print(f"⚠️ オンラインストア取得エラー: {str(e)}")
        print("オンラインストアの同期に時間がかかることがあります")

# テスト実行
if creation_success:
    test_feature_store_queries()
else:
    print("Feature Group の作成が完了してからテストを実行してください")
```

## Phase 3: データ前処理パイプライン

### 3.1 SageMaker Processing による前処理

```python
# セクション 7: SageMaker Processing ジョブ

from sagemaker.processing import ProcessingInput, ProcessingOutput
from sagemaker.sklearn.processing import SKLearnProcessor
import os

# 前処理スクリプトの作成
preprocessing_script = """
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler, LabelEncoder, OneHotEncoder
from sklearn.model_selection import train_test_split
import argparse
import joblib
import os

def preprocess_data(input_path, output_path):
    '''データ前処理メイン関数'''
    
    print("=== データ前処理開始 ===")
    
    # データ読み込み
    df = pd.read_csv(os.path.join(input_path, 'customer_churn.csv'))
    print(f"元データ形状: {df.shape}")
    
    # 特徴量エンジニアリング
    print("特徴量エンジニアリング実行中...")
    
    # 1. 新しい特徴量の作成
    df['balance_per_product'] = df['account_balance'] / (df['num_products'] + 1)
    df['age_group'] = pd.cut(df['age'], bins=[0, 30, 40, 50, 60, 100], 
                            labels=['<30', '30-40', '40-50', '50-60', '60+'])
    df['income_category'] = pd.cut(df['income'], 
                                 bins=[0, 30000, 50000, 80000, 150000, float('inf')],
                                 labels=['Low', 'Medium', 'High', 'Very High', 'Premium'])
    
    # 2. カテゴリカル変数のエンコーディング
    # One-hot encoding for geography
    geography_encoded = pd.get_dummies(df['geography'], prefix='geo')
    df = pd.concat([df, geography_encoded], axis=1)
    df.drop('geography', axis=1, inplace=True)
    
    # Age group encoding
    age_group_encoded = pd.get_dummies(df['age_group'], prefix='age_group')
    df = pd.concat([df, age_group_encoded], axis=1)
    df.drop('age_group', axis=1, inplace=True)
    
    # Income category encoding
    income_cat_encoded = pd.get_dummies(df['income_category'], prefix='income_cat')
    df = pd.concat([df, income_cat_encoded], axis=1)
    df.drop('income_category', axis=1, inplace=True)
    
    # 3. 数値特徴量の正規化
    numeric_features = ['age', 'income', 'credit_score', 'account_balance', 
                       'years_with_bank', 'balance_per_product']
    
    scaler = StandardScaler()
    df[numeric_features] = scaler.fit_transform(df[numeric_features])
    
    # 4. 特徴量とターゲットの分離
    X = df.drop(['customer_id', 'churned'], axis=1)
    y = df['churned']
    
    # 5. 訓練・検証・テストセット分割
    X_temp, X_test, y_temp, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    
    X_train, X_val, y_train, y_val = train_test_split(
        X_temp, y_temp, test_size=0.25, random_state=42, stratify=y_temp
    )
    
    print(f"訓練セット: {X_train.shape[0]} 件")
    print(f"検証セット: {X_val.shape[0]} 件") 
    print(f"テストセット: {X_test.shape[0]} 件")
    
    # 6. データ保存
    os.makedirs(output_path, exist_ok=True)
    
    # 訓練データ
    train_data = pd.concat([X_train, y_train], axis=1)
    train_data.to_csv(os.path.join(output_path, 'train.csv'), index=False)
    
    # 検証データ
    val_data = pd.concat([X_val, y_val], axis=1)
    val_data.to_csv(os.path.join(output_path, 'validation.csv'), index=False)
    
    # テストデータ
    test_data = pd.concat([X_test, y_test], axis=1)
    test_data.to_csv(os.path.join(output_path, 'test.csv'), index=False)
    
    # スケーラーの保存
    joblib.dump(scaler, os.path.join(output_path, 'scaler.pkl'))
    
    # 特徴量名の保存
    feature_names = list(X.columns)
    with open(os.path.join(output_path, 'feature_names.txt'), 'w') as f:
        for name in feature_names:
            f.write(f"{name}\\n")
    
    print("=== データ前処理完了 ===")
    print(f"特徴量数: {len(feature_names)}")
    print("保存ファイル:")
    print("- train.csv: 訓練データ")
    print("- validation.csv: 検証データ") 
    print("- test.csv: テストデータ")
    print("- scaler.pkl: 標準化スケーラー")
    print("- feature_names.txt: 特徴量名リスト")

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--input-path', type=str, default='/opt/ml/processing/input')
    parser.add_argument('--output-path', type=str, default='/opt/ml/processing/output')
    
    args = parser.parse_args()
    preprocess_data(args.input_path, args.output_path)
"""

# スクリプトファイル保存
with open('preprocessing.py', 'w') as f:
    f.write(preprocessing_script)

print("前処理スクリプト作成完了")
```

```python
# SageMaker Processing ジョブの実行

# SKLearn Processor の設定
sklearn_processor = SKLearnProcessor(
    framework_version='1.0-1',
    instance_type='ml.m5.xlarge',
    instance_count=1,
    base_job_name='customer-churn-preprocessing',
    role=role,
    sagemaker_session=sagemaker_session
)

print("=== SageMaker Processing ジョブ実行 ===")

# Processing ジョブ実行
try:
    sklearn_processor.run(
        code='preprocessing.py',
        inputs=[
            ProcessingInput(
                source=f's3://{bucket_name}/datasets/customers/',
                destination='/opt/ml/processing/input',
                input_name='customer-data'
            )
        ],
        outputs=[
            ProcessingOutput(
                source='/opt/ml/processing/output',
                destination=f's3://{bucket_name}/processed-data/customer-churn/',
                output_name='processed-data'
            )
        ],
        arguments=[
            '--input-path', '/opt/ml/processing/input',
            '--output-path', '/opt/ml/processing/output'
        ]
    )
    
    print("✅ Processing ジョブ送信完了")
    print(f"ジョブ名: {sklearn_processor.latest_job.job_name}")
    print("処理完了まで約10-15分かかります...")
    
except Exception as e:
    print(f"❌ Processing ジョブエラー: {str(e)}")
```

## 📊 ラボの検証とまとめ

### 検証手順

```python
# セクション 8: ラボ結果の検証

def verify_lab_completion():
    """ラボ完了の検証"""
    
    print("=== Lab 1 完了検証 ===")
    
    verification_results = {
        's3_bucket': False,
        'sample_data': False,
        'feature_store': False,
        'processing_job': False
    }
    
    # 1. S3バケットとデータの確認
    try:
        response = s3_client.list_objects_v2(Bucket=bucket_name, Prefix='datasets/')
        if response.get('Contents'):
            verification_results['s3_bucket'] = True
            verification_results['sample_data'] = True
            print("✅ S3バケットとサンプルデータ: 正常")
        else:
            print("❌ S3データが見つかりません")
    except Exception as e:
        print(f"❌ S3確認エラー: {str(e)}")
    
    # 2. Feature Store の確認
    try:
        feature_group_status = customer_feature_group.describe()
        if feature_group_status['FeatureGroupStatus'] == 'Created':
            verification_results['feature_store'] = True
            print("✅ Feature Store: 正常")
        else:
            print(f"⚠️ Feature Store ステータス: {feature_group_status['FeatureGroupStatus']}")
    except Exception as e:
        print(f"❌ Feature Store確認エラー: {str(e)}")
    
    # 3. Processing ジョブの確認
    try:
        processing_job_name = sklearn_processor.latest_job.job_name
        processing_status = sklearn_processor.latest_job.describe()
        
        if processing_status['ProcessingJobStatus'] == 'Completed':
            verification_results['processing_job'] = True
            print("✅ Processing ジョブ: 完了")
        else:
            print(f"⚠️ Processing ジョブ ステータス: {processing_status['ProcessingJobStatus']}")
    except Exception as e:
        print(f"❌ Processing ジョブ確認エラー: {str(e)}")
    
    # 結果サマリー
    completed_tasks = sum(verification_results.values())
    total_tasks = len(verification_results)
    
    print(f"\n=== 完了状況: {completed_tasks}/{total_tasks} ===")
    
    if completed_tasks == total_tasks:
        print("🎉 Lab 1 完全完了!")
        print("次のステップ: Lab 2 - モデル開発に進んでください")
    else:
        print("⚠️ 一部のタスクが未完了です")
        print("未完了のタスクを確認して再実行してください")
    
    return verification_results

# 検証実行
verification_results = verify_lab_completion()
```

### コスト サマリー

```python
# セクション 9: コストサマリーと次のステップ

def generate_cost_summary():
    """コスト概算の表示"""
    
    print("=== Lab 1 コストサマリー ===")
    
    costs = {
        'SageMaker Studio': '$0 (使用時のみ課金)',
        'S3 ストレージ': '$0.10-0.50 (データサイズ次第)',
        'Feature Store': '$0.05-0.20 (データ取り込み)',
        'Processing ジョブ': '$8-12 (ml.m5.xlarge × 実行時間)',
        'Athena クエリ': '$0.01-0.05 (スキャンデータ量次第)'
    }
    
    total_min = 8.16
    total_max = 12.75
    
    for service, cost in costs.items():
        print(f"  {service}: {cost}")
    
    print(f"\n総計概算: ${total_min:.2f} - ${total_max:.2f}")
    print("注意: 実際のコストは使用時間とリソースサイズに依存します")

generate_cost_summary()

print("\n=== 次のステップ ===")
print("Lab 1 完了後は以下のラボに進んでください:")
print("1. Lab 2: SageMaker でのモデル開発")
print("2. Lab 3: モデルのデプロイメント")
print("3. Lab 4: MLOps パイプライン構築")
print("4. Lab 5: モデル監視とメンテナンス")
```

## 🧹 リソースクリーンアップ

最後に、コスト削減のためのクリーンアップスクリプトも提供します：

```bash
#!/bin/bash
# スクリプト: cleanup-lab1.sh

echo "=== Lab 1 リソースクリーンアップ開始 ==="

# 設定読み込み
if [ -f "sagemaker-config.json" ]; then
    DOMAIN_ID=$(jq -r '.domain_id' sagemaker-config.json)
    USER_PROFILE_NAME=$(jq -r '.user_profile_name' sagemaker-config.json)
    EXECUTION_ROLE_NAME=$(jq -r '.execution_role_arn' sagemaker-config.json | sed 's/.*role\///')
    REGION=$(jq -r '.region' sagemaker-config.json)
else
    echo "設定ファイルが見つかりません。手動でリソースを削除してください。"
    exit 1
fi

# Feature Store 削除（オプション）
read -p "Feature Store を削除しますか？ (y/N): " delete_fs
if [ "$delete_fs" = "y" ] || [ "$delete_fs" = "Y" ]; then
    echo "Feature Store 削除中..."
    aws sagemaker delete-feature-group \
        --feature-group-name customer-features-lab1 \
        --region $REGION 2>/dev/null || echo "Feature Store は既に削除されています"
fi

# S3 バケット削除（オプション）
if [ -f "data_catalog.json" ]; then
    BUCKET_NAME=$(jq -r '.bucket_name' data_catalog.json)
    read -p "S3 バケット '$BUCKET_NAME' を削除しますか？ (y/N): " delete_s3
    if [ "$delete_s3" = "y" ] || [ "$delete_s3" = "Y" ]; then
        echo "S3 バケット削除中..."
        aws s3 rm s3://$BUCKET_NAME --recursive
        aws s3 rb s3://$BUCKET_NAME
    fi
fi

# SageMaker Studio リソース削除（オプション）
read -p "SageMaker Studio ドメインを削除しますか？ (y/N): " delete_studio
if [ "$delete_studio" = "y" ] || [ "$delete_studio" = "Y" ]; then
    echo "SageMaker Studio ドメイン削除中..."
    
    # ユーザープロファイル削除
    aws sagemaker delete-user-profile \
        --domain-id $DOMAIN_ID \
        --user-profile-name $USER_PROFILE_NAME \
        --region $REGION
    
    # ドメイン削除
    aws sagemaker delete-domain \
        --domain-id $DOMAIN_ID \
        --region $REGION
fi

echo "=== クリーンアップ完了 ==="
echo "注意: 一部のリソース削除には時間がかかることがあります"
```

このLab 1では、SageMakerの基本的な操作からFeature Storeの構築、データ前処理パイプラインまでを実践的に学習できます。次のLab 2では、このデータを使用してモデルの開発を行います。

<function_calls>
<invoke name="TodoWrite">
<parameter name="todos">[{"id": "19", "content": "MLE-A\u8a66\u9a13\u306e\u6700\u65b0\u60c5\u5831\u3068\u51fa\u984c\u7bc4\u56f2\u3092\u8abf\u67fb", "status": "completed", "priority": "high"}, {"id": "20", "content": "AWS ML\u30b5\u30fc\u30d3\u30b9\u306e\u6700\u65b0\u30c9\u30ad\u30e5\u30e1\u30f3\u30c8\u3092MCP\u30b5\u30fc\u30d0\u3067\u53c2\u7167", "status": "completed", "priority": "high"}, {"id": "21", "content": "ML\u30a8\u30f3\u30b8\u30cb\u30a2\u5411\u3051\u30cf\u30f3\u30ba\u30aa\u30f3\u6559\u6750\u306e\u69cb\u6210\u8a2d\u8a08", "status": "completed", "priority": "high"}, {"id": "22", "content": "\u5b9f\u8df5\u7684\u306aML\u30d1\u30a4\u30d7\u30e9\u30a4\u30f3\u30e9\u30dc\u306e\u4f5c\u6210", "status": "in_progress", "priority": "medium"}, {"id": "23", "content": "SageMaker\u3068\u95a2\u9023\u30b5\u30fc\u30d3\u30b9\u306e\u5b9f\u8df5\u30e9\u30dc", "status": "pending", "priority": "medium"}, {"id": "24", "content": "MLOps\u3068\u30e2\u30c7\u30eb\u30c7\u30d7\u30ed\u30a4\u306e\u30e9\u30dc", "status": "pending", "priority": "medium"}, {"id": "25", "content": "MLE-A\u8a66\u9a13\u60f3\u5b9a\u554f\u984c\u96c6\u306e\u4f5c\u6210", "status": "pending", "priority": "medium"}, {"id": "26", "content": "\u6559\u6750\u306e\u691c\u8a3c\u3068\u6700\u7d42\u8abf\u6574", "status": "pending", "priority": "low"}, {"id": "27", "content": "DevOps Pro\u8a66\u9a13\u306e\u6700\u65b0\u60c5\u5831\u3068\u51fa\u984c\u7bc4\u56f2\u3092\u8abf\u67fb", "status": "pending", "priority": "medium"}, {"id": "28", "content": "DevOps\u5411\u3051\u30cf\u30f3\u30ba\u30aa\u30f3\u6559\u6750\u306e\u4f5c\u6210", "status": "pending", "priority": "medium"}, {"id": "29", "content": "\u6559\u6750\u7528\u30d5\u30a9\u30eb\u30c0\u69cb\u9020\u306e\u6574\u7406\u3068\u4f5c\u6210", "status": "completed", "priority": "high"}]