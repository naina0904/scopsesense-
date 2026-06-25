import os
import time
import requests
from tenacity import retry, stop_after_attempt, wait_exponential
from backend.observability.structured_logger import get_logger

logger = get_logger(__name__)

class GitHubClient:

    def __init__(self, token: str = None):
        """
        Initialize the GitHub client.
        If a token is provided, use it directly; otherwise fallback to GITHUB_TOKEN env variable.
        """

        self.base_url = (
            "https://api.github.com"
        )

        self.token = token or os.getenv(
            "GITHUB_TOKEN"
        )

        self.headers = {

            "Authorization":
                f"Bearer {self.token}",

            "Accept":
                "application/vnd.github+json"
        }

    # ===================================
    # SAFE REQUEST
    # ===================================

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def _request(
        self,
        url,
        params=None,
        return_links=False
    ):
        for attempt in range(3):
            try:
                response = requests.get(
                    url,
                    headers=self.headers,
                    params=params
                )

                # -----------------------------
                # RATE LIMIT HANDLING
                # -----------------------------
                remaining = int(
                    response.headers.get(
                        "X-RateLimit-Remaining",
                        1
                    )
                )

                if remaining < 5:
                    print(
                        "[WARN] GitHub rate limit low."
                    )
                    time.sleep(5)

                response.raise_for_status()

                if return_links:
                    return response.json(), response.links
                return response.json()

            except Exception as e:
                logger.error("github_request_failed", attempt=attempt + 1, error=str(e))
                time.sleep(2)
                raise

        if return_links:
            return [], {}
        return []

    # ===================================
    # PAGINATION ENGINE
    # ===================================

    def _paginate(
        self,
        url,
        params=None,
        max_pages=None
    ):
        results = []
        page = 1
        
        if params is None:
            params = {}
        if "per_page" not in params:
            params["per_page"] = 100

        while url:
            # -------------------------
            # HARD PAGE CAP
            # -------------------------
            if max_pages and page > max_pages:
                break

            data, links = self._request(
                url,
                params,
                return_links=True
            )

            if not data:
                break

            results.extend(data)

            if 'next' in links:
                url = links['next']['url']
                params = None  # URL from links already has pagination parameters
                page += 1
            else:
                break

        return results

    # ===================================
    # USER REPOSITORIES
    # ===================================

    def get_user_repositories(

        self,

        owner
    ):

        url = (

            f"{self.base_url}/users/"

            f"{owner}/repos"
        )

        repos = self._paginate(url)

        results = []

        for repo in repos:

            results.append({

                "id":
                    repo.get("id"),

                "name":
                    repo.get("name"),

                "full_name":
                    repo.get("full_name"),

                "private":
                    repo.get("private"),

                "default_branch":
                    repo.get("default_branch"),

                "updated_at":
                    repo.get("updated_at")
            })

        return results

    # ===================================
    # REPOSITORY DETAILS
    # ===================================

    def get_repo_details(

        self,

        owner,

        repo
    ):

        url = (

            f"{self.base_url}/repos/"

            f"{owner}/{repo}"
        )

        return self._request(url)

    # ===================================
    # COMMITS
    # ===================================

    def get_commits(
        self,
        owner,
        repo,
        since=None,
        max_pages=None
    ):
        """
        Fetch commits for a repository.

        max_pages caps the number of API pages fetched
        (100 commits per page). Default 5 = 500 commits
        maximum, which is sufficient for analysis while
        avoiding multi-minute pagination on large repos.
        Pass max_pages=None to fetch all commits.
        """

        url = (

            f"{self.base_url}/repos/"

            f"{owner}/{repo}/commits"
        )

        params = {}

        if since:

            params["since"] = since

        commits = self._paginate(

            url,

            params,

            max_pages=max_pages
        )

        results = []

        for commit in commits:

            commit_data = commit.get(

                "commit",

                {}
            )

            author = commit_data.get(

                "author",

                {}
            )

            results.append({

                "sha":
                    commit.get("sha"),

                "message":
                    commit_data.get("message"),

                "author":
                    author.get("name"),

                "date":
                    author.get("date")
            })

        return results

    # ===================================
    # PULL REQUESTS
    # ===================================

    def get_pull_requests(

        self,

        owner,

        repo,

        state="all"
    ):

        url = (

            f"{self.base_url}/repos/"

            f"{owner}/{repo}/pulls"
        )

        prs = self._paginate(

            url,

            {

                "state":
                    state
            }
        )

        results = []

        for pr in prs:

            results.append({

                "id":
                    pr.get("id"),

                "number":
                    pr.get("number"),

                "title":
                    pr.get("title"),

                "body":
                    pr.get("body"),

                "state":
                    pr.get("state"),

                "created_at":
                    pr.get("created_at"),

                "merged_at":
                    pr.get("merged_at"),

                "html_url":
                    pr.get("html_url"),

                "user":
                    pr.get(

                        "user",

                        {}
                    ).get("login")
            })

        return results

    # ===================================
    # PULL REQUEST COMMITS
    # ===================================

    def get_pr_commits(
        self,
        owner,
        repo,
        pr_number
    ):
        url = f"{self.base_url}/repos/{owner}/{repo}/pulls/{pr_number}/commits"
        commits = self._paginate(url)
        
        results = []
        for commit in commits:
            commit_data = commit.get("commit", {})
            author = commit_data.get("author", {})
            results.append({
                "sha": commit.get("sha"),
                "message": commit_data.get("message"),
                "author": author.get("name"),
                "date": author.get("date"),
                "html_url": commit.get("html_url"),
                "stats": commit.get("stats", {})
            })
            
        return results
    # ===================================
    # PULL REQUEST REVIEWS
    # ===================================

    def get_pr_reviews(self, owner, repo, pr_number):
        url = f"{self.base_url}/repos/{owner}/{repo}/pulls/{pr_number}/reviews"
        reviews = self._paginate(url)
        
        results = []
        for review in reviews:
            results.append({
                "id": review.get("id"),
                "user": review.get("user", {}).get("login"),
                "body": review.get("body"),
                "state": review.get("state"),
                "submitted_at": review.get("submitted_at")
            })
            
        return results

    # ===================================
    # ISSUE COMMENTS
    # ===================================

    def get_issue_comments(self, owner, repo, issue_number):
        url = f"{self.base_url}/repos/{owner}/{repo}/issues/{issue_number}/comments"
        comments = self._paginate(url)
        
        results = []
        for comment in comments:
            results.append({
                "id": comment.get("id"),
                "user": comment.get("user", {}).get("login"),
                "body": comment.get("body"),
                "created_at": comment.get("created_at"),
                "updated_at": comment.get("updated_at")
            })
            
        return results

    # ===================================
    # ISSUES
    # ===================================

    def get_issues(
        self,
        owner,
        repo,
        state="all",
        since=None
    ):

        url = (

            f"{self.base_url}/repos/"

            f"{owner}/{repo}/issues"
        )

        params = {"state": state}
        if since:
            params["since"] = since

        issues = self._paginate(
            url,
            params
        )

        results = []

        for issue in issues:

            # Skip pull requests

            if "pull_request" in issue:

                continue

            milestone = issue.get("milestone")

            milestone_info = None

            if milestone:

                milestone_info = {

                    "id":
                        milestone.get("id"),

                    "number":
                        milestone.get("number"),

                    "title":
                        milestone.get("title"),

                    "description":
                        milestone.get("description"),

                    "state":
                        milestone.get("state"),

                    "due_on":
                        milestone.get("due_on")
                }

            results.append({

                "id":
                    issue.get("id"),

                "number":
                    issue.get("number"),

                "title":
                    issue.get("title"),

                "state":
                    issue.get("state"),

                "created_at":
                    issue.get("created_at"),

                "updated_at":
                    issue.get("updated_at"),

                "closed_at":
                    issue.get("closed_at"),

                "user":
                    issue.get(

                        "user",

                        {}
                    ).get("login"),

                "assignees":
                    [a.get("login") for a in issue.get("assignees", [])],

                "milestone":
                    milestone_info
            })

        return results

    # ===================================
    # MILESTONES
    # ===================================

    def get_milestones(

        self,

        owner,

        repo,

        state="all"
    ):
        """Fetch milestones for a repository.

        Returns a list of milestone dictionaries with keys:
        id, number, title, description, state, due_on, creator, open_issues, closed_issues, created_at, updated_at.
        """
        url = (

            f"{self.base_url}/repos/"

            f"{owner}/{repo}/milestones"
        )
        milestones = self._paginate(

            url,

            {

                "state":
                    state
            }
        )
        # Normalise fields to match the structure used elsewhere in the code.
        results = []
        for ms in milestones:

            results.append({

                "id":
                    ms.get("id"),

                "number":
                    ms.get("number"),

                "title":
                    ms.get("title"),

                "description":
                    ms.get("description"),

                "state":
                    ms.get("state"),

                "due_on":
                    ms.get("due_on"),

                "creator":
                    ms.get("creator", {}),

                "open_issues":
                    ms.get("open_issues"),

                "closed_issues":
                    ms.get("closed_issues"),

                "created_at":
                    ms.get("created_at"),

                "updated_at":
                    ms.get("updated_at")
            })

        return results

    # ===================================
    # CONTRIBUTORS
    # ===================================

    def get_contributors(

        self,

        owner,

        repo
    ):

        url = (

            f"{self.base_url}/repos/"

            f"{owner}/{repo}/contributors"
        )

        contributors = self._paginate(url)

        results = []

        for contributor in contributors:

            results.append({

                "developer":
                    contributor.get("login"),

                "commits":
                    contributor.get("contributions")
            })

        return results

    # ===================================
    # REPOSITORY TREE
    # ===================================

    def get_repo_tree(

        self,

        owner,

        repo,

        branch="main"
    ):

        # -----------------------------------
        # GET BRANCH SHA
        # -----------------------------------

        branch_url = (

            f"{self.base_url}/repos/"

            f"{owner}/{repo}/branches/"

            f"{branch}"
        )

        branch_data = (

            self._request(branch_url)

        )

        sha = (

            branch_data

            .get("commit", {})

            .get("sha")
        )

        if not sha:

            return []

        # -----------------------------------
        # GET TREE
        # -----------------------------------

        tree_url = (

            f"{self.base_url}/repos/"

            f"{owner}/{repo}/git/trees/"

            f"{sha}"
        )

        tree_data = self._request(

            tree_url,

            {

                "recursive": 1
            }
        )

        return tree_data.get(

            "tree",

            []
        )