from sqlalchemy import Column, Integer, String, JSON, Boolean
from sqlalchemy.sql import func
from backend.storage.database import Base

class CalendarProfile(Base):
    """Model representing a work calendar configuration.
    
    * ``working_days`` – JSON list of weekday numbers (0=Monday … 6=Sunday) that are considered work days.
    * ``holidays`` – JSON list of ISO date strings (YYYY-MM-DD) that are non‑working days.
    * ``timezone`` – IANA timezone name (e.g., "Asia/Kolkata").
    * ``advance_days`` – Number of days to look ahead for advanced/matching status calculations.
    * ``active`` – Flag to soft‑delete or deactivate a profile.
    """
    __tablename__ = "calendar_profiles"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, unique=True)
    working_days = Column(JSON, nullable=False, default="[0,1,2,3,4]")
    holidays = Column(JSON, nullable=False, default="[]")
    timezone = Column(String, nullable=False, default="UTC")
    advance_days = Column(Integer, nullable=False, default=0)
    active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
