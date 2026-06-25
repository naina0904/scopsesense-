"""
Semantic delay analysis engine.
Analyzes why a project is delayed without keyword mapping.
Works with any platform (GitHub, JIRA) via unified schema.
"""

from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from backend.observability.structured_logger import get_logger
import math
from enum import Enum

class InsufficientDataError(ValueError):
    """Raised when there is not enough data for meaningful analysis."""

from backend.integrations.core.unified_schema import (
    PlatformData,
    Feature,
    FeatureStatus,
    TimelineEvent,
    Contributor
)
from backend.semantic.embeddings import EmbeddingEngine

logger = get_logger(__name__)

class DelayCategory(Enum):
    """Categories of delays discovered."""
    UNASSIGNED_FEATURES = "unassigned_features"
    BLOCKED_FEATURES = "blocked_features"
    CONTRIBUTOR_OVERLOAD = "contributor_overload"
    INACTIVE_DEVELOPMENT = "inactive_development"
    MISSING_TIME_DATA = "missing_time_data"
    TIMELINE_MISALIGNMENT = "timeline_misalignment"
    SPRINT_SLIPPAGE = "sprint_slippage"
    DEVELOPER_TURNOVER = "developer_turnover"
    OWNERSHIP_TRANSFER = "ownership_transfer"

@dataclass
class DelayEvidence:
    """A single piece of delay evidence."""
    category: DelayCategory
    severity: float  # 0.0 to 1.0
    description: str
    affected_features: List[str] = field(default_factory=list)
    affected_contributors: List[str] = field(default_factory=list)
    timeline_markers: List[datetime] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class DelayAnalysisResult:
    """Complete delay analysis results."""
    project_key: str
    platform: str
    analysis_timestamp: datetime
    total_features: int
    completed_features: int
    in_progress_features: int
    blocked_features: int
    unassigned_features: int
    evidence: List[DelayEvidence] = field(default_factory=list)
    severity_score: float = 0.0  # Weighted average
    primary_causes: List[str] = field(default_factory=list)
    timeline_gaps: List[Tuple[datetime, datetime]] = field(default_factory=list)
    working_hours_breakdown: Dict[str, Any] = field(default_factory=dict)
    freshness_penalty_applied: bool = False
    freshness_penalty_factor: float = 1.0

