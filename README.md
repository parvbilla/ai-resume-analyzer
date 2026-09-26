# ResumeAI — AI-Powered Resume Intelligence Platform

> Upload your resume. Paste a job description. Get a deep ATS intelligence report with scores, skill gaps, keyword analysis, and a prioritized action plan — all running locally with no external AI APIs.

---

## What It Does

ResumeAI analyzes your PDF resume against a target job description using a **multi-signal ATS scoring engine** built entirely in Python. It tells you exactly why your resume scores the way it does and what to fix first.

**7 scoring signals, one weighted score:**

| Signal | Weight | What It Measures |
|---|---|---|
| Skill Alignment | 35% | How many required skills are in your resume |
| Keyword Coverage | 20% | Job-specific terminology match |
| Semantic Relevance | 20% | TF-IDF cosine similarity between resume and JD |
| Resume Structure | 10% | Presence of key sections (Summary, Experience, etc.) |
| Achievement Evidence | 10% | Quantified results, action verbs, metrics |
| Contact / Profile | 5% | Email, phone, LinkedIn, GitHub detection |

---

## Tech Stack

| Layer | Technology |
|---|---|
| **Backend** | Python 3.11+, FastAPI, SQLAlchemy, Pydantic v2 |
| **PDF Processing** | PyMuPDF (pymupdf) |
| **NLP / Scoring** | scikit-learn (TF-IDF + cosine similarity) |
| **Database** | SQLite (file-based, zero config) |
| **Frontend** | Vanilla HTML + CSS + JavaScript (no framework) |
| **Templates** | Jinja2 (served by FastAPI) |

No OpenAI. No external AI APIs. Everything runs locally.

---

## Project Structure

```
ai-resume-analyzer-new/
│
├── app/
│   ├── main.py                  # FastAPI app, middleware, lifecycle, health endpoints
│   ├── models.py                # SQLAlchemy ORM model (ResumeAnalysis table)
│   ├── schemas.py               # Pydantic request/response schemas
│   ├── database.py              # SQLite engine, session, schema migrations
│   │
│   ├── routes/
│   │   ├── resume.py            # POST /analyze, GET /history, GET /{id}
│   │   └── analysis.py          # Dashboard stats, trend, skill gaps, compare, delete
│   │
│   ├── services/
│   │   ├── ats_service.py       # Core ATS scoring engine (all 6 signals)
│   │   ├── pdf_service.py       # PDF text extraction and quality analysis
│   │   ├── skill_service.py     # Skill taxonomy, gap analysis, categorization
│   │   └── suggestion_service.py # Prioritized recommendation engine
│   │
│   ├── templates/
│   │   └── index.html           # Single-page dashboard UI
│   │
│   └── static/
│       ├── css/style.css        # UI styles
│       └── js/app.js            # All frontend logic (vanilla JS)
│
├── uploads/                     # Temporary PDF storage (auto-deleted after analysis)
├── resume_analyzer.db           # SQLite database (auto-created on first run)
├── .env                         # Environment config
├── requirements.txt             # Python dependencies
└── README.md
```

---

## API Endpoints

### Resume Analysis

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/resume/analyze` | Upload PDF + job description → full ATS report |
| `GET` | `/api/resume/history` | Latest analyses (limit param) |
| `GET` | `/api/resume/{id}` | Retrieve one complete analysis |

### Dashboard & Analytics

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/analysis/` | Paginated history with role/score filters |
| `GET` | `/api/analysis/{id}` | Full analysis report |
| `DELETE` | `/api/analysis/{id}` | Delete a saved analysis |
| `GET` | `/api/analysis/dashboard/stats` | Total analyses, avg/min/max scores |
| `GET` | `/api/analysis/dashboard/trend` | Score trend over N days |
| `GET` | `/api/analysis/dashboard/skill-gaps` | Most common skill gaps across all analyses |
| `GET` | `/api/analysis/compare/{id1}/{id2}` | Side-by-side comparison of two analyses |

### System

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/` | Dashboard UI |
| `GET` | `/health` | App health + uptime |
| `GET` | `/ready` | Database connectivity check |
| `GET` | `/api` | API metadata and endpoint list |
| `GET` | `/docs` | Swagger UI |
| `GET` | `/redoc` | ReDoc documentation |

---

## Installation & Setup

### 1. Clone the repository

```bash
git clone https://github.com/your-username/ai-resume-analyzer-new.git
cd ai-resume-analyzer-new
```

### 2. Create a virtual environment

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install fastapi uvicorn sqlalchemy pydantic pymupdf scikit-learn python-multipart jinja2 python-dotenv
```

Or if `requirements.txt` is populated:

```bash
pip install -r requirements.txt
```

### 4. Run the server

```bash
uvicorn app.main:app --reload
```

Open your browser at **http://localhost:8000**

---

## Environment Variables

