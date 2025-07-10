# AWS Lambda Functions for Novel Downloader Service

import json
import boto3
import os
from datetime import datetime
import uuid
from enhanced_downloader import EnhancedNovelDownloader

# DynamoDB and SQS clients
dynamodb = boto3.resource('dynamodb')
sqs = boto3.client('sqs')
s3 = boto3.client('s3')

# Environment variables
WORKS_TABLE = os.environ['WORKS_TABLE_NAME']
DOWNLOADS_TABLE = os.environ['DOWNLOADS_TABLE_NAME']
DOWNLOAD_QUEUE_URL = os.environ['DOWNLOAD_QUEUE_URL']
S3_BUCKET = os.environ['S3_BUCKET_NAME']

def api_handler(event, context):
    """
    API Gateway からのリクエストを処理するメインハンドラー
    """
    try:
        # リクエストの解析
        http_method = event['httpMethod']
        path = event['path']
        
        if http_method == 'POST' and path == '/api/download':
            return handle_download_request(event, context)
        elif http_method == 'GET' and '/api/status/' in path:
            return handle_status_request(event, context)
        elif http_method == 'GET' and path == '/api/works':
            return handle_works_list(event, context)
        else:
            return {
                'statusCode': 404,
                'headers': {
                    'Access-Control-Allow-Origin': '*',
                    'Content-Type': 'application/json'
                },
                'body': json.dumps({'error': 'Not Found'})
            }
            
    except Exception as e:
        print(f"Error in api_handler: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Content-Type': 'application/json'
            },
            'body': json.dumps({'error': 'Internal Server Error'})
        }

def handle_download_request(event, context):
    """
    ダウンロードリクエストの処理
    """
    try:
        # リクエストボディの解析
        body = json.loads(event['body'])
        work_id = body.get('work_id')
        user_id = event['requestContext']['authorizer']['user_id']
        
        if not work_id:
            return {
                'statusCode': 400,
                'headers': {'Access-Control-Allow-Origin': '*'},
                'body': json.dumps({'error': '作品IDが必要です'})
            }
        
        # ダウンロードタスクID生成
        task_id = str(uuid.uuid4())
        
        # DynamoDBにダウンロード記録を作成
        downloads_table = dynamodb.Table(DOWNLOADS_TABLE)
        downloads_table.put_item(
            Item={
                'user_id': user_id,
                'task_id': task_id,
                'work_id': work_id,
                'status': 'pending',
                'progress': 0,
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            }
        )
        
        # SQSにダウンロードタスクを送信
        message_body = {
            'task_id': task_id,
            'work_id': work_id,
            'user_id': user_id,
            'timestamp': datetime.now().isoformat(),
            'options': body.get('options', {})
        }
        
        sqs.send_message(
            QueueUrl=DOWNLOAD_QUEUE_URL,
            MessageBody=json.dumps(message_body),
            MessageAttributes={
                'TaskType': {
                    'StringValue': 'download',
                    'DataType': 'String'
                }
            }
        )
        
        return {
            'statusCode': 202,
            'headers': {'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({
                'message': 'ダウンロードを開始しました',
                'task_id': task_id,
                'work_id': work_id
            })
        }
        
    except Exception as e:
        print(f"Error in handle_download_request: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({'error': 'ダウンロード開始に失敗しました'})
        }

def handle_status_request(event, context):
    """
    ダウンロード状況の確認
    """
    try:
        # パスパラメータからタスクIDを取得
        task_id = event['pathParameters']['task_id']
        user_id = event['requestContext']['authorizer']['user_id']
        
        # DynamoDBからステータスを取得
        downloads_table = dynamodb.Table(DOWNLOADS_TABLE)
        response = downloads_table.get_item(
            Key={
                'user_id': user_id,
                'task_id': task_id
            }
        )
        
        if 'Item' not in response:
            return {
                'statusCode': 404,
                'headers': {'Access-Control-Allow-Origin': '*'},
                'body': json.dumps({'error': 'タスクが見つかりません'})
            }
        
        item = response['Item']
        
        # レスポンスの構築
        status_response = {
            'task_id': task_id,
            'work_id': item['work_id'],
            'status': item['status'],
            'progress': item['progress'],
            'created_at': item['created_at'],
            'updated_at': item['updated_at']
        }
        
        # ダウンロード完了時にファイルURLを追加
        if item['status'] == 'completed' and 'file_key' in item:
            status_response['download_url'] = generate_presigned_url(item['file_key'])
        
        # エラー情報がある場合は追加
        if 'error_message' in item:
            status_response['error_message'] = item['error_message']
        
        return {
            'statusCode': 200,
            'headers': {'Access-Control-Allow-Origin': '*'},
            'body': json.dumps(status_response)
        }
        
    except Exception as e:
        print(f"Error in handle_status_request: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({'error': 'ステータス確認に失敗しました'})
        }

