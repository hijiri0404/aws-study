# MLE-A 想定問題集 01 - データ準備とFeature Engineering

## 📋 試験情報

**Domain Focus**: Domain 1 - Data Preparation for Machine Learning (28%)  
**問題数**: 20問  
**制限時間**: 30分  
**合格点**: 14/20 (70%)

---

## 🔧 問題 1
あなたはオンライン小売業の機械学習エンジニアです。顧客の購買履歴データを使用して商品推薦システムを構築しています。顧客の購買データには以下の特徴があります：

- データサイズ: 10TB
- 更新頻度: リアルタイム
- 特徴量数: 500+
- 予測レイテンシ要件: 100ms以下

このユースケースに最適なAWSサービスの組み合わせは？

**A)** Amazon S3 + Amazon Athena + SageMaker Batch Transform  
**B)** Amazon SageMaker Feature Store + SageMaker Real-time Inference  
**C)** Amazon Redshift + AWS Lambda + API Gateway  
**D)** Amazon DynamoDB + Amazon Kinesis + SageMaker Multi-Model Endpoints

<details>
<summary>解答と解説</summary>

**正解: B**

**解説:**
- **リアルタイム更新**: Feature Store のオンラインストアがリアルタイム更新をサポート
- **大規模データ**: Feature Store は大規模データの効率的な管理が可能
- **低レイテンシ**: オンラインストア + リアルタイム推論エンドポイントで100ms要件を満たせる
- **多数の特徴量**: Feature Store は数百の特徴量を効率的に管理

**他の選択肢が不適切な理由:**
- A: Batch Transform はリアルタイム推論に不適切
- C: Redshift は分析用途で、100ms の低レイテンシ要件に不向き
- D: DynamoDB は特徴量ストアとしての最適化が不十分
</details>

---

## 🔧 問題 2
SageMaker Data Wrangler を使用してデータ前処理を行っています。以下の前処理ステップのうち、Data Wrangler でサポートされていないものは？

**A)** カテゴリカル変数のOne-hot encoding  
**B)** 時系列データの差分計算  
**C)** リアルタイムストリーミングデータの処理  
**D)** 外れ値の検出と削除

<details>
<summary>解答と解説</summary>

**正解: C**

**解説:**
Data Wrangler は**バッチデータ処理**に特化したサービスで、リアルタイムストリーミングデータの処理はサポートしていません。

**Data Wrangler がサポートする機能:**
- 300+ の組み込み変換
- カテゴリカルエンコーディング（One-hot, Label encoding等）
- 時系列変換（ラグ、差分、移動平均等）
- 外れ値検出と処理
- データの可視化と品質チェック

**リアルタイムストリーミング処理には:**
- Amazon Kinesis Analytics
- AWS Glue Streaming
- Amazon EMR with Spark Streaming
を使用する必要があります。
</details>

---

## 🔧 問題 3
Feature Store で特徴量グループを作成する際の必須パラメータは？

**A)** `FeatureGroupName` のみ  
**B)** `FeatureGroupName`, `RecordIdentifierFeatureName`, `EventTimeFeatureName`  
**C)** `FeatureGroupName`, `S3Uri`, `RoleArn`  
**D)** `FeatureGroupName`, `OnlineStoreConfig`, `OfflineStoreConfig`

<details>
<summary>解答と解説</summary>

**正解: B**

**解説:**
Feature Group 作成の**必須パラメータ**は：

1. **FeatureGroupName**: 特徴量グループの名前
2. **RecordIdentifierFeatureName**: レコードを一意に識別する特徴量名
3. **EventTimeFeatureName**: イベント発生時刻を示す特徴量名

```python
feature_group.create(
    s3_uri=s3_uri,
    record_identifier_name='customer_id',  # 必須
    event_time_feature_name='event_time',  # 必須
    role_arn=role,
    feature_definitions=feature_definitions
)
```

**その他のパラメータ**:
- `S3Uri`, `RoleArn`: 通常必要だが、セッションから推論可能
- `OnlineStoreConfig`, `OfflineStoreConfig`: オプション（デフォルト値使用可能）
</details>

---

## 🔧 問題 4
大規模なCSVファイル（100GB）をSageMaker Processing で効率的に処理したい場合の推奨アプローチは？

**A)** 単一のml.m5.24xlarge インスタンスを使用  
**B)** 複数のml.m5.large インスタンスでファイルを分割処理  
**C)** SageMaker Batch Transform を使用  
**D)** AWS Lambda で並列処理

<details>
<summary>解答と解説</summary>

**正解: B**

**解説:**
大規模データの効率的な処理には**水平スケーリング**が推奨されます。

