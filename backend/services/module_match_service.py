from backend.models.module_match import ModuleMatch
from backend.storage.repositories_extended import SessionLocal
from backend.storage.models_extended import ModuleMatch as ModuleMatchORM

class ModuleMatchService:
    """Service layer for persisting and retrieving ModuleMatch records.

    This bridges the Pydantic/Dataclass model used by the application logic
    with the SQLAlchemy ORM model defined in ``models_extended``.
    """

    @staticmethod
    def save(match: ModuleMatch) -> ModuleMatchORM:
        """Persist a ``ModuleMatch`` instance and return the ORM object."""
        from datetime import datetime
        db = SessionLocal()
        try:
            orm = ModuleMatchORM(
                audit_session_id=match.metadata.get('audit_session_id', 0),
                srs_node_id=match.srs_node_id,
                feature_id=match.feature_id,
                confidence_score=match.confidence_score,
                approval_status=match.approval_status,
                approval_timestamp=match.approval_timestamp,
                # Store raw metadata for future reference
                # JSON column can store arbitrary dict
                # Assuming ``metadata`` field exists on ORM (SQLAlchemy uses JSON column)
                # For simplicity we skip extra metadata beyond ORM fields
            )
            db.add(orm)
            db.commit()
            db.refresh(orm)
            return orm
        finally:
            db.close()

    @staticmethod
    def get_pending(audit_session_id: int = None):
        """Return list of pending (awaiting manager approval) matches, optionally filtered by session."""
        db = SessionLocal()
        try:
            query = db.query(ModuleMatchORM).filter(ModuleMatchORM.approval_status == 'PENDING_REVIEW')
            if audit_session_id is not None:
                query = query.filter(ModuleMatchORM.audit_session_id == audit_session_id)
            return query.all()
        finally:
            db.close()

    @staticmethod
    def approve(match_id: int) -> bool:
        """Mark a pending match as approved by a manager. Returns True if successful."""
        from datetime import datetime
        db = SessionLocal()
        try:
            mm = db.query(ModuleMatchORM).filter(
                ModuleMatchORM.id == match_id,
                ModuleMatchORM.approval_status == 'PENDING_REVIEW'
            ).first()
            if not mm:
                return False
            mm.approval_status = 'APPROVED'
            mm.approval_timestamp = datetime.utcnow()
            db.commit()
            return True
        finally:
            db.close()

    @staticmethod
    def reject(match_id: int) -> bool:
        """Mark a pending match as rejected. Returns True if successful."""
        from datetime import datetime
        db = SessionLocal()
        try:
            mm = db.query(ModuleMatchORM).filter(
                ModuleMatchORM.id == match_id,
                ModuleMatchORM.approval_status == 'PENDING_REVIEW'
            ).first()
            if not mm:
                return False
            mm.approval_status = 'REJECTED'
            mm.approval_timestamp = datetime.utcnow()
            db.commit()
            return True
        finally:
            db.close()
