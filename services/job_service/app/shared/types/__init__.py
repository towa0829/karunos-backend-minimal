from pydantic import BaseModel, Field
from typing import List, Optional

class BaseFig(BaseModel):
    is_need: bool = Field(..., description="図表が必要か（True）・不必要か（False）")
    message: List[str] = Field(..., description="具体的にどのような図表が必要なのか。数字なども含めてできるだけ具体的に記載するようにしてください。")

    class Config:
        description = "図表"
        extra = "forbid"

class BaseElementGenerateSchema(BaseModel):
    title: str = Field(..., description="構成要素のタイトル")
    text: str = Field(..., description="構成要素の本文章。スタイル要件に従って生成してください")
    fig: BaseFig

    class Config:
        description = "構成要素"
        extra = "forbid" 

class BaseElementSchema(BaseModel):
    title: str
    text: str
    fig_urls: List[str]

    class Config:
        extra = "forbid" 

class AnswerSchema(BaseModel):
    answer: str = Field(..., description="問題に対す答え。スタイル要件に従って生成してください")
    explanation: str = Field(..., description="問題に対する解説文章。スタイル要件に従って生成してください")
    fig: BaseFig

    class Config:
        description = "解答と解説"
        extra = "forbid" 