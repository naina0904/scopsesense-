from datetime import datetime

from backend.integrations.github.github_adapter import (
    GitHubAdapter
)

from backend.integrations.jira.jira_adapter import (
    JiraAdapter
)

from backend.core.context_builder import (
    ContextBuilder
)

from backend.semantic.mapper import (
    SemanticMapper
)

from backend.semantic.feature_engine import (
    FeatureIntelligenceEngine
)

from backend.semantic.contributor_engine import (
    ContributorIntelligenceEngine
)

from backend.semantic.requirement_matcher import (
    RequirementMatcher
)

from backend.semantic.confidence_engine import (
    ImplementationConfidenceEngine
)

from backend.semantic.drift_engine import (
    ArchitecturalDriftEngine
)

from backend.semantic.dependency_engine import (
    DependencyEngine
)

from backend.semantic.architecture_score_engine import (
    ArchitectureScoreEngine
)

from backend.prediction.risk_engine import (
    PredictiveRiskEngine
)

from backend.prediction.risk_propagation_engine import (
    RiskPropagationEngine
)

from backend.recommendation.remediation_engine import (
    RemediationEngine
)

from backend.agents.risk_investigator import (
    RiskInvestigatorAgent
)

from backend.agents.architecture_agent import (
    ArchitectureAgent
)

from backend.agents.contributor_agent import (
    ContributorAgent
)

from backend.agents.scalability_agent import (
    ScalabilityAgent
)

from backend.agents.planning_agent import (
    PlanningAgent
)

from backend.memory.repository_memory import (
    RepositoryMemory
)

from backend.srs.parser import (
    SRSParser
)

from backend.srs.extractor import (
    SRSFeatureExtractor,
    CATEGORY_SOFTWARE_FEATURE
)

from backend.intelligence.timeline_engine import (
    TimelineEngine
)

from backend.intelligence.feature_ownership_engine import (
    FeatureOwnershipEngine
)

from backend.intelligence.hotspot_engine import (
    HotspotEngine
)

from backend.intelligence.insight_narrative_engine import (
    InsightNarrativeEngine
)

from backend.semantic.causality_engine import (
    EngineeringCausalityEngine
)

from backend.llm.manager import (
    LLMManager
)

from backend.github.repo_cloner import (
    RepoCloner
)

from backend.semantic.code_parser import (
    CodeParser
)

from backend.semantic.code_chunker import (
    CodeChunker
)

from backend.semantic.embeddings import (
    EmbeddingEngine
)

from backend.semantic.vector_store import (
    VectorStore
)

from backend.storage.repositories import (

    AuditRepository,

    FeatureRepository,

    ContributorRepository
)


