"""
VibeReps Remote Server

Provides:
- REST API for local exercise tracker hook to POST sessions
- MCP HTTP/SSE transport for Claude Code to query stats
"""

import os
import json
import secrets
from datetime import datetime, timedelta
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, HTTPException, Header, Depends, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import func

from models import init_db, User, Exercise, DailySummaryRecord


# Database setup
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./vibereps.db")
SessionLocal = init_db(DATABASE_URL)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_user_by_api_key(api_key: str, db: Session) -> Optional[User]:
    return db.query(User).filter(User.api_key == api_key).first()


def require_user(x_api_key: str = Header(...), db: Session = Depends(get_db)) -> User:
    user = get_user_by_api_key(x_api_key, db)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return user


# Pydantic models
class ExerciseLog(BaseModel):
    exercise: str
    reps: int
    duration: int = 0


class UserCreate(BaseModel):
    username: str


class UserResponse(BaseModel):
    id: int
    username: str
    api_key: str


class StatsResponse(BaseModel):
    total_reps: int
    total_sessions: int
    current_streak: int
    reps_today: int
    sessions_today: int
    favorite_exercise: Optional[str]


class DailySummary(BaseModel):
    """Daily summary combining code metrics and exercises."""
    date: Optional[str] = None  # YYYY-MM-DD, defaults to today
    lines_accepted: int = 0
    pull_requests: int = 0
    commits: int = 0
    tokens_used: int = 0


# FastAPI app
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    yield
    # Shutdown


app = FastAPI(
    title="VibeReps API",
    description="Exercise tracking for Claude Code users",
    lifespan=lifespan
)


# ============== REST API (for hook) ==============

@app.post("/api/users", response_model=UserResponse)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    """Create a new user and return API key."""
    existing = db.query(User).filter(User.username == user.username).first()
    if existing:
        raise HTTPException(status_code=400, detail="Username already exists")

    api_key = secrets.token_hex(32)
    db_user = User(username=user.username, api_key=api_key)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    return UserResponse(id=db_user.id, username=db_user.username, api_key=api_key)


@app.post("/api/log")
def log_exercise(
    exercise: ExerciseLog,
    user: User = Depends(require_user),
    db: Session = Depends(get_db)
):
    """Log an exercise session (called by local hook)."""
    db_exercise = Exercise(
        user_id=user.id,
        exercise_type=exercise.exercise,
        reps=exercise.reps,
        duration=exercise.duration
    )
    db.add(db_exercise)
    db.commit()

    return {"status": "logged", "reps": exercise.reps, "exercise": exercise.exercise}


@app.get("/api/stats", response_model=StatsResponse)
def get_stats(user: User = Depends(require_user), db: Session = Depends(get_db)):
    """Get user stats."""
    return calculate_stats(user, db)


@app.get("/api/leaderboard")
def get_leaderboard(db: Session = Depends(get_db)):
    """Get top users by total reps."""
    results = (
        db.query(
            User.username,
            func.sum(Exercise.reps).label("total_reps"),
            func.count(Exercise.id).label("sessions")
        )
        .join(Exercise)
        .group_by(User.id)
        .order_by(func.sum(Exercise.reps).desc())
        .limit(10)
        .all()
    )

    return [
        {"rank": i + 1, "username": r.username, "total_reps": r.total_reps, "sessions": r.sessions}
        for i, r in enumerate(results)
    ]


