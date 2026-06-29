from fastapi import (
    APIRouter,
    UploadFile,
    File,
    Form,
    HTTPException,
    Depends
)
from backend.auth.jwt_utils import get_current_user, TokenData

from fastapi.responses import (
    JSONResponse
)

from pydantic import (
    BaseModel
)

import os
import uuid
import shutil
import requests
import json

from backend.services.audit_service import (
    AuditService
)

from backend.config.settings import settings

from backend.storage.database import (
    SessionLocal
)

from backend.storage.models import (
    Audit,
    Contributor,
    Feature
)

from backend.chat.project_chat import (
    ProjectChat
)

from backend.api.analytics_contracts import (
    risk_distribution_from_audit,
    roadmap_from_audit
)

# =================================================
# ROUTER
# =================================================

router = APIRouter()


# =================================================
# SERVICES
# =================================================

audit_service = None


class ChatRequest(BaseModel):

    question: str

    provider: str = "groq"


def get_audit_service():

    global audit_service

    if audit_service is None:

        audit_service = AuditService()

    return audit_service

# =================================================
# ROOT
# =================================================

@router.get("/")
async def health():

    return {

        "status":
            "ok",

        "platform":
            "ScopeSense v2"
    }

# =================================================
# HEALTH CHECK
# =================================================

@router.get("/health")
async def health_check():

    return {

        "status":
            "healthy",

        "service":
            "ScopeSense API"
    }


@router.get("/health/providers")
async def providers_health():

    provider_order = [
        name for name in ["gemini", "groq", "ollama"]
        if getattr(settings, f"{name.upper()}_ENABLED", False)
    ]

    providers = {
        "gemini": {
            "enabled": settings.GEMINI_ENABLED,
            "configured": bool(settings.GEMINI_API_KEY),
            "role": "primary",
            "status": "enabled" if settings.GEMINI_ENABLED else "disabled"
        },
        "groq": {
            "enabled": settings.GROQ_ENABLED,
            "configured": bool(settings.GROQ_API_KEY),
            "role": "primary",
            "status": "enabled" if settings.GROQ_ENABLED else "disabled"
        },
        "ollama": {
            "enabled": settings.OLLAMA_ENABLED,
            "configured": bool(settings.OLLAMA_URL),
            "role": "fallback",
            "status": "enabled" if settings.OLLAMA_ENABLED else "disabled"
        },
        "heuristic": {
            "enabled": settings.HEURISTIC_PARSER_ENABLED,
            "configured": True,
            "role": "fallback",
            "status": "enabled" if settings.HEURISTIC_PARSER_ENABLED else "disabled"
        }
    }

    return {
        "status": "healthy",
        "provider_order": provider_order,
        "providers": providers
    }

# =================================================
# TEST ROUTE
# =================================================

@router.get("/test")
async def test_route():

    return {

        "message":
            "Routes working successfully"
    }

# =================================================
# FETCH GITHUB REPOSITORIES
# =================================================

@router.get("/github/repos/{owner}")
async def get_repositories(owner: str, user: TokenData = Depends(get_current_user)):

    try:

        import os

        url = (
            f"https://api.github.com/users/"
            f"{owner}/repos"
            f"?per_page=100&sort=updated"
        )

        headers = {
            "Accept": "application/vnd.github+json"
        }

        token = os.getenv("GITHUB_TOKEN", "")

        if token:
            headers["Authorization"] = f"Bearer {token}"

        response = requests.get(url, headers=headers)

        if response.status_code != 200:

            raise HTTPException(

                status_code=response.status_code,

                detail="Failed to fetch repositories"
            )

        data = response.json()

        repos = []

        for repo in data:

            repos.append({

                "name":
                    repo["name"],

                "private":
                    repo.get(
                        "private",
                        False
                    ),

                "url":
                    repo.get(
                        "html_url",
                        ""
                    )
            })

        return {

            "success":
                True,

            "repositories":
                repos
        }

    except HTTPException as e:

        raise e

    except Exception as e:

        import traceback
        traceback.print_exc()

        raise HTTPException(

            status_code=500,

            detail=str(e)
        )

# =================================================
# START FULL AUDIT (ASYNC)
# =================================================

