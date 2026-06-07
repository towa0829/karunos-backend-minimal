from sqlalchemy.schema import Column
from sqlalchemy.types import INTEGER, TEXT
from pydantic import BaseModel
from shared.utils.shema import sqlalchemy_to_pydantic
from models.base import Base

class JobCategoryTable(Base):
    __tablename__ = "job_categories"

    category_id = Column(INTEGER, primary_key=True, autoincrement=True)
    name = Column(TEXT, nullable=False, unique=True)
    description = Column(TEXT)

JobCategoryTableSchema: BaseModel = sqlalchemy_to_pydantic(JobCategoryTable)
