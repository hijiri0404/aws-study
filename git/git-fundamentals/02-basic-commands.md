# Git 基本コマンド集

Gitの基本的なコマンドを実際の使用例と共に学習しましょう。各コマンドの動作を理解し、実際に手を動かして覚えることが重要です。

## 📖 目次

1. [初期設定](#初期設定)
2. [リポジトリの作成・取得](#リポジトリの作成取得)
3. [基本的なファイル操作](#基本的なファイル操作)
4. [コミット操作](#コミット操作)
5. [履歴とログ](#履歴とログ)
6. [ブランチ操作](#ブランチ操作)
7. [リモート操作](#リモート操作)
8. [状態確認](#状態確認)

## ⚙️ 初期設定

### 基本設定

Gitを使用する前に、必要な初期設定を行います。

```bash
# ユーザー名の設定
git config --global user.name "田中太郎"

# メールアドレスの設定
git config --global user.email "tanaka@example.com"

# デフォルトエディタの設定（VS Codeの場合）
git config --global core.editor "code --wait"

# デフォルトブランチ名の設定
git config --global init.defaultBranch main
```

### 設定の確認

```bash
# 全設定の確認
git config --list

# 特定の設定の確認
git config user.name
git config user.email

# 設定ファイルの場所
# グローバル設定: ~/.gitconfig
# ローカル設定: <リポジトリ>/.git/config
```

### よく使う設定

```bash
# 日本語ファイル名の文字化け防止
git config --global core.quotepath false

# 改行コードの自動変換（Windows）
git config --global core.autocrlf true

# 改行コードの自動変換（Mac/Linux）
git config --global core.autocrlf input

# カラー表示の有効化
git config --global color.ui auto
```

## 📁 リポジトリの作成・取得

### 新規リポジトリの作成

```bash
# 新しいディレクトリでリポジトリ初期化
mkdir my-project
cd my-project
git init

# または、ディレクトリ作成と同時に初期化
git init my-project
cd my-project
```

### 既存リポジトリのクローン

```bash
# HTTPSでクローン
git clone https://github.com/username/repository.git

# SSHでクローン
git clone git@github.com:username/repository.git

# 別名でクローン
git clone https://github.com/username/repository.git my-app

# 特定のブランチをクローン
git clone -b develop https://github.com/username/repository.git
```

## 📝 基本的なファイル操作

### ファイルの追加・ステージング

```bash
# 特定のファイルを追加
git add index.html
git add src/main.py

# 複数ファイルを一度に追加
git add index.html style.css script.js

# 全てのファイルを追加
git add .
git add -A

# 特定の拡張子のみ追加
git add "*.js"
git add "src/*.py"
```

### ファイルの削除

```bash
# ファイルを削除（ワーキングディレクトリとステージングエリアから）
git rm unwanted-file.txt

# ファイルをステージングエリアからのみ削除（ワーキングディレクトリには残す）
git rm --cached file.txt

# ディレクトリごと削除
git rm -r old-directory/
```

### ファイルの移動・リネーム

```bash
# ファイルの移動
git mv old-name.txt new-name.txt
git mv src/old-file.py src/new-file.py

# ディレクトリの移動
git mv old-dir/ new-dir/
```

## 💾 コミット操作

### 基本的なコミット

```bash
# ステージングエリアの変更をコミット
git commit -m "初回コミット: プロジェクト構造を作成"

# ステージングとコミットを同時実行（追跡済みファイルのみ）
git commit -am "バグ修正: ログイン機能の問題を解決"

# 詳細なコミットメッセージ
git commit -m "機能追加: ユーザー認証システム" -m "- JWT認証を実装\n- ログイン/ログアウト機能を追加\n- パスワードハッシュ化を実装"
```

### コミットメッセージのベストプラクティス

```bash
# 良いコミットメッセージの例
git commit -m "fix: ログインフォームのバリデーションエラーを修正"
git commit -m "feat: ユーザープロフィール編集機能を追加"
git commit -m "docs: READMEにインストール手順を追加"
git commit -m "refactor: データベース接続処理を共通化"

# コミットメッセージの形式（Conventional Commits）
# <type>: <description>
# 
# type例:
# feat: 新機能
# fix: バグ修正
# docs: ドキュメント
# style: フォーマット
# refactor: リファクタリング
# test: テスト
# chore: 雑務
```

### コミットの修正

```bash
# 最新コミットのメッセージを修正
git commit --amend -m "修正されたコミットメッセージ"

# 最新コミットにファイルを追加
git add forgotten-file.txt
git commit --amend --no-edit

# コミット時刻を現在時刻に更新
git commit --amend --date="$(date)"
```

## 📜 履歴とログ

### コミット履歴の確認

```bash
# 基本的なログ表示
git log

# 1行で表示
git log --oneline

# グラフ形式で表示
git log --graph --oneline

# 詳細な統計情報付き
git log --stat

# 特定の期間のログ
git log --since="2 weeks ago"
git log --until="2025-01-01"

# 特定のファイルの変更履歴
git log -- src/main.py
git log -p -- README.md
```

### より詳細なログオプション

```bash
# 美しいログ表示
git log --graph --pretty=format:'%C(yellow)%h%C(reset) %C(cyan)%an%C(reset) %C(green)%ar%C(reset) %s %C(red)%d%C(reset)'

# 特定の作者のコミット
git log --author="田中太郎"

# キーワード検索
git log --grep="バグ修正"

# ファイル内容の変更を表示
git log -p

# マージコミットを除外
git log --no-merges
```

### 差分の確認

```bash
# ワーキングディレクトリとステージングエリアの差分
git diff

# ステージングエリアと最新コミットの差分
git diff --cached
git diff --staged

# 特定のコミット間の差分
git diff HEAD~1 HEAD
git diff abc123..def456

# 特定のファイルの差分
git diff HEAD~1 src/main.py
```

## 🌿 ブランチ操作

### ブランチの作成と切り替え

```bash
# ブランチ一覧の表示
git branch
git branch -r  # リモートブランチも表示
git branch -a  # 全ブランチを表示

# 新しいブランチを作成
git branch feature/user-login
git branch hotfix/urgent-bug

# ブランチの切り替え
git checkout feature/user-login

# ブランチ作成と切り替えを同時実行
git checkout -b feature/new-feature
git switch -c feature/another-feature  # Git 2.23以降
```

### ブランチの管理

```bash
# ブランチの削除
git branch -d feature/completed-feature  # マージ済みブランチ
git branch -D feature/abandoned-feature  # 強制削除

# ブランチ名の変更
git branch -m old-name new-name
git branch -m feature/login feature/user-authentication

# リモートブランチの削除
git push origin --delete feature/old-branch
```

### マージ操作

```bash
# mainブランチに切り替え
git checkout main

# feature/user-loginブランチをマージ
git merge feature/user-login

# 早送りマージの無効化（マージコミットを作成）
git merge --no-ff feature/user-login

# マージ前のプレビュー
git merge --no-commit --no-ff feature/user-login
# 確認後に実際にマージ
git commit
```

## 🌐 リモート操作

### リモートリポジトリの管理

```bash
# リモートリポジトリの一覧
git remote
git remote -v  # URL付きで表示

# リモートリポジトリの追加
git remote add origin https://github.com/username/repository.git
git remote add upstream https://github.com/original/repository.git

# リモートリポジトリの削除
git remote remove old-remote

# リモートリポジトリのURL変更
git remote set-url origin https://github.com/username/new-repository.git
```

### プッシュとプル

```bash
# リモートリポジトリにプッシュ
git push origin main
git push origin feature/user-login

# 初回プッシュ（上流ブランチの設定）
git push -u origin main
git push --set-upstream origin feature/new-feature

# 全ブランチをプッシュ
git push origin --all

# タグもプッシュ
git push origin --tags
```

```bash
# リモートリポジトリから取得
git pull origin main

# フェッチ（マージはしない）
git fetch origin
git fetch --all

# 特定のブランチを取得
git pull origin develop

# リベースしながらプル
git pull --rebase origin main
```

## 📊 状態確認

### ワーキングディレクトリの状態

```bash
# 現在の状態を確認
git status

# 簡潔な表示
git status -s
git status --short

# 無視されたファイルも表示
git status --ignored
```

### ファイルの詳細情報

```bash
# 特定のコミットの詳細
git show HEAD
git show abc123

# 特定のファイルの内容を表示
git show HEAD:src/main.py
git show abc123:README.md

# 現在のブランチの確認
git branch --show-current
git symbolic-ref --short HEAD
```

## 🔧 よく使うコマンドの組み合わせ

### 日常的なワークフロー

```bash
# 1. 最新の変更を取得
git pull origin main

# 2. 新しいブランチで作業開始
git checkout -b feature/new-feature

# 3. ファイルを編集後、変更を確認
git status
git diff

# 4. 変更をステージング
git add .

# 5. コミット
git commit -m "feat: 新機能を追加"

# 6. リモートにプッシュ
git push -u origin feature/new-feature
```

### 効率的なエイリアス設定

```bash
# よく使うコマンドのエイリアス設定
git config --global alias.st status
git config --global alias.co checkout
git config --global alias.br branch
git config --global alias.ci commit
git config --global alias.unstage 'reset HEAD --'
git config --global alias.last 'log -1 HEAD'
git config --global alias.visual '!gitk'

# 使用例
git st        # git status
git co main   # git checkout main
git br        # git branch
git ci -m "メッセージ"  # git commit -m "メッセージ"
```

## 🎓 学習チェックリスト

この章で学んだコマンドを確認しましょう：

### 基本操作
- [ ] `git init`でリポジトリを初期化できる
- [ ] `git clone`でリポジトリを複製できる
- [ ] `git add`でファイルをステージングできる
- [ ] `git commit`で変更をコミットできる

### ブランチ操作
- [ ] `git branch`でブランチを作成できる
- [ ] `git checkout/switch`でブランチを切り替えられる
- [ ] `git merge`でブランチをマージできる

### リモート操作
- [ ] `git push`でリモートにアップロードできる
- [ ] `git pull`でリモートから取得できる
- [ ] `git fetch`で情報のみ取得できる

### 状態確認
- [ ] `git status`で現在の状態を確認できる
- [ ] `git log`でコミット履歴を確認できる
- [ ] `git diff`で変更内容を確認できる

## 💡 実践的なヒント

### コマンドを覚えるコツ
1. **毎日使う**: 基本的なコマンドを日常的に使用
2. **エイリアス活用**: よく使うコマンドは短縮形を設定
3. **ヘルプ確認**: `git help <command>`で詳細を確認
4. **チートシート**: 手元に基本コマンド一覧を用意

### よくあるミス
- **`git add .`の注意**: 意図しないファイルも追加される可能性
- **コミットメッセージ**: 後で理解できる具体的な内容を記述
- **ブランチ確認**: 作業前に正しいブランチにいるか確認
- **プッシュ前確認**: `git status`で状態を確認してからプッシュ

## 🚀 次のステップ

基本コマンドを覚えたら、次はブランチとワークフローを学習しましょう！

👉 [03-branching-workflow.md](./03-branching-workflow.md) でブランチ戦略を学習

---

**🤖 Generated with [Claude Code](https://claude.ai/code)**  
**📅 Last Updated**: 2025年1月  
**🎯 Goal**: 実践的なGitコマンドの習得