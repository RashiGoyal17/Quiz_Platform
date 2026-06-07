from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.admin_attempts import router as admin_attempts_router
from app.api.v1.analytics import router as analytics_router
from app.api.v1.attempts import router as attempts_router
from app.api.v1.auth import router as auth_router
from app.api.v1.health import router as health_router
from app.api.v1.question_banks import router as question_banks_router
from app.api.v1.questions import router as questions_router
from app.api.v1.quizzes import router as quizzes_router
from app.config import settings

app = FastAPI(
    title="Quiz Platform API",
    version="1.0.0",
    docs_url="/docs" if settings.is_development else None,
    redoc_url="/redoc" if settings.is_development else None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router, prefix="/api/v1", tags=["health"])
app.include_router(auth_router, prefix="/api/v1")
app.include_router(question_banks_router, prefix="/api/v1")
app.include_router(questions_router, prefix="/api/v1")
app.include_router(quizzes_router, prefix="/api/v1")
app.include_router(attempts_router, prefix="/api/v1")
app.include_router(admin_attempts_router, prefix="/api/v1")
app.include_router(analytics_router, prefix="/api/v1")


@app.get("/")
async def root():
    return {"message": "Quiz Platform API", "version": "1.0.0"}
