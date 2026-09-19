from __future__ import annotations

import json
import logging
import math
import os
import re
import time
import uuid
from pathlib import Path
from typing import Any

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    Request,
    UploadFile,
    status,
)
from sqlalchemy import desc
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import ResumeAnalysis
from ..services.ats_service import ATSService
from ..services.pdf_service import PDFService
from ..services.skill_service import SkillService
from ..services.suggestion_service import SuggestionService


# ============================================================
# LOGGER
# ============================================================

logger = logging.getLogger("resumeai.resume")


# ============================================================
# ROUTER
# ============================================================

router = APIRouter()


# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parents[2]

UPLOAD_DIR = BASE_DIR / "uploads"

UPLOAD_DIR.mkdir(
    parents=True,
    exist_ok=True,
)


# ============================================================
# CONFIGURATION
# ============================================================

MAX_FILE_SIZE = int(
    os.getenv(
        "MAX_RESUME_SIZE",
        10 * 1024 * 1024,
    )
)

MIN_RESUME_TEXT_LENGTH = int(
    os.getenv(
        "MIN_RESUME_TEXT_LENGTH",
        80,
    )
)

MIN_JOB_DESCRIPTION_LENGTH = int(
    os.getenv(
        "MIN_JOB_DESCRIPTION_LENGTH",
        80,
    )
)

MAX_JOB_DESCRIPTION_LENGTH = int(
    os.getenv(
        "MAX_JOB_DESCRIPTION_LENGTH",
        50_000,
    )
)

MAX_HISTORY_LIMIT = 100

ANALYSIS_VERSION = "4.0.0"

ENGINE_NAME = "ResumeAI Multi-Signal ATS Intelligence Engine"


# ============================================================
# FILE SECURITY
# ============================================================

ALLOWED_EXTENSION = ".pdf"

ALLOWED_CONTENT_TYPES = {
    "application/pdf",
    "application/octet-stream",
}

PDF_MAGIC = b"%PDF-"

CHUNK_SIZE = 1024 * 1024


# ============================================================
# SCORE CONFIGURATION
# ============================================================

SCORE_WEIGHTS = {
    "skills": 35,
    "keywords": 20,
    "semantic": 20,
    "sections": 10,
    "achievements": 10,
    "contact": 5,
}


# ============================================================
# UTILITY FUNCTIONS
# ============================================================

def _safe_filename(filename: str | None) -> str:
    """
    Sanitize the original filename.

    The original filename is retained only as metadata.
    Temporary disk filenames are UUID based.
    """

    original = filename or "resume.pdf"

    cleaned = Path(original).name

    cleaned = re.sub(
        r"[^a-zA-Z0-9._-]",
        "_",
        cleaned,
    )

    cleaned = cleaned[:255]

    if not cleaned.lower().endswith(".pdf"):
        cleaned += ".pdf"

    return cleaned


def _normalize_text(value: str | None) -> str:
    """
    Normalize user-provided text while preserving meaningful content.
    """

    if not value:
        return ""

    return " ".join(
        value.replace("\x00", " ").split()
    ).strip()


def _json_dumps(value: Any) -> str:
    """
    Safely serialize Python data into SQLite TEXT.
    """

    if value is None:
        return ""

    if isinstance(value, str):
        return value

    try:
        return json.dumps(
            value,
            ensure_ascii=False,
            default=str,
        )
    except (TypeError, ValueError):
        return str(value)


def _json_loads(value: str | None) -> Any:
    """
    Safely deserialize JSON.

    Supports older comma-separated database values.
    """

    if not value:
        return []

    if isinstance(value, (list, tuple, dict)):
        return value

    try:
        return json.loads(value)
    except (
        json.JSONDecodeError,
        TypeError,
        ValueError,
    ):
        return [
            item.strip()
            for item in str(value).split(",")
            if item.strip()
        ]


def _clamp_score(value: Any) -> float:
    """
    Keep scores safely inside 0-100.
    """

    try:
        number = float(value)
    except (
        TypeError,
        ValueError,
    ):
        return 0.0

    if not math.isfinite(number):
        return 0.0

    return round(
        max(
            0.0,
            min(
                100.0,
                number,
            ),
        ),
        2,
    )


