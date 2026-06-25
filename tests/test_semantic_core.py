import json
from datetime import datetime, timedelta, timezone
from unittest.mock import Mock, patch

from git import Repo

from backend.intelligence.git_miner import GitMiner
from backend.intelligence.feature_ownership_engine import FeatureOwnershipEngine
from backend.intelligence.hotspot_engine import HotspotEngine
from backend.intelligence.insight_narrative_engine import InsightNarrativeEngine
from backend.intelligence.timeline_engine import TimelineEngine
from backend.analytics.audit_engine import AuditEngine
from backend.semantic.causality_engine import EngineeringCausalityEngine
from backend.semantic.contributor_engine import ContributorIntelligenceEngine
from backend.srs.extractor import SRSFeatureExtractor
from backend.semantic.vector_store import VectorStore
from backend.storage.cache import SemanticCache
from backend.websocket.progress_manager import ProgressManager


def test_srs_feature_extractor_preserves_structured_features():

    content = """
Feature: Authentication System
Hours: 40
Developers: Alice, Bob
Priority: High
Timeline: 2 weeks
Dependencies: Redis, JWT
Milestone: M1
"""

    features = SRSFeatureExtractor().extract_features(content)

    assert features[0]["feature_name"] == "Authentication System"
    assert features[0]["expected_hours"] == 40
    assert features[0]["assigned_developers"] == ["Alice", "Bob"]
    assert features[0]["priority"] == "High"
    assert features[0]["dependencies"] == ["Redis", "JWT"]


def test_srs_feature_extractor_classification_metrics_without_filtering():

    content = """
Feature: Authentication System
Hours: 40
Developers: Alice, Bob
Priority: High
Timeline: 2 weeks
Dependencies: Redis, JWT
Milestone: M1

Feature: Security Monitoring
Priority: Medium

Feature: Recommended Team
Priority: Low
"""

    class FakeLLM:
        provider = "fake"

        def generate(self, prompt):
            return "[]"

    extractor = SRSFeatureExtractor(llm_manager=FakeLLM())
    features = extractor.extract_features(content)

    assert len(features) == 3
    classification_info = extractor.debug_info["classification"]
    assert classification_info["category_counts"]["SOFTWARE_FEATURE"] == 1
    assert classification_info["category_counts"]["NON_FUNCTIONAL_REQUIREMENT"] == 1
    assert classification_info["category_counts"]["TEAM_STRUCTURE"] == 1
    assert classification_info["kept_count"] == 1
    assert classification_info["filtered_count"] == 2
    assert len(classification_info["sample_classifications"]) == 3


def test_git_miner_builds_context_with_activity_files(tmp_path):

    repo = Repo.init(tmp_path)
    repo.config_writer().set_value("user", "name", "Alice").release()
    repo.config_writer().set_value("user", "email", "alice@example.com").release()

    auth_file = tmp_path / "auth.py"
    auth_file.write_text("print('auth')\n", encoding="utf-8")
    repo.index.add([str(auth_file)])
    repo.index.commit("auth initial")

    context = GitMiner(str(tmp_path)).build_context()

    assert context["contributors"][0]["name"] == "Alice"
    assert context["activity"][0]["message"] == "auth initial"
    assert "auth.py" in context["activity"][0]["files"]
    assert context["commit_velocity"] in ["low", "moderate", "high"]


