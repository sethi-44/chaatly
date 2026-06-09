from fastapi import FastAPI,HTTPException,Depends
from pydantic import BaseModel, Field, EmailStr
from app.database import SessionLocal
from sqlalchemy import or_
from sqlalchemy.orm import Session
from app.models import Meetup, User, MeetupParticipant
# TODO: Replace global session with FastAPI dependency injection
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
class MeetupCreate(BaseModel):
    title: str = Field(
        min_length=3,
        max_length=100
    )

    description: str | None = Field(
        default=None,
        max_length=500
    )

    location: str = Field(
        min_length=3,
        max_length=100
    )

    max_attendees: int = Field(
        gt=0,
        le=1000
    )

class UserCreate(BaseModel):
    username: str = Field(
        min_length=3,
        max_length=50
    )
    email: EmailStr 

app=FastAPI()

# Helper Function
def find_meetup(db: Session, meetup_id: int):
    return db.query(Meetup).filter(
        Meetup.id == meetup_id
    ).first()

@app.get("/")
def greet():
    return {
        "message":"Welcome to Chaatly"
    }

@app.get("/meetups")
def get_meetups(db:Session=Depends(get_db)):
    return db.query(Meetup).all()

@app.get("/meetups/{meetup_id}")
def get_meetup(meetup_id:int, db:Session=Depends(get_db)):
    meetup = find_meetup(db, meetup_id)
    if not meetup:
        raise HTTPException(status_code=404, detail="Meetup not found")
    return meetup

@app.post("/meetups",status_code=201)
def create_meetup(meetup: MeetupCreate, db:Session=Depends(get_db)):
    meetup_db = Meetup(
        title=meetup.title,
        description=meetup.description,
        location=meetup.location,
        max_attendees=meetup.max_attendees,
        host_id=1
    )

    db.add(meetup_db)
    db.commit()
    db.refresh(meetup_db)
    return meetup_db

@app.delete("/meetups/{meetup_id}")
def delete_meetup(meetup_id: int, db:Session=Depends(get_db)):
    meetup = find_meetup(db, meetup_id)
    if not meetup:
        raise HTTPException(status_code=404, detail="Meetup not found")
    db.delete(meetup)
    db.commit()
    return {"message": f"Meetup {meetup_id} deleted successfully"}

@app.put("/meetups/{meetup_id}")
def update_meetup(meetup_id: int, meetup: MeetupCreate, db:Session=Depends(get_db)):
    meetup_to_update = find_meetup(db, meetup_id)
    if not meetup_to_update:
        raise HTTPException(status_code=404, detail="Meetup not found")
    meetup_to_update.title = meetup.title
    meetup_to_update.description = meetup.description
    meetup_to_update.location = meetup.location
    meetup_to_update.max_attendees = meetup.max_attendees
    db.commit()
    db.refresh(meetup_to_update)
    return meetup_to_update


@app.post("/meetups/{meetup_id}/join",status_code=201)
def join_meetup(meetup_id: int, db:Session=Depends(get_db)):
    meetup = find_meetup(db, meetup_id)
    if not meetup:
        raise HTTPException(status_code=404, detail="Meetup not found")
    
    existing = db.query(MeetupParticipant).filter(
        MeetupParticipant.user_id == 1,
        MeetupParticipant.meetup_id == meetup_id
    ).first()

    if existing:
        raise HTTPException(
            status_code=400,
            detail="Already joined this meetup"
        )
    
    meetup_participant_count = db.query(MeetupParticipant).filter(
                                    MeetupParticipant.meetup_id == meetup_id
                                ).count()
    
    if meetup_participant_count < meetup.max_attendees:
        participant = MeetupParticipant(
            user_id=1,
            meetup_id=meetup_id
        )

        db.add(participant)
        db.commit()
        return {"message": f"Joined meetup {meetup_id} successfully"}
    else:
        raise HTTPException(status_code=400, detail="Meetup is full")
    
@app.post("/meetups/{meetup_id}/leave",status_code=200)
def leave_meetup(meetup_id: int, db:Session=Depends(get_db)):
    meetup = find_meetup(db, meetup_id)
    if not meetup:
        raise HTTPException(status_code=404, detail="Meetup not found")
    
    participant = db.query(MeetupParticipant).filter(
        MeetupParticipant.user_id == 1,
        MeetupParticipant.meetup_id == meetup_id
    ).first()

    if not participant:
        raise HTTPException(
            status_code=400,
            detail="Not a participant of this meetup"
        )
    
    db.delete(participant)
    db.commit()
    return {"message": f"Left meetup {meetup_id} successfully"}

@app.get("/meetups/{meetup_id}/participants")
def get_meetup_participants(meetup_id: int, db:Session=Depends(get_db)):
    meetup = find_meetup(db, meetup_id)
    if not meetup:
        raise HTTPException(status_code=404, detail="Meetup not found")
    
    participants = db.query(User).join(MeetupParticipant).filter(
        MeetupParticipant.meetup_id == meetup_id
    ).all()

    return participants    

@app.get("/meetups/{meetup_id}/attendance")
def get_attendance(
    meetup_id: int,
    db: Session = Depends(get_db)
):
    meetup = find_meetup(db, meetup_id)

    if not meetup:
        raise HTTPException(
            status_code=404,
            detail="Meetup not found"
        )

    attendee_count = db.query(MeetupParticipant).filter(
        MeetupParticipant.meetup_id == meetup_id
    ).count()

    return {
        "meetup_id": meetup_id,
        "attendees": attendee_count,
        "capacity": meetup.max_attendees,
        "spots_left": meetup.max_attendees - attendee_count
    }

@app.post("/users",status_code=201)
def create_user(user: UserCreate, db:Session=Depends(get_db)):
    existing_user = db.query(User).filter(
        or_(
            User.username == user.username,
            User.email == user.email
        )
    ).first()
    if existing_user:
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

@app.get("/users/{user_id}")
def get_user(user_id: int, db:Session=Depends(get_db)):
    user = db.query(User).filter(
        User.id == user_id
    ).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return user

@app.get("/users")
def get_users(db:Session=Depends(get_db)):
    return db.query(User).all()