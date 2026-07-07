from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from pydantic import BaseModel, ConfigDict
from typing import List, Optional, Dict, Any
from datetime import datetime, date, timedelta
import os
import uuid
import shutil
import logging

from backend.auth.dependencies import has_role, get_owned_session
from backend.auth.role import Role
from backend.auth.jwt_utils import get_current_user, TokenData
from backend.storage.database import get_db
from backend.storage.models_extended import AuditSession, CalendarProfile, SRSExtractionResult, PlatformFetchResult, ModuleMatch as ModuleMatchORM, PlatformConnection
from backend.services.srs_extraction_service import SRSExtractionService
from backend.services.platform_fetch_service import PlatformFetchService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/confirm", tags=["Confirmation"])

# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class ConfirmRequest(BaseModel):
    audit_session_id: int

class CalendarConfirmRequest(ConfirmRequest):
    working_days: Optional[List[str]] = None
    hours_per_day: Optional[int] = None
    holidays: Optional[List[str]] = None
    timezone: Optional[str] = None
    workday_start: Optional[str] = None
    workday_end: Optional[str] = None

class PlannedFeatureSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")
    module: str
    requirement: str
    assigned_developer: Optional[str] = None
    planned_hours: float
    priority: Optional[str] = None

class SavePlannedRequest(BaseModel):
    audit_session_id: int
    features: List[PlannedFeatureSchema]

class PlatformCredentials(BaseModel):
    platform: str
    owner: Optional[str] = None
    repo: Optional[str] = None
    github_pat: Optional[str] = None
    project_key: Optional[str] = None
    project_name: Optional[str] = None
    jira_domain: Optional[str] = None
    jira_api_token: Optional[str] = None
    jira_email: Optional[str] = None
    jira_username: Optional[str] = None

class FetchPlatformRequest(BaseModel):
    audit_session_id: int
    credentials: PlatformCredentials
    connection_id: Optional[int] = None
    force_full_sync: bool = False

class ActualFeatureSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")
    module: str
    requirement: str
    assigned_developer: str
    actual_hours: float
    hours_remaining: Optional[float] = None
    status: str
    issue_type: Optional[str] = None
    priority: Optional[str] = None
    created_date: Optional[str] = None
    completed_date: Optional[str] = None
    hierarchy_level: Optional[str] = None
    rollup_parent_id: Optional[str] = None
    story_points: Optional[float] = None
    resolutiondate: Optional[str] = None
    duedate: Optional[str] = None
    issue_key: Optional[str] = None

class SaveActualRequest(BaseModel):
    audit_session_id: int
    features: List[ActualFeatureSchema]

class NormalizationDataSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")
    module: str
    requirement: str
    planned_hours: float
    actual_hours: float
    hours_remaining: float
    story_points: Optional[float] = None
    hierarchy_level: Optional[str] = None
    rollup_parent_id: Optional[str] = None
    issue_key: Optional[str] = None
    assigned_developer: Optional[str] = None
    status: Optional[str] = None

class SaveNormalizationRequest(BaseModel):
    audit_session_id: int
    normalization_data: List[NormalizationDataSchema]

class MatchItem(BaseModel):
    srs_node_id: int
    feature_id: int
    confidence_score: float
    approval_status: str