def test_contributor_ownership_timeline_hotspot_causality_and_insights():

    features = [
        {
            "feature_name": "Authentication System",
            "expected_hours": 40,
            "assigned_developers": ["Alice"],
        }
    ]

    activity = [
        {
            "author": "Alice",
            "message": "implement authentication",
            "files": ["backend/authentication/service.py"],
            "timestamp": datetime.now(timezone.utc),
        }
    ]

    contributors = [{"name": "Alice", "total_commits": 1}]

    contributor_analysis = ContributorIntelligenceEngine().analyze(
        {
            "contributors": contributors,
            "activity": activity,
            "features": features,
        }
    )

    ownership = FeatureOwnershipEngine().analyze(
        features=features,
        activity=activity,
    )

    timeline = TimelineEngine().analyze_semantic_timeline(
        feature_data=features[0],
        repository_start_date=datetime.now(timezone.utc) - timedelta(days=10),
        actual_completion_date=datetime.now(timezone.utc),
        activity_gaps=[],
        commit_velocity="moderate",
    )

    hotspots = HotspotEngine().analyze(
        feature_ownership=ownership,
        timeline_analysis=[timeline],
    )

    causality = EngineeringCausalityEngine().analyze(
        timeline_analysis=timeline,
        contributor_analysis=contributor_analysis,
    )

    insights = InsightNarrativeEngine().generate(
        hotspots=hotspots,
        causality=[causality],
    )

    assert contributor_analysis[0]["developer"] == "Alice"
    assert ownership[0]["ownership_confidence"] > 0
    assert ownership[0]["evidence"]
    assert ownership[0]["contributing_factors"]["file_path_matches"] > 0
    assert timeline["feature"] == "Authentication System"
    assert hotspots[0]["feature"] == "Authentication System"
    assert causality["status"] in ["healthy", "moderate", "critical"]
    assert insights[0]["feature"] == "Authentication System"


def test_timeline_engine_detects_schedule_delay_from_planned_deadline():

    now = datetime.now(timezone.utc)
    feature = {
        "feature_name": "Authentication System",
        "expected_hours": 40,
        "assigned_developers": ["Alice"],
    }

    planned_deadline = now - timedelta(days=7)

    timeline = TimelineEngine().analyze_semantic_timeline(
        feature_data=feature,
        repository_start_date=now - timedelta(days=30),
        actual_completion_date=now,
        activity_gaps=[],
        commit_velocity="moderate",
        planned_completion_date=planned_deadline,
        schedule_source="github_milestone",
        matched_issue={
            "title": "Authentication System",
            "number": 42,
            "state": "open",
        },
    )

    assert timeline["schedule_delay_days"] > 0
    assert timeline["status"] == "delayed"
    assert timeline["schedule_source"] == "github_milestone"
    assert "planned_completion_date" in timeline
    assert "delay_root_cause" in timeline


def test_execute_audit_filters_downstream_ownership_and_timeline(tmp_path):

    content = """
Feature: Authentication System
Hours: 40
Developers: Alice
Priority: High

Feature: Recommended Team
Priority: Low
"""

    srs_file = tmp_path / "srs_test.txt"
    srs_file.write_text(content, encoding="utf-8")

    from backend.core.audit_workflow import AuditWorkflow

    workflow = AuditWorkflow()

    result = workflow.execute_audit(
        repository_context={
            "contributors": [],
            "activity": [],
        },
        srs_path=str(srs_file),
    )

    semantic_features = result.get("semantic_features", [])
    assert len(semantic_features) == 1
    assert len(result.get("feature_ownership", [])) == 1
    assert len(result.get("timeline_analysis", [])) == 1
    assert result["feature_ownership"][0]["feature"] == semantic_features[0]["feature_name"]
    assert result["timeline_analysis"][0]["feature"] == semantic_features[0]["feature_name"]


def test_execute_audit_resolves_feature_schedule_from_github_milestone(tmp_path):

    content = """
Feature: Authentication System
Hours: 40
Developers: Alice
Priority: High
Milestone: M1
"""

    srs_file = tmp_path / "srs_test.txt"
    srs_file.write_text(content, encoding="utf-8")

    from backend.core.audit_workflow import AuditWorkflow

    now = datetime.now(timezone.utc)

    result = AuditWorkflow().execute_audit(
        repository_context={
            "contributors": [],
            "activity": [],
            "issues": [
                {
                    "id": 1,
                    "title": "Authentication System",
                    "state": "open",
                    "created_at": now.isoformat(),
                    "milestone": {
                        "title": "M1",
                        "due_on": (now + timedelta(days=14)).strftime("%Y-%m-%dT%H:%M:%SZ"),
                        "number": 1,
                    },
                    "closed_at": None,
                }
            ],
            "milestones": [
                {
                    "id": 1,
                    "number": 1,
                    "title": "M1",
                    "due_on": (now + timedelta(days=14)).strftime("%Y-%m-%dT%H:%M:%SZ"),
                    "state": "open",
                }
            ],
            "repository_start_date": now - timedelta(days=7),
            "latest_activity_date": now,
            "activity_gaps": [],
            "commit_velocity": "low",
        },
        srs_path=str(srs_file),
    )

    timeline = result["timeline_analysis"][0]
    assert timeline["planned_completion_date"] is not None
    assert timeline["schedule_source"] == "github_milestone"
    assert timeline["matched_issue"]["title"] == "Authentication System"


