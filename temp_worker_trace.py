import os
import json
import shutil
from backend.srs.parser import SRSParser
from backend.srs.extractor import SRSFeatureExtractor
from backend.services.audit_service import AuditService
from backend.core.audit_workflow import AuditWorkflow

PROJECT_OWNER = "naina0904"
PROJECT_REPO = "aurora-engineering-platform"
SRS_FILENAME = "srs_7f6125c1cb3848d8ab6d969eb8b09983_auroraengineeringplatform (1).xlsx"
SRS_PATH = os.path.join("data", "uploads", SRS_FILENAME)

print(f"SRS_PATH: {SRS_PATH}")
print(f"SRS_EXISTS: {os.path.exists(SRS_PATH)}")

parsed_content = None
features = []

if os.path.exists(SRS_PATH):
    parser = SRSParser()
    parsed = parser.parse(SRS_PATH)
    parsed_content = parsed.get("raw_content", "")
    print(f"PARSED_RAW_LENGTH: {len(parsed_content)}")
    print("PARSED_PREVIEW:")
    print(parsed_content[:500])
    extractor = SRSFeatureExtractor()
    features = extractor.extract_features(parsed_content)
    print(f"SRS_FEATURE_EXTRACTOR_OUTPUT_COUNT: {len(features)}")
    print("SRS_FEATURES_SAMPLE:")
    print(json.dumps(features[:5], indent=2))
else:
    print("SRS_FILE_NOT_FOUND")

service = AuditService()
repository_context = service._build_repository_context(PROJECT_OWNER, PROJECT_REPO)
print(f"REPO_PATH: {repository_context.get('repo_path')}")
print(f"REPO_PATH_EXISTS: {os.path.exists(repository_context.get('repo_path') or '')}")
print(f"VECTOR_NAMESPACE: {repository_context.get('vector_namespace')}")
print(f"CONTRIBUTORS_COUNT: {len(repository_context.get('contributors', []))}")
print(f"ACTIVITY_COUNT: {len(repository_context.get('activity', []))}")
print(f"COMMIT_VELOCITY: {repository_context.get('commit_velocity')}")

workflow = AuditWorkflow(provider='gemini')
result = workflow.execute_audit(
    repository_context=repository_context,
    srs_path=SRS_PATH if os.path.exists(SRS_PATH) else None,
    provider='gemini',
    audit_run_id='forensic-trace-aurora'
)

print(f"RESULT_SEMANTIC_FEATURES_COUNT: {len(result.get('semantic_features', []))}")
print(f"RESULT_FEATURE_OWNERSHIP_COUNT: {len(result.get('feature_ownership', []))}")
print(f"RESULT_TIMELINE_ANALYSIS_COUNT: {len(result.get('timeline_analysis', []))}")
print(f"RESULT_INSIGHTS_COUNT: {len(result.get('insights', []))}")
print(f"RESULT_HEALTH_SCORE: {result.get('health_score')}")
print(f"RESULT_SEMANTIC_CONFIDENCE: {result.get('semantic_confidence')}")
print("RESULT_KEYS:")
print(sorted(result.keys()))
print("AI_SUMMARY_BEFORE_PERSISTENCE:")
print(json.dumps(result, indent=2)[:3000])

repo_path = repository_context.get('repo_path')
if repo_path and os.path.exists(repo_path):
    try:
        shutil.rmtree(repo_path)
        print(f"CLEANED_REPO_PATH: {repo_path}")
    except Exception as e:
        print(f"FAILED_CLEANUP_REPO_PATH: {e}")
