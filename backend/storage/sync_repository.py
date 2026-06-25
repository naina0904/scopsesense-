from backend.storage.database import (
    SessionLocal
)

from backend.storage.models import (
    RepositorySync
)


class SyncRepository:

    def __init__(self):

        self.SessionLocal = SessionLocal

    # -----------------------------------
    # GET LAST SYNC
    # -----------------------------------

    def get_last_sync(

        self,

        owner,

        repo
    ):

        db = self.SessionLocal()

        try:

            return (

                db.query(
                    RepositorySync
                )

                .filter(

                    RepositorySync.owner == owner,

                    RepositorySync.repo == repo
                )

                .first()
            )

        finally:

            db.close()

    # -----------------------------------
    # SAVE / UPDATE
    # -----------------------------------

    def save_sync(

        self,

        owner,

        repo,

        latest_commit_sha,

        last_synced_at
    ):

        db = self.SessionLocal()

        try:

            existing = (

                db.query(
                    RepositorySync
                )

                .filter(

                    RepositorySync.owner == owner,

                    RepositorySync.repo == repo
                )

                .first()
            )

            if existing:

                existing.latest_commit_sha = (
                    latest_commit_sha
                )

                existing.last_synced_at = (
                    last_synced_at
                )

            else:

                sync = RepositorySync(

                    owner=owner,

                    repo=repo,

                    latest_commit_sha=
                        latest_commit_sha,

                    last_synced_at=
                        last_synced_at
                )

                db.add(sync)

            db.commit()

        finally:

            db.close()