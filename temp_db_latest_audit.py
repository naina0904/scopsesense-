import psycopg2, json

conn = None
try:
    conn = psycopg2.connect("postgresql://postgres:12345@localhost:5433/scopesense")
    cur = conn.cursor()
    cur.execute("SELECT id, created_at, ai_summary FROM audits ORDER BY id DESC LIMIT 1")
    row = cur.fetchone()
    if not row:
        print('NO_ROW')
    else:
        id, created_at, ai_summary = row
        print('ID:', id)
        print('CREATED_AT:', created_at)
        if not ai_summary:
            print('AI_SUMMARY_EMPTY')
        else:
            obj = json.loads(ai_summary)
            sf = obj.get('semantic_features', [])
            fo = obj.get('feature_ownership', [])
            ta = obj.get('timeline_analysis', [])
            # prepare display names
            def name_of(f):
                return f.get('feature_name') or f.get('name') or f.get('feature')
            print('SEMANTIC_FEATURES_COUNT:', len(sf))
            vt = obj.get('variance_table', [])
            print('VARIANCE_TABLE_COUNT:', len(vt))
            total_planned = sum(float(x.get('planned_hours', 0)) for x in vt)
            total_actual = sum(float(x.get('actual_hours', 0)) for x in vt)
            print('TOTAL_PLANNED_HOURS_IN_VT:', total_planned)
            print('TOTAL_ACTUAL_HOURS_IN_VT:', total_actual)
            for x in vt:
                print(f"  Req: {x.get('requirement')[:30]}... | Planned: {x.get('planned_hours')} | Actual: {x.get('actual_hours')}")
    cur.close()
except Exception as e:
    import traceback
    traceback.print_exc()
finally:
    if conn:
        conn.close()
