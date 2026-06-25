from database.session import get_db
from database.models import FetchEntry
import json

try:
    db = next(get_db())
    entry = db.query(FetchEntry).order_by(FetchEntry.created_at.desc()).first()
    if entry and entry.platform_data_json:
        pd = entry.platform_data_json
        print('Contributors count:', len(pd.get('contributors', [])))
        for c in pd.get('contributors', []):
            print(c.get('id'), c.get('name'))
    else:
        print('No entries found')
except Exception as e:
    print('Error:', e)
