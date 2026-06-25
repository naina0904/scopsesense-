import sys, json
sys.path.insert(0, '/app')
from backend.storage.database import SessionLocal
from backend.storage.models_extended import PlatformFetchResult

db = SessionLocal()
fetch = db.query(PlatformFetchResult).filter_by(id=19).first()
raw_data = json.loads(fetch.raw_data) if isinstance(fetch.raw_data, str) else fetch.raw_data

found_worklog = False
for issue in raw_data.get('issues', []):
    key = issue.get('key')
    fields = issue.get('fields', {})
    tt = fields.get('timetracking', {})
    wl = fields.get('worklog', {})
    if tt or wl.get('total', 0) > 0:
        print(f"Issue: {key} HAS worklog or timetracking! TT: {tt}, WL Total: {wl.get('total')}")
        found_worklog = True

if not found_worklog:
    print("NO WORKLOGS OR TIMETRACKING FOUND ON ANY ISSUE IN FETCH ID 19!")
