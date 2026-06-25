import os
import json
from backend.storage.database import DATABASE_URL, SessionLocal
from backend.storage.models import Audit

print('LOCAL_ENV_DATABASE_URL', os.getenv('DATABASE_URL'))
print('LOCAL_MODULE_DATABASE_URL', DATABASE_URL)

db = SessionLocal()
audit = db.query(Audit).order_by(Audit.id.desc()).first()
print('LOCAL_AUDIT_EXISTS', bool(audit))
if audit:
    print('LOCAL_LATEST_ID', audit.id)
    print('LOCAL_PROJECT_NAME', audit.project_name)
    print('LOCAL_HEALTH_SCORE', audit.health_score)
    payload = audit.ai_summary or ''
    print('LOCAL_AI_SUMMARY_PREFIX', payload[:200])
    parsed = json.loads(payload)
    print('LOCAL_SEM_FEATURES_COUNT', len(parsed.get('semantic_features', [])))
    print('LOCAL_FEATURE_OWNERSHIP_COUNT', len(parsed.get('feature_ownership', [])))
    print('LOCAL_TIMELINE_ANALYSIS_COUNT', len(parsed.get('timeline_analysis', [])))
    print('LOCAL_INSIGHTS_COUNT', len(parsed.get('insights', [])))

db.close()
