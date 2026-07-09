"""
API routes for multi-platform delay analysis.
Handles GitHub and JIRA integration with semantic analysis.
"""

from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Depends, Query
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging
from backend.storage.database import get_db
from sqlalchemy.orm import Session
from backend.auth.jwt_utils import get_current_user, TokenData

from backend.integrations.github.github_adapter import GitHubAdapter
from backend.integrations.jira.jira_adapter import JiraAdapter
from backend.analysis.semantic_delay_analyzer import SemanticDelayAnalyzer, InsufficientDataError
from backend.analysis.faq_generator import FAQGenerator
from backend.srs.parser import SRSParser
from backend.srs.extractor import SRSFeatureExtractor
from backend.storage.models_extended import AuditSession, AuditResult, FAQRecord

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/delay-analysis", tags=["Delay Analysis"])
from backend.tasks.audit_tasks import execute_delay_analysis_task

import redis
import pickle
import os


redis_client = None
try:
    redis_client = redis.Redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379/0"))
    # Test connection
    redis_client.ping()
except Exception as e:
    logger.warning(f"Failed to connect to Redis: {e}. Falling back to in-memory session cache.")
    redis_client = None

def get_session(session_id: str) -> dict:
    """Retrieve session data with Redis first, then DB fallback.
    Returns a dict or None if not found.
    """
    # Try Redis cache
    if redis_client:
        try:
            raw = redis_client.get(f"session:{session_id}")
            if raw:
                return pickle.loads(raw)
        except Exception as e:
            logger.error(f"Redis get failed: {e}")
    # Fallback to DB
    from backend.storage.database import SessionLocal
    from backend.storage.models_extended import AuditResult, FindingRecord, FAQRecord, AuditSession, PlatformFetchResult, SRSExtractionResult
    db = SessionLocal()
    try:
        audit_session_id = None
        try:
            audit_session_id = int(session_id)
        except ValueError:
            p_key = session_id.split(":")[-1] if ":" in session_id else session_id
            session_obj = db.query(AuditSession).filter(AuditSession.project_key == p_key).order_by(AuditSession.id.desc()).first()
            if session_obj:
                audit_session_id = session_obj.id

        if not audit_session_id:
            raise HTTPException(status_code=404, detail="Session not found")

        audit_result = db.query(AuditResult).filter(AuditResult.audit_session_id == audit_session_id).first()
        if audit_result:
            audit_session = db.query(AuditSession).get(audit_session_id)
            seen_q = set()
            faqs = []
            for faq in db.query(FAQRecord).filter(FAQRecord.audit_session_id == audit_session_id).order_by(FAQRecord.relevance_score.desc()).all():
                q_norm = (faq.question or "").strip().lower()
                if q_norm not in seen_q:
                    seen_q.add(q_norm)
                    faqs.append({
                        "question": faq.question,
                        "answer": faq.answer,
                        "category": faq.category,
                        "relevance_score": faq.relevance_score,
                    })
            result_payload = audit_result.variance_json or {}
            result_payload["faqs"] = faqs

            features_list = []
            contributors_list = []
            srs_features = []
            platform_type = "jira"
            project_key = result_payload.get("project_key", "Project")
            provider = None

            if audit_session:
                platform_type = audit_session.platform_type or platform_type
                project_key = audit_session.project_key or project_key
                provider = getattr(audit_session, "provider", None)
                if audit_session.normalized_data_json:
                    features_list = audit_session.normalized_data_json
                if audit_session.platform_fetch_result_id:
                    p_res = db.query(PlatformFetchResult).get(audit_session.platform_fetch_result_id)
                    if p_res:
                        contributors_list = p_res.contributors_json or []
                        if not features_list and p_res.actual_data_json:
                            features_list = p_res.actual_data_json
                if audit_session.srs_result_id:
                    s_res = db.query(SRSExtractionResult).get(audit_session.srs_result_id)
                    if s_res and s_res.extracted_json:
                        srs_features = s_res.extracted_json.get("features", [])

            platform_data_dict = {
                "platform": platform_type,
                "platform_key": project_key,
                "features": features_list,
                "contributors": contributors_list
            }

            session_dict = {
                "audit_result": result_payload,
                "analysis_result": result_payload,
                "result_payload": result_payload,
                "faqs": faqs,
                "platform_data": platform_data_dict,
                "srs_features": srs_features,
                "provider": provider
            }
            # Repopulate Redis cache for future reads
            if redis_client:
                try:
                    redis_client.setex(f"session:{session_id}", 86400, pickle.dumps(session_dict))
                except Exception as e:
                    logger.error(f"Redis set after DB fallback failed: {e}")
            return session_dict
    except HTTPException:
        raise
    except Exception as db_err:
        logger.error(f"DB fallback error in get_session: {db_err}")
    finally:
        db.close()
    raise HTTPException(status_code=404, detail="Session not found")