**最適な構成:**
```python
sklearn_processor = SKLearnProcessor(
    framework_version='1.0-1',
    instance_type='ml.m5.large',
    instance_count=10,  # 複数インスタンス
    volume_size_in_gb=100
)
```

**利点:**
- 並列処理による高速化
- コスト効率（小さいインスタンス × 複数 < 大きいインスタンス × 1）
- 障害耐性の向上
- 柔軟なスケーリング

**他の選択肢が不適切な理由:**
- A: 単一インスタンスはボトルネックになりやすい
- C: Batch Transform は推論用、前処理には不適切
- D: Lambda の実行時間制限（15分）により大規模データ処理に不向き
</details>

---

## 🔧 問題 5
時系列予測モデルのために、過去30日間の売上データから特徴量を作成しています。以下のうち、データリークを避けるために最も重要な考慮事項は？

**A)** 特徴量の正規化を行う  
**B)** 将来の情報を含む特徴量を除外する  
**C)** 欠損値を適切に処理する  
**D)** カテゴリカル変数をエンコードする

<details>
<summary>解答と解説</summary>

**正解: B**

**解説:**
**データリーク（Data Leakage）**は機械学習で最も重要な問題の一つです。

**時系列データでのデータリーク例:**
- 予測時点より後の情報を特徴量に含める
- 集計期間が予測対象期間と重複
- 未来の統計量（未来の平均値等）を使用

**予防策:**
```python
# ❌ 悪い例: 将来の情報を含む
future_sales_avg = df['sales'].rolling(window=7).mean().shift(-3)  # 3日後の情報

# ✅ 良い例: 過去の情報のみ
past_sales_avg = df['sales'].rolling(window=7).mean().shift(1)    # 1日前までの情報
```

**時系列分割での注意点:**
```python
# ❌ ランダム分割（時系列では不適切）
train_test_split(X, y, test_size=0.2, random_state=42)

# ✅ 時系列分割
train_data = data[data['date'] < '2024-01-01']
test_data = data[data['date'] >= '2024-01-01']
```
</details>

---

## 🔧 問題 6
SageMaker Feature Store で、オンラインストアとオフラインストアの適切な使い分けは？

**A)** オンライン: バッチ予測、オフライン: リアルタイム予測  
**B)** オンライン: リアルタイム予測、オフライン: モデル訓練・バッチ予測  
**C)** オンライン: データ保存、オフライン: データ分析  
**D)** 両方とも同じ用途で使用可能

<details>
<summary>解答と解説</summary>

**正解: B**

**解説:**

**オンラインストア:**
- **用途**: リアルタイム予測、低レイテンシ検索
- **特徴**: インメモリキャッシュ、ミリ秒レベルの応答
- **制限**: 限定的なクエリ機能、高いコスト

**オフラインストア:**
- **用途**: モデル訓練、バッチ予測、データ分析
- **特徴**: S3ベース、Athenaで複雑なクエリ可能
- **利点**: 大容量、低コスト、長期保存

```python
# オンラインストア使用例（リアルタイム予測）
online_response = feature_group.get_record(
    record_identifier_value_as_string='customer_123'
)

# オフラインストア使用例（分析・訓練）
query = """
SELECT customer_id, age, income, churn_probability
FROM my_feature_group
WHERE event_time >= '2024-01-01'
"""
training_data = feature_store.athena_query(query)
```

**実装における注意点:**
- 同じデータが両方に格納される
- オンラインストアは最新データのみ（TTL設定可能）
- オフラインストアは履歴データすべて保持
</details>

---

## 🔧 問題 7
不均衡データセット（陽性クラス2%、陰性クラス98%）を扱う際の適切な前処理手法は？

**A)** 陰性クラスをランダムに削除してバランスを取る  
**B)** SMOTE（Synthetic Minority Over-sampling Technique）を適用  
**C)** 重み付き損失関数を使用し、データはそのまま保持  
**D)** B と C の両方を検討し、検証データで性能比較

<details>
<summary>解答と解説</summary>

**正解: D**

**解説:**
不均衡データ対策には複数のアプローチがあり、**データとビジネス要件に応じて最適解が異なる**ため、複数手法の比較検討が重要です。

**主要なアプローチ:**

1. **リサンプリング手法:**
   ```python
   from imblearn.over_sampling import SMOTE
   smote = SMOTE(random_state=42)
   X_resampled, y_resampled = smote.fit_resample(X, y)
   ```

2. **重み付き学習:**
   ```python
   from sklearn.ensemble import RandomForestClassifier
   clf = RandomForestClassifier(class_weight='balanced')
   ```

