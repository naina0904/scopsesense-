import json
try:
    import chromadb
    client = chromadb.PersistentClient(path="data/chroma")
    cols = client.list_collections()
    out = []
    total = 0
    for c in cols:
        try:
            col = client.get_collection(name=c.name)
            cnt = col.count()
        except Exception:
            try:
                cnt = c.count()
            except Exception:
                cnt = 'unknown'
        out.append({'name': c.name, 'count': cnt})
        if isinstance(cnt, int):
            total += cnt
    print(json.dumps({'collections': out, 'total_vectors': total}, indent=2))
except Exception as e:
    print(json.dumps({'error': str(e)}))
