from sqlalchemy import Column, Integer, String, Float, DateTime, Text, JSON, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from backend.storage.database import Base

# ===================================
# EXTENDED AUDIT MODELS
# ===================================

class SRSExtractionResult(Base):
    __tablename__ = "srs_extraction_results"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True)
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now())
    raw_file_path = Column(String, nullable=False)
    extracted_json = Column(JSON, nullable=False)  # structured SRS data

class IntegrationSyncState(Base):
    __tablename__ = "integration_sync_state"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True)
    platform = Column(String, nullable=False) # "github" or "jira"
    identifier = Column(String, nullable=False, unique=True) # owner/repo or project_key
    last_synced_at = Column(DateTime(timezone=True), nullable=True)
    last_successful_sync_at = Column(DateTime(timezone=True), nullable=True)
    sync_strategy = Column(String, default="DELTA")
    etag = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class PlatformFetchResult(Base):
    __tablename__ = "platform_fetch_results"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True)
    platform = Column(String, nullable=False)  # "github" or "jira"
    fetched_at = Column(DateTime(timezone=True), server_default=func.now())
    raw_data = Column(JSON, nullable=False)  # raw platform data
    actual_data_json = Column(JSON, nullable=True)  # canonical actual data
    platform_data_json = Column(JSON, nullable=True)  # Full PlatformData enriched payload
    organization_profile_json = Column(JSON, nullable=True)  # Discovered JUIL anchors

class AuditComparison(Base):
    __tablename__ = "audit_comparisons"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True)
    srs_result_id = Column(Integer, nullable=False)
    platform_result_id = Column(Integer, nullable=False)
    comparison_json = Column(JSON, nullable=False)  # merged SRS + platform data
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class VarianceResult(Base):
    __tablename__ = "variance_results"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True)
    audit_comparison_id = Column(Integer, nullable=False)
    variance_json = Column(JSON, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class PlatformConnection(Base):
    __tablename__ = "platform_connections"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True)
    platform = Column(String, nullable=False)  # "jira" or "github"
    credentials_json = Column(JSON, nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class RootCauseResult(Base):
    __tablename__ = "root_cause_results"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True)
    audit_comparison_id = Column(Integer, nullable=False)
    root_cause_json = Column(JSON, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    is_fault = Column(Boolean, default=True)

class CalendarProfile(Base):
    __tablename__ = "calendar_profiles"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False)
    workday_start = Column(String, default="09:00")  # HH:MM
    workday_end = Column(String, default="17:00")
    working_days = Column(JSON, default=[])  # List of weekday names
    hours_per_day = Column(Integer, default=8)
    holidays = Column(JSON, default=[])  # List of holiday dates
    timezone = Column(String, default="UTC")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class ModuleMatch(Base):
    __tablename__ = "module_matches"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True)
    audit_session_id = Column(Integer, ForeignKey('audit_sessions.id'), nullable=False)
    srs_node_id = Column(Integer, nullable=False)
    feature_id = Column(Integer, nullable=False)
    confidence_score = Column(Float, nullable=False)
    approval_status = Column(String, default='PENDING_REVIEW')
    approval_timestamp = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class AuditSession(Base):
    __tablename__ = "audit_sessions"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False)
    platform_type = Column(String, nullable=False)  # "github" or "jira"
    srs_result_id = Column(Integer, nullable=False)
    platform_fetch_result_id = Column(Integer, nullable=False)
    calendar_profile_id = Column(Integer, ForeignKey('calendar_profiles.id'), nullable=False)
    calendar_profile = relationship('CalendarProfile', backref='audit_sessions')
    srs_confirmed = Column(Boolean, default=False)
    platform_confirmed = Column(Boolean, default=False)
    calendar_confirmed = Column(Boolean, default=False)
    status = Column(String, default="IN_PROGRESS")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    # New progress tracking fields
    progress_percent = Column(Float, default=0.0)
    stage = Column(String, default="NOT_STARTED")
    # Approved workflow flags
    planned_data_approved = Column(Boolean, default=False)
    actual_data_approved = Column(Boolean, default=False)
    capacity_approved = Column(Boolean, default=False)
    normalized_data_approved = Column(Boolean, default=False)
    matches_approved = Column(Boolean, default=False)
    normalized_data_json = Column(JSON, nullable=True)
    coherence_result_json = Column(JSON, nullable=True)
    identity_resolution_json = Column(JSON, nullable=True)

class ChatSession(Base):
    __tablename__ = "chat_sessions"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True)
    audit_session_id = Column(Integer, nullable=False)
    session_data = Column(JSON, nullable=False)  # store messages & context
    last_interaction = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    is_active = Column(Boolean, default=True)

# -------------------------------------------------
# New models for persisting audit analysis results
# -------------------------------------------------
class AuditResult(Base):
    __tablename__ = "audit_results"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True)
    audit_session_id = Column(Integer, ForeignKey('audit_sessions.id'), nullable=False)
    variance_json = Column(JSON, nullable=True)
    primary_causes_json = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class FindingRecord(Base):
    __tablename__ = "finding_records"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True)
    audit_session_id = Column(Integer, ForeignKey('audit_sessions.id'), nullable=False)
    finding_json = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class FAQRecord(Base):
    __tablename__ = "faq_records"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True)
    audit_session_id = Column(Integer, ForeignKey('audit_sessions.id'), nullable=False)
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)
    category = Column(String, nullable=True)
    relevance_score = Column(Float, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class ChatMessage(Base):
    __tablename__ = "chat_messages"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True)
    audit_session_id = Column(Integer, ForeignKey('audit_sessions.id'), nullable=False)
    role = Column(String, nullable=False)  # 'user' or 'assistant'
    content = Column(Text, nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
