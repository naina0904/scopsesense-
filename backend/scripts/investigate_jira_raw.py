import sys
import json
sys.path.insert(0, '/app')

from backend.storage.database import SessionLocal
from backend.storage.models_extended import PlatformFetchResult

def investigate():
    db = SessionLocal()
    try:
        fetches = db.query(PlatformFetchResult).filter_by(platform="jira").order_by(PlatformFetchResult.id.desc()).all()
        issues = []
        for fetch in fetches:
            raw_data = fetch.raw_data
            if isinstance(raw_data, str):
                raw_data = json.loads(raw_data)
            _issues = raw_data.get('issues', []) if isinstance(raw_data, dict) else []
            if len(_issues) > 0:
                issues = _issues
                print(f"Found {len(issues)} issues in fetch ID {fetch.id}.")
                break
        
        if not issues:
            print("No Jira data with >0 issues found in history.")
            return

        print("=== STANDALONE INVESTIGATION ===")
        for issue in issues:
            key = issue.get("key")
            fields = issue.get("fields", {})
            issue_type = fields.get("issuetype", {}).get("name")
            
            parent_link = fields.get("parent")
            parent_key = parent_link.get("key") if isinstance(parent_link, dict) else parent_link

            epic_10008 = fields.get("customfield_10008")
            epic_10014 = fields.get("customfield_10014")
            
            components = fields.get("components", [])
            components_val = [c.get("name") for c in components]

            print(f"Issue: {key} | Type: {issue_type}")
            print(f"  Parent Field Value: {parent_key}")
            print(f"  Epic Link (10008): {epic_10008}")
            print(f"  Epic Link (10014): {epic_10014}")
            print(f"  Components Value: {components_val}")
            print("-")

        print("\n=== ACTUAL HOURS INVESTIGATION ===")
        for issue in issues:
            key = issue.get("key")
            fields = issue.get("fields", {})
            
            timespent = fields.get("timespent")
            aggregatetimespent = fields.get("aggregatetimespent")
            timeoriginalestimate = fields.get("timeoriginalestimate")
            
            timetracking = fields.get("timetracking", {})
            timetracking_spent = timetracking.get("timeSpentSeconds")

            print(f"Issue: {key}")
            print(f"  timespent: {timespent}")
            print(f"  aggregatetimespent: {aggregatetimespent}")
            print(f"  timeoriginalestimate: {timeoriginalestimate}")
            print(f"  timetracking.timeSpentSeconds: {timetracking_spent}")
            print("-")

    finally:
        db.close()

if __name__ == "__main__":
    investigate()
