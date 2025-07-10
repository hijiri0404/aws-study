# AWS認定試験対策教材

このディレクトリには、AWS認定試験向けの実践的なハンズオン教材が含まれています。

## 📚 教材構成

### 🌐 Networking Specialty (ANS-C01)
**AWS Certified Advanced Networking - Specialty**
- **難易度**: ⭐⭐⭐⭐⭐
- **対象**: ネットワークエンジニア、インフラエンジニア
- **推奨経験**: ネットワーキング5年以上

### 🤖 ML Engineer Associate (MLE-A) 
**AWS Certified Machine Learning Engineer - Associate**
- **難易度**: ⭐⭐⭐⭐
- **対象**: MLエンジニア、データサイエンティスト
- **推奨経験**: ML開発経験2年以上

### 🚀 DevOps Engineer Professional (DOP-C02)
**AWS Certified DevOps Engineer - Professional**
- **難易度**: ⭐⭐⭐⭐⭐
- **対象**: DevOpsエンジニア、SRE
- **推奨経験**: AWS運用経験3年以上

## 🎯 学習順序の推奨

### 初学者向け
1. **Associate レベル資格取得後**
2. **ML Engineer Associate** （MLに興味がある場合）
3. **DevOps Engineer Professional** （インフラ・運用に興味がある場合）
4. **Networking Specialty** （ネットワーク専門性が必要な場合）

### 経験者向け
1. **自分の専門分野から開始**
2. **実務で必要な資格を優先**

## 💰 コスト概算

各教材の実習には実際のAWSリソースを使用します：

| 教材 | 月額概算コスト | ラボ実行時間 | 単発実行コスト |
|------|----------------|--------------|----------------|
| Networking | $150-200 | 20-30時間 | $50-80 |
| ML Engineer | $100-150 | 15-25時間 | $40-60 |
| DevOps | $80-120 | 15-20時間 | $30-50 |

**注意**: コストを抑えるため、各ラボ後は必ずリソースを削除してください。

## 🛠️ 事前準備

### 必要なツール
- AWS CLI (最新版)
- AWS Management Console アクセス
- Python 3.8+
- Docker
- Git

### 権限設定
- 管理者権限（学習用アカウント推奨）
- 課金アラート設定
- MFA有効化

## 📋 学習の進め方

### 1. 基礎固め
- 各フォルダの `00-fundamentals.md` から開始
- AWS公式ドキュメントを併用

### 2. ハンズオン実践
- `labs/` ディレクトリの順番に実行
- 各ラボ後は必ず検証

### 3. 問題演習
- `practice-exams/` で理解度確認
- 苦手分野は再度ハンズオン

### 4. 試験準備
- `exam-tips.md` で最終確認
- AWS公式の練習問題も併用

## 🔧 サポート

### 困った時は
1. 各教材の `troubleshooting.md` を確認
2. AWS公式ドキュメントを参照
3. AWSサポートケースを作成（必要に応じて）

### アップデート
- AWS サービスの更新に合わせて教材も定期更新
- MCP サーバーを活用した最新情報の反映

---

**重要**: これらの教材は実践重視で設計されており、理論的な説明は最小限です。AWS公式の学習パスと併用することを強く推奨します。