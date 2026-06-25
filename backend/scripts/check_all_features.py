import sys
sys.path.insert(0, '/app')
from backend.storage.database import SessionLocal
from backend.storage.models import Feature

db = SessionLocal()
features = db.query(Feature).all()
print(f"Total features in database: {len(features)}")

# Check for actual_hours or estimated_hours
hours_count = 0
for f in features:
    if f.actual_hours and f.actual_hours > 0:
        hours_count += 1
print(f"Features with actual_hours > 0 in database: {hours_count}")
