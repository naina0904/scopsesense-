import sys
sys.path.insert(0, '/app')
from backend.storage.database import SessionLocal
from backend.storage.models_extended import IntegrationSyncState

db = SessionLocal()
states = db.query(IntegrationSyncState).filter_by(platform="jira").all()
for s in states:
    print(f"Jira Sync State: identifier={s.identifier}, last_synced_at={s.last_synced_at}, full_sync_completed={s.full_sync_completed}")
