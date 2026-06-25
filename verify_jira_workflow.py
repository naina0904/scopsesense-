import sys
import json
import logging
sys.path.append('/app')
from backend.services.platform_fetch_service import PlatformFetchService
from backend.integrations.core.unified_schema import PlatformData

logging.basicConfig(level=logging.INFO)

def log_stage(stage, inputs, outputs, obj_types, assumptions, failures):
    print(f"\n{'='*40}")
    print(f"STAGE: {stage}")
    print(f"{'='*40}")
    print(f"INPUTS: {inputs}")
    print(f"OUTPUTS: {outputs}")
    print(f"OBJECT TYPES: {obj_types}")
    print(f"ASSUMPTIONS: {assumptions}")
    if failures:
        print(f"FAILURES: {failures}")
    else:
        print("FAILURES: None")

def main():
    service = PlatformFetchService()
    project_key = 'SCRUM'
    domain = 'nainabhandari411.atlassian.net'
    import os
    token = os.getenv("JIRA_API_TOKEN", "")
    email = 'nainabhandari411@gmail.com'

    # Clear previous DB state to ensure a clean run
    # Actually, we should test the exact failure state, which is a DELTA fetch.
    # We will run fetch_jira ONCE (which works and saves to DB).
    # Then we run it AGAIN (which triggers the delta merge and crashes).
    
    print("\n\n>>> RUNNING INITIAL FETCH (BASELINE) <<<")
    try:
        fetch_entry1, adapter1 = service.fetch_jira(project_key, domain, token, email)
        log_stage("Initial Fetch", 
                 "Valid Jira Credentials", 
                 f"FetchEntry with {len(fetch_entry1.actual_data_json)} canonical records", 
                 "Features inside PlatformData are Feature objects", 
                 "Assuming initial fetch succeeds without existing data", 
                 None)
    except Exception as e:
        log_stage("Initial Fetch", "Valid Jira Credentials", None, None, None, f"Exception: {str(e)}")

    print("\n\n>>> RUNNING SECOND FETCH (DELTA UPSERT) <<<")
    try:
        fetch_entry2, adapter2 = service.fetch_jira(project_key, domain, token, email)
        log_stage("Delta Fetch", 
                 "Valid Jira Credentials + Existing DB State", 
                 f"FetchEntry with {len(fetch_entry2.actual_data_json)} canonical records", 
                 "Features inside PlatformData are dicts after DB load", 
                 "Assuming _merge_platform_data and subsequent steps handle dicts safely", 
                 None)
    except Exception as e:
        import traceback
        log_stage("Delta Fetch", "Valid Jira Credentials + Existing DB State", None, None, "Assuming safe dict handling", f"Exception: {str(e)}\n{traceback.format_exc()}")

if __name__ == "__main__":
    main()