class SaveMatchesRequest(BaseModel):
    audit_session_id: int
    matches: List[MatchItem]

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def generate_initial_matches(db: Session, session_obj: AuditSession):
    """Dynamically generate matches using EmbeddingEngine with substring fallback."""
    srs_res = db.query(SRSExtractionResult).filter(SRSExtractionResult.id == session_obj.srs_result_id).first()
    planned_features = srs_res.extracted_json.get("features", []) if srs_res else []
    
    platform_res = db.query(PlatformFetchResult).filter(PlatformFetchResult.id == session_obj.platform_fetch_result_id).first()
    actual_features = platform_res.actual_data_json if platform_res else []
    
    if not planned_features or not actual_features:
        return
        
    from backend.semantic.embeddings import EmbeddingEngine
    import math
    
    try:
        engine = EmbeddingEngine()
    except Exception as e:
        logger.warning(f"Could not load EmbeddingEngine: {e}. Using substring matching fallback.")
        engine = None
        
    org_profile = platform_res.organization_profile_json if platform_res else {}
    platform_data_json = platform_res.platform_data_json if platform_res else {}
    platform_features = platform_data_json.get("features", []) if platform_data_json else []
    sp_anchor = org_profile.get("story_point_anchor", {}).get("value")

    actual_embeddings = []
    
    # Pre-compute lookup for Parent-Aware Embeddings
    feature_lookup = {act.get('issue_key'): act.get('requirement', '') for act in actual_features if act.get('issue_key')}
    
    if engine:
        for idx, act in enumerate(actual_features):
            module_text = act.get('module', '')
            
            # Parent-Aware Semantic Matching
            if module_text == "Unmapped Work Item" and act.get("rollup_parent_id"):
                parent_title = feature_lookup.get(act.get("rollup_parent_id"), "")
                if parent_title:
                    module_text = parent_title
                    
            text = f"{module_text} {act.get('requirement', '')}"
            
            # JUIL: Matching Enrichment
            if sp_anchor and idx < len(platform_features):
                pf = platform_features[idx]
                issue_type = pf.get("platform_specific", {}).get("issue_type")
                if issue_type and issue_type == sp_anchor:
                    # Boost semantic weight by embedding the anchor issue_type explicitly
                    text += f" {issue_type}"

            try:
                emb = engine.generate_embedding(text)
                actual_embeddings.append((idx, emb))
            except Exception:
                actual_embeddings.append((idx, None))
                
    for s_idx, plan in enumerate(planned_features):
        plan_text = f"{plan.get('module', '')} {plan.get('requirement', '')}"
        best_score = 0.0
        best_act_idx = -1
        
        if engine:
            try:
                plan_emb = engine.generate_embedding(plan_text)
                for a_idx, act_emb in actual_embeddings:
                    if act_emb:
                        # Cosine similarity
                        dot = sum(a * b for a, b in zip(plan_emb, act_emb))
                        norm1 = math.sqrt(sum(a*a for a in plan_emb))
                        norm2 = math.sqrt(sum(b*b for b in act_emb))
                        score = dot / (norm1 * norm2) if norm1 > 0 and norm2 > 0 else 0.0
                        if score > best_score:
                            best_score = score
                            best_act_idx = a_idx
            except Exception as e:
                logger.error(f"Error computing embedding similarity: {e}")
                
        # Exact Substring Override (if semantic engine gets distracted by a mediocre match)
        if best_score < 0.85 or best_act_idx == -1:
            plan_req = plan.get('requirement', '').lower().strip()
            if plan_req and len(plan_req) > 3:
                for a_idx, act in enumerate(actual_features):
                    act_req = act.get('requirement', '').lower().strip()
                    if act_req and (plan_req in act_req or act_req in plan_req):
                        best_score = 0.85
                        best_act_idx = a_idx
                        break
                    
        if best_act_idx != -1:
            match_orm = ModuleMatchORM(
                audit_session_id=session_obj.id,
                srs_node_id=s_idx,
                feature_id=best_act_idx,
                confidence_score=float(best_score),
                approval_status="APPROVED" if best_score >= 0.75 else "PENDING_REVIEW"
            )
            db.add(match_orm)
            
    db.commit()

def merge_normalized_data(db: Session, session_obj: AuditSession) -> List[Dict[str, Any]]:
    """Merge planned features and actual features based on approved matches."""
    srs_res = db.query(SRSExtractionResult).filter(SRSExtractionResult.id == session_obj.srs_result_id).first()
    planned_features = srs_res.extracted_json.get("features", []) if srs_res else []
    
    platform_res = db.query(PlatformFetchResult).filter(PlatformFetchResult.id == session_obj.platform_fetch_result_id).first()
    actual_features = platform_res.actual_data_json if platform_res else []
    
    matches = db.query(ModuleMatchORM).filter(
        ModuleMatchORM.audit_session_id == session_obj.id,
        ModuleMatchORM.approval_status != 'REJECTED'
    ).all()
    
    # 1. Map 1-to-1 best matches first
    # If a feature_id matched multiple SRS requirements, only keep the match with highest confidence score
    best_matches = {}
    for m in matches:
        if m.feature_id >= 0:
            if m.feature_id not in best_matches or (m.confidence_score or 0.0) > (best_matches[m.feature_id].confidence_score or 0.0):
                best_matches[m.feature_id] = m

    plan_to_act_list = {}
    act_to_plan = {}
    for m in best_matches.values():
        if m.srs_node_id not in plan_to_act_list:
            plan_to_act_list[m.srs_node_id] = []
        plan_to_act_list[m.srs_node_id].append(m.feature_id)
        act_to_plan[m.feature_id] = m.srs_node_id

    # 2. Subtask Rollup Phase (only roll up unmapped child tasks!)
    subtask_hours = {}
    subtasks_to_remove = set()
    for act_idx, act in enumerate(actual_features):
        if act.get("rollup_parent_id"):
            if act_idx not in act_to_plan:
                parent_id = act.get("rollup_parent_id")
                subtask_hours[parent_id] = subtask_hours.get(parent_id, 0.0) + float(act.get("actual_hours") or 0.0)
                subtasks_to_remove.add(act.get("issue_key"))
            
    # 2.5 Build Implicit Identity Map
    implicit_identity_map = dict(session_obj.identity_resolution_json or {})
    for plan_idx, act_idxs in plan_to_act_list.items():
        if plan_idx < len(planned_features):
            plan_dev = planned_features[plan_idx].get("assigned_developer")
            if plan_dev and plan_dev != "Unassigned":
                for act_idx in act_idxs:
                    if 0 <= act_idx < len(actual_features):
                        act_dev = actual_features[act_idx].get("assigned_developer")
                        if act_dev and act_dev != "Unassigned":
                            implicit_identity_map[plan_dev] = act_dev
                            break
            
    merged = []
    
    # 3. Merge Mapped Data
    for idx, plan in enumerate(planned_features):
        act_idxs = plan_to_act_list.get(idx, [])
        if act_idxs:
            total_actual = 0.0
            last_act_module = "General"
            last_act_hierarchy = None
            last_act_issue_key = None
            last_act_developer = None
            last_act_status = None
            
            for act_idx in act_idxs:
                if 0 <= act_idx < len(actual_features):
                    act = actual_features[act_idx]
                    issue_key = act.get("issue_key")
                    
                    if issue_key in subtasks_to_remove:
                        continue # Skip direct counting, it's rolled up!
                        
                    base_actual = float(act.get("actual_hours") or 0.0)
                    rolled_up = subtask_hours.get(issue_key, 0.0)
                    total_actual += (base_actual + rolled_up)
                    
                    last_act_module = act.get("module") or last_act_module
                    last_act_hierarchy = act.get("hierarchy_level")
                    last_act_issue_key = act.get("issue_key")
                    last_act_developer = act.get("assigned_developer") or last_act_developer
                    last_act_status = act.get("status") or last_act_status
            
            planned_hours = float(plan.get("planned_hours") or 0.0)
            plan_dev = plan.get("assigned_developer")
            mapped_dev = implicit_identity_map.get(plan_dev, plan_dev)
            
            merged.append({
                "module": plan.get("module") or last_act_module,
                "requirement": plan.get("requirement"),
                "planned_hours": planned_hours,
                "actual_hours": total_actual,
                "hours_remaining": planned_hours - total_actual,
                "hierarchy_level": last_act_hierarchy,
                "rollup_parent_id": None,
                "story_points": None,
                "issue_key": last_act_issue_key,
                "assigned_developer": last_act_developer or mapped_dev,
                "status": last_act_status or plan.get("status"),
            })
        else:
            planned_hours = float(plan.get("planned_hours") or 0.0)
            plan_dev = plan.get("assigned_developer")
            mapped_dev = implicit_identity_map.get(plan_dev, plan_dev)
            
            merged.append({
                "module": plan.get("module") or "General",
                "requirement": plan.get("requirement"),
                "planned_hours": planned_hours,
                "actual_hours": 0.0,
                "hours_remaining": planned_hours,
                "assigned_developer": mapped_dev,
                "status": plan.get("status"),
            })
            
    # 4. Merge Unmapped (Drift) Data
    for idx, act in enumerate(actual_features):
        issue_key = act.get("issue_key")
        
        # Completely hide subtasks from the drift table!
        if issue_key in subtasks_to_remove:
            continue
            
        if idx not in act_to_plan:
            base_actual = float(act.get("actual_hours") or 0.0)
            rolled_up = subtask_hours.get(issue_key, 0.0)
            total_actual = base_actual + rolled_up
            
            merged.append({
                "module": act.get("module") or "General",
                "requirement": "[Drift] " + (act.get("requirement") or act.get("name") or f"Actual {idx + 1}"),
                "planned_hours": 0.0,
                "actual_hours": total_actual,
                "hours_remaining": -total_actual,
                "hierarchy_level": act.get("hierarchy_level"),
                "rollup_parent_id": act.get("rollup_parent_id"),
                "story_points": act.get("story_points"),
                "issue_key": act.get("issue_key"),
                "assigned_developer": act.get("assigned_developer"),
                "status": act.get("status"),
            })
            
    return merged

