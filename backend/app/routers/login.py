from app.security import verify_password, hash_password
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from fastapi import HTTPException, Depends,APIRouter
from jose import jwt,JWTError
from app.models import User,RefreshToken
from app.dependencies import get_db
from app.security import create_access_token,create_refresh_token, create_password_reset_token, verify_token
from app.schemas import RefreshRequest, RequestPasswordResetRequest, ResetPasswordRequest
from app.helpers import send_password_reset_email
from dotenv import load_dotenv
import os

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")

router = APIRouter()

@router.post("/login")
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(
        User.email == form_data.username
    ).first()

    if not user:
        raise HTTPException(
            status_code=401,
            detail="Invalid credentials"
        )

    if not verify_password(
        form_data.password,
        user.password_hash
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid credentials"
        )

    # if not user.is_verified:
    #     raise HTTPException(
    #         status_code=403,
    #         detail="Email not verified"
    #     )
    access_token = create_access_token(
        data={"sub": str(user.id)}
    )

    refresh_token = create_refresh_token(
        data={"sub": str(user.id)}
    )

    token_db = RefreshToken(
        token=refresh_token,
        user_id=user.id
    )

    db.add(token_db)
    db.commit()

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }

@router.post("/refresh")
def refresh_token(
        request: RefreshRequest,
        db: Session = Depends(get_db)
    ):
    try:
        payload = jwt.decode(
            request.refresh_token,
            SECRET_KEY,
            algorithms=[ALGORITHM]
        )
    except JWTError:
        raise HTTPException(
            status_code=401,
            detail="Invalid refresh token"
        )

    user_id = payload.get("sub")
    stored_token = db.query(
        RefreshToken
    ).filter(
        RefreshToken.token == request.refresh_token
    ).first()

    if not stored_token:
        raise HTTPException(
            status_code=401,
            detail="Invalid refresh token"
    )
    access_token = create_access_token(
        data={"sub": str(user_id)}
    )
    return {
        "access_token": access_token,
        "token_type": "bearer"
    }

@router.post("/logout")
def logout(
        request: RefreshRequest,
        db: Session = Depends(get_db)
    ):
    db.query(RefreshToken).filter(
        RefreshToken.token == request.refresh_token
    ).delete()

    db.commit()
    return {"message": "Logged out successfully"}

@router.post("/request-password-reset")
def request_password_reset(
    request: RequestPasswordResetRequest,
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.email == request.email).first()
    if user:
        reset_token = create_password_reset_token(user.email)
        send_password_reset_email(user.email, reset_token)
    
    # Always return 200 to prevent email enumeration
    return {"message": "If that email is registered, a password reset link has been sent."}

@router.post("/reset-password")
def reset_password(
    request: ResetPasswordRequest,
    db: Session = Depends(get_db)
):
    email = verify_token(request.token, "reset")
    if not email:
        raise HTTPException(
            status_code=400,
            detail="Invalid or expired password reset token"
        )
    
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )
    
    user.password_hash = hash_password(request.new_password)
    db.commit()

    return {"message": "Password reset successfully"}