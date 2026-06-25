# Sprint 1 Integration Implementation Plan

## Goal Description
Integrate the newly created **Hierarchy Builder**, **Jira Hierarchy Extractor**, and **Jira Worklog Rollup Service** into the existing Jira ingestion pipeline so that:
- `HierarchyNode` objects are built for every Jira issue.
- Epic → Story → Task/Sub‑task relationships are preserved end‑to‑end.
- `actual_hours` and `remaining_hours` are calculated from Jira worklogs and time‑tracking fields.
- All hierarchy information is persisted through `PlatformData` → `PlatformFetchResult`.

**Scope limitation**: No modifications to Table 1‑4 schemas, Semantic Matching, or Status Intelligence.

## User Review Required
None required; the plan is internal. The user only needs to approve before execution.

## Open Questions
1. **Persistence Mechanism** – Store hierarchy nodes as a JSON blob in the existing `platform_fetch_results` table or create a dedicated `hierarchy_nodes` table?
2. **Root ID Generation** – Use deterministic root ID (Epic key) or auto‑generated UUID for top‑level node?
3. **Missing Worklog Handling** – If an issue lacks worklogs, should `actual_hours` default to `0` and still persist the node, or omit the node?

## Proposed Changes
| Component | File (relative to repo root) | Change Type |
|-----------|------------------------------|------------|
| **Jira Ingestion Orchestrator** | `backend/integrations/jira/jira_ingestion_service.py` (or central Jira fetching service) | Insert calls to `JiraHierarchyExtractor`, `HierarchyBuilder`, and `JiraWorklogRollupService` in the required order. |
| **PlatformData Model** | `backend/models/platform_data.py` | Add `hierarchy_nodes: List[HierarchyNode]` field; ensure it is populated by the orchestrator. |
| **PlatformFetchResult Serialization** | `backend/models/platform_fetch_result.py` | Extend JSON (de)serialization to include `hierarchy_nodes`. |
| **Service Registry / DI** | `backend/services/service_registry.py` (or equivalent) | Register the three new services for dependency injection. |
| **Existing Hierarchy Services** | `backend/hierarchy/hierarchy_builder.py`<br>`backend/hierarchy/jira_hierarchy_extractor.py`<br>`backend/hierarchy/jira_worklog_rollup_service.py` | No code changes; just import and invoke. |
| **Tests** | `tests/integration/jira_ingestion_test.py` | Add tests verifying hierarchy nodes presence, Epic links, and hour calculations. |
| **Verification Script** | `backend/scripts/verify_sprint1.py` | New script to run post‑implementation audit (checks A‑D). |

## Verification Plan
1. **Automated Test Suite** – Run the new integration test; all must pass.
2. **Post‑Implementation Audit** – Execute `verify_sprint1.py` which will:
   - Pull a sample Jira project containing known Epic→Story→Task/Sub‑task relationships.
   - Confirm each `HierarchyNode` has correct `root_id`, `parent_id`, and `hierarchy_level`.
   - Validate `actual_hours` equals the sum of worklog entries and `remaining_hours` matches Jira time‑tracking fields.
   - Ensure `PlatformFetchResult` JSON payload includes the hierarchy data.
   - Run regression checks to confirm existing tables and matching logic remain unchanged.
3. **Manual Spot‑Check** – Inspect a few `PlatformFetchResult` rows in the database to verify persisted hierarchy information.

**PASS / FAIL Criteria**
- **PASS**: All verification steps succeed, no regression failures, hierarchy data correctly persisted.
- **FAIL**: Any step fails; the audit will identify the specific deficiency for remediation.

---
*Implementation may begin once you approve this plan.*

## Goal Description

Compare the current implemented ScopeSense project against the **ScopeSense Architecture Specification v1.0** (the FINAL APPROVED TARGET ARCHITECTURE). Produce a detailed compliance report covering:
- Existing reusable components
- Partially implemented pieces
- Missing elements
- Disconnected or out‑of‑sync parts between backend and frontend
- Items preventing a demo that matches the architecture

The report must include:
1. Current Compliance Percentage
2. Demo Readiness Percentage
3. Highest Priority Missing Component
4. Exact Next Development Task
5. Files Likely Affected
6. Estimated Effort
7. Expected Improvement After Completion

