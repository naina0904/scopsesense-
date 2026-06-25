import os
import json
from pathlib import Path

def list_files(base_path, patterns=None):
    files = []
    for root, dirs, filenames in os.walk(base_path):
        for f in filenames:
            if patterns and not any(f.endswith(p) for p in patterns):
                continue
            rel = os.path.relpath(os.path.join(root, f), base_path)
            files.append(rel)
    return files

def main():
    project_root = Path(__file__).resolve().parents[2]  # scopesense-v2 root
    backend_path = project_root / "backend"
    frontend_path = project_root / "frontend"

    snapshot = {
        "backend_modules": list_files(backend_path, patterns=[".py"]),
        "frontend_files": list_files(frontend_path, patterns=[".js", ".jsx", ".ts", ".tsx"]),
        "models": list_files(backend_path / "storage" / "models", patterns=[".py"]),
        "api_routes": list_files(backend_path / "api", patterns=[".py"]),
        "celery_tasks": list_files(backend_path / "tasks", patterns=[".py"]),
        "websocket": list_files(backend_path / "websocket", patterns=[".py"]),
    }
    output_path = project_root / "scripts" / "project_snapshot.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as fp:
        json.dump(snapshot, fp, indent=2)
    print(f"Snapshot written to {output_path}")

if __name__ == "__main__":
    main()
