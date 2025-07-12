# ブランチとワークフロー

Gitの真の力はブランチ機能にあります。ブランチを使った開発ワークフローを学習し、チーム開発で必須のスキルを身につけましょう。

## 📖 目次

1. [ブランチの基本概念](#ブランチの基本概念)
2. [ブランチ戦略](#ブランチ戦略)
3. [実践的なワークフロー](#実践的なワークフロー)
4. [マージとリベース](#マージとリベース)
5. [コンフリクト解決](#コンフリクト解決)
6. [タグ管理](#タグ管理)

## 🌿 ブランチの基本概念

### ブランチとは

**ブランチ**は、開発の流れを分岐させる機能です。メインの開発ラインから独立して作業を進めることができます。

```
main     ●───●───●───●───●   (安定したメインライン)
          \             /
feature    ●───●───●───●     (新機能開発)
```

### ブランチの利点

#### 1. 🔒 安全な実験
```bash
# 実験的な機能を安全に開発
git checkout -b experiment/new-ui
# 失敗しても main ブランチに影響なし
```

#### 2. 🚀 並行開発
```bash
# 複数の機能を同時に開発
git checkout -b feature/user-auth    # 認証機能
git checkout -b feature/payment      # 決済機能
git checkout -b hotfix/urgent-bug    # 緊急バグ修正
```

#### 3. 📋 リリース管理
```bash
# 安定版とベータ版を分離管理
main      ●───●───●───●  (安定版)
develop    \───●───●───●  (開発版)
```

### ブランチの種類

#### 1. メインブランチ
- **main/master**: 常に本番環境にデプロイ可能な状態
- **develop**: 開発中の最新機能を統合

#### 2. サポートブランチ
- **feature/**: 新機能開発
- **release/**: リリース準備
- **hotfix/**: 緊急バグ修正

## 🎯 ブランチ戦略

### Git Flow

Git Flowは最も有名なブランチ戦略の一つです。

```
main      ●───────●───────●  (v1.0)  (v2.0)
           \     /|\     /
develop     ●───● | ●───●
            |     |     |
feature     ●───●/      |
                        |
hotfix                  ●───●
```

#### ブランチの役割

1. **main**: 本番環境の安定版
2. **develop**: 開発の中心となるブランチ
3. **feature/**: 新機能開発用
4. **release/**: リリース準備用
5. **hotfix/**: 緊急修正用

#### Git Flow のコマンド例

```bash
# 新機能開発開始
git checkout develop
git checkout -b feature/user-profile

# 開発完了後、developにマージ
git checkout develop
git merge --no-ff feature/user-profile
git branch -d feature/user-profile

# リリース準備
git checkout develop
git checkout -b release/v1.2.0
# バージョン番号更新、バグ修正など

# リリース完了
git checkout main
git merge --no-ff release/v1.2.0
git tag v1.2.0
git checkout develop
git merge --no-ff release/v1.2.0
git branch -d release/v1.2.0
```

### GitHub Flow

GitHubが推奨するシンプルなワークフローです。

```
main    ●───●───●───●───●
         \     /     /
feature   ●───●─────●
```

#### GitHub Flow の手順

```bash
# 1. 新機能開発開始
git checkout main
git pull origin main
git checkout -b feature/new-feature

# 2. 開発・コミット
git add .
git commit -m "feat: 新機能を追加"
git push -u origin feature/new-feature

# 3. Pull Request作成
# GitHubのWeb UIでPull Requestを作成

# 4. レビュー・マージ
# レビュー後、mainブランチにマージ

# 5. ブランチ削除
git checkout main
git pull origin main
git branch -d feature/new-feature
```

### GitLab Flow

GitLabが提案するワークフローです。

```
main        ●───●───●───●
             \   \   \
production    ●───●───●    (本番環境)
staging        ●───●       (ステージング環境)
```

## 🔄 実践的なワークフロー

### 個人開発のワークフロー

```bash
# 1. プロジェクト開始
git init my-project
cd my-project
echo "# My Project" > README.md
git add README.md
git commit -m "initial commit"

# 2. 新機能開発
git checkout -b feature/todo-list
# 開発作業...
git add .
git commit -m "feat: TODO一覧表示機能を追加"

# 3. メインブランチに統合
git checkout main
git merge feature/todo-list
git branch -d feature/todo-list

# 4. リモートにプッシュ
git push origin main
```

### チーム開発のワークフロー

```bash
# 1. 最新状態に更新
git checkout main
git pull origin main

# 2. 作業ブランチ作成
git checkout -b feature/user-authentication

# 3. 開発・定期的なプッシュ
git add .
git commit -m "feat: ログイン画面を追加"
git push -u origin feature/user-authentication

# 4. 開発継続中の更新取り込み
git checkout main
git pull origin main
git checkout feature/user-authentication
git merge main  # または git rebase main

# 5. 開発完了・Pull Request
git push origin feature/user-authentication
# GitHub/GitLabでPull Request作成

# 6. マージ後のクリーンアップ
git checkout main
git pull origin main
git branch -d feature/user-authentication
git push origin --delete feature/user-authentication
```

### リリース管理のワークフロー

```bash
# 1. リリースブランチ作成
git checkout develop
git checkout -b release/v1.5.0

# 2. バージョン情報更新
echo "v1.5.0" > VERSION
git add VERSION
git commit -m "bump version to v1.5.0"

# 3. 最終テスト・バグ修正
git add .
git commit -m "fix: リリース前のバグ修正"

# 4. メインブランチにマージ
git checkout main
git merge --no-ff release/v1.5.0

# 5. タグ付け
git tag -a v1.5.0 -m "Release version 1.5.0"

# 6. developブランチにもマージ
git checkout develop
git merge --no-ff release/v1.5.0

# 7. リリースブランチ削除
git branch -d release/v1.5.0

# 8. リモートに反映
git push origin main
git push origin develop
git push origin v1.5.0
```

## 🔀 マージとリベース

### マージ（Merge）

マージは、2つのブランチの変更を統合する操作です。

#### Fast-Forward マージ

```bash
main     ●───●
          \
feature    ●───●

# マージ後
main     ●───●───●───●
```

```bash
git checkout main
git merge feature/simple-change
```

#### Non-Fast-Forward マージ

```bash
main     ●───●───●
          \     /
feature    ●───●

# マージ後（マージコミット作成）
main     ●───●───●───M
          \         /
feature    ●───●───●
```

```bash
git checkout main
git merge --no-ff feature/complex-change
```

### リベース（Rebase）

リベースは、コミット履歴を整理して線形にする操作です。

#### 基本的なリベース

```bash
main     ●───●───●
          \
feature    ●───●

# リベース後
main     ●───●───●───●───●
```

```bash
git checkout feature/clean-history
git rebase main
git checkout main
git merge feature/clean-history  # Fast-Forwardマージ
```

#### インタラクティブリベース

```bash
# 直近3つのコミットを整理
git rebase -i HEAD~3

# エディタが開き、コミットを整理可能
# pick: そのまま残す
# squash: 前のコミットにまとめる
# edit: コミットを編集する
# drop: コミットを削除する
```

### マージ vs リベース の使い分け

| 状況 | 推奨手法 | 理由 |
|------|----------|------|
| **機能ブランチの統合** | Merge | 開発履歴を残す |
| **コミット履歴の整理** | Rebase | 線形で見やすい履歴 |
| **公開済みブランチ** | Merge | 他の開発者への影響を避ける |
| **個人作業ブランチ** | Rebase | きれいな履歴を維持 |

## ⚠️ コンフリクト解決

### コンフリクトとは

複数の人が同じファイルの同じ箇所を変更した場合に発生します。

```bash
# コンフリクト発生例
git merge feature/conflicting-branch
# Auto-merging index.html
# CONFLICT (content): Merge conflict in index.html
# Automatic merge failed; fix conflicts and then commit the result.
```

### コンフリクトの解決手順

#### 1. コンフリクトファイルの確認

```bash
git status
# Unmerged paths:
#   both modified: index.html
```

#### 2. ファイル内容の確認

```html
<!DOCTYPE html>
<html>
<head>
<<<<<<< HEAD
    <title>My Website</title>
=======
    <title>Awesome Website</title>
>>>>>>> feature/new-title
</head>
```

#### 3. 手動解決

```html
<!DOCTYPE html>
<html>
<head>
    <title>My Awesome Website</title>
</head>
```

#### 4. 解決をマーク

```bash
git add index.html
git commit -m "resolve: タイトルのコンフリクトを解決"
```

### コンフリクト解決のツール

```bash
# マージツールの設定
git config --global merge.tool vimdiff

# マージツールの起動
git mergetool

# 人気のマージツール
# - VS Code: code --wait
# - KDiff3: kdiff3
# - Meld: meld
# - P4Merge: p4merge
```

## 🏷️ タグ管理

### タグとは

特定のコミットにマーカーを付ける機能です。主にリリースバージョンの管理に使用します。

### 軽量タグ

```bash
# 軽量タグの作成
git tag v1.0.0

# 特定のコミットにタグ
git tag v0.9.0 abc123

# タグ一覧
git tag
git tag -l "v1.*"
```

### 注釈付きタグ

```bash
# 注釈付きタグの作成
git tag -a v1.0.0 -m "Release version 1.0.0"

# タグの詳細確認
git show v1.0.0

# GPG署名付きタグ
git tag -s v1.0.0 -m "Signed release v1.0.0"
```

### タグの管理

```bash
# タグのプッシュ
git push origin v1.0.0
git push origin --tags  # 全タグをプッシュ

# タグの削除
git tag -d v1.0.0                    # ローカル
git push origin --delete tag v1.0.0  # リモート

# タグからブランチ作成
git checkout -b hotfix/v1.0.1 v1.0.0
```

## 🎓 学習チェックリスト

この章で学んだ内容を確認しましょう：

### ブランチ操作
- [ ] ブランチの作成・切り替えができる
- [ ] ブランチの削除ができる
- [ ] ブランチ一覧を確認できる
- [ ] リモートブランチを管理できる

### ワークフロー
- [ ] Git Flowの概念を理解している
- [ ] GitHub Flowの手順を実行できる
- [ ] チーム開発のワークフローを理解している
- [ ] リリース管理の流れを把握している

### マージとリベース
- [ ] マージの種類を理解している
- [ ] リベースの概念を理解している
- [ ] 使い分けができる
- [ ] コンフリクトを解決できる

### タグ管理
- [ ] タグの作成・削除ができる
- [ ] 軽量タグと注釈付きタグの違いを理解している
- [ ] タグを使ったリリース管理ができる

## 💡 実践的なヒント

### ブランチ名の付け方

```bash
# 良い例
feature/user-authentication
feature/shopping-cart
hotfix/security-vulnerability
release/v2.1.0

# 避けるべき例
new-stuff
fix
temp
test
```

### コミットメッセージのベストプラクティス

```bash
# 良い例
git commit -m "feat: ユーザー認証API実装"
git commit -m "fix: ログイン時のバリデーションエラー修正"
git commit -m "docs: API仕様書を更新"

# 避けるべき例
git commit -m "修正"
git commit -m "WIP"
git commit -m "いろいろ"
```

### チーム開発のルール例

1. **メインブランチの保護**: 直接プッシュ禁止
2. **Pull Requestの必須**: レビューなしでマージ禁止
3. **CI/CDの統合**: 自動テスト・デプロイ
4. **コミットメッセージ規約**: Conventional Commits準拠

## 🚀 次のステップ

ブランチとワークフローを理解したら、次はチーム開発について学習しましょう！

👉 [04-collaboration.md](./04-collaboration.md) でコラボレーションを学習

---

**🤖 Generated with [Claude Code](https://claude.ai/code)**  
**📅 Last Updated**: 2025年1月  
**🎯 Goal**: 効果的なブランチ戦略とワークフローの習得