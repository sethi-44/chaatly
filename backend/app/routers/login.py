from app.security import verify_password
from fastapi import APIRouter
from sqlalchemy.orm import Session
from fastapi import HTTPException, Depends
from app.models import User
from app.schemas import LoginRequest
from app.dependencies import get_db

router = APIRouter()

@router.post("/login")
def login(
    credentials: LoginRequest,
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(
        User.email == credentials.email
    ).first()

    if not user:
        raise HTTPException(
            status_code=401,
            detail="Invalid credentials"
        )

    if not verify_password(
        credentials.password,
        user.password_hash
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid credentials"
        )

    return {
        "message": "Login successful"
    }