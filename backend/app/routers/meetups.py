from fastapi import HTTPException, Depends, APIRouter, Request, Response, Query
from sqlalchemy.orm import Session
from app.models import Meetup, User, MeetupParticipant
from app.schemas import MeetupCreate, MeetupResponse, UserResponse
from app.dependencies import get_db
from app.helpers import find_meetup, get_meetup_attendance, is_participant, meetup_to_response
from app.supabase_auth import get_current_user_supabase
from app.rate_limit import limiter

router = APIRouter()

@router.get("/meetups", response_model=list[MeetupResponse])
@limiter.limit("60/minute")
def get_meetups(
    request: Request,
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
):
    meetups = db.query(Meetup).offset(skip).limit(limit).all()
    return [
        meetup_to_response(db, meetup)
        for meetup in meetups
    ]

@router.get("/meetups/joined", response_model=list[int])
@limiter.limit("60/minute")
def get_joined_meetups(request: Request, current_user: User = Depends(get_current_user_supabase), db: Session = Depends(get_db)):
    participants = db.query(MeetupParticipant).filter(MeetupParticipant.user_id == current_user.id).all()
    return [p.meetup_id for p in participants]

@router.get("/meetups/{meetup_id}", response_model=MeetupResponse)
@limiter.limit("60/minute")
def get_meetup(request: Request, response: Response, meetup_id: int, db: Session = Depends(get_db)):
    meetup = find_meetup(db, meetup_id)
    if not meetup:
        raise HTTPException(status_code=404, detail="Meetup not found")
    return meetup_to_response(db, meetup)

@router.post("/meetups", status_code=201, response_model=MeetupResponse)
@limiter.limit("20/minute")
def create_meetup(request: Request, response: Response, meetup: MeetupCreate, current_user: User = Depends(get_current_user_supabase), db: Session = Depends(get_db)):
    meetup_db = Meetup(
        title=meetup.title,
        description=meetup.description,
        location=meetup.location,
        max_attendees=meetup.max_attendees,
        host_id=current_user.id
    )


    db.add(meetup_db)
    db.commit()
    db.refresh(meetup_db)
    return meetup_to_response(db, meetup_db)

@router.delete("/meetups/{meetup_id}")
@limiter.limit("20/minute")
def delete_meetup(request: Request, response: Response, meetup_id: int, current_user: User = Depends(get_current_user_supabase), db: Session = Depends(get_db)):
    meetup = find_meetup(db, meetup_id)
    if not meetup:
        raise HTTPException(status_code=404, detail="Meetup not found")
    if meetup.host_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="Not allowed"
        )
    db.delete(meetup)
    db.commit()
    return {"message": f"Meetup {meetup_id} deleted successfully"}

@router.put("/meetups/{meetup_id}", response_model=MeetupResponse)
@limiter.limit("20/minute")
def update_meetup(request: Request, response: Response, meetup_id: int, meetup: MeetupCreate, current_user: User = Depends(get_current_user_supabase), db: Session = Depends(get_db)):
    meetup_to_update = find_meetup(db, meetup_id)
    if not meetup_to_update:
        raise HTTPException(status_code=404, detail="Meetup not found")
    if meetup_to_update.host_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="Not allowed"
        )

    current_attendance = get_meetup_attendance(db, meetup_id)
    if meetup.max_attendees < current_attendance:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot reduce max_attendees below current attendance ({current_attendance})"
        )

    meetup_to_update.title = meetup.title
    meetup_to_update.description = meetup.description
    meetup_to_update.location = meetup.location
    meetup_to_update.max_attendees = meetup.max_attendees
    db.commit()
    db.refresh(meetup_to_update)
    return meetup_to_response(db,meetup_to_update)


@router.post("/meetups/{meetup_id}/join", status_code=201)
@limiter.limit("30/minute")
def join_meetup(request: Request, response: Response, meetup_id: int, current_user: User = Depends(get_current_user_supabase), db: Session = Depends(get_db)):
    meetup = find_meetup(db, meetup_id)
    if not meetup:
        raise HTTPException(status_code=404, detail="Meetup not found")

    if meetup.host_id == current_user.id:
        raise HTTPException(
            status_code=400,
            detail="Host cannot join their own meetup as participant"
        )

    existing = is_participant(db, user_id=current_user.id, meetup_id=meetup_id)

    if existing:
        raise HTTPException(
            status_code=400,
            detail="Already joined this meetup"
        )
    
    meetup_participant_count = get_meetup_attendance(db, meetup_id)
    
    if meetup_participant_count < meetup.max_attendees:
        participant = MeetupParticipant(
            user_id=current_user.id,
            meetup_id=meetup_id
        )

        db.add(participant)
        db.commit()
        return {"message": f"Joined meetup {meetup_id} successfully"}
    else:
        raise HTTPException(status_code=400, detail="Meetup is full")
    
@router.post("/meetups/{meetup_id}/leave", status_code=200)
@limiter.limit("30/minute")
def leave_meetup(request: Request, response: Response, meetup_id: int, current_user: User = Depends(get_current_user_supabase), db: Session = Depends(get_db)):
    meetup = find_meetup(db, meetup_id)
    if not meetup:
        raise HTTPException(status_code=404, detail="Meetup not found")
    
    participant = is_participant(db, user_id=current_user.id, meetup_id=meetup_id)

    if not participant:
        raise HTTPException(
            status_code=400,
            detail="Not a participant of this meetup"
        )
    
    db.delete(participant)
    db.commit()
    return {"message": f"Left meetup {meetup_id} successfully"}

@router.get("/meetups/{meetup_id}/participants", response_model=list[UserResponse])
@limiter.limit("60/minute")
def get_meetup_participants(request: Request, response: Response, meetup_id: int, db: Session = Depends(get_db)):
    meetup = find_meetup(db, meetup_id)
    if not meetup:
        raise HTTPException(status_code=404, detail="Meetup not found")
    
    participants = db.query(User).join(MeetupParticipant).filter(
        MeetupParticipant.meetup_id == meetup_id
    ).all()

    return participants    

@router.get("/meetups/{meetup_id}/attendance")
@limiter.limit("60/minute")
def get_attendance(
    request: Request,
    response: Response,
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
        "attendees": attendee_count,
        "capacity": meetup.max_attendees,
        "spots_left": meetup.max_attendees - attendee_count
    }

@router.get("/my-meetups", response_model=list[MeetupResponse])
@limiter.limit("60/minute")
def get_my_meetups(
    request: Request,
    current_user: User = Depends(get_current_user_supabase),
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
):
    meetups = db.query(Meetup).filter(
        Meetup.host_id == current_user.id
    ).offset(skip).limit(limit).all()

    return [meetup_to_response(db, meetup) for meetup in meetups]

@router.get("/my-joined-meetups", response_model=list[MeetupResponse])
@limiter.limit("60/minute")
def get_my_joined_meetups(
    request: Request,
    current_user: User = Depends(get_current_user_supabase),
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
):
    joined_meetups = (
        db.query(Meetup)
        .join(MeetupParticipant)
        .filter(
            MeetupParticipant.user_id == current_user.id
        )
        .offset(skip).limit(limit)
        .all()
    )

    return [
        meetup_to_response(db, meetup)
        for meetup in joined_meetups
    ]