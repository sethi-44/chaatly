from fastapi import HTTPException, Depends, APIRouter, Request, Response, status, Query
from sqlalchemy.orm import Session
from app.models import User
from app.dependencies import get_db
from app.schemas import UserCreate, UserResponse, UserUpdate, ChangePasswordRequest
from app.helpers import find_user, existing_user
# from app.security import get_current_user, hash_password, verify_password  # DIY auth - commented out
from app.supabase_auth import get_current_user_supabase
from app.rate_limit import limiter

router = APIRouter()

async def get_current_admin_user(current_user: User = Depends(get_current_user_supabase)) -> User:
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user

@router.get(
    "/me",
    response_model=UserResponse
)
@limiter.limit("60/minute")
def me(
    request: Request,
    response: Response,
    current_user: User = Depends(get_current_user_supabase)
):
    return current_user

# @router.post("/users", status_code=201, response_model=UserResponse)  # DIY auth - commented out, use /supabase/register
# @limiter.limit("10/minute")
# def create_user(request: Request, user: UserCreate, db: Session = Depends(get_db)):
#     existing = existing_user(db, user)
#     if existing:
#         raise HTTPException(
#             status_code=400,
#             detail="User with this username or email already exists"
#         )
#     user_db = User(
#         username=user.username,
#         email=user.email,
#         password_hash=hash_password(user.password)
#     )
#
#     db.add(user_db)
#     db.commit()
#     db.refresh(user_db)
#     return user_db

@router.get("/users/{user_id}", response_model=UserResponse)
@limiter.limit("60/minute")
def get_user(request: Request, response: Response, user_id: str, current_user: User = Depends(get_current_user_supabase), db: Session = Depends(get_db)):
    user = find_user(db, user_id)

    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not allowed to access other users' data")
    
    return user

@router.get("/users", response_model=list[UserResponse])
@limiter.limit("30/minute")
def get_users(
    request: Request,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
):
    return db.query(User).offset(skip).limit(limit).all()

# TODO:
# Implement account deletion after deciding
# what should happen to hosted meetups.

@router.put("/users/me", response_model=UserResponse)
@limiter.limit("20/minute")
def update_user(request: Request, response: Response, user: UserUpdate, current_user: User = Depends(get_current_user_supabase), db: Session = Depends(get_db)):
    if user.username is not None and user.username != current_user.username:
        conflict = db.query(User).filter(User.username == user.username).first()
        if conflict:
            raise HTTPException(
                status_code=400,
                detail="Username already taken"
            )
        current_user.username = user.username

    if user.email is not None and user.email != current_user.email:
        conflict = db.query(User).filter(User.email == user.email).first()
        if conflict:
            raise HTTPException(
                status_code=400,
                detail="Email already taken"
            )
        current_user.email = user.email

    db.commit()
    db.refresh(current_user)
    return current_user

# @router.post("/users/me/change-password")  # DIY auth - commented out, use /supabase/change-password
# @limiter.limit("10/minute")
# def change_password(
#     request: Request,
#     body: ChangePasswordRequest,
#     current_user: User = Depends(get_current_user),
#     db: Session = Depends(get_db)
# ):
#     if not verify_password(
#         body.current_password,
#         current_user.password_hash
#     ):
#         raise HTTPException(
#             status_code=400,
#             detail="Current password is incorrect"
#         )
#     current_user.password_hash = hash_password(body.new_password)
#     db.commit()
#     return {"message": "Password changed successfully"}