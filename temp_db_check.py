import json
from backend.storage.database import SessionLocal
from backend.storage.models import Audit

db = SessionLocal()
try:
    latest = db.query(Audit).order_by(Audit.id.desc()).first()
    print('LATEST_ID:', latest.id if latest else None)
    print('PROJECT_NAME:', latest.project_name if latest else None)
    print('HEALTH_SCORE:', latest.health_score if latest else None)
    print('SEMANTIC_CONFIDENCE:', latest.semantic_confidence if latest else None)
    print('HAS_AISUMMARY:', bool(latest and latest.ai_summary))
    if latest and latest.ai_summary:
        payload = json.loads(latest.ai_summary)
        print('SEMANTIC_FEATURES_COUNT:', len(payload.get('semantic_features', [])))
        print('FEATURE_OWNERSHIP_COUNT:', len(payload.get('feature_ownership', [])))
        print('TIMELINE_ANALYSIS_COUNT:', len(payload.get('timeline_analysis', [])))
        print('INSIGHTS_COUNT:', len(payload.get('insights', [])))
        print('AI_SUMMARY_TYPE:', type(payload.get('ai_summary')).__name__)
        print('AI_SUMMARY_LENGTH:', len(payload.get('ai_summary') or ''))
finally:
    db.close()
