import json

import logging
logging.basicConfig(level=logging.INFO)

import os
import boto3
from botocore.client import Config
from botocore.exceptions import NoCredentialsError

bucket_name = os.environ.get('PICKLE_S3_BUCKET_NAME')

my_config = Config(
    region_name = 'us-east-2',
    signature_version = 's3v4'
)

try:
    s3_client = boto3.client(
        's3',
        config=my_config
    )
except NoCredentialsError:
    print("AWS Log In Issue")


def lambda_handler(event, context):
    body = json.loads(event.get('body', '{}'))
    pickle_name = body.get('user_token')
    s3_file_name = "robinhood" + pickle_name + ".pickle"

    try:
        s3_client.delete_object(Bucket=bucket_name, Key=s3_file_name)
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': 'https://www.returnssummary.com',
                'Access-Control-Allow-Methods': 'POST,OPTIONS,HEAD',
                'Access-Control-Allow-Headers': 'content-type'
            },
            'body': json.dumps({'status': 'success', 'message': 'Deleted Pickle'})
        }
    except Exception as e:
        logging.error("Error in logout function: %s", e, exc_info=True)
        return {
            'statusCode': 500,
            'headers': {
                'Access-Control-Allow-Origin': 'https://www.returnssummary.com',
                'Access-Control-Allow-Methods': 'POST,OPTIONS,HEAD',
                'Access-Control-Allow-Headers': 'content-type'
            },
            'body': json.dumps({'status': 'error', 'message': str(e)})
        }