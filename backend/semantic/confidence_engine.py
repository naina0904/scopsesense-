class ImplementationConfidenceEngine:

    def evaluate(

        self,

        requirement_matches
    ):

        results = []

        for match in requirement_matches:

            requirement = match.get(
                "requirement",
                "Unknown"
            )

            matches = match.get(
                "matches",
                {}
            )

            # Extract documents list from ChromaDB results dict structure
            matched_docs = []
            confidences = []
            if isinstance(matches, dict):
                docs_list = matches.get("documents")
                conf_list = matches.get("confidence")
                if docs_list and len(docs_list) > 0:
                    matched_docs = docs_list[0]
                if conf_list and len(conf_list) > 0:
                    confidences = conf_list[0]

            num_matches = len(matched_docs)
            max_conf = max(confidences) if confidences else 0.0

            confidence = 25

            # -----------------------------------
            # CONFIDENCE CALCULATION
            # -----------------------------------

            if num_matches >= 5 and max_conf >= 0.65:

                confidence = 95

            elif num_matches >= 3 and max_conf >= 0.55:

                confidence = 80

            elif num_matches >= 1 and max_conf >= 0.45:

                confidence = 60

            else:

                confidence = 25

            # -----------------------------------
            # STATUS
            # -----------------------------------

            if confidence >= 85:

                status = "IMPLEMENTED"

            elif confidence >= 60:

                status = "PARTIAL"

            else:

                status = "MISSING"

            results.append({

                "requirement":
                    requirement,

                "confidence":
                    confidence,

                "status":
                    status,

                "matched_chunks":
                    num_matches
            })

        return results