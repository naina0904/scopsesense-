"""
Semantic AI chatbot for project analysis Q&A.
Answers dynamic questions about project delays, contributors, features, etc.
Works semantically without keyword mapping.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

from backend.analysis.semantic_delay_analyzer import DelayAnalysisResult
from backend.integrations.core.unified_schema import PlatformData
from backend.llm.manager import LLMManager
from backend.semantic.embeddings import EmbeddingEngine
from backend.chat.user_guide_context import get_user_guide_context

logger = logging.getLogger(__name__)


class AnalysisContextualizer:
    """
    Builds semantic context from analysis data for LLM reasoning.
    Provides structured summaries for questions about delays, people, features, etc.
    """
    
    def __init__(
        self,
        platform_data: PlatformData,
        analysis_result: DelayAnalysisResult,
        provider: Optional[str] = None,
        faqs: Optional[List[Any]] = None,
        srs_features: Optional[List[Any]] = None
    ):
        if isinstance(platform_data, dict):
            from backend.integrations.core.unified_schema import PlatformData, PlatformType
            p_type = platform_data.get("platform", "jira")
            p_key = platform_data.get("platform_key", platform_data.get("project_key", "Project"))
            try:
                pt_enum = PlatformType(p_type)
            except ValueError:
                pt_enum = PlatformType.JIRA
            self.platform_data = PlatformData(
                platform=pt_enum,
                platform_key=str(p_key),
                features=platform_data.get("features", []),
                contributors=platform_data.get("contributors", []),
                timeline_events=platform_data.get("timeline_events", []),
                sprints=platform_data.get("sprints", [])
            )
        else:
            self.platform_data = platform_data

        if isinstance(analysis_result, dict):
            from backend.analysis.semantic_delay_analyzer import DelayAnalysisResult, DelayEvidence, DelayCategory
            ev_list = []
            for ev in analysis_result.get("evidence", []):
                if isinstance(ev, dict):
                    cat_str = ev.get("category", "unassigned_features")
                    try:
                        cat = DelayCategory(cat_str)
                    except ValueError:
                        cat = DelayCategory.UNASSIGNED_FEATURES
                    ev_list.append(DelayEvidence(
                        category=cat,
                        severity=float(ev.get("severity", 0.0)),
                        description=ev.get("description", "")
                    ))
                elif isinstance(ev, DelayEvidence):
                    ev_list.append(ev)
            if not ev_list:
                for rc in analysis_result.get("root_cause_table", []):
                    cat_name = rc.get("category", "Variance")
                    desc = rc.get("reason", "") or rc.get("evidence", "") or f"Issue in {cat_name}"
                    ev_list.append(DelayEvidence(
                        category=DelayCategory.UNASSIGNED_FEATURES,
                        severity=0.5,
                        description=f"[{cat_name}] {desc}"
                    ))
            ts = analysis_result.get("analysis_timestamp")
            if isinstance(ts, str):
                try:
                    ts = datetime.fromisoformat(ts.replace("Z", "+00:00"))
                except ValueError:
                    ts = datetime.utcnow()
            elif not isinstance(ts, datetime):
                ts = datetime.utcnow()
            self.analysis_result = DelayAnalysisResult(
                project_key=str(analysis_result.get("project_key", "Project")),
                platform=str(analysis_result.get("platform", "jira")),
                analysis_timestamp=ts,
                total_features=int(analysis_result.get("total_features", 0)),
                completed_features=int(analysis_result.get("completed_features", 0)),
                in_progress_features=int(analysis_result.get("in_progress_features", 0)),
                blocked_features=int(analysis_result.get("blocked_features", 0)),
                unassigned_features=int(analysis_result.get("unassigned_features", 0)),
                evidence=ev_list,
                severity_score=float(analysis_result.get("severity_score", 0.0) or (1.0 - (float(analysis_result.get("health_score", 100)) / 100.0))),
                primary_causes=analysis_result.get("primary_causes", [])
            )
        else:
            self.analysis_result = analysis_result

        self.faqs = faqs or []
        self.srs_features = srs_features or []
        if provider:
            self.llm_manager = LLMManager(provider=provider)
        else:
            self.llm_manager = LLMManager()
        self.embedding_engine = EmbeddingEngine()
        self.corpus_entries = []
        self.corpus_embeddings = []
        self._prepare_corpus()
    
    def build_context_summary(self) -> str:
        """Build comprehensive context for LLM."""
        summary = f"""
