from sqlalchemy import Column, Integer, String, DateTime, JSON, Boolean, ForeignKey
from sqlalchemy.sql import func
from backend.storage.database import Base

class CanonicalSRS(Base):
    __tablename__ = "canonical_srs"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True)
    audit_session_id = Column(Integer, ForeignKey('audit_sessions.id'), nullable=False)
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now())
    raw_json = Column(JSON, nullable=False)          # Raw parsed SRS JSON
    canonical_json = Column(JSON, nullable=False)    # Normalized canonical representation
    # Optional linking flag
    is_active = Column(Boolean, default=True)
