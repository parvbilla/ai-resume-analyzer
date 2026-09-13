from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import (
    Column,
    DateTime,
    Float,
    Index,
    Integer,
    String,
    Text,
)

from .database import Base


# ============================================================
# RESUME ANALYSIS
# ============================================================

class ResumeAnalysis(Base):
    """
    Stores one complete resume analysis.

    Each record represents one resume + one target job
    description analysis.
    """

    __tablename__ = "resume_analyses"

    # --------------------------------------------------------
    # PRIMARY ID
    # --------------------------------------------------------

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    # --------------------------------------------------------
    # RESUME INFORMATION
    # --------------------------------------------------------

    filename = Column(
        String(255),
        nullable=False,
    )

    resume_text = Column(
        Text,
        nullable=False,
    )

    # --------------------------------------------------------
    # TARGET JOB
    # --------------------------------------------------------

    job_description = Column(
        Text,
        nullable=False,
    )

    role_title = Column(
        String(255),
        nullable=False,
        default="Target Role",
    )

    # --------------------------------------------------------
    # OVERALL ATS / MATCH SCORE
    # --------------------------------------------------------

    match_percentage = Column(
        Float,
        nullable=False,
        default=0.0,
    )

    overall_score = Column(
        Float,
        nullable=False,
        default=0.0,
    )

    # --------------------------------------------------------
    # SCORE BREAKDOWN
    # --------------------------------------------------------
    # These scores make the analysis explainable instead of
    # showing only one mysterious ATS number.

    skills_score = Column(
        Float,
        nullable=False,
        default=0.0,
    )

    keyword_score = Column(
        Float,
        nullable=False,
        default=0.0,
    )

    semantic_score = Column(
        Float,
        nullable=False,
        default=0.0,
    )

    section_score = Column(
        Float,
        nullable=False,
        default=0.0,
    )

    achievement_score = Column(
        Float,
        nullable=False,
        default=0.0,
    )

    contact_score = Column(
        Float,
        nullable=False,
        default=0.0,
    )

    content_score = Column(
        Float,
        nullable=False,
        default=0.0,
    )

    # --------------------------------------------------------
    # SKILLS INTELLIGENCE
    # --------------------------------------------------------
    # Stored as JSON strings because SQLite does not require
    # a separate JSON database.

    detected_skills = Column(
        Text,
        nullable=False,
        default="",
    )

    missing_skills = Column(
        Text,
        nullable=False,
        default="",
    )

    # --------------------------------------------------------
    # KEYWORD INTELLIGENCE
    # --------------------------------------------------------

    detected_keywords = Column(
        Text,
        nullable=False,
        default="",
    )

    missing_keywords = Column(
        Text,
        nullable=False,
        default="",
    )

    # --------------------------------------------------------
    # RESUME SECTION ANALYSIS
    # --------------------------------------------------------

    sections = Column(
        Text,
        nullable=False,
        default="",
    )

    # --------------------------------------------------------
    # CONTENT / EVIDENCE ANALYSIS
    # --------------------------------------------------------

    strengths = Column(
        Text,
        nullable=False,
        default="",
    )

    weaknesses = Column(
        Text,
        nullable=False,
        default="",
    )

    insights = Column(
        Text,
        nullable=False,
        default="",
    )

    # --------------------------------------------------------
    # ACTION PLAN
    # --------------------------------------------------------

    suggestions = Column(
        Text,
        nullable=False,
        default="",
    )

    # --------------------------------------------------------
    # TIMESTAMPS
    # --------------------------------------------------------

    created_at = Column(
        DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    # ========================================================
    # DATABASE INDEXES
    # ========================================================

    __table_args__ = (
        Index(
            "ix_resume_analyses_created_at",
            "created_at",
        ),

        Index(
            "ix_resume_analyses_role_title",
            "role_title",
        ),

        Index(
            "ix_resume_analyses_overall_score",
            "overall_score",
        ),
    )

    # ========================================================
    # REPRESENTATION
    # ========================================================

    def __repr__(self) -> str:
        return (
            f"<ResumeAnalysis "
            f"id={self.id} "
            f"role={self.role_title!r} "
            f"score={self.overall_score:.1f}>"
        )