from pathlib import Path
from unittest.mock import patch

from backend.core.audit_workflow import AuditWorkflow
from backend.llm.manager import LLMManager

srs_path = Path('aurora_srs.txt')
if not srs_path.exists():
    raise FileNotFoundError(str(srs_path))

with patch.object(LLMManager, 'generate', side_effect=Exception('no llm')):
    workflow = AuditWorkflow()
    result = workflow.execute_audit(
        repository_context={
            'repo_path': '.',
            'vector_namespace': 'default',
            'languages': ['python'],
            'file_count': 100,
            'total_lines': 50000,
        },
        srs_path=str(srs_path),
        provider='groq',
        audit_run_id='aurora-classification-test'
    )

semantic_features = result.get('semantic_features', [])
ownership = result.get('feature_ownership', [])
timeline = result.get('timeline_analysis', [])

print('SEMANTIC_FEATURES_COUNT:', len(semantic_features))
print('OWNERSHIP_COUNT:', len(ownership))
print('TIMELINE_COUNT:', len(timeline))

semantic_matches = result.get('semantic_matches', [])
optional_matches = result.get('optional_intelligence', {}).get('semantic_matches', [])

for section_name, matches in [('semantic_matches', semantic_matches), ('optional_intelligence.semantic_matches', optional_matches)]:
    found = False
    for item in matches:
        matches_payload = item.get('matches') if isinstance(item, dict) else None
        if isinstance(matches_payload, dict) and 'documents' in matches_payload:
            found = True
            break
    print(f'{section_name}.documents exists:', found)

print('RESULT_KEYS:', sorted(result.keys()))