def _listify(value: Any) -> list:
    """
    Normalize service output into a list.
    """

    if value is None:
        return []

    if isinstance(value, list):
        return value

    if isinstance(value, tuple):
        return list(value)

    if isinstance(value, set):
        return list(value)

    if isinstance(value, str):
        return [
            item.strip()
            for item in value.split(",")
            if item.strip()
        ]

    return [value]


def _dictify(value: Any) -> dict:
    """
    Normalize service output into a dictionary.
    """

    if isinstance(value, dict):
        return value

    return {}


def _score_label(score: float) -> str:
    """
    Human-readable ATS score classification.
    """

    score = _clamp_score(score)

    if score >= 90:
        return "Exceptional"

    if score >= 80:
        return "Excellent"

    if score >= 70:
        return "Strong"

    if score >= 60:
        return "Good"

    if score >= 50:
        return "Needs Improvement"

    return "Weak"


def _score_status(score: float) -> str:
    """
    Machine-friendly score classification.
    """

    score = _clamp_score(score)

    if score >= 80:
        return "excellent"

    if score >= 70:
        return "strong"

    if score >= 60:
        return "good"

    if score >= 50:
        return "fair"

    return "weak"


def _extract_role_title(
    target_role: str | None,
    advanced_analysis: dict,
) -> str:
    """
    Determine the most useful role title.
    """

    if target_role:
        return target_role

    role = advanced_analysis.get(
        "role_title",
        "Target Role",
    )

    if isinstance(role, str):
        role = _normalize_text(role)

    return role or "Target Role"


def _calculate_improvement_potential(
    overall_score: float,
) -> dict[str, Any]:
    """
    Estimate theoretical improvement room.

    This is intentionally presented as potential,
    not a guaranteed score increase.
    """

    score = _clamp_score(overall_score)

    potential = round(
        max(0.0, 100.0 - score),
        2,
    )

    if score >= 90:
        level = "low"

    elif score >= 75:
        level = "moderate"

    elif score >= 60:
        level = "high"

    else:
        level = "very_high"

    return {
        "current_score": score,
        "maximum_possible_score": 100.0,
        "improvement_room": potential,
        "level": level,
    }


def _calculate_text_stats(
    resume_text: str,
    job_description: str,
) -> dict[str, Any]:
    """
    Generate lightweight text statistics.
    """

    resume_words = resume_text.split()
    jd_words = job_description.split()

    resume_chars = len(resume_text)
    jd_chars = len(job_description)

    return {
        "resume": {
            "characters": resume_chars,
            "words": len(resume_words),
            "estimated_pages": max(
                1,
                math.ceil(len(resume_words) / 550),
            ),
        },
        "job_description": {
            "characters": jd_chars,
            "words": len(jd_words),
        },
    }


# ============================================================
# PDF VALIDATION
# ============================================================

def _validate_pdf_metadata(
    resume: UploadFile,
) -> str:
    """
    Validate filename and content type.
    """

    original_filename = (
        resume.filename or "resume.pdf"
    )

    extension = Path(
        original_filename
    ).suffix.lower()

    if extension != ALLOWED_EXTENSION:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF resume files are supported.",
        )

    if (
        resume.content_type
        and resume.content_type
        not in ALLOWED_CONTENT_TYPES
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid PDF content type.",
        )

    return _safe_filename(
        original_filename
    )


