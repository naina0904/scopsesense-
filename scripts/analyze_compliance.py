import json
from pathlib import Path

# Hard‑coded list of required architectural elements extracted from ARCHITECTURE.md
REQUIRED = {
    "api_routes": [
        "/audit/start",
        "/profile",
        "/task/{task_id}",
        "/analytics/overview",
        "/audits/history",
        "/contributors/history",
        "/features/history",
        "/analytics/history",
        "/analytics/risks",
        "/analytics/roadmap",
        # The spec mentions several endpoints that are currently missing:
        "/audit/upload",
        "/audit/status/{taskId}",
        "/chat",
        "/audit/history",
        "/contributors/history",
        "/features/history",
        "/analytics/history",
        "/analytics/risks",
        "/analytics/roadmap",
    ],
    "backend_methods": {
        "AuditService.execute_full_audit": "execute_audit",
        "AuditWorkflow.execute_audit": "execute_audit",
        "TimelineEngine.analyze_timeline": "analyze_semantic_timeline",
    },
    "model_fields": {
        "Feature": ["feature_name", "implementation_score", "repository"],
        "Contributor": ["developer_name", "commits", "repository"],
    },
    "frontend_components": [
        "AuditResults",
        "StatusDrawer",
        "SidebarNavigation",
    ],
}

def load_snapshot():
    proj_root = Path(__file__).resolve().parents[2]
    snap_path = proj_root / "scripts" / "project_snapshot.json"
    with open(snap_path, "r", encoding="utf-8") as f:
        return json.load(f)

def check_routes(snapshot):
    existing = set()
    for file in snapshot.get("api_routes", []):
        # naive extraction of route strings from the file names is not possible here;
        # we will simply assume that any .py file under backend/api defines routes.
        existing.add(file)
    missing = []
    for route in REQUIRED["api_routes"]:
        # check if route string appears in any route file (simple grep)
        found = False
        for file in snapshot.get("api_routes", []):
            file_path = Path(__file__).resolve().parents[2] / "backend" / "api" / file
            try:
                content = file_path.read_text(encoding="utf-8")
                if route in content:
                    found = True
                    break
            except Exception:
                continue
        if not found:
            missing.append(route)
    return missing

def check_backend_methods(snapshot):
    missing = []
    for method, expected in REQUIRED["backend_methods"].items():
        parts = method.split(".")
        class_name, func_name = parts[0], parts[1]
        # search in all backend python files for class and function name
        found = False
        for file in snapshot.get("backend_modules", []):
            if not file.endswith('.py'):
                continue
            file_path = Path(__file__).resolve().parents[2] / "backend" / file
            try:
                txt = file_path.read_text(encoding="utf-8")
                if f"class {class_name}" in txt and f"def {expected}" in txt:
                    found = True
                    break
            except Exception:
                continue
        if not found:
            missing.append(method)
    return missing

def check_model_fields(snapshot):
    missing = {}
    for model, fields in REQUIRED["model_fields"].items():
        # locate model file
        model_file = None
        for f in snapshot.get("models", []):
            if model.lower() in f.lower():
                model_file = f
                break
        if not model_file:
            missing[model] = fields
            continue
        file_path = Path(__file__).resolve().parents[2] / "backend" / "storage" / "models" / model_file
        try:
            txt = file_path.read_text(encoding="utf-8")
            absent = [fld for fld in fields if fld not in txt]
            if absent:
                missing[model] = absent
        except Exception:
            missing[model] = fields
    return missing

def check_frontend_components(snapshot):
    missing = []
    for comp in REQUIRED["frontend_components"]:
        found = False
        for f in snapshot.get("frontend_files", []):
            file_path = Path(__file__).resolve().parents[2] / "frontend" / f
            try:
                txt = file_path.read_text(encoding="utf-8")
                if comp in txt:
                    found = True
                    break
            except Exception:
                continue
        if not found:
            missing.append(comp)
    return missing

def main():
    snapshot = load_snapshot()
    report = {
        "missing_routes": check_routes(snapshot),
        "missing_backend_methods": check_backend_methods(snapshot),
        "missing_model_fields": check_model_fields(snapshot),
        "missing_frontend_components": check_frontend_components(snapshot),
    }
    out_path = Path(__file__).resolve().parents[2] / "scripts" / "compliance_report.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    print(f"Compliance data written to {out_path}")

if __name__ == "__main__":
    main()
