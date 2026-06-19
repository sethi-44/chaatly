from fastapi import HTTPException,Depends
from sqlalchemy.orm import Session
from fastapi import APIRouter
from app.models import User
from app.dependencies import get_db
from app.schemas import UserCreate, UserResponse, UserUpdate, ChangePasswordRequest
from app.helpers import find_user,existing_user
from app.security import get_current_user,hash_password,verify_password

router = APIRouter()

@router.get(
    "/me",
    response_model=UserResponse
)
def me(
    current_user: User = Depends(get_current_user)
):
    return current_user

@router.post("/users",status_code=201, response_model=UserResponse)
def create_user(user: UserCreate, db:Session=Depends(get_db)):
    existing = existing_user(db, user)
    if existing:
        raise HTTPException(
            status_code=400,
            detail="User with this username or email already exists"
        )
    user_db = User(
        username=user.username,
        email=user.email,
        password_hash=hash_password(user.password)
    )

    db.add(user_db)
    db.commit()
    db.refresh(user_db)
    return user_db

@router.get("/users/{user_id}", response_model=UserResponse)
def get_user(user_id: int, db:Session=Depends(get_db)):
    user = find_user(db,user_id)

    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return user

@router.get("/users", response_model=list[UserResponse])
def get_users(db:Session=Depends(get_db)):
    return db.query(User).all()

# TODO:
# Implement account deletion after deciding
# what should happen to hosted meetups.

@router.put("/users/me", response_model=UserResponse)
def update_user(user: UserUpdate, current_user: User = Depends(get_current_user), db:Session=Depends(get_db)):
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

@router.post("/users/me/change-password")
def change_password(
    request: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db:Session=Depends(get_db)
):
    if not verify_password(
        request.current_password,
        current_user.password_hash
    ):
        raise HTTPException(
            status_code=400,
            detail="Current password is incorrect"
        )
    current_user.password_hash = hash_password(request.new_password)
    db.commit()
    return {"message": "Password changed successfully"}