PROJECT ANALYSIS CONTEXT
========================

Platform: {self.platform_data.platform.value}
Project Key: {self.platform_data.platform_key}
Analysis Time: {self.analysis_result.analysis_timestamp.isoformat()}

OVERALL METRICS
===============
Total Features: {self.analysis_result.total_features}
Completed: {self.analysis_result.completed_features} ({self.analysis_result.completed_features/max(1,self.analysis_result.total_features)*100:.0f}%)
In Progress: {self.analysis_result.in_progress_features}
Blocked: {self.analysis_result.blocked_features}
Unassigned: {self.analysis_result.unassigned_features}
Severity Score: {self.analysis_result.severity_score:.0%}

PRIMARY DELAY FACTORS
=====================
"""
        for i, cause in enumerate(self.analysis_result.primary_causes, 1):
            summary += f"{i}. {cause.replace('_', ' ').title()}\n"
        
        summary += "\nKEY EVIDENCE\n============\n"
        for evidence in self.analysis_result.evidence[:5]:
            summary += f"• {evidence.category.value.replace('_', ' ').title()}: {evidence.description}\n"
        
        summary += "\nCONTRIBUTORS\n============\n"
        for contrib in self.platform_data.contributors[:10]:
            features = self.platform_data.get_features_by_contributor(contrib.id)
            summary += f"• {contrib.name}: {len(features)} features, {contrib.commits_count} commits\n"
        
        summary += "\nFEATURE STATUS BREAKDOWN & DETAILS\n==================================\n"
        status_counts = {}
        for feature in self.platform_data.features:
            status = feature.status.value
            status_counts[status] = status_counts.get(status, 0) + 1
        
        for status, count in sorted(status_counts.items()):
            summary += f"• {status.replace('_', ' ').title()}: {count}\n"
            
        summary += "\nIndividual Feature Details:\n"
        for feature in self.platform_data.features[:50]:
            st_str = feature.status.value.replace('_', ' ').title()
            assignee = feature.assigned_to or "Unassigned"
            planned = feature.estimated_hours if feature.estimated_hours is not None else 0
            actual = feature.actual_hours if feature.actual_hours is not None else 0
            summary += f"• [{feature.id}] {feature.name} (Status: {st_str}, Assigned: {assignee}, Planned: {planned}h, Actual: {actual}h)\n"
        
        # Add ownership transfer summary
        ownership_features = []
        for feature in self.platform_data.features:
            history = getattr(feature, "ownership_history", [])
            if history:
                ownership_features.append(feature)
        if ownership_features:
            summary += "\nOWNERSHIP TRANSFERS\n===================\n"
            for feature in ownership_features:
                transfers = len(feature.ownership_history)
                summary += f"• Feature '{feature.name}': {transfers} assignee changes\n"
                
        # Add FAQ summary
        if self.faqs:
            summary += "\nFREQUENTLY ASKED QUESTIONS\n==========================\n"
            for faq in self.faqs:
                if hasattr(faq, "question") and hasattr(faq, "answer"):
                    summary += f"Q: {faq.question}\nA: {faq.answer}\n\n"
                elif isinstance(faq, dict) and "question" in faq and "answer" in faq:
                    summary += f"Q: {faq['question']}\nA: {faq['answer']}\n\n"

        # Add SRS findings
        if self.srs_features:
            summary += "\nSRS REQUIREMENTS & FINDINGS\n===========================\n"
            for feature in self.srs_features:
                if isinstance(feature, dict):
                    name = feature.get("name") or feature.get("title") or feature.get("requirement") or "Unknown"
                    desc = feature.get("description", "")
                    due = feature.get("due_date") or feature.get("priority", "")
                    summary += f"• SRS Feature: {name}\n  Description: {desc}\n  Info: {due}\n"

        return summary
    
    def answer_question(self, question: str) -> str:
        """
        Answer a question using semantic analysis and LLM reasoning.
        
        Args:
            question: User's question about the project
        
        Returns:
            Answer based on analysis context
        """
        context = self.build_context_summary()
        relevant_context = self._retrieve_relevant_context(question)
        user_guide_knowledge = get_user_guide_context()

        prompt = f"""