@app.post("/api/summary")
def log_daily_summary(
    summary: DailySummary,
    user: User = Depends(require_user),
    db: Session = Depends(get_db)
):
    """Log daily code metrics summary. Updates if exists for that date."""
    date = summary.date or datetime.utcnow().strftime("%Y-%m-%d")

    # Check if record exists for this date
    existing = (
        db.query(DailySummaryRecord)
        .filter(DailySummaryRecord.user_id == user.id)
        .filter(DailySummaryRecord.date == date)
        .first()
    )

    if existing:
        # Update existing record (accumulate)
        existing.lines_accepted += summary.lines_accepted
        existing.pull_requests += summary.pull_requests
        existing.commits += summary.commits
        existing.tokens_used += summary.tokens_used
    else:
        # Create new record
        existing = DailySummaryRecord(
            user_id=user.id,
            date=date,
            lines_accepted=summary.lines_accepted,
            pull_requests=summary.pull_requests,
            commits=summary.commits,
            tokens_used=summary.tokens_used
        )
        db.add(existing)

    db.commit()

    return {
        "status": "logged",
        "date": date,
        "lines_accepted": existing.lines_accepted,
        "pull_requests": existing.pull_requests,
        "commits": existing.commits,
        "tokens_used": existing.tokens_used
    }


@app.get("/api/summary/{date}")
def get_daily_summary(
    date: str,
    user: User = Depends(require_user),
    db: Session = Depends(get_db)
):
    """Get combined daily summary (code + exercises) for a specific date."""
    # Get code metrics
    code_summary = (
        db.query(DailySummaryRecord)
        .filter(DailySummaryRecord.user_id == user.id)
        .filter(DailySummaryRecord.date == date)
        .first()
    )

    # Get exercises for that date
    exercises = (
        db.query(Exercise)
        .filter(Exercise.user_id == user.id)
        .filter(func.date(Exercise.created_at) == date)
        .all()
    )

    # Aggregate exercises by type
    exercise_totals = {}
    for e in exercises:
        exercise_totals[e.exercise_type] = exercise_totals.get(e.exercise_type, 0) + e.reps

    return {
        "date": date,
        "code": {
            "lines_accepted": code_summary.lines_accepted if code_summary else 0,
            "pull_requests": code_summary.pull_requests if code_summary else 0,
            "commits": code_summary.commits if code_summary else 0,
            "tokens_used": code_summary.tokens_used if code_summary else 0
        },
        "exercises": exercise_totals,
        "total_reps": sum(exercise_totals.values())
    }


# ============== Helper functions ==============

def calculate_stats(user: User, db: Session) -> StatsResponse:
    """Calculate user statistics."""
    exercises = db.query(Exercise).filter(Exercise.user_id == user.id).all()

    today = datetime.utcnow().date()
    today_exercises = [e for e in exercises if e.created_at.date() == today]

    # Calculate streak
    streak = calculate_streak(exercises)

    # Find favorite exercise
    exercise_counts = {}
    for e in exercises:
        exercise_counts[e.exercise_type] = exercise_counts.get(e.exercise_type, 0) + e.reps
    favorite = max(exercise_counts, key=exercise_counts.get) if exercise_counts else None

    return StatsResponse(
        total_reps=sum(e.reps for e in exercises),
        total_sessions=len(exercises),
        current_streak=streak,
        reps_today=sum(e.reps for e in today_exercises),
        sessions_today=len(today_exercises),
        favorite_exercise=favorite
    )


def calculate_streak(exercises: list) -> int:
    """Calculate current streak (consecutive days with exercises)."""
    if not exercises:
        return 0

    dates = sorted(set(e.created_at.date() for e in exercises), reverse=True)
    today = datetime.utcnow().date()

    # Must have exercised today or yesterday to have an active streak
    if dates[0] < today - timedelta(days=1):
        return 0

    streak = 1
    for i in range(1, len(dates)):
        if dates[i - 1] - dates[i] == timedelta(days=1):
            streak += 1
        else:
            break

    return streak


# ============== MCP over HTTP/SSE ==============

