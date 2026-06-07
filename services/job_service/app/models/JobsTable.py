from sqlalchemy.schema import Column, ForeignKey
from sqlalchemy.types import INTEGER, TEXT, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy import func
from pydantic import BaseModel
from shared.utils.shema import sqlalchemy_to_pydantic
from models.base import Base


def _safe_getattr(obj, attr, default=None):
    try:
        return getattr(obj, attr)
    except Exception:
        return default

from models.JobImageTable import JobImageTable
from models.JobFeedbacksTabele import JobFeedbacksTable
from models.HistoryTable import HistoryTable    

class JobsTable(Base):
    __tablename__ = "jobs"

    job_id = Column(INTEGER, primary_key=True, autoincrement=True)
    industry_id = Column(INTEGER, ForeignKey("industries.industry_id", ondelete="RESTRICT"), nullable=False)
    category_id = Column(INTEGER, ForeignKey("job_categories.category_id", ondelete="RESTRICT"), nullable=False)
    name = Column(TEXT, nullable=False)
    description = Column(TEXT)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    images = relationship("JobImageTable", back_populates="job", cascade="all, delete-orphan")
    feedback = relationship("JobFeedbacksTable", back_populates="job", uselist=False)  # 1対1想定
    histories = relationship("HistoryTable", back_populates="job", cascade="all, delete-orphan")

    # --- Helpers / properties for JobDetailResponse (pydantic from_attributes=True expects these attrs) ---
    @property
    def imgs(self):
        # return list of image URLs
        return [img.img_url for img in (self.images or [])]

    # Delegated scalar fields from the 1:1 feedback relationship
    @property
    def salary(self):
        return _safe_getattr(self.feedback, "salary", 0)

    @property
    def level(self):
        return _safe_getattr(self.feedback, "level", 0)

    @property
    def end_time(self):
        v = _safe_getattr(self.feedback, "end_time")
        return v.isoformat() if v is not None else ""

    @property
    def holiday(self):
        return _safe_getattr(self.feedback, "holiday", 0)

    @property
    def overtime_hours(self):
        return _safe_getattr(self.feedback, "overtime_hours", 0)

    @property
    def age(self):
        return _safe_getattr(self.feedback, "age", 0)

    @property
    def tenure_years(self):
        return _safe_getattr(self.feedback, "tenure_years", 0)

    @property
    def marriage_age(self):
        return _safe_getattr(self.feedback, "marriage_age", 0)

    @property
    def gender_ratio(self):
        return _safe_getattr(self.feedback, "gender_ratio", 0.0)

    @property
    def romance_rate(self):
        return _safe_getattr(self.feedback, "romance_rate", 0.0)

    @property
    def social_signification(self):
        return _safe_getattr(self.feedback, "social_signification", "")

    @property
    def personality_traits(self):
        return _safe_getattr(self.feedback, "personality_traits", "")

    @property
    def growth_opportunities(self):
        return _safe_getattr(self.feedback, "growth_opportunities", "")

    @property
    def wrong_image(self):
        return _safe_getattr(self.feedback, "wrong_image", "")

    @property
    def uniform(self):
        return _safe_getattr(self.feedback, "uniform", False)

    @property
    def work_life_balance(self):
        return _safe_getattr(self.feedback, "work_life_balance", 0.0)

    @property
    def future_outlook(self):
        return _safe_getattr(self.feedback, "future_outlook", "")

    @property
    def rarity(self):
        return _safe_getattr(self.feedback, "rarity", 0.0)

    @property
    def scandal_history(self):
        return _safe_getattr(self.feedback, "scandal_history", "")

    @property
    def focus_on_education(self):
        return _safe_getattr(self.feedback, "focus_on_education", False)

    @property
    def focus_on_achievements(self):
        return _safe_getattr(self.feedback, "focus_on_achievements", False)

    @property
    def appeal_points(self):
        return _safe_getattr(self.feedback, "appeal_points", "")

    @property
    def daily_routine(self):
        return _safe_getattr(self.feedback, "daily_routine", "")

    @property
    def comments(self):
        return _safe_getattr(self.feedback, "comments", "")

    # --- Collections mapped for JobDetailResponse ---
    @property
    def skills(self):
        f = self.feedback
        if not f or not getattr(f, "skills", None):
            return []
        res = []
        for fs in f.skills:
            skill = getattr(fs, "skill", None)
            if skill is None:
                continue
            res.append({
                "skill_id": getattr(skill, "skill_id", None),
                "name": getattr(skill, "name", None),
                "is_required": getattr(fs, "is_required", None),
            })
        return res

    @property
    def certifications(self):
        f = self.feedback
        if not f or not getattr(f, "certifications", None):
            return []
        res = []
        for fc in f.certifications:
            cert = getattr(fc, "certification", None)
            if cert is None:
                continue
            res.append({
                "certification_id": getattr(cert, "certification_id", None),
                "name": getattr(cert, "name", None),
                "is_required": getattr(fc, "is_required", None),
            })
        return res

    @property
    def companies(self):
        f = self.feedback
        if not f or not getattr(f, "companies", None):
            return []
        res = []
        for fc in f.companies:
            comp = getattr(fc, "company", None)
            if comp is None:
                continue
            res.append({
                "company_id": getattr(comp, "company_id", None),
                "name": getattr(comp, "name", None),
            })
        return res

    @property
    def talents(self):
        f = self.feedback
        if not f or not getattr(f, "talents", None):
            return []
        res = []
        for ft in f.talents:
            tal = getattr(ft, "talent", None)
            if tal is None:
                continue
            res.append({
                "talent_id": getattr(tal, "talent_id", None),
                "name": getattr(tal, "name", None),
                "is_required": getattr(ft, "is_required", None),
            })
        return res

    @property
    def interests(self):
        f = self.feedback
        if not f or not getattr(f, "interests", None):
            return []
        res = []
        for fi in f.interests:
            intr = getattr(fi, "interest", None)
            if intr is None:
                continue
            res.append({
                "interest_id": getattr(intr, "interest_id", None),
                "name": getattr(intr, "name", None),
                "is_required": getattr(fi, "is_required", None),
            })
        return res

JobsTableSchema: BaseModel = sqlalchemy_to_pydantic(JobsTable)