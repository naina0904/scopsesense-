from backend.storage.database import (
    engine
)

from backend.storage.models import (
    Base
)

Base.metadata.create_all(
    bind=engine
)

print(
    "Database tables created."
)