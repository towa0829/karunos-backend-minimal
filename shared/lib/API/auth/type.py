from typing import Optional
from pydantic import BaseModel, Field


class AccessUser(BaseModel):
    """Cognito アクセストークンの claims"""
    sub: str
    login_id: str = Field(alias="sub")
    user_type: Optional[str] = Field(default=None, alias="custom:account_type")  # Optional

    class Config:
        populate_by_name = True