3. **閾値調整:**
   ```python
   from sklearn.metrics import precision_recall_curve
   precision, recall, thresholds = precision_recall_curve(y_true, y_scores)
   optimal_threshold = thresholds[np.argmax(precision + recall)]
   ```

**評価指標の選択:**
- Accuracy は不適切（98%のベースライン）
- Precision, Recall, F1-score, AUC-PR を使用

**SageMaker での実装例:**
```python
# AutoMLでの不均衡データ処理
automl_job = sagemaker.AutoML(
    target_attribute_name='target',
    problem_type='BinaryClassification',
    objective={'MetricName': 'F1'}  # 不均衡データ用の指標
)
```
</details>

---

## 🔧 問題 8
SageMaker Processing で大量の画像データ（10万枚、各5MB）を前処理する際の推奨構成は？

**A)** CPU最適化インスタンス（ml.c5.xlarge）を複数使用  
**B)** GPU搭載インスタンス（ml.p3.2xlarge）を単一使用  
**C)** メモリ最適化インスタンス（ml.r5.large）を複数使用  
**D)** GPU搭載インスタンス（ml.p3.xlarge）を複数使用

<details>
<summary>解答と解説</summary>

**正解: D**

**解説:**
画像前処理のような**計算集約的タスク**には**GPU並列処理**が最適です。

**データ量の計算:**
- 10万枚 × 5MB = 500GB
- 並列処理が必須

**推奨構成の理由:**
1. **GPU活用**: 画像処理（リサイズ、正規化、拡張）はGPUで高速化
2. **複数インスタンス**: データ分散処理で時間短縮
3. **適切なGPUサイズ**: p3.xlarge は 1GPU、コスト効率が良い

```python
# 画像処理用のProcessorセットアップ
image_processor = PyTorchProcessor(
    framework_version='1.12',
    py_version='py38',
    instance_type='ml.p3.xlarge',
    instance_count=4,  # 4インスタンスで並列処理
    volume_size_in_gb=200,
    role=role
)

# 処理時間の推定
# CPU: ~20時間, GPU(単一): ~4時間, GPU(並列): ~1時間
```

**他の選択肢の問題:**
- A: CPU処理は画像処理に非効率
- B: 単一インスタンスではボトルネック
- C: メモリ最適化は不要、GPU処理能力が重要
</details>

---

## 🔧 問題 9
以下のPythonコードでSageMaker Feature Storeから特徴量を取得しています。この実装の問題点は？

```python
def get_customer_features(customer_ids):
    features = []
    for customer_id in customer_ids:
        response = feature_group.get_record(
            record_identifier_value_as_string=str(customer_id)
        )
        features.append(response.record)
    return features
```

**A)** エラーハンドリングがない  
**B)** データ型変換が不適切  
**C)** バッチ処理を使用していない  
**D)** 上記すべて

<details>
<summary>解答と解説</summary>

**正解: D**

**解説:**
提供されたコードには複数の問題があります。

**問題点と改善案:**

1. **エラーハンドリング不足:**
   ```python
   try:
       response = feature_group.get_record(...)
   except ClientError as e:
       if e.response['Error']['Code'] == 'ResourceNotFound':
           # レコードが存在しない場合の処理
           return None
       else:
           raise e
   ```

2. **非効率な逐次処理:**
   ```python
   # ❌ 悪い例: ループで逐次処理
   for customer_id in customer_ids:
       response = feature_group.get_record(...)
   
   # ✅ 改善案: バッチ処理
   from concurrent.futures import ThreadPoolExecutor
   
   def get_batch_features(customer_ids, batch_size=10):
       with ThreadPoolExecutor(max_workers=batch_size) as executor:
           futures = [executor.submit(get_single_record, cid) 
                     for cid in customer_ids]
           return [f.result() for f in futures]
   ```

3. **データ型変換の問題:**
   ```python
   # レスポンスの適切な処理
   def parse_feature_record(record):
       features = {}
       for feature in record:
           feature_name = feature.feature_name
           value = feature.value_as_string
           # 適切なデータ型に変換
           if feature_name in numeric_features:
               features[feature_name] = float(value)
           else:
               features[feature_name] = value
       return features
   ```

**最適化されたコード例:**
```python
import asyncio
from concurrent.futures import ThreadPoolExecutor
import logging

async def get_customer_features_optimized(customer_ids, max_workers=10):
    async def get_single_feature(customer_id):
        try:
            response = await feature_group.get_record(
                record_identifier_value_as_string=str(customer_id)
            )
            return parse_feature_record(response.record)
        except Exception as e:
            logging.warning(f"Failed to get features for {customer_id}: {e}")
            return None
    
    tasks = [get_single_feature(cid) for cid in customer_ids]
    return await asyncio.gather(*tasks)
```
</details>