async def _save_uploaded_pdf(
    resume: UploadFile,
    destination: Path,
) -> int:
    """
    Stream the uploaded file to disk.

    Security:
    - bounded memory usage
    - maximum file size
    - PDF magic-byte validation
    """

    total_size = 0
    first_chunk = True

    try:
        with destination.open("wb") as output_file:

            while True:

                chunk = await resume.read(
                    CHUNK_SIZE
                )

                if not chunk:
                    break

                if first_chunk:
                    first_chunk = False

                    if not chunk.startswith(
                        PDF_MAGIC
                    ):
                        raise HTTPException(
                            status_code=(
                                status.HTTP_400_BAD_REQUEST
                            ),
                            detail=(
                                "The uploaded file is not "
                                "a valid PDF."
                            ),
                        )

                total_size += len(chunk)

                if total_size > MAX_FILE_SIZE:
                    raise HTTPException(
                        status_code=(
                            status.HTTP_413_REQUEST_ENTITY_TOO_LARGE
                        ),
                        detail=(
                            "Resume file is too large. "
                            f"Maximum allowed size is "
                            f"{MAX_FILE_SIZE // (1024 * 1024)} MB."
                        ),
                    )

                output_file.write(chunk)

    finally:
        await resume.close()

    if total_size == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The uploaded resume file is empty.",
        )

    return total_size


# ============================================================
# RESPONSE BUILDER
# ============================================================

def _build_analysis_response(
    analysis: ResumeAnalysis,
) -> dict[str, Any]:
    """
    Convert SQLAlchemy model into a frontend-friendly
    ResumeAI intelligence response.
    """

    detected_skills = _json_loads(
        getattr(
            analysis,
            "detected_skills",
            "",
        )
    )

    missing_skills = _json_loads(
        getattr(
            analysis,
            "missing_skills",
            "",
        )
    )

    detected_keywords = _json_loads(
        getattr(
            analysis,
            "detected_keywords",
            "",
        )
    )

    missing_keywords = _json_loads(
        getattr(
            analysis,
            "missing_keywords",
            "",
        )
    )

    sections = _json_loads(
        getattr(
            analysis,
            "sections",
            "",
        )
    )

    strengths = _json_loads(
        getattr(
            analysis,
            "strengths",
            "",
        )
    )

    weaknesses = _json_loads(
        getattr(
            analysis,
            "weaknesses",
            "",
        )
    )

    insights = _json_loads(
        getattr(
            analysis,
            "insights",
            "",
        )
    )

    suggestions = _json_loads(
        getattr(
            analysis,
            "suggestions",
            "",
        )
    )

    overall_score = _clamp_score(
        getattr(
            analysis,
            "overall_score",
            analysis.match_percentage,
        )
    )

    match_percentage = _clamp_score(
        getattr(
            analysis,
            "match_percentage",
            overall_score,
        )
    )

    score_breakdown = {
        "overall_score": overall_score,

        "skills_score": _clamp_score(
            getattr(
                analysis,
                "skills_score",
                0,
            )
        ),

        "keyword_score": _clamp_score(
            getattr(
                analysis,
                "keyword_score",
                0,
            )
        ),

        "semantic_score": _clamp_score(
            getattr(
                analysis,
                "semantic_score",
                0,
            )
        ),

        "section_score": _clamp_score(
            getattr(
                analysis,
                "section_score",
                0,
            )
        ),

        "achievement_score": _clamp_score(
            getattr(
                analysis,
                "achievement_score",
                0,
            )
        ),

        "contact_score": _clamp_score(
            getattr(
                analysis,
                "contact_score",
                0,
            )
        ),

        "content_score": _clamp_score(
            getattr(
                analysis,
                "content_score",
                0,
            )
        ),
    }

    total_keywords = (
        len(detected_keywords)
        + len(missing_keywords)
    )

    keyword_coverage = (
        round(
            (
                len(detected_keywords)
                / total_keywords
            ) * 100,
            2,
        )
        if total_keywords
        else score_breakdown["keyword_score"]
    )

    return {
        "success": True,

        "id": analysis.id,

        "filename": analysis.filename,

        "role_title": getattr(
            analysis,
            "role_title",
            "Target Role",
        ),

        "created_at": analysis.created_at,

        # ----------------------------------------------------
        # Main scores
        # ----------------------------------------------------

        "match_percentage": match_percentage,

        "overall_score": overall_score,

        "score_label": _score_label(
            overall_score
        ),

        "score_status": _score_status(
            overall_score
        ),

        "score_breakdown": score_breakdown,

        # ----------------------------------------------------
        # Skills
        # ----------------------------------------------------

        "detected_skills": detected_skills,

        "missing_skills": missing_skills,

        "skill_matches": [
            {
                "name": skill,
                "category": "Technical",
                "relevance": 100.0,
            }
            for skill in detected_skills
        ],

        "skill_gaps": [
            {
                "name": skill,
                "category": "Technical",
                "importance": "HIGH",
                "recommendation": (
                    f"Only add {skill} if you genuinely "
                    "know it. Where applicable, prove "
                    "it through projects or experience."
                ),
            }
            for skill in missing_skills
        ],

        # ----------------------------------------------------
        # Keywords
        # ----------------------------------------------------

        "keyword_analysis": {
            "detected": detected_keywords,
            "missing": missing_keywords,
            "coverage_percentage": keyword_coverage,
            "total_relevant_keywords": total_keywords,
        },

        # ----------------------------------------------------
        # Resume intelligence
        # ----------------------------------------------------

        "sections": sections,

        "content_analysis": {},

        "contact_analysis": {},

        "resume_health": {},

        # ----------------------------------------------------
        # Intelligence
        # ----------------------------------------------------

        "strengths": strengths,

        "weaknesses": weaknesses,

        "insights": insights,

        "recommendations": suggestions,

        # ----------------------------------------------------
        # Improvement
        # ----------------------------------------------------

        "improvement_potential": (
            _calculate_improvement_potential(
                overall_score
            )
        ),

        # ----------------------------------------------------
        # Meta
        # ----------------------------------------------------

        "meta": {
            "analysis_version": ANALYSIS_VERSION,
            "engine": ENGINE_NAME,
        },
    }


