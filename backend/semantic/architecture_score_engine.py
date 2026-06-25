class ArchitectureScoreEngine:

    def evaluate(
        self,
        dependencies
    ):

        total_dependencies = 0

        high_coupling_files = []

        circular_risk = False

        # -----------------------------------
        # ANALYZE DEPENDENCIES
        # -----------------------------------

        for item in dependencies:

            imports = item.get(
                "imports",
                []
            )

            total_dependencies += len(
                imports
            )

            if len(imports) > 10:

                high_coupling_files.append(
                    item["file"]
                )

        # -----------------------------------
        # SIMPLE CIRCULAR DETECTION
        # -----------------------------------

        file_map = {

            item["file"]: item["imports"]

            for item in dependencies
        }

        for file, imports in file_map.items():

            for dependency in imports:

                dep_file = (
                    dependency.split(".")[-1]
                    + ".py"
                )

                if dep_file in file_map:

                    if file.replace(
                        ".py",
                        ""
                    ) in file_map[
                        dep_file
                    ]:

                        circular_risk = True

        # -----------------------------------
        # SCORING
        # -----------------------------------

        coupling_score = max(

            0,

            100 - total_dependencies
        )

        stability_score = (

            95

            if not circular_risk

            else 60
        )

        complexity_score = max(

            0,

            100 - (
                len(high_coupling_files)
                * 10
            )
        )

        return {

            "coupling_score":
                coupling_score,

            "stability_score":
                stability_score,

            "complexity_score":
                complexity_score,

            "high_coupling_files":
                high_coupling_files,

            "circular_dependency_risk":
                circular_risk
        }