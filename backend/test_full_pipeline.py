from pprint import pprint

from backend.core.audit_workflow import (
    AuditWorkflow
)

from backend.intelligence.git_miner import (
    GitMiner
)


# =====================================================
# VALIDATION REPOSITORIES
# =====================================================

VALIDATION_REPOS = [

    {
        "name":
            "healthy-enterprise",

        "repo_path":
            r"C:\Users\Raghuram\Desktop\AI\validation-repos\healthy-enterprise",

        "srs_path":
            r"C:\Users\Raghuram\Desktop\AI\validation-repos\healthy-enterprise\docs\srs.txt"
    },

    {
        "name":
            "delayed-project",

        "repo_path":
            r"C:\Users\Raghuram\Desktop\AI\validation-repos\delayed-project",

        "srs_path":
            r"C:\Users\Raghuram\Desktop\AI\validation-repos\delayed-project\docs\srs.txt"
    }
]


# =====================================================
# RUN VALIDATION
# =====================================================

def run_validation():

    workflow = AuditWorkflow()

    for repo in VALIDATION_REPOS:

        print("\n")
        print("=" * 80)

        print(
            f"RUNNING VALIDATION: {repo['name']}"
        )

        print("=" * 80)

        try:

            # -------------------------------------------------
            # REAL GIT INTELLIGENCE
            # -------------------------------------------------

            miner = GitMiner(

                repo["repo_path"]
            )

            context = miner.build_context()

            # Inject repo_path and vector_namespace to trigger the optional semantic code intelligence pipeline
            context["repo_path"] = repo["repo_path"]
            context["vector_namespace"] = f"validation_{repo['name']}"

            # -------------------------------------------------
            # EXECUTE AUDIT
            # -------------------------------------------------

            result = workflow.execute_audit(

                repository_context=
                    context,

                srs_path=
                    repo["srs_path"]
            )

            # -------------------------------------------------
            # SEMANTIC FEATURES
            # -------------------------------------------------

            print("\n")
            print("SEMANTIC FEATURES")
            print("-" * 50)

            pprint(

                result.get(
                    "semantic_features"
                )
            )

            # -------------------------------------------------
            # TIMELINE ANALYSIS
            # -------------------------------------------------

            print("\n")
            print("TIMELINE ANALYSIS")
            print("-" * 50)

            pprint(

                result.get(
                    "timeline_analysis"
                )
            )

            # -------------------------------------------------
            # CONTRIBUTOR ANALYSIS
            # -------------------------------------------------

            print("\n")
            print("CONTRIBUTOR ANALYSIS")
            print("-" * 50)

            pprint(

                result.get(
                    "contributors"
                )
            )

            # -------------------------------------------------
            # FEATURE OWNERSHIP
            # -------------------------------------------------

            print("\n")
            print("FEATURE OWNERSHIP")
            print("-" * 50)

            pprint(

                result.get(
                    "feature_ownership"
                )
            )

            # -------------------------------------------------
            # HOTSPOT ANALYSIS
            # -------------------------------------------------

            print("\n")
            print("HOTSPOT ANALYSIS")
            print("-" * 50)

            pprint(

                result.get(
                    "hotspots"
                )
            )

            # -------------------------------------------------
            # INSIGHT NARRATIVES
            # -------------------------------------------------

            print("\n")
            print("INSIGHT NARRATIVES")
            print("-" * 50)

            pprint(

                result.get(
                    "insights"
                )
            )

            # -------------------------------------------------
            # CAUSALITY ANALYSIS
            # -------------------------------------------------

            print("\n")
            print("CAUSALITY ANALYSIS")
            print("-" * 50)

            pprint(

                result.get(
                    "causality"
                )
            )

            # -------------------------------------------------
            # ARCHITECTURE & SCORES (SEMANTIC OPTIONAL PIPELINE)
            # -------------------------------------------------
            print("\n")
            print("ARCHITECTURE & SCORES")
            print("-" * 50)
            print("Architecture Scores:")
            pprint(result.get("architecture_scores"))
            print("Dependency edges found:", len(result.get("dependencies", [])))
            print("Implementation Analysis matched requirements:", len(result.get("implementation_analysis", [])))

            print("\n")
            print("=" * 80)
            print("VALIDATION COMPLETED")
            print("=" * 80)

        except Exception as e:

            print("\n")
            print("=" * 80)
            print("VALIDATION FAILED")
            print("=" * 80)

            print(str(e))


# =====================================================
# MAIN
# =====================================================

if __name__ == "__main__":

    run_validation()