# ============================================================
# ANALYZE RESUME
# ============================================================

@router.post(
    "/analyze",
    status_code=status.HTTP_201_CREATED,
)
async def analyze_resume(
    request: Request,
    resume: UploadFile = File(...),
    job_description: str = Form(...),
    target_role: str | None = Form(None),
    db: Session = Depends(get_db),
):
    """
    Analyze a resume against a target job description.
    """

    started_at = time.perf_counter()

    request_id = getattr(
        request.state,
        "request_id",
        uuid.uuid4().hex,
    )

    file_path: Path | None = None

    try:

        # ====================================================
        # 1. Validate PDF metadata
        # ====================================================

        original_filename = (
            _validate_pdf_metadata(resume)
        )

        # ====================================================
        # 2. Validate Job Description
        # ====================================================

        job_description = _normalize_text(
            job_description
        )

        if (
            len(job_description)
            < MIN_JOB_DESCRIPTION_LENGTH
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "Job description is too short. "
                    f"Please provide at least "
                    f"{MIN_JOB_DESCRIPTION_LENGTH} characters."
                ),
            )

        if (
            len(job_description)
            > MAX_JOB_DESCRIPTION_LENGTH
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "Job description is too long. "
                    f"Maximum allowed length is "
                    f"{MAX_JOB_DESCRIPTION_LENGTH:,} characters."
                ),
            )

        # ====================================================
        # 3. Target role
        # ====================================================

        target_role = (
            _normalize_text(target_role)
            if target_role
            else None
        )

        if target_role:
            target_role = target_role[:255]

        # ====================================================
        # 4. Secure temporary path
        # ====================================================

        temporary_filename = (
            f"{uuid.uuid4().hex}.pdf"
        )

        file_path = (
            UPLOAD_DIR
            / temporary_filename
        )

        # ====================================================
        # 5. Save PDF
        # ====================================================

        file_size = await _save_uploaded_pdf(
            resume,
            file_path,
        )

        logger.info(
            "Resume uploaded | request_id=%s | size=%d",
            request_id,
            file_size,
        )

        # ====================================================
        # 6. Extract resume text
        # ====================================================

        resume_text = PDFService.extract_text(
            str(file_path)
        )

        resume_text = _normalize_text(
            resume_text
        )

        if (
            len(resume_text)
            < MIN_RESUME_TEXT_LENGTH
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "Could not extract enough readable "
                    "text from this PDF. Please upload "
                    "a text-based resume PDF rather than "
                    "a scanned image."
                ),
            )

        # ====================================================
        # 7. Skill intelligence
        # ====================================================

        detected_skills = (
            SkillService.extract_skills(
                resume_text
            )
        )

        missing_skills = (
            SkillService.find_missing_skills(
                resume_text,
                job_description,
            )
        )

        # ====================================================
        # 8. Advanced ATS intelligence
        # ====================================================

        try:

            advanced_analysis = (
                ATSService.analyze(
                    resume_text,
                    job_description,
                )
            )

        except (
            AttributeError,
            TypeError,
        ):

            logger.warning(
                "Advanced ATS unavailable; "
                "using legacy similarity | request_id=%s",
                request_id,
            )

            match_percentage = (
                ATSService.calculate_similarity(
                    resume_text,
                    job_description,
                )
            )

            advanced_analysis = {
                "role_title": (
                    target_role
                    or "Target Role"
                ),

                "overall_score": match_percentage,

                "match_percentage": match_percentage,

                "skills_score": 0,

                "keyword_score": 0,

                "semantic_score": match_percentage,

                "section_score": 0,

                "achievement_score": 0,

                "contact_score": 0,

                "content_score": 0,

                "skills": {
                    "detected": detected_skills,
                    "missing": missing_skills,
                },

                "keywords": {
                    "detected": [],
                    "missing": [],
                },

                "sections": [],

                "content": {},

                "contact": {},

                "strengths": [],

                "weaknesses": [],

                "insights": [],
            }

        # ====================================================
        # 9. Validate ATS output
        # ====================================================

        if not isinstance(
            advanced_analysis,
            dict,
        ):
            raise RuntimeError(
                "ATSService returned an invalid "
                "analysis result."
            )

        # ====================================================
        # 10. Scores
        # ====================================================

        overall_score = _clamp_score(
            advanced_analysis.get(
                "overall_score",
                advanced_analysis.get(
                    "match_percentage",
                    0,
                ),
            )
        )

        match_percentage = _clamp_score(
            advanced_analysis.get(
                "match_percentage",
                overall_score,
            )
        )

        # ====================================================
        # 11. Extract intelligence
        # ====================================================

        skills_data = _dictify(
            advanced_analysis.get(
                "skills",
                {},
            )
        )

        keywords_data = _dictify(
            advanced_analysis.get(
                "keywords",
                {},
            )
        )

        sections_data = _listify(
            advanced_analysis.get(
                "sections",
                [],
            )
        )

        content_data = _dictify(
            advanced_analysis.get(
                "content",
                {},
            )
        )

        contact_data = _dictify(
            advanced_analysis.get(
                "contact",
                {},
            )
        )

        detected_skills = _listify(
            skills_data.get(
                "detected",
                detected_skills,
            )
        )

        missing_skills = _listify(
            skills_data.get(
                "missing",
                missing_skills,
            )
        )

        detected_keywords = _listify(
            keywords_data.get(
                "detected",
                [],
            )
        )

        missing_keywords = _listify(
            keywords_data.get(
                "missing",
                [],
            )
        )

        strengths = _listify(
            advanced_analysis.get(
                "strengths",
                [],
            )
        )

        weaknesses = _listify(
            advanced_analysis.get(
                "weaknesses",
                [],
            )
        )

        insights = _listify(
            advanced_analysis.get(
                "insights",
                [],
            )
        )

        # ====================================================
        # 12. Suggestions / action engine
        # ====================================================

        try:

            suggestions = (
                SuggestionService.generate(
                    overall_score,
                    missing_skills,
                    advanced_analysis,
                )
            )

        except TypeError:

            # Backward compatibility
            suggestions = (
                SuggestionService.generate(
                    overall_score,
                    missing_skills,
                )
            )

        suggestions = _listify(
            suggestions
        )

        # ====================================================
        # 13. Quick wins
        # ====================================================

        quick_wins = []

        if hasattr(
            SuggestionService,
            "quick_wins",
        ):
            try:
                quick_wins = _listify(
                    SuggestionService.quick_wins(
                        overall_score,
                        missing_skills,
                        advanced_analysis,
                    )
                )
            except (
                TypeError,
                AttributeError,
            ):
                quick_wins = []

        # ====================================================
        # 14. Action plan
        # ====================================================

        action_plan = []

        if hasattr(
            SuggestionService,
            "action_plan",
        ):
            try:
                action_plan = _listify(
                    SuggestionService.action_plan(
                        overall_score,
                        missing_skills,
                        advanced_analysis,
                    )
                )
            except (
                TypeError,
                AttributeError,
            ):
                action_plan = []

        # ====================================================
        # 15. Role title
        # ====================================================

        role_title = _extract_role_title(
            target_role,
            advanced_analysis,
        )

        # ====================================================
        # 16. Text statistics
        # ====================================================

        text_stats = _calculate_text_stats(
            resume_text,
            job_description,
        )

        # ====================================================
        # 17. Build DB payload
        # ====================================================

        analysis_kwargs = {
            "filename": original_filename,

            "resume_text": resume_text,

            "job_description": job_description,

            "match_percentage": match_percentage,

            "detected_skills": _json_dumps(
                detected_skills
            ),

            "missing_skills": _json_dumps(
                missing_skills
            ),

            "suggestions": _json_dumps(
                suggestions
            ),
        }

        # ====================================================
        # 18. Ultra-Pro model fields
        # ====================================================

        model_fields = {

            "overall_score": overall_score,

            "skills_score": _clamp_score(
                advanced_analysis.get(
                    "skills_score",
                    0,
                )
            ),

            "keyword_score": _clamp_score(
                advanced_analysis.get(
                    "keyword_score",
                    0,
                )
            ),

            "semantic_score": _clamp_score(
                advanced_analysis.get(
                    "semantic_score",
                    0,
                )
            ),

            "section_score": _clamp_score(
                advanced_analysis.get(
                    "section_score",
                    0,
                )
            ),

            "achievement_score": _clamp_score(
                advanced_analysis.get(
                    "achievement_score",
                    0,
                )
            ),

            "contact_score": _clamp_score(
                advanced_analysis.get(
                    "contact_score",
                    0,
                )
            ),

            "content_score": _clamp_score(
                advanced_analysis.get(
                    "content_score",
                    0,
                )
            ),

            "role_title": role_title,

            "detected_keywords": _json_dumps(
                detected_keywords
            ),

            "missing_keywords": _json_dumps(
                missing_keywords
            ),

            "sections": _json_dumps(
                sections_data
            ),

            "strengths": _json_dumps(
                strengths
            ),

            "weaknesses": _json_dumps(
                weaknesses
            ),

            "insights": _json_dumps(
                insights
            ),
        }

        # ====================================================
        # 19. Model compatibility
        # ====================================================

        model_columns = {
            column.name
            for column
            in ResumeAnalysis.__table__.columns
        }

        for field_name, field_value in (
            model_fields.items()
        ):

            if field_name in model_columns:

                analysis_kwargs[
                    field_name
                ] = field_value

        # ====================================================
        # 20. Database persistence
        # ====================================================

        analysis = ResumeAnalysis(
            **analysis_kwargs
        )

        db.add(analysis)

        db.commit()

        db.refresh(analysis)

        # ====================================================
        # 21. Build response
        # ====================================================

        response = _build_analysis_response(
            analysis
        )

        # ====================================================
        # 22. Add rich intelligence
        # ====================================================

        processing_time = round(
            time.perf_counter()
            - started_at,
            4,
        )

        response["content_analysis"] = (
            content_data
        )

        response["contact_analysis"] = (
            contact_data
        )

        response["resume_health"] = (
            advanced_analysis.get(
                "resume_health",
                advanced_analysis.get(
                    "health",
                    {},
                ),
            )
        )

        response["text_statistics"] = (
            text_stats
        )

        response["advanced_analysis"] = {
            key: value
            for key, value
            in advanced_analysis.items()
            if key not in {
                "resume_text",
                "job_description",
            }
        }

        response["recommendation_engine"] = {
            "total_recommendations": len(
                suggestions
            ),

            "quick_wins": quick_wins,

            "action_plan": action_plan,
        }

        response["meta"] = {
            "request_id": request_id,

            "analysis_id": analysis.id,

            "analysis_version": ANALYSIS_VERSION,

            "engine": ENGINE_NAME,

            "processing_time_seconds": processing_time,

            "file_size_bytes": file_size,

            "max_file_size_bytes": MAX_FILE_SIZE,

            "target_role": role_title,

            "score_weights": SCORE_WEIGHTS,

            "privacy": {
                "temporary_pdf_deleted": True,
                "raw_resume_returned": False,
                "raw_job_description_returned": False,
            },
        }

        logger.info(
            (
                "Resume analysis completed | "
                "request_id=%s | "
                "analysis_id=%s | "
                "score=%.2f | "
                "processing=%.4fs"
            ),
            request_id,
            analysis.id,
            overall_score,
            processing_time,
        )

        return response

    # ========================================================
    # EXPECTED CLIENT ERRORS
    # ========================================================

    except HTTPException:
        db.rollback()
        raise

    # ========================================================
    # UNEXPECTED ERRORS
    # ========================================================

    except Exception:

        db.rollback()

        logger.exception(
            "Resume analysis failed | request_id=%s",
            request_id,
        )

        raise HTTPException(
            status_code=(
                status.HTTP_500_INTERNAL_SERVER_ERROR
            ),
            detail=(
                "Resume analysis failed unexpectedly. "
                f"Reference ID: {request_id}"
            ),
        )

    # ========================================================
    # GUARANTEED CLEANUP
    # ========================================================

    finally:

        if file_path is not None:

            try:

                if file_path.exists():

                    file_path.unlink()

                    logger.debug(
                        "Temporary resume deleted | path=%s",
                        file_path,
                    )

            except OSError:

                logger.warning(
                    "Unable to remove temporary resume | path=%s",
                    file_path,
                )