MCP_TOOLS = [
    {
        "name": "log_exercise_session",
        "description": "Log an exercise session for the user",
        "inputSchema": {
            "type": "object",
            "properties": {
                "exercise": {
                    "type": "string",
                    "description": "Type of exercise (squats, pushups, jumping_jacks)"
                },
                "reps": {
                    "type": "integer",
                    "description": "Number of repetitions completed"
                },
                "duration": {
                    "type": "integer",
                    "description": "Duration in seconds",
                    "default": 0
                }
            },
            "required": ["exercise", "reps"]
        }
    },
    {
        "name": "get_stats",
        "description": "Get exercise statistics for the user",
        "inputSchema": {
            "type": "object",
            "properties": {}
        }
    },
    {
        "name": "get_leaderboard",
        "description": "Get the top 10 users by total reps",
        "inputSchema": {
            "type": "object",
            "properties": {}
        }
    },
    {
        "name": "check_streak",
        "description": "Check the user's current exercise streak",
        "inputSchema": {
            "type": "object",
            "properties": {}
        }
    },
    {
        "name": "get_progress_today",
        "description": "Get today's exercise progress toward daily goals",
        "inputSchema": {
            "type": "object",
            "properties": {}
        }
    },
    {
        "name": "log_daily_summary",
        "description": "Log daily code metrics (lines accepted, PRs, commits, tokens)",
        "inputSchema": {
            "type": "object",
            "properties": {
                "lines_accepted": {
                    "type": "integer",
                    "description": "Lines of code accepted today"
                },
                "pull_requests": {
                    "type": "integer",
                    "description": "Pull requests created today"
                },
                "commits": {
                    "type": "integer",
                    "description": "Commits made today"
                },
                "tokens_used": {
                    "type": "integer",
                    "description": "Tokens used today"
                },
                "date": {
                    "type": "string",
                    "description": "Date in YYYY-MM-DD format (defaults to today)"
                }
            }
        }
    },
    {
        "name": "get_daily_summary",
        "description": "Get combined daily summary of code metrics and exercises",
        "inputSchema": {
            "type": "object",
            "properties": {
                "date": {
                    "type": "string",
                    "description": "Date in YYYY-MM-DD format (defaults to today)"
                }
            }
        }
    }
]


