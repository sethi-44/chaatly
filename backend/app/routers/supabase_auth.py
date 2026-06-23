import os
from fastapi import APIRouter, Depends, HTTPException, Request, status, Body, Response
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr, Field
from app.dependencies import get_db
from app.models import User, RefreshToken
from app.supabase_auth import (
    get_current_user_supabase,
    create_supabase_user,
    sign_in_supabase_user,
    refresh_supabase_session,
    sign_out_supabase_user,
    request_password_reset_supabase,
    update_password_supabase,
    verify_email_supabase,
    verify_otp_supabase,
    get_supabase_user_by_email,
)
from datetime import datetime
from app.rate_limit import limiter

COOKIE_DOMAIN = os.getenv("COOKIE_DOMAIN")
COOKIE_SECURE = os.getenv("COOKIE_SECURE", "true").lower() == "true"

# Enforce secure cookies in production
ENV = os.getenv("ENV", "development")
if ENV == "production" and not COOKIE_SECURE:
    raise RuntimeError("COOKIE_SECURE must be true in production")


def set_auth_cookies(response: Response, access_token: str, refresh_token: str):
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=COOKIE_SECURE,
        samesite="lax",
        max_age=30 * 60,
        path="/",
        domain=COOKIE_DOMAIN,
    )
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=COOKIE_SECURE,
        samesite="lax",
        max_age=7 * 24 * 60 * 60,
        path="/",
        domain=COOKIE_DOMAIN,
    )


def clear_auth_cookies(response: Response):
    response.delete_cookie(key="access_token", path="/", domain=COOKIE_DOMAIN)
    response.delete_cookie(key="refresh_token", path="/", domain=COOKIE_DOMAIN)

router = APIRouter(prefix="/supabase", tags=["supabase-auth"])


