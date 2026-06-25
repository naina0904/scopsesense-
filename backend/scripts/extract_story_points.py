import sys, json
sys.path.insert(0, '/app')
from backend.storage.database import SessionLocal
from backend.storage.models_extended import PlatformFetchResult
from backend.integrations.jira.jira_adapter import JiraAdapter

db = SessionLocal()
fetch = db.query(PlatformFetchResult).filter_by(id=19).first()
raw_data = json.loads(fetch.raw_data) if isinstance(fetch.raw_data, str) else fetch.raw_data

sp_field = raw_data.get('story_point_field_id', 'customfield_10016')

print(f"Using Story Point Field ID: {sp_field}")
print("Issue Key | Issue Type | Story Points | Assignee | Status")
print("-" * 60)

for issue in raw_data.get('issues', []):
    key = issue.get('key')
    fields = issue.get('fields', {})
    sp = fields.get(sp_field)
    
    if sp is not None:
        issue_type = fields.get('issuetype', {}).get('name', 'Unknown')
        status = fields.get('status', {}).get('name', 'Unknown')
        assignee = fields.get('assignee')
        assignee_name = assignee.get('displayName', 'Unassigned') if assignee else 'Unassigned'
        
        print(f"{key} | {issue_type} | {sp} | {assignee_name} | {status}")
