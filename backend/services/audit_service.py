import base64
import copy
import json
import re
import uuid
import os
import shutil

from datetime import (
    datetime,
    date,
    timezone
)


class _SafeEncoder(json.JSONEncoder):
    """Handles datetime and bytes so audit result persists cleanly."""

    def default(self, obj):

        if isinstance(obj, (datetime, date)):
            return obj.isoformat()

        if isinstance(obj, bytes):
            return base64.b64encode(obj).decode("utf-8")

        try:
            return super().default(obj)
        except TypeError:
            return str(obj)

from backend.config.settings import (
    settings
)

from backend.intelligence.repository_profiler import (
    RepositoryProfiler
)

from backend.core.audit_workflow import (
    AuditWorkflow
)

from backend.github.client import (
    GitHubClient
)

from backend.github.repo_cloner import (
    RepoCloner
)

from backend.execution.state_machine import (
    AuditStage
)

from backend.websocket.progress_manager import (
    progress_manager
)

from backend.storage.repositories import (
    AuditRepository
)


class AuditService:

    # =================================================
    # INIT
    # =================================================

    def __init__(self):

        self.profiler = (

            RepositoryProfiler(

                github_token=
                    settings.GITHUB_TOKEN
            )
        )

        # NOTE: AuditWorkflow is instantiated per-call in
        # execute_full_audit so the provider arg is respected.
        # Do NOT store a shared instance here.

        self.github_client = (
            GitHubClient()
        )

        self.repo_cloner = (
            RepoCloner()
        )

        self.audit_repository = (
            AuditRepository()
        )

    # =================================================
    # CREATE TASK ID
    # =================================================

    def create_task_id(self):

        return str(
            uuid.uuid4()
        )

    # =================================================
    # UPDATE PROGRESS
    # =================================================

    def update_progress(

        self,

        task_id,

        stage,

        percentage,

        log_message=None
    ):

        progress_manager.update(

            task_id=
                task_id,

            stage=
                stage,

            percentage=
                percentage
        )

        if log_message:

            progress_manager.add_log(

                task_id=
                    task_id,

                message=
                    log_message
            )

    # =================================================
    # DIRECT REPOSITORY PROFILE
    # =================================================

    def execute_repository_audit(

        self,

        owner,

        repo
    ):

        task_id = self.create_task_id()

        try:

            # -----------------------------------------
            # INITIALIZING
            # -----------------------------------------

            self.update_progress(

                task_id,

                AuditStage.INITIALIZING,

                5,

                "Initializing repository audit"
            )

            # -----------------------------------------
            # FETCHING GITHUB
            # -----------------------------------------

            self.update_progress(

                task_id,

                AuditStage.FETCHING_GITHUB,

                20,

                "Fetching repository metadata"
            )

            # -----------------------------------------
            # ANALYZING
            # -----------------------------------------

            self.update_progress(

                task_id,

                AuditStage.ANALYZING,

                50,

                "Running intelligence analysis"
            )

            result = (

                self.profiler
                .profile_repository(

                    owner=owner,

                    repo=repo
                )
            )

            # -----------------------------------------
            # GENERATING REPORT
            # -----------------------------------------

            self.update_progress(

                task_id,

                AuditStage.GENERATING_REPORT,

                90,

                "Generating executive insights"
            )

            # -----------------------------------------
            # COMPLETED
            # -----------------------------------------

            self.update_progress(

                task_id,

                AuditStage.COMPLETED,

                100,

                "Audit completed successfully"
            )

            return {

                "task_id":
                    task_id,

                "result":
                    result
            }

        except Exception as e:

            self.update_progress(

                task_id,

                AuditStage.FAILED,

                100,

                str(e)
            )

            raise e

    # =================================================
    # FULL AUDIT WORKFLOW
    # =================================================

    def execute_full_audit(

        self,

        github_owner,

        github_repo,

        provider,

        srs_path,

        audit_run_id=None
    ):

        task_id = (
            audit_run_id
            or self.create_task_id()
        )


        repo_path_to_cleanup = None

        try:

            # -----------------------------------------
            # INITIALIZING
            # -----------------------------------------

            self.update_progress(

                task_id,

                AuditStage.INITIALIZING,

                5,

                "Initializing full audit workflow"
            )

            # -----------------------------------------
            # PARSING SRS
            # -----------------------------------------

            self.update_progress(

                task_id,

                AuditStage.PARSING_SRS,

                25,

                "Parsing SRS document"
            )

            repository_context = (

                self._build_repository_context(

                    github_owner,

                    github_repo
                )
            )

            # Extract repo_path for cleanup in finally block
            repo_path_to_cleanup = repository_context.get("repo_path")

            # -----------------------------------------
            # SEMANTIC MAPPING
            # -----------------------------------------

            self.update_progress(

                task_id,

                AuditStage.SEMANTIC_MAPPING,

                50,

                "Running semantic intelligence"
            )

            workflow = AuditWorkflow(
                provider=provider
            )

            results = (

                workflow
                .execute_audit(

                    repository_context=
                        repository_context,

                    srs_path=
                        srs_path,

                    provider=
                        provider,

                    audit_run_id=
                        task_id
                )
            )

            # -----------------------------------------
            # GENERATING REPORT
            # -----------------------------------------

            self.update_progress(

                task_id,

                AuditStage.GENERATING_REPORT,

                90,

                "Generating final audit report"
            )

            self._persist_audit_result(

                owner=github_owner,

                repo=github_repo,

                task_id=task_id,

                result=results,

                workflow=workflow
            )

            progress_manager.set_result(

                task_id,

                {

                    "task_id":
                        task_id,

                    "result":
                        results
                }
            )

            # -----------------------------------------
            # COMPLETED
            # -----------------------------------------

            self.update_progress(

                task_id,

                AuditStage.COMPLETED,

                100,

                "Full audit completed"
            )

            return {

                "task_id":
                    task_id,

                "result":
                    results
            }

        except Exception as e:

            self.update_progress(

                task_id,

                AuditStage.FAILED,

                100,

                str(e)
            )

            raise e

        finally:

            # ─────────────────────────────────────────
            # CLEANUP WORKSPACE REPOSITORY
            # ─────────────────────────────────────────
            # Deletes the cloned repository workspace
            # directory to avoid piling up MBs of temp
            # repositories on the worker disk.
            # ─────────────────────────────────────────
            if repo_path_to_cleanup and os.path.exists(repo_path_to_cleanup):

                try:

                    shutil.rmtree(repo_path_to_cleanup)

                    print(
                        f"[AuditService] Cleaned up cloned repository path: "
                        f"{repo_path_to_cleanup}"
                    )

                except Exception as cleanup_err:

                    print(
                        f"[AuditService] Failed to clean up path "
                        f"{repo_path_to_cleanup}: {cleanup_err}"
                    )
    # GET TASK PROGRESS
    # =================================================

    def get_task_progress(

        self,

        task_id
    ):

        return (

            progress_manager
            .get_progress(
                task_id
            )
        )

    # =================================================
    # BUILD REPOSITORY CONTEXT
    # =================================================

    def _build_repository_context(

        self,

        owner,

        repo
    ):

        # -------------------------------------------------
        # SEMANTIC CODE INDEXING — REPOSITORY CLONE
        # -------------------------------------------------
        # Clone the repository to a local workspace path so
        # that CodeParser, CodeChunker, EmbeddingEngine, and
        # VectorStore can index source files and perform
        # SRS-to-code matching.
        #
        # If cloning fails (private repo without token,
        # network error, disk issue) repo_path is set to
        # None and the audit falls back gracefully to
        # metadata-only mode — all existing intelligence
        # (timeline, hotspot, narrative, etc.) is unaffected.
        # -------------------------------------------------

        repo_path = None

        try:

            # Build the authenticated HTTPS clone URL.
            # If GITHUB_TOKEN is set, embed it so private
            # repositories are accessible.
            token = getattr(settings, "GITHUB_TOKEN", "") or ""

            if token:

                clone_url = (
                    f"https://{token}@github.com/"
                    f"{owner}/{repo}.git"
                )

            else:

                clone_url = (
                    f"https://github.com/"
                    f"{owner}/{repo}.git"
                )

            repo_name = f"{owner}_{repo}"

            repo_path = (

                self.repo_cloner
                .clone_repository(
                    clone_url,
                    repo_name
                )
            )

        except Exception as clone_err:

            print(
                f"[AuditService] Repository clone skipped "
                f"({owner}/{repo}): {clone_err}. "
                "Continuing with metadata-only intelligence."
            )

            repo_path = None

        # -------------------------------------------------
        # GITHUB METADATA
        # -------------------------------------------------

        commits = (

            self.github_client
            .get_commits(
                owner,
                repo
            )
        )

        contributors = {}

        activity = []

        commit_dates = []

        for commit in commits:

            author = (
                commit.get(
                    "author"
                )
                or "Unknown"
            )

            if author not in contributors:

                contributors[author] = {

                    "name":
                        author,

                    "total_commits":
                        0
                }

            contributors[
                author
            ][
                "total_commits"
            ] += 1

            parsed_date = self._parse_commit_date(
                commit.get(
                    "date"
                )
            )

            if parsed_date:

                commit_dates.append(
                    parsed_date
                )

            activity.append({

                "author":
                    author,

                "timestamp":
                    parsed_date,

                "message":
                    commit.get(
                        "message",
                        ""
                    ),

                "files":
                    commit.get(
                        "files",
                        []
                    )
            })

        activity = sorted(

            activity,

            key=lambda item:
                item.get(
                    "timestamp"
                )
                or datetime.min.replace(
                    tzinfo=timezone.utc
                )
        )

        issues = self.github_client.get_issues(
            owner,
            repo,
            state="all"
        )

        milestones = self.github_client.get_milestones(
            owner,
            repo,
            state="all"
        )

        return {

            "contributors":
                list(
                    contributors.values()
                ),

            "activity":
                activity,

            "repository_start_date":
                min(commit_dates)
                if commit_dates
                else datetime.utcnow(),

            "latest_activity_date":
                max(commit_dates)
                if commit_dates
                else datetime.utcnow(),

            "activity_gaps":
                self._activity_gaps(
                    activity
                ),

            "commit_velocity":
                self._commit_velocity(
                    commit_dates
                ),

            "issues":
                issues,

            "milestones":
                milestones,

            "vector_namespace":
                f"{owner}_{repo}",

            # -----------------------------------------
            # SEMANTIC CODE INDEXING ENTRY POINT
            # -----------------------------------------
            # repo_path is consumed by _run_optional_intelligence()
            # in AuditWorkflow to activate CodeParser, CodeChunker,
            # EmbeddingEngine, VectorStore, and RequirementMatcher.
            # None here means the `if repo_path:` guard in
            # _run_optional_intelligence() falls back to metadata-only.
            # -----------------------------------------
            "repo_path":
                repo_path
        }

    # =================================================
    # DATE + ACTIVITY HELPERS
    # =================================================

    def _parse_commit_date(

        self,

        value
    ):

        if not value:

            return None

        try:

            return datetime.fromisoformat(

                value.replace(
                    "Z",
                    "+00:00"
                )
            )

        except Exception:

            return None

    def _activity_gaps(

        self,

        activity
    ):

        dated_activity = [

            item

            for item in activity

            if item.get(
                "timestamp"
            )
        ]

        gaps = []

        for idx in range(
            1,
            len(dated_activity)
        ):

            previous = dated_activity[
                idx - 1
            ]

            current = dated_activity[idx]

            delta = (

                current["timestamp"]
                -
                previous["timestamp"]
            )

            if delta.days >= 14:

                gaps.append({

                    "start":
                        previous[
                            "timestamp"
                        ],

                    "end":
                        current[
                            "timestamp"
                        ],

                    "gap_days":
                        delta.days,

                    "previous_commit":
                        previous.get(
                            "message",
                            ""
                        ),

                    "next_commit":
                        current.get(
                            "message",
                            ""
                        )
                })

        return gaps

    def _commit_velocity(

        self,

        commit_dates
    ):

        if len(commit_dates) <= 1:

            return "low"

        duration_days = max(

            1,

            (
                max(commit_dates)
                -
                min(commit_dates)
            ).days
        )

        commits_per_week = (

            len(commit_dates)
            /
            (duration_days / 7)
        )

        if commits_per_week >= 5:

            return "high"

        if commits_per_week >= 2:

            return "moderate"

        return "low"

    # =================================================
    # =================================================
    # SEMANTIC INTEGRITY VALIDATION
    # =================================================

    def _validate_semantic_integrity(self, result: dict):
        """
        Prevents binary payload corruption (e.g. from DOCX/ZIP misinterpreted as text)
        from polluting the PostgreSQL database.

        NOTE: Only validates individual feature_name values — NOT the full JSON dump.
        Scanning the full dump would false-positive on any repository that legitimately
        processes Office/ZIP files (e.g. a repo with docx parsing utilities).
        """
        ZIP_BINARY_HEADER = "PK\x03\x04"

        for feature in result.get("semantic_features", []):
            name = feature.get("feature_name", "")

            # Block names that are clearly binary garbage (ZIP entry headers)
            if name.startswith(ZIP_BINARY_HEADER):
                raise ValueError(
                    "Semantic corruption detected: Feature name starts with ZIP binary header"
                )

            # Block names that are unreasonably long (binary blob leaked as text)
            if len(name) > 200:
                truncated_name = name[:200].rstrip()
                feature["feature_name"] = truncated_name

            cleaned_name = self._clean_semantic_feature_name(
                feature["feature_name"]
            )
            feature["feature_name"] = cleaned_name

    def _sanitize_semantic_features(self, features):
        if not isinstance(features, list):
            return features

        cleaned_features = []
        for feature in features:
            if not isinstance(feature, dict):
                continue

            name = feature.get("feature_name", "")
            cleaned_name = self._clean_semantic_feature_name(name)
            feature["feature_name"] = cleaned_name

            if self._is_noisy_feature_name(cleaned_name):
                continue

            cleaned_features.append(feature)

        return cleaned_features

    def _clean_semantic_feature_name(self, name: str) -> str:
        if not isinstance(name, str):
            return name

        cleaned = name.strip()
        if not cleaned:
            return cleaned

        cleaned = re.sub(r"\s+", " ", cleaned)
        cleaned = re.sub(
            r"^(feature|module|requirement|capability|section|page)[:\-\.\)]\s*",
            "",
            cleaned,
            flags=re.I,
        )

        if any(separator in cleaned for separator in ["•", "||", "| |", " - "]):
            segments = re.split(r"\s*•\s*|\s*\|\|\s*|\s*\|\s*\|\s*|\s*-\s*", cleaned)
            segments = [seg.strip(" .,:;\n\r") for seg in segments if seg.strip()]
            if segments:
                plausible = [seg for seg in segments if len(seg) >= 8]
                cleaned = max(plausible, key=len) if plausible else segments[0]

        if ":" in cleaned:
            left, right = [part.strip() for part in cleaned.split(":", 1)]
            if len(right) >= 8 and len(left) <= 60:
                cleaned = right
            else:
                cleaned = left

        cleaned = re.sub(r"\s+", " ", cleaned).strip(" .,:;")

        if len(cleaned) > 120:
            cleaned = cleaned[:120].rsplit(" ", 1)[0]

        return cleaned

    def _is_noisy_feature_name(self, name: str) -> bool:
        if not isinstance(name, str):
            return True

        trimmed = name.strip()
        if len(trimmed) < 4:
            return True

        lower = trimmed.lower()
        if lower in {
            "feature",
            "module",
            "requirement",
            "capability",
            "section",
            "details",
            "overview",
            "summary",
        }:
            return True

        if re.search(r"\b(summary|overview|background|notes|documentation|audit trail|feature list|project modules|ui pages|requirement sections)\b", lower):
            return True

        return False

    def _sanitize_persisted_audit(self, result: dict) -> dict:
        """Return a persistence-safe copy with raw semantic match documents removed.
        
        Preserves debug_extraction and all diagnostic fields.
        Only removes raw document payloads from semantic_matches.
        """
        sanitized = copy.deepcopy(result)

        def remove_documents_from_matches(matches):
            if not isinstance(matches, list):
                return

            for item in matches:
                if not isinstance(item, dict):
                    continue
                matches_payload = item.get("matches")
                if isinstance(matches_payload, dict):
                    matches_payload.pop("documents", None)

        # Remove documents from semantic_matches (from optional_intelligence)
        remove_documents_from_matches(
            sanitized.get("optional_intelligence", {}).get("semantic_matches")
        )
        
        # Remove documents from root-level semantic_matches
        remove_documents_from_matches(sanitized.get("semantic_matches"))

        raw_semantic_features = copy.deepcopy(
            sanitized.get("semantic_features", [])
        )
        sanitized["_raw_semantic_features"] = raw_semantic_features
        sanitized["_raw_feature_count"] = len(raw_semantic_features)
        sanitized["_normalization_config_version"] = "1.0"
        sanitized["_normalization_applied_at_response"] = False

        # Keep semantic_features raw in storage.
        # Only derived collections should have normalized feature labels.
        for collection_name, key_name in [
            ("timeline_analysis", "feature"),
            ("feature_ownership", "feature"),
            ("hotspots", "feature"),
        ]:
            entries = sanitized.get(collection_name)
            if isinstance(entries, list):
                for entry in entries:
                    if isinstance(entry, dict) and key_name in entry:
                        entry[key_name] = self._clean_semantic_feature_name(
                            entry.get(key_name, "")
                        )

        # Preserve debug_extraction and all other fields
        # (they are safe diagnostic info with no raw document payloads)

        return sanitized

    # =================================================
    # PERSISTENCE
    # =================================================

    def _persist_audit_result(

        self,

        owner,

        repo,

        task_id,

        result,

        workflow=None
    ):

        self._validate_semantic_integrity(result)


        result[
            "repository"
        ] = repo

        result[
            "owner"
        ] = owner

        try:

            memory_engine = (
                workflow.memory_engine
                if workflow
                else None
            )

            if memory_engine:

                memory_engine.save_snapshot(

                    owner,

                    repo,

                    self._sanitize_persisted_audit(result)
                )

        except Exception as e:

            result[
                "memory_persistence_error"
            ] = str(e)

        try:

            self.audit_repository.save_audit(

                project_name=
                    f"{owner}/{repo}",

                health_score=
                    result.get(
                        "health_score",
                        0
                    ),

                semantic_confidence=
                    result.get(
                        "semantic_confidence",
                        0
                    ),

                ai_summary=
                    json.dumps(
                        self._sanitize_persisted_audit(result)
                    )
            )

        except Exception as e:

            result[
                "database_persistence_error"
            ] = str(e)
