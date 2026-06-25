"""
FAQ auto-generator for delay analysis.
Generates contextual questions and answers based on detected delay evidence.
"""

from typing import List, Dict, Any
from datetime import datetime
import logging

from backend.analysis.semantic_delay_analyzer import DelayAnalysisResult, DelayEvidence, DelayCategory

logger = logging.getLogger(__name__)


class FAQ:
    """Single FAQ item."""
    
    def __init__(
        self,
        question: str,
        answer: str,
        evidence_refs: List[str],
        category: str,
        relevance_score: float = 0.8
    ):
        self.question = question
        self.answer = answer
        self.evidence_refs = evidence_refs
        self.category = category
        self.relevance_score = relevance_score


class FAQGenerator:
    """
    Generates FAQs from delay analysis results.
    Produces 10-20 contextual questions with evidence-backed answers.
    """
    
    def __init__(self, analysis_result: DelayAnalysisResult):
        """
        Initialize FAQ generator.
        
        Args:
            analysis_result: DelayAnalysisResult from semantic analyzer
        """
        self.result = analysis_result
        self.evidence_by_category = self._group_evidence()
    
    def _group_evidence(self) -> Dict[str, List[DelayEvidence]]:
        """Group evidence by category for easier access."""
        grouped = {}
        for evidence in self.result.evidence:
            category = evidence.category.value
            if category not in grouped:
                grouped[category] = []
            grouped[category].append(evidence)
        return grouped
    
    def generate(self) -> List[FAQ]:
        """
        Generate 10-20 contextual FAQs.
        
        Returns:
            List of 5 FAQ items, ranked by relevance
        """
        faqs = []
        
        # Generate potential questions from evidence
        candidates = []
        
        # Q1: Most critical delay factor
        if self.result.primary_causes:
            candidates.append(self._generate_primary_cause_faq())
        
        # Q2: Unassigned features
        if DelayCategory.UNASSIGNED_FEATURES.value in self.evidence_by_category:
            candidates.append(self._generate_unassigned_faq())
        
        # Q3: Developer overload
        if DelayCategory.CONTRIBUTOR_OVERLOAD.value in self.evidence_by_category:
            candidates.append(self._generate_overload_faq())
        
        # Q4: Blocked features
        if DelayCategory.BLOCKED_FEATURES.value in self.evidence_by_category:
            candidates.append(self._generate_blocked_faq())
        
        # Q5: Timeline gaps
        if DelayCategory.INACTIVE_DEVELOPMENT.value in self.evidence_by_category:
            candidates.append(self._generate_gap_faq())
        
        # Q6: Sprint slippage
        if DelayCategory.SPRINT_SLIPPAGE.value in self.evidence_by_category:
            candidates.append(self._generate_sprint_faq())
        
        # Q7: Developer turnover
        if DelayCategory.DEVELOPER_TURNOVER.value in self.evidence_by_category:
            candidates.append(self._generate_turnover_faq())
        
        # Q7.5: Ownership transfers
        if DelayCategory.OWNERSHIP_TRANSFER.value in self.evidence_by_category:
            candidates.append(self._generate_ownership_transfer_faq())
        
        # Q8: Time tracking issues
        if DelayCategory.MISSING_TIME_DATA.value in self.evidence_by_category:
            candidates.append(self._generate_time_tracking_faq())
        
        # Q9: Overall status
        candidates.append(self._generate_overall_status_faq())
        
        # Sort by relevance and keep the strongest contract-compliant set.
        candidates.sort(key=lambda f: f.relevance_score, reverse=True)
        faqs = candidates[:5]
        
        # If we have fewer than 5, fill with generic questions
        while len(faqs) < 5:
            faqs.append(self._generate_generic_faq(len(faqs)))
        
        return faqs
    
    def _generate_primary_cause_faq(self) -> FAQ:
        """Generate FAQ about primary delay cause."""
        primary = self.result.primary_causes[0] if self.result.primary_causes else None
        
        if not primary:
            return self._generate_generic_faq(0)
        
        evidence = self.evidence_by_category.get(primary, [])
        top_evidence = evidence[0] if evidence else None
        
        category_display = primary.replace("_", " ").title()
        
        question = f"What is the primary reason for project delays?"
        answer = f"{category_display} is the primary delay factor identified in your project.\n\n"
        
        if top_evidence:
            answer += f"Details: {top_evidence.description}\n\n"
            if top_evidence.affected_features:
                answer += f"Affected items: {', '.join(top_evidence.affected_features[:3])}"
                if len(top_evidence.affected_features) > 3:
                    answer += f" and {len(top_evidence.affected_features) - 3} more"
        
        return FAQ(
            question=question,
            answer=answer,
            evidence_refs=self.result.primary_causes[:3],
            category=primary,
            relevance_score=0.95
        )
    
    def _generate_unassigned_faq(self) -> FAQ:
        """Generate FAQ about unassigned features."""
        evidence = self.evidence_by_category[DelayCategory.UNASSIGNED_FEATURES.value][0]
        count = evidence.metadata.get("unassigned_count", 0)
        percentage = evidence.metadata.get("percentage", 0)
        
        question = "Why are some features unassigned and causing delays?"
        answer = f"{count} features ({percentage:.0f}% of total) have no assigned developer.\n\n"
        answer += "This is a critical delay factor because:\n"
        answer += "• No clear ownership means unclear responsibility\n"
        answer += "• Development cannot proceed without assignment\n"
        answer += f"• {count} features are currently blocked by this\n\n"
        answer += "Action: Assign each unassigned feature to a capable developer."
        
        return FAQ(
            question=question,
            answer=answer,
            evidence_refs=[DelayCategory.UNASSIGNED_FEATURES.value],
            category=DelayCategory.UNASSIGNED_FEATURES.value,
            relevance_score=0.9
        )
    
    def _generate_overload_faq(self) -> FAQ:
        """Generate FAQ about developer overload."""
        evidence_list = self.evidence_by_category[DelayCategory.CONTRIBUTOR_OVERLOAD.value]
        top_evidence = evidence_list[0] if evidence_list else None
        
        if not top_evidence:
            return self._generate_generic_faq(0)
        
        dev_name = top_evidence.metadata.get("contributor", "A developer")
        feature_count = top_evidence.metadata.get("feature_count", 0)
        
        question = f"Why is developer '{dev_name}' overloaded and causing slowdown?"
        answer = f"Developer '{dev_name}' is currently assigned to {feature_count} features.\n\n"
        answer += f"This creates delays because:\n"
        answer += f"• Context switching between {feature_count} features reduces productivity\n"
        answer += f"• Each feature gets less focused attention\n"
        answer += f"• Quality may suffer due to divided focus\n"
        answer += f"• Single point of failure if developer becomes unavailable\n\n"
        answer += f"Action: Redistribute {feature_count} features across the team."
        
        return FAQ(
            question=question,
            answer=answer,
            evidence_refs=[DelayCategory.CONTRIBUTOR_OVERLOAD.value],
            category=DelayCategory.CONTRIBUTOR_OVERLOAD.value,
            relevance_score=0.88
        )
    
    def _generate_blocked_faq(self) -> FAQ:
        """Generate FAQ about blocked features."""
        evidence_list = self.evidence_by_category[DelayCategory.BLOCKED_FEATURES.value]
        count = len(evidence_list)
        
        question = f"Which features are blocked and for how long?"
        answer = f"{count} features are currently in a blocked state:\n\n"
        
        for i, evidence in enumerate(evidence_list[:3], 1):
            feature_name = evidence.affected_features[0] if evidence.affected_features else "Unknown"
            blocked_days = evidence.metadata.get("blocked_days", "unknown")
            answer += f"{i}. {feature_name}: blocked for {blocked_days} days\n"
        
        if count > 3:
            answer += f"\n... and {count - 3} more blocked features\n"
        
        answer += "\nReason for blocking (common causes):\n"
        answer += "• Dependencies on other features\n"
        answer += "• Resource constraints\n"
        answer += "• External blockers\n"
        answer += "• Technical debt\n\n"
        answer += "Action: Investigate and remove blockers on high-priority features."
        
        return FAQ(
            question=question,
            answer=answer,
            evidence_refs=[DelayCategory.BLOCKED_FEATURES.value],
            category=DelayCategory.BLOCKED_FEATURES.value,
            relevance_score=0.85
        )
    
    def _generate_gap_faq(self) -> FAQ:
        """Generate FAQ about development gaps."""
        evidence = self.evidence_by_category[DelayCategory.INACTIVE_DEVELOPMENT.value][0]
        gap_count = evidence.metadata.get("gap_count", 0)
        total_gap_days = evidence.metadata.get("total_gap_days", 0)
        
        question = "Why are there periods of no development activity?"
        answer = f"Detected {gap_count} inactive periods totaling {total_gap_days} days.\n\n"
        answer += f"This affects project delivery because:\n"
        answer += f"• {total_gap_days} days with no commits = {total_gap_days * 8} lost working hours\n"
        answer += f"• May indicate team being blocked or context-switched\n"
        answer += f"• Could mean features are stalled waiting for review/merge\n"
        answer += f"• Reduces overall project velocity\n\n"
        answer += "Investigate: Check for PR reviews, blocked dependencies, or team blockers."
        
        return FAQ(
            question=question,
            answer=answer,
            evidence_refs=[DelayCategory.INACTIVE_DEVELOPMENT.value],
            category=DelayCategory.INACTIVE_DEVELOPMENT.value,
            relevance_score=0.82
        )
    
    def _generate_sprint_faq(self) -> FAQ:
        """Generate FAQ about sprint slippage."""
        evidence_list = self.evidence_by_category[DelayCategory.SPRINT_SLIPPAGE.value]
        
        question = "How many features are slipping from sprints?"
        answer = ""
        
        for evidence in evidence_list[:2]:
            sprint_name = evidence.metadata.get("sprint", "Unknown Sprint")
            incomplete = evidence.metadata.get("incomplete_count", 0)
            total = evidence.metadata.get("total_count", 0)
            answer += f"• {sprint_name}: {incomplete}/{total} features incomplete\n"
        
        if len(evidence_list) > 2:
            answer += f"• ... and {len(evidence_list) - 2} more sprints with slippage\n"
        
        answer += "\nSpirit slippage indicates:\n"
        answer += "• Sprint planning is optimistic\n"
        answer += "• Velocity metrics may be unreliable\n"
        answer += "• Bottlenecks not being addressed\n\n"
        answer += "Action: Review sprint planning methodology and identify bottlenecks."
        
        return FAQ(
            question=question,
            answer=answer,
            evidence_refs=[DelayCategory.SPRINT_SLIPPAGE.value],
            category=DelayCategory.SPRINT_SLIPPAGE.value,
            relevance_score=0.8
        )
    
    def _generate_turnover_faq(self) -> FAQ:
        """Generate FAQ about developer turnover."""
        evidence_list = self.evidence_by_category[DelayCategory.DEVELOPER_TURNOVER.value]
        
        question = "Which features have had developer changes mid-implementation?"
        answer = f"Detected {len(evidence_list)} features with multiple developer touch-points:\n\n"
        
        for i, evidence in enumerate(evidence_list[:3], 1):
            feature = evidence.metadata.get("feature", "Unknown")
            dev_count = evidence.metadata.get("developer_count", 0)
            answer += f"{i}. {feature}: {dev_count} different developers worked on it\n"
        
        if len(evidence_list) > 3:
            answer += f"\n... and {len(evidence_list) - 3} more features\n"
        
        answer += "\nMultiple developers on one feature causes:\n"
        answer += "• Knowledge loss and context switching\n"
        answer += "• Inconsistent implementation patterns\n"
        answer += "• Potential rework and refactoring\n"
        answer += "• Reduced code quality\n\n"
        answer += "Action: Assign features to single developers; handoffs only when necessary."
        
        return FAQ(
            question=question,
            answer=answer,
            evidence_refs=[DelayCategory.DEVELOPER_TURNOVER.value],
            category=DelayCategory.DEVELOPER_TURNOVER.value,
            relevance_score=0.78
        )
    
    def _generate_time_tracking_faq(self) -> FAQ:
        """Generate FAQ about time tracking gaps."""
        evidence = self.evidence_by_category[DelayCategory.MISSING_TIME_DATA.value][0]
        count = evidence.metadata.get("feature_count", 0)
        percentage = evidence.metadata.get("percentage", 0)
        
        question = "Why can't we calculate accurate working hours for some features?"
        answer = f"{count} features ({percentage:.0f}%) lack complete time tracking data.\n\n"
        answer += "This prevents accurate delay analysis because:\n"
        answer += "• Can't calculate actual vs. estimated hours\n"
        answer += "• Can't identify budget overruns\n"
        answer += "• Difficult to predict future timeline\n"
        answer += "• No historical data for velocity calculation\n\n"
        answer += "Action: Ensure all features have estimated hours and actual hours logged."
        
        return FAQ(
            question=question,
            answer=answer,
            evidence_refs=[DelayCategory.MISSING_TIME_DATA.value],
            category=DelayCategory.MISSING_TIME_DATA.value,
            relevance_score=0.75
        )
    
    def _generate_ownership_transfer_faq(self) -> FAQ:
        """Generate FAQ about feature ownership transfers."""
        evidence_list = self.evidence_by_category[DelayCategory.OWNERSHIP_TRANSFER.value]
        
        question = "Which features have changed ownership and how does it affect delivery?"
        answer = f"Detected {len(evidence_list)} features with ownership transfers (multiple assignee changes):\n\n"
        
        for i, evidence in enumerate(evidence_list[:3], 1):
            feature_name = evidence.metadata.get("feature", "Unknown Feature")
            transfer_count = evidence.metadata.get("transfer_count", 0)
            
            history_str = ""
            history_items = evidence.metadata.get("history", [])
            if history_items:
                owners = []
                for item in history_items:
                    frm = item.get("from") or "Unassigned"
                    to = item.get("to") or "Unassigned"
                    owners.append(f"{frm} → {to}")
                history_str = f" ({'; '.join(owners)})"
                
            answer += f"{i}. {feature_name}: transferred {transfer_count} times{history_str}\n"
            
        if len(evidence_list) > 3:
            answer += f"\n... and {len(evidence_list) - 3} more features with ownership transfers\n"
            
        answer += "\nFrequent ownership transfers affect delivery because:\n"
        answer += "• Knowledge loss and context re-establishment delay progress\n"
        answer += "• Inconsistent understanding of requirements can lead to bugs\n"
        answer += "• Shifted accountability can cause tasks to stall\n\n"
        answer += "Action: Stabilize feature ownership and ensure clear handoff documentation when transfers are unavoidable."
        
        return FAQ(
            question=question,
            answer=answer,
            evidence_refs=[DelayCategory.OWNERSHIP_TRANSFER.value],
            category=DelayCategory.OWNERSHIP_TRANSFER.value,
            relevance_score=0.83
        )

    def _generate_overall_status_faq(self) -> FAQ:
        """Generate FAQ about overall project status."""
        completed = self.result.completed_features
        in_progress = self.result.in_progress_features
        blocked = self.result.blocked_features
        total = self.result.total_features
        
        completion_percentage = (completed / total * 100) if total > 0 else 0
        
        question = "What's the overall status of the project?"
        answer = f"Project Status Overview:\n"
        answer += f"• Total Features: {total}\n"
        answer += f"• Completed: {completed} ({completion_percentage:.0f}%)\n"
        answer += f"• In Progress: {in_progress}\n"
        answer += f"• Blocked: {blocked}\n\n"
        answer += f"Severity Score: {self.result.severity_score:.0%}\n\n"
        answer += "Key Findings:\n"
        
        for cause in self.result.primary_causes[:3]:
            answer += f"• {cause.replace('_', ' ').title()}\n"
        
        answer += "\nRecommendation: Focus on the primary causes above to improve delivery."
        
        return FAQ(
            question=question,
            answer=answer,
            evidence_refs=self.result.primary_causes[:3],
            category="overall",
            relevance_score=0.9
        )
    
    def _generate_generic_faq(self, index: int) -> FAQ:
        """Generate generic FAQ to fill remaining slots."""
        generic_questions = [
            ("What specific actions should we take first?", 
             "Prioritize: 1) Assign unassigned features, 2) Unblock blocked items, 3) Redistribute overloaded developers."),
            
            ("How can we prevent delays in future sprints?",
             "Implement: Better planning, realistic story estimation, daily standups, dependency tracking, and velocity metrics."),
            
            ("Which developers are key to unblocking delays?",
             "Review the identified overloaded developers and critical feature owners. Consider pairing to spread knowledge."),
            
            ("When can we expect to complete all features?",
             "Based on current velocity and identified delays, a revised timeline will be generated after addressing key blockers."),
            
            ("What are hidden dependencies causing delays?",
             "Cross-team dependencies and technical debt are often hidden causes. Review dependency evidence across components."),

            ("Which project area needs the manager's attention today?",
             "Start with the highest-severity primary cause and the features attached to that evidence."),

            ("How reliable is this audit result?",
             "Reliability depends on available SRS, platform activity, time tracking, assignment, and calendar data."),

            ("What should be reviewed in the next status meeting?",
             "Review blocked features, unassigned work, overloaded developers, and the largest working-capacity variance."),

            ("What changed most from the original plan?",
             "Compare planned effort against actual effort and review the root-cause evidence for the largest variance."),

            ("How does team capacity affect the predicted delay?",
             "Available weekly capacity controls expected duration; holidays and fewer working days reduce that capacity.")
        ]
        
        if index < len(generic_questions):
            q, a = generic_questions[index]
            return FAQ(
                question=q,
                answer=a,
                evidence_refs=[],
                category="general",
                relevance_score=0.7
            )
        
        return FAQ(
            question="How should we measure progress going forward?",
            answer="Track: Feature completion rate, burn-down chart, velocity trends, and time-to-close metrics.",
            evidence_refs=[],
            category="general",
            relevance_score=0.65
        )