class SupabaseRegisterRequest(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class SupabaseLoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: dict


class SupabaseVerifyEmailRequest(BaseModel):
    token: str


class SupabaseRequestPasswordResetRequest(BaseModel):
    email: EmailStr


class SupabaseResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(min_length=8, max_length=128)


class SupabaseChangePasswordRequest(BaseModel):
    current_password: str = Field(min_length=8, max_length=128)
    new_password: str = Field(min_length=8, max_length=128)


class SupabaseUserResponse(BaseModel):
    id: str
    email: str
    username: str | None = None
    email_confirmed_at: datetime | None = None
    created_at: datetime | None = None
    user_metadata: dict | None = None

    class Config:
        from_attributes = True


@router.post("/register", status_code=201, response_model=SupabaseLoginResponse)
@limiter.limit("3/minute")
def supabase_register(
    request: Request,
    response: Response,
    user_data: SupabaseRegisterRequest,
    db: Session = Depends(get_db)
):
    existing = db.query(User).filter(
        (User.username == user_data.username) | (User.email == user_data.email)
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username or email already exists"
        )
    
    result = create_supabase_user(user_data.email, user_data.password, user_data.username)
    supabase_user = result["user"]
    
    if not supabase_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to create user in Supabase"
        )
    
    new_user = User(
        id=supabase_user.id,
        username=user_data.username,
        email=user_data.email,
        password_hash="managed_by_supabase"
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    session = result.get("session")
    if not session:
        sign_in_result = sign_in_supabase_user(user_data.email, user_data.password)
        session = sign_in_result["session"]
    
    set_auth_cookies(response, session.access_token, session.refresh_token)
    
    return {
        "access_token": session.access_token,
        "refresh_token": session.refresh_token,
        "token_type": "bearer",
        "user": {
            "id": supabase_user.id,
            "email": supabase_user.email,
            "username": user_data.username,
        }
    }


@router.post("/login", response_model=SupabaseLoginResponse)
@limiter.limit("5/minute")
def supabase_login(
    request: Request,
    response: Response,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    result = sign_in_supabase_user(form_data.username, form_data.password)
    supabase_user = result["user"]
    session = result["session"]
    
    user = db.query(User).filter(User.id == supabase_user.id).first()
    if not user:
        user = db.query(User).filter(User.email == form_data.username).first()
        if user:
            user.id = supabase_user.id
            db.commit()
            db.refresh(user)
        else:
            user = User(
                id=supabase_user.id,
                username=supabase_user.user_metadata.get("username", form_data.username),
                email=supabase_user.email,
                password_hash="managed_by_supabase"
            )
            db.add(user)
            db.commit()
            db.refresh(user)
    
    token_db = RefreshToken(
        token=session.refresh_token,
        user_id=user.id
    )
    db.add(token_db)
    db.commit()
    
    set_auth_cookies(response, session.access_token, session.refresh_token)
    
    return {
        "access_token": session.access_token,
        "refresh_token": session.refresh_token,
        "token_type": "bearer",
        "user": {
            "id": supabase_user.id,
            "email": supabase_user.email,
            "username": supabase_user.user_metadata.get("username"),
        }
    }


@router.post("/refresh", response_model=SupabaseLoginResponse)
@limiter.limit("10/minute")
def supabase_refresh(
    request: Request,
    response: Response,
    refresh_token: str = Body(embed=True),
    db: Session = Depends(get_db)
):
    result = refresh_supabase_session(refresh_token)
    supabase_user = result["user"]
    session = result["session"]
    
    db.query(RefreshToken).filter(RefreshToken.token == refresh_token).delete()
    
    token_db = RefreshToken(
        token=session.refresh_token,
        user_id=supabase_user.id
    )
    db.add(token_db)
    db.commit()
    
    set_auth_cookies(response, session.access_token, session.refresh_token)
    
    return {
        "access_token": session.access_token,
        "refresh_token": session.refresh_token,
        "token_type": "bearer",
        "user": {
            "id": supabase_user.id,
            "email": supabase_user.email,
            "username": supabase_user.user_metadata.get("username"),
        }
    }


class SupabaseLogoutRequest(BaseModel):
    refresh_token: str


@router.post("/logout")
@limiter.limit("10/minute")
def supabase_logout(
    request: Request,
    response: Response,
    body: SupabaseLogoutRequest,
    db: Session = Depends(get_db)
):
    sign_out_supabase_user(body.refresh_token)
    
    db.query(RefreshToken).filter(RefreshToken.token == body.refresh_token).delete()
    db.commit()
    
    clear_auth_cookies(response)
    
    return {"message": "Logged out successfully"}


@router.post("/request-password-reset")
@limiter.limit("3/minute")
def supabase_request_password_reset(
    request: Request,
    response: Response,
    body: SupabaseRequestPasswordResetRequest,
    db: Session = Depends(get_db)
):
    request_password_reset_supabase(body.email)
    return {"message": "If that email is registered, a password reset link has been sent."}


@router.post("/reset-password")
@limiter.limit("5/minute")
def supabase_reset_password(
    request: Request,
    response: Response,
    body: SupabaseResetPasswordRequest,
    db: Session = Depends(get_db)
):
    # Verify the OTP token (type="recovery" for password reset)
    result = verify_otp_supabase(body.token, type="recovery")
    update_password_supabase(result["session"].access_token, body.new_password)
    return {"message": "Password reset successfully"}


@router.post("/verify-email")
@limiter.limit("10/minute")
def supabase_verify_email(
    request: Request,
    response: Response,
    body: SupabaseVerifyEmailRequest,
    db: Session = Depends(get_db)
):
    verify_email_supabase(body.token)
    return {"message": "Email verified successfully"}


@router.get("/me", response_model=SupabaseUserResponse)
@limiter.limit("60/minute")
def supabase_me(
    request: Request,
    response: Response,
    current_user: User = Depends(get_current_user_supabase)
):
    supabase_user = get_supabase_user_by_email(current_user.email)
    return {
        "id": current_user.id,
        "email": current_user.email,
        "username": current_user.username,
        "email_confirmed_at": supabase_user.email_confirmed_at if supabase_user else None,
        "created_at": supabase_user.created_at if supabase_user else None,
        "user_metadata": supabase_user.user_metadata if supabase_user else None,
    }


@router.post("/change-password")
@limiter.limit("10/minute")
def supabase_change_password(
    request: Request,
    response: Response,
    body: SupabaseChangePasswordRequest,
    current_user: User = Depends(get_current_user_supabase),
    db: Session = Depends(get_db)
):
    try:
        from app.supabase_auth import get_supabase_client
        sign_in_result = get_supabase_client().auth.sign_in_with_password({
            "email": current_user.email,
            "password": body.current_password
        })
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect"
        )
    
    update_password_supabase(sign_in_result.session.access_token, body.new_password)
    
    # Revoke all local refresh tokens for this user (Supabase invalidates sessions server-side)
    db.query(RefreshToken).filter(RefreshToken.user_id == current_user.id).delete()
    db.commit()
    
    # Clear auth cookies since session is invalidated
    clear_auth_cookies(response)
    
    return {"message": "Password changed successfully. Please log in again."}