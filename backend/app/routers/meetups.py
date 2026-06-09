from fastapi import HTTPException,Depends
from sqlalchemy.orm import Session
from fastapi import APIRouter
from app.models import Meetup, User, MeetupParticipant
from app.schemas import MeetupCreate
from app.dependencies import get_db
from app.helpers import find_meetup,get_meetup_attendance,is_participant

router = APIRouter()

@router.get("/meetups")
def get_meetups(db:Session=Depends(get_db)):
    return db.query(Meetup).all()

@router.get("/meetups/{meetup_id}")
def get_meetup(meetup_id:int, db:Session=Depends(get_db)):
    meetup = find_meetup(db, meetup_id)
    if not meetup:
        raise HTTPException(status_code=404, detail="Meetup not found")
    return meetup

@router.post("/meetups",status_code=201)
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

@router.delete("/meetups/{meetup_id}")
def delete_meetup(meetup_id: int, db:Session=Depends(get_db)):
    meetup = find_meetup(db, meetup_id)
    if not meetup:
        raise HTTPException(status_code=404, detail="Meetup not found")
    db.delete(meetup)
    db.commit()
    return {"message": f"Meetup {meetup_id} deleted successfully"}

@router.put("/meetups/{meetup_id}")
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


@router.post("/meetups/{meetup_id}/join",status_code=201)
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
    
    meetup_participant_count = get_meetup_attendance(db, meetup_id)
    
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
    
@router.post("/meetups/{meetup_id}/leave",status_code=200)
def leave_meetup(meetup_id: int, db:Session=Depends(get_db)):
    meetup = find_meetup(db, meetup_id)
    if not meetup:
        raise HTTPException(status_code=404, detail="Meetup not found")
    
    participant = is_participant(db, user_id=1, meetup_id=meetup_id)

    if not participant:
        raise HTTPException(
            status_code=400,
            detail="Not a participant of this meetup"
        )
    
    db.delete(participant)
    db.commit()
    return {"message": f"Left meetup {meetup_id} successfully"}

@router.get("/meetups/{meetup_id}/participants")
def get_meetup_participants(meetup_id: int, db:Session=Depends(get_db)):
    meetup = find_meetup(db, meetup_id)
    if not meetup:
        raise HTTPException(status_code=404, detail="Meetup not found")
    
    participants = db.query(User).join(MeetupParticipant).filter(
        MeetupParticipant.meetup_id == meetup_id
    ).all()

    return participants    

@router.get("/meetups/{meetup_id}/attendance")
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

    attendee_count = get_meetup_attendance(db, meetup_id)

    return {
        "meetup_id": meetup_id,
        "attendees": attendee_count,
        "capacity": meetup.max_attendees,
        "spots_left": meetup.max_attendees - attendee_count
    }