def set_session(session_id: str, session_data: dict):

    if redis_client:
        try:
            redis_client.setex(f"session:{session_id}", 86400, pickle.dumps(session_data))
        except Exception as e:
            logger.error(f"Redis set failed: {e}")


# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class PlatformCredentials(BaseModel):
    """Platform-specific credentials."""
    platform: str  # "github" or "jira"
    
    # GitHub fields
    owner: Optional[str] = None
    repo: Optional[str] = None
    github_pat: Optional[str] = None
    
    # JIRA fields
    project_key: Optional[str] = None
    jira_domain: Optional[str] = None
    jira_api_token: Optional[str] = None
    jira_email: Optional[str] = None
    jira_username: Optional[str] = None


class DelayAnalysisRequest(BaseModel):
    """Request for delay analysis."""
    credentials: PlatformCredentials
    srs_file: Optional[UploadFile] = None
    srs_features: Optional[List[Dict[str, Any]]] = None


class FAQItem(BaseModel):
    """FAQ item response."""
    question: str
    answer: str
    category: str
    relevance_score: float


class DelayAnalysisResponse(BaseModel):
    """Response from delay analysis."""
    project_key: str
    platform: str
    analysis_timestamp: str
    total_features: int
    completed_features: int
    in_progress_features: int
    blocked_features: int
    unassigned_features: int
    severity_score: float
    primary_causes: List[str]
    evidence_count: int
    faqs: List[FAQItem]
    session_id: str
    freshness_penalty_applied: bool = False
    freshness_penalty_factor: float = 1.0


class ChatbotRequest(BaseModel):
    """Request for chatbot Q&A."""
    question: str
    project_key: str
    platform: str
    session_id: Optional[str] = None
    provider: str = "groq"


class ChatbotResponse(BaseModel):
    """Response from chatbot."""
    question: str
    answer: str
    timestamp: str


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def _validate_github_creds(creds: PlatformCredentials) -> bool:
    """Validate GitHub credentials."""
    return all([creds.owner, creds.repo, creds.github_pat])


def _validate_jira_creds(creds: PlatformCredentials) -> bool:
    """Validate JIRA credentials."""
    return all([
        creds.project_key,
        creds.jira_domain,
        creds.jira_api_token,
        creds.jira_email or creds.jira_username
    ])


def _get_platform_adapter(creds: PlatformCredentials):
    """Get appropriate platform adapter based on credentials."""
    if creds.platform.lower() == "github":
        if not _validate_github_creds(creds):
            raise HTTPException(status_code=400, detail="Invalid GitHub credentials")
        return GitHubAdapter(creds.owner, creds.repo, creds.github_pat)
    
    elif creds.platform.lower() == "jira":
        if not _validate_jira_creds(creds):
            raise HTTPException(status_code=400, detail="Invalid JIRA credentials")
        return JiraAdapter(
            project_key=creds.project_key,
            domain=creds.jira_domain,
            api_token=creds.jira_api_token,
            email=creds.jira_email,
            username=creds.jira_username
        )
    
    else:
        raise HTTPException(status_code=400, detail=f"Unsupported platform: {creds.platform}")


# ============================================================================
# ENDPOINTS
# ============================================================================

def _parse_srs_file(srs_file: Optional[UploadFile]) -> List[Dict[str, Any]]:
    """Save an uploaded SRS file, parse it, and extract structured features."""
    if not srs_file:
        return []

    uploads_dir = os.getenv("UPLOADS_DIR", "/app/data/uploads")
    os.makedirs(uploads_dir, exist_ok=True)

    import uuid, shutil, os

    original_filename = srs_file.filename or "srs_upload"
    srs_filename = f"srs_{uuid.uuid4().hex}_{original_filename}"
    srs_path = os.path.join(uploads_dir, srs_filename)

    with open(srs_path, "wb") as f:
        shutil.copyfileobj(srs_file.file, f)

    parser = SRSParser()
    try:
        parsed_srs = parser.parse(srs_path)
        extractor = SRSFeatureExtractor()
        extracted_features = extractor.extract_features(parsed_srs["raw_content"])
    except Exception as e:
        logger.error(f"Failed to parse SRS file: {e}")
        raise HTTPException(status_code=400, detail=f"Failed to parse SRS file. Ensure it is a valid document. Error: {str(e)}")

    if not extracted_features:
        raise HTTPException(status_code=400, detail="SRS parsing succeeded but yielded 0 features. The file may be empty or improperly formatted.")

    return extracted_features