# ============================================================================
# ENDPOINTS
# ============================================================================

@router.post("/srs/upload")
async def upload_srs(
    audit_session_id: int = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user = Depends(has_role(Role.MANAGER))
):
    """Upload SRS file, extract features immediately, and save to DB."""
    session_obj = get_owned_session(audit_session_id, db=db, current_user=user)
    if not session_obj:
        raise HTTPException(status_code=404, detail="Audit session not found")
        
    uploads_dir = os.getenv("UPLOADS_DIR", "/app/data/uploads")
    os.makedirs(uploads_dir, exist_ok=True)
    
    filename = f"srs_{uuid.uuid4().hex}_{file.filename}"
    file_path = os.path.join(uploads_dir, filename)
    
    with open(file_path, "wb") as f:
        shutil.copyfileobj(file.file, f)
        
    try:
        service = SRSExtractionService()
        srs_entry = service.extract_and_store(file_path)
        
        session_obj.srs_result_id = srs_entry.id
        session_obj.planned_data_approved = False
        db.commit()
        
        return srs_entry.extracted_json
    except Exception as e:
        logger.error(f"SRS Ingestion error: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/session/{session_id}/srs-data")
def get_srs_data(session_id: int, db: Session = Depends(get_db), user = Depends(has_role(Role.MANAGER))):
    """Retrieve planned data from the database."""
    session_obj = get_owned_session(session_id, db=db, current_user=user)
    if not session_obj:
        raise HTTPException(status_code=404, detail="Audit session not found")
    if not session_obj.srs_result_id:
        return {"features": []}
    srs_res = db.query(SRSExtractionResult).filter(SRSExtractionResult.id == session_obj.srs_result_id).first()
    if not srs_res:
        return {"features": []}
    return srs_res.extracted_json