# ============================================================
# ANALYSIS HISTORY
# ============================================================

@router.get(
    "/history",
)
def get_analysis_history(
    limit: int = 20,
    db: Session = Depends(get_db),
):
    """
    Return latest resume analyses.
    """

    limit = max(
        1,
        min(
            limit,
            MAX_HISTORY_LIMIT,
        ),
    )

    analyses = (
        db.query(ResumeAnalysis)
        .order_by(
            desc(
                ResumeAnalysis.created_at
            )
        )
        .limit(limit)
        .all()
    )

    items = []

    for analysis in analyses:

        score = _clamp_score(
            getattr(
                analysis,
                "overall_score",
                analysis.match_percentage,
            )
        )

        items.append(
            {
                "id": analysis.id,

                "filename": analysis.filename,

                "role_title": getattr(
                    analysis,
                    "role_title",
                    "Target Role",
                ),

                "overall_score": score,

                "match_percentage": _clamp_score(
                    analysis.match_percentage
                ),

                "score_label": _score_label(
                    score
                ),

                "score_status": _score_status(
                    score
                ),

                "created_at": analysis.created_at,
            }
        )

    return {
        "success": True,

        "count": len(items),

        "limit": limit,

        "items": items,
    }


# ============================================================
# GET SINGLE ANALYSIS
# ============================================================

@router.get(
    "/{analysis_id}",
)
def get_analysis(
    analysis_id: int,
    db: Session = Depends(get_db),
):
    """
    Retrieve one complete analysis.
    """

    if analysis_id <= 0:

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid analysis ID.",
        )

    analysis = (
        db.query(ResumeAnalysis)
        .filter(
            ResumeAnalysis.id
            == analysis_id
        )
        .first()
    )

    if analysis is None:

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resume analysis not found.",
        )

    response = _build_analysis_response(
        analysis
    )

    response["meta"] = {
        "analysis_version": ANALYSIS_VERSION,
        "engine": ENGINE_NAME,
        "source": "database",
        "raw_resume_returned": False,
        "raw_job_description_returned": False,
    }

    return response