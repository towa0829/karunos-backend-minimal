from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from shared.lib.API.auth.auth import auth
from shared.lib.API.auth.type import AccessUser
from shared.lib.API.client import Client

# Extract raw Bearer token for forwarding to other services
security = HTTPBearer()

def get_bearer_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    return credentials.credentials

# Base dependency: validate Cognito token and extract claims
get_access_user = auth.claim(AccessUser)

# Composed dependency: authenticate with Cognito, then fetch user info
def get_current_user(
    user: AccessUser = Depends(get_access_user),
    token: str = Depends(get_bearer_token),
):
    """Authenticate with Cognito and return downstream user data.

    - login_id = Cognito `sub`
    - forwards the original Bearer token to downstream service
    """
    login_id = user.login_id  # equals user.sub
    user_type = user.user_type or None  # default to dreamer if not set
    
    api = Client(key=token)
    
    # Call appropriate service based on user_type
    if user_type == "mentor":
        ok, data, err = api.get(f"http://mentor-service:8000/api/v1/admin/{login_id}")
        data["user_type"] = "mentor"
        data["id"] = data["mentor_id"]
    else:
        ok, data, err = api.get(f"http://dreamer-service:8000/api/v1/admin/{login_id}")
        data["user_type"] = "dreamer"
        data["id"] = data["dreamer_id"]
    
    if not ok:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(err))
    
    return data
