from git import Repo


class GitMiner:

    # =================================================
    # INIT
    # =================================================

    def __init__(

        self,

        repo_path
    ):

        self.repo_path = repo_path

        self.repo = Repo(repo_path)

        # ---------------------------------------------
        # CHRONOLOGICAL COMMITS
        # ---------------------------------------------

        self.commits = sorted(

            list(
                self.repo.iter_commits(
                    "HEAD"
                )
            ),

            key=lambda c:
                c.committed_datetime.timestamp()
        )

    # =================================================
    # BUILD CONTEXT
    # =================================================

    def build_context(

        self
    ):

        contributors = {}

        activity = []

        for commit in self.commits:

            author = (
                commit.author.name
            )

            timestamp = (
                commit.committed_datetime
            )

            message = (
                commit.message.strip()
            )

            files = []

            try:

                files = list(
                    commit.stats.files.keys()
                )

            except:

                pass

            # -----------------------------------------
            # CONTRIBUTORS
            # ---------------------------------------------

            if author not in contributors:

                contributors[
                    author
                ] = {

                    "name":
                        author,

                    "total_commits":
                        0
                }

            contributors[
                author
            ][
                "total_commits"
            ] += 1

            # -----------------------------------------
            # ACTIVITY
            # ---------------------------------------------

            activity.append({

                "author":
                    author,

                "timestamp":
                    timestamp,

                "message":
                    message,

                "files":
                    files
            })

        return {

            "contributors":

                list(
                    contributors.values()
                ),

            "activity":
                activity,

            "repository_start_date":

                self.get_repository_start_date(),

            "latest_activity_date":

                self.get_latest_activity_date(),

            "activity_gaps":

                self.get_activity_gaps(),

            "commit_velocity":

                self.get_commit_velocity()
        }

    # =================================================
    # REPOSITORY START DATE
    # =================================================

    def get_repository_start_date(

        self
    ):

        if not self.commits:

            return None

        return self.commits[
            0
        ].committed_datetime

    # =================================================
    # LATEST ACTIVITY DATE
    # =================================================

    def get_latest_activity_date(

        self
    ):

        if not self.commits:

            return None

        return self.commits[
            -1
        ].committed_datetime

    # =================================================
    # ACTIVITY GAPS
    # =================================================

    def get_activity_gaps(

        self
    ):

        gaps = []

        if len(self.commits) <= 1:

            return gaps

        for idx in range(

            1,

            len(self.commits)
        ):

            previous_commit = (
                self.commits[idx - 1]
            )

            current_commit = (
                self.commits[idx]
            )

            delta = (

                current_commit.committed_datetime
                -
                previous_commit.committed_datetime
            )

            # -----------------------------------------
            # SIGNIFICANT INACTIVITY GAP
            # -----------------------------------------

            if delta.days >= 14:

                gaps.append({

                    "start":
                        previous_commit
                        .committed_datetime,

                    "end":
                        current_commit
                        .committed_datetime,

                    "gap_days":
                        delta.days,

                    "previous_commit":
                        previous_commit.message.strip(),

                    "next_commit":
                        current_commit.message.strip()
                })

        # ---------------------------------------------
        # DEBUG VALIDATION
        # ---------------------------------------------

        print("\n")
        print("TEMPORAL GAP DEBUG")

        if not gaps:

            print(
                "No significant activity gaps detected."
            )

        for gap in gaps:

            print(gap)

        return gaps

    # =================================================
    # COMMIT VELOCITY
    # =================================================

    def get_commit_velocity(

        self
    ):

        if len(self.commits) <= 1:

            return "low"

        start_date = (
            self.commits[0]
            .committed_datetime
        )

        end_date = (
            self.commits[-1]
            .committed_datetime
        )

        duration = (
            end_date - start_date
        )

        total_days = max(
            1,
            duration.days
        )

        commits_per_week = (

            len(self.commits)
            /
            (total_days / 7)
        )

        # ---------------------------------------------
        # VELOCITY CLASSIFICATION
        # ---------------------------------------------

        if commits_per_week >= 5:

            velocity = "high"

        elif commits_per_week >= 2:

            velocity = "moderate"

        else:

            velocity = "low"

        # ---------------------------------------------
        # DEBUG VALIDATION
        # ---------------------------------------------

        print("\n")
        print("COMMIT VELOCITY DEBUG")

        print(

            f"Total Commits: {len(self.commits)}"
        )

        print(

            f"Project Duration Days: {total_days}"
        )

        print(

            f"Commits Per Week: {commits_per_week:.2f}"
        )

        print(

            f"Velocity: {velocity}"
        )

        return velocity