Create a `.env` file in the project root. All variables are optional — defaults work out of the box.

```env
# Database
DATABASE_FILE=resume_analyzer.db
DATABASE_URL=sqlite:///./resume_analyzer.db

# File upload limits
MAX_RESUME_SIZE=10485760        # 10 MB in bytes
MIN_RESUME_TEXT_LENGTH=80
MIN_JOB_DESCRIPTION_LENGTH=80
MAX_JOB_DESCRIPTION_LENGTH=50000

# Debug
SQL_ECHO=false
```

---

## How the Analysis Works

### Step-by-step flow

```
User uploads PDF + Job Description
        │
        ▼
1. PDF Validation       → magic byte check, size limit, extension check
        │
        ▼
2. Text Extraction      → PyMuPDF extracts clean text, removes headers/footers
        │
        ▼
3. Skill Detection      → SkillService matches 100+ canonical skills with aliases
        │
        ▼
4. ATS Analysis         → ATSService runs all 6 scoring signals
        │
        ├── Skill Alignment     (TF-IDF + taxonomy matching)
        ├── Keyword Coverage    (frequency-ranked JD keywords)
        ├── Semantic Similarity (TF-IDF cosine similarity, bigrams)
        ├── Section Health      (regex section detection)
        ├── Achievement Score   (action verbs + quantified metrics)
        └── Contact Score       (email, phone, LinkedIn, GitHub regex)
        │
        ▼
5. Weighted Score       → overall_score = Σ(signal × weight)
        │
        ▼
6. Recommendations      → SuggestionService generates prioritized action plan
        │
        ▼
7. Database Save        → SQLite stores full analysis result
        │
        ▼
8. Response             → JSON with scores, skills, keywords, insights, recommendations
        │
        ▼
9. Cleanup              → Temporary PDF deleted from disk
```

### Skill Taxonomy

The `SkillService` recognizes **100+ canonical skills** across 11 categories with alias support:

- **Programming** — Python, Java, JavaScript, TypeScript, Go, Rust, C++, C#, and more
- **Frontend** — React, Next.js, Vue.js, Angular, Tailwind CSS, Redux, and more
- **Backend** — FastAPI, Django, Flask, Node.js, Express, Spring Boot, and more
- **Databases** — PostgreSQL, MySQL, MongoDB, Redis, SQLite, Firebase, and more
- **Cloud / DevOps** — AWS, Azure, GCP, Docker, Kubernetes, CI/CD, Terraform, and more
- **AI / Data** — scikit-learn, TensorFlow, PyTorch, Pandas, NumPy, OpenCV, and more
- **Security** — JWT, OAuth2, Authentication, RBAC, Cybersecurity
- **Testing** — Jest, Cypress, Playwright, Pytest, Unit/Integration Testing
- **CS Fundamentals** — OOP, DSA, System Design, Microservices, REST API
- **Version Control** — Git, GitHub, GitLab, Bitbucket
- **Tools** — Figma, Jira, Postman, Agile, Scrum

Aliases handle common variations: `react.js` → `react`, `nodejs` → `node.js`, `sklearn` → `scikit-learn`, `c sharp` → `c#`, etc.

---

## Score Classification

| Score Range | Label | Meaning |
|---|---|---|
| 90 – 100 | Exceptional | Highly competitive, strong ATS pass |
| 80 – 89 | Excellent | Strong match, minor optimizations possible |
| 70 – 79 | Strong | Good alignment, targeted improvements recommended |
| 60 – 69 | Good | Solid foundation, needs keyword and skill work |
| 50 – 59 | Needs Improvement | Partial alignment, significant tailoring needed |
| 35 – 49 | Weak | Low alignment, major rework required |
| 0 – 34 | Critical | Resume needs to be retargeted for this role |

---

## Database Schema

Single table: `resume_analyses`

| Column | Type | Description |
|---|---|---|
| `id` | INTEGER PK | Auto-increment primary key |
| `filename` | VARCHAR(255) | Original PDF filename |
| `resume_text` | TEXT | Extracted resume text |
| `job_description` | TEXT | Target job description |
| `role_title` | VARCHAR(255) | Target role name |
| `match_percentage` | FLOAT | Raw match score |
| `overall_score` | FLOAT | Weighted ATS score (0–100) |
| `skills_score` | FLOAT | Skill alignment sub-score |
| `keyword_score` | FLOAT | Keyword coverage sub-score |
| `semantic_score` | FLOAT | Semantic similarity sub-score |
| `section_score` | FLOAT | Resume structure sub-score |
| `achievement_score` | FLOAT | Achievement evidence sub-score |
| `contact_score` | FLOAT | Contact/profile sub-score |
| `content_score` | FLOAT | Overall content quality sub-score |
| `detected_skills` | TEXT (JSON) | Skills found in resume |
| `missing_skills` | TEXT (JSON) | Skills in JD but not in resume |
| `detected_keywords` | TEXT (JSON) | Keywords matched |
| `missing_keywords` | TEXT (JSON) | Keywords not found |
| `sections` | TEXT (JSON) | Section detection results |
| `strengths` | TEXT (JSON) | Generated strength statements |
| `weaknesses` | TEXT (JSON) | Generated weakness statements |
| `insights` | TEXT (JSON) | AI career insights |
| `suggestions` | TEXT (JSON) | Prioritized recommendations |
| `created_at` | DATETIME | UTC timestamp |

