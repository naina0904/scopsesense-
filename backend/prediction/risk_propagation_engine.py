class RiskPropagationEngine:

    def analyze(

        self,

        dependency_results,

        predictive_risks
    ):

        propagation = []

        # -----------------------------------
        # BUILD DEPENDENCY MAP
        # -----------------------------------

        dependency_map = {}

        for item in dependency_results:

            file_name = item.get(
                "file",
                "Unknown"
            )

            imports = item.get(
                "imports",
                []
            )

            dependency_map[
                file_name
            ] = imports

        # -----------------------------------
        # PROPAGATE RISKS
        # -----------------------------------

        for risk in predictive_risks:

            message = risk.get(
                "message",
                ""
            )

            affected = []

            for file_name, imports in (

                dependency_map.items()
            ):

                for imp in imports:

                    if imp.lower() in (
                        message.lower()
                    ):

                        affected.append(
                            file_name
                        )

            propagation.append({

                "risk":
                    message,

                "affected_files":
                    affected,

                "impact_radius":
                    len(affected)
            })

        return propagation