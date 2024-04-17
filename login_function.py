import robin_stocks.robinhood as r
import logging
import json

logging.basicConfig(level=logging.INFO)

def lambda_handler(event, context):
    body = json.loads(event.get('body', '{}'))
    username = body.get('username')
    password = body.get('password')
    mfa_code = body.get('mfa_code')
    user_token = body.get("user_token")

    if mfa_code == '':
        mfa_code = None

    try:
        r.authentication.login(username, password, mfa_code=mfa_code, expiresIn=3600, pickle_name=user_token)
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': 'https://www.returnssummary.com',
                'Access-Control-Allow-Methods': 'POST,OPTIONS,HEAD',
                'Access-Control-Allow-Headers': 'content-type'
            },
            'body': json.dumps({'status': 'success', 'message': 'Login successful'})
        }
    except Exception as e:
        logging.error("Error in login function: %s", e, exc_info=True)
        return {
            'statusCode': 404,
            'headers': {
                'Access-Control-Allow-Origin': 'https://www.returnssummary.com',
                'Access-Control-Allow-Methods': 'POST,OPTIONS,HEAD',
                'Access-Control-Allow-Headers': 'content-type'
            },
            'body': json.dumps({'status': 'error', 'message': str(e)})
        }