You are an expert project manager and ScopeSense AI copilot analyzing a software project's delays and performance.

{user_guide_knowledge}

Relevant Evidence and Features from Project:
{relevant_context}

Project Summary Context:
{context}

User Question: {question}

CRITICAL RULES FOR INTERPRETATION & ANSWERS:
1. If "Actual Hours" is 0 or no time is logged, it does NOT mean a ticket/feature doesn't exist. It usually means the developer hasn't logged their time yet.
2. A positive variance means overrun. A negative variance means under-budget or unstarted.
3. Do not assume a ticket is missing if it appears in the "Evidence" or "Features" lists.
4. When answering conceptual questions (e.g. how metrics like EVM/SPI/Slip are calculated, or what troubleshooting actions to take), explicitly cite the formulas and thresholds from the canonical User Guide section above.

Provide a concrete, evidence-based answer drawing from the User Guide definitions and analysis context above.
Focus on: specific features, formulas, contributors, timeline data, and actionable insights.
"""
        
        # Get LLM response
        try:
            response = self.llm_manager.generate(prompt)
            return response
        except Exception as e:
            logger.error(f"LLM generate failed: {e}")
            return self._fallback_answer(question)
    
    def _fallback_answer(self, question: str) -> str:
        """Fallback answer if LLM is unavailable."""
        question_lower = question.lower()
        
        # Detect question type
        if "who" in question_lower and ("delay" in question_lower or "responsible" in question_lower):
            return self._answer_who_caused_delay()
        
        elif "why" in question_lower and "delay" in question_lower:
            return self._answer_why_delayed()
        
        elif "which" in question_lower and ("feature" in question_lower or "module" in question_lower):
            return self._answer_which_feature_delayed()
        
        elif "developer" in question_lower or "developer" in question_lower:
            return self._answer_developer_assignment(question)
        
        elif "work" in question_lower or "working" in question_lower:
            return self._answer_who_working(question)
        
        else:
            return self._answer_general_delay_question()
    
    def _answer_who_caused_delay(self) -> str:
        """Answer: Who caused the delay?"""
        answer = "Based on the analysis, delays are caused by multiple factors:\n\n"
        
        # Find overloaded developers
        overloaded = {}
        for contrib in self.platform_data.contributors:
            features = self.platform_data.get_features_by_contributor(contrib.id)
            if len(features) > 10:
                overloaded[contrib.name] = len(features)
        
        if overloaded:
            answer += "Overloaded Developers (bottlenecks):\n"
            for name, count in sorted(overloaded.items(), key=lambda x: x[1], reverse=True):
                answer += f"• {name}: {count} features assigned\n"
            answer += "\n"
        
        # Find inactive contributors
        inactive = []
        for contrib in self.platform_data.contributors:
            events = self.platform_data.get_events_by_contributor(contrib.id)
            if not events:
                inactive.append(contrib.name)
        
        if inactive:
            answer += f"Inactive Contributors: {', '.join(inactive[:3])}\n\n"
        
        answer += "Primary Causes (not people):\n"
        for i, cause in enumerate(self.analysis_result.primary_causes, 1):
            answer += f"{i}. {cause.replace('_', ' ').title()}\n"
        
        return answer
    
    def _answer_why_delayed(self) -> str:
        """Answer: Why is the project delayed?"""
        answer = "The project is delayed due to:\n\n"
        
        for evidence in self.analysis_result.evidence[:5]:
            answer += f"• {evidence.description}\n"
        
        answer += f"\nSeverity: {self.analysis_result.severity_score:.0%}\n"
        answer += "Most critical: " + (self.analysis_result.primary_causes[0].replace("_", " ").title() if self.analysis_result.primary_causes else "N/A")
        
        return answer
    
    def _answer_which_feature_delayed(self) -> str:
        """Answer: Which feature is delayed?"""
        answer = "Delayed Features:\n\n"
        
        # Get in-progress and blocked features
        in_progress = self.platform_data.get_features_by_status(self.platform_data.features[0].status) if self.platform_data.features else []
        blocked = self.platform_data.get_features_by_status(self.platform_data.features[0].status) if self.platform_data.features else []
        
        delayed_features = in_progress + blocked
        
        for i, feature in enumerate(delayed_features[:5], 1):
            assigned = feature.assigned_to or "Unassigned"
            days_in_progress = (datetime.utcnow() - feature.created_date).days if feature.created_date else "unknown"
            answer += f"{i}. {feature.name} ({feature.status.value})\n"
            answer += f"   Assigned to: {assigned}\n"
            answer += f"   Duration: {days_in_progress} days\n\n"
        
        if len(delayed_features) > 5:
            answer += f"... and {len(delayed_features) - 5} more features in progress/blocked\n"
        
        return answer
    
    def _answer_developer_assignment(self, question: str) -> str:
        """Answer questions about developer assignments."""
        answer = "Developer Workload:\n\n"
        
        for contrib in sorted(
            self.platform_data.contributors,
            key=lambda c: len(self.platform_data.get_features_by_contributor(c.id)),
            reverse=True
        )[:10]:
            features = self.platform_data.get_features_by_contributor(contrib.id)
            answer += f"• {contrib.name}: {len(features)} features\n"
        
        return answer
    
    def _answer_who_working(self, question: str) -> str:
        """Answer questions about who is working/working on what."""
        answer = "Active Contributors:\n\n"
        
        # Check recent timeline events
        recent_events = [e for e in self.platform_data.timeline_events 
                        if (datetime.utcnow() - e.timestamp).days < 7]
        
        active_contributors = set(e.contributor_id for e in recent_events if e.contributor_id)
        
        if active_contributors:
            answer += "Recently Active (last 7 days):\n"
            for contrib_id in active_contributors:
                contrib = self.platform_data.get_contributor_by_id(contrib_id)
                if contrib:
                    answer += f"• {contrib.name}\n"
        else:
            answer += "No recent activity detected.\n"
        
        answer += "\nAll Contributors by Activity:\n"
        for contrib in sorted(
            self.platform_data.contributors,
            key=lambda c: len(self.platform_data.get_events_by_contributor(c.id)),
            reverse=True
        )[:5]:
            events = self.platform_data.get_events_by_contributor(contrib.id)
            answer += f"• {contrib.name}: {len(events)} activities\n"
        
        return answer
    
    def _answer_general_delay_question(self) -> str:
        """Provide general context about delays."""
        answer = "Project Delay Analysis Summary:\n\n"
        answer += f"Status: {self.analysis_result.severity_score:.0%} Severity\n"
        answer += f"Completed Features: {self.analysis_result.completed_features}/{self.analysis_result.total_features}\n"
        answer += f"In Progress: {self.analysis_result.in_progress_features}\n"
        answer += f"Blocked: {self.analysis_result.blocked_features}\n\n"
        answer += "Main Issues:\n"
        for cause in self.analysis_result.primary_causes[:3]:
            answer += f"• {cause.replace('_', ' ').title()}\n"
        
        return answer

    def _prepare_corpus(self) -> None:
        """Build a retrieval corpus from evidence and feature data."""
        self.corpus_entries = []

        for evidence in self.analysis_result.evidence:
            entry_text = (
                f"Evidence: {evidence.category.value.replace('_', ' ').title()} - {evidence.description}"
            )
            self.corpus_entries.append({
                "text": entry_text,
                "source": "evidence"
            })

        for feature in self.platform_data.features:
            feature_text = (
                f"Feature: {feature.name}. Status: {feature.status.value}. "
                f"Assigned to: {feature.assigned_to or 'unassigned'}. "
                f"Created: {feature.created_date.isoformat() if feature.created_date else 'unknown'}."
            )
            self.corpus_entries.append({
                "text": feature_text,
                "source": "feature"
            })
            
            # Add ownership transfer history to corpus
            history = getattr(feature, "ownership_history", [])
            for entry in history:
                frm = entry.get("previous_owner") or "Unassigned"
                to = entry.get("new_owner") or "Unassigned"
                ts = entry.get("timestamp")
                ts_str = ts.isoformat() if isinstance(ts, datetime) else str(ts)
                entry_text = (
                    f"Ownership Transfer on Feature '{feature.name}': "
                    f"transferred from {frm} to {to} on {ts_str}."
                )
                self.corpus_entries.append({
                    "text": entry_text,
                    "source": "ownership_transfer"
                })

        # Add FAQs to corpus
        if self.faqs:
            for faq in self.faqs:
                if hasattr(faq, "question") and hasattr(faq, "answer"):
                    q, a = faq.question, faq.answer
                elif isinstance(faq, dict) and "question" in faq and "answer" in faq:
                    q, a = faq["question"], faq["answer"]
                else:
                    continue
                self.corpus_entries.append({
                    "text": f"FAQ Question: {q} - Answer: {a}",
                    "source": "faq"
                })

        # Add SRS requirements to corpus
        if self.srs_features:
            for feature in self.srs_features:
                if isinstance(feature, dict):
                    name = feature.get("name", "Unknown")
                    desc = feature.get("description", "")
                    due = feature.get("due_date", "")
                    entry_text = f"SRS Requirement: {name}. Description: {desc}. Due Date: {due}."
                    self.corpus_entries.append({
                        "text": entry_text,
                        "source": "srs_requirement"
                    })

        self.corpus_embeddings = [
            self.embedding_engine.generate_embedding(entry["text"])
            for entry in self.corpus_entries
        ]

    def _retrieve_relevant_context(self, question: str, top_k: int = 5) -> str:
        """Retrieve the most relevant evidence and features for a question."""
        if not question or not self.corpus_entries:
            return "No additional context available."

        query_embedding = self.embedding_engine.generate_embedding(question)

        scores = []
        for idx, embedding in enumerate(self.corpus_embeddings):
            score = self._cosine_similarity(query_embedding, embedding)
            scores.append((score, self.corpus_entries[idx]["text"]))

        top_matches = sorted(scores, key=lambda x: x[0], reverse=True)[:top_k]
        return "\n".join(
            f"- ({score:.2f}) {text}" for score, text in top_matches if score > 0.0
        ) or "No strongly relevant context found."

    @staticmethod
    def _cosine_similarity(
        vec1: List[float],
        vec2: List[float]
    ) -> float:
        """Compute cosine similarity between two vectors."""
        if not vec1 or not vec2 or len(vec1) != len(vec2):
            return 0.0

        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        norm1 = sum(a * a for a in vec1) ** 0.5
        norm2 = sum(b * b for b in vec2) ** 0.5

        if norm1 == 0 or norm2 == 0:
            return 0.0

        return dot_product / (norm1 * norm2)


class ProjectChatbot:
    """
    Main chatbot interface for answering questions about project analysis.
    Maintains conversation context and handles semantic queries.
    """
    
    def __init__(
        self,
        platform_data: PlatformData,
        analysis_result: DelayAnalysisResult,
        provider: Optional[str] = None,
        faqs: Optional[List[Any]] = None,
        srs_features: Optional[List[Any]] = None
    ):
        self.contextualizer = AnalysisContextualizer(
            platform_data=platform_data,
            analysis_result=analysis_result,
            provider=provider,
            faqs=faqs,
            srs_features=srs_features
        )
        self.conversation_history = []
    
    def chat(self, user_message: str) -> str:
        """
        Process user message and generate response.
        
        Args:
            user_message: User's question or statement
        
        Returns:
            Chatbot response
        """
        # Add to history
        self.conversation_history.append({
            "role": "user",
            "message": user_message,
            "timestamp": datetime.utcnow()
        })
        
        # Get answer
        answer = self.contextualizer.answer_question(user_message)
        
        # Add response to history
        self.conversation_history.append({
            "role": "assistant",
            "message": answer,
            "timestamp": datetime.utcnow()
        })
        
        return answer
    
    def get_history(self) -> List[Dict[str, Any]]:
        """Get conversation history."""
        return self.conversation_history
    
    def clear_history(self):
        """Clear conversation history."""
        self.conversation_history = []
