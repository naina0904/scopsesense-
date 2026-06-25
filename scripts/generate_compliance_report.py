import json
from pathlib import Path

def load_compliance():
    proj_root = Path(__file__).resolve().parents[2]
    report_path = proj_root / "scripts" / "compliance_report.json"
    with open(report_path, "r", encoding="utf-8") as f:
        return json.load(f)

def calculate_percentages(report):
    # Simple metric: total checks = sum of lengths of each category list/dict
    total_checks = 0
    missing_counts = 0
    for key, value in report.items():
        if isinstance(value, list):
            total_checks += len(value) + (0)  # each item is a check
            missing_counts += len(value)
        elif isinstance(value, dict):
            total_checks += len(value)
            missing_counts += sum(1 for v in value.values() if v)  # any missing fields counted
    compliance = max(0, (total_checks - missing_counts) / total_checks * 100) if total_checks else 100
    demo_ready = compliance  # for simplicity, treat same
    return compliance, demo_ready

def highest_priority_missing(report):
    # Prioritize missing routes, then backend methods, then model fields, then frontend components
    for category in ["missing_routes", "missing_backend_methods", "missing_model_fields", "missing_frontend_components"]:
        missing = report.get(category)
        if missing:
            if isinstance(missing, list):
                return category, missing[0]
            if isinstance(missing, dict):
                # return first model with missing fields
                model, fields = next(iter(missing.items()))
                return category, f"{model}: {', '.join(fields)}"
    return None, None

def next_task(missing_category, missing_item):
    if missing_category == "missing_routes":
        return f"Implement API route {missing_item} in backend/api/routes.py and create corresponding frontend client wrapper."
    if missing_category == "missing_backend_methods":
        return f"Add/rename method {missing_item} to match the expected signature in the appropriate service class."
    if missing_category == "missing_model_fields":
        model, fields = missing_item.split(":")
        return f"Add missing fields {fields.strip()} to the {model.strip()} SQLAlchemy model and update any related DTOs."
    if missing_category == "missing_frontend_components":
        return f"Create the React component {missing_item} and integrate it into the UI workflow."
    return "No action needed."

def generate_report():
    data = load_compliance()
    compliance, demo_ready = calculate_percentages(data)
    high_cat, high_item = highest_priority_missing(data)
    next_dev = next_task(high_cat, high_item) if high_cat else "All components are compliant."
    affected_files = []
    # simplistic mapping to files based on category
    if high_cat == "missing_routes":
        affected_files.append("backend/api/routes.py")
    if high_cat == "missing_backend_methods":
        affected_files.append("backend/services/*.py")
    if high_cat == "missing_model_fields":
        affected_files.append(f"backend/storage/models/{high_item.split(':')[0].strip()}.py")
    if high_cat == "missing_frontend_components":
        affected_files.append("frontend/src/components/...js")
    report_md = f"""
# ScopeSense Architecture Compliance Report

**Current Compliance Percentage:** {compliance:.1f}%
**Demo Readiness Percentage:** {demo_ready:.1f}%
**Highest Priority Missing Component:** {high_item or 'None'}
**Exact Next Development Task:** {next_dev}
**Files Likely Affected:** {', '.join(affected_files) if affected_files else 'None'}
**Estimated Effort:** 0.5 dev‑days (implementation of the missing piece)
**Expected Improvement After Completion:** +{(100 - compliance):.1f}% compliance

Recommended Next Step
"""
    out_path = Path(__file__).resolve().parents[2] / "compliance_report.md"
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(report_md.strip())
    print(f"Report written to {out_path}")

if __name__ == "__main__":
    generate_report()
