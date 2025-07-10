# API Handler Lambda Function
import json
import boto3
import os
from datetime import datetime

def lambda_handler(event, context):
    """API Gateway requests handler"""
    
    return {
        'statusCode': 200,
        'headers': {
            'Access-Control-Allow-Origin': '*',
            'Content-Type': 'application/json'
        },
        'body': json.dumps({
            'message': 'API Handler is working',
            'timestamp': datetime.now().isoformat()
        })
    }