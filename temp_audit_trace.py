import os, sys, json, traceback, types
ROOT = os.path.abspath('.')
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from backend.services.audit_service import AuditService
from backend.tasks.audit_tasks import audit_service
from backend.semantic.requirement_matcher import RequirementMatcher
from backend.intelligence.feature_ownership_engine import FeatureOwnershipEngine
from backend.intelligence.timeline_engine import TimelineEngine
from backend.intelligence.hotspot_engine import HotspotEngine
from backend.semantic.contributor_engine import ContributorIntelligenceEngine
from backend.semantic.dependency_engine import DependencyEngine
from backend.semantic.confidence_engine import ImplementationConfidenceEngine
from backend.intelligence.insight_narrative_engine import InsightNarrativeEngine
from backend.storage.repositories import AuditRepository

LOCAL_REPO = r"C:\Users\Raghuram\Desktop\AI\validation-repos\healthy-enterprise"
SRS_PATH = r"C:\Users\Raghuram\Desktop\AI\validation-repos\healthy-enterprise\docs\srs.txt"
OWNER = "octocat"
REPO = "Spoon-Knife"
PROVIDER = "gemini"

STATUS = {}

# Helper for wrappers

def make_wrapper(name, func, output_len=None, is_dict=False):
    def wrapped(*args, **kwargs):
        STATUS[name] = {'entered': True, 'completed': False, 'exception': None, 'output_size': None}
        print(f"[TRACE] ENTER {name}")
        try:
            result = func(*args, **kwargs)
            if isinstance(result, list):
                size = len(result)
            elif isinstance(result, dict):
                size = len(result)
            else:
                size = 1
            STATUS[name]['completed'] = True
            STATUS[name]['output_size'] = size
            print(f"[TRACE] EXIT  {name}: output_size={size}")
            return result
        except Exception as e:
            STATUS[name]['exception'] = repr(e)
            print(f"[TRACE] ERROR {name}: {repr(e)}")
            traceback.print_exc()
            raise
    return wrapped

# Patch methods
RequirementMatcher.match_requirements = make_wrapper(
    'RequirementMatcher.match_requirements',
    RequirementMatcher.match_requirements
)
FeatureOwnershipEngine.analyze = make_wrapper(
    'FeatureOwnershipEngine.analyze',
    FeatureOwnershipEngine.analyze
)
TimelineEngine.analyze_semantic_timeline = make_wrapper(
    'TimelineEngine.analyze_semantic_timeline',
    TimelineEngine.analyze_semantic_timeline
)
HotspotEngine.analyze = make_wrapper(
    'HotspotEngine.analyze',
    HotspotEngine.analyze
)
ContributorIntelligenceEngine.analyze = make_wrapper(
    'ContributorIntelligenceEngine.analyze',
    ContributorIntelligenceEngine.analyze
)
DependencyEngine.analyze_repository = make_wrapper(
    'DependencyEngine.analyze_repository',
    DependencyEngine.analyze_repository
)
ImplementationConfidenceEngine.evaluate = make_wrapper(
    'ImplementationConfidenceEngine.evaluate',
    ImplementationConfidenceEngine.evaluate
)
InsightNarrativeEngine.generate = make_wrapper(
    'InsightNarrativeEngine.generate',
    InsightNarrativeEngine.generate
)

# Track persistence
orig_persist = AuditService._persist_audit_result

def wrapped_persist(self, owner, repo, task_id, result, workflow=None):
    print("[TRACE] ENTER AuditService._persist_audit_result")
    STATUS['AuditService._persist_audit_result'] = {'entered': True, 'completed': False, 'exception': None}
    try:
        res = orig_persist(self, owner, repo, task_id, result, workflow=workflow)
        STATUS['AuditService._persist_audit_result']['completed'] = True
        print("[TRACE] EXIT  AuditService._persist_audit_result")
        return res
    except Exception as e:
        STATUS['AuditService._persist_audit_result']['exception'] = repr(e)
        print(f"[TRACE] ERROR AuditService._persist_audit_result: {repr(e)}")
        traceback.print_exc()
        raise

AuditService._persist_audit_result = wrapped_persist

orig_save_audit = AuditRepository.save_audit

def wrapped_save_audit(self, project_name, health_score, semantic_confidence, ai_summary):
    print("[TRACE] ENTER AuditRepository.save_audit")
    STATUS['AuditRepository.save_audit'] = {'entered': True, 'completed': False, 'exception': None}
    try:
        audit = orig_save_audit(self, project_name, health_score, semantic_confidence, ai_summary)
        STATUS['AuditRepository.save_audit']['completed'] = True
        STATUS['AuditRepository.save_audit']['output_id'] = audit.id if hasattr(audit, 'id') else None
        print(f"[TRACE] EXIT  AuditRepository.save_audit: id={STATUS['AuditRepository.save_audit']['output_id']}")
        return audit
    except Exception as e:
        STATUS['AuditRepository.save_audit']['exception'] = repr(e)
        print(f"[TRACE] ERROR AuditRepository.save_audit: {repr(e)}")
        traceback.print_exc()
        raise

AuditRepository.save_audit = wrapped_save_audit

# Patch _build_repository_context to use local repo
orig_build_context = AuditService._build_repository_context

def patched_build_context(self, owner, repo):
    print(f"[TRACE] PATCHED _build_repository_context: using LOCAL_REPO={LOCAL_REPO}")
    from backend.intelligence.git_miner import GitMiner
    miner = GitMiner(LOCAL_REPO)
    context = miner.build_context()
    context['repo_path'] = LOCAL_REPO
    context['vector_namespace'] = f"{owner}_{repo}"
    return context

AuditService._build_repository_context = patched_build_context

# Run workflow
print("[TRACE] Starting execute_full_audit")
service = AuditService()
try:
    result = service.execute_full_audit(
        github_owner=OWNER,
        github_repo=REPO,
        provider=PROVIDER,
        srs_path=SRS_PATH,
        audit_run_id='temp-debug-001'
    )
    print("[TRACE] execute_full_audit completed successfully")
    print(json.dumps(result, indent=2)[:4000])
except Exception as e:
    print("[TRACE] execute_full_audit raised:", repr(e))
    traceback.print_exc()
finally:
    print("\n[TRACE] STATUS SUMMARY")
    print(json.dumps(STATUS, indent=2))