def test_execute_audit_uses_filtered_features_for_requirement_matching(tmp_path):

    content = """
Feature: Authentication System
Hours: 40
Developers: Alice
Priority: High

Feature: Recommended Team
Priority: Low
"""

    srs_file = tmp_path / "srs_test.txt"
    srs_file.write_text(content, encoding="utf-8")
    repo_path = tmp_path / "repo"
    repo_path.mkdir()

    from backend.core.audit_workflow import AuditWorkflow
    from backend.semantic.requirement_matcher import RequirementMatcher

    workflow = AuditWorkflow()

    with patch.object(workflow.code_parser, "parse_repository", return_value=[]), patch.object(
        type(workflow.requirement_matcher),
        "match_requirements",
        autospec=True,
    ) as mocked_match:
        mocked_match.return_value = []

        workflow.execute_audit(
            repository_context={
                "repo_path": str(repo_path),
                "vector_namespace": "default",
            },
            srs_path=str(srs_file),
        )

        assert mocked_match.call_count == 1
        requirements_arg = mocked_match.call_args[0][1]
        assert requirements_arg == ["Authentication System"]


def test_llm_manager_falls_back_when_requested_provider_is_disabled(monkeypatch):
    from backend.config.settings import settings
    from backend.llm.manager import LLMManager

    monkeypatch.setattr(settings, "GEMINI_ENABLED", False)
    monkeypatch.setattr(settings, "GROQ_ENABLED", True)
    monkeypatch.setattr(settings, "OLLAMA_ENABLED", False)

    manager = LLMManager(provider="gemini")

    assert manager.requested_provider == "gemini"
    assert manager.provider == "groq"
    assert manager.get_provider_status()["gemini"]["enabled"] is False
    assert manager.get_provider_status()["groq"]["active"] is True


def test_persist_audit_removes_semantic_match_documents():

    from backend.services.audit_service import AuditService

    service = object.__new__(AuditService)
    service.audit_repository = Mock()
    service.audit_repository.save_audit.return_value = None

    memory_engine = Mock()
    workflow = Mock()
    workflow.memory_engine = memory_engine

    result = {
        "semantic_features": [
            {
                "feature_name": "Authentication System",
                "description": "Login and auth flow",
            }
        ],
        "optional_intelligence": {
            "semantic_matches": [
                {
                    "requirement": "Authentication System",
                    "matches": {
                        "ids": [["id1"]],
                        "documents": [["class AuthService: pass"]],
                        "metadatas": [[{"path": "auth.py"}]],
                        "distances": [[1.0]],
                    },
                }
            ]
        },
        "semantic_matches": [
            {
                "requirement": "Authentication System",
                "matches": {
                    "ids": [["id1"]],
                    "documents": [["class AuthService: pass"]],
                    "metadatas": [[{"path": "auth.py"}]],
                    "distances": [[1.0]],
                },
            }
        ],
    }

    service._persist_audit_result(
        owner="local",
        repo="aurora-engineering-platform",
        task_id="test-run",
        result=result,
        workflow=workflow,
    )

    saved_snapshot = memory_engine.save_snapshot.call_args[0][2]
    assert "documents" not in saved_snapshot["optional_intelligence"]["semantic_matches"][0]["matches"]
    assert "documents" not in saved_snapshot["semantic_matches"][0]["matches"]

    saved_json = service.audit_repository.save_audit.call_args[1]["ai_summary"]
    persisted = json.loads(saved_json)
    assert "documents" not in persisted["optional_intelligence"]["semantic_matches"][0]["matches"]
    assert "documents" not in persisted["semantic_matches"][0]["matches"]
    assert persisted["optional_intelligence"]["semantic_matches"][0]["matches"]["ids"] == [["id1"]]
    assert persisted["optional_intelligence"]["semantic_matches"][0]["matches"]["metadatas"] == [[{"path": "auth.py"}]]
    assert persisted["optional_intelligence"]["semantic_matches"][0]["matches"]["distances"] == [[1.0]]


