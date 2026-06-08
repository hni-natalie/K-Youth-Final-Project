from fastapi import FastAPI, Request
from starlette.exceptions import HTTPException as StarletteHTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from backend.api.routes import search_routes, stats_by_role_routes, stats_routes, analyze_routes, updates_routes
from backend.core.config import settings
from backend.utils.error_handlers import DatabaseError, InternalServerError, UnprocessableEntityError


app = FastAPI(title="Job Market API", version="1.0")

# =========================
# CORS middleware
# =========================
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(search_routes.router, prefix="/api/search", tags=["Search"])
app.include_router(stats_routes.router, prefix="/api/stats", tags=["Stats"])
app.include_router(analyze_routes.router, prefix="/analyze", tags=["Analyze"])
app.include_router(stats_by_role_routes.router, prefix="/api/stats_by_role", tags=["Role"])
app.include_router(updates_routes.router, prefix="/api/updates", tags=["Updates"])

# GLOBAL ERROR HANDLERS
@app.exception_handler(InternalServerError)
async def internal_error_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "message": exc.detail,
            "data": None
        }
    )

@app.exception_handler(UnprocessableEntityError)
async def request_error_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "message": exc.detail,
            "data": None
        }
    )

@app.exception_handler(DatabaseError)
async def db_error_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "message": exc.detail,
            "data": None
        }
    )

@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    if exc.status_code == 404:
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "status": "error",
                "message": f"Endpoint {request.url.path} not found",
                "data": None,
            },
        )

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "message": exc.detail,
            "data": None,
        },
    )

@app.get("/api/health")
def health_check():
    return {
        "message": "API is running",
        "data": {"db_path": settings.DB_PATH}
    }
