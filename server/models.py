"""Database models for VibeReps server."""

from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship

Base = declarative_base()


class User(Base):
    """User account."""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    api_key = Column(String(64), unique=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Goals
    daily_rep_goal = Column(Integer, default=50)
    daily_session_goal = Column(Integer, default=3)

    exercises = relationship("Exercise", back_populates="user")

    @property
    def total_reps(self):
        return sum(e.reps for e in self.exercises)


class Exercise(Base):
    """Individual exercise session."""

    __tablename__ = "exercises"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    exercise_type = Column(String(50), nullable=False)  # squats, pushups, jumping_jacks
    reps = Column(Integer, nullable=False)
    duration = Column(Integer, default=0)  # seconds
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="exercises")


class DailySummaryRecord(Base):
    """Daily code metrics summary."""

    __tablename__ = "daily_summaries"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    date = Column(String(10), nullable=False)  # YYYY-MM-DD

    lines_accepted = Column(Integer, default=0)
    pull_requests = Column(Integer, default=0)
    commits = Column(Integer, default=0)
    tokens_used = Column(Integer, default=0)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User")


def init_db(database_url: str = "sqlite:///./vibereps.db"):
    """Initialize database and return session factory."""
    engine = create_engine(database_url, connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return SessionLocal
