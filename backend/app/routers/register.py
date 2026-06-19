from app.security import hash_password, create_verification_token, verify_token
from fastapi import APIRouter
from sqlalchemy.orm import Session
from fastapi import HTTPException, Depends
from app.models import User
from app.schemas import UserCreate, VerifyEmailRequest
from app.dependencies import get_db
from app.helpers import existing_user, send_verification_email
router = APIRouter()

@router.post("/register", status_code=201)
def register(
    user: UserCreate,
    db: Session = Depends(get_db)
):
    existing = existing_user(db, user)

    if existing:
        raise HTTPException(
            status_code=400,
            detail="Username or email already exists"
        )

    new_user = User(
        username=user.username,
        email=user.email,
        password_hash=hash_password(
            user.password
        )
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    verification_token = create_verification_token(new_user.email)
    send_verification_email(new_user.email, verification_token)

    return {
        "id": new_user.id,
        "username": new_user.username,
        "email": new_user.email
    }

@router.post("/verify-email")
def verify_email(
    request: VerifyEmailRequest,
    db: Session = Depends(get_db)
):
    email = verify_token(request.token, "verification")
    if not email:
        raise HTTPException(
            status_code=400,
            detail="Invalid or expired verification token"
        )
    
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )
    
    if user.is_verified:
        return {"message": "Email already verified"}

    user.is_verified = True
    db.commit()

    return {"message": "Email verified successfully"}