import os

class RequirementMatcher:

    def __init__(
        self,
        vector_store,
        embedding_engine
    ):

        self.vector_store = (
            vector_store
        )

        self.embedding_engine = (
            embedding_engine
        )

    def match_requirements(
        self,
        requirements,
        namespace=None
    ):

        print(
            f"[RequirementMatcher] Matching {len(requirements)} requirements "
            f"against VectorStore under namespace '{namespace}'..."
        )

        matches = []

        for requirement in requirements:

            results = (

                self.vector_store
                .semantic_search(

                    requirement,

                    self.embedding_engine,

                    top_k=3,

                    namespace=namespace
                )
            )

            # Print search results for runtime proof
            matched_docs = results.get("documents", [[]])[0]
            matched_metas = results.get("metadatas", [[]])[0]
            matched_conf = results.get("confidence", [[]])[0]

            print(
                f"[RequirementMatcher] Req: '{requirement}' -> "
                f"Matched {len(matched_docs)} code chunks:"
            )

            for doc, meta, conf in zip(matched_docs, matched_metas, matched_conf):

                path = meta.get("path") if meta else None

                base_path = os.path.basename(path) if path else "Unknown"

                snippet = doc[:80].strip().replace("\n", " ")

                print(
                    f"  - [{base_path}] (Conf: {conf:.4f}): '{snippet}...'"
                )

            matches.append({

                "requirement":
                    requirement,

                "matches":
                    results
            })

        print("[RequirementMatcher] All requirements matched successfully.")

        return matches
