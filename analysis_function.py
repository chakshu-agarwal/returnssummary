import robin_stocks.robinhood as r
from robinhood_data_research_copy import final_results
import json
import os
from io import StringIO
import pandas as pd

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


def generate_presigned_url(bucket, s3_file_name):
    try:
        response = s3_client.generate_presigned_url(ClientMethod='get_object',
                                             Params={'Bucket': bucket,
                                                     'Key': s3_file_name},
                                             ExpiresIn=3600)
        return response
    except ClientError as e:
        return None

# List of allowed origins
ALLOWED_ORIGINS = [
    'https://rr-frontend-psi.vercel.app',
    'https://www.returnssummary.com',
    'https://rr-split-chakshu-agarwals-projects.vercel.app',
    'http://localhost:3000'  # For local development
]

def lambda_handler(event, context):
    start_date = event.get('start_date')
    end_date = event.get('end_date')
    user_token = event.get('user_token')

    # Get the origin from the request headers
    origin = event.get('headers', {}).get('Origin') or event.get('headers', {}).get('origin')

    # Check if the origin is allowed
    if origin not in ALLOWED_ORIGINS:
        origin = ALLOWED_ORIGINS[0]  # Default to the first allowed origin if not matched

    # Login to Robinhood using pickle file 
    try:
        r.authentication.login(pickle_name=user_token)
        pass
    except Exception as e:
        logging.error("Error in login function: %s", e, exc_info=True)  
        return {
            'statusCode': 404,
            'headers': {
                'Access-Control-Allow-Origin': origin,
                'Access-Control-Allow-Methods': 'POST,OPTIONS,HEAD',
                'Access-Control-Allow-Headers': 'content-type'
            },
            'body': json.dumps({'status': 'Login Timeout:', 'message': 'Please login again.'})
        }

    table.put_item(
        Item={
            'user_token': user_token,
            'analysis_status': 'Pending',
            'analysis_results': {}
        }
    )
    
    try:
        # Run analysis and upload CSV to S3
        analysis_response = final_results(start_date, end_date)
        summary = analysis_response['message']['summary']

        csv_buffer = StringIO()
        summary.to_csv(csv_buffer, index=False)
        csv_buffer.seek(0)
        object_name = f'returns_summary_{user_token}.csv' #if sanitized_email_address else f'returns_summary_{random_string}.csv'
        # Upload CSV to S3
        s3_client.put_object(Bucket=bucket_name, Key=object_name, Body=csv_buffer.getvalue())

        if analysis_response['status'] == 'success':
            response_message = analysis_response['message']
            response_message.pop('summary', None)
            response_message['file_url'] = generate_presigned_url(bucket_name, object_name)
            response_message['object_name'] = object_name
            # Update DynamoDB table with results
            table.update_item(
                Key={'user_token': user_token},
                UpdateExpression='set analysis_status=:s, analysis_results=:r',
                ExpressionAttributeValues={
                    ':s': 'Success',
                    ':r': response_message
                }
            )
            return {
                'statusCode': 200,
                'body': json.dumps(response_message)
            }
        else:
            table.update_item(
                Key={'user_token': user_token},
                UpdateExpression='set analysis_status=:s, analysis_results=:r',
                ExpressionAttributeValues={
                    ':s': 'Failure',
                    ':r': analysis_response['message']
                }
            )
            return {
                'statusCode': 500,
                'body': json.dumps({'status': 'error', 'message': analysis_response['message']})
            }
    except Exception as e:
        logging.error("Error in analysis function: %s", e, exc_info=True)
        table.update_item(
            Key={'user_token': user_token},
            UpdateExpression='set analysis_status=:s, analysis_results=:r',
            ExpressionAttributeValues={
                ':s': 'Failure',
                ':r': str(e)
            }
        )
        return {
            'statusCode': 500,
            'body': json.dumps({'status': 'error', 'message': str(e)})
        }