@router.post("/planned/save")
def save_planned_features(request: SavePlannedRequest, db: Session = Depends(get_db), user = Depends(has_role(Role.MANAGER))):
    """Approve/Edit Table 1 planned data."""
    session_obj = get_owned_session(request.audit_session_id, db=db, current_user=user)
    if not session_obj:
        raise HTTPException(status_code=404, detail="Audit session not found")
    if not session_obj.srs_result_id:
        raise HTTPException(status_code=400, detail="No SRS extraction result linked to this session")
        
    srs_res = db.query(SRSExtractionResult).filter(SRSExtractionResult.id == session_obj.srs_result_id).first()
    if not srs_res:
        raise HTTPException(status_code=404, detail="SRS extraction result record not found")
        
    extracted_json = dict(srs_res.extracted_json)
    extracted_json["features"] = [f.model_dump() for f in request.features]
    srs_res.extracted_json = extracted_json
    
    session_obj.planned_data_approved = True
    db.commit()
    return {"status": "saved", "planned_data_approved": True}

@router.get("/integrations/connections")
def get_connections(db: Session = Depends(get_db)):
    """Get saved platform credentials (without secrets)."""
    conns = db.query(PlatformConnection).all()
    results = []
    for c in conns:
        safe_creds = c.credentials_json.copy()
        # mask sensitive tokens
        if "github_pat" in safe_creds and safe_creds["github_pat"]:
            safe_creds["github_pat"] = "********"
        if "jira_api_token" in safe_creds and safe_creds["jira_api_token"]:
            safe_creds["jira_api_token"] = "********"
            
        results.append({
            "id": c.id,
            "platform": c.platform,
            "credentials": safe_creds
        })
    return {"connections": results}

@router.get("/integrations/jira/projects/{conn_id}")
def fetch_jira_projects(conn_id: int, db: Session = Depends(get_db)):
    """Fetch Jira projects using stored credentials."""
    conn = db.query(PlatformConnection).filter(PlatformConnection.id == conn_id).first()
    if not conn or conn.platform.lower() != "jira":
        raise HTTPException(status_code=404, detail="Jira connection not found")
        
    creds = conn.credentials_json
    domain = creds.get("jira_domain")
    api_token = creds.get("jira_api_token")
    email = creds.get("jira_email")
    username = creds.get("jira_username")
    
    if not domain or not api_token:
        raise HTTPException(status_code=400, detail="Incomplete Jira credentials")
        
    from backend.integrations.jira.jira_client import JiraClient
    try:
        client = JiraClient(domain=domain, api_token=api_token, email=email, username=username)
        projects = client.get_projects()
        
        return {"projects": [{"key": p.get("key"), "name": p.get("name")} for p in projects]}
    except Exception as e:
        logger.error(f"Failed to fetch Jira projects: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch Jira projects: {e}")

@router.get("/integrations/github/repos/{conn_id}")
def fetch_github_repos(conn_id: int, db: Session = Depends(get_db)):
    """Fetch GitHub repositories using stored PAT."""
    conn = db.query(PlatformConnection).filter(PlatformConnection.id == conn_id).first()
    if not conn or conn.platform.lower() != "github":
        raise HTTPException(status_code=404, detail="GitHub connection not found")
        
    creds = conn.credentials_json
    token = creds.get("github_pat")
    
    if not token:
        raise HTTPException(status_code=400, detail="Missing GitHub token")
        
    import requests
    try:
        response = requests.get(
            "https://api.github.com/user/repos",
            headers={"Authorization": f"Bearer {token}", "Accept": "application/vnd.github.v3+json"},
            params={"per_page": 100, "sort": "updated"}
        )
        response.raise_for_status()
        repos = response.json()
        
        return {"repos": [{"full_name": r.get("full_name"), "name": r.get("name")} for r in repos]}
    except Exception as e:
        logger.error(f"Failed to fetch GitHub repos: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch GitHub repositories: {e}")

@router.post("/integrations/connections/clone")
def clone_connection(payload: dict, db: Session = Depends(get_db)):
    """Clone an existing connection and change the project target."""
    base_id = payload.get("smart_base_id")
    platform = payload.get("platform")
    
    base_conn = db.query(PlatformConnection).filter(PlatformConnection.id == base_id).first()
    if not base_conn:
        raise HTTPException(status_code=404, detail="Base connection not found")
        
    new_creds = base_conn.credentials_json.copy()
    
    if platform == "jira":
        new_creds["project_key"] = payload.get("project_key")
        new_creds["project_name"] = payload.get("project_name")
    elif platform == "github":
        new_creds["owner"] = payload.get("owner")
        new_creds["repo"] = payload.get("repo")
        new_creds["project_name"] = payload.get("project_name")
        
    # Check duplicate
    existing = db.query(PlatformConnection).filter(PlatformConnection.platform == platform).all()
    for e in existing:
        if platform == "jira" and e.credentials_json.get("jira_domain") == new_creds.get("jira_domain") and e.credentials_json.get("project_key") == new_creds.get("project_key"):
            return {"status": "success", "message": "Connection already exists"}
        if platform == "github" and e.credentials_json.get("owner") == new_creds.get("owner") and e.credentials_json.get("repo") == new_creds.get("repo"):
            return {"status": "success", "message": "Connection already exists"}
            
    conn = PlatformConnection(platform=platform)
    conn.credentials_json = new_creds
    db.add(conn)
    db.commit()
    return {"status": "success"}

