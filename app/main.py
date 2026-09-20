from __future__ import annotations

import logging
import time
import uuid
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.exceptions import HTTPException as StarletteHTTPException

from .database import Base, engine
from .routes import resume


# ============================================================
# APPLICATION METADATA
# ============================================================

APP_NAME = "ResumeAI"
APP_DESCRIPTION = (
    "AI-powered resume intelligence platform for ATS analysis, "
    "skill intelligence, job matching and actionable career insights."
)
APP_VERSION = "3.0.0"


# ============================================================
# PATH CONFIGURATION
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

TEMPLATES_DIR = BASE_DIR / "templates"
STATIC_DIR = BASE_DIR / "static"
UPLOADS_DIR = BASE_DIR.parent / "uploads"

# Make sure required directories exist.
TEMPLATES_DIR.mkdir(parents=True, exist_ok=True)
STATIC_DIR.mkdir(parents=True, exist_ok=True)
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================
# LOGGING
# ============================================================

logging.basicConfig(
    level=logging.INFO,
    format=(
        "%(asctime)s | %(levelname)s | "
        "%(name)s | %(message)s"
    ),
)

logger = logging.getLogger(APP_NAME)


# ============================================================
# APPLICATION STATE
# ============================================================

START_TIME = time.time()


# ============================================================
# DATABASE INITIALIZATION
# ============================================================

def initialize_database() -> None:
    """
    Initialize database tables.

    For the current SQLite-based architecture this creates
    missing tables without destroying existing data.

    Future production deployments can replace this with
    Alembic migrations.
    """

    try:
        # Importing models before create_all ensures SQLAlchemy
        # has registered the application's model metadata.
        from . import models  # noqa: F401

        Base.metadata.create_all(bind=engine)

        logger.info("Database initialized successfully.")

    except Exception:
        logger.exception("Database initialization failed.")
        raise


