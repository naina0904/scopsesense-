import sys
sys.path.append('/app')
from backend.services.platform_fetch_service import PlatformFetchService

try:
    service = PlatformFetchService()
    token = os.getenv("JIRA_API_TOKEN", "")
    fetch_entry, adapter = service.fetch_jira(
        project_key='SCRUM', 
        domain='nainabhandari411.atlassian.net', 
        api_token=token, 
        email='nainabhandari411@gmail.com'
    )
    print("SUCCESS!")
    print("Features Length:", len(fetch_entry.actual_data_json))
except Exception as e:
    import traceback
    print("ERROR!")
    traceback.print_exc()