@router.post("/analyze")
async def analyze_delays(
    platform: Optional[str] = Form(None),
    owner: Optional[str] = Form(None),
    repo: Optional[str] = Form(None),
    github_pat: Optional[str] = Form(None),
    project_key: Optional[str] = Form(None),
    jira_domain: Optional[str] = Form(None),
    jira_api_token: Optional[str] = Form(None),
    jira_email: Optional[str] = Form(None),
    jira_username: Optional[str] = Form(None),
    provider: Optional[str] = Form("groq"),
    srs_file: Optional[UploadFile] = File(None),
    audit_session_id: Optional[int] = Form(None),
    db: Session = Depends(get_db),
    user: TokenData = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Queue project delay analysis using GitHub or JIRA data.
    Verifies that all 5 approval steps are completed before scheduling.
    """
    audit_session = None
    if audit_session_id:
        audit_session = db.query(AuditSession).filter(
            AuditSession.id == audit_session_id,
            AuditSession.user_id == user.user_id
        ).first()
    if not audit_session:
        audit_session = db.query(AuditSession).filter(
            AuditSession.user_id == user.user_id,
            AuditSession.status.in_(["IN_PROGRESS", "RUNNING"])
        ).order_by(AuditSession.id.desc()).first()
    if not audit_session:
        raise HTTPException(status_code=404, detail="No active audit session found")

    # Enforce 5 approval flags
    if not (audit_session.planned_data_approved and
            audit_session.actual_data_approved and
            audit_session.capacity_approved and
            audit_session.normalized_data_approved and
            audit_session.matches_approved):
        raise HTTPException(
            status_code=400,
            detail="Cannot run audit. All 5 steps (Planned data, Actual data, Capacity configuration, Merged dataset, and Semantic matches) must be approved by the manager first."
        )

    p_type = platform or audit_session.platform_type or "github"
    audit_session.platform_type = p_type
    audit_session.status = "RUNNING"
    audit_session.progress_percent = 5
    audit_session.stage = "QUEUED"
    db.commit()

    session_id = str(audit_session.id)

    # Dispatch Celery task with credentials bypassed since it reads approved DB tables
    task = execute_delay_analysis_task.delay(
        credentials_dict={},
        srs_features=None,
        srs_file_content=None,
        provider=provider,
        session_id=session_id,
    )

    return {"task_id": task.id, "session_id": session_id, "status": "QUEUED"}


@router.get("/row-intelligence", response_model=dict)
async def get_row_intelligence(
    session_id: int,
    requirement: str,
    db: Session = Depends(get_db),
    user: TokenData = Depends(get_current_user)
):
    """
    Generate context-specific Root Cause, Severity, 5 FAQs, and row-level chatbot prompt
    for a specific requirement in an audit session.
    """
    audit_session = db.query(AuditSession).filter(
        AuditSession.id == session_id,
        AuditSession.user_id == user.user_id
    ).first()
    if not audit_session:
        raise HTTPException(status_code=404, detail="Audit session not found")
    audit_result = db.query(AuditResult).filter(AuditResult.audit_session_id == session_id).first()
    if not audit_result or not audit_result.variance_json:
        raise HTTPException(status_code=404, detail="Audit results not found for this session")
        
    variance_table = audit_result.variance_json.get("variance_table", [])
    
    row = None
    for item in variance_table:
        if item.get("requirement") == requirement:
            row = item
            break
            
    if not row:
        raise HTTPException(status_code=404, detail=f"Requirement '{requirement}' not found in variance table")
        
    variance = row.get("variance", 0.0)
    severity = row.get("severity", "medium")
    
    from backend.llm.manager import LLMManager
    import json
    
    prompt = f"""You are ScopeSense's AI intelligence engine. Analyze the following project requirement delay details and generate a concise, definitive root cause explanation, 5 relevant context-aware FAQs, and a system prompt for chatbot Q&A.

Requirement details:
- Module: {row.get('module')}
- Requirement: {row.get('requirement')}
- Evidence/Tickets: {row.get('evidence')}
- Developer: {row.get('developer')}
- Planned Hours: {row.get('planned_hours')}
- Actual Hours: {row.get('actual_hours')}
- Variance: {row.get('variance')} hours
- Status: {row.get('status')}

CRITICAL RULES FOR INTERPRETATION:
1. "Actual Hours = 0" does NOT mean the ticket does not exist. If 'Evidence/Tickets' lists a ticket, it means a ticket exists and is assigned, but the developer simply has NOT LOGGED any time (Time Spent) against it yet.
2. A Negative Variance (e.g., -20h) means the task is under-budget or unstarted. A Positive Variance means the task took longer than planned (overrun).
3. Do not falsely claim "no ticket exists" if there is an item in the Evidence/Tickets field.
4. BE SPECIFIC AND DEFINITIVE: Do NOT use vague speculation or hedging words like 'either... or', 'possibly', or 'might be'. State the direct operational root cause clearly and authoritatively in 2 to 3 punchy sentences.

Respond strictly in JSON format. The response must be a single JSON object with these exact keys:
- root_cause: A crisp, strong, authoritative 2-to-3 sentence executive root cause explanation. Directly state the key takeaway (e.g., pending time-logging, blocker bottleneck, or estimation mismatch) without hedging.
- severity: "high", "medium", or "low"
- faqs: A list of exactly 5 objects, each with "question" and "answer" keys. Keep answers concise (1-2 sentences).
- system_prompt: A system prompt tailored for a chatbot helping the manager answer further questions about this specific requirement.
"""

    try:
        from backend.config.settings import settings
        manager = LLMManager(provider=settings.LLM_PROVIDER)
        response_text = manager.generate(prompt)
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0]
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0]
        data = json.loads(response_text.strip())
        
        raw_faqs = data.get("faqs", [])
        seen_row_q = set()
        faqs = []
        for f in raw_faqs:
            q_norm = (f.get("question") or "").strip().lower()
            if q_norm and q_norm not in seen_row_q:
                seen_row_q.add(q_norm)
                faqs.append(f)
        if len(faqs) > 5:
            faqs = faqs[:5]
        
        return {
            "requirement": requirement,
            "root_cause": data.get("root_cause"),
            "severity": data.get("severity", severity),
            "faqs": faqs,
            "system_prompt": data.get("system_prompt", f"You are a chatbot helping answer questions about requirement '{requirement}'."),
            "fallback_used": manager.provider_used if manager.provider_used and manager.provider_used != manager.requested_provider else None
        }
    except Exception as e:
        logger.warning(f"Row intelligence AI generation failed or rate-limited ({e}). Using deterministic heuristic fallback.")
        dev = row.get("developer") or "Unassigned"
        mod = row.get("module") or "General"
        ev = row.get("evidence") or []
        ev_str = ", ".join([str(x) for x in ev]) if isinstance(ev, list) else str(ev)
        act = float(row.get("actual_hours") or 0.0)
        pln = float(row.get("planned_hours") or 0.0)
        var = float(row.get("variance") or 0.0)

        if act == 0 and ev:
            heuristic_rc = f"Ticket is assigned to developer '{dev}' in Jira ({ev_str}), but no work hours have been logged against it yet. This pending time tracking creates an apparent roadmap variance of {int(var)}h."
        elif var > 0:
            heuristic_rc = f"Development effort on requirement '{requirement}' exceeded planned capacity by {int(var)}h. Technical complexity or cross-component dependencies impacted developer delivery speed."
        else:
            heuristic_rc = f"Requirement '{requirement}' is operating within budget or unstarted, with {int(pln)}h planned vs {int(act)}h logged."

        heuristic_faqs = [
            {"question": f"Why does requirement '{requirement}' show a variance of {int(var)}h?", "answer": heuristic_rc},
            {"question": f"Who is responsible for delivering '{requirement}'?", "answer": f"Developer '{dev}' is assigned to this requirement under module '{mod}'."},
            {"question": "Are there Jira tickets tracked for this feature?", "answer": f"Yes, tracked under evidence IDs: {ev_str}." if ev_str else "No explicit Jira tickets or evidence items were matched to this requirement."},
            {"question": "What immediate action should management take?", "answer": "Verify developer progress and ensure all time spent is logged accurately in Jira." if act == 0 else "Review potential blockers with the assigned engineer and re-evaluate sprint capacity."},
            {"question": "How does this impact project milestone completion?", "answer": "Unresolved variance on core module requirements directly affects downstream integration and deployment timelines."}
        ]

        return {
            "requirement": requirement,
            "root_cause": heuristic_rc,
            "severity": severity,
            "faqs": heuristic_faqs,
            "system_prompt": f"You are a chatbot helping answer questions about requirement '{requirement}'.",
            "fallback_used": "Heuristic Engine"
        }


def _paginate(items: List[Dict[str, Any]], page: int, page_size: int) -> Dict[str, Any]:
    total = len(items)
    start = max(0, (page - 1) * page_size)
    end = start + page_size
    return {
        "items": items[start:end],
        "page": page,
        "page_size": page_size,
        "total": total,
    }


def _result_payload_for_session(db: Session, session_id: int, user: TokenData) -> Dict[str, Any]:
    audit_session = db.query(AuditSession).filter(
        AuditSession.id == session_id,
        AuditSession.user_id == user.user_id
    ).first()
    if not audit_session:
        raise HTTPException(status_code=404, detail="Audit session not found")

    audit_result = db.query(AuditResult).filter(
        AuditResult.audit_session_id == session_id
    ).order_by(AuditResult.id.desc()).first()
    if not audit_result:
        raise HTTPException(status_code=404, detail="Audit result not found")

    payload = dict(audit_result.variance_json or {})
    
    if not audit_session.identity_resolution_json and "identity_resolution" in payload:
        try:
            audit_session.identity_resolution_json = payload["identity_resolution"]
            db.commit()
        except Exception as e:
            db.rollback()
            from backend.observability.structured_logger import get_logger
            lgr = get_logger(__name__)
            lgr.error("failed_to_persist_identity_resolution", error=str(e))
            
    seen_q = set()
    faqs = []
    for faq in db.query(FAQRecord).filter(FAQRecord.audit_session_id == session_id).order_by(FAQRecord.relevance_score.desc()).all():
        q_norm = (faq.question or "").strip().lower()
        if q_norm not in seen_q:
            seen_q.add(q_norm)
            faqs.append({
                "question": faq.question,
                "answer": faq.answer,
                "category": faq.category,
                "relevance_score": faq.relevance_score,
            })
    payload["faqs"] = faqs
    if "audit_report" in audit_result.variance_json:
        payload["audit_report"] = audit_result.variance_json["audit_report"]
    payload["session_id"] = str(session_id)
    payload["audit_session"] = {
        "id": audit_session.id,
        "status": audit_session.status,
        "progress_percent": audit_session.progress_percent,
        "stage": audit_session.stage,
        "srs_confirmed": audit_session.srs_confirmed,
        "platform_confirmed": audit_session.platform_confirmed,
        "calendar_confirmed": audit_session.calendar_confirmed,
    }
    return payload


@router.get("/results/latest/active", response_model=dict)
async def get_latest_active_results(
    db: Session = Depends(get_db),
    user: TokenData = Depends(get_current_user),
) -> Dict[str, Any]:
    audit_session = db.query(AuditSession).filter(
        AuditSession.user_id == user.user_id,
        AuditSession.status == "COMPLETED"
    ).order_by(AuditSession.id.desc()).first()
    if not audit_session:
        raise HTTPException(status_code=404, detail="No completed audit result found")
    return _result_payload_for_session(db, audit_session.id, user)


@router.get("/results/{session_id}", response_model=dict)
async def get_results(
    session_id: int,
    variance_page: int = Query(1, ge=1),
    developer_page: int = Query(1, ge=1),
    root_cause_page: int = Query(1, ge=1),
    faq_page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
    user: TokenData = Depends(get_current_user),
) -> Dict[str, Any]:
    payload = _result_payload_for_session(db, session_id, user)
    payload["variance_table"] = _paginate(payload.get("variance_table", []), variance_page, page_size)
    payload["developer_table"] = _paginate(payload.get("developer_table", []), developer_page, page_size)
    payload["root_cause_table"] = _paginate(payload.get("root_cause_table", []), root_cause_page, page_size)
    payload["faq_table"] = _paginate(payload.get("faqs", []), faq_page, page_size)
    return payload


@router.get("/analyze/status/{task_id}")
async def get_analyze_status(task_id: str) -> dict:
    from backend.tasks.celery_app import celery
    task = celery.AsyncResult(task_id)
    if task.state == "PENDING":
        return {"status": "QUEUED"}
    elif task.state == "SUCCESS":
        return task.result if task.result is not None else {"status": "COMPLETED"}
    elif task.state == "FAILURE":
        return {"status": "FAILED", "error": str(task.info)}
    else:
        return {"status": task.state}


@router.post("/chat")
async def chat(request: ChatbotRequest, db: Session = Depends(get_db)) -> ChatbotResponse:
    """
    Chat with AI about project delays and performance.
    
    Args:
        question: Question about the project
        project_key: Project identifier
        platform: Platform type (github or jira)
        session_id: Optional session identifier
        provider: Optional provider name
    
    Returns:
        Answer to the question
    """
    try:
        session_id = request.session_id or f"{request.platform}:{request.project_key}"
        session = get_session(session_id)
        if not session:
            logger.warning(f"No session found for {session_id}, falling back to general LLM response.")
            from backend.llm.manager import LLMManager
            from backend.config.settings import settings
            provider = request.provider or settings.LLM_PROVIDER
            llm = LLMManager(provider=provider)
            try:
                answer = llm.generate(f"You are an AI Copilot for software engineering project audits. Answer the user's question concisely and authoritatively: {request.question}")
            except Exception as e:
                logger.error(f"Fallback LLM generation failed: {e}")
                answer = "I am ready to assist! Please execute or select an audit session to analyze specific project delays and metrics."
            return ChatbotResponse(
                question=request.question,
                answer=answer,
                timestamp=datetime.utcnow().isoformat()
            )

        result_payload = session.get("result_payload") or session.get("audit_result")
        platform_data = session.get("platform_data")
        
        # Handle Row Context queries explicitly using LLM
        if "[Row Context:" in request.question:
            from backend.llm.manager import LLMManager
            from backend.config.settings import settings
            provider = request.provider or session.get("provider") or settings.LLM_PROVIDER
            llm = LLMManager(provider=provider)
            prompt = (
                "You are an expert software project management AI assistant. "
                "You are provided with a specific 'Row Context' containing details about a single requirement or task. "
                "Answer the user's question. If the question pertains to this task, use the provided context. "
                "CRITICAL RULES: \n"
                "1. If 'Actual Hours' is 0 but there is a ticket listed, it means the ticket exists but the developer hasn't logged time. Do not say the ticket is missing.\n"
                "2. Positive variance means overrun; negative variance means under-budget or unstarted.\n"
                "If the question is general or unrelated to the specific task, you should still answer it fully using your general knowledge.\n\n"
                f"{request.question}"
            )
            try:
                answer = llm.generate(prompt)
            except Exception as e:
                logger.error(f"Row context LLM generation failed: {e}")
                answer = "I'm sorry, I couldn't generate an answer at this time."
                
            return ChatbotResponse(
                question=request.question,
                answer=answer,
                timestamp=datetime.utcnow().isoformat(),
            )
            
        # Only fallback for general queries when both platform_data and result_payload are missing
        if not platform_data and not result_payload:
            # Instead of naive keyword matching, we can use LLM with the result payload summary
            from backend.llm.manager import LLMManager
            from backend.config.settings import settings
            import json
            provider = request.provider or session.get("provider") or settings.LLM_PROVIDER
            llm = LLMManager(provider=provider)
            
            # Create a concise summary of the project to fit in context
            variance_table = result_payload.get("variance_table", [])
            total_planned = sum(v.get("planned_hours", 0) for v in variance_table)
            total_actual = sum(v.get("actual_hours", 0) for v in variance_table)
            
            summary = {
                "schedule_variance": result_payload.get("schedule_variance"),
                "total_planned_hours": total_planned,
                "total_actual_hours": total_actual,
                "total_features": result_payload.get("total_features"),
                "primary_causes": result_payload.get("primary_causes"),
                "severity_score": result_payload.get("severity_score"),
            }
            prompt = (
                "You are an expert project management AI assistant. "
                "You are provided with a summary of the project delays. "
                "Answer the user's question. If the question relates to the project, use the summary. "
                "CRITICAL RULES: \n"
                "1. If 'Actual Hours' is 0, do not assume tickets don't exist. It usually means developers have not logged time (Time Spent) in their tracking tool.\n"
                "2. Only reference data provided in the context; do not hallucinate metrics.\n"
                "If the question is general or unrelated, still answer it fully using your general knowledge.\n"
                f"Project Summary: {json.dumps(summary)}\n\n"
                f"User Question: {request.question}"
            )
            try:
                answer = llm.generate(prompt)
            except Exception as e:
                logger.error(f"Fallback LLM generation failed: {e}")
                causes = result_payload.get("primary_causes", [])
                answer = "The latest audit identifies these primary causes: "
                answer += ", ".join(causes) if causes else "no primary causes recorded"
                
            return ChatbotResponse(
                question=request.question,
                answer=answer,
                timestamp=datetime.utcnow().isoformat(),
            )

        platform_data = session["platform_data"]
        # Truncate large platform data payload to stay within token budget if dict
        if isinstance(platform_data, dict):
            from backend.llm.token_budget import truncate_to_budget
            import json
            try:
                platform_text = json.dumps(platform_data)
                platform_text = truncate_to_budget(platform_text)
                platform_data = json.loads(platform_text)
            except Exception:
                pass
        analysis_result = session["analysis_result"]
        faqs = session.get("faqs", [])
        srs_features = session.get("srs_features", [])
        from backend.config.settings import settings
        provider = request.provider or session.get("provider") or settings.LLM_PROVIDER
        
        from backend.storage.models_extended import ChatMessage
        
# Removed duplicate chat persistence (handled later)

        
        from backend.llm.manager import LLMManager
        
        chatbot = session.get("chatbot")
        if not chatbot:
            from backend.analysis.project_chatbot import ProjectChatbot
            chatbot = ProjectChatbot(
                platform_data=platform_data,
                analysis_result=analysis_result,
                provider=provider,
                faqs=faqs,
                srs_features=srs_features
            )
            session["chatbot"] = chatbot
        else:
            chatbot.contextualizer.llm_manager = LLMManager(provider=provider)
            
        # Compute answer first
        answer = chatbot.chat(request.question)
        # Persist chat messages to DB after answer is available
        try:
            audit_session_id = int(session_id) if session_id.isdigit() else None
            if audit_session_id:
                user_msg = ChatMessage(
                    audit_session_id=audit_session_id,
                    role='user',
                    content=request.question
                )
                assistant_msg = ChatMessage(
                    audit_session_id=audit_session_id,
                    role='assistant',
                    content=answer
                )
                db.add_all([user_msg, assistant_msg])
                db.commit()
        except Exception as db_err:
            logger.error(f"Failed to persist chat messages: {db_err}")
        # Update session with the chatbot state (e.g. chat history memory)
        session["chatbot"] = chatbot
        set_session(session_id, session)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Chatbot query failed: {e}")
        raise HTTPException(status_code=500, detail=f"Chat failed: {str(e)}")


@router.get("/platforms")
async def list_platforms() -> Dict[str, Any]:
    """
    Get list of supported platforms and their auth requirements.
    
    Returns:
        Supported platforms and credential requirements
    """
    return {
        "supported_platforms": [
            {
                "name": "github",
                "required_fields": ["owner", "repo", "github_pat"],
                "description": "GitHub repository analysis using Personal Access Token"
            },
            {
                "name": "jira",
                "required_fields": ["project_key", "jira_domain", "jira_api_token", "jira_email"],
                "description": "JIRA project analysis using API token (Cloud or Server)"
            }
        ]
    }


@router.post("/validate-credentials")
async def validate_credentials(credentials: PlatformCredentials) -> Dict[str, Any]:
    """
    Validate platform credentials without full analysis.
    
    Args:
        credentials: Platform credentials to validate
    
    Returns:
        Validation result
    """
    try:
        adapter = _get_platform_adapter(credentials)
        is_valid = adapter.authenticate()
        
        return {
            "valid": is_valid,
            "platform": credentials.platform,
            "message": "Credentials are valid" if is_valid else "Credentials are invalid"
        }
    
    except HTTPException as e:
        return {
            "valid": False,
            "platform": credentials.platform,
            "message": str(e.detail)
        }
    except Exception as e:
        logger.error(f"Credential validation failed: {e}")
        return {
            "valid": False,
            "platform": credentials.platform,
            "message": f"Validation error: {str(e)}"
        }


@router.get("/health")
async def health_check() -> Dict[str, str]:
    """Health check for delay analysis service."""
    return {
        "status": "healthy",
        "service": "Delay Analysis API",
        "version": "1.0.0"
    }
