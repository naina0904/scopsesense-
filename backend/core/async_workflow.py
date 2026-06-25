from concurrent.futures import (
    ThreadPoolExecutor,
    as_completed
)

from backend.analytics.audit_engine import (
    AuditEngine
)


class AsyncAuditWorkflow:

    MAX_WORKERS = 5

    def __init__(self):

        self.audit_engine = AuditEngine()

    def process_feature(
        self,
        mapping
    ):

        feature = mapping["feature"]

        matched_commits = (
            mapping["matched_commits"]
        )

        return self.audit_engine.evaluate_feature(
            feature,
            matched_commits
        )

    def process_mappings_parallel(
        self,
        mappings
    ):

        results = []

        with ThreadPoolExecutor(
            max_workers=self.MAX_WORKERS
        ) as executor:

            futures = [
                executor.submit(
                    self.process_feature,
                    mapping
                )
                for mapping in mappings
            ]

            for future in as_completed(futures):

                results.append(
                    future.result()
                )

        return results