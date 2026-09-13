from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
)


# ============================================================
# COMMON CONFIGURATION
# ============================================================

class APIBaseModel(BaseModel):
    """
    Base schema used throughout the application.

    extra='ignore' keeps the API resilient if the frontend sends
    harmless additional fields.
    """

    model_config = ConfigDict(
        extra="ignore",
        str_strip_whitespace=True,
    )


# ============================================================
# ANALYSIS REQUEST
# ============================================================

class ResumeAnalysisRequest(APIBaseModel):
    """
    Optional structured data that can accompany a resume analysis.

    The actual PDF is uploaded through multipart/form-data.
    """

    job_description: str = Field(
        ...,
        min_length=80,
        max_length=50_000,
        description=(
            "Target job description used to evaluate resume fit."
        ),
    )

    target_role: str | None = Field(
        default=None,
        max_length=255,
        description="Optional target job title.",
    )

    @field_validator("job_description")
    @classmethod
    def validate_job_description(
        cls,
        value: str,
    ) -> str:
        value = " ".join(value.split())

        if len(value) < 80:
            raise ValueError(
                "Job description must contain at least 80 "
                "meaningful characters."
            )

        return value

    @field_validator("target_role")
    @classmethod
    def validate_target_role(
        cls,
        value: str | None,
    ) -> str | None:
        if value is None:
            return None

        value = " ".join(value.split())

        return value or None


# ============================================================
# SCORE SCHEMA
# ============================================================

class ScoreMetric(APIBaseModel):
    """
    One explainable scoring dimension.
    """

    score: float = Field(
        default=0.0,
        ge=0.0,
        le=100.0,
    )

    label: str = Field(
        ...,
        min_length=1,
        max_length=100,
    )

    description: str = Field(
        default="",
        max_length=500,
    )


# ============================================================
# SCORE BREAKDOWN
# ============================================================

class ScoreBreakdown(APIBaseModel):
    """
    Complete ATS scoring breakdown.
    """

    overall_score: float = Field(
        default=0.0,
        ge=0.0,
        le=100.0,
    )

    skills_score: float = Field(
        default=0.0,
        ge=0.0,
        le=100.0,
    )

    keyword_score: float = Field(
        default=0.0,
        ge=0.0,
        le=100.0,
    )

    semantic_score: float = Field(
        default=0.0,
        ge=0.0,
        le=100.0,
    )

    section_score: float = Field(
        default=0.0,
        ge=0.0,
        le=100.0,
    )

    achievement_score: float = Field(
        default=0.0,
        ge=0.0,
        le=100.0,
    )

    contact_score: float = Field(
        default=0.0,
        ge=0.0,
        le=100.0,
    )

    content_score: float = Field(
        default=0.0,
        ge=0.0,
        le=100.0,
    )


# ============================================================
# SKILL INTELLIGENCE
# ============================================================

class SkillMatch(APIBaseModel):
    """
    A skill detected in the resume.
    """

    name: str = Field(
        ...,
        min_length=1,
        max_length=100,
    )

    category: str = Field(
        default="Technical",
        max_length=100,
    )

    relevance: float = Field(
        default=0.0,
        ge=0.0,
        le=100.0,
    )


class SkillGap(APIBaseModel):
    """
    A skill requested by the job but not sufficiently present
    in the resume.
    """

    name: str = Field(
        ...,
        min_length=1,
        max_length=100,
    )

    category: str = Field(
        default="Technical",
        max_length=100,
    )

    importance: Literal[
        "LOW",
        "MEDIUM",
        "HIGH",
        "CRITICAL",
    ] = "MEDIUM"

    recommendation: str = Field(
        default="Consider adding relevant evidence for this skill.",
        max_length=500,
    )


# ============================================================
# KEYWORD INTELLIGENCE
# ============================================================

class KeywordAnalysis(APIBaseModel):
    """
    Job-description keyword coverage.
    """

    detected: list[str] = Field(
        default_factory=list,
    )

    missing: list[str] = Field(
        default_factory=list,
    )

    coverage_percentage: float = Field(
        default=0.0,
        ge=0.0,
        le=100.0,
    )

    total_relevant_keywords: int = Field(
        default=0,
        ge=0,
    )


# ============================================================
# SECTION HEALTH
# ============================================================

class SectionHealth(APIBaseModel):
    """
    Health of a resume section.
    """

    name: str = Field(
        ...,
        min_length=1,
        max_length=100,
    )

    present: bool = False

    score: float = Field(
        default=0.0,
        ge=0.0,
        le=100.0,
    )

    feedback: str = Field(
        default="",
        max_length=500,
    )


# ============================================================
# CONTENT / ACHIEVEMENT INTELLIGENCE
# ============================================================

class ContentAnalysis(APIBaseModel):
    """
    Evidence and writing-quality analysis.
    """

    achievement_count: int = Field(
        default=0,
        ge=0,
    )

    quantified_achievement_count: int = Field(
        default=0,
        ge=0,
    )

    action_verb_count: int = Field(
        default=0,
        ge=0,
    )

    weak_phrase_count: int = Field(
        default=0,
        ge=0,
    )

    score: float = Field(
        default=0.0,
        ge=0.0,
        le=100.0,
    )


# ============================================================
# CONTACT / PROFILE QUALITY
# ============================================================

class ContactAnalysis(APIBaseModel):
    """
    Contact information and professional profile health.
    """

    email_present: bool = False

    phone_present: bool = False

    linkedin_present: bool = False

    github_present: bool = False

    portfolio_present: bool = False

    score: float = Field(
        default=0.0,
        ge=0.0,
        le=100.0,
    )


# ============================================================
# INSIGHTS
# ============================================================

