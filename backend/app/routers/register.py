from app.security import hash_password
from fastapi import APIRouter
from sqlalchemy.orm import Session
from fastapi import HTTPException, Depends
from app.models import User
from app.schemas import UserCreate
from app.dependencies import get_db
from app.helpers import existing_user 
router = APIRouter()

@router.post("/register", status_code=201)
def register(
    user: UserCreate,
    db: Session = Depends(get_db)
):
    exxisting_user = existing_user(db, user) 

    if exxisting_user:
        raise HTTPException(
            status_code=400,
            detail="Username or email already exists"
        )

    new_user = User(
        username=user.username,
        email=user.email,
        password_hash=hash_password(
            user.password
        )
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {
        "id": new_user.id,
        "username": new_user.username,
        "email": new_user.email
    }