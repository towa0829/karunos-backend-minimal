from sqlalchemy.schema import Column, ForeignKey, PrimaryKeyConstraint
from sqlalchemy.types import UUID, INTEGER, BOOLEAN, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy import func
from pydantic import BaseModel
from shared.utils.shema import sqlalchemy_to_pydantic
from models.base import Base

from models.TalentTable import TalentTable

class FeedbackTalentTable(Base):
    __tablename__ = "feedback_talent"

    feedback_id = Column(UUID(as_uuid=True), ForeignKey("job_feedbacks.feedback_id", ondelete="CASCADE"), nullable=False)
    talent_id = Column(INTEGER, ForeignKey("talents.talent_id", ondelete="RESTRICT"), nullable=False)
    is_required = Column(BOOLEAN, nullable=False, default=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    __table_args__ = (
        PrimaryKeyConstraint("feedback_id", "talent_id"),
    )

    feedback = relationship("JobFeedbacksTable", back_populates="talents")
    talent = relationship("TalentTable", back_populates="feedbacks")

FeedbackTalentTableSchema: BaseModel = sqlalchemy_to_pydantic(FeedbackTalentTable)
