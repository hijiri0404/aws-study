#!/usr/bin/env python3
"""
小説ダウンローダーサービス
ECS Fargate用のコンテナ化されたサービス
"""

import os
import time
import json
import logging
from flask import Flask, request, jsonify
from threading import Thread
import boto3
from novel_downloader import NovelDownloader

# ログ設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Flaskアプリケーション初期化
app = Flask(__name__)

# AWS SDKクライアント初期化
dynamodb = boto3.resource('dynamodb')
sqs = boto3.client('sqs')
s3 = boto3.client('s3')

class NovelDownloaderService:
    """小説ダウンローダーサービスクラス"""
    
    def __init__(self):
        self.downloads_table = dynamodb.Table(os.environ['DOWNLOADS_TABLE_NAME'])
        self.works_table = dynamodb.Table(os.environ['WORKS_TABLE_NAME'])
        self.queue_url = os.environ['DOWNLOAD_QUEUE_URL']
        self.bucket_name = os.environ['DOWNLOADS_BUCKET_NAME']
    
    def process_download_request(self, work_url, user_id, task_id):
        """ダウンロード要求を処理"""
        try:
            logger.info(f"Starting download for task {task_id}")
            
            # タスクステータスを実行中に更新
            self.downloads_table.update_item(
                Key={'user_id': user_id, 'task_id': task_id},
                UpdateExpression='SET #status = :status, updated_at = :timestamp',
                ExpressionAttributeNames={'#status': 'status'},
                ExpressionAttributeValues={
                    ':status': 'running',
                    ':timestamp': int(time.time())
                }
            )
            
            # 小説ダウンローダーを実行
            downloader = NovelDownloader()
            result = downloader.download_novel(work_url)
            
            # 完成したファイルをS3にアップロード
            file_key = f"downloads/{user_id}/{task_id}/novel.txt"
            s3.upload_file(result['output_file'], self.bucket_name, file_key)
            
            # タスクステータスを完了に更新
            self.downloads_table.update_item(
                Key={'user_id': user_id, 'task_id': task_id},
                UpdateExpression='SET #status = :status, file_url = :url, completed_at = :timestamp',
                ExpressionAttributeNames={'#status': 'status'},
                ExpressionAttributeValues={
                    ':status': 'completed',
                    ':url': f"s3://{self.bucket_name}/{file_key}",
                    ':timestamp': int(time.time())
                }
            )
            
            logger.info(f"Download completed for task {task_id}")
            
        except Exception as e:
            logger.error(f"Download failed for task {task_id}: {str(e)}")
            
            # エラー状態に更新
            self.downloads_table.update_item(
                Key={'user_id': user_id, 'task_id': task_id},
                UpdateExpression='SET #status = :status, error_message = :error, updated_at = :timestamp',
                ExpressionAttributeNames={'#status': 'status'},
                ExpressionAttributeValues={
                    ':status': 'failed',
                    ':error': str(e),
                    ':timestamp': int(time.time())
                }
            )

# サービスインスタンス作成
service = NovelDownloaderService()

@app.route('/health', methods=['GET'])
def health_check():
    """ヘルスチェックエンドポイント"""
    return jsonify({'status': 'healthy', 'timestamp': int(time.time())})

@app.route('/download', methods=['POST'])
def download_novel():
    """小説ダウンロード要求エンドポイント"""
    data = request.get_json()
    
    work_url = data.get('work_url')
    user_id = data.get('user_id')
    task_id = data.get('task_id')
    
    if not all([work_url, user_id, task_id]):
        return jsonify({'error': 'Missing required parameters'}), 400
    
    # バックグラウンドタスクとして実行
    thread = Thread(
        target=service.process_download_request,
        args=(work_url, user_id, task_id)
    )
    thread.start()
    
    return jsonify({
        'message': 'Download started',
        'task_id': task_id,
        'status': 'queued'
    })

@app.route('/status/<task_id>', methods=['GET'])
def get_status(task_id):
    """タスクステータス取得エンドポイント"""
    user_id = request.args.get('user_id')
    
    if not user_id:
        return jsonify({'error': 'Missing user_id parameter'}), 400
    
    try:
        response = service.downloads_table.get_item(
            Key={'user_id': user_id, 'task_id': task_id}
        )
        
        if 'Item' not in response:
            return jsonify({'error': 'Task not found'}), 404
        
        return jsonify(response['Item'])
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # 本番環境ではGunicorn使用、開発時はFlask組み込みサーバー使用
    port = int(os.environ.get('PORT', 8080))
    
    if os.environ.get('FLASK_ENV') == 'development':
        app.run(host='0.0.0.0', port=port, debug=True)
    else:
        from gunicorn.app.wsgiapp import WSGIApplication
        
        class StandaloneApplication(WSGIApplication):
            def __init__(self, app, options=None):
                self.options = options or {}
                self.application = app
                super().__init__()
            
            def load_config(self):
                for key, value in self.options.items():
                    self.cfg.set(key.lower(), value)
            
            def load(self):
                return self.application
        
        options = {
            'bind': f'0.0.0.0:{port}',
            'workers': 2,
            'timeout': 300,
            'keepalive': 2,
        }
        
        StandaloneApplication(app, options).run()