---

## 🔧 問題 10
時系列データでの特徴量エンジニアリングにおいて、「ラグ特徴量」を作成する際の重要な考慮事項は？

**A)** ラグの数は多いほど良い  
**B)** 予測時に利用可能なデータのみを使用  
**C)** 欠損値は単純に削除  
**D)** すべてのラグ特徴量を同じ重みで扱う

<details>
<summary>解答と解説</summary>

**正解: B**

**解説:**
時系列データでのラグ特徴量作成では、**実際の予測時に利用可能なデータのみ**を使用することが最重要です。

**適切なラグ特徴量の実装:**
```python
def create_lag_features(df, target_col, lags=[1, 7, 30]):
    """
    適切なラグ特徴量の作成
    """
    df_lagged = df.copy()
    
    for lag in lags:
        # lag日前の値を特徴量として追加
        df_lagged[f'{target_col}_lag_{lag}'] = df[target_col].shift(lag)
    
    # 予測時に利用不可能な期間を削除
    df_lagged = df_lagged.dropna()
    
    return df_lagged

# ❌ 悪い例: 未来の情報を含む
df['sales_lag_minus1'] = df['sales'].shift(-1)  # 1日後の売上

# ✅ 良い例: 過去の情報のみ
df['sales_lag_1'] = df['sales'].shift(1)        # 1日前の売上
df['sales_lag_7'] = df['sales'].shift(7)        # 7日前の売上
```

**その他の重要な考慮事項:**

1. **適切なラグ数の選択:**
   ```python
   # ドメイン知識に基づく選択
   # 小売業: 週次（7日）、月次（30日）パターン
   # 金融: 日次、週次パターン
   ```

2. **欠損値の適切な処理:**
   ```python
   # forward fill（前方補完）
   df['sales_lag_1'] = df['sales'].shift(1).fillna(method='ffill')
   
   # 移動平均での補完
   df['sales_lag_1'] = df['sales'].shift(1).fillna(
       df['sales'].rolling(window=7).mean()
   )
   ```

3. **統計的特徴量の組み合わせ:**
   ```python
   # 移動平均
   df['sales_ma_7'] = df['sales'].rolling(window=7).mean().shift(1)
   
   # 移動標準偏差
   df['sales_std_7'] = df['sales'].rolling(window=7).std().shift(1)
   
   # 季節性調整
   df['sales_seasonal'] = df['sales'] / df.groupby(df.index.dayofweek)['sales'].transform('mean')
   ```

**SageMaker での時系列特徴量エンジニアリング:**
```python
from sagemaker.tensorflow import TensorFlow

# TensorFlow での時系列モデル
tf_estimator = TensorFlow(
    entry_point='time_series_model.py',
    framework_version='2.8',
    py_version='py39',
    instance_type='ml.m5.large',
    hyperparameters={
        'sequence_length': 30,  # 30日分の履歴を使用
        'prediction_horizon': 7  # 7日後を予測
    }
)
```
</details>

---

## 📊 解答一覧

| 問題 | 正解 | Domain | 重要度 |
|------|------|--------|--------|
| 1 | B | Data Preparation | ⭐⭐⭐ |
| 2 | C | Data Preparation | ⭐⭐ |
| 3 | B | Feature Store | ⭐⭐⭐ |
| 4 | B | Data Processing | ⭐⭐⭐ |
| 5 | B | Data Quality | ⭐⭐⭐⭐ |
| 6 | B | Feature Store | ⭐⭐⭐ |
| 7 | D | Data Preparation | ⭐⭐⭐⭐ |
| 8 | D | Processing | ⭐⭐ |
| 9 | D | Implementation | ⭐⭐⭐ |
| 10 | B | Time Series | ⭐⭐⭐⭐ |

## 🎯 学習のポイント

### 高得点のコツ
1. **Feature Store の理解**: オンライン/オフラインストアの使い分け
2. **データリーク防止**: 時系列データでの注意点
3. **スケーリング戦略**: 大規模データ処理のアプローチ
4. **実装詳細**: SageMaker の具体的な設定方法

### 復習すべき領域
- **70%未満の場合**: 基本概念から再学習
- **70-85%の場合**: 実装詳細を重点的に
- **85%以上の場合**: 次のDomainの学習へ

### 次のステップ
このDomain 1で8割以上正解できたら、**Domain 2: ML Model Development** の学習に進んでください。

---
**注意**: この問題集はMLE-A試験の出題傾向を基に作成されており、実際の試験問題とは異なります。AWS公式の練習問題も併用することを推奨します。