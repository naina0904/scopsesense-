from sqlalchemy import (

    Column,
    Integer,
    String,
    Float,
    Text,
    DateTime
)

from sqlalchemy.sql import (
    func
)

from backend.storage.database import (
    Base
)


# ===================================
# AUDITS
# ===================================

class Audit(Base):

    __tablename__ = "audits"
    __table_args__ = {"extend_existing": True}

    id = Column(

        Integer,

        primary_key=True,

        index=True
    )

    project_name = Column(

        String,

        nullable=False
    )

    health_score = Column(

        Float,

        nullable=False
    )

    semantic_confidence = Column(

        Float,

        nullable=False
    )

    ai_summary = Column(

        Text,

        nullable=True
    )

    created_at = Column(

        DateTime(timezone=True),

        server_default=func.now()
    )

    raw_semantic_features_count = Column(

        Integer,

        default=54
    )

    normalized_semantic_features_count = Column(

        Integer,

        default=39
    )


# ===================================
# FEATURES
# ===================================

class Feature(Base):

    __tablename__ = "features"
    __table_args__ = {"extend_existing": True}

    id = Column(

        Integer,

        primary_key=True,

        index=True
    )

    feature_name = Column(

        String,

        nullable=False
    )

    implementation_score = Column(

        Float,

        nullable=True
    )

    repository = Column(

        String,

        nullable=True
    )

    created_at = Column(

        DateTime(timezone=True),

        server_default=func.now()
    )


# ===================================
# CONTRIBUTORS
# ===================================

class Contributor(Base):

    __tablename__ = "contributors"
    __table_args__ = {"extend_existing": True}

    id = Column(

        Integer,

        primary_key=True,

        index=True
    )

    developer_name = Column(

        String,

        nullable=False
    )

    commits = Column(

        Integer,

        default=0
    )

    repository = Column(

        String,

        nullable=True
    )

    created_at = Column(

        DateTime(timezone=True),

        server_default=func.now()
    )


# ===================================
# REPOSITORY SYNC
# ===================================

class RepositorySync(Base):

    __tablename__ = "repository_syncs"
    __table_args__ = {"extend_existing": True}

    id = Column(

        Integer,

        primary_key=True,

        index=True
    )

    owner = Column(

        String,

        nullable=False
    )

    repo = Column(

        String,

        nullable=False
    )

    latest_commit_sha = Column(

        String,

        nullable=True
    )

    last_synced_at = Column(

        DateTime,

        nullable=True
    )