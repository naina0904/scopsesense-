"""Database migration to add normalization metadata columns to the audits table."""

from sqlalchemy import text

from backend.storage.database import engine


def upgrade():
    with engine.connect() as conn:
        conn.execute(text(
            """
            ALTER TABLE audits
            ADD COLUMN IF NOT EXISTS raw_semantic_features_count INTEGER DEFAULT 54,
            ADD COLUMN IF NOT EXISTS normalized_semantic_features_count INTEGER DEFAULT 39
            """
        ))
        conn.commit()


def downgrade():
    with engine.connect() as conn:
        conn.execute(text(
            """
            ALTER TABLE audits
            DROP COLUMN IF EXISTS raw_semantic_features_count,
            DROP COLUMN IF EXISTS normalized_semantic_features_count
            """
        ))
        conn.commit()
