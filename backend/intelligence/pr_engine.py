class PREngine:

    # -------------------------------------------------
    # ANALYZE PR
    # -------------------------------------------------

    def analyze_pull_request(

        self,
        pr
    ):

        analysis = {

            "number":
                pr.number,

            "title":
                pr.title,

            "state":
                pr.state,

            "review_count":
                pr.comments,

            "labels": [

                label.name
                for label in pr.labels
            ],

            "merged_at":
                str(pr.merged_at)
        }

        return analysis