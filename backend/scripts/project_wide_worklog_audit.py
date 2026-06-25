import sys
import json
import os
sys.path.insert(0, '/app')

from backend.storage.database import SessionLocal
from backend.storage.models_extended import PlatformConfiguration, PlatformFetchResult
from backend.integrations.jira.jira_client import JiraClient

def run_audit():
    db = SessionLocal()
    
    try:
        # Get credentials
        config = db.query(PlatformConfiguration).filter_by(platform="JIRA").first()
        if not config:
            print("No JIRA config found!")
            return
            
        credentials = json.loads(config.credentials)
        client = JiraClient(
            domain=credentials.get("domain", "https://nainabhandari411.atlassian.net"),
            email=credentials.get("email"),
            api_token=credentials.get("api_token")
        )
        
        project_key = config.platform_key
        if not project_key:
            project_key = "SCRUM"
            
        print(f"--- PROJECT-WIDE WORKLOG AUDIT: {project_key} ---")
        
        # 1. Fetch ALL issues in the project
        print(f"\nFetching all issues for project {project_key}...")
        all_issues = client.get_issues(project_key=project_key, jql=f"project = {project_key}", max_results=100)
        
        print(f"1. Total number of issues in project {project_key}: {len(all_issues)}")
        
        # Check Fetch ID 19
        fetch = db.query(PlatformFetchResult).filter_by(id=19).first()
        fetch_raw = json.loads(fetch.raw_data) if isinstance(fetch.raw_data, str) else fetch.raw_data
        fetch_issues = fetch_raw.get('issues', [])
        
        print(f"4. Fetch ID 19 contains: {len(fetch_issues)} issues.")
        if len(all_issues) == len(fetch_issues):
            print("   -> Fetch ID 19 contains ALL project issues.")
        else:
            print("   -> Fetch ID 19 contains a subset of issues.")
            
        # Analyze worklogs
        worklog_count = 0
        timespent_count = 0
        aggregatetimespent_count = 0
        issues_with_worklogs = []
        
        # Track custom fields for Tempo or other time tracking
        tempo_fields_found = set()
        
        for issue in all_issues:
            fields = issue.get("fields", {})
            
            # Check native fields
            wl_total = fields.get("worklog", {}).get("total", 0)
            if wl_total > 0:
                worklog_count += 1
                
            ts = fields.get("timespent")
            if ts and ts > 0:
                timespent_count += 1
                
            ats = fields.get("aggregatetimespent")
            if ats and ats > 0:
                aggregatetimespent_count += 1
                
            if wl_total > 0 or (ts and ts > 0):
                assignee = fields.get('assignee')
                assignee_name = assignee.get('displayName', 'Unassigned') if assignee else 'Unassigned'
                issues_with_worklogs.append({
                    "key": issue.get("key"),
                    "type": fields.get("issuetype", {}).get("name", "Unknown"),
                    "assignee": assignee_name,
                    "count": wl_total,
                    "hours": round((ts or 0) / 3600, 2),
                    "status": fields.get("status", {}).get("name", "Unknown")
                })
                
            # Check for Tempo fields (Tempo fields are usually customfield_100xx and contain 'tempo' or 'team')
            for k, v in fields.items():
                if isinstance(v, dict):
                    v_str = json.dumps(v).lower()
                    if "tempo" in v_str:
                        tempo_fields_found.add(k)
        
        print("\n2. Worklog Metrics:")
        print(f"   - Issues with worklog.total > 0: {worklog_count}")
        print(f"   - Issues with timespent > 0: {timespent_count}")
        print(f"   - Issues with aggregatetimespent > 0: {aggregatetimespent_count}")
        
        print("\n3. Issues Containing Worklogs:")
        if issues_with_worklogs:
            print(f"{'Key':<10} | {'Type':<10} | {'Assignee':<20} | {'WL Count':<10} | {'Total Hours':<12} | {'Status':<15}")
            print("-" * 85)
            for iw in issues_with_worklogs:
                print(f"{iw['key']:<10} | {iw['type']:<10} | {iw['assignee']:<20} | {iw['count']:<10} | {iw['hours']:<12} | {iw['status']:<15}")
        else:
            print("   None.")
            
        print("\n5. Exact JQL Used by ScopeSense:")
        print("   Default: `project = [KEY]`")
        print("   If Incremental: `project = [KEY] AND updated >= '[DATE]'`")
        
        print("\n7 & 8. Third-Party Plugin Investigation:")
        if tempo_fields_found:
            print(f"   - Discovered Potential Tempo Fields: {tempo_fields_found}")
        else:
            print("   - No obvious 'Tempo' signatures found in custom fields.")
            
    finally:
        db.close()

if __name__ == "__main__":
    run_audit()
