from sqlalchemy.schema import Column, ForeignKey, PrimaryKeyConstraint
from sqlalchemy.types import UUID, INTEGER, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy import func
from pydantic import BaseModel
from shared.utils.shema import sqlalchemy_to_pydantic
from models.base import Base

from models.CompanyTable import CompanyTable

class FeedbackCompanyTable(Base):
    __tablename__ = "feedback_company"

    feedback_id = Column(UUID(as_uuid=True), ForeignKey("job_feedbacks.feedback_id", ondelete="CASCADE"), nullable=False)
    company_id = Column(INTEGER, ForeignKey("companies.company_id", ondelete="RESTRICT"), nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    __table_args__ = (
        PrimaryKeyConstraint("feedback_id", "company_id"),
    )

    feedback = relationship("JobFeedbacksTable", back_populates="companies")
    company = relationship("CompanyTable", back_populates="feedbacks")

FeedbackCompanyTableSchema: BaseModel = sqlalchemy_to_pydantic(FeedbackCompanyTable)
