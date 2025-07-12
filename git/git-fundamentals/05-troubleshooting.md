# Gitトラブルシューティング

Gitを使用していると様々な問題に遭遇します。よくある問題とその解決方法を学習し、自信を持ってGitを使いこなせるようになりましょう。

## 📖 目次

1. [一般的なエラーと対処法](#一般的なエラーと対処法)
2. [コミット関連の問題](#コミット関連の問題)
3. [ブランチ・マージの問題](#ブランチマージの問題)
4. [リモート関連の問題](#リモート関連の問題)
5. [パフォーマンスの問題](#パフォーマンスの問題)
6. [データ復旧](#データ復旧)

## ⚠️ 一般的なエラーと対処法

### 「Permission denied」エラー

#### 症状
```bash
git push origin main
# Permission denied (publickey).
# fatal: Could not read from remote repository.
```

#### 原因と対処法

**1. SSH鍵の設定不備**
```bash
# SSH鍵の確認
ls -la ~/.ssh/
# id_rsa, id_rsa.pub が存在するか確認

# SSH鍵の生成（存在しない場合）
ssh-keygen -t ed25519 -C "your-email@example.com"

# SSH鍵をGitHubに追加
cat ~/.ssh/id_ed25519.pub
# 出力された公開鍵をGitHubのSettings > SSH and GPG keysに追加
```

**2. SSH接続テスト**
```bash
# GitHub接続テスト
ssh -T git@github.com
# Hi username! You've successfully authenticated...

# GitLab接続テスト
ssh -T git@gitlab.com
```

**3. HTTPSの使用（代替案）**
```bash
# SSH → HTTPS に変更
git remote set-url origin https://github.com/username/repository.git

# GitHubのPersonal Access Tokenを使用
# Settings > Developer settings > Personal access tokensで生成
```

### 「fatal: not a git repository」エラー

#### 症状
```bash
git status
# fatal: not a git repository (or any of the parent directories): .git
```

#### 対処法
```bash
# 現在のディレクトリを確認
pwd

# Gitリポジトリかどうか確認
ls -la | grep .git

# リポジトリ初期化（新規の場合）
git init

# 正しいディレクトリに移動（既存の場合）
cd /path/to/your/repository
```

### 「You have unstaged changes」エラー

#### 症状
```bash
git checkout main
# error: Your local changes to the following files would be overwritten by checkout:
#   file.txt
# Please commit your changes or stash them before you switch branches.
```

#### 対処法

**1. 変更をコミット**
```bash
git add .
git commit -m "作業中の変更を保存"
git checkout main
```

**2. 変更を一時保存（stash）**
```bash
git stash
git checkout main
# 必要に応じて変更を復元
git stash pop
```

**3. 変更を破棄**
```bash
# 注意：変更が完全に失われます
git checkout -- .
git checkout main
```

## 📝 コミット関連の問題

### 間違ったファイルをコミットした

#### ファイルをコミットから除外

```bash
# 最新コミットからファイルを除外
git reset --soft HEAD~1
git reset HEAD unwanted-file.txt
git commit -m "修正されたコミット"

# または、amendを使用
git reset HEAD~1 unwanted-file.txt
git commit --amend
```

#### 機密情報をコミットした

```bash
# ⚠️ 重要：リモートにプッシュ前の場合
git reset --hard HEAD~1

# ⚠️ プッシュ済みの場合（force pushが必要）
git filter-branch --force --index-filter \
  'git rm --cached --ignore-unmatch secret-file.txt' \
  --prune-empty --tag-name-filter cat -- --all

# すべてのリモートに強制プッシュ
git push origin --force --all
```

### コミットメッセージの修正

#### 最新コミットのメッセージ修正

```bash
git commit --amend -m "修正されたコミットメッセージ"
```

#### 古いコミットのメッセージ修正

```bash
# 直近3つのコミットを修正
git rebase -i HEAD~3

# エディタで 'pick' を 'edit' に変更
# 各コミットで以下を実行
git commit --amend -m "新しいメッセージ"
git rebase --continue
```

### 複数のコミットを統合

```bash
# 直近3つのコミットを統合
git rebase -i HEAD~3

# エディタで2番目以降を 'squash' に変更
# pick abc123 first commit
# squash def456 second commit
# squash ghi789 third commit
```

## 🌿 ブランチ・マージの問題

### ブランチ切り替えができない

#### 症状
```bash
git checkout feature-branch
# error: pathspec 'feature-branch' did not match any file(s) known to git
```

#### 対処法

**1. ブランチ存在確認**
```bash
# ローカルブランチ確認
git branch

# リモートブランチ確認
git branch -r

# 全ブランチ確認
git branch -a
```

**2. リモートブランチの取得**
```bash
# リモート情報更新
git fetch origin

# リモートブランチをローカルに作成
git checkout -b feature-branch origin/feature-branch
```

### マージコンフリクトの解決

#### 基本的な解決手順

```bash
# マージ実行
git merge feature-branch
# Auto-merging file.txt
# CONFLICT (content): Merge conflict in file.txt

# コンフリクトファイルの確認
git status
# Unmerged paths:
#   both modified: file.txt

# ファイル内容の確認と編集
cat file.txt
# <<<<<<< HEAD
# Current branch content
# =======
# Feature branch content
# >>>>>>> feature-branch

# 手動で修正後
git add file.txt
git commit -m "resolve: file.txtのコンフリクトを解決"
```

#### マージツールの使用

```bash
# マージツールの設定
git config --global merge.tool vimdiff

# マージツールの起動
git mergetool

# 人気のマージツール
# - VS Code: `code --wait`
# - KDiff3: `kdiff3`
# - Meld: `meld`
```

### 間違ったマージの取り消し

```bash
# マージコミット直後の場合
git reset --hard HEAD~1

# マージコミットのハッシュが分かっている場合
git reset --hard <commit-before-merge>

# 安全な方法（revert使用）
git revert -m 1 <merge-commit-hash>
```

## 🌐 リモート関連の問題

### プッシュが拒否される

#### 症状
```bash
git push origin main
# ! [rejected] main -> main (fetch first)
# error: failed to push some refs to 'origin'
```

#### 対処法

**1. リモートの変更を取得**
```bash
# 安全な方法
git fetch origin
git merge origin/main
git push origin main

# または pull を使用
git pull origin main
git push origin main
```

**2. リベースを使用**
```bash
git pull --rebase origin main
git push origin main
```

**3. 強制プッシュ（注意が必要）**
```bash
# ⚠️ 他の開発者の作業を上書きする可能性
git push --force-with-lease origin main

# さらに危険（非推奨）
git push --force origin main
```

### リモートブランチの同期問題

#### リモートブランチが削除されている

```bash
# 削除されたリモートブランチの情報をクリーンアップ
git remote prune origin

# または
git fetch --prune origin

# 対応するローカルブランチも削除
git branch -d feature-branch
```

#### アップストリームブランチの設定

```bash
# 現在のブランチにアップストリームを設定
git branch --set-upstream-to=origin/main main

# プッシュ時に設定
git push -u origin feature-branch
```

## ⚡ パフォーマンスの問題

### リポジトリサイズが大きい

#### ファイル履歴から大きなファイルを削除

```bash
# 大きなファイルを特定
git rev-list --objects --all | grep "$(git verify-pack -v .git/objects/pack/*.idx | sort -k 3 -nr | head -10 | awk '{print$1}')"

# BFG Repo-Cleanerを使用（推奨）
# https://rtyley.github.io/bfg-repo-cleaner/
bfg --strip-blobs-bigger-than 50M

# 手動での削除（高度）
git filter-branch --force --index-filter \
  'git rm --cached --ignore-unmatch large-file.bin' \
  --prune-empty --tag-name-filter cat -- --all
```

#### ガベージコレクション

```bash
# 不要なオブジェクトをクリーンアップ
git gc --aggressive --prune=now

# リポジトリの整合性確認
git fsck --full
```

### Git操作が遅い

#### 設定の最適化

```bash
# プリロードの有効化
git config core.preloadindex true

# ファイルシステム監視の有効化
git config core.fsmonitor true

# 並列処理の設定
git config submodule.fetchJobs 4
```

#### 部分クローンの使用

```bash
# 浅いクローン（履歴を制限）
git clone --depth 1 https://github.com/user/repo.git

# 特定のブランチのみ
git clone --single-branch --branch main https://github.com/user/repo.git

# 大きなファイルを除外
git clone --filter=blob:limit=1m https://github.com/user/repo.git
```

## 🔧 データ復旧

### 削除したコミットの復旧

#### reflogを使用した復旧

```bash
# 操作履歴の確認
git reflog

# 特定のコミットに戻る
git reset --hard HEAD@{2}

# または
git reset --hard <commit-hash>
```

#### 削除したブランチの復旧

```bash
# 削除したブランチのコミットハッシュを特定
git reflog | grep feature-branch

# ブランチを再作成
git checkout -b feature-branch <commit-hash>
```

### 削除したファイルの復旧

#### まだコミットしていない場合

```bash
# 特定のファイルを復元
git checkout HEAD -- deleted-file.txt

# 全てのファイルを復元
git checkout HEAD -- .
```

#### コミット済みの場合

```bash
# 特定のコミットからファイルを復元
git checkout <commit-hash> -- deleted-file.txt

# 削除コミットを特定
git log --oneline --follow -- deleted-file.txt

# 削除前のコミットから復元
git checkout <commit-before-deletion> -- deleted-file.txt
```

### stashの復旧

```bash
# stash一覧の確認
git stash list

# 特定のstashを復元
git stash apply stash@{2}

# stashの詳細確認
git stash show -p stash@{1}

# 削除したstashの復旧（reflog使用）
git fsck --no-reflog | awk '/dangling commit/ {print $3}' | xargs git log --oneline -1
```

## 🎓 学習チェックリスト

この章で学んだトラブルシューティングを確認しましょう：

### 基本的なエラー対応
- [ ] Permission deniedエラーを解決できる
- [ ] SSH鍵の設定・確認ができる
- [ ] 「not a git repository」エラーを解決できる
- [ ] unstaged changesエラーを対処できる

### コミット問題の解決
- [ ] 間違ったコミットを修正できる
- [ ] コミットメッセージを修正できる
- [ ] 複数のコミットを統合できる
- [ ] 機密情報の漏洩に対処できる

### ブランチ・マージ問題
- [ ] コンフリクトを解決できる
- [ ] 間違ったマージを取り消せる
- [ ] ブランチ切り替え問題を解決できる

### データ復旧
- [ ] 削除したコミットを復旧できる
- [ ] 削除したファイルを復元できる
- [ ] reflogを活用できる

## 🚨 予防策とベストプラクティス

### 事前予防策

#### 1. バックアップの習慣

```bash
# 定期的なリモートプッシュ
git push origin --all
git push origin --tags

# 重要な作業前のstash
git stash push -m "作業開始前の保存"
```

#### 2. 設定の最適化

```bash
# 自動改行変換（Windows）
git config --global core.autocrlf true

# 日本語ファイル名対応
git config --global core.quotepath false

# エディタ設定
git config --global core.editor "code --wait"
```

#### 3. .gitignoreの活用

```gitignore
# OS固有
.DS_Store
Thumbs.db

# IDE/エディタ
.vscode/
.idea/
*.swp

# 言語固有
node_modules/
__pycache__/
*.pyc

# 機密情報
.env
config/secrets.yml
```

### 危険な操作への注意

#### ⚠️ 避けるべきコマンド

```bash
# 公開ブランチでの強制プッシュ
git push --force origin main  # 危険

# より安全な代替
git push --force-with-lease origin main

# 公開履歴の書き換え
git rebase -i origin/main  # 危険（ローカルのみにする）

# 完全な削除
git reset --hard HEAD~5  # 慎重に実行
```

## 💡 実践的なヒント

### トラブル対応の手順

1. **現状把握**: `git status`, `git log --oneline`
2. **バックアップ**: 重要な作業は事前にstash
3. **情報収集**: エラーメッセージを正確に読む
4. **段階的解決**: 小さな変更から試す
5. **確認**: 解決後の状態を確認

### 有用なツール

```bash
# Git状態の可視化
git log --graph --oneline --all

# 差分の確認
git diff --color-words

# インタラクティブなadd
git add -i

# ファイル内検索
git grep "検索文字列"

# 変更者の確認
git blame filename.txt
```

## 🚀 まとめ

Gitのトラブルシューティングは経験を積むことで上達します。重要なポイント：

1. **慌てない**: ほとんどの問題は解決可能
2. **reflogを活用**: Git履歴の強力な味方
3. **段階的アプローチ**: 小さな変更から試す
4. **予防策の実践**: .gitignore、定期バックアップ
5. **チーム共有**: 解決方法をドキュメント化

継続的な学習と実践で、Gitを安全かつ効率的に使いこなせるようになります！

---

**🤖 Generated with [Claude Code](https://claude.ai/code)**  
**📅 Last Updated**: 2025年1月  
**🎯 Goal**: 実践的なGitトラブルシューティングスキルの習得