class Insight(APIBaseModel):
    """
    One deeper resume intelligence insight.
    """

    title: str = Field(
        ...,
        min_length=1,
        max_length=150,
    )

    detail: str = Field(
        ...,
        min_length=1,
        max_length=1_000,
    )

    category: Literal[
        "SKILLS",
        "KEYWORDS",
        "CONTENT",
        "ATS",
        "STRUCTURE",
        "CAREER",
        "CONTACT",
        "SEMANTIC",
    ] = "ATS"

    impact: Literal[
        "LOW",
        "MEDIUM",
        "HIGH",
        "CRITICAL",
    ] = "MEDIUM"


# ============================================================
# RECOMMENDATIONS
# ============================================================

class Recommendation(APIBaseModel):
    """
    Prioritized action item for improving the resume.
    """

    priority: Literal[
        "LOW",
        "MEDIUM",
        "HIGH",
        "CRITICAL",
    ] = "MEDIUM"

    title: str = Field(
        ...,
        min_length=1,
        max_length=200,
    )

    detail: str = Field(
        ...,
        min_length=1,
        max_length=1_000,
    )

    category: Literal[
        "SKILLS",
        "KEYWORDS",
        "CONTENT",
        "ATS",
        "STRUCTURE",
        "CONTACT",
        "SUMMARY",
        "FORMATTING",
    ] = "ATS"


# ============================================================
# RESUME HEALTH
# ============================================================

class ResumeHealth(APIBaseModel):
    """
    High-level resume quality indicators.
    """

    overall: float = Field(
        default=0.0,
        ge=0.0,
        le=100.0,
    )

    ats_ready: bool = False

    has_contact_information: bool = False

    has_summary: bool = False

    has_experience: bool = False

    has_education: bool = False

    has_skills: bool = False

    has_projects: bool = False

    has_quantified_achievements: bool = False


# ============================================================
# COMPLETE ANALYSIS RESPONSE
# ============================================================

class ResumeAnalysisResponse(APIBaseModel):
    """
    Complete response returned after resume analysis.
    """

    id: int

    filename: str

    role_title: str

    created_at: datetime

    # --------------------------------------------------------
    # Main scores
    # --------------------------------------------------------

    match_percentage: float = Field(
        default=0.0,
        ge=0.0,
        le=100.0,
    )

    overall_score: float = Field(
        default=0.0,
        ge=0.0,
        le=100.0,
    )

    score_breakdown: ScoreBreakdown

    # --------------------------------------------------------
    # Skills
    # --------------------------------------------------------

    detected_skills: list[str] = Field(
        default_factory=list,
    )

    missing_skills: list[str] = Field(
        default_factory=list,
    )

    skill_matches: list[SkillMatch] = Field(
        default_factory=list,
    )

    skill_gaps: list[SkillGap] = Field(
        default_factory=list,
    )

    # --------------------------------------------------------
    # Keywords
    # --------------------------------------------------------

    keyword_analysis: KeywordAnalysis

    # --------------------------------------------------------
    # Resume structure
    # --------------------------------------------------------

    sections: list[SectionHealth] = Field(
        default_factory=list,
    )

    # --------------------------------------------------------
    # Content
    # --------------------------------------------------------

    content_analysis: ContentAnalysis

    # --------------------------------------------------------
    # Contact
    # --------------------------------------------------------

    contact_analysis: ContactAnalysis

    # --------------------------------------------------------
    # Health
    # --------------------------------------------------------

    resume_health: ResumeHealth

    # --------------------------------------------------------
    # Intelligence
    # --------------------------------------------------------

    strengths: list[str] = Field(
        default_factory=list,
    )

    weaknesses: list[str] = Field(
        default_factory=list,
    )

    insights: list[Insight] = Field(
        default_factory=list,
    )

    recommendations: list[Recommendation] = Field(
        default_factory=list,
    )


# ============================================================
# HISTORY ITEM
# ============================================================

class AnalysisHistoryItem(APIBaseModel):
    """
    Lightweight representation used by the dashboard history.
    """

    id: int

    filename: str

    role_title: str

    overall_score: float = Field(
        default=0.0,
        ge=0.0,
        le=100.0,
    )

    match_percentage: float = Field(
        default=0.0,
        ge=0.0,
        le=100.0,
    )

    created_at: datetime


# ============================================================
# PAGINATION
# ============================================================

class PaginationMeta(APIBaseModel):
    """
    Pagination information for API collections.
    """

    page: int = Field(
        default=1,
        ge=1,
    )

    page_size: int = Field(
        default=10,
        ge=1,
        le=100,
    )

    total_items: int = Field(
        default=0,
        ge=0,
    )

    total_pages: int = Field(
        default=0,
        ge=0,
    )

    has_next: bool = False

    has_previous: bool = False


class AnalysisHistoryResponse(APIBaseModel):
    """
    Paginated analysis history response.
    """

    items: list[AnalysisHistoryItem] = Field(
        default_factory=list,
    )

    pagination: PaginationMeta


# ============================================================
# API MESSAGE
# ============================================================

class APIMessage(APIBaseModel):
    """
    Standard lightweight API response.
    """

    success: bool = True

    message: str = Field(
        ...,
        min_length=1,
        max_length=500,
    )


# ============================================================
# ERROR RESPONSE
# ============================================================

class APIError(APIBaseModel):
    """
    Consistent API error structure.
    """

    success: bool = False

    error: str = Field(
        ...,
        min_length=1,
        max_length=100,
    )

    detail: str = Field(
        ...,
        min_length=1,
        max_length=1_000,
    )

    request_id: str | None = Field(
        default=None,
        max_length=100,
    )

    details: dict[str, Any] | None = None