class SemanticMapper:

    def map_project_context(
        self,
        context
    ):

        contributors = (
            len(
                context.get(
                    "contributors",
                    []
                )
            )
        )

        tasks = (
            len(
                context.get(
                    "tasks",
                    []
                )
            )
        )

        activity = (
            len(
                context.get(
                    "activity",
                    []
                )
            )
        )

        return {

            "contributors_detected":
                contributors,

            "tasks_detected":
                tasks,

            "activity_events":
                activity,

            "semantic_alignment":
                "healthy"
        }