The answer must end with the line **"Recommended Next Step"** followed by the single most important implementation task.

---

## Approach

The assessment will be performed in three phases:

### Phase 1 – Information Gathering
1. **Read Architecture Specification** – `ARCHITECTURE.md`. Identify all required contracts, tables, APIs, UI routes, and synchronization rules.
2. **Enumerate Backend Artifacts** – List backend modules, services, API routes, models, and tasks.
3. **Enumerate Frontend Artifacts** – Scan `frontend/src` for pages, components, React contexts, API client wrappers, and navigation definitions.
4. **Collect Data Model Definitions** – Open `backend/storage/models/*` to capture the actual DB schema.
5. **Collect API Contracts** – Review `backend/api/routes.py`, DTOs, and any OpenAPI schema generation.
6. **Collect WebSocket / Real‑time Flow** – Review `backend/websocket/*` and Celery task definitions.
7. **Collect Synchronization‑Critical Files** – Files referenced in the spec that must stay in sync (e.g., Table 1‑4 DTOs, audit contracts, etc.).

### Phase 2 – Gap Analysis
For each architectural element, evaluate:
- **Exists & matches spec** – fully implemented and contract‑compatible.
- **Partial** – present but signatures, field names, or return payloads diverge.
- **Missing** – no implementation.
- **Disconnected** – backend exists but no frontend consumer (or vice‑versa).
- **Out‑of‑sync** – data models/DTOs differ from spec (extra/renamed fields, missing flags).

Document findings in a structured table.

### Phase 3 – Reporting & Recommendations
1. Calculate **Compliance Percentage** = (Number of fully compliant elements / Total required elements) * 100.
2. Calculate **Demo Readiness Percentage** – proportion of end‑to‑end flow (upload SRS → audit execution → results UI) that works without contract violations.
3. Identify the **Highest Priority Missing Component** – the element whose absence blocks the demo or violates a synchronization rule.
4. Derive the **Exact Next Development Task** – a single, concrete code change that resolves the highest‑priority gap.
5. List **Files Likely Affected** for that task.
6. Provide an **Effort Estimate** (in developer‑days) and the **Expected Improvement** (percentage lift in compliance/readiness).

---

## Open Questions (User Review Required)
- **Frontend source location** – Confirm the path to the React/Vite project (e.g., `frontend/`).
- **Data model source** – Does the project maintain separate Pydantic DTO files (e.g., `backend/api/schemas/*.py`)? If not, should we generate them for comparison?
- **Desired granularity for percentages** – Should UI‑only components count equally with backend contracts, or should each contract/table be counted as one element?

> **Please confirm the above questions or provide any missing paths.**

---

## Proposed Changes (Implementation Steps)

### 1️⃣ Information Gathering Scripts
- Add a temporary script `scripts/collect_project_snapshot.py` to programmatically list backend modules, frontend files, database models, and API routes, outputting a JSON manifest.

### 2️⃣ Gap‑Analysis Logic
- Write `scripts/analyze_compliance.py` that parses the architecture spec, loads the manifest, and produces a markdown/comma‑separated matrix of compliance status.

### 3️⃣ Reporting Generator
- Create `scripts/generate_compliance_report.py` that consumes the matrix, calculates percentages, and formats the final report per your requirements.

### 4️⃣ Validation & Unit Tests
- Add tests under `tests/` to ensure known mismatches (e.g., method name mismatches) are correctly flagged.

---

## Verification Plan
- **Automated Tests** – Run the collection and analysis scripts; assert that known gaps are flagged.
- **Manual Verification** – Inspect the generated report to ensure it aligns with observed code.

---

## Dependencies
- Python 3.10+, `pydantic`, `toml`, `pathlib`, `json` – already in `requirements.txt`.
- No external network calls are required.

---

## Timeline
| Step | Duration (dev‑days) |
|------|---------------------|
| Script creation & manifest generation | 0.5 |
| Gap‑analysis implementation | 1.0 |
| Reporting generation & formatting | 0.5 |
| Tests & verification | 0.5 |
| **Total** | **2.5 dev‑days** |

---

**Next Action** – Await your confirmation on the open questions and approval of this implementation plan.
