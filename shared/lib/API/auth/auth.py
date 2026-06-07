import os

from fastapi_cloudauth.cognito import Cognito

auth = Cognito(
    region = os.getenv("COGNITO_REGION"),
    userPoolId = os.getenv("COGNITO_USERPOOL_ID"),
    client_id = os.getenv("COGNITO_APP_CLIENT_ID"),
)