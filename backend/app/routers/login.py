# DIY AUTH - COMMENTED OUT: Migrated to Supabase Auth
# This file is kept for reference but not used in production.
# All auth is now handled by Supabase (see app/supabase_auth.py and app/routers/supabase_auth.py)

# from app.security import verify_password, hash_password, SECRET_KEY, ALGORITHM, create_access_token, create_refresh_token, create_password_reset_token, verify_token
# from fastapi.security import OAuth2PasswordRequestForm
# from sqlalchemy.orm import Session
# from fastapi import HTTPException, Depends, APIRouter, Request
# from jose import jwt, JWTError
# from app.models import User, RefreshToken
# from app.dependencies import get_db
# from app.schemas import RefreshRequest, RequestPasswordResetRequest, ResetPasswordRequest
# from app.helpers import send_password_reset_email
# from app.rate_limit import limiter

# router = APIRouter()

# @router.post("/login")
# @limiter.limit("5/minute")
# def login(
#     request: Request,
#     form_data: OAuth2PasswordRequestForm = Depends(),
#     db: Session = Depends(get_db)
# ):
#     user = db.query(User).filter(
#         User.email == form_data.username
#     ).first()

#     if not user:
#         raise HTTPException(
#             status_code=401,
#             detail="Invalid credentials"
#         )

#     if not verify_password(
#         form_data.password,
#         user.password_hash
#     ):
#         raise HTTPException(
#             status_code=401,
#             detail="Invalid credentials"
#         )

#     # if not user.is_verified:
#     #     raise HTTPException(
#     #         status_code=403,
#     #         detail="Email not verified"
#     #     )
#     access_token = create_access_token(
#         data={"sub": str(user.id)}
#     )

#     refresh_token = create_refresh_token(
#         data={"sub": str(user.id)}
#     )

#     token_db = RefreshToken(
#         token=refresh_token,
#         user_id=user.id
#     )

#     db.add(token_db)
#     db.commit()

#     return {
#         "access_token": access_token,
#         "refresh_token": refresh_token,
#         "token_type": "bearer"
#     }

# @router.post("/refresh")
# @limiter.limit("10/minute")
# def refresh_token(
#     request: Request,
#     body: RefreshRequest,
#     db: Session = Depends(get_db)
# ):
#     try:
#         payload = jwt.decode(
#             body.refresh_token,
#             SECRET_KEY,
#             algorithms=[ALGORITHM]
#         )
#     except JWTError:
#         raise HTTPException(
#             status_code=401,
#             detail="Invalid refresh token"
#         )

#     user_id = payload.get("sub")
#     stored_token = db.query(
#         RefreshToken
#     ).filter(
#         RefreshToken.token == body.refresh_token
#     ).first()

#     if not stored_token:
#         raise HTTPException(
#             status_code=401,
#             detail="Invalid refresh token"
#     )
#     access_token = create_access_token(
#         data={"sub": str(user_id)}
#     )
#     return {
#         "access_token": access_token,
#         "token_type": "bearer"
#     }

# @router.post("/logout")
# @limiter.limit("10/minute")
# def logout(
#     request: Request,
#     body: RefreshRequest,
#     db: Session = Depends(get_db)
# ):
#     db.query(RefreshToken).filter(
#         RefreshToken.token == body.refresh_token
#     ).delete()

#     db.commit()
#     return {"message": "Logged out successfully"}

# @router.post("/request-password-reset")
# @limiter.limit("3/minute")
# def request_password_reset(
#     request: Request,
#     body: RequestPasswordResetRequest,
#     db: Session = Depends(get_db)
# ):
#     user = db.query(User).filter(User.email == body.email).first()
#     if user:
#         reset_token = create_password_reset_token(user.email)
#         send_password_reset_email(user.email, reset_token)
    
#     # Always return 200 to prevent email enumeration
#     return {"message": "If that email is registered, a password reset link has been sent."}

# @router.post("/reset-password")
# @limiter.limit("5/minute")
# def reset_password(
#     request: Request,
#     body: ResetPasswordRequest,
#     db: Session = Depends(get_db)
# ):
#     email = verify_token(body.token, "reset")
#     if not email:
#         raise HTTPException(
#             status_code=400,
#             detail="Invalid or expired password reset token"
#         )
    
#     user = db.query(User).filter(User.email == email).first()
#     if not user:
#         raise HTTPException(
#             status_code=404,
#             detail="User not found"
#     )
    
#     user.password_hash = hash_password(body.new_password)
#     db.commit()

#     return {"message": "Password reset successfully"}