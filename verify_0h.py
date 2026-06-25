import os
import json
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Assuming DB_URL is in environment
DB_URL = os.environ.get("DATABASE_URL", "postgresql://scopesense:scopesense@db:5432/scopesense")
engine = create_engine(DB_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
db = SessionLocal()

result = db.execute(text("SELECT platform_data_json FROM platform_fetch_results ORDER BY id DESC LIMIT 1")).fetchone()
if not result:
    print("No platform fetch results found.")
    exit(0)

platform_data_json = result[0]
features = platform_data_json.get("features", [])

print(f"Total features: {len(features)}")
for f in features:
    issue_key = f.get("issue_key") or f.get("id")
    hierarchy = f.get("hierarchy_level", "UNKNOWN")
    actual_hours = f.get("actual_hours", 0)
    print(f"Feature: {issue_key} | Hierarchy: {hierarchy} | Actual Hours: {actual_hours}")

db.close()
