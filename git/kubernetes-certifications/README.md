# Kubernetes認定試験対策教材

このディレクトリには、Kubernetes認定試験向けの実践的なハンズオン教材が含まれています。

## 📚 教材構成

### ⚡ CKA (Certified Kubernetes Administrator)
**Certified Kubernetes Administrator**
- **難易度**: ⭐⭐⭐⭐
- **対象**: Kubernetesクラスター管理者、インフラエンジニア
- **推奨経験**: Kubernetes実務経験6ヶ月以上

### 🚀 CKAD (Certified Kubernetes Application Developer)  
**Certified Kubernetes Application Developer**
- **難易度**: ⭐⭐⭐
- **対象**: アプリケーション開発者、DevOpsエンジニア
- **推奨経験**: Kubernetes開発経験3ヶ月以上

### 🔒 CKS (Certified Kubernetes Security Specialist)
**Certified Kubernetes Security Specialist**
- **難易度**: ⭐⭐⭐⭐⭐
- **対象**: セキュリティエンジニア、上級管理者
- **推奨経験**: CKA取得済み + セキュリティ実務経験

## 🎯 学習順序の推奨

### 初学者向け
1. **CKAD** → アプリケーション開発から開始
2. **CKA** → クラスター管理の習得
3. **CKS** → セキュリティ専門性の強化

### 経験者向け
1. **CKA** → 基盤となる管理スキル
2. **CKAD** → 開発視点の理解
3. **CKS** → セキュリティの深化

## 💰 コスト概算

各教材の実習には実際のKubernetesクラスターを使用します：

| 教材 | 月額概算コスト | ラボ実行時間 | 単発実行コスト |
|------|----------------|--------------|----------------|
| CKA | $80-120 | 25-35時間 | $30-50 |
| CKAD | $60-100 | 20-30時間 | $25-40 |
| CKS | $100-150 | 30-40時間 | $40-60 |

**注意**: コストを抑えるため、各ラボ後は必ずクラスターを削除してください。

## 🛠️ 事前準備

### 必要なツール
- `kubectl` (最新版)
- Docker Desktop または Podman
- AWS CLI または Azure CLI または Google Cloud CLI  
- Git
- テキストエディタ (VS Code推奨)

### 推奨学習環境
- **AWS EKS**: マネージドKubernetes（推奨）
- **Google GKE**: 高機能なマネージドサービス
- **Azure AKS**: Azureユーザー向け
- **minikube**: ローカル学習用（無料）

## 📋 学習の進め方

### 1. 基礎固め
- 各フォルダの `00-fundamentals.md` から開始
- Kubernetes公式ドキュメントを併用

### 2. ハンズオン実践
- `labs/` ディレクトリの順番に実行
- 実際のクラスターでの操作経験を積む

### 3. 問題演習
- `practice-exams/` で実技試験対策
- 時間を計測して実戦慣れ

### 4. 試験準備
- `exam-tips.md` で最終確認
- 公式の練習問題も併用

## 🔧 サポート

### 困った時は
1. 各教材の `troubleshooting.md` を確認
2. Kubernetes公式ドキュメントを参照
3. コミュニティフォーラムで質問

### アップデート
- Kubernetesの更新に合わせて教材も定期更新
- 最新バージョン（v1.28+）に対応

## 🎯 試験概要

| 試験 | 時間 | 問題数 | 形式 | 費用 |
|------|------|--------|------|------|
| CKA | 2時間 | 15-20問 | 実技 | $395 |
| CKAD | 2時間 | 15-20問 | 実技 | $395 |
| CKS | 2時間 | 15-20問 | 実技 | $395 |

**重要**: すべて実技試験です。実際のKubernetesクラスターでタスクを完了する必要があります。

---

**重要**: これらの教材は実践重視で設計されており、理論的な説明は最小限です。Kubernetes公式ドキュメントと併用することを強く推奨します。