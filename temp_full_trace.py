import os, json, sys
from datetime import datetime
from backend.srs.parser import SRSParser
from backend.srs.extractor import SRSFeatureExtractor
from backend.core.audit_workflow import AuditWorkflow
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

SRS_PATH = os.path.join('data','uploads','srs_7f6125c1cb3848d8ab6d969eb8b09983_auroraengineeringplatform (1).xlsx')
print('SRS_PATH', SRS_PATH)
parser = SRSParser()
parsed = parser.parse(SRS_PATH)
content = parsed.get('raw_content','')
print('PARSED_CONTENT_LENGTH', len(content))

extractor = SRSFeatureExtractor()
features = extractor.extract_features(content)
print('EXTRACTED_FEATURE_COUNT', len(features))
print('EXTRACTED_FEATURE_NAMES')
for f in features:
    print('-', f.get('feature_name'))

workflow = AuditWorkflow()
requirements = [f.get('feature_name') for f in features if f.get('feature_name')]
print('REQUIREMENTS_COUNT', len(requirements))
matches = []
if requirements:
    try:
        matches = workflow.requirement_matcher.match_requirements(requirements, namespace='default')
        print('REQUIREMENT_MATCHER_COUNT', len(matches))
    except Exception as e:
        print('REQUIREMENT_MATCHER_EXCEPTION', e)
        matches = []
else:
    print('REQUIREMENT_MATCHER_COUNT', 0)

try:
    ownership = workflow.feature_ownership_engine.analyze(features, activity=[], semantic_matches=matches)
    print('FEATURE_OWNERSHIP_COUNT', len(ownership))
except Exception as e:
    print('FEATURE_OWNERSHIP_EXCEPTION', e)
    ownership = []

# Timeline
repo_start = datetime.utcnow()
actual_completion = datetime.utcnow()
timeline_results = []
for feature in features:
    tr = workflow.timeline_engine.analyze_semantic_timeline(feature, repo_start, actual_completion, activity_gaps=[], commit_velocity='unknown')
    timeline_results.append(tr)
print('TIMELINE_ANALYSIS_COUNT', len(timeline_results))

# Query DB for latest aurora audit
DATABASE_URL = os.getenv('DATABASE_URL','postgresql://postgres:12345@db:5432/scopesense')
print('DB_URL', DATABASE_URL)
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
session = Session()
q = text("SELECT id, project_name, ai_summary FROM audits WHERE project_name like '%aurora%' ORDER BY id DESC LIMIT 1")
row = session.execute(q).fetchone()
if not row:
    print('NO_AUDIT_IN_DB')
    session.close()
    sys.exit(0)
audit_id, project_name, ai_summary = row
print('LATEST_AUDIT_ID', audit_id)
if ai_summary:
    summary = json.loads(ai_summary)
    sf = summary.get('semantic_features', [])
    fo = summary.get('feature_ownership', [])
    ta = summary.get('timeline_analysis', [])
    print('PERSISTED_semantic_features_count', len(sf))
    print('PERSISTED_feature_ownership_count', len(fo))
    print('PERSISTED_timeline_analysis_count', len(ta))
else:
    print('ai_summary_EMPTY')

session.close()
print('TRACE_COMPLETE')
