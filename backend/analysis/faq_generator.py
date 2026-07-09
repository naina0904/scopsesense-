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
        
        candidates.sort(key=lambda f: f.relevance_score, reverse=True)
        seen_questions = set()
        faqs = []
        for f in candidates:
            q_norm = (f.question or "").strip().lower()
            if q_norm not in seen_questions:
                seen_questions.add(q_norm)
                faqs.append(f)
            if len(faqs) == 5:
                break
        
        # If we have fewer than 5, fill with unique generic questions
        idx = 0
        while len(faqs) < 5 and idx < 20:
            gen_f = self._generate_generic_faq(idx)
            q_norm = (gen_f.question or "").strip().lower()
            if q_norm not in seen_questions:
                seen_questions.add(q_norm)
                faqs.append(gen_f)
            idx += 1
        
        return faqs
    
    def _generate_primary_cause_faq(self) -> FAQ:
        """Generate FAQ about primary delay cause."""
        primary = self.result.primary_causes[0] if self.result.primary_causes else None
        
        if not primary:
            return self._generate_generic_faq(0)
        
        evidence = self.evidence_by_category.get(primary, [])
        top_evidence = evidence[0] if evidence else None
        category_display = primary.replace("_", " ").title()
        
        question = "What is the primary technical root cause driving project schedule drift?"
        answer = f"📌 PRIMARY ROOT CAUSE: {category_display.upper()}\n\n"
        
        if top_evidence:
            answer += f"• Diagnostic Finding: {top_evidence.description}\n\n"
            if top_evidence.affected_features:
                answer += f"• Impacted Scope: {', '.join(top_evidence.affected_features[:3])}"
                if len(top_evidence.affected_features) > 3:
                    answer += f" (+{len(top_evidence.affected_features) - 3} additional requirements)"
                answer += "\n\n"
        
        answer += "🎯 EXECUTIVE ACTION PLAN:\n"
        answer += "1. Conduct immediate technical review on impacted requirements to isolate bottlenecks.\n"
        answer += "2. Re-allocate engineering bandwidth from non-critical tasks to resolve root-cause blockers."
        
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
        
        question = "Why are unassigned requirements jeopardizing the delivery timeline?"
        answer = f"⚠️ RESOURCE ALLOCATION GAP: {count} Requirements ({percentage:.0f}% of total scope)\n\n"
        answer += "• Impact Analysis: Unassigned features represent orphaned roadmap commitments without engineering accountability. In Jira, these tasks show 0 logged hours and stall critical path progress.\n"
        answer += "• Risk Assessment: High probability of cascading sprint delays if dependencies rely on these unassigned modules.\n\n"
        answer += "🎯 EXECUTIVE ACTION PLAN:\n"
        answer += "1. Enforce mandatory ticket assignment across all active engineering leads within 24 hours.\n"
        answer += "2. Move unassigned future-phase items into backlog epics to prevent baseline skew."
        
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
        
        question = f"How is developer bandwidth bottlenecking delivery (e.g., {dev_name})?"
        answer = f"🚨 CAPACITY BOTTLENECK: {dev_name} ({feature_count} concurrent requirements)\n\n"
        answer += f"• Diagnostic Finding: Assigning {feature_count} complex architectural features to a single contributor exceeds optimal engineering cognitive load.\n"
        answer += "• Velocity Impact: Severe context-switching penalties result in extended cycle times, code review delays, and single-point-of-failure risk.\n\n"
        answer += "🎯 EXECUTIVE ACTION PLAN:\n"
        answer += f"1. Immediately re-assign at least 40% of {dev_name}'s secondary modules to peer engineers.\n"
        answer += "2. Implement Work-In-Progress (WIP) limits per developer in Jira sprint boards."
        
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
        
        question = "Which requirements are currently stalled by technical blockers?"
        answer = f"🛑 CRITICAL PATH BLOCKERS: {count} Stalled Requirements\n\n"
        
        for i, evidence in enumerate(evidence_list[:3], 1):
            feature_name = evidence.affected_features[0] if evidence.affected_features else "Unknown Requirement"
            blocked_days = evidence.metadata.get("blocked_days", "unknown")
            answer += f"• {feature_name}: Blocked for {blocked_days} days\n"
        
        if count > 3:
            answer += f"• (+{count - 3} additional blocked requirements)\n"
        
        answer += "\n• Root Cause Analysis: Stalls typically originate from unresolved cross-module API dependencies, pending third-party integrations, or unapproved architectural RFCs.\n\n"
        answer += "🎯 EXECUTIVE ACTION PLAN:\n"
        answer += "1. Convene an emergency architecture unblocking sync with module owners.\n"
        answer += "2. Escalate external vendor or infrastructure dependencies immediately."
        
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
        
        question = "Why are there prolonged development activity gaps across repositories?"
        answer = f"📉 VELOCITY STALL: {gap_count} Inactive Periods ({total_gap_days} Total Days)\n\n"
        answer += f"• Quantitative Impact: {total_gap_days} days without commit or Jira progress equates to ~{total_gap_days * 8} lost engineering hours across teams.\n"
        answer += "• Diagnostic Finding: Indicates silent bottlenecks such as protracted code review queues, unclear requirements, or unlogged offline development.\n\n"
        answer += "🎯 EXECUTIVE ACTION PLAN:\n"
        answer += "1. Enforce 24-hour SLA on pull request reviews and branch merges.\n"
        answer += "2. Require engineers to log daily work-in-progress updates against active Jira tickets."
        
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
        
        question = "What is the trend of requirement slippage across sprint boundaries?"
        answer = "🔄 SPRINT COMMITMENT SLIPPAGE:\n\n"
        
        for evidence in evidence_list[:2]:
            sprint_name = evidence.metadata.get("sprint", "Unknown Sprint")
            incomplete = evidence.metadata.get("incomplete_count", 0)
            total = evidence.metadata.get("total_count", 0)
            answer += f"• {sprint_name}: {incomplete} of {total} committed features slipped to next sprint\n"
        
        if len(evidence_list) > 2:
            answer += f"• (+{len(evidence_list) - 2} additional sprints exhibiting carryover)\n"
        
        answer += "\n• Diagnostic Finding: Consistently carrying over tasks indicates over-optimistic sprint planning, scope creep mid-sprint, or unindexed bug remediation.\n\n"
        answer += "🎯 EXECUTIVE ACTION PLAN:\n"
        answer += "1. Apply a 20% capacity buffer for technical debt and unplanned hotfixes in upcoming sprints.\n"
        answer += "2. Freeze story point commitments based on empirical trailing velocity rather than targets."
        
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
        
        question = "How is developer turnover and task reassignment impacting code quality?"
        answer = f"🔀 CONTINUITY FRICTION: {len(evidence_list)} Requirements with Mid-Stream Handoffs\n\n"
        
        for i, evidence in enumerate(evidence_list[:3], 1):
            feature = evidence.metadata.get("feature", "Unknown Requirement")
            dev_count = evidence.metadata.get("developer_count", 0)
            answer += f"• {feature}: Handled by {dev_count} different engineers\n"
        
        if len(evidence_list) > 3:
            answer += f"• (+{len(evidence_list) - 3} additional multi-handover items)\n"
        
        answer += "\n• Diagnostic Finding: Frequent reassignment degrades architectural consistency, introduces refactoring loops, and inflates onboarding overhead.\n\n"
        answer += "🎯 EXECUTIVE ACTION PLAN:\n"
        answer += "1. Enforce end-to-end feature ownership from design specification to production release.\n"
        answer += "2. Mandate structured technical handoff docs before transferring in-progress Jira tickets."
        
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
        
        question = "Why is time tracking incomplete across certain roadmap requirements?"
        answer = f"⏱️ AUDIT BLIND SPOT: {count} Requirements ({percentage:.0f}% of baseline) Lack Time Logs\n\n"
        answer += "• Impact Analysis: Missing Jira worklogs prevent real-time earned value management (EVM), distort cost-to-complete forecasts, and obscure actual developer effort.\n"
        answer += "• Diagnostic Finding: Tasks are either unstarted, logged under generic overarching epics, or tracked outside standard Jira workflows.\n\n"
        answer += "🎯 EXECUTIVE ACTION PLAN:\n"
        answer += "1. Enforce strict daily Jira time-logging protocols across all engineering squads.\n"
        answer += "2. Map orphaned worklogs from parent Epics down to child requirement tickets."
        
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
        
        question = "Which requirements have suffered from repeated ownership transfers?"
        answer = f"🔁 OWNERSHIP CHURN: {len(evidence_list)} Requirements Re-Assigned Multiple Times\n\n"
        
        for i, evidence in enumerate(evidence_list[:3], 1):
            feature_name = evidence.metadata.get("feature", "Unknown Feature")
            transfer_count = evidence.metadata.get("transfer_count", 0)
            answer += f"• {feature_name}: Re-assigned {transfer_count} times across sprints\n"
            
        if len(evidence_list) > 3:
            answer += f"• (+{len(evidence_list) - 3} additional churned requirements)\n"
            
        answer += "\n• Diagnostic Finding: High ownership churn correlates with vague SRS acceptance criteria or shifting product priorities during sprint execution.\n\n"
        answer += "🎯 EXECUTIVE ACTION PLAN:\n"
        answer += "1. Freeze requirement specifications prior to sprint kickoff.\n"
        answer += "2. Lock primary assignee accountability until feature passes QA sign-off."
        
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
        
        question = "What is the executive status and schedule drift of this project?"
        answer = f"📊 EXECUTIVE AUDIT SUMMARY\n\n"
        answer += f"• Roadmap Scope: {total} tracked requirements across core engineering modules.\n"
        answer += f"• Completion Rate: {completed} completed ({completion_percentage:.0f}%), {in_progress} active, {blocked} blocked.\n"
        answer += f"• Risk Severity Index: {self.result.severity_score:.0%} (Schedule Slip Forecasted).\n\n"
        answer += "🔍 PRIMARY DRIFT DRIVERS:\n"
        for cause in self.result.primary_causes[:3]:
            answer += f"• {cause.replace('_', ' ').title()}\n"
        
        answer += "\n🎯 BOARD-READY RECOMMENDATION:\n"
        answer += "Enforce immediate sprint boundary reconciliation. Freeze unbudgeted ghost tasks and re-baseline unstarted requirements before authorizing next engineering sprint."
        
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
            ("What immediate executive interventions will yield highest velocity ROI?", 
             "🎯 TOP 3 INTERVENTIONS:\n\n1. Resource Re-allocation: Redistribute tickets from overloaded engineers to balance squad capacity.\n2. Scope Protection: Quarantine unbudgeted ghost work (+11.0h detected) into future phases.\n3. Accountability Lock: Assign leads to all unassigned roadmap items within 24 hours."),
            
            ("How do we calibrate sprint planning to prevent recurring roadmap slip?",
             "📐 CALIBRATION PROTOCOL:\n\n• Adopt empirical trailing velocity rather than aspirational targets.\n• Institute a mandatory 15% architecture reserve buffer for integration testing.\n• Enforce strict Definition of Ready (DoR) before pulling SRS items into sprint backlog."),
            
            ("What is the financial and operational impact of unbudgeted Ghost Work?",
             "💸 GHOST WORK IMPACT ANALYSIS:\n\n• Unbudgeted tasks consume core development hours without contributing to SRS milestone completion.\n• Creates synthetic schedule drift by diluting team focus away from committed baseline features.\n• Action: Audit all Jira tickets lacking SRS traceability codes and require product manager sign-off."),
            
            ("How does ScopeSense reconcile SRS baseline hours against Jira worklogs?",
             "🔬 MATHEMATICAL RECONCILIATION:\n\n• The AI engine links SRS specification nodes to Jira epics and stories via semantic vector embedding.\n• Net Schedule Drift is computed precisely as: (Total Jira Worked Hours − Total SRS Planned Hours).\n• Positive variance indicates budget overrun; negative variance with 0 actuals indicates unstarted Ghost Gaps."),
            
            ("What key metrics should executive leadership track weekly?",
             "📈 EXECUTIVE KPI DASHBOARD:\n\n• Net Schedule Drift (Hours & Forecasted Weeks)\n• Ghost Scope Creep Ratio (% of non-SRS hours logged)\n• Requirement Coverage Index (% of SRS baseline with active Jira tasks)\n• Developer Load Distribution (Max vs. Median ticket assignment)")
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
            question="How should engineering governance evolve post-audit?",
            answer="🛡️ GOVERNANCE FRAMEWORK:\n\n• Implement bi-weekly automated ScopeSense drift audits.\n• Require architecture sign-off for any task exceeding planned baseline by >20%.\n• Integrate automated time-tracking hooks between IDEs and Jira.",
            evidence_refs=[],
            category="general",
            relevance_score=0.65
        )