Indexes on `created_at`, `role_title`, and `overall_score` for fast queries.

---

## Frontend Features

The single-page UI (`index.html` + `app.js`) includes:

- **Drag-and-drop PDF upload** with magic-byte validation
- **Animated ATS score ring** with smooth counter animation
- **Score breakdown bars** — 6 weighted signals visualized
- **Skill tags** — detected (green) and missing (yellow)
- **Keyword intelligence** — found vs. missing columns
- **Resume health grid** — section, content, contact checks
- **Strengths & weaknesses** panels
- **AI career insights** list
- **Prioritized action plan** with critical/high/medium/low badges
- **Analysis history** — stored in `localStorage`, shown on dashboard
- **Dark / light mode** toggle with persistence
- **Keyboard shortcut** — `Ctrl+Enter` to trigger analysis
- **Toast notifications** for all user actions
- **Responsive layout** — works on mobile, tablet, desktop

---

## Security

- PDF files are validated by **magic bytes** (`%PDF-`), not just extension
- Uploaded files are saved with **UUID filenames** — original name is metadata only
- Temporary PDFs are **deleted from disk** after every analysis (success or failure)
- Security headers on every response: `X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy`, `Permissions-Policy`
- Every request gets a **unique `X-Request-ID`** for tracing
- Raw resume text and job descriptions are **never returned** in API responses by default
- File size hard-capped at **10 MB**
- Job description length validated: **80 – 50,000 characters**

---

## Analysis Response Structure

```json
{
  "success": true,
  "id": 42,
  "filename": "resume.pdf",
  "role_title": "Full Stack Developer",
  "overall_score": 74.5,
  "match_percentage": 74.5,
  "score_label": "Strong",
  "score_breakdown": {
    "skills_score": 68.0,
    "keyword_score": 72.0,
    "semantic_score": 81.3,
    "section_score": 80.0,
    "achievement_score": 60.0,
    "contact_score": 75.0
  },
  "detected_skills": ["python", "react", "fastapi", "postgresql", "docker"],
  "missing_skills": ["kubernetes", "aws", "typescript"],
  "keyword_analysis": {
    "detected": ["python", "api", "backend", "sql"],
    "missing": ["microservices", "cloud", "ci/cd"],
    "coverage_percentage": 72.0,
    "total_relevant_keywords": 40
  },
  "strengths": ["Strong alignment with backend skills", "Uses strong action verbs"],
  "weaknesses": ["Missing cloud/DevOps skills", "No quantified achievements detected"],
  "insights": ["Your resume has a strong foundation but still has optimization opportunities."],
  "recommendations": [
    {
      "priority": "high",
      "category": "skills",
      "title": "Improve high-impact skill coverage",
      "description": "Important skills missing: kubernetes, aws, typescript.",
      "action": "Add truthful evidence from projects or work experience.",
      "impact": 80
    }
  ],
  "improvement_potential": {
    "current_score": 74.5,
    "improvement_room": 25.5,
    "level": "moderate"
  },
  "meta": {
    "analysis_version": "4.0.0",
    "engine": "ResumeAI Multi-Signal ATS Intelligence Engine",
    "processing_time_seconds": 0.312
  }
}
```

---

## Known Limitations

- **Scanned / image PDFs are not supported** — the PDF must contain selectable text
- **No OCR** — image-only resumes will fail with a clear error message
- **SQLite only** — not recommended for multi-user production deployments (use PostgreSQL + Alembic for that)
- **No authentication** — the app has no login system; all analyses are shared in the same database
- **`requirements.txt` is empty** — dependencies must be installed manually (see Installation)
- **Skill taxonomy is fixed** — custom or niche skills not in the taxonomy won't be detected

---

## Roadmap / Possible Improvements

- [ ] Fill in `requirements.txt` with pinned versions
- [ ] Add Alembic for proper database migrations
- [ ] Add PostgreSQL support for production
- [ ] Add user authentication (JWT-based)
- [ ] Add OCR support for scanned PDFs (Tesseract)
- [ ] Export analysis as PDF report
- [ ] Resume version comparison UI
- [ ] Docker + docker-compose setup
- [ ] Deploy to AWS / Railway / Render

---

## License

MIT License — free to use, modify, and distribute.

---

> Built with Python · FastAPI · SQLAlchemy · scikit-learn · PyMuPDF · Vanilla JS
