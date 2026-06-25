from datetime import datetime

from github import Github

from backend.intelligence.engineering_graph import (
    EngineeringGraphEngine
)

from backend.intelligence.timeline_engine import (
    TimelineEngine
)

from backend.intelligence.risk_engine import (
    RiskEngine
)

from backend.intelligence.executive_report_engine import (
    ExecutiveReportEngine
)

from backend.intelligence.signal_fetch_engine import (
    SignalFetchEngine
)

from backend.intelligence.scoring_engine import (
    ScoringEngine
)

from backend.memory.repository_memory import (
    RepositoryMemory
)


class RepositoryProfiler:

    # -------------------------------------------------
    # INIT
    # -------------------------------------------------

    def __init__(
        self,
        github_token
    ):

        self.github = Github(
            github_token
        )

        self.graph_engine = (
            EngineeringGraphEngine()
        )

        self.timeline_engine = (
            TimelineEngine()
        )

        self.risk_engine = (
            RiskEngine()
        )

        self.executive_engine = (
            ExecutiveReportEngine()
        )

        self.signal_engine = (
            SignalFetchEngine()
        )

        self.scoring_engine = (
            ScoringEngine()
        )

        self.memory = (
            RepositoryMemory()
        )

    # -------------------------------------------------
    # MAIN PROFILER
    # -------------------------------------------------

    def profile_repository(

        self,
        owner,
        repo
    ):

        repository = self.github.get_repo(
            f"{owner}/{repo}"
        )

        # -------------------------------------------------
        # RECENT SIGNALS
        # -------------------------------------------------

        recent_signals = (

            self.signal_engine
            .fetch_recent_signals(
                repository
            )
        )

        # -------------------------------------------------
        # CORE ANALYSIS
        # -------------------------------------------------

        pull_requests = (

            self._analyze_pull_requests(
                repository
            )
        )

        branches = (

            self._analyze_branches(
                repository
            )
        )

        issues = (

            self._analyze_issues(
                repository
            )
        )

        contributors = (

            self._analyze_contributors(
                repository
            )
        )

        releases = (

            self._analyze_releases(
                repository
            )
        )

        # -------------------------------------------------
        # ENGINEERING GRAPH
        # -------------------------------------------------

        engineering_graph = (

            self.graph_engine.build_graph(

                repository,

                pull_requests
            )
        )

        # -------------------------------------------------
        # TIMELINE
        # -------------------------------------------------

        timeline = (

            self.timeline_engine
            .analyze_timeline(
                repository
            )
        )

        # -------------------------------------------------
        # PROFILE OBJECT
        # -------------------------------------------------

        profile = {

            "repository":
                repo,

            "owner":
                owner,

            "profiled_at":
                str(datetime.utcnow()),

            "metadata":

                self._collect_repository_metadata(
                    repository
                ),

            "recent_signals":
                recent_signals,

            "branches":
                branches,

            "pull_requests":
                pull_requests,

            "engineering_graph":
                engineering_graph,

            "timeline":
                timeline,

            "issues":
                issues,

            "contributors":
                contributors,

            "releases":
                releases
        }

        # -------------------------------------------------
        # WORKFLOW STYLE
        # -------------------------------------------------

        profile[
            "workflow_style"
        ] = (

            self._detect_workflow_style(
                profile
            )
        )

        # -------------------------------------------------
        # ENGINEERING MATURITY
        # -------------------------------------------------

        profile[
            "engineering_maturity"
        ] = (

            self._detect_engineering_maturity(
                profile
            )
        )

        # -------------------------------------------------
        # DELIVERY RISK
        # -------------------------------------------------

        profile[
            "delivery_risk"
        ] = (

            self._detect_delivery_risk(
                profile
            )
        )

        # -------------------------------------------------
        # RISK ANALYSIS
        # -------------------------------------------------

        profile[
            "risk_analysis"
        ] = (

            self.risk_engine
            .analyze_risks(
                profile
            )
        )

        # -------------------------------------------------
        # SCORING ENGINE
        # -------------------------------------------------

        profile[
            "scores"
        ] = (

            self.scoring_engine
            .generate_scores(
                profile
            )
        )

        # -------------------------------------------------
        # EXECUTIVE REPORT
        # -------------------------------------------------

        profile[
            "executive_report"
        ] = (

            self.executive_engine
            .generate_report(
                profile
            )
        )

        # -------------------------------------------------
        # PREVIOUS SNAPSHOT
        # -------------------------------------------------

        previous_snapshot = (

            self.memory.latest_snapshot(
                owner,
                repo
            )
        )

        # -------------------------------------------------
        # EVOLUTION ANALYSIS
        # -------------------------------------------------

        if previous_snapshot:

            comparison = (

                self.memory.compare(

                    previous_snapshot[
                        "data"
                    ],

                    profile
                )
            )

            profile[
                "evolution_analysis"
            ] = comparison

        # -------------------------------------------------
        # SAVE MEMORY SNAPSHOT
        # -------------------------------------------------

        self.memory.save_snapshot(

            owner,
            repo,
            profile
        )

        return profile

    # -------------------------------------------------
    # REPOSITORY METADATA
    # -------------------------------------------------

    def _collect_repository_metadata(

        self,
        repository
    ):

        return {

            "default_branch":
                repository.default_branch,

            "stars":
                repository.stargazers_count,

            "forks":
                repository.forks_count,

            "open_issues":
                repository.open_issues_count,

            "languages":
                repository.languages_url,

            "created_at":
                str(repository.created_at),

            "updated_at":
                str(repository.updated_at)
        }

    # -------------------------------------------------
    # BRANCH ANALYSIS
    # -------------------------------------------------

    def _analyze_branches(

        self,
        repository
    ):

        branches = list(
            repository.get_branches()
        )

        branch_names = [

            branch.name
            for branch in branches
        ]

        release_branches = [

            branch
            for branch in branch_names
            if "release" in branch.lower()
        ]

        hotfix_branches = [

            branch
            for branch in branch_names
            if "hotfix" in branch.lower()
        ]

        feature_branches = [

            branch
            for branch in branch_names
            if "feature" in branch.lower()
        ]

        return {

            "total_branches":
                len(branch_names),

            "branches":
                branch_names,

            "release_branches":
                release_branches,

            "hotfix_branches":
                hotfix_branches,

            "feature_branches":
                feature_branches
        }

    # -------------------------------------------------
    # PR ANALYSIS
    # -------------------------------------------------

    def _analyze_pull_requests(

        self,
        repository
    ):

        prs = repository.get_pulls(
            state="all"
        )

        pr_list = list(prs)

        merged_prs = 0
        open_prs = 0
        draft_prs = 0
        oversized_prs = 0

        review_latency = []

        analyzed_prs = []

        for pr in pr_list[:50]:

            if pr.merged:
                merged_prs += 1

            if pr.state == "open":
                open_prs += 1

            if pr.draft:
                draft_prs += 1

            try:

                files_changed = (
                    pr.changed_files
                )

                if files_changed > 25:
                    oversized_prs += 1

            except:
                pass

            try:

                if pr.created_at and pr.updated_at:

                    latency = (

                        pr.updated_at -
                        pr.created_at

                    ).total_seconds() / 3600

                    review_latency.append(
                        latency
                    )

            except:
                pass

            analyzed_prs.append({

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
            })

        average_review_latency = 0

        if review_latency:

            average_review_latency = round(

                sum(review_latency) /
                len(review_latency),

                2
            )

        return {

            "summary": {

                "total_prs":
                    len(pr_list),

                "merged_prs":
                    merged_prs,

                "open_prs":
                    open_prs,

                "draft_prs":
                    draft_prs,

                "oversized_prs":
                    oversized_prs,

                "average_review_latency_hours":
                    average_review_latency
            },

            "pull_requests":
                analyzed_prs
        }

    # -------------------------------------------------
    # ISSUE ANALYSIS
    # -------------------------------------------------

    def _analyze_issues(

        self,
        repository
    ):

        issues = repository.get_issues(
            state="open"
        )

        issue_list = list(issues)

        labels = {}

        for issue in issue_list[:100]:

            for label in issue.labels:

                label_name = label.name

                labels[label_name] = (

                    labels.get(
                        label_name,
                        0
                    ) + 1
                )

        return {

            "issue_count":
                len(issue_list),

            "top_labels":
                labels
        }

    # -------------------------------------------------
    # CONTRIBUTOR ANALYSIS
    # -------------------------------------------------

    def _analyze_contributors(

        self,
        repository
    ):

        contributors = list(
            repository.get_contributors()
        )

        contributor_data = []

        for contributor in contributors[:25]:

            contributor_data.append({

                "username":
                    contributor.login,

                "contributions":
                    contributor.contributions
            })

        return {

            "contributors":
                contributor_data
        }

    # -------------------------------------------------
    # RELEASE ANALYSIS
    # -------------------------------------------------

    def _analyze_releases(

        self,
        repository
    ):

        releases = list(
            repository.get_releases()
        )

        release_names = [

            release.title
            for release in releases
        ]

        return {

            "release_count":
                len(releases),

            "recent_releases":
                release_names[:10]
        }

    # -------------------------------------------------
    # WORKFLOW STYLE
    # -------------------------------------------------

    def _detect_workflow_style(

        self,
        profile
    ):

        total_prs = profile[
            "pull_requests"
        ][
            "summary"
        ][
            "total_prs"
        ]

        total_branches = profile[
            "branches"
        ][
            "total_branches"
        ]

        if total_prs > 20 and total_branches > 3:

            return "pull_request_driven"

        return "commit_driven"

    # -------------------------------------------------
    # ENGINEERING MATURITY
    # -------------------------------------------------

    def _detect_engineering_maturity(

        self,
        profile
    ):

        total_prs = profile[
            "pull_requests"
        ][
            "summary"
        ][
            "total_prs"
        ]

        releases = profile[
            "releases"
        ][
            "release_count"
        ]

        contributors = len(

            profile[
                "contributors"
            ][
                "contributors"
            ]
        )

        if (
            total_prs > 50 and
            releases > 5 and
            contributors > 5
        ):

            return "high"

        if (
            total_prs > 10 and
            contributors > 2
        ):

            return "medium"

        return "low"

    # -------------------------------------------------
    # DELIVERY RISK
    # -------------------------------------------------

    def _detect_delivery_risk(

        self,
        profile
    ):

        open_issues = profile[
            "issues"
        ][
            "issue_count"
        ]

        oversized_prs = profile[
            "pull_requests"
        ][
            "summary"
        ][
            "oversized_prs"
        ]

        if oversized_prs > 10:

            return "high"

        if open_issues > 50:

            return "issue_overload"

        return "normal"