class SemanticDelayAnalyzer:
    """
    Analyzes project delays semantically without keyword mapping.
    Uses patterns, timelines, contributor activity, and feature state.
    """
    
    # Configuration
    WORKING_HOURS_PER_WEEK = 40  # 5 days * 8 hours
    WORKING_HOURS_PER_DAY = 8
    INACTIVE_THRESHOLD_DAYS = 7  # No events for 7+ days = inactive
    CONTRIBUTOR_OVERLOAD_THRESHOLD = 15  # 15+ features per contributor
    
    def __init__(
        self,
        platform_data: PlatformData,
        srs_features: Optional[List[Dict[str, Any]]] = None,
        calendar_profile: Optional[Dict[str, Any]] = None,
        org_profile: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize analyzer.
        
        Args:
            platform_data: Unified platform data
            srs_features: Optional SRS feature list for comparison
            calendar_profile: Optional calendar data
            org_profile: Optional discovered usage intelligence profile (JUIL)
        """
        self.platform_data = platform_data
        self.srs_features = srs_features or []
        self.calendar_profile = calendar_profile or {}
        self.org_profile = org_profile or {}
        self.analysis_timestamp = datetime.utcnow()
        self.embedding_engine = EmbeddingEngine()
    
    def analyze(self) -> DelayAnalysisResult:
        """
        Perform comprehensive delay analysis.
        
        Returns:
            DelayAnalysisResult with evidence and causes
        """
        result = DelayAnalysisResult(
            project_key=self.platform_data.platform_key,
            platform=self.platform_data.platform.value,
            analysis_timestamp=self.analysis_timestamp,
            total_features=len(self.platform_data.features),
            completed_features=len(self.platform_data.get_features_by_status(FeatureStatus.DONE)),
            in_progress_features=len(self.platform_data.get_features_by_status(FeatureStatus.IN_PROGRESS)),
            blocked_features=len(self.platform_data.get_features_by_status(FeatureStatus.BLOCKED)),
            unassigned_features=len([f for f in self.platform_data.features if not f.assigned_to])
        )
        
        # Data Sufficiency Pre-flight Check (MISSING_TIME_DATA)
        if len(self.platform_data.features) == 0:
            raise InsufficientDataError("Insufficient platform data: no features were found for analysis.")

        # Freshness Penalty
        freshness_penalty_applied = False
        confidence_modifier = 1.0
        latest_event_time = None
        
        if self.platform_data.timeline_events:
            latest_event_time = max(e.timestamp for e in self.platform_data.timeline_events)
        
        if latest_event_time:
            time_since_last_event = self.analysis_timestamp - latest_event_time
            if time_since_last_event > timedelta(hours=24):
                freshness_penalty_applied = True
                confidence_modifier = 0.85

        # Run all analysis engines
        evidence = []
        evidence.extend(self._analyze_unassigned_features())
        evidence.extend(self._analyze_blocked_features())
        evidence.extend(self._analyze_contributor_overload())
        evidence.extend(self._analyze_development_gaps())
        evidence.extend(self._analyze_timeline_alignment())
        evidence.extend(self._analyze_sprint_slippage())
        evidence.extend(self._analyze_developer_turnover())
        evidence.extend(self._analyze_time_tracking_gaps())
        evidence.extend(self._analyze_ownership_transfers())
        
        # Apply freshness penalty to all evidence severities
        for e in evidence:
            e.severity = e.severity * confidence_modifier
            if freshness_penalty_applied:
                e.metadata["freshness_penalty_applied"] = True
                e.metadata["original_severity"] = e.severity / confidence_modifier
        
        result.evidence = evidence
        result.freshness_penalty_applied = freshness_penalty_applied
        result.freshness_penalty_factor = confidence_modifier
        
        # Calculate severity score (weighted)
        if evidence:
            total_severity = sum(e.severity for e in evidence)
            result.severity_score = min(1.0, total_severity / max(1, len(evidence)))
        
        # Extract primary causes (top 3 by severity)
        sorted_evidence = sorted(evidence, key=lambda e: e.severity, reverse=True)
        result.primary_causes = [e.category.value for e in sorted_evidence[:3]]
        
        # Calculate working hours impact (only if we have timeline data)
        if self.platform_data.timeline_events:
            result.working_hours_breakdown = self._calculate_working_hours()
        
        return result
    
    def _analyze_unassigned_features(self) -> List[DelayEvidence]:
        """Detect features without assignees, adaptive to JUIL anchors."""
        ownership_anchor = self.org_profile.get("ownership_anchor", {}).get("value")
        
        level_map = { "epic": 1, "story": 2, "task": 2, "bug": 2, "sub-task": 3, "subtask": 3 }
        anchor_level = level_map.get(ownership_anchor.lower() if ownership_anchor else "story", 1)
        
        unassigned = []
        for f in self.platform_data.features:
            if not f.assigned_to:
                issue_type = f.platform_specific.get("issue_type", "Unknown").lower()
                feature_level = level_map.get(issue_type, 3)
                
                # JUIL Findings Enrichment:
                if ownership_anchor and feature_level < anchor_level:
                    continue
                unassigned.append(f)
        
        if not unassigned:
            return []
        
        unassigned_count = len(unassigned)
        total = len(self.platform_data.features)
        severity = min(1.0, unassigned_count / max(1, total))
        
        return [DelayEvidence(
            category=DelayCategory.UNASSIGNED_FEATURES,
            severity=severity,
            description=f"{unassigned_count} features ({severity*100:.0f}%) have no assigned developer" + (f" (Organization Profile Rule Applied: {ownership_anchor} is the ownership anchor)" if ownership_anchor else ""),
            affected_features=[f.id for f in unassigned],
            metadata={"unassigned_count": unassigned_count, "percentage": severity*100, "juil_rule_applied": bool(ownership_anchor)}
        )]
    
    def _analyze_blocked_features(self) -> List[DelayEvidence]:
        """Detect blocked features and their duration."""
        blocked = self.platform_data.get_features_by_status(FeatureStatus.BLOCKED)
        
        if not blocked:
            return []

        
        evidence = []
        severity = min(1.0, len(blocked) / max(1, len(self.platform_data.features)))
        
        # Get when features became blocked (from timeline)
        for feature in blocked:
            events = self.platform_data.get_events_for_feature(feature.id)
            blocked_time = None
            
            for event in reversed(events):
                if "blocked" in event.description.lower():
                    blocked_time = event.timestamp
                    break
            
            duration_days = None
            if blocked_time:
                duration_days = (self.analysis_timestamp - blocked_time).days
            
            evidence.append(DelayEvidence(
                category=DelayCategory.BLOCKED_FEATURES,
                severity=severity,
                description=f"Feature '{feature.name}' is blocked" + (f" for {duration_days} days" if duration_days else ""),
                affected_features=[feature.id],
                timeline_markers=[blocked_time] if blocked_time else [],
                metadata={
                    "blocked_count": len(blocked),
                    "feature": feature.name,
                    "blocked_days": duration_days or "unknown"
                }
            ))
        
        return evidence
    
    def _analyze_contributor_overload(self) -> List[DelayEvidence]:
        """Detect contributors assigned to too many features."""
        evidence = []
        
        for contributor in self.platform_data.contributors:
            assigned_features = self.platform_data.get_features_by_contributor(contributor.id)
            
            if len(assigned_features) > self.CONTRIBUTOR_OVERLOAD_THRESHOLD:
                severity = min(1.0, len(assigned_features) / 30)  # 30+ is max severity
                
                evidence.append(DelayEvidence(
                    category=DelayCategory.CONTRIBUTOR_OVERLOAD,
                    severity=severity,
                    description=f"Developer '{contributor.name}' is overloaded with {len(assigned_features)} features",
                    affected_features=[f.id for f in assigned_features],
                    affected_contributors=[contributor.id],
                    metadata={
                        "contributor": contributor.name,
                        "feature_count": len(assigned_features),
                        "commits": contributor.commits_count
                    }
                ))
        
        return evidence
    
    def _analyze_development_gaps(self) -> List[DelayEvidence]:
        """Detect periods with no development activity."""
        if not self.platform_data.timeline_events:
            return []
        
        evidence = []
        
        # Sort events by timestamp
        sorted_events = sorted(self.platform_data.timeline_events, key=lambda e: e.timestamp)
        
        if len(sorted_events) < 2:
            return evidence
        
        # Find gaps between events
        gaps = []
        for i in range(len(sorted_events) - 1):
            current_event = sorted_events[i]
            next_event = sorted_events[i + 1]
            gap_days = (next_event.timestamp - current_event.timestamp).days
            
            if gap_days >= self.INACTIVE_THRESHOLD_DAYS:
                gaps.append((current_event.timestamp, next_event.timestamp, gap_days))
        
        if gaps:
            total_gap_days = sum(g[2] for g in gaps)
            severity = min(1.0, total_gap_days / 90)  # 90 days = max severity
            
            evidence.append(DelayEvidence(
                category=DelayCategory.INACTIVE_DEVELOPMENT,
                severity=severity,
                description=f"{len(gaps)} inactive periods detected, totaling {total_gap_days} days",
                timeline_markers=[g[0] for g in gaps],
                metadata={
                    "gap_count": len(gaps),
                    "total_gap_days": total_gap_days,
                    "gaps": [{"start": g[0].isoformat(), "end": g[1].isoformat(), "days": g[2]} for g in gaps]
                }
            ))
        
        return evidence
    
    def _analyze_timeline_alignment(self) -> List[DelayEvidence]:
        """Compare actual timeline against SRS promises."""
        if not self.srs_features:
            return []
        
        evidence = []
        
        # Match platform features to SRS features
        for srs_feature in self.srs_features:
            srs_name = srs_feature.get("name", "").lower()
            
            # Find matching platform feature (semantic similarity)
            platform_feature = self._find_matching_feature(srs_name)
            
            if not platform_feature:
                evidence.append(DelayEvidence(
                    category=DelayCategory.TIMELINE_MISALIGNMENT,
                    severity=0.7,
                    description=f"SRS feature '{srs_feature.get('name')}' not found in platform data",
                    metadata={"srs_feature": srs_feature.get("name")}
                ))
                continue
            
            # Check if due date was missed
            srs_due = srs_feature.get("due_date")
            platform_due = platform_feature.due_date
            
            if srs_due and platform_due:
                try:
                    srs_due_date = datetime.fromisoformat(srs_due) if isinstance(srs_due, str) else srs_due
                    if platform_due > srs_due_date and platform_feature.status != FeatureStatus.DONE:
                        delay_days = (platform_due - srs_due_date).days
                        severity = min(1.0, delay_days / 90)
                        
                        evidence.append(DelayEvidence(
                            category=DelayCategory.TIMELINE_MISALIGNMENT,
                            severity=severity,
                            description=f"Feature '{srs_feature.get('name')}' is {delay_days} days behind SRS due date",
                            affected_features=[platform_feature.id],
                            metadata={
                                "srs_due": srs_due,
                                "platform_due": platform_due.isoformat(),
                                "delay_days": delay_days
                            }
                        ))
                except:
                    pass
        
        return evidence
    
    def _analyze_sprint_slippage(self) -> List[DelayEvidence]:
        """Detect features that slipped from their sprints."""
        evidence = []
        
        for sprint in self.platform_data.sprints:
            if not sprint.end_date:
                continue
            
            # Check which features were supposed to be done in this sprint
            sprint_features = [f for f in self.platform_data.features if f.id in sprint.features]
            incomplete = [f for f in sprint_features if f.status != FeatureStatus.DONE]
            
            if incomplete and sprint.end_date < self.analysis_timestamp:
                severity = min(1.0, len(incomplete) / max(1, len(sprint_features)))
                
                evidence.append(DelayEvidence(
                    category=DelayCategory.SPRINT_SLIPPAGE,
                    severity=severity,
                    description=f"Sprint '{sprint.name}' ended with {len(incomplete)} incomplete features",
                    affected_features=[f.id for f in incomplete],
                    timeline_markers=[sprint.end_date],
                    metadata={
                        "sprint": sprint.name,
                        "incomplete_count": len(incomplete),
                        "total_count": len(sprint_features),
                        "end_date": sprint.end_date.isoformat()
                    }
                ))
        
        return evidence
    
    def _analyze_developer_turnover(self) -> List[DelayEvidence]:
        """Detect developer changes mid-feature."""
        evidence = []
        
        for feature in self.platform_data.features:
            events = self.platform_data.get_events_for_feature(feature.id)
            
            if len(events) < 2:
                continue
            
            # Track contributor changes on this feature
            contributors_on_feature = set()
            for event in events:
                if event.contributor_id:
                    contributors_on_feature.add(event.contributor_id)
            
            if len(contributors_on_feature) > 2:  # More than 2 contributors = turnover
                severity = min(1.0, (len(contributors_on_feature) - 2) / 5)
                
                evidence.append(DelayEvidence(
                    category=DelayCategory.DEVELOPER_TURNOVER,
                    severity=severity,
                    description=f"Feature '{feature.name}' has been touched by {len(contributors_on_feature)} developers",
                    affected_features=[feature.id],
                    affected_contributors=list(contributors_on_feature),
                    metadata={
                        "feature": feature.name,
                        "developer_count": len(contributors_on_feature),
                        "developers": list(contributors_on_feature)
                    }
                ))
        
        return evidence
    
    def _analyze_time_tracking_gaps(self) -> List[DelayEvidence]:
        """Detect features without time tracking data."""
        features_without_tracking = [
            f for f in self.platform_data.features
            if f.estimated_hours is None or f.actual_hours is None
        ]
        
        if not features_without_tracking:
            return []
        
        severity = len(features_without_tracking) / max(1, len(self.platform_data.features))
        
        return [DelayEvidence(
            category=DelayCategory.MISSING_TIME_DATA,
            severity=severity,
            description=f"{len(features_without_tracking)} features lack complete time tracking data",
            affected_features=[f.id for f in features_without_tracking],
            metadata={
                "feature_count": len(features_without_tracking),
                "percentage": severity * 100
            }
        )]
    
    def _analyze_ownership_transfers(self) -> List[DelayEvidence]:
        """Detect features with frequent ownership changes."""
        evidence = []
        
        for feature in self.platform_data.features:
            history = getattr(feature, "ownership_history", [])
            if not history:
                continue
            
            transfer_count = len(history)
            if transfer_count >= 2:
                severity = min(1.0, 0.2 * transfer_count)
                contributors = set()
                for h in history:
                    if h.get("previous_owner"):
                        contributors.add(h["previous_owner"])
                    if h.get("new_owner"):
                        contributors.add(h["new_owner"])
                
                timeline_markers = [h["timestamp"] for h in history if isinstance(h.get("timestamp"), datetime)]
                
                description = f"Feature '{feature.name}' has been transferred {transfer_count} times between owners"
                evidence.append(DelayEvidence(
                    category=DelayCategory.OWNERSHIP_TRANSFER,
                    severity=severity,
                    description=description,
                    affected_features=[feature.id],
                    affected_contributors=list(contributors),
                    timeline_markers=timeline_markers,
                    metadata={
                        "feature": feature.name,
                        "transfer_count": transfer_count,
                        "history": [
                            {
                                "from": h["previous_owner"],
                                "to": h["new_owner"],
                                "timestamp": h["timestamp"].isoformat() if isinstance(h.get("timestamp"), datetime) else str(h.get("timestamp"))
                            }
                            for h in history
                        ]
                    }
                ))
        
        return evidence

    def _find_matching_feature(self, srs_name: str) -> Optional[Feature]:
        """Find platform feature matching SRS name using semantic similarity."""
        if not srs_name or not srs_name.strip():
            return None

        query_embedding = self.embedding_engine.generate_embedding(
            srs_name
        )

        best_feature = None
        best_score = 0.0

        for feature in self.platform_data.features:
            feature_text = f"{feature.name or ''} {feature.description or ''}"
            feature_embedding = self.embedding_engine.generate_embedding(
                feature_text
            )
            score = self._cosine_similarity(
                query_embedding,
                feature_embedding
            )

            if score > best_score:
                best_score = score
                best_feature = feature

        if best_score >= 0.75:
            return best_feature

        # Fallback to substring matching if embeddings are inconclusive
        srs_name_lower = srs_name.lower()
        for feature in self.platform_data.features:
            if srs_name_lower in feature.name.lower() or feature.name.lower() in srs_name_lower:
                return feature

        return None

    @staticmethod
    def _cosine_similarity(
        vec1: List[float],
        vec2: List[float]
    ) -> float:
        """Compute cosine similarity between two vectors."""
        if not vec1 or not vec2 or len(vec1) != len(vec2):
            return 0.0

        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        norm1 = math.sqrt(sum(a * a for a in vec1))
        norm2 = math.sqrt(sum(b * b for b in vec2))

        if norm1 == 0 or norm2 == 0:
            return 0.0

        return dot_product / (norm1 * norm2)
    
    def _calculate_working_hours(self) -> Dict[str, Any]:
        """
        Calculate working hours impact.
        Only counts weekday hours (Mon-Fri, 8h/day).
        Requires timeline data to be accurate.
        """
        if not self.platform_data.timeline_events:
            return {"status": "no_data"}
        
        sorted_events = sorted(self.platform_data.timeline_events, key=lambda e: e.timestamp)
        
        if not sorted_events:
            return {"status": "no_events"}
        
        # Calculate total span
        first_event = sorted_events[0]
        last_event = sorted_events[-1]
        total_days = (last_event.timestamp - first_event.timestamp).days
        
        working_day_names = self.calendar_profile.get("working_days") or [
            "Monday",
            "Tuesday",
            "Wednesday",
            "Thursday",
            "Friday",
        ]
        working_day_indexes = {
            self._weekday_to_index(day)
            for day in working_day_names
            if self._weekday_to_index(day) is not None
        }
        if not working_day_indexes:
            working_day_indexes = {0, 1, 2, 3, 4}

        holidays = {
            self._parse_holiday(holiday)
            for holiday in self.calendar_profile.get("holidays", [])
        }
        holidays.discard(None)

        hours_per_day = self.calendar_profile.get("hours_per_day") or self.WORKING_HOURS_PER_DAY
        working_days = 0
        current = first_event.date()
        last_date = last_event.date()
        while current <= last_date:
            if current.weekday() in working_day_indexes and current not in holidays:
                working_days += 1
            current += timedelta(days=1)

        working_hours = working_days * hours_per_day
        
        # Count actual events (commits)
        commit_events = [e for e in sorted_events if e.event_type == "commit"]
        
        return {
            "status": "calculated",
            "total_timeline_days": total_days,
            "estimated_working_days": int(working_days),
            "estimated_working_hours": int(working_hours),
            "hours_per_day": hours_per_day,
            "working_days_per_week": len(working_day_indexes),
            "holiday_count": len(holidays),
            "actual_commit_events": len(commit_events),
            "average_commits_per_week": len(commit_events) / max(1, total_days / 7)
        }

    @staticmethod
    def _weekday_to_index(day: Any) -> Optional[int]:
        if isinstance(day, int):
            return day if 0 <= day <= 6 else None

        normalized = str(day).strip().lower()
        mapping = {
            "mon": 0,
            "monday": 0,
            "tue": 1,
            "tuesday": 1,
            "wed": 2,
            "wednesday": 2,
            "thu": 3,
            "thursday": 3,
            "fri": 4,
            "friday": 4,
            "sat": 5,
            "saturday": 5,
            "sun": 6,
            "sunday": 6,
        }
        return mapping.get(normalized)

    @staticmethod
    def _parse_holiday(value: Any) -> Optional[date]:
        if isinstance(value, datetime):
            return value.date()
        if isinstance(value, date):
            return value
        try:
            return datetime.fromisoformat(str(value)).date()
        except ValueError:
            return None
