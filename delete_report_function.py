import logging
logging.basicConfig(level=logging.INFO)

import json
import os
import boto3
from botocore.client import Config
from botocore.exceptions import ClientError
from botocore.exceptions import NoCredentialsError

bucket_name = os.environ.get('AWS_S3_BUCKET_NAME')
pickle_bucket_name = os.environ.get('PICKLE_S3_BUCKET_NAME')

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
    'https://returnssummary.cc',
    'https://www.returnssummary.cc',
    'https://www.returnssummary.com',
    'https://rr-split-chakshu-agarwals-projects.vercel.app',
    'http://localhost:3000'  # For local development
]

def lambda_handler(event, context):
    body = json.loads(event.get('body', '{}'))
    object_name = body.get("object_name")
    user_token = body.get("user_token")

    # Get the origin from the request headers
    origin = event.get('headers', {}).get('Origin') or event.get('headers', {}).get('origin')

    # Check if the origin is allowed
    if origin not in ALLOWED_ORIGINS:
        origin = ALLOWED_ORIGINS[0]  # Default to the first allowed origin if not matched

    # Extract s3 pickle_name from object_name
    if user_token is None:
        start = len("returns_summary_")
        end = object_name.index(".csv")
        pickle_name = object_name[start:end]
        s3_file_name = "robinhood" + pickle_name + ".pickle"
        # Try to delete pickle file from S3
        try:
            s3_client.delete_object(Bucket=pickle_bucket_name, Key=s3_file_name)
            pass
        except ClientError as e:
            logging.error('Error in deleting pickle file: %s', e, exc_info=True)
    
    # Delete CSV from S3
    try:
        s3_client.delete_object(Bucket=bucket_name, Key=object_name)
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': origin,
                'Access-Control-Allow-Methods': 'POST,OPTIONS,HEAD',
                'Access-Control-Allow-Headers': 'content-type'
            },
            'body': json.dumps({'status': 'success', 'message': 'File deleted successfully'})
        }
    except ClientError as e:
        # logging.error(e)
        return {
            'statusCode': 500,
            'headers': {
                'Access-Control-Allow-Origin': origin,
                'Access-Control-Allow-Methods': 'POST,OPTIONS,HEAD',
                'Access-Control-Allow-Headers': 'content-type'
            },
            'body': json.dumps({'status': 'error', 'message': 'Failed to delete file'})
        }