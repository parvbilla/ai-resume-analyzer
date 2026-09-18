from __future__ import annotations

from typing import Any


class SuggestionService:
    """
    Ultra-Pro Resume Recommendation Engine.

    Converts ATS analysis into:
    - prioritized recommendations
    - actionable fixes
    - skill-gap actions
    - keyword actions
    - content improvements
    - section improvements
    - achievement improvements
    - contact/profile improvements
    - quick wins
    - impact estimates
    - structured recommendation objects

    Designed to work with the upgraded ATSService.
    """

    # ============================================================
    # CONFIGURATION
    # ============================================================

    PRIORITY_ORDER = {
        "critical": 0,
        "high": 1,
        "medium": 2,
        "low": 3,
    }

    # ============================================================
    # MAIN GENERATOR
    # ============================================================

    @classmethod
    def generate(
        cls,
        match_percentage: float = 0,
        missing_skills: list[str] | None = None,
        advanced_analysis: dict[str, Any] | None = None,
    ) -> list[Any]:
        """
        Generate intelligent resume recommendations.

        Supports both:

            SuggestionService.generate(score, missing_skills)

        and:

            SuggestionService.generate(
                overall_score,
                missing_skills,
                advanced_analysis
            )

        Returns a list of structured recommendation objects.
        """

        missing_skills = missing_skills or []
        analysis = advanced_analysis or {}

        recommendations: list[dict[str, Any]] = []

        # --------------------------------------------------------
        # Extract available analysis
        # --------------------------------------------------------

        skill_data = cls._get_section(
            analysis,
            "skill_alignment",
        )

        keyword_data = cls._get_section(
            analysis,
            "keyword_analysis",
        )

        section_data = cls._get_section(
            analysis,
            "sections",
        )

        achievement_data = cls._get_section(
            analysis,
            "achievements",
        )

        contact_data = cls._get_section(
            analysis,
            "contact",
        )

        quality_data = cls._get_section(
            analysis,
            "resume_quality",
        )

        # --------------------------------------------------------
        # Score-based recommendations
        # --------------------------------------------------------

        recommendations.extend(
            cls._score_recommendations(
                match_percentage
            )
        )

        # --------------------------------------------------------
        # Skill recommendations
        # --------------------------------------------------------

        recommendations.extend(
            cls._skill_recommendations(
                missing_skills,
                skill_data,
                analysis,
            )
        )

        # --------------------------------------------------------
        # Keyword recommendations
        # --------------------------------------------------------

        recommendations.extend(
            cls._keyword_recommendations(
                keyword_data
            )
        )

        # --------------------------------------------------------
        # Section recommendations
        # --------------------------------------------------------

        recommendations.extend(
            cls._section_recommendations(
                section_data
            )
        )

        # --------------------------------------------------------
        # Achievement recommendations
        # --------------------------------------------------------

        recommendations.extend(
            cls._achievement_recommendations(
                achievement_data
            )
        )

        # --------------------------------------------------------
        # Contact recommendations
        # --------------------------------------------------------

        recommendations.extend(
            cls._contact_recommendations(
                contact_data
            )
        )

        # --------------------------------------------------------
        # Resume quality recommendations
        # --------------------------------------------------------

        recommendations.extend(
            cls._quality_recommendations(
                quality_data
            )
        )

        # --------------------------------------------------------
        # Final processing
        # --------------------------------------------------------

        recommendations = cls._deduplicate(
            recommendations
        )

        recommendations = cls._sort(
            recommendations
        )

        # Limit dashboard output.
        return recommendations[:12]

    # ============================================================
    # SCORE RECOMMENDATIONS
    # ============================================================

    @classmethod
    def _score_recommendations(
        cls,
        score: float,
    ) -> list[dict[str, Any]]:

        recommendations = []

        score = cls._safe_score(score)

        if score < 35:

            recommendations.append(
                cls._recommendation(
                    priority="critical",
                    category="overall",
                    title="Retarget your resume",
                    description=(
                        "Your resume has low alignment with the target role. "
                        "Tailor your skills, projects, experience bullets, "
                        "and terminology to the job description."
                    ),
                    action="Create a role-specific version of your resume.",
                    impact=95,
                )
            )

        elif score < 50:

            recommendations.append(
                cls._recommendation(
                    priority="critical",
                    category="overall",
                    title="Increase role alignment",
                    description=(
                        "The resume currently matches only part of the "
                        "target role. Focus first on high-value skills "
                        "and job-specific keywords."
                    ),
                    action="Prioritize the largest ATS gaps before applying.",
                    impact=85,
                )
            )

        elif score < 70:

            recommendations.append(
                cls._recommendation(
                    priority="high",
                    category="overall",
                    title="Tailor the resume further",
                    description=(
                        "Your resume has a reasonable foundation, "
                        "but additional role-specific tailoring could "
                        "improve ATS performance."
                    ),
                    action="Review missing skills and keywords first.",
                    impact=75,
                )
            )

        elif score < 85:

            recommendations.append(
                cls._recommendation(
                    priority="medium",
                    category="overall",
                    title="Polish your strongest areas",
                    description=(
                        "Your resume is well aligned. Focus on measurable "
                        "achievements, precise wording, and remaining gaps."
                    ),
                    action="Optimize the weakest scoring categories.",
                    impact=55,
                )
            )

        else:

            recommendations.append(
                cls._recommendation(
                    priority="low",
                    category="overall",
                    title="Perform final optimization",
                    description=(
                        "Your resume is strongly aligned with the target role. "
                        "Focus on small improvements rather than major rewrites."
                    ),
                    action="Polish achievements and remove unnecessary content.",
                    impact=30,
                )
            )

        return recommendations

    # ============================================================
    # SKILL RECOMMENDATIONS
    # ============================================================

    @classmethod
    def _skill_recommendations(
        cls,
        missing_skills: list[str],
        skill_data: dict[str, Any],
        analysis: dict[str, Any],
    ) -> list[dict[str, Any]]:

        recommendations = []

        # Prefer richer skill-gap information when available.
        skill_gaps = analysis.get(
            "skill_gaps",
            [],
        )

        if skill_gaps:

            critical = [
                item.get("skill")
                for item in skill_gaps
                if item.get("priority") == "critical"
            ]

            high = [
                item.get("skill")
                for item in skill_gaps
                if item.get("priority") == "high"
            ]

            if critical:

                recommendations.append(
                    cls._recommendation(
                        priority="critical",
                        category="skills",
                        title="Address critical skill gaps",
                        description=(
                            "These skills appear especially important "
                            "for the target role: "
                            + cls._format_items(critical[:5])
                            + "."
                        ),
                        action=(
                            "If you genuinely have this experience, "
                            "surface it prominently. Otherwise, consider "
                            "learning the highest-value skill."
                        ),
                        impact=90,
                        related_items=critical[:5],
                    )
                )

            if high:

                recommendations.append(
                    cls._recommendation(
                        priority="high",
                        category="skills",
                        title="Improve high-impact skill coverage",
                        description=(
                            "Important skills missing from the resume include "
                            + cls._format_items(high[:5])
                            + "."
                        ),
                        action=(
                            "Add truthful evidence from projects, internships, "
                            "work, or coursework where applicable."
                        ),
                        impact=80,
                        related_items=high[:5],
                    )
                )

        elif missing_skills:

            recommendations.append(
                cls._recommendation(
                    priority="high",
                    category="skills",
                    title="Highlight missing role skills",
                    description=(
                        "The job description contains skills that are not "
                        "clearly represented in your resume: "
                        + cls._format_items(
                            missing_skills[:8]
                        )
                        + "."
                    ),
                    action=(
                        "Only add skills you genuinely know. "
                        "Where applicable, connect them to projects "
                        "or experience."
                    ),
                    impact=80,
                    related_items=missing_skills[:8],
                )
            )

        return recommendations

    # ============================================================
    # KEYWORD RECOMMENDATIONS
    # ============================================================

    @classmethod
    def _keyword_recommendations(
        cls,
        keyword_data: dict[str, Any],
    ) -> list[dict[str, Any]]:

        if not keyword_data:
            return []

        coverage = cls._safe_score(
            keyword_data.get(
                "coverage",
                0,
            )
        )

        missing = keyword_data.get(
            "missing_keywords",
            [],
        )

        if coverage < 40:

            return [
                cls._recommendation(
                    priority="critical",
                    category="keywords",
                    title="Improve ATS keyword coverage",
                    description=(
                        "A significant portion of job-specific terminology "
                        "is missing from the resume."
                    ),
                    action=(
                        "Naturally incorporate relevant keywords into "
                        "your summary, skills, projects, and experience."
                    ),
                    impact=90,
                    related_items=missing[:10],
                )
            ]

        if coverage < 65:

            return [
                cls._recommendation(
                    priority="high",
                    category="keywords",
                    title="Strengthen keyword alignment",
                    description=(
                        "Your keyword coverage is moderate and can be improved."
                    ),
                    action=(
                        "Review missing keywords and add only those that "
                        "accurately describe your experience."
                    ),
                    impact=75,
                    related_items=missing[:8],
                )
            ]

        if coverage < 80:

            return [
                cls._recommendation(
                    priority="medium",
                    category="keywords",
                    title="Polish job-specific terminology",
                    description=(
                        "Most important terminology is covered, but some "
                        "relevant keywords are still missing."
                    ),
                    action=(
                        "Add remaining relevant terms naturally instead of "
                        "keyword stuffing."
                    ),
                    impact=50,
                    related_items=missing[:6],
                )
            ]

        return []

    # ============================================================
    # SECTION RECOMMENDATIONS
    # ============================================================

    @classmethod
    def _section_recommendations(
        cls,
        section_data: dict[str, Any],
    ) -> list[dict[str, Any]]:

        if not section_data:
            return []

        missing = section_data.get(
            "missing_important",
            [],
        )

        score = cls._safe_score(
            section_data.get(
                "score",
                0,
            )
        )

        if not missing and score >= 80:
            return []

        if missing:

            return [
                cls._recommendation(
                    priority="medium",
                    category="structure",
                    title="Improve resume structure",
                    description=(
                        "Important resume sections were not clearly detected: "
                        + cls._format_items(missing)
                        + "."
                    ),
                    action=(
                        "Use clear, conventional section headings so ATS "
                        "systems and recruiters can scan the resume easily."
                    ),
                    impact=60,
                    related_items=missing,
                )
            ]

        return []

    # ============================================================
    # ACHIEVEMENT RECOMMENDATIONS
    # ============================================================

    @classmethod
    def _achievement_recommendations(
        cls,
        achievement_data: dict[str, Any],
    ) -> list[dict[str, Any]]:

        if not achievement_data:
            return []

        metrics = achievement_data.get(
            "metric_count",
            0,
        )

        action_verbs = achievement_data.get(
            "action_verb_count",
            0,
        )

        recommendations = []

        if metrics == 0:

            recommendations.append(
                cls._recommendation(
                    priority="high",
                    category="achievements",
                    title="Add measurable results",
                    description=(
                        "Your resume does not contain enough clearly "
                        "detectable quantified outcomes."
                    ),
                    action=(
                        "Where truthful, quantify impact using percentages, "
                        "time saved, performance improvements, users, scale, "
                        "revenue, or other measurable results."
                    ),
                    impact=85,
                )
            )

        elif metrics < 3:

            recommendations.append(
                cls._recommendation(
                    priority="medium",
                    category="achievements",
                    title="Increase quantified impact",
                    description=(
                        "Some measurable evidence is present, but more "
                        "results-focused bullets could strengthen the resume."
                    ),
                    action=(
                        "Convert responsibility-focused bullets into "
                        "action + technology + measurable result statements."
                    ),
                    impact=65,
                )
            )

        if action_verbs < 3:

            recommendations.append(
                cls._recommendation(
                    priority="medium",
                    category="writing",
                    title="Use stronger action verbs",
                    description=(
                        "The resume contains relatively few strong "
                        "action-oriented verbs."
                    ),
                    action=(
                        "Start experience and project bullets with verbs "
                        "such as built, engineered, optimized, automated, "
                        "designed, deployed, or improved."
                    ),
                    impact=55,
                )
            )

        return recommendations

    # ============================================================
    # CONTACT RECOMMENDATIONS
    # ============================================================

    @classmethod
    def _contact_recommendations(
        cls,
        contact_data: dict[str, Any],
    ) -> list[dict[str, Any]]:

        if not contact_data:
            return []

        recommendations = []

        if not contact_data.get("email"):

            recommendations.append(
                cls._recommendation(
                    priority="critical",
                    category="contact",
                    title="Add a professional email",
                    description=(
                        "A professional email address was not detected."
                    ),
                    action=(
                        "Add a recruiter-friendly email address near "
                        "your name at the top of the resume."
                    ),
                    impact=90,
                )
            )

        if not contact_data.get("phone"):

            recommendations.append(
                cls._recommendation(
                    priority="high",
                    category="contact",
                    title="Add a phone number",
                    description=(
                        "A phone number was not detected in the resume."
                    ),
                    action=(
                        "Add a current professional phone number "
                        "with your location if appropriate."
                    ),
                    impact=70,
                )
            )

        if not contact_data.get("linkedin"):

            recommendations.append(
                cls._recommendation(
                    priority="medium",
                    category="contact",
                    title="Add your LinkedIn profile",
                    description=(
                        "A LinkedIn profile was not detected."
                    ),
                    action=(
                        "Include a clean LinkedIn URL if you maintain "
                        "an up-to-date professional profile."
                    ),
                    impact=45,
                )
            )

        if not contact_data.get("github"):

            recommendations.append(
                cls._recommendation(
                    priority="low",
                    category="contact",
                    title="Consider adding GitHub",
                    description=(
                        "A GitHub profile was not detected."
                    ),
                    action=(
                        "For software roles, include GitHub when it "
                        "contains relevant, polished work."
                    ),
                    impact=35,
                )
            )

        return recommendations

    # ============================================================
    # QUALITY RECOMMENDATIONS
    # ============================================================

    @classmethod
    def _quality_recommendations(
        cls,
        quality_data: dict[str, Any],
    ) -> list[dict[str, Any]]:

        if not quality_data:
            return []

        recommendations = []

        word_count = quality_data.get(
            "word_count",
            0,
        )

        weak_phrases = quality_data.get(
            "weak_phrases",
            [],
        )

        if word_count < 150:

            recommendations.append(
                cls._recommendation(
                    priority="high",
                    category="content",
                    title="Add stronger supporting content",
                    description=(
                        "The resume appears unusually short based on "
                        "the extracted text."
                    ),
                    action=(
                        "Add relevant projects, achievements, technical "
                        "skills, or experience rather than filler."
                    ),
                    impact=70,
                )
            )

        elif word_count > 1300:

            recommendations.append(
                cls._recommendation(
                    priority="medium",
                    category="content",
                    title="Reduce unnecessary content",
                    description=(
                        "The resume appears lengthy and may contain "
                        "content that can be made more concise."
                    ),
                    action=(
                        "Remove repetition and prioritize accomplishments "
                        "directly relevant to the target role."
                    ),
                    impact=55,
                )
            )

        if weak_phrases:

            recommendations.append(
                cls._recommendation(
                    priority="medium",
                    category="writing",
                    title="Replace generic claims",
                    description=(
                        "Generic phrases were detected: "
                        + cls._format_items(
                            weak_phrases[:6]
                        )
                        + "."
                    ),
                    action=(
                        "Replace generic claims with concrete evidence "
                        "showing what you built, improved, or achieved."
                    ),
                    impact=60,
                    related_items=weak_phrases[:6],
                )
            )

        return recommendations

    # ============================================================
    # QUICK WINS
    # ============================================================

    @classmethod
    def quick_wins(
        cls,
        analysis: dict[str, Any],
    ) -> list[dict[str, Any]]:

        recommendations = cls.generate(
            analysis.get("overall_score", 0),
            analysis.get("missing_skills", []),
            analysis,
        )

        quick = [
            recommendation
            for recommendation in recommendations
            if recommendation.get("impact", 0) >= 50
            and recommendation.get("priority")
            in {"critical", "high", "medium"}
        ]

        return quick[:5]

    # ============================================================
    # ACTION PLAN
    # ============================================================

    @classmethod
    def action_plan(
        cls,
        analysis: dict[str, Any],
    ) -> dict[str, Any]:

        recommendations = cls.generate(
            analysis.get("overall_score", 0),
            analysis.get("missing_skills", []),
            analysis,
        )

        critical = [
            item
            for item in recommendations
            if item["priority"] == "critical"
        ]

        high = [
            item
            for item in recommendations
            if item["priority"] == "high"
        ]

        medium = [
            item
            for item in recommendations
            if item["priority"] == "medium"
        ]

        low = [
            item
            for item in recommendations
            if item["priority"] == "low"
        ]

        return {
            "total_actions": len(recommendations),
            "critical": critical,
            "high": high,
            "medium": medium,
            "low": low,
            "quick_wins": cls.quick_wins(
                analysis
            ),
            "next_best_action": (
                recommendations[0]
                if recommendations
                else None
            ),
        }

    # ============================================================
    # SCORE IMPROVEMENT ESTIMATE
    # ============================================================

    @classmethod
    def estimate_improvement(
        cls,
        analysis: dict[str, Any],
    ) -> dict[str, Any]:

        current = cls._safe_score(
            analysis.get(
                "overall_score",
                0,
            )
        )

        recommendations = cls.generate(
            current,
            analysis.get(
                "missing_skills",
                [],
            ),
            analysis,
        )

        potential_gain = 0

        for item in recommendations:

            priority = item.get(
                "priority",
                "low",
            )

            if priority == "critical":
                potential_gain += 8

            elif priority == "high":
                potential_gain += 5

            elif priority == "medium":
                potential_gain += 3

            else:
                potential_gain += 1

        potential_gain = min(
            potential_gain,
            25,
        )

        projected = min(
            100,
            current + potential_gain,
        )

        return {
            "current_score": round(
                current,
                2,
            ),
            "estimated_gain": potential_gain,
            "projected_score": round(
                projected,
                2,
            ),
        }

    # ============================================================
    # RECOMMENDATION FACTORY
    # ============================================================

    @staticmethod
    def _recommendation(
        priority: str,
        category: str,
        title: str,
        description: str,
        action: str,
        impact: int,
        related_items: list[str] | None = None,
    ) -> dict[str, Any]:

        return {
            "priority": priority,
            "category": category,
            "title": title,
            "description": description,
            "action": action,
            "impact": max(
                0,
                min(100, int(impact)),
            ),
            "related_items": related_items or [],
        }

    # ============================================================
    # HELPERS
    # ============================================================

    @staticmethod
    def _get_section(
        analysis: dict[str, Any],
        key: str,
    ) -> dict[str, Any]:

        value = analysis.get(key)

        if isinstance(value, dict):
            return value

        return {}

    @staticmethod
    def _safe_score(
        value: Any,
    ) -> float:

        try:
            return max(
                0.0,
                min(
                    100.0,
                    float(value or 0),
                ),
            )
        except (
            TypeError,
            ValueError,
        ):
            return 0.0

    @staticmethod
    def _format_items(
        items: list[str],
    ) -> str:

        if not items:
            return "none"

        return ", ".join(
            str(item)
            for item in items
        )

    @classmethod
    def _sort(
        cls,
        recommendations: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:

        return sorted(
            recommendations,
            key=lambda item: (
                cls.PRIORITY_ORDER.get(
                    item.get(
                        "priority",
                        "low",
                    ),
                    3,
                ),
                -int(
                    item.get(
                        "impact",
                        0,
                    )
                ),
            ),
        )

    @staticmethod
    def _deduplicate(
        recommendations: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:

        seen = set()
        unique = []

        for recommendation in recommendations:

            key = (
                recommendation.get("category"),
                recommendation.get("title"),
            )

            if key in seen:
                continue

            seen.add(key)
            unique.append(recommendation)

        return unique