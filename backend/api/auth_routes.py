from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from backend.auth.jwt_utils import create_access_token, get_current_user, TokenData
from backend.auth.role import Role

router = APIRouter(prefix="/api/v1/auth", tags=["Authentication"])

class LoginRequest(BaseModel):
    user_id: int
    role: Role

class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

@router.post("/login", response_model=LoginResponse)
def login(req: LoginRequest):
    """Simple login endpoint that returns a JWT.
    In a real system this would verify a password or external SSO.
    """
    if req.user_id <= 0:
        raise HTTPException(status_code=400, detail="Invalid user ID")
    token = create_access_token(user_id=req.user_id, role=req.role.value)
    return LoginResponse(access_token=token)

@router.get("/me")
def read_current_user(token: TokenData = Depends(get_current_user)):
    """Return the token payload for the caller."""
    return {"user_id": token.user_id, "role": token.role}
