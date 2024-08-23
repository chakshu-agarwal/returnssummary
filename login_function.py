import robin_stocks.robinhood as r
import logging
import json

logging.basicConfig(level=logging.INFO)

# List of allowed origins
ALLOWED_ORIGINS = [
    'https://rr-frontend-psi.vercel.app',
    'https://www.returnssummary.com',
    'https://rr-split-chakshu-agarwals-projects.vercel.app',
    'http://localhost:3000'  # For local development
]

def lambda_handler(event, context):
    body = json.loads(event.get('body', '{}'))
    username = body.get('username')
    password = body.get('password')
    mfa_code = body.get('mfa_code')
    user_token = body.get("user_token")

    # Get the origin from the request headers
    origin = event.get('headers', {}).get('Origin') or event.get('headers', {}).get('origin')

    # Check if the origin is allowed
    if origin not in ALLOWED_ORIGINS:
        origin = ALLOWED_ORIGINS[0]  # Default to the first allowed origin if not matched


    if mfa_code == '':
        mfa_code = None

    try:
        r.authentication.login(username, password, mfa_code=mfa_code, expiresIn=3600, pickle_name=user_token)
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': origin,
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
                'Access-Control-Allow-Origin': origin,
                'Access-Control-Allow-Methods': 'POST,OPTIONS,HEAD',
                'Access-Control-Allow-Headers': 'content-type'
            },
            'body': json.dumps({'status': 'error', 'message': str(e)})
        }
