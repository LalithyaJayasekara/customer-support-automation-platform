from collections import deque
from datetime import datetime, timedelta
from typing import Deque, Dict
import asyncio
import os

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from sqlalchemy.orm import Session
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration

from app.models.schemas import (
    AnalyticsOverview,
    AnalyticsRunRecord,
    AnalyticsTicketRecord,
    AnalyzeRequest,
    AnalyzeResponse,
    HistoryRunDetail,
    HistoryRunSummary,
    LoginRequest,
    TicketInput,
    TokenResponse,
    UserCreate,
    UserResponse,
)
from app.config import settings
from app.services.pipeline import build_metrics, run_ticket_pipeline
from app.services.storage_v2 import (
    delete_history_run,
    get_analytics_overview,
    get_history_run_detail,
    init_db,
    list_analytics_runs,
    list_analytics_tickets,
    list_history_runs,
    save_analysis_run,
)
from app.services.user_service import (
    authenticate_user,
    create_user,
    get_user_by_email,
    get_user_by_username,
)
from app.logging_config import logger
from app.dependencies import get_current_user
from app.database import get_db

# Initialize Sentry for error tracking (optional)
if os.getenv("SENTRY_DSN"):
    sentry_sdk.init(
        dsn=os.getenv("SENTRY_DSN"),
        integrations=[FastApiIntegration()],
        traces_sample_rate=1.0,
    )

app = FastAPI(
    title="Support Helper",
    version="2.0.0",
    description="Smart customer support message organizer and response assistant",
    docs_url="/docs",
    redoc_url="/redoc"
)

class SimpleRateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, max_requests: int, window_seconds: int):
        super().__init__(app)
        self.max_requests = max_requests
        self.window = timedelta(seconds=window_seconds)
        self.requests: Dict[str, Deque[datetime]] = {}
        self.lock = asyncio.Lock()

    async def dispatch(self, request: Request, call_next):
        identifier = self._get_client_ip(request)
        now = datetime.utcnow()

        async with self.lock:
            queue = self.requests.setdefault(identifier, deque())
            while queue and queue[0] <= now - self.window:
                queue.popleft()

            if len(queue) >= self.max_requests:
                retry_after = int((queue[0] + self.window - now).total_seconds()) or 1
                return JSONResponse(
                    status_code=429,
                    content={"detail": "Rate limit exceeded. Try again later."},
                    headers={
                        "Retry-After": str(retry_after),
                        "X-RateLimit-Limit": str(self.max_requests),
                        "X-RateLimit-Remaining": "0",
                    },
                )

            queue.append(now)

        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(self.max_requests)
        response.headers["X-RateLimit-Remaining"] = str(max(0, self.max_requests - len(queue)))
        if queue:
            response.headers["X-RateLimit-Reset"] = str(int((queue[0] + self.window - now).total_seconds()))
        return response

    def _get_client_ip(self, request: Request) -> str:
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            return forwarded.split(",")[0].strip()
        client = request.client
        return client.host if client else "unknown"

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if settings.rate_limit_enabled:
    app.add_middleware(
        SimpleRateLimitMiddleware,
        max_requests=settings.rate_limit_requests,
        window_seconds=settings.rate_limit_window_seconds,
    )

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error("Unhandled exception", exc_info=exc)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )

@app.on_event("startup")
def startup_event() -> None:
    """Initialize application on startup"""
    logger.info("Support Helper is starting up...")
    init_db()
    logger.info("Ready to help! ✓")


@app.post("/auth/register", response_model=UserResponse)
def register_user(user: UserCreate, db: Session = Depends(get_db)):
    """Create a new account"""
    try:
        logger.info("Starting user registration", username=user.username, email=user.email)
        
        # Check if user already exists
        db_user = get_user_by_username(db, user.username)
        if db_user:
            logger.warning("Username already taken", username=user.username)
            raise HTTPException(status_code=400, detail="This username is already taken")

        db_user = get_user_by_email(db, user.email)
        if db_user:
            logger.warning("Email already registered", email=user.email)
            raise HTTPException(status_code=400, detail="This email is already registered")

        # Create new user
        logger.info("Creating new user", username=user.username)
        new_user = create_user(db, user)
        db.commit()  # Manually commit the transaction
        logger.info("User created successfully", user_id=new_user.id)
        return new_user

    except HTTPException:
        db.rollback()  # Rollback on HTTP exceptions
        raise
    except Exception as e:
        db.rollback()  # Rollback on other exceptions
        logger.error("User registration failed", error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="Account creation failed")


@app.post("/auth/login", response_model=TokenResponse)
def login_user(login_data: LoginRequest, db: Session = Depends(get_db)):
    """Sign in to your account"""
    try:
        user = authenticate_user(db, login_data.username, login_data.password)
        if not user:
            raise HTTPException(
                status_code=401,
                detail="Username or password is incorrect",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Create access token
        from app.auth import create_access_token
        access_token = create_access_token(data={"sub": user.username})

        # Return token and user info
        user_response = UserResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            is_active=user.is_active,
            created_at=user.created_at.isoformat() if user.created_at else None
        )
        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            user=user_response
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("User login failed", error=str(e))
        raise HTTPException(status_code=500, detail="Login failed")


