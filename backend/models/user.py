from sqlalchemy import Column, Integer, String
from backend.storage.database import Base

class User(Base):
    __tablename__ = "users"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, nullable=False, index=True)
    email = Column(String, unique=True, nullable=False, index=True)
    from enum import Enum
    class RoleEnum(str, Enum):
        ADMIN = "ADMIN"
        MANAGER = "MANAGER"
        VIEWER = "VIEWER"

    role = Column(Enum(RoleEnum), nullable=False)  # stores values matching Role enum

    def __repr__(self):
        return f"<User id={self.id} username={self.username} role={self.role}>"