@router.post("/audit/start")
async def start_audit(

    owner: str = Form(...),

    repository: str = Form(...),

    provider: str = Form(...),

    srs_file: UploadFile = File(...),

    user: TokenData = Depends(get_current_user)
):

    try:

        # ---------------------------------------------
        # SAVE SRS FILE TO SHARED UPLOADS VOLUME
        # ---------------------------------------------
        # CRITICAL: We MUST write to /app/data/uploads
        # (shared Docker volume) NOT the OS temp dir.
        # The Celery worker runs in a different container
        # and cannot access /tmp from the API container.
        # ---------------------------------------------

        uploads_dir = os.getenv(
            "UPLOADS_DIR",
            "/app/data/uploads"
        )

        os.makedirs(uploads_dir, exist_ok=True)

        import uuid, shutil
        # Preserve original extension and save file under shared volume
        _, ext = os.path.splitext(srs_file.filename)
        ext = ext.lower()
        if not ext:
            ext = ".txt"

        ALLOWED_EXTENSIONS = {".txt", ".md", ".docx", ".pdf", ".xlsx"}
        if ext not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file type: {ext}. Allowed types are: {', '.join(sorted(ALLOWED_EXTENSIONS))}"
            )

        srs_filename = f"srs_{uuid.uuid4().hex}_{srs_file.filename}"
        srs_path = os.path.join(uploads_dir, srs_filename)

        print(f"[API] Original filename: {srs_file.filename}")
        print(f"[API] Saved filename: {srs_filename}")
        print(f"[API] Detected extension: {ext}")

        with open(srs_path, "wb") as f:
            shutil.copyfileobj(srs_file.file, f)

        # ---------------------------------------------
        # START CELERY TASK
        # ---------------------------------------------

        from backend.tasks.audit_tasks import (
            execute_audit
        )

        task = execute_audit.delay(

            owner,

            repository,

            srs_path,

            provider
        )

        # ---------------------------------------------
        # RESPONSE
        # ---------------------------------------------

        return {

            "success":
                True,

            "task_id":
                task.id,

            "message":
                "Audit started successfully"
        }

    except Exception as e:

        return JSONResponse(

            status_code=500,

            content={

                "success":
                    False,

                "error":
                    str(e)
            }
        )

# =================================================
# DIRECT REPOSITORY PROFILE
# =================================================

@router.post("/profile")
async def profile_repository(

    owner: str = Form(...),

    repository: str = Form(...),

    user: TokenData = Depends(get_current_user)
):

    try:

        result = (

            get_audit_service()
            .execute_repository_audit(

                owner=owner,

                repo=repository
            )
        )

        return {

            "success":
                True,

            "data":
                result
        }

    except Exception as e:

        raise HTTPException(

            status_code=500,

            detail=str(e)
        )

# =================================================
# TASK PROGRESS
# =================================================

@router.get("/task/{task_id}")
async def get_task_progress(

    task_id: str,
    user: TokenData = Depends(get_current_user)
):

    try:

        progress = (

            get_audit_service()
            .get_task_progress(
                task_id
            )
        )

        return {

            "success":
                True,

            "task":
                progress
        }

    except Exception as e:

        raise HTTPException(

            status_code=500,

            detail=str(e)
        )

# =================================================
# ANALYTICS OVERVIEW
# =================================================

@router.get("/analytics/overview")
async def analytics_overview(user: TokenData = Depends(get_current_user)):

    db = None

    try:

        db = SessionLocal()

        audits = db.query(Audit).all()

        total_audits = len(audits)

        avg_health = 0

        if total_audits > 0:

            avg_health = sum(

                audit.health_score
                for audit in audits

            ) / total_audits

        return {

            "success":
                True,

            "total_audits":
                total_audits,

            "average_health_score":
                round(
                    avg_health,
                    2
                ),

            "average_health":
                round(
                    avg_health,
                    2
                ),

            "latest_audit":
                audits[-1].project_name
        }

    except Exception as e:

        return {

            "success":
                False,

            "error":
                str(e)
        }

    finally:

        if db:

            db.close()


# =================================================
# AUDIT HISTORY
# =================================================

@router.get("/audits/history")
async def audit_history(user: TokenData = Depends(get_current_user)):

    db = None

    try:

        db = SessionLocal()

        audits = (

            db.query(Audit)
            .order_by(Audit.id.asc())
            .all()
        )

        return {

            "success":
                True,

            "audits": [

                {

                    "id":
                        audit.id,

                    "project_name":
                        audit.project_name,

                    "health_score":
                        audit.health_score,

                    "semantic_confidence":
                        audit.semantic_confidence,

                    "created_at":
                        str(audit.created_at)
                }

                for audit in audits
            ]
        }

    except Exception as e:

        return {

            "success":
                False,

            "audits":
                [],

            "error":
                str(e)
        }

    finally:

        if db:

            db.close()


