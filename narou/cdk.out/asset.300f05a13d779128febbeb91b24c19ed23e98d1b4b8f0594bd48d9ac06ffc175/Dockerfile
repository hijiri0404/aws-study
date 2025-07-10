# 小説ダウンローダー用Docker イメージ
# Python 3.11ベースのスリムイメージを使用
FROM python:3.11-slim

# 作業ディレクトリの設定
WORKDIR /app

# システムパッケージの更新とpipアップグレード
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        curl \
        ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && pip install --upgrade pip

# Pythonの依存関係ファイルをコピー
COPY requirements.txt .

# Python依存関係のインストール
RUN pip install --no-cache-dir -r requirements.txt

# アプリケーションコードをコピー
COPY app/ .

# 非rootユーザーを作成
RUN useradd --create-home --shell /bin/bash app && \
    chown -R app:app /app
USER app

# ヘルスチェック用エンドポイント
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# ポート8080を公開
EXPOSE 8080

# アプリケーション起動コマンド
CMD ["python", "novel_downloader_service.py"]