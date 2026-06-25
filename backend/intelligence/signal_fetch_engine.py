from datetime import datetime
from datetime import timedelta


class SignalFetchEngine:

    # -------------------------------------------------
    # FETCH RECENT SIGNALS
    # -------------------------------------------------

    def fetch_recent_signals(

        self,
        repository,
        days=7
    ):

        since = (

            datetime.utcnow() -
            timedelta(days=days)
        )

        signals = {

            "pull_requests": [],
            "issues": [],
            "commits": [],
            "releases": []
        }

        # -------------------------------------------------
        # RECENT PRS
        # -------------------------------------------------

        try:

            prs = repository.get_pulls(
                state="all",
                sort="updated",
                direction="desc"
            )

            for pr in prs:

                updated_at = (
                    pr.updated_at
                )

                if updated_at < since:

                    break

                signals[
                    "pull_requests"
                ].append({

                    "number":
                        pr.number,

                    "title":
                        pr.title,

                    "state":
                        pr.state,

                    "updated_at":
                        str(pr.updated_at),

                    "merged":
                        pr.merged
                })

        except:
            pass

        # -------------------------------------------------
        # RECENT ISSUES
        # -------------------------------------------------

        try:

            issues = repository.get_issues(
                state="all",
                sort="updated",
                direction="desc"
            )

            for issue in issues:

                updated_at = (
                    issue.updated_at
                )

                if updated_at < since:

                    break

                signals[
                    "issues"
                ].append({

                    "number":
                        issue.number,

                    "title":
                        issue.title,

                    "state":
                        issue.state,

                    "updated_at":
                        str(issue.updated_at)
                })

        except:
            pass

        # -------------------------------------------------
        # RECENT COMMITS
        # -------------------------------------------------

        try:

            commits = repository.get_commits()

            for commit in commits[:50]:

                commit_date = (

                    commit.commit.author.date
                )

                if commit_date < since:

                    break

                signals[
                    "commits"
                ].append({

                    "sha":
                        commit.sha,

                    "message":
                        commit.commit.message,

                    "author":
                        commit.commit.author.name,

                    "date":
                        str(commit_date)
                })

        except:
            pass

        # -------------------------------------------------
        # RECENT RELEASES
        # -------------------------------------------------

        try:

            releases = repository.get_releases()

            for release in releases:

                published_at = (
                    release.published_at
                )

                if (
                    published_at and
                    published_at < since
                ):

                    break

                signals[
                    "releases"
                ].append({

                    "name":
                        release.title,

                    "published_at":
                        str(
                            release.published_at
                        )
                })

        except:
            pass

        return signals