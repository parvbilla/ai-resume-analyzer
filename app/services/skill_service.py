from __future__ import annotations

import re
from collections import Counter
from typing import Any


class SkillService:
    """
    Ultra-Pro ATS Skill Intelligence Engine.

    Features:
    - Canonical skill normalization
    - Large technical skill taxonomy
    - Alias recognition
    - Safe matching for C++, C#, Node.js, etc.
    - Skill frequency detection
    - Required vs optional skill analysis
    - Missing skill detection
    - Matched skill detection
    - Skill coverage percentage
    - Priority scoring
    - Category classification
    - Evidence/context detection
    - Skill gap intelligence
    """

    # ============================================================
    # SKILL TAXONOMY
    # ============================================================

    SKILL_ALIASES: dict[str, list[str]] = {

        # --------------------------------------------------------
        # PROGRAMMING LANGUAGES
        # --------------------------------------------------------

        "python": ["python", "python3", "python 3"],
        "java": ["java"],
        "javascript": ["javascript", "js", "ecmascript"],
        "typescript": ["typescript", "ts"],
        "c++": ["c++", "cpp"],
        "c#": ["c#", "c sharp", "csharp"],
        "go": ["golang", "go language"],
        "rust": ["rust"],
        "php": ["php"],
        "ruby": ["ruby"],
        "kotlin": ["kotlin"],
        "swift": ["swift"],
        "dart": ["dart"],
        "r": ["r programming", "r language"],

        # --------------------------------------------------------
        # FRONTEND
        # --------------------------------------------------------

        "html": ["html", "html5"],
        "css": ["css", "css3"],
        "sass": ["sass", "scss"],
        "tailwind css": ["tailwind", "tailwind css"],
        "bootstrap": ["bootstrap"],
        "react": ["react", "react.js", "reactjs"],
        "next.js": ["next.js", "nextjs", "next js"],
        "vue.js": ["vue", "vue.js", "vuejs"],
        "angular": ["angular", "angular.js", "angularjs"],
        "redux": ["redux", "redux toolkit", "rtk"],
        "zustand": ["zustand"],
        "material ui": ["material ui", "mui"],
        "framer motion": ["framer motion", "framer-motion"],

        # --------------------------------------------------------
        # BACKEND
        # --------------------------------------------------------

        "node.js": ["node.js", "nodejs", "node js"],
        "express": ["express", "express.js", "expressjs"],
        "fastapi": ["fastapi", "fast api"],
        "django": ["django"],
        "flask": ["flask"],
        "spring boot": ["spring boot", "springboot"],
        "nestjs": ["nestjs", "nest.js"],
        "laravel": ["laravel"],
        "asp.net": ["asp.net", "aspnet"],

        # --------------------------------------------------------
        # DATABASES
        # --------------------------------------------------------

        "sql": ["sql"],
        "mysql": ["mysql", "my sql"],
        "postgresql": ["postgresql", "postgres", "postgre sql"],
        "mongodb": ["mongodb", "mongo db", "mongo"],
        "sqlite": ["sqlite"],
        "redis": ["redis"],
        "firebase": ["firebase"],
        "supabase": ["supabase"],
        "dynamodb": ["dynamodb", "dynamo db"],
        "oracle": ["oracle database", "oracle db"],

        # --------------------------------------------------------
        # API / ARCHITECTURE
        # --------------------------------------------------------

        "rest api": [
            "rest api",
            "restful api",
            "restful services",
            "rest services",
        ],
        "graphql": ["graphql"],
        "websocket": ["websocket", "websockets"],
        "microservices": [
            "microservices",
            "microservices architecture",
        ],
        "api design": ["api design"],
        "system design": ["system design"],
        "event driven architecture": [
            "event driven architecture",
            "event-driven architecture",
        ],

        # --------------------------------------------------------
        # CLOUD / DEVOPS
        # --------------------------------------------------------

        "aws": ["aws", "amazon web services"],
        "azure": ["azure", "microsoft azure"],
        "gcp": ["gcp", "google cloud", "google cloud platform"],
        "docker": ["docker", "containerization"],
        "kubernetes": ["kubernetes", "k8s"],
        "jenkins": ["jenkins"],
        "github actions": ["github actions", "github action"],
        "gitlab ci": ["gitlab ci", "gitlab pipelines"],
        "ci/cd": [
            "ci/cd",
            "ci cd",
            "cicd",
            "continuous integration",
            "continuous deployment",
        ],
        "terraform": ["terraform"],
        "ansible": ["ansible"],
        "linux": ["linux"],
        "bash": ["bash", "shell scripting", "shell script"],
        "powershell": ["powershell"],

        # --------------------------------------------------------
        # VERSION CONTROL
        # --------------------------------------------------------

        "git": ["git"],
        "github": ["github", "git hub"],
        "gitlab": ["gitlab"],
        "bitbucket": ["bitbucket"],

        # --------------------------------------------------------
        # DATA / AI / ML
        # --------------------------------------------------------

        "machine learning": [
            "machine learning",
            "machine-learning",
        ],
        "deep learning": [
            "deep learning",
            "deep-learning",
        ],
        "artificial intelligence": [
            "artificial intelligence",
            "artificial intelligence",
            "ai",
        ],
        "nlp": [
            "nlp",
            "natural language processing",
        ],
        "computer vision": [
            "computer vision",
            "computer-vision",
        ],
        "pandas": ["pandas"],
        "numpy": ["numpy"],
        "scikit-learn": [
            "scikit-learn",
            "sklearn",
            "scikit learn",
        ],
        "tensorflow": ["tensorflow"],
        "pytorch": ["pytorch", "py torch"],
        "keras": ["keras"],
        "opencv": ["opencv", "open cv"],
        "matplotlib": ["matplotlib"],
        "seaborn": ["seaborn"],

        # --------------------------------------------------------
        # CS FUNDAMENTALS
        # --------------------------------------------------------

        "oop": [
            "oop",
            "object oriented programming",
            "object-oriented programming",
        ],
        "data structures": [
            "data structures",
            "data structure",
        ],
        "algorithms": [
            "algorithms",
            "algorithm",
        ],
        "dsa": [
            "dsa",
            "data structures and algorithms",
        ],
        "operating systems": [
            "operating systems",
            "operating system",
        ],
        "computer networks": [
            "computer networks",
            "computer networking",
        ],
        "database management": [
            "database management",
            "dbms",
            "database management systems",
        ],

        # --------------------------------------------------------
        # SECURITY / AUTH
        # --------------------------------------------------------

        "jwt": [
            "jwt",
            "json web token",
            "json web tokens",
        ],
        "oauth": [
            "oauth",
            "oauth2",
            "oauth 2.0",
        ],
        "authentication": [
            "authentication",
            "user authentication",
        ],
        "authorization": [
            "authorization",
            "role based authorization",
            "rbac",
        ],
        "cybersecurity": [
            "cybersecurity",
            "cyber security",
        ],

        # --------------------------------------------------------
        # TESTING
        # --------------------------------------------------------

        "jest": ["jest"],
        "cypress": ["cypress"],
        "playwright": ["playwright"],
        "pytest": ["pytest"],
        "unit testing": [
            "unit testing",
            "unit tests",
        ],
        "integration testing": [
            "integration testing",
            "integration tests",
        ],

        # --------------------------------------------------------
        # PRODUCTIVITY / DESIGN
        # --------------------------------------------------------

        "figma": ["figma"],
        "agile": ["agile", "agile methodology"],
        "scrum": ["scrum"],
        "jira": ["jira"],
        "postman": ["postman"],
    }

    # ============================================================
    # SKILL CATEGORIES
    # ============================================================

    SKILL_CATEGORIES = {
        "programming": {
            "python", "java", "javascript", "typescript",
            "c++", "c#", "go", "rust", "php", "ruby",
            "kotlin", "swift", "dart", "r",
        },

        "frontend": {
            "html", "css", "sass", "tailwind css",
            "bootstrap", "react", "next.js", "vue.js",
            "angular", "redux", "zustand",
            "material ui", "framer motion",
        },

        "backend": {
            "node.js", "express", "fastapi", "django",
            "flask", "spring boot", "nestjs",
            "laravel", "asp.net",
        },

        "database": {
            "sql", "mysql", "postgresql", "mongodb",
            "sqlite", "redis", "firebase",
            "supabase", "dynamodb", "oracle",
        },

        "cloud_devops": {
            "aws", "azure", "gcp", "docker",
            "kubernetes", "jenkins", "github actions",
            "gitlab ci", "ci/cd", "terraform",
            "ansible", "linux", "bash", "powershell",
        },

        "api_architecture": {
            "rest api", "graphql", "websocket",
            "microservices", "api design",
            "system design",
            "event driven architecture",
        },

        "ai_data": {
            "machine learning", "deep learning",
            "artificial intelligence", "nlp",
            "computer vision", "pandas", "numpy",
            "scikit-learn", "tensorflow", "pytorch",
            "keras", "opencv", "matplotlib", "seaborn",
        },

        "computer_science": {
            "oop", "data structures", "algorithms",
            "dsa", "operating systems",
            "computer networks", "database management",
        },

        "security": {
            "jwt", "oauth", "authentication",
            "authorization", "cybersecurity",
        },

        "testing": {
            "jest", "cypress", "playwright",
            "pytest", "unit testing",
            "integration testing",
        },

        "tools": {
            "git", "github", "gitlab", "bitbucket",
            "postman", "figma", "jira",
        },
    }

    # ============================================================
    # ACTION VERBS / EVIDENCE
    # ============================================================

    STRONG_ACTION_VERBS = {
        "built", "developed", "designed", "implemented",
        "engineered", "architected", "optimized",
        "automated", "deployed", "integrated",
        "created", "delivered", "improved",
        "reduced", "increased", "led", "managed",
        "launched", "migrated", "refactored",
    }

    # ============================================================
    # NORMALIZATION
    # ============================================================

    @staticmethod
    def _normalize_text(text: str) -> str:
        if not text:
            return ""

        text = text.lower()

        text = (
            text.replace("\u00a0", " ")
            .replace("–", "-")
            .replace("—", "-")
        )

        text = re.sub(r"\s+", " ", text)

        return text.strip()

    @classmethod
    def _contains_skill(cls, text: str, alias: str) -> bool:
        """
        Robust skill matching.

        Important:
        We do NOT use \\b because it breaks skills like:
        - C++
        - C#
        - Node.js
        - Next.js
        """

        normalized_text = cls._normalize_text(text)
        normalized_alias = cls._normalize_text(alias)

        if not normalized_text or not normalized_alias:
            return False

        pattern = rf"(?<!\w){re.escape(normalized_alias)}(?!\w)"

        return re.search(
            pattern,
            normalized_text,
            flags=re.IGNORECASE,
        ) is not None

    # ============================================================
    # BASIC EXTRACTION
    # ============================================================

    @classmethod
    def extract_skills(cls, text: str) -> list[str]:
        """
        Extract canonical skills from text.
        """

        if not text:
            return []

        detected: list[str] = []

        for skill, aliases in cls.SKILL_ALIASES.items():
            if any(
                cls._contains_skill(text, alias)
                for alias in aliases
            ):
                detected.append(skill)

        return sorted(set(detected))

    # ============================================================
    # SKILL FREQUENCY
    # ============================================================

    @classmethod
    def skill_frequency(
        cls,
        text: str,
    ) -> dict[str, int]:
        """
        Count how frequently each canonical skill appears.
        """

        if not text:
            return {}

        normalized_text = cls._normalize_text(text)

        frequencies: dict[str, int] = {}

        for skill, aliases in cls.SKILL_ALIASES.items():

            count = 0

            for alias in aliases:
                normalized_alias = cls._normalize_text(alias)

                if not normalized_alias:
                    continue

                pattern = rf"(?<!\w){re.escape(normalized_alias)}(?!\w)"

                count += len(
                    re.findall(
                        pattern,
                        normalized_text,
                        flags=re.IGNORECASE,
                    )
                )

            if count:
                frequencies[skill] = count

        return dict(
            sorted(
                frequencies.items(),
                key=lambda item: item[1],
                reverse=True,
            )
        )

    # ============================================================
    # CATEGORY DETECTION
    # ============================================================

    @classmethod
    def categorize_skills(
        cls,
        skills: list[str],
    ) -> dict[str, list[str]]:
        """
        Group detected skills by technical category.
        """

        skill_set = set(skills)

        result: dict[str, list[str]] = {}

        for category, category_skills in cls.SKILL_CATEGORIES.items():

            matches = sorted(
                skill_set.intersection(category_skills)
            )

            if matches:
                result[category] = matches

        return result

    # ============================================================
    # MATCHED / MISSING
    # ============================================================

    @classmethod
    def get_skill_match(
        cls,
        resume_text: str,
        job_description: str,
    ) -> dict[str, Any]:
        """
        Complete resume-vs-JD skill comparison.
        """

        resume_skills = set(
            cls.extract_skills(resume_text)
        )

        job_skills = set(
            cls.extract_skills(job_description)
        )

        matched = sorted(
            resume_skills.intersection(job_skills)
        )

        missing = sorted(
            job_skills - resume_skills
        )

        extra = sorted(
            resume_skills - job_skills
        )

        coverage = (
            len(matched) / len(job_skills) * 100
            if job_skills
            else 0
        )

        return {
            "resume_skills": sorted(resume_skills),
            "required_skills": sorted(job_skills),
            "matched_skills": matched,
            "missing_skills": missing,
            "additional_skills": extra,
            "coverage": round(coverage, 2),
            "required_count": len(job_skills),
            "matched_count": len(matched),
            "missing_count": len(missing),
        }

    # ============================================================
    # MISSING SKILLS
    # ============================================================

    @classmethod
    def find_missing_skills(
        cls,
        resume_text: str,
        job_description: str,
    ) -> list[str]:
        return cls.get_skill_match(
            resume_text,
            job_description,
        )["missing_skills"]

    # ============================================================
    # MATCHED SKILLS
    # ============================================================

    @classmethod
    def find_matched_skills(
        cls,
        resume_text: str,
        job_description: str,
    ) -> list[str]:

        return cls.get_skill_match(
            resume_text,
            job_description,
        )["matched_skills"]

    # ============================================================
    # SKILL MATCH SCORE
    # ============================================================

    @classmethod
    def calculate_skill_match(
        cls,
        resume_text: str,
        job_description: str,
    ) -> float:
        """
        ATS skill alignment score from 0-100.
        """

        return cls.get_skill_match(
            resume_text,
            job_description,
        )["coverage"]

    # ============================================================
    # PRIORITY ANALYSIS
    # ============================================================

    @classmethod
    def analyze_skill_gaps(
        cls,
        resume_text: str,
        job_description: str,
    ) -> list[dict[str, Any]]:
        """
        Rank missing skills by importance.

        Priority is based on:
        - Frequency in JD
        - Category
        - Whether it appears repeatedly
        """

        resume_skills = set(
            cls.extract_skills(resume_text)
        )

        job_frequencies = cls.skill_frequency(
            job_description
        )

        gaps = []

        for skill, frequency in job_frequencies.items():

            if skill in resume_skills:
                continue

            category = cls.get_skill_category(skill)

            if frequency >= 4:
                priority = "critical"
            elif frequency >= 2:
                priority = "high"
            else:
                priority = "medium"

            gaps.append({
                "skill": skill,
                "category": category,
                "frequency": frequency,
                "priority": priority,
                "impact_score": min(
                    100,
                    40 + frequency * 15,
                ),
            })

        priority_order = {
            "critical": 0,
            "high": 1,
            "medium": 2,
        }

        gaps.sort(
            key=lambda item: (
                priority_order[item["priority"]],
                -item["frequency"],
            )
        )

        return gaps

    # ============================================================
    # CATEGORY
    # ============================================================

    @classmethod
    def get_skill_category(
        cls,
        skill: str,
    ) -> str:

        for category, skills in cls.SKILL_CATEGORIES.items():

            if skill in skills:
                return category

        return "other"

    # ============================================================
    # SKILL EVIDENCE
    # ============================================================

    @classmethod
    def skill_evidence(
        cls,
        text: str,
        skill: str,
        context_window: int = 100,
    ) -> list[str]:
        """
        Find resume snippets surrounding a skill.

        This enables future UI such as:

            Python
            "Built FastAPI services using Python..."

        instead of simply saying:

            Python ✓
        """

        if not text or not skill:
            return []

        aliases = cls.SKILL_ALIASES.get(
            skill.lower(),
            [skill],
        )

        evidence: list[str] = []

        for alias in aliases:

            pattern = re.compile(
                rf"(?<!\w){re.escape(alias)}(?!\w)",
                flags=re.IGNORECASE,
            )

            for match in pattern.finditer(text):

                start = max(
                    0,
                    match.start() - context_window,
                )

                end = min(
                    len(text),
                    match.end() + context_window,
                )

                snippet = text[start:end].strip()

                if snippet and snippet not in evidence:
                    evidence.append(snippet)

                if len(evidence) >= 3:
                    return evidence

        return evidence

    # ============================================================
    # COMPLETE INTELLIGENCE
    # ============================================================

    @classmethod
    def analyze(
        cls,
        resume_text: str,
        job_description: str,
    ) -> dict[str, Any]:
        """
        Full ATS skill intelligence report.
        """

        match = cls.get_skill_match(
            resume_text,
            job_description,
        )

        resume_skills = match["resume_skills"]
        required_skills = match["required_skills"]

        skill_gaps = cls.analyze_skill_gaps(
            resume_text,
            job_description,
        )

        matched_details = []

        for skill in match["matched_skills"]:

            frequency = cls.skill_frequency(
                job_description
            ).get(skill, 1)

            matched_details.append({
                "skill": skill,
                "category": cls.get_skill_category(skill),
                "job_frequency": frequency,
                "evidence": cls.skill_evidence(
                    resume_text,
                    skill,
                ),
            })

        return {
            "score": match["coverage"],

            "resume_skills": resume_skills,

            "required_skills": required_skills,

            "matched_skills": match["matched_skills"],

            "missing_skills": match["missing_skills"],

            "additional_skills": match["additional_skills"],

            "matched_count": match["matched_count"],

            "required_count": match["required_count"],

            "missing_count": match["missing_count"],

            "coverage": match["coverage"],

            "resume_categories": cls.categorize_skills(
                resume_skills
            ),

            "required_categories": cls.categorize_skills(
                required_skills
            ),

            "skill_frequency": cls.skill_frequency(
                job_description
            ),

            "skill_gaps": skill_gaps,

            "matched_details": matched_details,
        }


# ================================================================
# BACKWARD-COMPATIBLE HELPER
# ================================================================

def extract_skills(text: str) -> list[str]:
    """
    Convenience function for future imports.
    """

    return SkillService.extract_skills(text)