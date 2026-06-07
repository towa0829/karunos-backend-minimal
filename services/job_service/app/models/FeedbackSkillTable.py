from sqlalchemy.schema import Column, ForeignKey, PrimaryKeyConstraint
from sqlalchemy.types import UUID, INTEGER, BOOLEAN, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy import func
from pydantic import BaseModel
from shared.utils.shema import sqlalchemy_to_pydantic
from models.base import Base

from models.SkillTable import SkillTable

class FeedbackSkillTable(Base):
    __tablename__ = "feedback_skill"

    feedback_id = Column(UUID(as_uuid=True), ForeignKey("job_feedbacks.feedback_id", ondelete="CASCADE"), nullable=False)
    skill_id = Column(INTEGER, ForeignKey("skills.skill_id", ondelete="RESTRICT"), nullable=False)
    is_required = Column(BOOLEAN, nullable=False, default=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    __table_args__ = (
        PrimaryKeyConstraint("feedback_id", "skill_id"),
    )

    feedback = relationship("JobFeedbacksTable", back_populates="skills")
    skill = relationship("SkillTable", back_populates="feedbacks")

FeedbackSkillTableSchema: BaseModel = sqlalchemy_to_pydantic(FeedbackSkillTable)
