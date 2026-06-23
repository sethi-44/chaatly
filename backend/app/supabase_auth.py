from supabase import create_client, Client
from gotrue import AsyncGoTrueClient
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from app.dependencies import get_db
from sqlalchemy.orm import Session
from app.models import User
import os

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
SUPABASE_JWT_SECRET = os.getenv("SUPABASE_JWT_SECRET")

_supabase: Client = None
_supabase_admin = None

import logging

logger = logging.getLogger(__name__)

def get_supabase_client() -> Client:
    global _supabase, _supabase_admin
    if _supabase is None:
        _supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
        _supabase_admin = _supabase.auth.admin
        logger.info("Supabase client initialized")
    return _supabase

def get_supabase_admin():
    return get_supabase_client().auth.admin

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="supabase/login")


async def get_current_user_supabase(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    try:
        response = get_supabase_client().auth.get_user(token)
        if not response.user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        user_id = response.user.id
        user = db.query(User).filter(User.id == user_id).first()
        
        if not user:
            user = db.query(User).filter(User.email == response.user.email).first()
            if user:
                user.id = user_id
                db.commit()
                db.refresh(user)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found in local database",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        return user
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Authentication failed: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )


def create_supabase_user(email: str, password: str, username: str) -> dict:
    try:
        response = get_supabase_admin().create_user({
            "email": email,
            "password": password,
            "user_metadata": {"username": username},
            "email_confirm": True
        })
        logger.info(f"User registered successfully in Supabase: {username}")
        return {"user": response.user, "session": None}
    except Exception as e:
        logger.error(f"Failed to create user {email}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create user: {str(e)}"
        )


def sign_in_supabase_user(email: str, password: str) -> dict:
    try:
        response = get_supabase_client().auth.sign_in_with_password({
            "email": email,
            "password": password
        })
        return {"user": response.user, "session": response.session}
    except Exception as e:
        logger.warning(f"Failed login attempt for email: {email}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )


def refresh_supabase_session(refresh_token: str) -> dict:
    try:
        response = get_supabase_client().auth.refresh_session(refresh_token)
        return {"user": response.user, "session": response.session}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )


def sign_out_supabase_user(refresh_token: str) -> None:
    try:
        get_supabase_client().auth.sign_out(refresh_token)
    except Exception:
        pass


def request_password_reset_supabase(email: str) -> None:
    try:
        get_supabase_client().auth.reset_password_for_email(email)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to send reset email: {str(e)}"
        )


def verify_otp_supabase(token: str, type: str = "recovery") -> dict:
    """Verify an OTP token (for email verification or password recovery)."""
    try:
        response = get_supabase_client().auth.verify_otp({"token": token, "type": type})
        return {"user": response.user, "session": response.session}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired token"
        )


def update_password_supabase(access_token: str, new_password: str) -> None:
    try:
        get_supabase_client().auth.update_user({"password": new_password}, access_token)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to update password: {str(e)}"
        )


def verify_email_supabase(token: str) -> None:
    try:
        get_supabase_client().auth.verify_otp({"token": token, "type": "signup"})
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired verification token"
        )


def get_supabase_user_by_email(email: str):
    try:
        response = get_supabase_admin().list_users()
        for user in response:
            if user.email == email:
                return user
        return None
    except Exception:
        return None


def delete_supabase_user(user_id: str) -> None:
    try:
        get_supabase_admin().delete_user(user_id)
    except Exception:
        pass