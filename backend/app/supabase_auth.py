from supabase import create_client, Client
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from app.dependencies import get_db
from sqlalchemy.orm import Session
from app.models import User
import os

SUPABASE_URL = os.getenv("SUPABASE_URL")
if not SUPABASE_URL:
    raise ValueError("SUPABASE_URL environment variable is not set")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
if not SUPABASE_SERVICE_ROLE_KEY:
    raise ValueError("SUPABASE_SERVICE_ROLE_KEY environment variable is not set")

import logging
logger = logging.getLogger(__name__)

_supabase_admin_client = None

def get_supabase_client() -> Client:
    # Always create a fresh client for auth actions so session state doesn't leak across requests
    return create_client(SUPABASE_URL, SUPABASE_ANON_KEY)

def get_supabase_admin_client() -> Client:
    global _supabase_admin_client
    if _supabase_admin_client is None:
        _supabase_admin_client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
    return _supabase_admin_client

def get_supabase_admin():
    return get_supabase_admin_client().auth.admin

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
        err_msg = str(e).lower()
        if "expired" in err_msg or "invalid jwt" in err_msg:
            logger.debug(f"Token expired for request — client should refresh")
        else:
            logger.error("Authentication failed", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
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
        logger.error(f"Failed to create user {email}", exc_info=True)
        print("====== SUPABASE ERROR ======")
        print(repr(e))
        print("============================")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e) if "User not allowed" in str(e) else "Failed to create user"
        )


def sign_in_supabase_user(email: str, password: str) -> dict:
    """Sign in using direct HTTP call to avoid SDK auto-refresh threads."""
    import httpx
    try:
        resp = httpx.post(
            f"{SUPABASE_URL}/auth/v1/token?grant_type=password",
            json={"email": email, "password": password},
            headers={
                "apikey": SUPABASE_ANON_KEY,
                "Content-Type": "application/json",
            },
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
        
        class _User:
            def __init__(self, d):
                self.id = d["id"]
                self.email = d.get("email")
                self.user_metadata = d.get("user_metadata", {})
        
        class _Session:
            def __init__(self, d):
                self.access_token = d["access_token"]
                self.refresh_token = d["refresh_token"]
                self.token_type = d.get("token_type", "bearer")
                self.user = _User(d["user"])
        
        session = _Session(data)
        return {"user": session.user, "session": session}
    except Exception:
        logger.warning(f"Failed login attempt for email: {email}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )


def refresh_supabase_session(refresh_token: str) -> dict:
    """Refresh using direct HTTP call to avoid SDK auto-refresh threads."""
    import httpx
    try:
        resp = httpx.post(
            f"{SUPABASE_URL}/auth/v1/token?grant_type=refresh_token",
            json={"refresh_token": refresh_token},
            headers={
                "apikey": SUPABASE_ANON_KEY,
                "Content-Type": "application/json",
            },
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
        
        class _User:
            def __init__(self, d):
                self.id = d["id"]
                self.email = d.get("email")
                self.user_metadata = d.get("user_metadata", {})
        
        class _Session:
            def __init__(self, d):
                self.access_token = d["access_token"]
                self.refresh_token = d["refresh_token"]
                self.token_type = d.get("token_type", "bearer")
                self.user = _User(d["user"])
        
        session = _Session(data)
        return {"user": session.user, "session": session}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )


def sign_out_supabase_user(refresh_token: str) -> None:
    import httpx
    try:
        httpx.post(
            f"{SUPABASE_URL}/auth/v1/logout",
            json={"refresh_token": refresh_token},
            headers={
                "apikey": SUPABASE_ANON_KEY,
                "Content-Type": "application/json",
            },
            timeout=5,
        )
    except Exception:
        pass


def request_password_reset_supabase(email: str) -> None:
    try:
        get_supabase_client().auth.reset_password_for_email(email)
    except Exception:
        logger.error("Failed to send reset email", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to send reset email"
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
    except Exception:
        logger.error("Failed to update password", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to update password"
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