@router.post("/integrations/connections")
def save_connection(creds: PlatformCredentials, db: Session = Depends(get_db)):
    platform = creds.platform.lower()
    if platform not in ["jira", "github"]:
        raise HTTPException(status_code=400, detail="Invalid platform")
        
    new_creds_dump = creds.model_dump()
    
    # Check for exact duplicates
    existing = db.query(PlatformConnection).filter(PlatformConnection.platform == platform).all()
    for e in existing:
        if platform == "jira" and e.credentials_json.get("jira_domain") == new_creds_dump.get("jira_domain") and e.credentials_json.get("project_key") == new_creds_dump.get("project_key"):
            return {"status": "success", "message": "Jira credentials already exist"}
        if platform == "github" and e.credentials_json.get("owner") == new_creds_dump.get("owner") and e.credentials_json.get("repo") == new_creds_dump.get("repo"):
            return {"status": "success", "message": "GitHub credentials already exist"}
            
    conn = PlatformConnection(platform=platform)
    conn.credentials_json = new_creds_dump
    db.add(conn)
    db.commit()
    return {"status": "success", "message": f"{platform.capitalize()} credentials saved"}

@router.delete("/integrations/connections/{conn_id}")
def delete_connection(conn_id: int, db: Session = Depends(get_db), user = Depends(has_role(Role.MANAGER))):
    conn = db.query(PlatformConnection).filter(PlatformConnection.id == conn_id).first()
    if not conn:
        raise HTTPException(status_code=404, detail="Connection not found")
    db.delete(conn)
    db.commit()
    return {"status": "success", "message": "Connection deleted"}

@router.post("/actual/fetch")
def fetch_platform_data(request: FetchPlatformRequest, db: Session = Depends(get_db), user = Depends(has_role(Role.MANAGER))):
    """Fetch raw platform data, canonicalize immediately, and save to DB."""
    session_obj = get_owned_session(request.audit_session_id, db=db, current_user=user)
    if not session_obj:
        raise HTTPException(status_code=404, detail="Audit session not found")
        
    creds = request.credentials
    platform = creds.platform.lower() if creds and creds.platform else None
    
    # Try fetching from DB if credentials are missing
    if not platform:
        # Fallback to Jira for demo purposes if not specified
        platform = "jira"
        
    conn = None
    if request.connection_id:
        conn = db.query(PlatformConnection).filter(PlatformConnection.id == request.connection_id).first()
    else:
        conn = db.query(PlatformConnection).filter(PlatformConnection.platform == platform).first()
        
    if conn:
        # Override request credentials with saved credentials
        saved_creds = conn.credentials_json
        creds = PlatformCredentials(**saved_creds)
    elif not creds:
        raise HTTPException(status_code=400, detail=f"No saved credentials for {platform}")

    service = PlatformFetchService()
    try:
        if creds.platform.lower() == "github":
            if not creds.owner or not creds.repo or not creds.github_pat:
                raise HTTPException(status_code=400, detail="Missing GitHub owner, repo or token")
            fetch_entry, _ = service.fetch_github(creds.owner, creds.repo, creds.github_pat)
        elif creds.platform.lower() == "jira":
            if not creds.project_key or not creds.jira_domain or not creds.jira_api_token:
                raise HTTPException(status_code=400, detail="Missing JIRA domain, project key or token")
            fetch_entry, _ = service.fetch_jira(
                creds.project_key, creds.jira_domain, creds.jira_api_token, 
                email=creds.jira_email, username=creds.jira_username,
                force_full_sync=request.force_full_sync
            )
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported platform: {creds.platform}")
            
        session_obj.platform_fetch_result_id = fetch_entry.id
        session_obj.platform_type = creds.platform
        session_obj.actual_data_approved = False
        db.commit()
        
        return {"features": fetch_entry.actual_data_json}
    except Exception as e:
        logger.error(f"Platform connection/fetch error: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/session/{session_id}/platform-data")
def get_platform_data(session_id: int, db: Session = Depends(get_db), user = Depends(has_role(Role.MANAGER))):
    """Retrieve actual data from the database."""
    session_obj = get_owned_session(session_id, db=db, current_user=user)
    if not session_obj:
        raise HTTPException(status_code=404, detail="Audit session not found")
    if not session_obj.platform_fetch_result_id:
        return {"features": []}
    platform_res = db.query(PlatformFetchResult).filter(PlatformFetchResult.id == session_obj.platform_fetch_result_id).first()
    if not platform_res:
        return {"features": []}
    return {"features": platform_res.actual_data_json or []}

@router.post("/actual/save")
def save_actual_features(request: SaveActualRequest, db: Session = Depends(get_db), user = Depends(has_role(Role.MANAGER))):
    """Approve/Edit Table 2 actual data."""
    session_obj = get_owned_session(request.audit_session_id, db=db, current_user=user)
    if not session_obj:
        raise HTTPException(status_code=404, detail="Audit session not found")
    if not session_obj.platform_fetch_result_id:
        raise HTTPException(status_code=400, detail="No platform data linked to this session")
    if not session_obj.planned_data_approved:
        raise HTTPException(status_code=403, detail="Planned data must be approved first")
        
    platform_res = db.query(PlatformFetchResult).filter(PlatformFetchResult.id == session_obj.platform_fetch_result_id).first()
    if not platform_res:
        raise HTTPException(status_code=404, detail="Platform fetch result record not found")
        
    platform_res.actual_data_json = [f.model_dump() for f in request.features]
    session_obj.actual_data_approved = True
    db.commit()
    return {"status": "saved", "actual_data_approved": True}

