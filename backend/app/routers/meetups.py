from fastapi import HTTPException, Depends, APIRouter, Request, Response, Query, UploadFile, File
import mimetypes
from sqlalchemy.orm import Session
from app.models import Meetup, User, MeetupParticipant, MeetupPhoto
from app.schemas import MeetupCreate, MeetupResponse, UserResponse, MeetupPhotoResponse
from app.dependencies import get_db
from app.helpers import find_meetup, get_meetup_attendance, is_participant, meetup_to_response
from app.supabase_auth import get_current_user_supabase, get_supabase_admin_client
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
        event_date=meetup.event_date,
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
        
    if meetup.image_url:
        filename = meetup.image_url.split("/")[-1]
        try:
            supabase = get_supabase_admin_client()
            supabase.storage.from_("meetup-images").remove([filename])
        except Exception:
            pass

    if meetup.photos:
        try:
            supabase = get_supabase_admin_client()
            filenames = ["/".join(p.image_url.split("/")[-2:]) for p in meetup.photos]
            if filenames:
                supabase.storage.from_("meetup-gallery").remove(filenames)
        except Exception:
            pass

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

@router.post("/meetups/{meetup_id}/image")
@limiter.limit("5/minute")
async def upload_meetup_image(
    request: Request,
    meetup_id: int,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user_supabase),
    db: Session = Depends(get_db)
):
    meetup = find_meetup(db, meetup_id)
    if not meetup:
        raise HTTPException(status_code=404, detail="Meetup not found")
    if meetup.host_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only host can upload image")

    ALLOWED_TYPES = ["image/jpeg", "image/png", "image/webp"]
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(status_code=400, detail="Invalid file type. Only JPEG, PNG, and WebP are allowed.")
    
    file.file.seek(0, 2)
    file_size = file.file.tell()
    file.file.seek(0)
    if file_size > 5 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File size exceeds 5MB limit.")
        
    ext = mimetypes.guess_extension(file.content_type) or ".jpg"
    filename = f"{meetup_id}{ext}"
    
    supabase = get_supabase_admin_client()
    content = await file.read()
    
    try:
        supabase.storage.from_("meetup-images").upload(
            filename,
            content,
            {"content-type": file.content_type, "upsert": "true"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to upload image: {str(e)}")
        
    public_url = supabase.storage.from_("meetup-images").get_public_url(filename)
    
    meetup.image_url = public_url
    db.commit()
    db.refresh(meetup)
    
    return {"message": "Meetup image uploaded successfully", "image_url": public_url}

@router.delete("/meetups/{meetup_id}/image")
@limiter.limit("5/minute")
def delete_meetup_image(
    request: Request,
    meetup_id: int,
    current_user: User = Depends(get_current_user_supabase),
    db: Session = Depends(get_db)
):
    meetup = find_meetup(db, meetup_id)
    if not meetup:
        raise HTTPException(status_code=404, detail="Meetup not found")
    if meetup.host_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only host can delete image")

    if not meetup.image_url:
        return {"message": "No image to delete"}
        
    filename = meetup.image_url.split("/")[-1]
    
    supabase = get_supabase_admin_client()
    try:
        supabase.storage.from_("meetup-images").remove([filename])
    except Exception:
        pass
        
    meetup.image_url = None
    db.commit()
    
    return {"message": "Meetup image deleted successfully"}

import uuid

@router.post("/meetups/{meetup_id}/photos", response_model=MeetupPhotoResponse)
@limiter.limit("10/minute")
async def upload_meetup_photo(
    request: Request,
    meetup_id: int,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user_supabase),
    db: Session = Depends(get_db)
):
    meetup = find_meetup(db, meetup_id)
    if not meetup:
        raise HTTPException(status_code=404, detail="Meetup not found")
        
    is_host = meetup.host_id == current_user.id
    participant = is_participant(db, current_user.id, meetup_id)
    if not is_host and not participant:
        raise HTTPException(status_code=403, detail="Only host and participants can upload photos")

    ALLOWED_TYPES = ["image/jpeg", "image/png", "image/webp"]
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(status_code=400, detail="Invalid file type. Only JPEG, PNG, and WebP are allowed.")
    
    file.file.seek(0, 2)
    file_size = file.file.tell()
    file.file.seek(0)
    if file_size > 5 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File size exceeds 5MB limit.")
        
    ext = mimetypes.guess_extension(file.content_type) or ".jpg"
    filename = f"{meetup_id}/{uuid.uuid4()}{ext}"
    
    supabase = get_supabase_admin_client()
    content = await file.read()
    
    try:
        supabase.storage.from_("meetup-gallery").upload(
            filename,
            content,
            {"content-type": file.content_type, "upsert": "false"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to upload photo: {str(e)}")
        
    public_url = supabase.storage.from_("meetup-gallery").get_public_url(filename)
    
    new_photo = MeetupPhoto(
        meetup_id=meetup_id,
        user_id=current_user.id,
        image_url=public_url
    )
    db.add(new_photo)
    db.commit()
    db.refresh(new_photo)
    
    return new_photo

@router.delete("/meetups/{meetup_id}/photos/{photo_id}")
@limiter.limit("10/minute")
def delete_meetup_photo(
    request: Request,
    meetup_id: int,
    photo_id: int,
    current_user: User = Depends(get_current_user_supabase),
    db: Session = Depends(get_db)
):
    photo = db.query(MeetupPhoto).filter(MeetupPhoto.id == photo_id, MeetupPhoto.meetup_id == meetup_id).first()
    if not photo:
        raise HTTPException(status_code=404, detail="Photo not found")
        
    meetup = find_meetup(db, meetup_id)
    is_host = meetup and meetup.host_id == current_user.id
    if not is_host and photo.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not allowed to delete this photo")

    filename = "/".join(photo.image_url.split("/")[-2:])
    
    supabase = get_supabase_admin_client()
    try:
        supabase.storage.from_("meetup-gallery").remove([filename])
    except Exception:
        pass
        
    db.delete(photo)
    db.commit()
    
    return {"message": "Photo deleted successfully"}

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