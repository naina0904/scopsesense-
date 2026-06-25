import sys, json
sys.path.insert(0, '/app')
from backend.storage.database import SessionLocal
from backend.storage.models_extended import PlatformFetchResult

db = SessionLocal()
fetch = db.query(PlatformFetchResult).filter_by(id=19).first()
raw_data = json.loads(fetch.raw_data) if isinstance(fetch.raw_data, str) else fetch.raw_data

# The fetch method get_issues returns a dict with 'project', 'issues', etc.
# Wait, JiraClient.get_issues returns List[Dict] or does JiraAdapter wrap it?
# In jira_adapter.py: return {"project": project, "issues": issues, "boards": boards, ...}
# So 'issues' is just the list of issues that were fetched!
issues = raw_data.get('issues', [])
print("Number of issues fetched in ID 19:", len(issues))

tempo_fields = set()
third_party_clues = []

for issue in issues:
    fields = issue.get('fields', {})
    for k, v in fields.items():
        if isinstance(v, dict):
            v_str = json.dumps(v).lower()
            if 'tempo' in v_str or 'timesheet' in v_str:
                tempo_fields.add(k)
                third_party_clues.append(f"{issue.get('key')} has {k}: {v_str[:100]}")
        elif isinstance(v, str):
            v_str = v.lower()
            if 'tempo' in v_str or 'timesheet' in v_str:
                tempo_fields.add(k)

print("Potential Third-Party/Tempo Fields Found:", tempo_fields)
if third_party_clues:
    print("Examples:")
    for clue in third_party_clues[:5]:
        print(f"  - {clue}")

