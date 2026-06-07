from sqlalchemy.schema import Column
from sqlalchemy.types import (
    UUID,
    TEXT,
    TIMESTAMP,
    INTEGER,
    DateTime
)
from sqlalchemy import func
from pydantic import BaseModel

from shared.utils.security import gen_uuid7
from shared.utils.shema import sqlalchemy_to_pydantic
from models.base import Base

class DreamerTable(Base):
    __tablename__ = "dreamers"

    dreamer_id = Column(UUID(as_uuid=True), primary_key=True, default=gen_uuid7)
    organization_id = Column(INTEGER, index=True)
    login_id = Column(TEXT, nullable=False, index=True)
    name_family = Column(TEXT, nullable=False)
    name_given = Column(TEXT, nullable=False)
    last_login_at = Column(TIMESTAMP)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

DreamerTableSchema: BaseModel = sqlalchemy_to_pydantic(DreamerTable)