@router.post("/calendar/preview")
def preview_calendar(request: CalendarConfirmRequest, db: Session = Depends(get_db), user = Depends(has_role(Role.MANAGER))):
    """Compute and preview capacity metrics based on custom schedule rules."""
    session_obj = get_owned_session(request.audit_session_id, db=db, current_user=user)
    if not session_obj:
        raise HTTPException(status_code=404, detail="Audit session not found")
        
    working_day_names = request.working_days or ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
    hours_per_day = request.hours_per_day or 8
    holidays_raw = request.holidays or []
    
    from backend.analysis.semantic_delay_analyzer import SemanticDelayAnalyzer
    
    working_day_indexes = {
        SemanticDelayAnalyzer._weekday_to_index(day)
        for day in working_day_names
        if SemanticDelayAnalyzer._weekday_to_index(day) is not None
    }
    if not working_day_indexes:
        working_day_indexes = {0, 1, 2, 3, 4}
        
    holidays = set()
    for h in holidays_raw:
        parsed = SemanticDelayAnalyzer._parse_holiday(h)
        if parsed:
            holidays.add(parsed)
            
    # Standard 30-day projection from today
    total_days = 30
    start_date = date.today()
    end_date = start_date + timedelta(days=total_days - 1)
    
    working_days_count = 0
    holiday_impact_days = 0
    current = start_date
    while current <= end_date:
        if current.weekday() in working_day_indexes:
            if current in holidays:
                holiday_impact_days += 1
            else:
                working_days_count += 1
        current += timedelta(days=1)
        
    available_capacity = (working_days_count + holiday_impact_days) * hours_per_day
    holiday_impact = holiday_impact_days * hours_per_day
    effective_capacity = working_days_count * hours_per_day
    
    return {
        "total_working_days": working_days_count,
        "available_capacity": available_capacity,
        "effective_capacity": effective_capacity,
        "holiday_impact": holiday_impact,
        "holiday_count": holiday_impact_days
    }

@router.get("/session/{session_id}/normalization-data")
def get_normalization_data(session_id: int, db: Session = Depends(get_db), user = Depends(has_role(Role.MANAGER))):
    """Retrieve merged planned & actual dataset based on approved matches."""
    session_obj = get_owned_session(session_id, db=db, current_user=user)
    if not session_obj:
        raise HTTPException(status_code=404, detail="Audit session not found")
    
    if session_obj.normalized_data_json and len(session_obj.normalized_data_json) > 0:
        return {"normalization_data": session_obj.normalized_data_json}
    
    # Check if matches exist, generate them if not
    matches = db.query(ModuleMatchORM).filter(ModuleMatchORM.audit_session_id == session_id).all()
    if not matches:
        generate_initial_matches(db, session_obj)
        
    merged = merge_normalized_data(db, session_obj)
    return {"normalization_data": merged}

@router.post("/normalization/save")
def save_normalization_data(request: SaveNormalizationRequest, db: Session = Depends(get_db), user = Depends(has_role(Role.MANAGER))):
    """Approve Table 3 merged dataset."""
    session_obj = get_owned_session(request.audit_session_id, db=db, current_user=user)
    if not session_obj:
        raise HTTPException(status_code=404, detail="Audit session not found")
        
    if not session_obj.planned_data_approved or not session_obj.actual_data_approved or not session_obj.capacity_approved:
        raise HTTPException(status_code=403, detail="Previous steps must be approved first")
        
    session_obj.normalized_data_json = [n.model_dump() for n in request.normalization_data]
    session_obj.normalized_data_approved = True
    db.commit()
    return {"status": "saved", "normalized_data_approved": True}

@router.get("/session/{session_id}/matches")
def get_matches(session_id: int, db: Session = Depends(get_db), user = Depends(has_role(Role.MANAGER))):
    """Retrieve semantic matches and generate if none exist."""
    session_obj = get_owned_session(session_id, db=db, current_user=user)
    if not session_obj:
        raise HTTPException(status_code=404, detail="Audit session not found")
        
    matches = db.query(ModuleMatchORM).filter(ModuleMatchORM.audit_session_id == session_id).all()
    if not matches:
        generate_initial_matches(db, session_obj)
        matches = db.query(ModuleMatchORM).filter(ModuleMatchORM.audit_session_id == session_id).all()
        
    srs_res = db.query(SRSExtractionResult).filter(SRSExtractionResult.id == session_obj.srs_result_id).first()
    planned_features = srs_res.extracted_json.get("features", []) if srs_res else []
    
    platform_res = db.query(PlatformFetchResult).filter(PlatformFetchResult.id == session_obj.platform_fetch_result_id).first()
    actual_features = platform_res.actual_data_json if platform_res else []
    
    result = []
    for m in matches:
        plan_feat = planned_features[m.srs_node_id] if 0 <= m.srs_node_id < len(planned_features) else {}
        act_feat = actual_features[m.feature_id] if 0 <= m.feature_id < len(actual_features) else {}
        
        result.append({
            "id": m.id,
            "srs_node_id": m.srs_node_id,
            "feature_id": m.feature_id,
            "module": plan_feat.get("module") or act_feat.get("module") or "General",
            "requirement": plan_feat.get("requirement") or "Unmatched",
            "matched_story": act_feat.get("requirement") or act_feat.get("name") or "Unmatched",
            "confidence_score": m.confidence_score,
            "approval_status": m.approval_status,
            "planned_hours": plan_feat.get("planned_hours", 0.0),
            "actual_hours": act_feat.get("actual_hours", 0.0),
            "assigned_developer": act_feat.get("assigned_developer") or plan_feat.get("assigned_developer") or "Unassigned"
        })
    return {"matches": result}

