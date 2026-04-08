"""Main FastAPI application entry point"""
import logging
from fastapi import FastAPI
from fastapi import Response
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from sqladmin import Admin
from app.core.config import settings
from app.database.db import init_db, engine
from app.api.v1 import auth, users, lawyers, cases, consultations, messages, citizens, lawyers_professional, social_workers
from app.admin import all_views, authentication_backend

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title=settings.API_TITLE,
    version=settings.API_VERSION,
    description=settings.API_DESCRIPTION,
)

# Debug: Log CORS settings
import json
cors_origins = settings.CORS_ORIGINS
if isinstance(cors_origins, str):
    try:
        cors_origins = json.loads(cors_origins)
    except:
        cors_origins = [cors_origins]
print(f"✅ CORS Origins: {cors_origins}")

# SessionMiddleware must come before Admin (required for auth cookie)
app.add_middleware(SessionMiddleware, secret_key=settings.SECRET_KEY)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins if isinstance(cors_origins, list) else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Admin panel (Django-style) ──────────────────────────────────────────────
admin = Admin(
    app,
    engine,
    title="LegalAid India — Admin",
    authentication_backend=authentication_backend,
)

for view in all_views:
    admin.add_view(view)

# Initialize database on startup
@app.on_event("startup")
def startup_event():
    """Initialize database on startup"""
    try:
        init_db()
        logger.info("✅ Database initialized successfully")
    except Exception as e:
        logger.error(f"⚠️ Database initialization failed: {e}")
        logger.info("   Make sure PostgreSQL is running and credentials in .env are correct")

# Health check endpoint
@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {"status": "ok", "service": "LegalAid India API"}


@app.head("/health", include_in_schema=False)
def health_check_head():
    """Health check endpoint for HEAD probes"""
    return Response(status_code=200)

# Include API routers
app.include_router(auth.router, prefix="/api/v1", tags=["Authentication"])
app.include_router(users.router, prefix="/api/v1", tags=["Users"])
app.include_router(lawyers.router, prefix="/api/v1", tags=["Lawyers"])
app.include_router(lawyers_professional.router, prefix="/api/v1")
app.include_router(cases.router, prefix="/api/v1", tags=["Cases"])
app.include_router(consultations.router, prefix="/api/v1", tags=["Consultations"])
app.include_router(messages.router, prefix="/api/v1", tags=["Messages"])
app.include_router(citizens.router, prefix="/api/v1")
app.include_router(social_workers.router, prefix="/api/v1")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.SERVER_HOST,
        port=settings.SERVER_PORT,
        reload=settings.DEBUG,
    )
