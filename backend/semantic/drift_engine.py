class ArchitecturalDriftEngine:

    def analyze(

        self,

        requirements,

        implementation_results
    ):

        drifts = []

        keywords = [

            "microservice",

            "redis",

            "jwt",

            "rbac",

            "graphql",

            "kafka"
        ]

        for requirement in requirements:

            lower = requirement.lower()

            for keyword in keywords:

                if keyword in lower:

                    found = False

                    for item in implementation_results:

                        if (
                            keyword in
                            item["requirement"]
                            .lower()
                        ):

                            if item[
                                "confidence"
                            ] >= 60:

                                found = True

                    if not found:

                        drifts.append({

                            "technology":
                                keyword,

                            "severity":
                                "High",

                            "message":
                                f"{keyword} mentioned "
                                f"in SRS but "
                                f"implementation "
                                f"confidence low"
                        })

        return drifts