def handle_mcp_tool_call(tool_name: str, arguments: dict, user: User, db: Session) -> dict:
    """Handle an MCP tool call and return the result."""

    if tool_name == "log_exercise_session":
        exercise = Exercise(
            user_id=user.id,
            exercise_type=arguments["exercise"],
            reps=arguments["reps"],
            duration=arguments.get("duration", 0)
        )
        db.add(exercise)
        db.commit()
        return {"status": "logged", "exercise": arguments["exercise"], "reps": arguments["reps"]}

    elif tool_name == "get_stats":
        stats = calculate_stats(user, db)
        return stats.model_dump()

    elif tool_name == "get_leaderboard":
        results = (
            db.query(
                User.username,
                func.sum(Exercise.reps).label("total_reps"),
                func.count(Exercise.id).label("sessions")
            )
            .join(Exercise)
            .group_by(User.id)
            .order_by(func.sum(Exercise.reps).desc())
            .limit(10)
            .all()
        )
        return {
            "leaderboard": [
                {"rank": i + 1, "username": r.username, "total_reps": r.total_reps, "sessions": r.sessions}
                for i, r in enumerate(results)
            ]
        }

    elif tool_name == "check_streak":
        exercises = db.query(Exercise).filter(Exercise.user_id == user.id).all()
        streak = calculate_streak(exercises)
        return {"current_streak": streak, "message": f"You're on a {streak} day streak!"}

    elif tool_name == "get_progress_today":
        today = datetime.utcnow().date()
        today_exercises = (
            db.query(Exercise)
            .filter(Exercise.user_id == user.id)
            .filter(func.date(Exercise.created_at) == today)
            .all()
        )
        reps_today = sum(e.reps for e in today_exercises)
        sessions_today = len(today_exercises)

        return {
            "reps_today": reps_today,
            "sessions_today": sessions_today,
            "rep_goal": user.daily_rep_goal,
            "session_goal": user.daily_session_goal,
            "rep_progress": f"{reps_today}/{user.daily_rep_goal}",
            "session_progress": f"{sessions_today}/{user.daily_session_goal}"
        }

    elif tool_name == "log_daily_summary":
        date = arguments.get("date") or datetime.utcnow().strftime("%Y-%m-%d")

        existing = (
            db.query(DailySummaryRecord)
            .filter(DailySummaryRecord.user_id == user.id)
            .filter(DailySummaryRecord.date == date)
            .first()
        )

        if existing:
            existing.lines_accepted += arguments.get("lines_accepted", 0)
            existing.pull_requests += arguments.get("pull_requests", 0)
            existing.commits += arguments.get("commits", 0)
            existing.tokens_used += arguments.get("tokens_used", 0)
        else:
            existing = DailySummaryRecord(
                user_id=user.id,
                date=date,
                lines_accepted=arguments.get("lines_accepted", 0),
                pull_requests=arguments.get("pull_requests", 0),
                commits=arguments.get("commits", 0),
                tokens_used=arguments.get("tokens_used", 0)
            )
            db.add(existing)

        db.commit()
        return {
            "status": "logged",
            "date": date,
            "lines_accepted": existing.lines_accepted,
            "pull_requests": existing.pull_requests,
            "commits": existing.commits,
            "tokens_used": existing.tokens_used
        }

    elif tool_name == "get_daily_summary":
        date = arguments.get("date") or datetime.utcnow().strftime("%Y-%m-%d")

        code_summary = (
            db.query(DailySummaryRecord)
            .filter(DailySummaryRecord.user_id == user.id)
            .filter(DailySummaryRecord.date == date)
            .first()
        )

        exercises = (
            db.query(Exercise)
            .filter(Exercise.user_id == user.id)
            .filter(func.date(Exercise.created_at) == date)
            .all()
        )

        exercise_totals = {}
        for e in exercises:
            exercise_totals[e.exercise_type] = exercise_totals.get(e.exercise_type, 0) + e.reps

        return {
            "date": date,
            "code": {
                "lines_accepted": code_summary.lines_accepted if code_summary else 0,
                "pull_requests": code_summary.pull_requests if code_summary else 0,
                "commits": code_summary.commits if code_summary else 0,
                "tokens_used": code_summary.tokens_used if code_summary else 0
            },
            "exercises": exercise_totals,
            "total_reps": sum(exercise_totals.values())
        }

    else:
        raise ValueError(f"Unknown tool: {tool_name}")


@app.post("/mcp")
async def mcp_endpoint(request: Request, db: Session = Depends(get_db)):
    """
    MCP HTTP endpoint for Claude Code.

    Handles JSON-RPC style MCP messages.
    Authentication via X-API-Key header.
    """
    api_key = request.headers.get("X-API-Key")
    body = await request.json()

    method = body.get("method")
    params = body.get("params", {})
    msg_id = body.get("id")

    def make_response(result):
        return {"jsonrpc": "2.0", "id": msg_id, "result": result}

    def make_error(code, message):
        return {"jsonrpc": "2.0", "id": msg_id, "error": {"code": code, "message": message}}

    # Handle initialization (no auth required)
    if method == "initialize":
        return make_response({
            "protocolVersion": "2024-11-05",
            "capabilities": {"tools": {}},
            "serverInfo": {"name": "vibereps", "version": "1.0.0"}
        })

    if method == "notifications/initialized":
        return make_response({})

    # List tools (no auth required)
    if method == "tools/list":
        return make_response({"tools": MCP_TOOLS})

    # Tool calls require auth
    if method == "tools/call":
        if not api_key:
            return make_error(-32001, "X-API-Key header required")

        user = get_user_by_api_key(api_key, db)
        if not user:
            return make_error(-32001, "Invalid API key")

        tool_name = params.get("name")
        arguments = params.get("arguments", {})

        try:
            result = handle_mcp_tool_call(tool_name, arguments, user, db)
            return make_response({
                "content": [{"type": "text", "text": json.dumps(result, indent=2)}]
            })
        except Exception as e:
            return make_error(-32000, str(e))

    return make_error(-32601, f"Method not found: {method}")


# Health check
@app.get("/health")
def health():
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
