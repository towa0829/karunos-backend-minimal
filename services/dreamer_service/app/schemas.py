from pydantic import BaseModel, Field, ConfigDict
from uuid import UUID
from typing import List, Optional

# Dreamer Schemas
class NewDreamerRequest(BaseModel):
    organization_id: Optional[int] = Field(None, description = "団体ID")
    name_family: str = Field(..., description = "苗字")
    name_given: str = Field(..., description = "名前")

class NewDreamerResponse(BaseModel):
    dreamer_id: UUID = Field(..., description = "dreamer ID")
    
    model_config = ConfigDict(from_attributes=True)

class UpdateDreamerRequest(BaseModel):
    organization_id: int = Field(None, description = "団体ID")
    name_family: str = Field(None, description = "苗字")
    name_given: str = Field(None, description = "名前")

class DreamerGroupSummary(BaseModel): #サブモデル
    name: str = Field(..., description = "グループ名")
    group_id: UUID = Field(..., description = "グループID")

class DreamerResponse(BaseModel):
    dreamer_id: UUID = Field(..., description = "dreamer ID")
    login_id: str = Field(..., description = "ログイン用ID")
    organization_id: int = Field(..., description = "団体ID")
    name_family: str = Field(..., description = "苗字")
    name_given: str = Field(..., description = "名前")
    groups: List[DreamerGroupSummary] = Field(
        default_factory = list,
        description = "所属しているdreamerのグループ概要リスト"
    )

    model_config = ConfigDict(from_attributes=True)

    
#Dreamer Group Schemas
class NewDreamerGroupRequest(BaseModel):
    name: str = Field(..., description = "グループ名")
    description: Optional[str] = Field(None, description = "グループの説明")
    dreamers: List[UUID] = Field(
        default_factory = list,
        description = "初期所属のdreamerのIDリスト")

class NewDreamerGroupResponse(BaseModel):
    group_id: UUID =Field(..., description = "グループID")

    model_config = ConfigDict(from_attributes=True)


class DreamerInGroup(BaseModel): #サブモデル
    name: str = Field(..., description = "dreamer名")
    dreamer_id: UUID = Field(..., description = "dreamer ID")

class DreamerGroupResponse(BaseModel):
    name: str = Field(..., description = "グループ名")
    description: Optional[str] = Field(None, description = "グループの説明")
    dreamers: List[DreamerInGroup] = Field(
        default_factory = list,
        description = "所属しているdreamerの一覧"
        )

    model_config = ConfigDict(from_attributes=True)

class UpdateDreamerGroupRequest(BaseModel):
    name: str = Field(None, description = "グループ名")
    description: str = Field(None, description = "グループの説明")

#Dreamer to Group
class DreamerToGroupRequest(BaseModel):
    dreamers: List[UUID] = Field(..., description = "更新したいdreamer IDのリスト")
    
class DreamerToGroupResponse(BaseModel):
    dreamers: List[UUID] = Field(..., description = "更新後のdreamer IDのリスト")

    model_config = ConfigDict(from_attributes=True)