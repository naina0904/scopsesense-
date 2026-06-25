class FeatureIntelligenceEngine:

    def analyze(
        self,
        context
    ):

        features = []

        activity = context.get(
            "activity",
            []
        )

        tasks = context.get(
            "tasks",
            []
        )

        # -------------------------
        # AUTHENTICATION
        # -------------------------

        auth_detected = any(
            "auth" in (
                item.get(
                    "message",
                    ""
                ).lower()
            )
            for item in activity
        )

        features.append({

            "name":
                "Authentication System",

            "status":
                "Completed"
                if auth_detected
                else "Incomplete",

            "confidence":
                86 if auth_detected else 42
        })

        # -------------------------
        # ANALYTICS
        # -------------------------

        analytics_detected = any(
            "analytics" in (
                task.get(
                    "title",
                    ""
                ).lower()
            )
            for task in tasks
        )

        features.append({

            "name":
                "Analytics Dashboard",

            "status":
                "Completed"
                if analytics_detected
                else "Incomplete",

            "confidence":
                78 if analytics_detected else 31
        })

        return features