# =================================================
# CONTRIBUTOR HISTORY
# =================================================

@router.get("/contributors/history")
async def contributor_history(user: TokenData = Depends(get_current_user)):

    db = None

    try:

        db = SessionLocal()

        contributors = (

            db.query(Contributor)
            .all()
        )

        return {

            "success":
                True,

            "contributors": [

                {

                    "developer":
                        item.developer_name,

                    "commits":
                        item.commits,

                    "repository":
                        item.repository
                }

                for item in contributors
            ]
        }

    except Exception as e:

        latest = _latest_audit_payload()

        return {

            "success":
                False,

            "contributors":
                latest.get(
                    "contributors",
                    []
                ),

            "error":
                str(e)
        }

    finally:

        if db:

            db.close()


# =================================================
# FEATURE HISTORY
# =================================================

@router.get("/features/history")
async def feature_history(user: TokenData = Depends(get_current_user)):

    latest = _latest_audit_payload()

    return {

        "success":
            True,

        "features":
            latest.get(
                "semantic_features",
                []
            ),

        "feature_ownership":
            latest.get(
                "feature_ownership",
                []
            )
    }


# =================================================
# ANALYTICS HISTORY
# =================================================

@router.get("/analytics/history")
async def analytics_history(user: TokenData = Depends(get_current_user)):

    data = await audit_history()

    return data.get(
        "audits",
        []
    )


# =================================================
# ANALYTICS RISKS
# =================================================

@router.get("/analytics/risks")
async def analytics_risks(user: TokenData = Depends(get_current_user)):

    latest = _latest_audit_payload()

    return risk_distribution_from_audit(
        latest
    )


# =================================================
# ANALYTICS ROADMAP
# =================================================

@router.get("/analytics/roadmap")
async def analytics_roadmap(user: TokenData = Depends(get_current_user)):

    latest = _latest_audit_payload()

    return roadmap_from_audit(
        latest
    )


# =================================================
# LATEST AUDIT SEMANTIC SECTIONS
# =================================================

@router.get("/audit/latest")
async def latest_audit(
    owner: str | None = None,
    repo: str | None = None,
    normalize: bool = False,
    user: TokenData = Depends(get_current_user)
):

    return {

        "success":
            True,

        "result":
            _latest_audit_payload(
                owner=owner,
                repo=repo,
                normalize=normalize
            )
    }


# =================================================
# PAYLOAD HELPERS
# =================================================

def _latest_audit_payload(
    owner: str | None = None,
    repo: str | None = None,
    normalize: bool = False
):

    db = None

    try:

        db = SessionLocal()

        query = db.query(Audit)

        if owner and repo:
            query = query.filter(
                Audit.project_name == f"{owner}/{repo}"
            )

        audit = (

            query
            .order_by(
                Audit.created_at.desc(),
                Audit.id.desc()
            )
            .first()
        )

        if not audit or not audit.ai_summary:

            return {}

        result = json.loads(
            audit.ai_summary
        )
        
        # Re-sanitize as defense-in-depth in case DB record pre-dates Phase 2E
        # This removes any unsanitized documents from old audit records
        from backend.services.audit_service import AuditService
        sanitizer = AuditService()
        sanitized = sanitizer._sanitize_persisted_audit(result)

        # Use the raw semantic feature copy when available.
        if sanitized.get("_raw_semantic_features") is not None:
            sanitized["semantic_features"] = sanitized["_raw_semantic_features"]

        if normalize:
            from backend.services.normalization_service import NormalizationService
            normalizer = NormalizationService()
            sanitized = normalizer.normalize_audit_result(
                sanitized,
                config_version="1.0"
            )
            sanitized["_normalization_applied"] = True
            sanitized["_normalization_applied_at_response"] = True
        else:
            sanitized["_normalization_applied"] = False

        if not sanitized.get("project_name"):
            sanitized["project_name"] = audit.project_name

        if "audit_id" not in sanitized:
            sanitized["audit_id"] = audit.id

        return sanitized

    except Exception as e:
        import traceback
        print(f"ERROR in _latest_audit_payload: {str(e)}")
        print(traceback.format_exc())
        return {}

    finally:

        if db:

            db.close()