def handle_works_list(event, context):
    """
    作品一覧の取得
    """
    try:
        user_id = event['requestContext']['authorizer']['user_id']
        
        # DynamoDBから作品一覧を取得
        downloads_table = dynamodb.Table(DOWNLOADS_TABLE)
        response = downloads_table.query(
            IndexName='user-id-index',
            KeyConditionExpression='user_id = :user_id',
            ExpressionAttributeValues={
                ':user_id': user_id
            },
            ScanIndexForward=False,  # 新しい順
            Limit=50
        )
        
        works = []
        for item in response['Items']:
            work = {
                'task_id': item['task_id'],
                'work_id': item['work_id'],
                'status': item['status'],
                'progress': item['progress'],
                'created_at': item['created_at']
            }
            
            if item['status'] == 'completed' and 'file_key' in item:
                work['download_url'] = generate_presigned_url(item['file_key'])
            
            works.append(work)
        
        return {
            'statusCode': 200,
            'headers': {'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({'works': works})
        }
        
    except Exception as e:
        print(f"Error in handle_works_list: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({'error': '作品一覧の取得に失敗しました'})
        }

def download_processor(event, context):
    """
    SQSからのメッセージを処理してダウンロードを実行
    """
    try:
        for record in event['Records']:
            # SQSメッセージの解析
            message_body = json.loads(record['body'])
            task_id = message_body['task_id']
            work_id = message_body['work_id']
            user_id = message_body['user_id']
            options = message_body.get('options', {})
            
            print(f"Processing download task: {task_id} for work: {work_id}")
            
            # ステータスを"processing"に更新
            update_download_status(user_id, task_id, 'processing', 0)
            
            try:
                # ダウンローダーを初期化
                downloader = EnhancedNovelDownloader(
                    work_id=work_id,
                    output_dir='/tmp',
                    start_chapter=options.get('start_chapter', 1),
                    end_chapter=options.get('end_chapter'),
                    force_update=options.get('force_update', False)
                )
                
                # 作品情報を取得
                downloader.get_novel_info()
                
                # プログレスコールバック関数を定義
                def progress_callback(current, total):
                    progress = int((current / total) * 100)
                    update_download_status(user_id, task_id, 'processing', progress)
                
                # ダウンロード実行（プログレスコールバック付き）
                downloader.download_all_with_progress(progress_callback)
                
                # S3にファイルをアップロード
                file_key = f"downloads/{user_id}/{task_id}/{work_id}_{downloader.novel_title}.txt"
                s3.upload_file(
                    downloader.output_file,
                    S3_BUCKET,
                    file_key,
                    ExtraArgs={'ContentType': 'text/plain; charset=utf-8'}
                )
                
                # ステータスを"completed"に更新
                update_download_status(user_id, task_id, 'completed', 100, file_key=file_key)
                
                print(f"Download completed: {task_id}")
                
            except Exception as e:
                print(f"Download failed for task {task_id}: {str(e)}")
                update_download_status(user_id, task_id, 'failed', 0, error_message=str(e))
                
    except Exception as e:
        print(f"Error in download_processor: {str(e)}")
        raise

def update_download_status(user_id, task_id, status, progress, file_key=None, error_message=None):
    """
    ダウンロードステータスの更新
    """
    try:
        downloads_table = dynamodb.Table(DOWNLOADS_TABLE)
        
        update_expression = "SET #status = :status, progress = :progress, updated_at = :updated_at"
        expression_attribute_names = {"#status": "status"}
        expression_attribute_values = {
            ":status": status,
            ":progress": progress,
            ":updated_at": datetime.now().isoformat()
        }
        
        if file_key:
            update_expression += ", file_key = :file_key"
            expression_attribute_values[":file_key"] = file_key
        
        if error_message:
            update_expression += ", error_message = :error_message"
            expression_attribute_values[":error_message"] = error_message
        
        downloads_table.update_item(
            Key={
                'user_id': user_id,
                'task_id': task_id
            },
            UpdateExpression=update_expression,
            ExpressionAttributeNames=expression_attribute_names,
            ExpressionAttributeValues=expression_attribute_values
        )
        
    except Exception as e:
        print(f"Error updating download status: {str(e)}")

def generate_presigned_url(file_key, expiration=3600):
    """
    S3ファイルの署名付きURLを生成
    """
    try:
        url = s3.generate_presigned_url(
            'get_object',
            Params={'Bucket': S3_BUCKET, 'Key': file_key},
            ExpiresIn=expiration
        )
        return url
    except Exception as e:
        print(f"Error generating presigned URL: {str(e)}")
        return None

# Cognito Authorizer for API Gateway
def cognito_authorizer(event, context):
    """
    Cognito JWTトークンの検証
    """
    try:
        import jwt
        import requests
        
        # JWTトークンの取得
        token = event['authorizationToken'].replace('Bearer ', '')
        
        # Cognito公開キーの取得とトークン検証
        # 実装は省略（boto3.client('cognito-idp')使用）
        
        # 検証成功時のポリシー生成
        policy = {
            "principalId": "user_id_from_token",
            "policyDocument": {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Action": "execute-api:Invoke",
                        "Effect": "Allow",
                        "Resource": event['methodArn']
                    }
                ]
            },
            "context": {
                "user_id": "user_id_from_token"
            }
        }
        
        return policy
        
    except Exception as e:
        print(f"Authorization failed: {str(e)}")
        raise Exception('Unauthorized')