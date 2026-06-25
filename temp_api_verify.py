import json
import urllib.request
from urllib.error import URLError, HTTPError
from backend.storage.database import SessionLocal
from backend.storage.models import Audit

url = 'http://localhost:8000/audit/latest'
print('URL:', url)
try:
    with urllib.request.urlopen(url, timeout=20) as resp:
        api_body = resp.read().decode('utf-8')
        print('HTTP_STATUS:', resp.status)
        api_json = json.loads(api_body)
except HTTPError as e:
    print('HTTP_ERROR', e.code, e.reason)
    api_json = None
except URLError as e:
    print('URL_ERROR', e.reason)
    api_json = None
except Exception as e:
    print('EXCEPTION', repr(e))
    api_json = None

if api_json is None:
    raise SystemExit('API request failed')

print('API_RAW_KEYS:', sorted(api_json.keys()))
result = api_json.get('result')
print('API_RESULT_TYPE:', type(result).__name__)
if isinstance(result, dict):
    print('API_TOP_KEYS:', sorted(result.keys()))
    print('API_SEM_FEATURES_COUNT:', len(result.get('semantic_features', [])))
    print('API_FEATURE_OWNERSHIP_COUNT:', len(result.get('feature_ownership', [])))
    print('API_TIMELINE_ANALYSIS_COUNT:', len(result.get('timeline_analysis', [])))
    print('API_INSIGHTS_COUNT:', len(result.get('insights', [])))
    print('API_PROJECT_NAME:', result.get('project_name'))
    print('API_HEALTH_SCORE:', result.get('health_score'))
    print('API_SEMANTIC_CONFIDENCE:', result.get('semantic_confidence'))
else:
    raise SystemExit('API result was not a JSON object')

# load DB payload

db = SessionLocal()
audit = db.query(Audit).order_by(Audit.id.desc()).first()
if not audit:
    raise SystemExit('No audit row found')
if not audit.ai_summary:
    raise SystemExit('No ai_summary in audit row')
db_payload = json.loads(audit.ai_summary)
print('DB_TOP_KEYS:', sorted(db_payload.keys()))
print('DB_SEM_FEATURES_COUNT:', len(db_payload.get('semantic_features', [])))
print('DB_FEATURE_OWNERSHIP_COUNT:', len(db_payload.get('feature_ownership', [])))
print('DB_TIMELINE_ANALYSIS_COUNT:', len(db_payload.get('timeline_analysis', [])))
print('DB_INSIGHTS_COUNT:', len(db_payload.get('insights', [])))
print('DB_PROJECT_NAME:', db_payload.get('project_name'))
print('DB_HEALTH_SCORE:', db_payload.get('health_score'))
print('DB_SEMANTIC_CONFIDENCE:', db_payload.get('semantic_confidence'))

def compare_struct(a, b, path=''):
    if type(a) != type(b):
        return [(path or 'root', type(a).__name__, type(b).__name__, a, b)]
    if isinstance(a, dict):
        diffs = []
        all_keys = sorted(set(a) | set(b))
        for key in all_keys:
            ka = a.get(key, '__MISSING__')
            kb = b.get(key, '__MISSING__')
            newpath = f"{path}.{key}" if path else key
            if ka == '__MISSING__' or kb == '__MISSING__':
                diffs.append((newpath, ka, kb, 'MISSING', 'MISSING'))
            else:
                diffs.extend(compare_struct(ka, kb, newpath))
        return diffs
    if isinstance(a, list):
        if len(a) != len(b):
            return [(path, len(a), len(b), 'LENGTH_MISMATCH', 'LENGTH_MISMATCH')]
        diffs = []
        for i, (ea, eb) in enumerate(zip(a, b)):
            diffs.extend(compare_struct(ea, eb, f"{path}[{i}]") )
        return diffs
    if a != b:
        return [(path, a, b, 'VALUE_MISMATCH', 'VALUE_MISMATCH')]
    return []

comparison = compare_struct(db_payload, result)
print('DIFF_COUNT:', len(comparison))
for diff in comparison[:100]:
    print('DIFF:', diff)

if len(comparison) == 0:
    print('IDENTICAL: True')
else:
    print('IDENTICAL: False')
