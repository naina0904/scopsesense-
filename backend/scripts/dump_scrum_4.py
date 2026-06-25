import sys
import json
sys.path.insert(0, '/app')

from backend.storage.database import SessionLocal
from backend.storage.models_extended import PlatformFetchResult

def investigate():
    db = SessionLocal()
    try:
        fetch = db.query(PlatformFetchResult).filter_by(id=19).first()
        raw_data = fetch.raw_data
        if isinstance(raw_data, str):
            raw_data = json.loads(raw_data)
        
        issues = raw_data.get('issues', [])
        
        for issue in issues:
            key = issue.get("key")
            if key in ["SCRUM-35", "SCRUM-4"]:
                print(f"\n--- ISSUE: {key} ---")
                fields = issue.get("fields", {})
                
                print("Issue Type:", fields.get("issuetype", {}).get("name"))
                print("Status:", fields.get("status", {}).get("name"))
                assignee = fields.get("assignee")
                print("Assignee:", assignee.get("displayName") if assignee else "None")
                
                # Check timetracking
                timetracking = fields.get("timetracking", "NOT_PRESENT")
                print(f"timetracking = {timetracking}")
                
                # Check worklog
                worklog = fields.get("worklog", "NOT_PRESENT")
                print(f"worklog = {json.dumps(worklog) if isinstance(worklog, dict) else worklog}")
                
                # Subtasks
                subtasks = fields.get("subtasks", [])
                print(f"subtasks = {json.dumps(subtasks)}")

    finally:
        db.close()

if __name__ == "__main__":
    investigate()
