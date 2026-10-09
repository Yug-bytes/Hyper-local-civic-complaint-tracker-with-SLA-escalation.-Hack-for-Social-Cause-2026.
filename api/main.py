"""Main FastAPI application for Civic Complaint Tracker.

Includes CORS middleware, standard JSON error response envelopes,
and modular routers for complaints, metrics, and administration.
"""

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from api.routes import admin, complaints, metrics
from api.schemas import ErrorDetail, ErrorEnvelope
from config import get_settings
from errors import (
    AuthError,
    ConfigurationError,
    NotFoundError,
    RateLimitError,
    StorageError,
    ValidationError,
)

settings = get_settings()

app = FastAPI(
    title="Civic Complaint Tracker API",
    version="1.0.0",
    description="Hyper-Local Civic Complaint Tracker with SLA Escalation API",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

# ──────────────────────────────────────────────────────────────
# CORS Configuration
# ──────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ──────────────────────────────────────────────────────────────
# Standard Exception Handlers
# ──────────────────────────────────────────────────────────────


@app.exception_handler(ValidationError)
def validation_error_handler(request: Request, exc: ValidationError) -> JSONResponse:
    envelope = ErrorEnvelope(
        error=ErrorDetail(code="VALIDATION_ERROR", message=str(exc))
    )
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST, content=envelope.model_dump()
    )


@app.exception_handler(NotFoundError)
def not_found_error_handler(request: Request, exc: NotFoundError) -> JSONResponse:
    envelope = ErrorEnvelope(error=ErrorDetail(code="NOT_FOUND", message=str(exc)))
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND, content=envelope.model_dump()
    )


@app.exception_handler(RateLimitError)
def rate_limit_error_handler(request: Request, exc: RateLimitError) -> JSONResponse:
    envelope = ErrorEnvelope(error=ErrorDetail(code="RATE_LIMITED", message=str(exc)))
    return JSONResponse(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS, content=envelope.model_dump()
    )


@app.exception_handler(AuthError)
def auth_error_handler(request: Request, exc: AuthError) -> JSONResponse:
    envelope = ErrorEnvelope(error=ErrorDetail(code="UNAUTHORIZED", message=str(exc)))
    return JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED, content=envelope.model_dump()
    )


@app.exception_handler(StorageError)
def storage_error_handler(request: Request, exc: StorageError) -> JSONResponse:
    envelope = ErrorEnvelope(error=ErrorDetail(code="STORAGE_ERROR", message=str(exc)))
    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE, content=envelope.model_dump()
    )


@app.exception_handler(ConfigurationError)
def configuration_error_handler(
    request: Request, exc: ConfigurationError
) -> JSONResponse:
    envelope = ErrorEnvelope(
        error=ErrorDetail(code="CONFIGURATION_ERROR", message=str(exc))
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=envelope.model_dump(),
    )


@app.exception_handler(RequestValidationError)
def request_validation_error_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    # Build readable error message from Pydantic errors
    first_error = exc.errors()[0] if exc.errors() else {}
    msg = first_error.get("msg", "Invalid request parameters.")
    loc = " -> ".join(str(part) for part in first_error.get("loc", []))
    message = f"{loc}: {msg}" if loc else msg

    envelope = ErrorEnvelope(
        error=ErrorDetail(code="VALIDATION_ERROR", message=message)
    )
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=envelope.model_dump(),
    )


@app.exception_handler(HTTPException)
def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    code = "HTTP_ERROR"
    if exc.status_code == 404:
        code = "NOT_FOUND"
    elif exc.status_code == 401:
        code = "UNAUTHORIZED"
    elif exc.status_code == 403:
        code = "FORBIDDEN"
    elif exc.status_code == 400:
        code = "BAD_REQUEST"

    envelope = ErrorEnvelope(error=ErrorDetail(code=code, message=str(exc.detail)))
    return JSONResponse(status_code=exc.status_code, content=envelope.model_dump())


# ──────────────────────────────────────────────────────────────
# Health & Status
# ──────────────────────────────────────────────────────────────


@app.get("/api/health", tags=["health"])
def health_check() -> dict[str, str]:
    """Health check endpoint for container and deployment monitors."""
    return {"status": "ok", "env": settings.env}


# ──────────────────────────────────────────────────────────────
# Routers
# ──────────────────────────────────────────────────────────────
app.include_router(complaints.router)
app.include_router(metrics.router)
app.include_router(admin.router)


# ──────────────────────────────────────────────────────────────
# Static Frontend Serving (Single Deployment / Production)
# ──────────────────────────────────────────────────────────────
from pathlib import Path
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

FRONTEND_DIST = Path(__file__).resolve().parent.parent / "frontend" / "dist"

if FRONTEND_DIST.is_dir():
    # Mount static assets for bundled JS, CSS, and media
    assets_dir = FRONTEND_DIST / "assets"
    if assets_dir.is_dir():
        app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="frontend-assets")

    @app.get("/{full_path:path}", include_in_schema=False)
    async def serve_spa(full_path: str):
        # Prevent intercepting /api or /docs
        if full_path.startswith("api/") or full_path == "api" or full_path == "docs":
            raise HTTPException(status_code=404, detail="Not Found")

        file_candidate = FRONTEND_DIST / full_path
        if file_candidate.is_file():
            return FileResponse(file_candidate)
        return FileResponse(FRONTEND_DIST / "index.html")
else:
    @app.get("/", include_in_schema=False)
    def root_status() -> dict[str, str]:
        return {
            "status": "online",
            "service": "Civic Complaint Tracker API",
            "docs": "/docs",
            "api_docs": "/api/docs",
            "frontend": "http://localhost:5173",
        }
