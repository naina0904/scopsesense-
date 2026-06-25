import os
import shutil
from git import Repo


class RepoCloner:

    def __init__(self):

        self.base_dir = "data/repos"

        os.makedirs(
            self.base_dir,
            exist_ok=True
        )

    def clone_repository(
        self,
        repo_url,
        repo_name
    ):

        repo_path = (
            f"{self.base_dir}/{repo_name}"
        )

        if os.path.exists(repo_path):

            shutil.rmtree(repo_path)

        Repo.clone_from(
            repo_url,
            repo_path
        )

        return repo_path