from fastapi import Depends, HTTPException
from backend.auth.jwt_utils import get_current_user, TokenData
from backend.auth.role import Role
from backend.storage.database import get_db
from backend.storage.models_extended import AuditSession
from sqlalchemy.orm import Session

def has_role(required_role: Role):
    """Dependency that ensures the current user has at least the required role.

    Roles are hierarchical: ADMIN > MANAGER > ANALYST.
    """
    def role_checker(user = Depends(get_current_user)):
        role_hierarchy = {Role.ADMIN: 3, Role.MANAGER: 2, Role.ANALYST: 1}
        user_role = Role(user.role)
        if role_hierarchy[user_role] < role_hierarchy[required_role]:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return user
    return role_checker

def get_owned_session(session_id: int, db: Session = Depends(get_db), current_user: TokenData = Depends(get_current_user)) -> AuditSession:
    """Retrieve an AuditSession ensuring the requesting user owns it.

    Returns the session object or raises HTTPException:
    - 404 if the session does not exist
    - 403 if the session belongs to a different user
    """
    session = db.query(AuditSession).filter(AuditSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Audit session not found")
    if session.user_id != current_user.user_id:
        raise HTTPException(status_code=403, detail="Access to this audit session is forbidden")
    return session
