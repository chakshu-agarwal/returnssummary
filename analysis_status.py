import json
import os
import decimal

import logging
logging.basicConfig(level=logging.INFO)

import boto3
from botocore.client import Config
from botocore.exceptions import ClientError
from botocore.exceptions import NoCredentialsError

bucket_name = os.environ.get('AWS_S3_BUCKET_NAME')
table_name = os.environ.get('RESULTS_TABLE')

my_config = Config(
    region_name = 'us-east-1',
    signature_version = 's3v4'
)

try:
    s3_client = boto3.client(
        's3',
        config=my_config
    )
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(table_name)
except NoCredentialsError:
    print("AWS Log In Issue")


# DynamoDB stores numerical values as Decimal objects. This class converts Decimal objects to float for JSON serialization
class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, decimal.Decimal):
            return float(obj)
        return super(DecimalEncoder, self).default(obj)

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
    user_token = body.get("user_token")

    # Get the origin from the request headers
    origin = event.get('headers', {}).get('Origin') or event.get('headers', {}).get('origin')

    # Check if the origin is allowed
    if origin not in ALLOWED_ORIGINS:
        origin = ALLOWED_ORIGINS[0]  # Default to the first allowed origin if not matched

    # CHeck if the table has data for the user_token. If not, return status pending. If yes, return the Result
    try:
        response = table.get_item(Key={'user_token': user_token})
        item = response.get('Item', {})
        status = item.get('analysis_status', 'Pending')
        result = item.get('analysis_results', {})
        # if status == 'Success', delete the dynamodb item
        if status == 'Success':
            table.delete_item(Key={'user_token': user_token})
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': origin,
                'Access-Control-Allow-Methods': 'POST,OPTIONS,HEAD',
                'Access-Control-Allow-Headers': 'content-type'
            },
            'body': json.dumps({'status': status, 'message': result}, cls=DecimalEncoder)
        }
    except ClientError as e:
        logging.error(e)
        return {
            'statusCode': 500,
            'headers': {
                'Access-Control-Allow-Origin': origin,
                'Access-Control-Allow-Methods': 'POST,OPTIONS,HEAD',
                'Access-Control-Allow-Headers': 'content-type'
            },
            'body': json.dumps({'status': 'error', 'message': 'Failed to retrieve data from DynamoDB'})
        }