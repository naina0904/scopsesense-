class EngineeringGraphEngine:

    def __init__(self):

        self.nodes = []

        self.edges = []

    # -------------------------------------------------
    # BUILD GRAPH
    # -------------------------------------------------

    def build_graph(

        self,
        repository,
        pr_data=None
    ):

        graph = {

            "nodes": [],
            "edges": []
        }

        pull_requests = []

        try:

            if pr_data and "pull_requests" in pr_data:

                pull_requests = pr_data[
                    "pull_requests"
                ]

            else:

                prs = list(

                    repository.get_pulls(
                        state="all"
                    )
                )

                for pr in prs[:25]:

                    pull_requests.append({

                        "number":
                            pr.number,

                        "title":
                            pr.title,

                        "state":
                            pr.state,

                        "review_count":
                            0,

                        "merged_at":
                            str(pr.merged_at),

                        "labels": [

                            label.name
                            for label in pr.labels
                        ]
                    })

        except:

            pull_requests = []

        for pr in pull_requests:

            pr_node_id = (
                f"pr_{pr['number']}"
            )

            graph["nodes"].append({

                "id":
                    pr_node_id,

                "type":
                    "pull_request",

                "title":
                    pr.get(
                        "title",
                        "unknown"
                    ),

                "state":
                    pr.get(
                        "state",
                        "unknown"
                    )
            })

            if pr.get(
                "review_count",
                0
            ) > 0:

                review_node = (

                    f"review_{pr['number']}"
                )

                graph["nodes"].append({

                    "id":
                        review_node,

                    "type":
                        "review"
                })

                graph["edges"].append({

                    "source":
                        pr_node_id,

                    "target":
                        review_node,

                    "relationship":
                        "reviewed_by"
                })

            if pr.get(
                "merged_at"
            ) not in [None, "None"]:

                merge_node = (

                    f"merge_{pr['number']}"
                )

                graph["nodes"].append({

                    "id":
                        merge_node,

                    "type":
                        "merge_event"
                })

                graph["edges"].append({

                    "source":
                        pr_node_id,

                    "target":
                        merge_node,

                    "relationship":
                        "merged_into"
                })

            for label in pr.get(
                "labels",
                []
            ):

                label_node = (
                    f"label_{label}"
                )

                graph["nodes"].append({

                    "id":
                        label_node,

                    "type":
                        "label",

                    "name":
                        label
                })

                graph["edges"].append({

                    "source":
                        pr_node_id,

                    "target":
                        label_node,

                    "relationship":
                        "tagged_as"
                })

        return graph