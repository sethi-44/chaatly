# DIY AUTH - COMMENTED OUT: Migrated to Supabase Auth
# This file is kept for reference but not used in production.
# All auth is now handled by Supabase (see app/supabase_auth.py and app/routers/supabase_auth.py)

# from app.security import hash_password, create_verification_token, verify_token
# from fastapi import APIRouter, Request
# from sqlalchemy.orm import Session
# from fastapi import HTTPException, Depends
# from app.models import User
# from app.schemas import UserCreate, VerifyEmailRequest
# from app.dependencies import get_db
# from app.helpers import existing_user, send_verification_email
# from app.rate_limit import limiter

# router = APIRouter()

# @router.post("/register", status_code=201)
# @limiter.limit("3/minute")
# def register(
#     request: Request,
#     user: UserCreate,
#     db: Session = Depends(get_db)
# ):
#     existing = existing_user(db, user)

#     if existing:
#         raise HTTPException(
#             status_code=400,
#             detail="Username or email already exists"
#         )

#     new_user = User(
#         username=user.username,
#         email=user.email,
#         password_hash=hash_password(
#             user.password
#         )
#     )

#     db.add(new_user)
#     db.commit()
#     db.refresh(new_user)

#     verification_token = create_verification_token(new_user.email)
#     send_verification_email(new_user.email, verification_token)

#     return {
#         "id": new_user.id,
#         "username": new_user.username,
#         "email": new_user.email
#     }

# @router.post("/verify-email")
# @limiter.limit("10/minute")
# def verify_email(
#     request: Request,
#     body: VerifyEmailRequest,
#     db: Session = Depends(get_db)
# ):
#     email = verify_token(body.token, "verification")
#     if not email:
#         raise HTTPException(
#             status_code=400,
#             detail="Invalid or expired verification token"
#         )
    
#     user = db.query(User).filter(User.email == email).first()
#     if not user:
#         raise HTTPException(
#             status_code=404,
#             detail="User not found"
#         )
    
#     if user.is_verified:
#         return {"message": "Email already verified"}

#     user.is_verified = True
#     db.commit()

#     return {"message": "Email verified successfully"}