@router.post("/matches/approve/{match_id}")
def approve_match(match_id: int, db: Session = Depends(get_db), user = Depends(has_role(Role.MANAGER))):
    """Approve a semantic match."""
    mm = db.query(ModuleMatchORM).filter(ModuleMatchORM.id == match_id).first()
    if not mm:
        raise HTTPException(status_code=404, detail="Match record not found")
        
    mm.approval_status = "APPROVED"
    mm.approval_timestamp = datetime.utcnow()
    db.commit()
    return {"status": "approved", "match_id": match_id}

@router.post("/matches/reject/{match_id}")
def reject_match(match_id: int, db: Session = Depends(get_db), user = Depends(has_role(Role.MANAGER))):
    """Reject a semantic match."""
    mm = db.query(ModuleMatchORM).filter(ModuleMatchORM.id == match_id).first()
    if not mm:
        raise HTTPException(status_code=404, detail="Match record not found")
        
    mm.approval_status = "REJECTED"
    mm.approval_timestamp = datetime.utcnow()
    db.commit()
    return {"status": "rejected", "match_id": match_id}

@router.post("/matches/save")
def save_matches_checklist(request: SaveMatchesRequest, db: Session = Depends(get_db), user = Depends(has_role(Role.MANAGER))):
    """Save/update entire matches checklist and approve matches step."""
    session_obj = get_owned_session(request.audit_session_id, db=db, current_user=user)
    if not session_obj:
        raise HTTPException(status_code=404, detail="Audit session not found")
        
    if not session_obj.normalized_data_approved:
        raise HTTPException(status_code=403, detail="Normalized data must be approved first")
        
    for item in request.matches:
        # Check if match already exists for this srs_node_id in this session
        mm = db.query(ModuleMatchORM).filter(
            ModuleMatchORM.audit_session_id == request.audit_session_id,
            ModuleMatchORM.srs_node_id == item.srs_node_id
        ).first()
        
        if mm:
            mm.feature_id = item.feature_id
            mm.approval_status = item.approval_status
            mm.confidence_score = item.confidence_score
            mm.approval_timestamp = datetime.utcnow()
        else:
            mm = ModuleMatchORM(
                audit_session_id=request.audit_session_id,
                srs_node_id=item.srs_node_id,
                feature_id=item.feature_id,
                confidence_score=item.confidence_score,
                approval_status=item.approval_status,
                approval_timestamp=datetime.utcnow()
            )
            db.add(mm)
            
    session_obj.matches_approved = True
    db.commit()
    return {"status": "saved", "matches_approved": True}

@router.post("/srs", response_model=dict)
def confirm_srs(request: ConfirmRequest, db: Session = Depends(get_db), user = Depends(has_role(Role.MANAGER))):
    """Mark the SRS as confirmed for the given audit session."""
    session_obj = get_owned_session(request.audit_session_id, db=db, current_user=user)
    if not session_obj:
        raise HTTPException(status_code=404, detail="Audit session not found")
    session_obj.srs_confirmed = True
    session_obj.planned_data_approved = True
    db.commit()
    return {"status": "srs_confirmed", "audit_session_id": request.audit_session_id}

@router.post("/platform", response_model=dict)
def confirm_platform(request: ConfirmRequest, db: Session = Depends(get_db), user = Depends(has_role(Role.MANAGER))):
    """Mark the platform data as confirmed for the given audit session."""
    session_obj = get_owned_session(request.audit_session_id, db=db, current_user=user)
    if not session_obj:
        raise HTTPException(status_code=404, detail="Audit session not found")
    session_obj.platform_confirmed = True
    session_obj.actual_data_approved = True
    db.commit()
    return {"status": "platform_confirmed", "audit_session_id": request.audit_session_id}

