import os

from sqlalchemy import (
    create_engine
)

from sqlalchemy.orm import (

    sessionmaker,

    declarative_base
)


# ===================================
# DATABASE URL
# ===================================

DATABASE_URL = os.getenv(

    "DATABASE_URL",

    "postgresql://postgres:12345@localhost/scopesense"
)


# ===================================
# ENGINE
# ===================================

engine = create_engine(

    DATABASE_URL,

    pool_pre_ping=True
)


# ===================================
# SESSION
# ===================================

SessionLocal = sessionmaker(

    autocommit=False,

    autoflush=False,

    bind=engine
)


# ===================================
# BASE
# ===================================

Base = declarative_base()


# ===================================
# DATABASE DEPENDENCY
# ===================================

def get_db():

    db = SessionLocal()

    try:

        yield db

    finally:

        db.close()