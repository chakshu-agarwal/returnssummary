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
    region_name = 'us-east-2',
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


def lambda_handler(event, context):
    body = json.loads(event.get('body', '{}'))
    user_token = body.get("user_token")

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
                'Access-Control-Allow-Origin': 'https://www.returnssummary.com',
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
                'Access-Control-Allow-Origin': 'https://www.returnssummary.com',
                'Access-Control-Allow-Methods': 'POST,OPTIONS,HEAD',
                'Access-Control-Allow-Headers': 'content-type'
            },
            'body': json.dumps({'status': 'error', 'message': 'Failed to retrieve data from DynamoDB'})
        }