# ============================================================
# APPLICATION LIFECYCLE
# ============================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application startup/shutdown lifecycle.

    Startup:
        - Initialize database
        - Prepare application directories
        - Log application startup

    Shutdown:
        - Log application shutdown
    """

    logger.info("=" * 70)
    logger.info("Starting %s v%s", APP_NAME, APP_VERSION)
    logger.info("=" * 70)

    initialize_database()

    logger.info("Templates directory: %s", TEMPLATES_DIR)
    logger.info("Static directory: %s", STATIC_DIR)
    logger.info("Uploads directory: %s", UPLOADS_DIR)
    logger.info("Application startup completed.")

    yield

    logger.info("Application shutdown completed.")
    logger.info("=" * 70)


# ============================================================
# FASTAPI APPLICATION
# ============================================================

app = FastAPI(
    title=APP_NAME,
    description=APP_DESCRIPTION,
    version=APP_VERSION,

    # Swagger
    docs_url="/docs",
    swagger_ui_parameters={
        "displayRequestDuration": True,
        "filter": True,
        "persistAuthorization": True,
        "tryItOutEnabled": True,
    },

    # ReDoc
    redoc_url="/redoc",

    # OpenAPI
    openapi_url="/openapi.json",

    # Lifecycle
    lifespan=lifespan,
)


# ============================================================
# STATIC FILES
# ============================================================

app.mount(
    "/static",
    StaticFiles(directory=str(STATIC_DIR)),
    name="static",
)


# ============================================================
# JINJA2 TEMPLATE ENGINE
# ============================================================

templates = Jinja2Templates(
    directory=str(TEMPLATES_DIR),
)


# ============================================================
# MIDDLEWARE
# ============================================================

@app.middleware("http")
async def request_middleware(
    request: Request,
    call_next,
):
    """
    Global HTTP middleware.

    Adds:
    - Request ID
    - Request timing
    - Security headers
    - Server timing information
    """

    request_id = str(uuid.uuid4())
    request.state.request_id = request_id

    start_time = time.perf_counter()

    try:
        response = await call_next(request)

    except Exception:
        logger.exception(
            "Unhandled request error | request_id=%s | path=%s",
            request_id,
            request.url.path,
        )
        raise

    process_time = time.perf_counter() - start_time

    # --------------------------------------------------------
    # Request tracing
    # --------------------------------------------------------

    response.headers["X-Request-ID"] = request_id

    response.headers["X-Process-Time"] = (
        f"{process_time:.4f}"
    )

    # --------------------------------------------------------
    # Security headers
    # --------------------------------------------------------

    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = (
        "strict-origin-when-cross-origin"
    )
    response.headers["Permissions-Policy"] = (
        "camera=(), microphone=(), geolocation=()"
    )

    # --------------------------------------------------------
    # Logging
    # --------------------------------------------------------

    logger.info(
        "%s %s -> %s | %.2fms | request_id=%s",
        request.method,
        request.url.path,
        response.status_code,
        process_time * 1000,
        request_id,
    )

    return response


# ============================================================
# GLOBAL EXCEPTION HANDLERS
# ============================================================

@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(
    request: Request,
    exc: StarletteHTTPException,
):
    """
    Consistent JSON response for HTTP errors.
    """

    request_id = getattr(
        request.state,
        "request_id",
        None,
    )

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": {
                "message": str(exc.detail),
                "status_code": exc.status_code,
            },
            "request_id": request_id,
        },
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
):
    """
    Clean validation error response.
    """

    request_id = getattr(
        request.state,
        "request_id",
        None,
    )

    return JSONResponse(
        status_code=422,
        content={
            "success": False,
            "error": {
                "message": "Request validation failed.",
                "details": exc.errors(),
            },
            "request_id": request_id,
        },
    )


@app.exception_handler(Exception)
async def global_exception_handler(
    request: Request,
    exc: Exception,
):
    """
    Last-resort exception handler.

    Prevents raw internal implementation details from being
    exposed to users.
    """

    request_id = getattr(
        request.state,
        "request_id",
        None,
    )

    logger.exception(
        "Unhandled application exception | request_id=%s",
        request_id,
    )

    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": {
                "message": (
                    "Something went wrong while processing "
                    "your request."
                ),
                "status_code": 500,
            },
            "request_id": request_id,
        },
    )


# ============================================================
# API ROUTERS
# ============================================================

app.include_router(
    resume.router,
    prefix="/api/resume",
    tags=["Resume Analysis"],
)


# ============================================================
# WEB APPLICATION
# ============================================================

@app.get(
    "/",
    include_in_schema=False,
)
async def home(request: Request):
    """
    ResumeAI landing/dashboard page.
    """

    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "title": "ResumeAI — Intelligent Resume Analyzer",
            "app_name": APP_NAME,
            "app_version": APP_VERSION,
        },
    )


# ============================================================
# HEALTH CHECK
# ============================================================

@app.get(
    "/health",
    tags=["System"],
    summary="Application health check",
)
async def health_check() -> dict[str, Any]:
    """
    Basic application health endpoint.
    """

    uptime = time.time() - START_TIME

    return {
        "success": True,
        "status": "healthy",
        "service": APP_NAME,
        "version": APP_VERSION,
        "uptime_seconds": round(uptime, 2),
    }


# ============================================================
# READINESS CHECK
# ============================================================

@app.get(
    "/ready",
    tags=["System"],
    summary="Application readiness check",
)
async def readiness_check() -> dict[str, Any]:
    """
    Indicates whether the application is ready to process
    requests.

    The database connection is tested here.
    """

    try:
        with engine.connect() as connection:
            connection.exec_driver_sql("SELECT 1")

        return {
            "success": True,
            "status": "ready",
            "database": "connected",
        }

    except Exception:
        logger.exception("Readiness check failed.")

        return JSONResponse(
            status_code=503,
            content={
                "success": False,
                "status": "not_ready",
                "database": "unavailable",
            },
        )


# ============================================================
# API INFORMATION
# ============================================================

@app.get(
    "/api",
    tags=["System"],
    summary="ResumeAI API information",
)
async def api_information() -> dict[str, Any]:
    """
    Public API metadata.
    """

    return {
        "success": True,
        "name": APP_NAME,
        "version": APP_VERSION,
        "description": APP_DESCRIPTION,
        "status": "online",
        "endpoints": {
            "documentation": "/docs",
            "redoc": "/redoc",
            "health": "/health",
            "readiness": "/ready",
            "resume_analysis": "/api/resume/analyze",
        },
    }