class AuditWorkflow:

    # =================================================
    # INIT
    # =================================================

    def __init__(

        self,

        provider="gemini"
    ):

        self.provider = provider

        # ---------------------------------------------
        # CORE ENGINES
        # ---------------------------------------------

        self.mapper = SemanticMapper()

        self.feature_engine = (
            FeatureIntelligenceEngine()
        )

        self.contributor_engine = (
            ContributorIntelligenceEngine()
        )

        self.confidence_engine = (
            ImplementationConfidenceEngine()
        )

        self.drift_engine = (
            ArchitecturalDriftEngine()
        )

        self.dependency_engine = (
            DependencyEngine()
        )

        self.architecture_engine = (
            ArchitectureScoreEngine()
        )

        self.risk_engine = (
            PredictiveRiskEngine()
        )

        self.propagation_engine = (
            RiskPropagationEngine()
        )

        self.remediation_engine = (
            RemediationEngine()
        )

        # ---------------------------------------------
        # SEMANTIC INTELLIGENCE
        # ---------------------------------------------

        # ---------------------------------------------
        # LLM
        # ---------------------------------------------

        self.llm_manager = LLMManager(
            provider=provider
        )

        # ---------------------------------------------
        # SEMANTIC INTELLIGENCE
        # ---------------------------------------------

        self.timeline_engine = (
            TimelineEngine()
        )

        self.feature_ownership_engine = (
            FeatureOwnershipEngine()
        )

        self.hotspot_engine = (
            HotspotEngine()
        )

        self.insight_engine = (
            InsightNarrativeEngine(
                llm_manager=self.llm_manager
            )
        )

        self.causality_engine = (
            EngineeringCausalityEngine()
        )

        # ---------------------------------------------
        # AI AGENTS
        # ---------------------------------------------

        self.risk_agent = (
            RiskInvestigatorAgent(
                llm_manager=self.llm_manager
            )
        )

        self.architecture_agent = (
            ArchitectureAgent(
                llm_manager=self.llm_manager
            )
        )

        self.contributor_agent = (
            ContributorAgent(
                llm_manager=self.llm_manager
            )
        )

        self.scalability_agent = (
            ScalabilityAgent(
                llm_manager=self.llm_manager
            )
        )

        self.planning_agent = (
            PlanningAgent(
                llm_manager=self.llm_manager
            )
        )

        # ---------------------------------------------
        # MEMORY
        # ---------------------------------------------

        self.memory_engine = (
            RepositoryMemory()
        )

        # ---------------------------------------------
        # REPOSITORY INTELLIGENCE
        # ---------------------------------------------

        self.repo_cloner = (
            RepoCloner()
        )

        self.code_parser = (
            CodeParser()
        )

        self.chunker = (
            CodeChunker()
        )

        self.embedding_engine = (
            EmbeddingEngine()
        )

        self.vector_store = (
            VectorStore()
        )

        # ---------------------------------------------
        # SRS + REQUIREMENTS
        # ---------------------------------------------

        self.srs_parser = (
            SRSParser()
        )

        self.srs_extractor = (
            SRSFeatureExtractor(
                llm_manager=self.llm_manager
            )
        )

        self.requirement_matcher = (
            RequirementMatcher(

                self.vector_store,

                self.embedding_engine
            )
        )

        # ---------------------------------------------
        # DATABASE
        # ---------------------------------------------

        self.audit_repository = (
            AuditRepository()
        )

        self.feature_repository = (
            FeatureRepository()
        )

        self.contributor_repository = (
            ContributorRepository()
        )

    # =================================================
    # EXECUTE AUDIT
    # =================================================

    def execute_audit(

        self,

        repository_context,

        srs_path=None,

        provider=None,

        audit_run_id=None
    ):

        result = {

            "semantic_features":
                [],

            "timeline_analysis":
                [],

            "contributors":
                [],

            "feature_ownership":
                [],

            "hotspots":
                [],

            "insights":
                [],

            "causality":
                {},

            "optional_intelligence":
                {},

            "agent_findings":
                {},

            "audit_run_id":
                audit_run_id,

            "provider":
                provider or self.provider,

            "generated_at":
                str(datetime.utcnow())
        }
        
        # Sprint 3A: Cross-Platform Correlation
        jira_data = repository_context.get("jira_platform_data")
        github_data = repository_context.get("github_platform_data")
        
        if jira_data and github_data:
            from backend.hierarchy.cross_platform_mapper import CrossPlatformMapper
            unified_nodes = CrossPlatformMapper.correlate_platforms(jira_data, github_data)
            repository_context["unified_hierarchy_nodes"] = unified_nodes

        # ---------------------------------------------
        # PARSE SRS
        # ---------------------------------------------

        if srs_path:

            parsed_srs = (

                self.srs_parser.parse(
                    srs_path
                )
            )

            extracted_features = (

                self.srs_extractor.extract_features(

                    parsed_srs[
                        "raw_content"
                    ]
                )
            )

            result[
                "semantic_features"
            ] = extracted_features

            classification_info = self.srs_extractor.debug_info.get("classification", {})
            result["debug_extraction"] = {
                "requested_provider": self.srs_extractor.debug_info.get("requested_provider"),
                "successful_provider": self.srs_extractor.debug_info.get("successful_provider"),
                "provider_used": self.srs_extractor.debug_info.get("provider_used"),
                "provider_fallbacks": self.srs_extractor.debug_info.get("provider_fallbacks", []),
                "provider_latency_ms": self.srs_extractor.debug_info.get("provider_latency_ms", {}),
                "fallback_extraction_used": self.srs_extractor.debug_info.get("fallback_extraction_used", False),
                "raw_feature_names_before_normalization": self.srs_extractor.debug_info.get("raw_feature_names_before_normalization", [])[:5],
                "classification": {
                    "category_counts": classification_info.get("category_counts", {}),
                    "kept_count": classification_info.get("kept_count", 0),
                    "filtered_count": classification_info.get("filtered_count", 0),
                    "sample_classifications": classification_info.get("sample_classifications", [])
                }
            }

            # Surface any LLM extraction errors for observability and UI reporting
            if hasattr(self.srs_extractor, "last_llm_error") and self.srs_extractor.last_llm_error:
                result.setdefault("optional_intelligence", {})
                result["optional_intelligence"]["llm_error"] = {
                    "error": self.srs_extractor.last_llm_error,
                    "provider_attempts": getattr(self.srs_extractor, "last_llm_provider_attempts", None)
                }

        else:

            extracted_features = []

        # ---------------------------------------------
        # CONTRIBUTOR ANALYSIS
        # ---------------------------------------------

        try:
            software_feats = [
                f for f in extracted_features
                if self.srs_extractor._classify_feature(f) == CATEGORY_SOFTWARE_FEATURE
            ]
        except Exception:
            # Fallback: if classification routine is unavailable, keep original list
            software_feats = extracted_features

        # ---------------------------------------------
        # PROJECT COHERENCE VALIDATION
        # ---------------------------------------------
        from backend.config.settings import settings
        if settings.ENABLE_PROJECT_COHERENCE:
            from backend.coherence.project_coherence_validator import ProjectCoherenceValidator
            
            # Extract platform data from context
            jira_pdata = repository_context.get("jira_platform_data")
            github_pdata = repository_context.get("github_platform_data")
            pdata = jira_pdata or github_pdata
            
            validator = ProjectCoherenceValidator()
            coherence_result = validator.validate(extracted_features, pdata)
            
            # Save coherence result as supplementary data
            result["coherence"] = coherence_result

        # ---------------------------------------------
        # IDENTITY RESOLUTION ENGINE
        # ---------------------------------------------
        if getattr(settings, "ENABLE_IDENTITY_RESOLUTION", False):
            from backend.identity.identity_resolution_engine import IdentityResolutionEngine
            
            source_identities = []
            
            # Extract from SRS
            for f in extracted_features:
                for dev in f.get("assigned_developers", []):
                    source_identities.append({"identity": dev, "source": "SRS"})
                    
            # Extract from Jira/GitHub platform data
            jira_pdata = repository_context.get("jira_platform_data")
            github_pdata = repository_context.get("github_platform_data")
            
            for pdata in [jira_pdata, github_pdata]:
                if not pdata:
                    continue
                src_name = "Jira" if pdata is jira_pdata else "GitHub"
                for c in getattr(pdata, "contributors", []):
                    if getattr(c, "id", None):
                        source_identities.append({"identity": c.id, "source": src_name})
                    if getattr(c, "name", None):
                        source_identities.append({"identity": c.name, "source": src_name})
                
                for feature in getattr(pdata, "features", []):
                    if getattr(feature, "assigned_to", None):
                        source_identities.append({"identity": feature.assigned_to, "source": src_name})
                    for author in getattr(feature, "active_contributors", []):
                        source_identities.append({"identity": author, "source": src_name})
                        
            manual_aliases = {
                "Alice Smith": ["S2", "alice-smith99", "alice"],
                "Bob": ["S3", "bob-dev"]
            }
            ire = IdentityResolutionEngine(manual_aliases)
            identity_map = ire.resolve_identities(source_identities)
            
            result["identity_resolution"] = identity_map
            
            # Suppress False Ghost Authorship
            if github_pdata:
                for feature in github_pdata.features:
                    if feature.variance_detected and feature.variance_reason and "Ghost Authorship" in feature.variance_reason:
                        assigned = feature.assigned_to
                        authors = feature.active_contributors
                        if assigned and authors:
                            # If ANY active contributor resolves to the assigned user
                            for author in authors:
                                if ire.are_same_person(assigned, author, identity_map):
                                    feature.variance_detected = False
                                    explanation = ire.explain_resolution(assigned, author, identity_map)
                                    feature.variance_reason = explanation
                                    break

        result["semantic_features"] = software_feats

        contributor_context = {
            "contributors": repository_context.get("contributors", []),
            "activity": repository_context.get("activity", []),
            "features": software_feats
        }

        # Use filtered software features for downstream analysis wherever possible.
        # Preserve raw extracted features for debug and fallback when filtering removes all items.
        features_for_analysis = software_feats if software_feats else extracted_features

        contributor_analysis = (

            self.contributor_engine.analyze(

                contributor_context
            )
        )

        optional_results = (

            self._run_optional_intelligence(

                repository_context=
                    repository_context,

                extracted_features=
                    extracted_features,

                software_features=
                    features_for_analysis,

                contributor_analysis=
                    contributor_analysis
            )
        )

        ownership_analysis = (

            self.feature_ownership_engine.analyze(

                features=
                    features_for_analysis,

                activity=
                    repository_context.get(
                        "activity",
                        []
                    ),

                semantic_matches=
                    optional_results.get(
                        "semantic_matches"
                    )
            )
        )

        ownership_analysis = (

            self._augment_feature_ownership(

                ownership_analysis,

                repository_context.get(
                    "activity",
                    []
                )
            )
        )

        result[
            "feature_ownership"
        ] = ownership_analysis

        repository_start_date = (

            repository_context.get(
                "repository_start_date",
                datetime.utcnow()
            )
        )

        actual_completion_date = (

            repository_context.get(
                "latest_activity_date",
                datetime.utcnow()
            )
        )

        activity_gaps = (

            repository_context.get(
                "activity_gaps",
                []
            )
        )

        commit_velocity = (

            repository_context.get(
                "commit_velocity",
                "unknown"
            )
        )

        STRONG_OWNERSHIP_CONFIDENCE = 70

        timeline_results = []

        for feature in features_for_analysis:

            ownership_record = next(

                (
                    item
                    for item in ownership_analysis
                    if item.get(
                        "feature"
                    ) == feature.get(
                        "feature_name"
                    )
                ),

                None
            )

            feature_start_date = None
            feature_actual_completion_date = None
            feature_ownership_confidence = None

            if ownership_record:

                feature_ownership_confidence = (

                    ownership_record.get(
                        "ownership_confidence",
                        0
                    )
                )

                if (
                    feature_ownership_confidence >=
                    STRONG_OWNERSHIP_CONFIDENCE and
                    ownership_record.get(
                        "earliest_commit_timestamp"
                    ) and
                    ownership_record.get(
                        "latest_commit_timestamp"
                    )
                ):

                    feature_start_date = (

                        ownership_record[
                            "earliest_commit_timestamp"
                        ]
                    )

                    feature_actual_completion_date = (

                        ownership_record[
                            "latest_commit_timestamp"
                        ]
                    )

            schedule_details = self._resolve_feature_schedule(

                feature,

                repository_context
            )

            closed_at = None
            if schedule_details.get("matched_issue"):
                closed_at = (
                    schedule_details["matched_issue"].get(
                        "closed_at"
                    )
                )

            if (
                not feature_actual_completion_date and
                closed_at
            ):

                try:
                    feature_actual_completion_date = datetime.fromisoformat(
                        closed_at.replace("Z", "+00:00")
                    )
                except Exception:
                    feature_actual_completion_date = feature_actual_completion_date

            timeline_analysis = (

                self.timeline_engine
                .analyze_semantic_timeline(

                    feature_data=
                        feature,

                    repository_start_date=
                        repository_start_date,

                    actual_completion_date=
                        actual_completion_date,

                    activity_gaps=
                        activity_gaps,

                    commit_velocity=
                        commit_velocity,

                    feature_start_date=
                        feature_start_date,

                    feature_actual_completion_date=
                        feature_actual_completion_date,

                    feature_ownership_confidence=
                        feature_ownership_confidence,

                    planned_start_date=
                        schedule_details.get(
                            "planned_start_date"
                        ),

                    planned_completion_date=
                        schedule_details.get(
                            "planned_completion_date"
                        ),

                    schedule_source=
                        schedule_details.get(
                            "schedule_source"
                        ),

                    matched_issue=
                        schedule_details.get(
                            "matched_issue"
                        )
                )
            )

            timeline_results.append(
                timeline_analysis
            )

        result[
            "timeline_analysis"
        ] = timeline_results

        # ---------------------------------------------
        # HOTSPOT ANALYSIS
        # ---------------------------------------------

        hotspot_analysis = (

            self.hotspot_engine.analyze(

                feature_ownership=
                    ownership_analysis,

                timeline_analysis=
                    timeline_results
            )
        )

        result[
            "hotspots"
        ] = hotspot_analysis

        # ---------------------------------------------
        # CAUSALITY ANALYSIS
        # ---------------------------------------------

        causality_results = []

        for timeline in timeline_results:

            causality = (

                self.causality_engine.analyze(

                    timeline_analysis=
                        timeline,

                    contributor_analysis=
                        contributor_analysis
                )
            )

            causality_results.append(
                causality
            )

        result[
            "causality"
        ] = causality_results

        # ---------------------------------------------
        # INSIGHT NARRATIVES
        # ---------------------------------------------

        insight_analysis = (

            self.insight_engine.generate(

                hotspots=
                    hotspot_analysis,

                causality=
                    causality_results
            )
        )

        result[
            "insights"
        ] = insight_analysis

        self._annotate_explainability(

            result=result,

            repository_context=repository_context
        )

        # ---------------------------------------------
        # SEMANTIC TRACEABILITY
        # ---------------------------------------------
        if "feature_ownership" in features_to_run:
            from backend.intelligence.feature_ownership_engine import FeatureOwnershipEngine
            engine = FeatureOwnershipEngine()
            result["feature_ownership"] = engine.run(repository_context)

        # Sprint 4: Audit Findings Engine & Sprint 5: Audit Report Engine
        if "features" in repository_context:
            from backend.intelligence.audit_findings_engine import AuditFindingsEngine
            findings = AuditFindingsEngine.run(repository_context["features"])
            # The schema defines it as a dataclass, we dump to dict for JSON serialization
            import dataclasses
            result["agent_findings"] = [dataclasses.asdict(f) for f in findings]
            
            from backend.intelligence.audit_report_engine import AuditReportEngine
            report = AuditReportEngine.generate(findings)
            result["audit_report"] = dataclasses.asdict(report)

        # ---------------------------------------------
        # OPTIONAL AGENTS / EXISTING ENGINES
        # ---------------------------------------------
        # Optional intelligence was computed earlier, before timeline analysis.

        result[
            "optional_intelligence"
        ] = optional_results

        for key, value in optional_results.items():

            result[key] = value

        # ---------------------------------------------
        # PROVIDER METADATA
        # ---------------------------------------------

        result[
            "provider_metadata"
        ] = {
            "requested_provider":
                getattr(self.llm_manager, "requested_provider", None),

            "selected_provider":
                getattr(self.llm_manager, "provider", None),

            "provider_used":
                getattr(self.llm_manager, "provider_used", None),

            "provider_fallbacks":
                getattr(self.llm_manager, "provider_fallbacks", []),

            "provider_latency_ms":
                getattr(self.llm_manager, "provider_latency_ms", {}),

            "provider_order":
                list(self.llm_manager.default_provider_order),

            "provider_statuses":
                self.llm_manager.get_provider_status(),

            "faqs_applicable":
                getattr(self.llm_manager, "provider_used", None) in [
                    "gemini",
                    "groq"
                ]
        }

        # ---------------------------------------------
        # AGENTS AS ADDITIVE FINDINGS ONLY
        # ---------------------------------------------

        result[
            "agent_findings"
        ] = self._run_agent_findings(

            contributor_analysis=
                contributor_analysis,

            optional_results=
                optional_results
        )

        # ---------------------------------------------
        # FRONTEND-COMPATIBLE SUMMARY FIELDS
        # ---------------------------------------------

        self._apply_frontend_adapter(
            result
        )

        return self._serialize_for_transport(
            result
        )

    # =================================================
    # EXPLAINABILITY
    # =================================================

    def _annotate_explainability(

        self,

        result,

        repository_context
    ):

        activity_gaps = repository_context.get(
            "activity_gaps",
            []
        )

        commit_velocity = repository_context.get(
            "commit_velocity",
            "unknown"
        )

        for timeline in result.get(
            "timeline_analysis",
            []
        ):

            timeline[
                "reasoning"
            ] = [

                "Timeline status is derived from estimated effort, developer capacity, completion date, activity gaps, and commit velocity."
            ]

            timeline[
                "evidence"
            ] = [

                {
                    "type":
                        "commit_velocity",

                    "value":
                        commit_velocity
                },

                {
                    "type":
                        "activity_gap_count",

                    "value":
                        len(activity_gaps)
                }
            ]

        for hotspot in result.get(
            "hotspots",
            []
        ):

            hotspot[
                "reasoning"
            ] = [

                "Hotspot score combines contributor spread, ownership confidence, timeline delay, activity gaps, and velocity."
            ]

            hotspot[
                "contributing_factors"
            ] = {

                "contributors":
                    len(
                        hotspot.get(
                            "contributors",
                            []
                        )
                    ),

                "matched_files":
                    len(
                        hotspot.get(
                            "matched_files",
                            []
                        )
                    ),

                "largest_activity_gap":
                    hotspot.get(
                        "largest_activity_gap",
                        0
                    ),

                "timeline_status":
                    hotspot.get(
                        "timeline_status"
                    ),

                "commit_velocity":
                    hotspot.get(
                        "commit_velocity"
                    )
            }

            hotspot[
                "evidence"
            ] = [

                {
                    "type":
                        "matched_files",

                    "value":
                        hotspot.get(
                            "matched_files",
                            []
                        )
                },

                {
                    "type":
                        "contributors",

                    "value":
                        hotspot.get(
                            "contributors",
                            []
                        )
                }
            ]

    def _resolve_feature_schedule(

        self,

        feature,

        repository_context
    ):

        planned_start_date = None
        planned_completion_date = None
        schedule_source = None
        matched_issue = None

        def normalize_text(value):
            if not isinstance(value, str):
                return ""
            return value.strip().lower()

        def parse_date(value):
            if not value or not isinstance(value, str):
                return None

            candidate = value.strip()

            try:
                return datetime.fromisoformat(
                    candidate.replace("Z", "+00:00")
                )
            except Exception:
                pass

            for fmt in ["%d/%m/%Y", "%d.%m.%Y"]:
                try:
                    return datetime.strptime(
                        candidate,
                        fmt
                    )
                except Exception:
                    continue

            return None

        feature_name = normalize_text(
            feature.get("feature_name", "")
        )
        feature_milestone = normalize_text(
            feature.get("milestone", "")
        )
        feature_timeline = feature.get("timeline")

        issues = repository_context.get("issues", []) or []
        milestones = repository_context.get("milestones", []) or []

        if feature_milestone:
            for milestone in milestones:
                if normalize_text(milestone.get("title")) == feature_milestone:
                    planned_completion_date = (
                        parse_date(
                            milestone.get("due_on")
                        )
                    )
                    schedule_source = "github_milestone"

                    for issue in issues:
                        issue_milestone = issue.get("milestone") or {}
                        if (
                            normalize_text(issue.get("title")) == feature_name
                            or normalize_text(issue_milestone.get("title")) == feature_milestone
                        ):
                            matched_issue = issue
                            break
                    break

        if not planned_completion_date:
            for issue in issues:
                issue_title = normalize_text(issue.get("title"))
                issue_milestone = issue.get("milestone") or {}
                if (
                    feature_milestone and
                    normalize_text(issue_milestone.get("title")) == feature_milestone
                ) or (
                    feature_name and
                    feature_name in issue_title
                ):
                    due_date = parse_date(
                        issue_milestone.get("due_on")
                    )
                    if due_date:
                        planned_completion_date = due_date
                        schedule_source = "github_milestone"
                        matched_issue = issue
                        break
                    matched_issue = issue

        if not planned_completion_date and isinstance(feature_timeline, str):
            planned_completion_date = (
                parse_date(
                    feature_timeline
                )
            )
            if planned_completion_date:
                schedule_source = "srs_timeline"

        if not planned_completion_date and feature_timeline:
            schedule_source = schedule_source or "estimated_effort"

        return {
            "planned_start_date": planned_start_date,
            "planned_completion_date": planned_completion_date,
            "schedule_source": schedule_source,
            "matched_issue": matched_issue,
        }

    # =================================================
    # OPTIONAL INTELLIGENCE
    # =================================================

    def _run_optional_intelligence(

        self,

        repository_context,

        extracted_features,

        software_features,

        contributor_analysis
    ):

        optional = {

            "implementation_analysis":
                [],

            "semantic_matches":
                [],

            "architectural_drift":
                [],

            "dependencies":
                [],

            "architecture_scores":
                {},

            "predictive_risks":
                [],

            "risk_propagation":
                [],

            "recommendations":
                []
        }

        requirements = [

            feature.get(
                "feature_name",
                ""
            )

            for feature in (
                software_features
                if software_features
                else extracted_features
            )

            if feature.get(
                "feature_name"
            )
        ]

        repo_path = repository_context.get(
            "repo_path"
        )

        vector_namespace = repository_context.get(
            "vector_namespace",
            "default"
        )

        # These engines are intentionally additive. If repository
        # files or vector state are unavailable, the canonical
        # semantic spine still completes unchanged.
        try:

            if repo_path:

                print(
                    f"\n[AuditWorkflow] >>> RUNNING OPTIONAL SEMANTIC PIPELINE <<<"
                    f"\n  - repo_path: {repo_path}"
                    f"\n  - vector_namespace: {vector_namespace}"
                )

                documents = (

                    self.code_parser
                    .parse_repository(
                        repo_path
                    )
                )

                chunks = (

                    self.chunker
                    .chunk_documents(
                        documents
                    )
                )

                if chunks:

                    self.vector_store.index_code_chunks(

                        chunks,

                        self.embedding_engine,

                        namespace=vector_namespace
                    )

                if requirements:

                    matches = (

                        self.requirement_matcher
                        .match_requirements(
                            requirements,

                            namespace=vector_namespace
                        )
                    )

                    optional["semantic_matches"] = matches

                    optional[
                        "implementation_analysis"
                    ] = (

                        self.confidence_engine
                        .evaluate(
                            matches
                        )
                    )

                print("[AuditWorkflow] DependencyEngine starting analysis...")
                optional[
                    "dependencies"
                ] = (

                    self.dependency_engine
                    .analyze_repository(
                        repo_path
                    )
                )
                print(
                    f"[AuditWorkflow] DependencyEngine analysis complete. "
                    f"Analyzed {len(optional['dependencies'])} import edges."
                )

                print("[AuditWorkflow] ArchitectureScoreEngine starting evaluation...")
                optional[
                    "architecture_scores"
                ] = (

                    self.architecture_engine
                    .evaluate(
                        optional[
                            "dependencies"
                        ]
                    )
                )
                print(
                    f"[AuditWorkflow] ArchitectureScoreEngine evaluation complete. "
                    f"Architecture Score: {optional['architecture_scores'].get('score', 0)}"
                )

        except Exception as e:

            optional[
                "optional_engine_error"
            ] = str(e)

        try:

            if requirements:

                optional[
                    "architectural_drift"
                ] = (

                    self.drift_engine
                    .analyze(

                        requirements,

                        optional[
                            "implementation_analysis"
                        ]
                    )
                )

            optional[
                "predictive_risks"
            ] = (

                self.risk_engine
                .analyze(

                    optional[
                        "implementation_analysis"
                    ],

                    contributor_analysis,

                    optional[
                        "architectural_drift"
                    ]
                )
            )

            optional[
                "risk_propagation"
            ] = (

                self.propagation_engine
                .analyze(

                    optional[
                        "dependencies"
                    ],

                    optional[
                        "predictive_risks"
                    ]
                )
            )

            optional[
                "recommendations"
            ] = (

                self.remediation_engine
                .generate(

                    optional[
                        "predictive_risks"
                    ],

                    optional[
                        "architecture_scores"
                    ]
                )
            )

        except Exception as e:

            optional[
                "risk_engine_error"
            ] = str(e)

        return optional

    # =================================================
    # AGENT FINDINGS
    # =================================================

    def _run_agent_findings(

        self,

        contributor_analysis,

        optional_results
    ):

        findings = {}

        dependencies = optional_results.get(
            "dependencies",
            []
        )

        architecture_scores = optional_results.get(
            "architecture_scores",
            {}
        )

        predictive_risks = optional_results.get(
            "predictive_risks",
            []
        )

        recommendations = optional_results.get(
            "recommendations",
            []
        )

        try:

            findings[
                "architecture"
            ] = self.architecture_agent.analyze(

                architecture_scores,

                dependencies
            )

            findings[
                "contributors"
            ] = self.contributor_agent.analyze(
                contributor_analysis
            )

            findings[
                "risk_investigation"
            ] = self.risk_agent.investigate(

                predictive_risks,

                dependencies,

                architecture_scores
            )

            findings[
                "scalability"
            ] = self.scalability_agent.analyze(

                dependencies,

                architecture_scores
            )

            findings[
                "planning"
            ] = self.planning_agent.generate_plan(

                predictive_risks,

                recommendations,

                architecture_scores
            )

            findings[
                "evidence_context"
            ] = {

                "dependency_count":
                    len(dependencies),

                "predictive_risk_count":
                    len(predictive_risks),

                "recommendation_count":
                    len(recommendations),

                "contributor_count":
                    len(contributor_analysis),

                "architecture_scores":
                    architecture_scores
            }

        except Exception as e:

            findings[
                "agent_error"
            ] = str(e)

        return findings

    # =================================================
    # FRONTEND ADAPTER
    # =================================================

    def _apply_frontend_adapter(

        self,

        result
    ):

        hotspots = result.get(
            "hotspots",
            []
        )

        risks = result.get(
            "predictive_risks",
            []
        )

        critical_hotspots = len([

            item

            for item in hotspots

            if item.get(
                "risk_level"
            ) in [
                "critical",
                "high"
            ]
        ])

        result[
            "health_score"
        ] = max(
            0,
            100 - (critical_hotspots * 15) - (len(risks) * 5)
        )

        implementation = result.get(
            "implementation_analysis",
            []
        )

        if implementation:

            result[
                "semantic_confidence"
            ] = round(

                sum(

                    item.get(
                        "confidence",
                        0
                    )

                    for item in implementation
                )
                / len(implementation),

                2
            )

        else:

            ownership = result.get(
                "feature_ownership",
                []
            )

            if ownership:

                result[
                    "semantic_confidence"
                ] = round(

                    sum(

                        item.get(
                            "ownership_confidence",
                            0
                        )

                        for item in ownership
                    )
                    / len(ownership),

                    2
                )

            else:

                result[
                    "semantic_confidence"
                ] = 0

        insights = result.get(
            "insights",
            []
        )

        result[
            "ai_summary"
        ] = "\n".join([

            item.get(
                "narrative",
                ""
            )

            for item in insights
        ])

    def _augment_feature_ownership(

        self,

        ownership_results,

        activity
    ):

        normalized_activity = []

        for entry in activity:

            normalized_activity.append({
                "timestamp":
                    entry.get(
                        "timestamp"
                    ),
                "author":
                    entry.get(
                        "author"
                    ),
                "message":
                    entry.get(
                        "message",
                        ""
                    ),
                "files": [
                    file_path.replace(
                        "\\",
                        "/"
                    ).lower()
                    for file_path in entry.get(
                        "files",
                        []
                    )
                ]
            })

        for ownership in ownership_results:

            matched_files = [
                file_path.replace(
                    "\\",
                    "/"
                ).lower()
                for file_path in ownership.get(
                    "matched_files",
                    []
                )
            ]

            matched_commits = []

            for entry in normalized_activity:

                if not entry.get(
                    "timestamp"
                ):

                    continue

                if any(
                    normalized_file == git_file
                    or git_file.endswith(
                        normalized_file
                    )
                    for normalized_file in matched_files
                    for git_file in entry["files"]
                ):

                    matched_commits.append({
                        "author":
                            entry["author"],
                        "timestamp":
                            entry["timestamp"],
                        "message":
                            entry["message"],
                        "files":
                            entry["files"]
                    })

            ownership[
                "matched_commits"
            ] = matched_commits

            if matched_commits:

                timestamps = [
                    commit["timestamp"]
                    for commit in matched_commits
                    if commit.get(
                        "timestamp"
                    )
                ]

                ownership[
                    "earliest_commit_timestamp"
                ] = min(timestamps)

                ownership[
                    "latest_commit_timestamp"
                ] = max(timestamps)

            else:

                ownership[
                    "earliest_commit_timestamp"
                ] = None

                ownership[
                    "latest_commit_timestamp"
                ] = None

        return ownership_results

    # =================================================
    # SERIALIZATION
    # =================================================

    def _serialize_for_transport(

        self,

        value
    ):

        if isinstance(
            value,
            datetime
        ):

            return value.isoformat()

        if isinstance(
            value,
            list
        ):

            return [

                self._serialize_for_transport(
                    item
                )

                for item in value
            ]

        if isinstance(
            value,
            dict
        ):

            return {

                key:
                    self._serialize_for_transport(
                        item
                    )

                for key, item in value.items()
            }

        return value
