import robin_stocks.robinhood as r
import json
import os

import logging
logging.basicConfig(level=logging.INFO)

import boto3
from botocore.client import Config
from botocore.exceptions import ClientError
from botocore.exceptions import NoCredentialsError

table_name = os.environ.get('RESULTS_TABLE')

try:
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(table_name)
except NoCredentialsError:
    print("No table found in DynamoDB")

lambdaClient = boto3.client('lambda')

# List of allowed origins
ALLOWED_ORIGINS = [
    'https://rr-frontend-psi.vercel.app',
    'https://returnssummary.cc',
    'https://www.returnssummary.cc',
    'https://www.returnssummary.com',
    'https://rr-split-chakshu-agarwals-projects.vercel.app',
    'http://localhost:3000'  # For local development
]

def lambda_handler(event, context):
    body = json.loads(event.get('body', '{}'))
    end_date = body.get('end_date')
    start_date = body.get('start_date')
    user_token = body.get("user_token")

    payload = {
        'start_date': start_date,
        'end_date': end_date,
        'user_token': user_token
    }

     # Get the origin from the request headers
    origin = event.get('headers', {}).get('Origin') or event.get('headers', {}).get('origin')

    # Check if the origin is allowed
    if origin not in ALLOWED_ORIGINS:
        origin = ALLOWED_ORIGINS[0]  # Default to the first allowed origin if not matched


    response = lambdaClient.invoke(
        FunctionName=os.environ.get('CHILD_FUNCTION'),
        InvocationType='Event',
        Payload=json.dumps(payload),
    )

    if response['StatusCode'] != 202:
        logging.error('Error invoking second Lambda function: %s', response)
        return {
            'statusCode': 500,
            'headers': {
                'Access-Control-Allow-Origin': origin,
                'Access-Control-Allow-Methods': 'POST,OPTIONS,HEAD',
                'Access-Control-Allow-Headers': 'content-type'
            },
            'body': json.dumps({'status': 'Lambda Error:', 'message': 'Error invoking second Lambda function'})
        }
    
    return {
        'statusCode': 200,
        'headers': {
            'Access-Control-Allow-Origin': origin,
            'Access-Control-Allow-Methods': 'POST,OPTIONS,HEAD',
            'Access-Control-Allow-Headers': 'content-type'
        },
        'body': json.dumps({'status': 'success', 'message': 'Lambda invocation started'})
    }