def test_adaptive_commit_effort_includes_complexity_factors():

    engine = object.__new__(AuditEngine)

    feature = {
        "feature_name": "Authentication System",
        "expected_hours": 20,
    }

    commits = [
        {
            "message": "authentication service and tests",
            "files": [
                "backend/authentication/service.py",
                "tests/test_authentication.py",
            ],
            "insertions": 180,
            "deletions": 20,
        }
    ]

    effort = engine._estimate_commit_effort(
        feature,
        commits,
    )

    reasoning = engine._effort_reasoning(
        feature,
        commits,
    )

    assert effort > engine.BASE_HOURS_PER_COMMIT
    assert "test_modifications" in reasoning["factors"]
    assert reasoning["method"] == "adaptive_commit_effort"


def test_vector_store_namespace_helpers_are_stable():

    store = object.__new__(VectorStore)

    assert (
        store._normalize_namespace("owner/repo")
        == "owner_repo"
    )

    first = store._document_id(
        "chunk",
        "same content",
        0,
        "owner_repo",
    )

    second = store._document_id(
        "chunk",
        "same content",
        0,
        "owner_repo",
    )

    assert first == second
    assert first.startswith("owner_repo_chunk_0_")


def test_semantic_cache_gen_key_includes_commit_sha():

    cache = SemanticCache()

    first_key = cache.generate_key(
        "Authentication System",
        [
            {"sha": "abc123", "message": "Initial auth implementation"}
        ]
    )

    second_key = cache.generate_key(
        "Authentication System",
        [
            {"sha": "def456", "message": "Initial auth implementation"}
        ]
    )

    assert first_key != second_key


def test_progress_manager_stores_replayable_events():

    progress = ProgressManager()

    progress.redis_client = None

    progress.update(
        "run-1",
        "SEMANTIC_MAPPING",
        50,
    )

    progress.add_log(
        "run-1",
        "Running semantic intelligence",
    )

    events = progress.get_events(
        "run-1"
    )

    assert events[0]["type"] == "progress_update"
    assert events[1]["type"] == "log_update"


def test_execute_audit_persists_only_software_features(tmp_path):

    content = """
Feature: Authentication System
Hours: 40
Developers: Alice, Bob
Priority: High
Timeline: 2 weeks
Dependencies: Redis, JWT
Milestone: M1

Feature: Recommended Team
Priority: Low

Feature: Security Monitoring
Priority: Medium
"""

    srs_file = tmp_path / "srs_test.txt"
    srs_file.write_text(content, encoding="utf-8")

    from backend.core.audit_workflow import AuditWorkflow

    workflow = AuditWorkflow()

    result = workflow.execute_audit(repository_context={}, srs_path=str(srs_file))

    # debug_extraction should retain classification metrics
    debug = result.get("debug_extraction", {})
    classification = debug.get("classification", {})
    assert classification.get("kept_count") == 1
    assert classification.get("filtered_count") == 2
    assert classification.get("category_counts", {}).get("SOFTWARE_FEATURE") == 1
    assert classification.get("sample_classifications")
    assert classification.get("kept_count") + classification.get("filtered_count") == 3

    # semantic_features persisted in the result must contain only SOFTWARE_FEATURE items
    semantic_features = result.get("semantic_features", [])
    assert len(semantic_features) == 1
    assert len(semantic_features) == classification.get("kept_count")
    assert all(
        workflow.srs_extractor._classify_feature(f) == "SOFTWARE_FEATURE"
        for f in semantic_features
    )

    # preserve audit result shape and contract defaults
    assert "semantic_features" in result
    assert "debug_extraction" in result
    assert "timeline_analysis" in result
    assert "feature_ownership" in result
    assert "contributors" in result
    assert "hotspots" in result
    assert "insights" in result
    assert "causality" in result
    assert "optional_intelligence" in result
    assert "agent_findings" in result
    assert "audit_run_id" in result
    assert "provider" in result
    assert "generated_at" in result
    assert isinstance(result.get("timeline_analysis"), list)
    assert isinstance(result.get("feature_ownership"), list)
