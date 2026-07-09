class RiskInvestigatorAgent:

    def __init__(
        self,
        llm_manager=None
    ):
        self.llm_manager = llm_manager

    def investigate(

        self,

        predictive_risks,

        dependencies,

        architecture_scores,

        semantic_matches=None
    ):

        investigations = []

        for risk in predictive_risks:

            risk_type = risk.get(
                "type",
                "Unknown"
            )

            severity = risk.get(
                "severity",
                "LOW"
            )

            message = risk.get(
                "message",
                ""
            )

            root_causes = []

            # -----------------------------------
            # REDIS
            # -----------------------------------

            if "redis" in message.lower():

                root_causes.append(

                    "Redis dependency chain affects realtime infrastructure."
                )

                root_causes.append(

                    "WebSocket and Celery pipelines depend on Redis availability."
                )

            # -----------------------------------
            # WEBSOCKET
            # -----------------------------------

            if "websocket" in message.lower():

                root_causes.append(

                    "Realtime event delivery pipeline is tightly coupled."
                )

            # -----------------------------------
            # BURNOUT
            # -----------------------------------

            if "burnout" in message.lower():

                root_causes.append(

                    "Repository ownership distribution is imbalanced."
                )

            # -----------------------------------
            # ARCHITECTURE
            # -----------------------------------

            if severity == "HIGH":

                root_causes.append(

                    "Critical engineering instability detected."
                )

            # -----------------------------------
            # HIGH COUPLING
            # -----------------------------------

            if architecture_scores.get(
                "high_coupling_files"
            ):

                root_causes.append(

                    "High dependency coupling increases cascading failure risk."
                )

            investigations.append({

                "risk":
                    risk_type,

                "severity":
                    severity,

                "message":
                    message,

                "root_causes":
                    root_causes
            })

        # -----------------------------------
        # SEMANTIC DRIFT & ROADMAP GAPS (PHASE 3 AGENTIC REASONING)
        # -----------------------------------
        if semantic_matches:
            unmapped_count = sum(1 for m in semantic_matches if not m.get("issue_key") or m.get("confidence", 1.0) < 0.70)
            if unmapped_count > 0:
                investigations.append({
                    "risk": "Semantic Roadmap Drift",
                    "severity": "HIGH" if unmapped_count > 3 else "MEDIUM",
                    "message": f"Detected {unmapped_count} SRS requirements with missing or low-confidence Jira mappings.",
                    "root_causes": [
                        "Divergent naming conventions between BA specification (SRS) and engineering task tracking (Jira).",
                        "Unbudgeted engineering effort or future roadmap items lacking active sprint allocation."
                    ]
                })

        return investigations