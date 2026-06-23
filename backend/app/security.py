# DIY AUTH - COMMENTED OUT: Migrated to Supabase Auth
# This file is kept for reference but not used in production.
# All auth is now handled by Supabase (see app/supabase_auth.py and app/routers/supabase_auth.py)

# from passlib.context import CryptContext
# from jose import jwt, JWTError
# from datetime import datetime, timedelta, timezone
# from fastapi.security import OAuth2PasswordBearer
# from fastapi import Depends, HTTPException
# from sqlalchemy.orm import Session
# from app.dependencies import get_db
# from app.models import User
# import os

# oauth2_scheme = OAuth2PasswordBearer(
#     tokenUrl="login"
# )

# pwd_context = CryptContext(
#     schemes=["bcrypt"],
#     deprecated="auto"
# )

# SECRET_KEY = os.getenv("SECRET_KEY")
# ALGORITHM = os.getenv("ALGORITHM")
# ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES"))
# REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS"))

# def hash_password(password: str):
#     return pwd_context.hash(password)

# def verify_password(
#     plain_password: str,
#     hashed_password: str
# ):
#     return pwd_context.verify(
#         plain_password,
#         hashed_password
#     )

# def create_access_token(data: dict):
#     to_encode = data.copy()

#     expire = datetime.now(timezone.utc) + timedelta(
#         minutes=ACCESS_TOKEN_EXPIRE_MINUTES
#     )

#     to_encode.update({
#         "exp": expire
#     })

#     return jwt.encode(
#         to_encode,
#         SECRET_KEY,
#         algorithm=ALGORITHM
#     )

# def get_current_user(
#     token: str = Depends(oauth2_scheme),
#     db: Session = Depends(get_db)
# ):
#     try:
#         payload = jwt.decode(
#             token,
#             SECRET_KEY,
#             algorithms=[ALGORITHM]
#         )

#         user_id = payload.get("sub")

#         if user_id is None:
#             raise HTTPException(
#                 status_code=401,
#                 detail="Invalid token"
#             )

#     except JWTError:
#         raise HTTPException(
#             status_code=401,
#             detail="Invalid token"
#         )

#     user = db.query(User).filter(
#         User.id == int(user_id)
#     ).first()

#     if not user:
#         raise HTTPException(
#             status_code=401,
#             detail="User not found"
#         )

#     return user

# def create_refresh_token(data: dict):
#     to_encode = data.copy()

#     expire = datetime.now(timezone.utc) + timedelta(
#         days=REFRESH_TOKEN_EXPIRE_DAYS
#     )

#     to_encode.update({
#         "exp": expire
#     })

#     return jwt.encode(
#         to_encode,
#         SECRET_KEY,
#         algorithm=ALGORITHM
#     )

# def create_verification_token(email: str):
#     expire = datetime.now(timezone.utc) + timedelta(hours=24)
#     to_encode = {"sub": email, "type": "verification", "exp": expire}
#     return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

# def create_password_reset_token(email: str):
#     expire = datetime.now(timezone.utc) + timedelta(minutes=15)
#     to_encode = {"sub": email, "type": "reset", "exp": expire}
#     return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

# def verify_token(token: str, token_type: str):
#     try:
#         payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
#         if payload.get("type") != token_type:
#             return None
#         return payload.get("sub")
#     except JWTError:
#         return None

# NOTE: The functions below are still needed for email verification and password reset
# in the Supabase auth flow. They create JWT tokens for email links (not for session auth).
from passlib.context import CryptContext
from jose import jwt, JWTError
from datetime import datetime, timedelta, timezone
import os

pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto"
)

SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    raise ValueError(
        "SECRET_KEY environment variable is not set. "
        "Please set it to a strong random string."
    )
EMAIL_TOKEN_SECRET = os.getenv("EMAIL_TOKEN_SECRET", SECRET_KEY)
ALGORITHM = os.getenv("ALGORITHM", "HS256")

def hash_password(password: str):
    """Hash a password using bcrypt. Kept for any legacy password needs."""
    return pwd_context.hash(password)

def verify_password(
    plain_password: str,
    hashed_password: str
):
    """Verify a password against its bcrypt hash. Kept for any legacy password needs."""
    return pwd_context.verify(
        plain_password,
        hashed_password
    )

def create_verification_token(email: str):
    """Create a JWT token for email verification links (24h expiry)."""
    expire = datetime.now(timezone.utc) + timedelta(hours=24)
    to_encode = {"sub": email, "type": "verification", "exp": expire}
    return jwt.encode(to_encode, EMAIL_TOKEN_SECRET, algorithm=ALGORITHM)

def create_password_reset_token(email: str):
    """Create a JWT token for password reset links (15min expiry)."""
    expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode = {"sub": email, "type": "reset", "exp": expire}
    return jwt.encode(to_encode, EMAIL_TOKEN_SECRET, algorithm=ALGORITHM)

def verify_token(token: str, token_type: str):
    """Verify a JWT token for email verification or password reset."""
    try:
        payload = jwt.decode(token, EMAIL_TOKEN_SECRET, algorithms=[ALGORITHM])
        if payload.get("type") != token_type:
            return None
        return payload.get("sub")
    except JWTError:
        return None