from sqlalchemy.schema import Column
from sqlalchemy.types import INTEGER, TEXT
from sqlalchemy.orm import relationship
from pydantic import BaseModel
from shared.utils.shema import sqlalchemy_to_pydantic
from models.base import Base

class InterestTable(Base):
    __tablename__ = "interests"

    interest_id = Column(INTEGER, primary_key=True, autoincrement=True)
    name = Column(TEXT, nullable=False, unique=True)

    feedbacks = relationship("FeedbackInterestTable", back_populates="interest")

InterestTableSchema: BaseModel = sqlalchemy_to_pydantic(InterestTable)
