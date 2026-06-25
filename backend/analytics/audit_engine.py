from backend.semantic.ai_reasoner import (
    AIReasoner
)

from backend.storage.cache import (
    SemanticCache
)


class AuditEngine:

    BASE_HOURS_PER_COMMIT = 2

    def __init__(self):

        self.ai_reasoner = AIReasoner()

        self.cache = SemanticCache()

    def evaluate_feature(
        self,
        feature,
        matched_commits
    ):

        commit_objects = []

        for item in matched_commits:

            if "commit" in item:
                commit_objects.append(
                    item["commit"]
                )
            else:
                commit_objects.append(item)

        actual_hours = (
            self._estimate_commit_effort(

                feature,

                commit_objects
            )
        )

        expected_hours = max(
            feature["expected_hours"],
            1
        )

        completion_percentage = min(
            100,
            round(
                (
                    actual_hours /
                    expected_hours
                ) * 100,
                2
            )
        )

        if completion_percentage >= 100:
            risk = "LOW"
        elif completion_percentage >= 70:
            risk = "MEDIUM"
        else:
            risk = "HIGH"

        cache_key = self.cache.generate_key(
            feature["feature_name"],
            commit_objects
        )

        if self.cache.exists(cache_key):

            ai_analysis = self.cache.get(
                cache_key
            )

        else:

            ai_analysis = (
                self.ai_reasoner.analyze_feature_completion(
                    feature["feature_name"],
                    commit_objects
                )
            )

            self.cache.set(
                cache_key,
                ai_analysis
            )

        return {
            "feature_name": feature["feature_name"],
            "developer": feature["developer"],
            "expected_hours": expected_hours,
            "actual_hours": actual_hours,
            "completion_percentage": completion_percentage,
            "risk_level": risk,
            "matched_commits": len(commit_objects),
            "effort_reasoning":
                self._effort_reasoning(

                    feature,

                    commit_objects
                ),
            "ai_analysis": ai_analysis
        }

    def _estimate_commit_effort(

        self,

        feature,

        commits
    ):

        total = 0

        for commit in commits:

            files = commit.get(
                "files",
                []
            )

            insertions = commit.get(
                "insertions",
                0
            )

            deletions = commit.get(
                "deletions",
                0
            )

            message = (
                commit.get(
                    "message",
                    ""
                )
                .lower()
            )

            effort = self.BASE_HOURS_PER_COMMIT

            effort += min(
                len(files) * 0.5,
                4
            )

            effort += min(
                (insertions + deletions) / 120,
                5
            )

            if any(
                self._is_test_file(file_path)
                for file_path in files
            ):

                effort += 1

            if any(
                self._is_architecture_file(file_path)
                for file_path in files
            ):

                effort += 2

            if self._semantic_relevance(
                feature,
                message,
                files
            ):

                effort += 1.5

            total += effort

        return round(
            total,
            2
        )

    def _effort_reasoning(

        self,

        feature,

        commits
    ):

        return {

            "method":
                "adaptive_commit_effort",

            "factors": [
                "files_changed",
                "insertions_deletions",
                "test_modifications",
                "architecture_impact",
                "semantic_feature_relevance"
            ],

            "commit_count":
                len(commits),

            "feature":
                feature.get(
                    "feature_name"
                )
        }

    def _is_test_file(

        self,

        file_path
    ):

        lower = file_path.lower()

        return (
            "test" in lower
            or lower.endswith("_spec.py")
            or lower.endswith(".spec.js")
        )

    def _is_architecture_file(

        self,

        file_path
    ):

        lower = file_path.lower()

        return any(

            keyword in lower

            for keyword in [
                "architecture",
                "infra",
                "config",
                "database",
                "celery",
                "websocket",
                "semantic"
            ]
        )

    def _semantic_relevance(

        self,

        feature,

        message,

        files
    ):

        feature_name = (
            feature.get(
                "feature_name",
                ""
            )
            .lower()
        )

        keywords = [

            word

            for word in feature_name.split()

            if len(word) >= 4
        ]

        joined_files = " ".join(files).lower()

        return any(

            keyword in message
            or keyword in joined_files

            for keyword in keywords
        )

    def generate_audit(
        self,
        mappings
    ):

        results = []

        for mapping in mappings:

            feature = mapping["feature"]

            matched_commits = (
                mapping["matched_commits"]
            )

            result = self.evaluate_feature(
                feature,
                matched_commits
            )

            results.append(result)

        return results