@app.get("/auth/me", response_model=UserResponse)
def get_current_user_info(current_user: str = Depends(get_current_user), db: Session = Depends(get_db)):
    """Get your account info"""
    try:
        user = get_user_by_username(db, current_user)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        return UserResponse.model_validate(user)

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get user info", error=str(e), user=current_user)
        raise HTTPException(status_code=500, detail="Failed to get user info")


@app.get("/health")
def health_check():
    """Check if service is running"""
    return {"status": "healthy", "version": "2.0.0"}


@app.get("/system-mode")
def system_mode():
    """Get system configuration mode"""
    ai_ready = bool(settings.use_llm and settings.openai_api_key)
    return {
        "mode": "ai" if ai_ready else "rule-based",
        "ai_ready": ai_ready,
        "use_agents_sdk": settings.use_agents_sdk,
        "database_type": "postgresql" if "postgresql" in settings.database_url else "sqlite"
    }


@app.post("/analyze", response_model=AnalyzeResponse)
def analyze_tickets(request: AnalyzeRequest, current_user: str = Depends(get_current_user)):
    """Analyze and organize customer messages"""
    try:
        logger.info("Starting message analysis", user=current_user, ticket_count=len(request.tickets))

        # Run the analysis pipeline for each ticket
        results = []
        for ticket in request.tickets:
            result = run_ticket_pipeline(ticket)
            results.append(result)
        
        metrics = build_metrics(results)

        # Save to database
        run_id = save_analysis_run(request.tickets, results, metrics)

        logger.info("Analysis complete", run_id=run_id, user=current_user)

        return AnalyzeResponse(
            run_id=run_id,
            results=results,
            metrics=metrics
        )

    except Exception as e:
        logger.error("Analysis failed", error=str(e), user=current_user)
        raise HTTPException(status_code=500, detail="Analysis failed")


@app.get("/history", response_model=list[HistoryRunSummary])
def get_history(limit: int = 20, current_user: str = Depends(get_current_user)):
    """Get analysis history"""
    try:
        runs = list_history_runs(limit)
        logger.info("History retrieved", user=current_user, count=len(runs))
        return runs
    except Exception as e:
        logger.error("Failed to retrieve history", error=str(e), user=current_user)
        raise HTTPException(status_code=500, detail="Failed to retrieve history")


@app.get("/history/{run_id}", response_model=HistoryRunDetail)
def get_history_detail(run_id: int, current_user: str = Depends(get_current_user)):
    """Get detailed analysis run data"""
    try:
        run_detail = get_history_run_detail(run_id)
        if not run_detail:
            raise HTTPException(status_code=404, detail="Run not found")

        logger.info("Run detail retrieved", run_id=run_id, user=current_user)
        return run_detail

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to retrieve run detail", run_id=run_id, error=str(e), user=current_user)
        raise HTTPException(status_code=500, detail="Failed to retrieve run detail")


@app.delete("/history/{run_id}")
def delete_history(run_id: int, current_user: str = Depends(get_current_user)):
    """Delete analysis run"""
    try:
        success = delete_history_run(run_id)
        if not success:
            raise HTTPException(status_code=404, detail="Run not found")

        logger.info("Run deleted", run_id=run_id, user=current_user)
        return {"message": "Run deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to delete run", run_id=run_id, error=str(e), user=current_user)
        raise HTTPException(status_code=500, detail="Failed to delete run")


@app.get("/analytics/overview", response_model=AnalyticsOverview)
def get_analytics(current_user: str = Depends(get_current_user)):
    """Get analytics overview"""
    try:
        overview = get_analytics_overview()
        logger.info("Analytics overview retrieved", user=current_user)
        return AnalyticsOverview(**overview)
    except Exception as e:
        logger.error("Failed to retrieve analytics", error=str(e), user=current_user)
        raise HTTPException(status_code=500, detail="Failed to retrieve analytics")


@app.get("/analytics/runs")
def get_analytics_runs(limit: int = 100, current_user: str = Depends(get_current_user)):
    """Get analytics runs data"""
    try:
        runs = list_analytics_runs(limit)
        logger.info("Analytics runs retrieved", user=current_user, count=len(runs))
        return runs
    except Exception as e:
        logger.error("Failed to retrieve analytics runs", error=str(e), user=current_user)
        raise HTTPException(status_code=500, detail="Failed to retrieve analytics runs")


@app.get("/analytics/tickets")
def get_analytics_tickets(limit: int = 1000, current_user: str = Depends(get_current_user)):
    """Get analytics tickets data"""
    try:
        tickets = list_analytics_tickets(limit)
        logger.info("Analytics tickets retrieved", user=current_user, count=len(tickets))
        return tickets
    except Exception as e:
        logger.error("Failed to retrieve analytics tickets", error=str(e), user=current_user)
        raise HTTPException(status_code=500, detail="Failed to retrieve analytics tickets")
