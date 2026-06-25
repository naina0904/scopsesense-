from backend.storage.database import (
    SessionLocal
)

from backend.storage.models import (

    Audit,
    Feature,
    Contributor
)


class AuditRepository:

    def save_audit(

        self,

        project_name,

        health_score,

        semantic_confidence,

        ai_summary
    ):

        db = SessionLocal()

        try:

            audit = Audit(

                project_name=project_name,

                health_score=health_score,

                semantic_confidence=
                    semantic_confidence,

                ai_summary=ai_summary
            )

            db.add(audit)

            db.commit()

            db.refresh(audit)

            return audit

        finally:

            db.close()

    def get_all_audits(self):

        db = SessionLocal()

        audits = (
            db.query(Audit)
            .order_by(Audit.id.desc())
            .all()
        )

        db.close()

        return audits


class FeatureRepository:

    def save_features(
        self,
        features,
        repository=None
    ):

        db = SessionLocal()

        try:

            for feature in features:

                item = Feature(

                    feature_name=
                        feature.get(
                            "feature_name"
                        )
                        or feature.get(
                            "name",
                            "Unknown Feature"
                        ),

                    implementation_score=
                        feature.get(
                            "implementation_score"
                        )
                        or feature.get(
                            "confidence"
                        )
                        or feature.get(
                            "ownership_confidence"
                        ),

                    repository=repository
                )

                db.add(item)

            db.commit()

        finally:

            db.close()

    def get_all_features(self):

        db = SessionLocal()

        features = (
            db.query(Feature)
            .all()
        )

        db.close()

        return features


class ContributorRepository:

    def save_contributors(
        self,
        contributors,
        repository=None
    ):

        db = SessionLocal()

        try:

            for contributor in contributors:

                item = Contributor(

                    developer_name=
                        contributor.get(
                            "developer"
                        )
                        or contributor.get(
                            "name",
                            "Unknown"
                        ),

                    commits=
                        contributor.get(
                            "commits",
                            0
                        )
                        or contributor.get(
                            "total_commits",
                            0
                        ),

                    repository=repository
                )

                db.add(item)

            db.commit()

        finally:

            db.close()

    def get_all_contributors(self):

        db = SessionLocal()

        contributors = (
            db.query(Contributor)
            .all()
        )

        db.close()

        return contributors
