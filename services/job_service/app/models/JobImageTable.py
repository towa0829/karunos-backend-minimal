from sqlalchemy.schema import Column, ForeignKey
from sqlalchemy.types import INTEGER, TEXT, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy import func
from pydantic import BaseModel
from shared.utils.shema import sqlalchemy_to_pydantic
from models.base import Base

class JobImageTable(Base):
    __tablename__ = "job_images"

    img_id = Column(INTEGER, primary_key=True, autoincrement=True)
    job_id = Column(INTEGER, ForeignKey("jobs.job_id", ondelete="RESTRICT"), nullable=False)
    img_url = Column(TEXT, nullable=False)
    alt = Column(TEXT, nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    job = relationship("JobsTable", back_populates="images")

JobImageTableSchema: BaseModel = sqlalchemy_to_pydantic(JobImageTable)
