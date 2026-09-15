from __future__ import annotations

import re
from collections import Counter
from typing import Any

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from .skill_service import SkillService


class ATSService:
    """
    Ultra-Pro ATS Resume Intelligence Engine.

    Designed for ResumeAI.

    Scoring signals:
        1. Skill Alignment       -> 35%
        2. Keyword Coverage      -> 20%
        3. Semantic Relevance    -> 20%
        4. Section Health        -> 10%
        5. Achievement Evidence  -> 10%
        6. Contact/Profile       -> 5%

    The service also provides:
        - ATS score
        - score breakdown
        - matched keywords
        - missing keywords
        - skill gaps
        - resume sections
        - achievements
        - action verbs
        - contact detection
        - strengths
        - weaknesses
        - insights
        - prioritized recommendations
        - semantic similarity
        - keyword coverage
        - resume health
    """

    # ============================================================
    # CONFIGURATION
    # ============================================================

    WEIGHTS = {
        "skills": 0.35,
        "keywords": 0.20,
        "semantic": 0.20,
        "sections": 0.10,
        "achievements": 0.10,
        "contact": 0.05,
    }

    MIN_TEXT_LENGTH = 30

    # ============================================================
    # RESUME SECTIONS
    # ============================================================

    SECTION_ALIASES = {
        "summary": [
            "summary",
            "professional summary",
            "profile",
            "about me",
            "career summary",
            "objective",
            "career objective",
        ],
        "experience": [
            "experience",
            "work experience",
            "professional experience",
            "employment history",
            "work history",
        ],
        "education": [
            "education",
            "academic background",
            "academic qualifications",
            "qualifications",
        ],
        "skills": [
            "skills",
            "technical skills",
            "core skills",
            "technologies",
            "technical expertise",
        ],
        "projects": [
            "projects",
            "personal projects",
            "academic projects",
            "key projects",
        ],
        "certifications": [
            "certifications",
            "certificates",
            "licenses",
        ],
        "achievements": [
            "achievements",
            "accomplishments",
            "awards",
            "honors",
        ],
        "languages": [
            "languages",
            "language proficiency",
        ],
        "interests": [
            "interests",
            "hobbies",
            "activities",
        ],
        "volunteering": [
            "volunteering",
            "volunteer experience",
            "community involvement",
        ],
    }

    # ============================================================
    # ACTION VERBS
    # ============================================================

    ACTION_VERBS = {
        "built",
        "developed",
        "designed",
        "implemented",
        "engineered",
        "architected",
        "optimized",
        "automated",
        "deployed",
        "integrated",
        "created",
        "delivered",
        "improved",
        "reduced",
        "increased",
        "led",
        "managed",
        "launched",
        "migrated",
        "refactored",
        "configured",
        "tested",
        "maintained",
        "resolved",
        "analyzed",
        "streamlined",
        "scaled",
        "accelerated",
        "transformed",
    }

    # ============================================================
    # WEAK / GENERIC PHRASES
    # ============================================================

    WEAK_PHRASES = {
        "hardworking",
        "team player",
        "quick learner",
        "passionate",
        "motivated",
        "self motivated",
        "responsible",
        "good communication",
        "excellent communication",
        "detail oriented",
        "results oriented",
        "works well under pressure",
        "fast learner",
    }

    # ============================================================
    # CONTACT PATTERNS
    # ============================================================

    EMAIL_PATTERN = re.compile(
        r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b",
        re.IGNORECASE,
    )

    PHONE_PATTERN = re.compile(
        r"(?<!\d)"
        r"(?:\+?\d{1,3}[\s.-]?)?"
        r"(?:\(?\d{2,4}\)?[\s.-]?)?"
        r"\d{3,4}[\s.-]?\d{3,4}"
        r"(?!\d)"
    )

    LINKEDIN_PATTERN = re.compile(
        r"(linkedin\.com|linkedin)",
        re.IGNORECASE,
    )

    GITHUB_PATTERN = re.compile(
        r"(github\.com|github)",
        re.IGNORECASE,
    )

    # ============================================================
    # GENERIC TEXT HELPERS
    # ============================================================

    @staticmethod
    def _clean_text(text: str) -> str:
        if not text:
            return ""

        text = text.replace("\u00a0", " ")
        text = text.replace("\r\n", "\n")
        text = text.replace("\r", "\n")

        text = re.sub(r"[ \t]+", " ", text)
        text = re.sub(r"\n{3,}", "\n\n", text)

        return text.strip()

    @staticmethod
    def _normalize(text: str) -> str:
        text = ATSService._clean_text(text)
        return text.lower()

    @staticmethod
    def _tokenize(text: str) -> list[str]:
        """
        Extract meaningful tokens.

        Keeps technical forms such as:
            c++
            c#
            node.js
            next.js
            ci/cd
        """

        if not text:
            return []

        return re.findall(
            r"[a-zA-Z0-9+#./-]+",
            text.lower(),
        )

    # ============================================================
    # TF-IDF SEMANTIC SCORE
    # ============================================================

    @classmethod
    def calculate_semantic_similarity(
        cls,
        resume_text: str,
        job_description: str,
    ) -> float:
        """
        Calculate semantic similarity using TF-IDF.

        A token-overlap component is also blended in so that
        longer resumes are not unfairly punished.
        """

        resume = cls._clean_text(resume_text)
        job = cls._clean_text(job_description)

        if (
            len(resume) < cls.MIN_TEXT_LENGTH
            or len(job) < cls.MIN_TEXT_LENGTH
        ):
            return 0.0

        try:
            vectorizer = TfidfVectorizer(
                stop_words="english",
                ngram_range=(1, 2),
                sublinear_tf=True,
                max_features=5000,
            )

            matrix = vectorizer.fit_transform(
                [resume, job]
            )

            tfidf_score = float(
                cosine_similarity(
                    matrix[0:1],
                    matrix[1:2],
                )[0][0]
            )

        except (ValueError, RuntimeError):
            tfidf_score = 0.0

        resume_tokens = set(
            cls._meaningful_tokens(resume)
        )

        job_tokens = set(
            cls._meaningful_tokens(job)
        )

        if not job_tokens:
            overlap_score = 0.0
        else:
            overlap_score = (
                len(resume_tokens.intersection(job_tokens))
                / len(job_tokens)
            )

        # Blend both signals.
        score = (
            tfidf_score * 0.65
            + overlap_score * 0.35
        )

        return round(
            min(100.0, score * 100),
            2,
        )

    @classmethod
    def calculate_similarity(
        cls,
        resume_text: str,
        job_description: str,
    ) -> float:
        """
        Backward-compatible similarity method.
        """

        return cls.calculate_semantic_similarity(
            resume_text,
            job_description,
        )

    # ============================================================
    # KEYWORD ANALYSIS
    # ============================================================

    @classmethod
    def extract_job_keywords(
        cls,
        job_description: str,
        limit: int = 40,
    ) -> list[str]:
        """
        Extract high-value keywords from a job description.

        Removes common English stop words and ranks terms by
        frequency.
        """

        tokens = cls._meaningful_tokens(
            job_description
        )

        if not tokens:
            return []

        frequency = Counter(tokens)

        return [
            word
            for word, _ in frequency.most_common(limit)
        ]

    @classmethod
    def keyword_analysis(
        cls,
        resume_text: str,
        job_description: str,
    ) -> dict[str, Any]:

        resume = cls._normalize(resume_text)
        job = cls._normalize(job_description)

        keywords = cls.extract_job_keywords(
            job_description,
            limit=50,
        )

        matched = []
        missing = []

        for keyword in keywords:

            if cls._keyword_exists(
                resume,
                keyword,
            ):
                matched.append(keyword)
            else:
                missing.append(keyword)

        coverage = (
            len(matched) / len(keywords) * 100
            if keywords
            else 0
        )

        return {
            "required_keywords": keywords,
            "matched_keywords": matched,
            "missing_keywords": missing,
            "coverage": round(coverage, 2),
            "matched_count": len(matched),
            "missing_count": len(missing),
            "total_count": len(keywords),
        }

    @classmethod
    def _keyword_exists(
        cls,
        text: str,
        keyword: str,
    ) -> bool:

        if not keyword:
            return False

        pattern = rf"(?<!\w){re.escape(keyword)}(?!\w)"

        return re.search(
            pattern,
            text,
            flags=re.IGNORECASE,
        ) is not None

    # ============================================================
    # SECTION DETECTION
    # ============================================================

    @classmethod
    def detect_sections(
        cls,
        resume_text: str,
    ) -> dict[str, bool]:

        normalized = cls._normalize(
            resume_text
        )

        detected = {}

        for section, aliases in cls.SECTION_ALIASES.items():

            detected[section] = any(
                cls._section_exists(
                    normalized,
                    alias,
                )
                for alias in aliases
            )

        return detected

    @staticmethod
    def _section_exists(
        text: str,
        alias: str,
    ) -> bool:

        pattern = (
            rf"(?:^|\n)\s*"
            rf"{re.escape(alias.lower())}"
            rf"\s*(?::|-|$)"
        )

        return re.search(
            pattern,
            text,
            flags=re.IGNORECASE,
        ) is not None

    @classmethod
    def section_score(
        cls,
        resume_text: str,
    ) -> dict[str, Any]:

        sections = cls.detect_sections(
            resume_text
        )

        important_sections = {
            "summary",
            "experience",
            "education",
            "skills",
            "projects",
        }

        present_important = sum(
            sections.get(section, False)
            for section in important_sections
        )

        score = (
            present_important
            / len(important_sections)
            * 100
        )

        return {
            "score": round(score, 2),
            "sections": sections,
            "present": [
                name
                for name, exists in sections.items()
                if exists
            ],
            "missing_important": [
                name
                for name in important_sections
                if not sections.get(name, False)
            ],
        }

    # ============================================================
    # ACHIEVEMENT / EVIDENCE ANALYSIS
    # ============================================================

    @classmethod
    def achievement_analysis(
        cls,
        resume_text: str,
    ) -> dict[str, Any]:

        text = cls._clean_text(
            resume_text
        )

        lower = text.lower()

        action_verbs = []

        for verb in cls.ACTION_VERBS:

            if re.search(
                rf"\b{re.escape(verb)}\b",
                lower,
            ):
                action_verbs.append(verb)

        # Detect measurable evidence.
        metrics = re.findall(
            r"""
            (?:
                \b\d+(?:\.\d+)?%
                |
                \b\d+(?:\.\d+)?\s*
                (?:users?|customers?|projects?|employees?|clients?)
                |
                \$\s?\d+(?:,\d{3})*(?:\.\d+)?
                |
                \b\d+(?:\.\d+)?x\b
            )
            """,
            lower,
            flags=re.IGNORECASE | re.VERBOSE,
        )

        achievement_lines = []

        for line in text.splitlines():

            line = line.strip()

            if not line:
                continue

            has_action = any(
                re.search(
                    rf"\b{re.escape(verb)}\b",
                    line.lower(),
                )
                for verb in cls.ACTION_VERBS
            )

            has_number = bool(
                re.search(
                    r"\d+%|\b\d+\b|\$\d+",
                    line,
                )
            )

            if has_action and has_number:
                achievement_lines.append(line)

        # Score based on evidence quality.
        action_score = min(
            50,
            len(action_verbs) * 5,
        )

        metric_score = min(
            50,
            len(metrics) * 10,
        )

        score = action_score + metric_score

        return {
            "score": round(
                min(100, score),
                2,
            ),
            "action_verbs": sorted(
                set(action_verbs)
            ),
            "metrics": metrics,
            "achievement_lines": achievement_lines[:20],
            "action_verb_count": len(
                set(action_verbs)
            ),
            "metric_count": len(metrics),
        }

    # ============================================================
    # CONTACT / PROFILE ANALYSIS
    # ============================================================

    @classmethod
    def contact_analysis(
        cls,
        resume_text: str,
    ) -> dict[str, Any]:

        text = cls._clean_text(
            resume_text
        )

        email_found = bool(
            cls.EMAIL_PATTERN.search(text)
        )

        phone_found = bool(
            cls.PHONE_PATTERN.search(text)
        )

        linkedin_found = bool(
            cls.LINKEDIN_PATTERN.search(text)
        )

        github_found = bool(
            cls.GITHUB_PATTERN.search(text)
        )

        checks = {
            "email": email_found,
            "phone": phone_found,
            "linkedin": linkedin_found,
            "github": github_found,
        }

        score = (
            sum(checks.values())
            / len(checks)
            * 100
        )

        return {
            "score": round(score, 2),
            "email": email_found,
            "phone": phone_found,
            "linkedin": linkedin_found,
            "github": github_found,
            "profile_completeness": round(
                score,
                2,
            ),
        }

    # ============================================================
    # WEAK PHRASES
    # ============================================================

    @classmethod
    def detect_weak_phrases(
        cls,
        resume_text: str,
    ) -> list[str]:

        normalized = cls._normalize(
            resume_text
        )

        found = []

        for phrase in cls.WEAK_PHRASES:

            if cls._keyword_exists(
                normalized,
                phrase,
            ):
                found.append(phrase)

        return sorted(found)

    # ============================================================
    # RESUME QUALITY
    # ============================================================

    @classmethod
    def resume_quality(
        cls,
        resume_text: str,
    ) -> dict[str, Any]:

        text = cls._clean_text(
            resume_text
        )

        words = cls._tokenize(text)

        word_count = len(words)

        sections = cls.section_score(
            text
        )

        achievements = cls.achievement_analysis(
            text
        )

        contact = cls.contact_analysis(
            text
        )

        weak_phrases = cls.detect_weak_phrases(
            text
        )

        # Reasonable resume length.
        if 250 <= word_count <= 900:
            length_score = 100
        elif 150 <= word_count <= 1100:
            length_score = 80
        elif 100 <= word_count <= 1300:
            length_score = 60
        else:
            length_score = 40

        score = (
            sections["score"] * 0.35
            + achievements["score"] * 0.30
            + contact["score"] * 0.20
            + length_score * 0.15
        )

        return {
            "score": round(score, 2),
            "word_count": word_count,
            "character_count": len(text),
            "length_score": length_score,
            "section_score": sections["score"],
            "achievement_score": achievements["score"],
            "contact_score": contact["score"],
            "weak_phrases": weak_phrases,
        }

    # ============================================================
    # STRENGTHS
    # ============================================================

    @classmethod
    def generate_strengths(
        cls,
        skill_data: dict[str, Any],
        keyword_data: dict[str, Any],
        achievement_data: dict[str, Any],
        section_data: dict[str, Any],
        contact_data: dict[str, Any],
    ) -> list[str]:

        strengths = []

        if skill_data["coverage"] >= 80:
            strengths.append(
                "Strong alignment with the job's required technical skills."
            )
        elif skill_data["coverage"] >= 60:
            strengths.append(
                "Good coverage of the role's core technical skills."
            )

        if keyword_data["coverage"] >= 70:
            strengths.append(
                "Strong keyword alignment with the job description."
            )

        if achievement_data["metric_count"] >= 2:
            strengths.append(
                "Resume contains measurable achievements and results."
            )

        if achievement_data["action_verb_count"] >= 5:
            strengths.append(
                "Uses strong action-oriented language."
            )

        if section_data["score"] >= 80:
            strengths.append(
                "Resume has a well-structured section layout."
            )

        if contact_data["score"] >= 75:
            strengths.append(
                "Contact and professional profile information is well covered."
            )

        return strengths[:8]

    # ============================================================
    # WEAKNESSES
    # ============================================================

    @classmethod
    def generate_weaknesses(
        cls,
        skill_data: dict[str, Any],
        keyword_data: dict[str, Any],
        achievement_data: dict[str, Any],
        section_data: dict[str, Any],
        contact_data: dict[str, Any],
        weak_phrases: list[str],
    ) -> list[str]:

        weaknesses = []

        if skill_data["coverage"] < 50:
            weaknesses.append(
                "Low alignment with the technical skills requested by the job."
            )
        elif skill_data["coverage"] < 70:
            weaknesses.append(
                "Several important job skills are missing from the resume."
            )

        if keyword_data["coverage"] < 50:
            weaknesses.append(
                "Resume keyword coverage is relatively low."
            )

        if achievement_data["metric_count"] == 0:
            weaknesses.append(
                "No clear measurable achievements were detected."
            )

        if achievement_data["action_verb_count"] < 3:
            weaknesses.append(
                "Experience bullets could use stronger action verbs."
            )

        if section_data["missing_important"]:
            weaknesses.append(
                "Important resume sections are missing: "
                + ", ".join(
                    section_data["missing_important"]
                )
                + "."
            )

        if contact_data["email"] is False:
            weaknesses.append(
                "Professional email address was not detected."
            )

        if weak_phrases:
            weaknesses.append(
                "Generic phrases detected: "
                + ", ".join(weak_phrases[:5])
                + "."
            )

        return weaknesses[:10]

    # ============================================================
    # INSIGHTS
    # ============================================================

    @classmethod
    def generate_insights(
        cls,
        score: float,
        skill_data: dict[str, Any],
        keyword_data: dict[str, Any],
        achievement_data: dict[str, Any],
        section_data: dict[str, Any],
    ) -> list[str]:

        insights = []

        if score >= 85:
            insights.append(
                "Your resume is highly aligned with this target role."
            )
        elif score >= 70:
            insights.append(
                "Your resume has a strong foundation but still has optimization opportunities."
            )
        elif score >= 50:
            insights.append(
                "Your resume shows partial alignment and should be tailored before applying."
            )
        else:
            insights.append(
                "Your resume needs substantial tailoring for this specific role."
            )

        if skill_data["missing_skills"]:
            top_gaps = skill_data[
                "missing_skills"
            ][:5]

            insights.append(
                "Highest-impact skill gaps: "
                + ", ".join(top_gaps)
                + "."
            )

        if keyword_data["missing_keywords"]:
            insights.append(
                f"{len(keyword_data['missing_keywords'])} "
                "important job keywords are not clearly represented."
            )

        if achievement_data["metric_count"] == 0:
            insights.append(
                "Adding quantified results could significantly strengthen your experience section."
            )

        if section_data["score"] < 70:
            insights.append(
                "Improving resume section structure could improve ATS readability."
            )

        return insights[:8]

    # ============================================================
    # RECOMMENDATIONS
    # ============================================================

    @classmethod
    def generate_recommendations(
        cls,
        skill_data: dict[str, Any],
        keyword_data: dict[str, Any],
        achievement_data: dict[str, Any],
        section_data: dict[str, Any],
        contact_data: dict[str, Any],
        weak_phrases: list[str],
    ) -> list[dict[str, Any]]:

        recommendations = []

        if skill_data["missing_skills"]:

            recommendations.append({
                "priority": "critical",
                "category": "skills",
                "title": "Close the biggest skill gaps",
                "description": (
                    "Where truthful and supported by your experience, "
                    "highlight relevant missing skills such as: "
                    + ", ".join(
                        skill_data["missing_skills"][:5]
                    )
                    + "."
                ),
            })

        if keyword_data["missing_keywords"]:

            recommendations.append({
                "priority": "high",
                "category": "keywords",
                "title": "Improve keyword alignment",
                "description": (
                    "Naturally incorporate relevant job-specific terminology "
                    "into your experience, projects, and skills sections."
                ),
            })

        if achievement_data["metric_count"] == 0:

            recommendations.append({
                "priority": "high",
                "category": "achievements",
                "title": "Quantify your impact",
                "description": (
                    "Add measurable outcomes such as performance improvements, "
                    "users served, response-time reductions, revenue, scale, "
                    "or project results where truthful."
                ),
            })

        if achievement_data["action_verb_count"] < 3:

            recommendations.append({
                "priority": "medium",
                "category": "writing",
                "title": "Strengthen experience bullets",
                "description": (
                    "Start important bullets with precise action verbs such as "
                    "built, engineered, optimized, automated, or deployed."
                ),
            })

        if section_data["missing_important"]:

            recommendations.append({
                "priority": "medium",
                "category": "structure",
                "title": "Improve resume structure",
                "description": (
                    "Consider adding clearly labeled sections for: "
                    + ", ".join(
                        section_data["missing_important"]
                    )
                    + "."
                ),
            })

        if not contact_data["email"]:

            recommendations.append({
                "priority": "critical",
                "category": "contact",
                "title": "Add a professional email",
                "description": (
                    "Make sure recruiters can identify a professional email address."
                ),
            })

        if weak_phrases:

            recommendations.append({
                "priority": "low",
                "category": "writing",
                "title": "Replace generic phrases",
                "description": (
                    "Replace vague claims with evidence-based statements "
                    "showing what you actually achieved."
                ),
            })

        priority_order = {
            "critical": 0,
            "high": 1,
            "medium": 2,
            "low": 3,
        }

        recommendations.sort(
            key=lambda item: priority_order[
                item["priority"]
            ]
        )

        return recommendations[:10]

    # ============================================================
    # MAIN ATS ANALYSIS
    # ============================================================

    @classmethod
    def analyze(
        cls,
        resume_text: str,
        job_description: str,
    ) -> dict[str, Any]:
        """
        Complete ResumeAI ATS analysis.

        Returns a structured intelligence report.
        """

        resume_text = cls._clean_text(
            resume_text
        )

        job_description = cls._clean_text(
            job_description
        )

        if not resume_text:
            raise ValueError(
                "Resume text cannot be empty."
            )

        if not job_description:
            raise ValueError(
                "Job description cannot be empty."
            )

        # --------------------------------------------------------
        # Core signals
        # --------------------------------------------------------

        skill_match = SkillService.get_skill_match(
            resume_text,
            job_description,
        )

        keyword_data = cls.keyword_analysis(
            resume_text,
            job_description,
        )

        semantic_score = (
            cls.calculate_semantic_similarity(
                resume_text,
                job_description,
            )
        )

        section_data = cls.section_score(
            resume_text
        )

        achievement_data = cls.achievement_analysis(
            resume_text
        )

        contact_data = cls.contact_analysis(
            resume_text
        )

        quality_data = cls.resume_quality(
            resume_text
        )

        weak_phrases = quality_data[
            "weak_phrases"
        ]

        # --------------------------------------------------------
        # Skill gaps
        # --------------------------------------------------------

        skill_gaps = SkillService.analyze_skill_gaps(
            resume_text,
            job_description,
        )

        # --------------------------------------------------------
        # Final weighted score
        # --------------------------------------------------------

        skills_score = skill_match["coverage"]

        keywords_score = keyword_data[
            "coverage"
        ]

        overall_score = (
            skills_score
            * cls.WEIGHTS["skills"]
            +
            keywords_score
            * cls.WEIGHTS["keywords"]
            +
            semantic_score
            * cls.WEIGHTS["semantic"]
            +
            section_data["score"]
            * cls.WEIGHTS["sections"]
            +
            achievement_data["score"]
            * cls.WEIGHTS["achievements"]
            +
            contact_data["score"]
            * cls.WEIGHTS["contact"]
        )

        overall_score = round(
            min(100.0, max(0.0, overall_score)),
            2,
        )

        # --------------------------------------------------------
        # Strengths / weaknesses / insights
        # --------------------------------------------------------

        strengths = cls.generate_strengths(
            skill_match,
            keyword_data,
            achievement_data,
            section_data,
            contact_data,
        )

        weaknesses = cls.generate_weaknesses(
            skill_match,
            keyword_data,
            achievement_data,
            section_data,
            contact_data,
            weak_phrases,
        )

        insights = cls.generate_insights(
            overall_score,
            skill_match,
            keyword_data,
            achievement_data,
            section_data,
        )

        recommendations = cls.generate_recommendations(
            skill_match,
            keyword_data,
            achievement_data,
            section_data,
            contact_data,
            weak_phrases,
        )

        # --------------------------------------------------------
        # Final response
        # --------------------------------------------------------

        return {
            "overall_score": overall_score,

            "score_label": cls.get_score_label(
                overall_score
            ),

            "skills_score": round(
                skills_score,
                2,
            ),

            "keyword_score": round(
                keywords_score,
                2,
            ),

            "semantic_score": round(
                semantic_score,
                2,
            ),

            "section_score": round(
                section_data["score"],
                2,
            ),

            "achievement_score": round(
                achievement_data["score"],
                2,
            ),

            "contact_score": round(
                contact_data["score"],
                2,
            ),

            "content_score": round(
                quality_data["score"],
                2,
            ),

            "skill_alignment": skill_match,

            "matched_skills": skill_match[
                "matched_skills"
            ],

            "missing_skills": skill_match[
                "missing_skills"
            ],

            "additional_skills": skill_match[
                "additional_skills"
            ],

            "skill_gaps": skill_gaps,

            "keyword_analysis": keyword_data,

            "detected_keywords": keyword_data[
                "matched_keywords"
            ],

            "missing_keywords": keyword_data[
                "missing_keywords"
            ],

            "semantic_relevance": semantic_score,

            "sections": section_data,

            "achievements": achievement_data,

            "contact": contact_data,

            "resume_quality": quality_data,

            "strengths": strengths,

            "weaknesses": weaknesses,

            "insights": insights,

            "recommendations": recommendations,

            "score_breakdown": {
                "skills": round(
                    skills_score,
                    2,
                ),
                "keywords": round(
                    keywords_score,
                    2,
                ),
                "semantic": round(
                    semantic_score,
                    2,
                ),
                "sections": round(
                    section_data["score"],
                    2,
                ),
                "achievements": round(
                    achievement_data["score"],
                    2,
                ),
                "contact": round(
                    contact_data["score"],
                    2,
                ),
            },
        }

    # ============================================================
    # SCORE LABEL
    # ============================================================

    @staticmethod
    def get_score_label(
        score: float,
    ) -> str:

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

        if score >= 35:
            return "Weak"

        return "Critical"

    # ============================================================
    # MEANINGFUL TOKEN EXTRACTION
    # ============================================================

    @classmethod
    def _meaningful_tokens(
        cls,
        text: str,
    ) -> list[str]:

        tokens = cls._tokenize(text)

        stop_words = {
            "the",
            "and",
            "for",
            "with",
            "that",
            "this",
            "from",
            "are",
            "you",
            "your",
            "our",
            "their",
            "have",
            "has",
            "will",
            "can",
            "should",
            "would",
            "into",
            "using",
            "used",
            "use",
            "job",
            "role",
            "work",
            "working",
            "team",
            "about",
            "years",
            "year",
            "experience",
            "required",
            "requirements",
            "responsibilities",
        }

        return [
            token
            for token in tokens
            if len(token) >= 2
            and token not in stop_words
        ]