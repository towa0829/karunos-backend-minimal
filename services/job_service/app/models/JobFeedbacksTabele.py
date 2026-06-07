from sqlalchemy.schema import Column, ForeignKey
from sqlalchemy.types import UUID, INTEGER, TEXT, BOOLEAN, REAL, TIME, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy import func
from pydantic import BaseModel
from shared.utils.security import gen_uuid7
from shared.utils.shema import sqlalchemy_to_pydantic
from models.base import Base

from models.FeedbackSkillTable import FeedbackSkillTable
from models.FeedbackCertificationTable import FeedbackCertificationTable
from models.FeedbackCompanyTable import FeedbackCompanyTable
from models.FeedbackTalentTable import FeedbackTalentTable
from models.FeedbackInterestTable import FeedbackInterestTable

class JobFeedbacksTable(Base):
    __tablename__ = "job_feedbacks"

    feedback_id = Column(UUID(as_uuid=True), primary_key=True, default=gen_uuid7)
    job_id = Column(INTEGER, ForeignKey("jobs.job_id", ondelete="CASCADE"), nullable=False)
    salary = Column(INTEGER)
    level = Column(INTEGER)
    end_time = Column(TIME)
    holiday = Column(INTEGER)
    overtime_hours = Column(INTEGER)
    age = Column(INTEGER)
    tenure_years = Column(INTEGER)
    marriage_age = Column(INTEGER)
    gender_ratio = Column(REAL)
    romance_rate = Column(REAL)
    social_signification = Column(TEXT)
    personality_traits = Column(TEXT)
    growth_opportunities = Column(TEXT)
    wrong_image = Column(TEXT)
    uniform = Column(BOOLEAN)
    work_life_balance = Column(REAL)
    future_outlook = Column(TEXT)
    rarity = Column(REAL)
    scandal_history = Column(TEXT)
    focus_on_education = Column(BOOLEAN)
    focus_on_achievements = Column(BOOLEAN)
    appeal_points = Column(TEXT)
    daily_routine = Column(TEXT)
    comments = Column(TEXT)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    job = relationship("JobsTable", back_populates="feedback")

    # ✅ 多対多リレーション（中間テーブル経由）
    skills = relationship("FeedbackSkillTable", back_populates="feedback", cascade="all, delete-orphan")
    certifications = relationship("FeedbackCertificationTable", back_populates="feedback", cascade="all, delete-orphan")
    companies = relationship("FeedbackCompanyTable", back_populates="feedback", cascade="all, delete-orphan")
    talents = relationship("FeedbackTalentTable", back_populates="feedback", cascade="all, delete-orphan")
    interests = relationship("FeedbackInterestTable", back_populates="feedback", cascade="all, delete-orphan")

JobFeedbackTableSchema: BaseModel = sqlalchemy_to_pydantic(JobFeedbacksTable)
