from backend.storage.database import SessionLocal
from backend.storage.models_extended import (
    SRSExtractionResult,
    PlatformFetchResult,
    AuditComparison,
    VarianceResult,
    RootCauseResult,
    ChatSession,
    IntegrationSyncState
)

class IntegrationSyncStateRepository:
    def get(self, platform: str, identifier: str):
        db = SessionLocal()
        try:
            return db.query(IntegrationSyncState).filter(
                IntegrationSyncState.platform == platform,
                IntegrationSyncState.identifier == identifier
            ).first()
        finally:
            db.close()

    def upsert(self, platform: str, identifier: str, last_synced_at):
        db = SessionLocal()
        try:
            state = db.query(IntegrationSyncState).filter(
                IntegrationSyncState.platform == platform,
                IntegrationSyncState.identifier == identifier
            ).first()
            
            if state:
                state.last_synced_at = last_synced_at
                state.last_successful_sync_at = last_synced_at
            else:
                state = IntegrationSyncState(
                    platform=platform,
                    identifier=identifier,
                    last_synced_at=last_synced_at,
                    last_successful_sync_at=last_synced_at
                )
                db.add(state)
            
            db.commit()
            db.refresh(state)
            return state
        finally:
            db.close()

class SRSRepository:
    def save(self, uploaded_at, raw_file_path, extracted_json):
        db = SessionLocal()
        try:
            srs = SRSExtractionResult(
                uploaded_at=uploaded_at,
                raw_file_path=raw_file_path,
                extracted_json=extracted_json,
            )
            db.add(srs)
            db.commit()
            db.refresh(srs)
            return srs
        finally:
            db.close()

    def get(self, srs_id):
        db = SessionLocal()
        try:
            return db.query(SRSExtractionResult).filter(SRSExtractionResult.id == srs_id).first()
        finally:
            db.close()

class PlatformFetchRepository:
    def save(self, platform, raw_data, actual_data_json=None, platform_data_json=None, organization_profile_json=None):
        db = SessionLocal()
        try:
            fetch = PlatformFetchResult(
                platform=platform,
                raw_data=raw_data,
                actual_data_json=actual_data_json,
                platform_data_json=platform_data_json,
                organization_profile_json=organization_profile_json
            )
            db.add(fetch)
            db.commit()
            db.refresh(fetch)
            return fetch
        finally:
            db.close()

    def get(self, fetch_id):
        db = SessionLocal()
        try:
            return db.query(PlatformFetchResult).filter(PlatformFetchResult.id == fetch_id).first()
        finally:
            db.close()

    def get_latest(self, platform: str):
        # We assume the user wants the latest snapshot for this platform
        db = SessionLocal()
        try:
            # We can order by id desc since it's sequential
            return db.query(PlatformFetchResult).filter(
                PlatformFetchResult.platform == platform
            ).order_by(PlatformFetchResult.id.desc()).first()
        finally:
            db.close()

class AuditComparisonRepository:
    def save(self, srs_result_id, platform_result_id, comparison_json):
        db = SessionLocal()
        try:
            comp = AuditComparison(
                srs_result_id=srs_result_id,
                platform_result_id=platform_result_id,
                comparison_json=comparison_json,
            )
            db.add(comp)
            db.commit()
            db.refresh(comp)
            return comp
        finally:
            db.close()

    def get(self, comp_id):
        db = SessionLocal()
        try:
            return db.query(AuditComparison).filter(AuditComparison.id == comp_id).first()
        finally:
            db.close()

# Similar simple repositories for VarianceResult, RootCauseResult, FAQResult, ChatSession can be added as needed.
