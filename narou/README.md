# 小説家になろう 拡張版ダウンローダー

「小説家になろう」の作品を効率的にダウンロードするPythonスクリプトです。

![License](https://img.shields.io/badge/license-Personal%20Use-blue)
![Python](https://img.shields.io/badge/python-3.7+-green)
![Platform](https://img.shields.io/badge/platform-Linux%20%7C%20macOS%20%7C%20Windows-lightgrey)

## ✨ 主な特徴

### 🚀 **スマートダウンロード**
- **初回**: 作品の全章を自動取得
- **2回目以降**: 新章・未取得章のみを自動検出してダウンロード
- **既存章スキップ**: ダウンロード済みの章は自動的にスキップ

### 📊 **作品別進捗管理**
- 作品ごとに独立した進捗管理
- ダウンロード履歴の記録
- 失敗章の自動記録・再試行対応

### 🔍 **自動情報取得**
- 作品タイトル・作者名の自動取得
- 総章数の自動検出
- WEB側更新日の記録

### 📁 **整理されたファイル管理**
- 作品IDと作品名を含むファイル名
- 日付付きファイル（重複防止）
- データベースファイルは別フォルダで管理

---

## 🚀 クイックスタート

### 1. 環境準備
```bash
# 必要なライブラリをインストール
pip3 install beautifulsoup4 requests
```

### 2. 基本的な使い方
```bash
# 作品を初回ダウンロード
python3 enhanced_downloader.py n2627t

# 更新チェック（2回目以降）
python3 enhanced_downloader.py n2627t

# 進捗確認
python3 enhanced_downloader.py n2627t --status
```

---

## 📖 詳細な使い方

### 🎯 **Step 1: 作品IDの確認**

1. 「小説家になろう」で読みたい作品のページにアクセス
2. URLから作品IDを確認
   ```
   https://ncode.syosetu.com/n2627t/
                            ^^^^^^ ← これが作品ID
   ```

### 🚀 **Step 2: 初回ダウンロード**

```bash
python3 enhanced_downloader.py n2627t
```

**実行例の出力:**
```
作品情報取得中: https://ncode.syosetu.com/n2627t/
作品名: 黒の魔王
作者: 菱影代理
検出章数: 100章

小説ダウンロード開始: 黒の魔王
第1章完了: プロローグ
進捗: 1/100 (1.0%) | 失敗: 0
...
処理完了!
出力ファイル: n2627t_黒の魔王_20250707.txt
```

### 🔄 **Step 3: 更新チェック（2回目以降）**

```bash
python3 enhanced_downloader.py n2627t
```

**更新がある場合:**
```
🆕 新章発見: 20章追加されています
今回ダウンロード: 20章（第101-120章のみ）
既存章: 100章スキップ
```

**更新がない場合:**
```
✅ 更新なし（全章ダウンロード済み）
ダウンロードをスキップします
```

### 📊 **Step 4: 進捗確認**

```bash
python3 enhanced_downloader.py n2627t --status
```

**出力例:**
```
=== 作品状態: 黒の魔王 ===
作品ID: n2627t
作者: 菱影代理
総章数: 120章
完了章数: 120章
失敗章数: 0章
初回DL: 2025-01-07
最終DL: 2025-01-07

ダウンロード履歴:
  1. 2025-01-07 - 100章取得
  2. 2025-01-07 - 20章取得
```

---

## 🎛️ 実用的な使用パターン

### パターン1: 定期的な更新チェック
```bash
# 複数作品をまとめて更新チェック（個別実行）
python3 enhanced_downloader.py n2627t
python3 enhanced_downloader.py n5455cx
python3 enhanced_downloader.py n7069ds

# ワンライナー（一括実行）
for work in n2627t n5455cx n7069ds; do python3 enhanced_downloader.py "$work"; done
```

### パターン2: 途中から読み始める
```bash
# 第50章から最新章まで取得
python3 enhanced_downloader.py n2627t --start 50

# 第100-200章のみ取得
python3 enhanced_downloader.py n2627t --start 100 --end 200
```

### パターン3: 特定章の再取得
```bash
# 失敗章がある場合の強制再取得
python3 enhanced_downloader.py n2627t --force
```

### パターン4: バックグラウンド実行
```bash
# 長時間取得をバックグラウンドで実行
nohup python3 enhanced_downloader.py n2627t > download.log 2>&1 &

# 進捗確認
tail -f download.log
```

---

## 📝 コマンド一覧

| コマンド | 説明 | 使用例 |
|----------|------|--------|
| `python3 enhanced_downloader.py [作品ID]` | 基本実行（更新チェック・新章取得） | `python3 enhanced_downloader.py n2627t` |
| `--status` | 作品状態表示 | `python3 enhanced_downloader.py n2627t --status` |
| `--start N` | 開始章指定 | `python3 enhanced_downloader.py n2627t --start 50` |
| `--end N` | 終了章指定 | `python3 enhanced_downloader.py n2627t --end 100` |
| `--force` | 強制再取得 | `python3 enhanced_downloader.py n2627t --force` |
| `--output-dir PATH` | 出力先指定 | `python3 enhanced_downloader.py n2627t --output-dir /novels` |

---

## 📁 ファイル構成

```
narou/
├── enhanced_downloader.py              # メインプログラム
├── README.md                           # このファイル
├── n2627t_黒の魔王_20250707.txt         # ダウンロードファイル
├── n5455cx_インフィニット・デンドログラム_20250707.txt
└── data/                               # データ管理フォルダ
    ├── novels_database.json            # 全作品管理データベース
    ├── progress_n2627t.json            # 作品別進捗ファイル
    └── progress_n5455cx.json
```

---

## 🔧 トラブルシューティング

### よくある問題と解決法

| 問題 | 原因 | 解決法 |
|------|------|--------|
| **ダウンロードが途中で止まる** | ネットワークエラー | 同じコマンドを再実行（自動レジューム） |
| **HTTP 403エラー** | アクセス制限 | しばらく時間をおいてから再実行 |
| **章が見つからない** | 指定章数が無効 | `--status`で実際の章数を確認 |
| **ファイルが重複している** | 日付の異なるファイル | 古いファイルを手動削除 |

### デバッグ用コマンド

```bash
# ファイルサイズの確認
ls -lh n2627t_*.txt

# 章数の確認
grep -c "^第.*章" n2627t_*.txt

# エラーログの確認（バックグラウンド実行時）
tail -f download.log
```

---

## 🛠️ 技術的詳細

### 処理フロー

#### 初回実行時
```
作品情報取得 → タイトル・章数検出 → データベース記録 → 
全章ダウンロード → 進捗保存 → ファイル出力
```

#### 2回目以降
```
既存データ読み込み → WEB情報取得 → 更新チェック → 
新章のみダウンロード → 進捗更新 → ファイル出力
```

### 使用技術
- **Python 3.7+**
- **BeautifulSoup4**: HTMLパース・要素抽出
- **requests**: HTTP通信
- **JSON**: データベース管理

### サイト負荷への配慮
- 章ごとに2.5秒の待機時間
- 適切なUser-Agent設定
- 失敗時の自動再試行制限

---

## 📚 対応作品例

| 作品ID | 作品名 | 使用例 |
|--------|--------|--------|
| `n7069ds` | 五つの塔の頂へ | `python3 enhanced_downloader.py n7069ds` |
| `n2627t` | 黒の魔王 | `python3 enhanced_downloader.py n2627t` |
| `n5455cx` | インフィニット・デンドログラム | `python3 enhanced_downloader.py n5455cx` |
| `n4830bu` | 無職転生 | `python3 enhanced_downloader.py n4830bu` |
| `n6316bn` | 転生したらスライムだった件 | `python3 enhanced_downloader.py n6316bn` |

---

## 💡 活用のヒント

### 定期実行の設定（cron）
```bash
# 毎日午前2時に更新チェック
# crontab -e で以下を追加
0 2 * * * cd /path/to/narou && python3 enhanced_downloader.py n2627t >> /var/log/novel_update.log 2>&1
```

### 複数作品の一括管理

#### ワンライナー（簡単）
```bash
# 基本の一括実行
for work in n2627t n5455cx n7069ds; do python3 enhanced_downloader.py "$work"; done

# 詳細な出力付き
for work in n2627t n5455cx n7069ds; do echo "=== $work 更新チェック ==="; python3 enhanced_downloader.py "$work"; echo ""; done

# 状態確認のみ（一括）
for work in n2627t n5455cx n7069ds; do python3 enhanced_downloader.py "$work" --status; echo ""; done

# エラー時も継続実行
for work in n2627t n5455cx n7069ds; do python3 enhanced_downloader.py "$work" || echo "$work でエラー発生"; done
```

#### スクリプトファイル（高機能）
```bash
#!/bin/bash
# update_novels.sh - 複数作品更新スクリプト
works=("n2627t" "n5455cx" "n7069ds")
for work in "${works[@]}"; do
    echo "=== $work の更新チェック開始 ==="
    python3 enhanced_downloader.py "$work"
    echo ""
done
```

### 読書環境との連携
```bash
# Kindleなどの電子書籍リーダーへの転送
# テキストファイルをepub形式に変換
pandoc n2627t_黒の魔王_20250707.txt -o 黒の魔王.epub
```

---

## ⚖️ 利用規約・注意事項

### 📜 ライセンス
このプログラムは個人利用目的で作成されています。

### ⚠️ 重要な注意事項
- ダウンロードした作品の著作権は各作者に帰属します
- 商用利用や二次配布は禁止されています  
- 「小説家になろう」の利用規約を遵守してご使用ください
- サイトに過度な負荷をかけないよう適切にご利用ください
- 本プログラムの使用により生じた問題について、作者は責任を負いません

### 📞 サポート
- バグ報告や機能要望は Issues でお知らせください
- 使い方に関する質問も歓迎します

---

**Happy Reading! 📚✨**

> 素晴らしい物語との出会いが、あなたの人生を豊かにしますように。