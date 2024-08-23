import json

import logging
logging.basicConfig(level=logging.INFO)

import os
import boto3
from botocore.client import Config
from botocore.exceptions import ClientError
from botocore.exceptions import NoCredentialsError

bucket_name = os.environ.get('PICKLE_S3_BUCKET_NAME')
results_bucket_name = os.environ.get('AWS_S3_BUCKET_NAME')

my_config = Config(
    region_name = 'us-east-1',
    signature_version = 's3v4'
)

try:
    s3_client = boto3.client(
        's3',
        config=my_config
    )
except NoCredentialsError:
    print("AWS Log In Issue")

# List of allowed origins
ALLOWED_ORIGINS = [
    'https://rr-frontend-psi.vercel.app',
    'https://www.returnssummary.com',
    'https://rr-split-chakshu-agarwals-projects.vercel.app',
    'http://localhost:3000'  # For local development
]

def lambda_handler(event, context):
    pickle_name = event.get('user_token')
    s3_file_name = "robinhood" + pickle_name + ".pickle"
    object_name = f'returns_summary_{pickle_name}.csv'

    if object_name:
        try:
            s3_client.delete_object(Bucket=results_bucket_name, Key=object_name)
        except ClientError as e:
            logging.error('Error in deleting object: %s', e, exc_info=True)

    # Get the origin from the request headers
    origin = event.get('headers', {}).get('Origin') or event.get('headers', {}).get('origin')

    # Check if the origin is allowed
    if origin not in ALLOWED_ORIGINS:
        origin = ALLOWED_ORIGINS[0]  # Default to the first allowed origin if not matched

    try:
        s3_client.delete_object(Bucket=bucket_name, Key=s3_file_name)
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': origin,
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
                'Access-Control-Allow-Origin': origin,
                'Access-Control-Allow-Methods': 'POST,OPTIONS,HEAD',
                'Access-Control-Allow-Headers': 'content-type'
            },
            'body': json.dumps({'status': 'error', 'message': str(e)})
        }