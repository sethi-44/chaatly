from fastapi import HTTPException,Depends
from sqlalchemy.orm import Session
from fastapi import APIRouter
from app.models import User
from app.dependencies import get_db
from app.schemas import UserCreate
from app.helpers import find_user,existing_user

router = APIRouter()

@router.post("/users",status_code=201)
def create_user(user: UserCreate, db:Session=Depends(get_db)):
    exxisting_user = existing_user(db, user)
    if exxisting_user:
        raise HTTPException(
            status_code=400,
            detail="User with this username or email already exists"
        )
    user_db = User(
        username=user.username,
        email=user.email
    )

    db.add(user_db)
    db.commit()
    db.refresh(user_db)
    return user_db

@router.get("/users/{user_id}")
def get_user(user_id: int, db:Session=Depends(get_db)):
    user = find_user(db,user_id)

    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return user

@router.get("/users")
def get_users(db:Session=Depends(get_db)):
    return db.query(User).all()