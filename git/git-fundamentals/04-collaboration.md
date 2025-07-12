# チーム開発・コラボレーション

Gitの真価は、チーム開発での協力において発揮されます。効率的なコラボレーション手法を学び、プロフェッショナルな開発チームの一員として活躍しましょう。

## 📖 目次

1. [チーム開発の基本](#チーム開発の基本)
2. [GitHub/GitLabでのコラボレーション](#githubgitlabでのコラボレーション)
3. [Pull Request / Merge Request](#pull-request--merge-request)
4. [コードレビュー](#コードレビュー)
5. [イシュー管理](#イシュー管理)
6. [継続的インテグレーション](#継続的インテグレーション)

## 🤝 チーム開発の基本

### チーム開発の課題

#### 1. 同時編集による競合
```bash
# 開発者Aの作業
git add file.py
git commit -m "機能Aを追加"

# 開発者Bの作業（同じファイル）
git add file.py
git commit -m "機能Bを追加"

# プッシュ時にコンフリクト発生
git push origin main
# error: failed to push some refs
```

#### 2. 変更の追跡困難
```bash
# 誰がいつ何を変更したかわからない
git log --oneline
# abc123 バグ修正
# def456 機能追加
# 具体的な内容が不明...
```

#### 3. 品質管理の難しさ
- テストされていないコードの混入
- コーディング規約の不統一
- セキュリティ問題の見落とし

### チーム開発のベストプラクティス

#### 1. 🔒 ブランチ保護ルール

```bash
# メインブランチの直接変更を禁止
# GitHub/GitLabの設定で以下を有効化：
# - 直接プッシュの禁止
# - Pull Requestの必須化
# - レビューの必須化
# - CI/CDテストの必須化
```

#### 2. 📝 明確なコミットメッセージ

```bash
# Conventional Commits形式
git commit -m "feat(auth): ユーザーログイン機能を追加

- JWT認証を実装
- ログイン画面のUIを作成
- セッション管理機能を追加

Closes #123"
```

#### 3. 🌿 適切なブランチ戦略

```bash
# 機能別ブランチの作成
git checkout -b feature/user-profile
git checkout -b feature/payment-system
git checkout -b hotfix/security-patch
```

## 🐙 GitHub/GitLabでのコラボレーション

### リポジトリの権限管理

#### 権限レベル

1. **Read**: クローン、イシュー作成
2. **Write**: プッシュ、ブランチ作成
3. **Maintain**: 設定変更、リリース管理
4. **Admin**: 全権限

#### チーム構成例

```yaml
# 開発チーム構成
Core Team:
  - Lead Developer (Admin)
  - Senior Developers (Maintain)
  - Developers (Write)
  
Contributors:
  - Junior Developers (Write)
  - Interns (Write with restrictions)
  
External:
  - OSS Contributors (Read)
```

### フォーク・ワークフロー

オープンソースプロジェクトでよく使用される手法です。

```bash
# 1. 元リポジトリをフォーク
# GitHubのWeb UIで「Fork」ボタンをクリック

# 2. フォークしたリポジトリをクローン
git clone https://github.com/yourname/original-project.git
cd original-project

# 3. 元リポジトリをupstreamとして追加
git remote add upstream https://github.com/original/original-project.git

# 4. 新機能開発
git checkout -b feature/new-feature
# 開発作業...
git commit -m "feat: 新機能を追加"

# 5. フォークリポジトリにプッシュ
git push origin feature/new-feature

# 6. Pull Requestを作成
# GitHub Web UIでPull Requestを作成

# 7. 元リポジトリの最新変更を同期
git checkout main
git pull upstream main
git push origin main
```

### リポジトリ構成のベストプラクティス

```
project-root/
├── .github/                    # GitHub設定
│   ├── ISSUE_TEMPLATE/        # イシューテンプレート
│   ├── PULL_REQUEST_TEMPLATE.md
│   └── workflows/             # GitHub Actions
├── docs/                      # ドキュメント
├── src/                       # ソースコード
├── tests/                     # テストコード
├── .gitignore                 # 無視ファイル設定
├── README.md                  # プロジェクト概要
├── CONTRIBUTING.md            # 貢献ガイド
└── CODE_OF_CONDUCT.md         # 行動規範
```

## 🔄 Pull Request / Merge Request

### Pull Requestの作成手順

#### 1. ブランチ作成・開発

```bash
# 最新のmainブランチから開始
git checkout main
git pull origin main

# 機能ブランチ作成
git checkout -b feature/user-notification

# 開発作業
echo "notification system" > notification.py
git add notification.py
git commit -m "feat: ユーザー通知システムを追加"

# リモートにプッシュ
git push -u origin feature/user-notification
```

#### 2. Pull Request作成

```markdown
# Pull Requestテンプレート例

## 概要
ユーザーに対する通知機能を実装しました。

## 変更内容
- [ ] メール通知機能
- [ ] プッシュ通知機能
- [ ] 通知設定UI

## テスト
- [ ] 単体テスト追加
- [ ] 統合テスト実行
- [ ] 手動テスト完了

## 関連イシュー
Closes #456

## スクリーンショット
![notification-ui](screenshot.png)

## レビューポイント
- 通知のタイミング設定
- パフォーマンスへの影響
- セキュリティ考慮事項
```

### Pull Requestのベストプラクティス

#### 1. 📏 適切なサイズ

```bash
# 良い例：小さな変更
git diff --stat
# notification.py | 45 +++++++++++++++++++++
# tests/test_notification.py | 23 +++++++++++
# 2 files changed, 68 insertions(+)

# 避けるべき例：大きすぎる変更
git diff --stat
# 50 files changed, 2000 insertions(+), 1500 deletions(-)
```

#### 2. 🎯 単一の目的

```bash
# 良い例：機能ごとに分離
feature/user-authentication    # 認証機能のみ
feature/password-reset         # パスワードリセットのみ

# 避けるべき例：複数の機能を混在
feature/user-system           # 認証 + プロフィール + 設定
```

#### 3. 📝 明確な説明

```markdown
# 良いPull Request説明
## 背景
ユーザーからのフィードバックで、通知機能の要望が多数寄せられていました。

## 解決方法
非同期処理を使用したメール通知システムを実装しました。

## 影響範囲
- 新規機能追加のため、既存機能への影響はありません
- データベースマイグレーションが必要です
```

### レビュープロセス

#### 1. 自動チェック

```yaml
# .github/workflows/pr-check.yml
name: PR Check
on:
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v2
    - name: Run tests
      run: |
        npm test
        npm run lint
        npm run security-check
```

#### 2. 人的レビュー

```bash
# レビュアーの割り当て
# GitHub UI上で以下を設定：
# - 必須レビュアー: 2名以上
# - コードオーナー: 自動割り当て
# - 専門分野別レビュアー
```

## 👁️ コードレビュー

### 効果的なレビューのポイント

#### 1. 🔍 レビュー観点

**機能性**
```python
# レビュー例：エラーハンドリングの確認
def send_notification(user, message):
    try:
        email_service.send(user.email, message)
    except EmailServiceError:
        # レビューコメント：ログ出力とフォールバック処理を追加してください
        pass
```

**可読性**
```python
# レビュー例：命名の改善提案
def calc(x, y):  # ❌ 不明確
    return x + y

def calculate_total_price(base_price, tax):  # ✅ 明確
    return base_price + tax
```

**セキュリティ**
```python
# レビュー例：SQLインジェクション対策
query = f"SELECT * FROM users WHERE id = {user_id}"  # ❌ 危険
# レビューコメント：パラメータ化クエリを使用してください

query = "SELECT * FROM users WHERE id = %s"  # ✅ 安全
cursor.execute(query, (user_id,))
```

#### 2. 💬 建設的なフィードバック

```markdown
# 良いレビューコメント例

## 提案
この部分は `map()` を使用することで、より関数型プログラミングのスタイルになります：
```python
# 現在のコード
result = []
for item in items:
    result.append(process(item))

# 提案
result = list(map(process, items))
```

## 質問
この実装の計算量はO(n²)のように見えますが、大量のデータでの性能テストは実施されましたか？

## 賞賛
エラーハンドリングが非常に丁寧に実装されていて素晴らしいです！
```

### レビューツールの活用

#### GitHub/GitLabの機能

```bash
# ファイル内コメント
# 特定の行にコメントを付与

# 提案変更
# コードの修正案を直接提示

# レビューステータス
# - Request Changes（修正要求）
# - Approve（承認）
# - Comment（コメントのみ）
```

## 📋 イシュー管理

### 効果的なイシュー作成

#### バグレポート例

```markdown
# Bug Report

## 環境
- OS: macOS 12.0
- Browser: Chrome 95.0
- Node.js: 16.13.0

## 再現手順
1. ログイン画面を開く
2. 無効なメールアドレスを入力
3. パスワードを入力
4. ログインボタンをクリック

## 期待結果
エラーメッセージが表示される

## 実際の結果
500エラーでアプリケーションがクラッシュ

## エラーログ
```
Error: Cannot read property 'email' of undefined
  at validateUser (auth.js:25)
```

## スクリーンショット
![error-screenshot](error.png)
```

#### 機能要求例

```markdown
# Feature Request

## 概要
ユーザーがプロフィール画像をアップロードできる機能

## 背景
現在、ユーザーはデフォルトのアバターしか使用できず、
個性的なプロフィール作成ができない状況です。

## 提案する機能
- 画像ファイルのアップロード
- 画像のリサイズとトリミング
- 複数フォーマット対応（JPEG, PNG, WebP）

## 受け入れ基準
- [ ] 5MB以下のファイルサイズ制限
- [ ] 正方形へのトリミング機能
- [ ] プレビュー機能
- [ ] 不適切な画像の検出

## 技術的考慮事項
- CDNでの画像配信
- セキュリティスキャン
- パフォーマンス最適化
```

### ラベルとマイルストーン

#### ラベルの分類例

```yaml
# タイプ
- bug: バグレポート
- enhancement: 機能強化
- feature: 新機能
- documentation: ドキュメント

# 優先度
- priority/critical: 最優先
- priority/high: 高優先度
- priority/medium: 中優先度
- priority/low: 低優先度

# ステータス
- status/blocked: ブロック中
- status/in-progress: 作業中
- status/review: レビュー中

# コンポーネント
- component/frontend: フロントエンド
- component/backend: バックエンド
- component/database: データベース
```

#### マイルストーンの管理

```markdown
# マイルストーン例

## v2.1.0 Release (2025-03-01)
- User Profile Management
- Advanced Search
- Performance Improvements

## v2.0.0 Release (2025-02-01)
- New Authentication System
- API v2 Implementation
- Mobile App Support
```

## 🔄 継続的インテグレーション

### GitHub Actionsの設定

#### 基本的なCI/CDパイプライン

```yaml
# .github/workflows/ci.yml
name: CI/CD Pipeline

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    
    strategy:
      matrix:
        node-version: [14.x, 16.x, 18.x]
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Setup Node.js
      uses: actions/setup-node@v3
      with:
        node-version: ${{ matrix.node-version }}
        cache: 'npm'
    
    - name: Install dependencies
      run: npm ci
    
    - name: Run linter
      run: npm run lint
    
    - name: Run tests
      run: npm test
    
    - name: Run security audit
      run: npm audit
    
    - name: Upload coverage reports
      uses: codecov/codecov-action@v3

  deploy:
    needs: test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Deploy to staging
      run: |
        echo "Deploying to staging environment"
        # デプロイスクリプト実行
```

### 品質ゲート

#### テストカバレッジ

```bash
# カバレッジしきい値の設定
{
  "scripts": {
    "test": "jest --coverage --coverageThreshold='{\"global\":{\"branches\":80,\"functions\":80,\"lines\":80,\"statements\":80}}'"
  }
}
```

#### コード品質チェック

```yaml
# SonarCloudとの統合
- name: SonarCloud Scan
  uses: SonarSource/sonarcloud-github-action@master
  env:
    GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
    SONAR_TOKEN: ${{ secrets.SONAR_TOKEN }}
```

## 🎓 学習チェックリスト

この章で学んだ内容を確認しましょう：

### チーム開発基本
- [ ] ブランチ保護ルールの設定ができる
- [ ] 適切なコミットメッセージを書ける
- [ ] チーム開発のワークフローを理解している

### コラボレーション
- [ ] フォーク・ワークフローを実行できる
- [ ] Pull Requestを作成・レビューできる
- [ ] 権限管理の概念を理解している

### コードレビュー
- [ ] 建設的なフィードバックができる
- [ ] セキュリティ観点でのレビューができる
- [ ] レビューツールを効果的に使用できる

### プロジェクト管理
- [ ] 効果的なイシューを作成できる
- [ ] ラベルとマイルストーンを管理できる
- [ ] CI/CDパイプラインの基本を理解している

## 💡 実践的なヒント

### チーム開発の成功要因

1. **明確なコミュニケーション**: 定期的な進捗共有
2. **ドキュメント化**: 決定事項と変更の記録
3. **自動化**: 反復作業の自動化
4. **品質重視**: テストとレビューの徹底

### よくある問題と対策

| 問題 | 対策 |
|------|------|
| **コンフリクト頻発** | 定期的なマージ・リベース |
| **レビュー遅延** | レビュー担当者の明確化 |
| **品質低下** | CI/CDパイプラインの強化 |
| **コミュニケーション不足** | 定期的なミーティング |

## 🚀 次のステップ

チーム開発の基本を理解したら、次はトラブルシューティングを学習しましょう！

👉 [05-troubleshooting.md](./05-troubleshooting.md) でトラブル解決法を学習

---

**🤖 Generated with [Claude Code](https://claude.ai/code)**  
**📅 Last Updated**: 2025年1月  
**🎯 Goal**: 効果的なチーム開発とコラボレーションの習得