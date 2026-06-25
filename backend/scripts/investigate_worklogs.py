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
        
        target_keys = ["SCRUM-35", "SCRUM-32", "SCRUM-31", "SCRUM-26", "SCRUM-24"]
        
        print("=== WORKLOG AND STORY POINT INVESTIGATION ===")
        for issue in issues:
            key = issue.get("key")
            if key in target_keys:
                print(f"\n--- ISSUE: {key} ---")
                fields = issue.get("fields", {})
                
                # Check timetracking
                timetracking = fields.get("timetracking", "NOT_PRESENT")
                print(f"fields.timetracking = {timetracking}")
                
                # Check time spent
                timespent = fields.get("timespent", "NOT_PRESENT")
                print(f"fields.timespent = {timespent}")
                
                # Check aggregatetimespent
                aggregatetimespent = fields.get("aggregatetimespent", "NOT_PRESENT")
                print(f"fields.aggregatetimespent = {aggregatetimespent}")
                
                # Check timeoriginalestimate
                timeoriginalestimate = fields.get("timeoriginalestimate", "NOT_PRESENT")
                print(f"fields.timeoriginalestimate = {timeoriginalestimate}")
                
                # Check worklog
                worklog = fields.get("worklog", "NOT_PRESENT")
                print(f"fields.worklog = {json.dumps(worklog)[:200] if isinstance(worklog, dict) else worklog}...")
                
                # Story points
                # Check custom fields that look like numbers
                for k, v in fields.items():
                    if k.startswith("customfield_") and isinstance(v, (int, float)):
                        print(f"Possible Story Points: {k} = {v}")

    finally:
        db.close()

if __name__ == "__main__":
    investigate()
