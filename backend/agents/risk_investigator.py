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

        architecture_scores
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

        return investigations