@router.post("/calendar", response_model=dict)
def confirm_calendar(request: CalendarConfirmRequest, db: Session = Depends(get_db), user = Depends(has_role(Role.MANAGER))):
    """Mark the calendar configuration as confirmed for the given audit session."""
    session_obj = get_owned_session(request.audit_session_id, db=db, current_user=user)
    if not session_obj:
        raise HTTPException(status_code=404, detail="Audit session not found")
    profile = db.query(CalendarProfile).filter(CalendarProfile.id == session_obj.calendar_profile_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Calendar profile not found")
    if request.working_days is not None:
        profile.working_days = request.working_days
    if request.hours_per_day is not None:
        if request.hours_per_day < 1 or request.hours_per_day > 24:
            raise HTTPException(status_code=400, detail="hours_per_day must be between 1 and 24")
        profile.hours_per_day = request.hours_per_day
    if request.holidays is not None:
        profile.holidays = request.holidays
    if request.timezone is not None:
        profile.timezone = request.timezone
    if request.workday_start is not None:
        profile.workday_start = request.workday_start
    if request.workday_end is not None:
        profile.workday_end = request.workday_end
    session_obj.calendar_confirmed = True
    session_obj.capacity_approved = True
    db.commit()
    return {
        "status": "calendar_confirmed",
        "audit_session_id": request.audit_session_id,
        "calendar_profile": {
            "working_days": profile.working_days,
            "hours_per_day": profile.hours_per_day,
            "holidays": profile.holidays,
            "timezone": profile.timezone,
            "workday_start": profile.workday_start,
            "workday_end": profile.workday_end,
        }
    }

@router.get("/session/active", response_model=dict)
def get_active_session(db: Session = Depends(get_db), user: TokenData = Depends(get_current_user)):
    # Find active session for user
    session_obj = db.query(AuditSession).filter(
        AuditSession.user_id == user.user_id,
        AuditSession.status.in_(["IN_PROGRESS", "COMPLETED"])
    ).order_by(AuditSession.id.desc()).first()

    if not session_obj:
        # Create default CalendarProfile if none exists
        profile = db.query(CalendarProfile).filter(CalendarProfile.user_id == user.user_id).first()
        if not profile:
            profile = CalendarProfile(
                user_id=user.user_id,
                workday_start="09:00",
                workday_end="17:00",
                working_days=["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
                hours_per_day=8,
                holidays=[],
                timezone="UTC"
            )
            db.add(profile)
            db.commit()
            db.refresh(profile)

        # Create default AuditSession
        session_obj = AuditSession(
            user_id=user.user_id,
            platform_type="github",
            srs_result_id=0,
            platform_fetch_result_id=0,
            calendar_profile_id=profile.id,
            srs_confirmed=False,
            platform_confirmed=False,
            calendar_confirmed=False,
            status="IN_PROGRESS"
        )
        db.add(session_obj)
        db.commit()
        db.refresh(session_obj)

    return {
        "id": session_obj.id,
        "user_id": session_obj.user_id,
        "platform_type": session_obj.platform_type,
        "srs_confirmed": session_obj.srs_confirmed,
        "platform_confirmed": session_obj.platform_confirmed,
        "calendar_confirmed": session_obj.calendar_confirmed,
        "planned_data_approved": session_obj.planned_data_approved,
        "actual_data_approved": session_obj.actual_data_approved,
        "capacity_approved": session_obj.capacity_approved,
        "normalized_data_approved": session_obj.normalized_data_approved,
        "matches_approved": session_obj.matches_approved,
        "status": session_obj.status,
        "progress_percent": session_obj.progress_percent,
        "stage": session_obj.stage,
        "calendar_profile": {
            "working_days": session_obj.calendar_profile.working_days,
            "hours_per_day": session_obj.calendar_profile.hours_per_day,
            "holidays": session_obj.calendar_profile.holidays,
            "timezone": session_obj.calendar_profile.timezone,
            "workday_start": session_obj.calendar_profile.workday_start,
            "workday_end": session_obj.calendar_profile.workday_end,
        }
    }

@router.post("/session/start", response_model=dict)
def start_new_session(db: Session = Depends(get_db), user: TokenData = Depends(get_current_user)):
    # Mark old sessions as CANCELLED
    db.query(AuditSession).filter(
        AuditSession.user_id == user.user_id,
        AuditSession.status == "IN_PROGRESS"
    ).update({"status": "CANCELLED"})

    # Create new CalendarProfile if none exists
    profile = db.query(CalendarProfile).filter(CalendarProfile.user_id == user.user_id).first()
    if not profile:
        profile = CalendarProfile(
            user_id=user.user_id,
            workday_start="09:00",
            workday_end="17:00",
            working_days=["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
            hours_per_day=8,
            holidays=[],
            timezone="UTC"
        )
        db.add(profile)
        db.commit()
        db.refresh(profile)

    session_obj = AuditSession(
        user_id=user.user_id,
        platform_type="github",
        srs_result_id=0,
        platform_fetch_result_id=0,
        calendar_profile_id=profile.id,
        srs_confirmed=False,
        platform_confirmed=False,
        calendar_confirmed=False,
        status="IN_PROGRESS"
    )
    db.add(session_obj)
    db.commit()
    db.refresh(session_obj)

    return {
        "id": session_obj.id,
        "user_id": session_obj.user_id,
        "platform_type": session_obj.platform_type,
        "srs_confirmed": session_obj.srs_confirmed,
        "platform_confirmed": session_obj.platform_confirmed,
        "calendar_confirmed": session_obj.calendar_confirmed,
        "planned_data_approved": session_obj.planned_data_approved,
        "actual_data_approved": session_obj.actual_data_approved,
        "capacity_approved": session_obj.capacity_approved,
        "normalized_data_approved": session_obj.normalized_data_approved,
        "matches_approved": session_obj.matches_approved,
        "status": session_obj.status,
        "progress_percent": session_obj.progress_percent,
        "stage": session_obj.stage,
        "calendar_profile": {
            "working_days": profile.working_days,
            "hours_per_day": profile.hours_per_day,
            "holidays": profile.holidays,
            "timezone": profile.timezone,
            "workday_start": profile.workday_start,
            "workday_end": profile.workday_end,
        }
    }
