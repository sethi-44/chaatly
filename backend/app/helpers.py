from app.models import Meetup, User,MeetupParticipant
from app.schemas import MeetupResponse
from sqlalchemy.orm import Session
import logging

logger = logging.getLogger(__name__)

def find_meetup(db, meetup_id):
    return db.query(Meetup).filter(
        Meetup.id == meetup_id
    ).first()

def find_user(db, user_id: str):
    return db.query(User).filter(
        User.id == user_id
    ).first()

def get_meetup_attendance(
    db: Session,
    meetup_id: int
):
    return db.query(
        MeetupParticipant
    ).filter(
        MeetupParticipant.meetup_id == meetup_id
    ).count()

def is_participant(
    db: Session,
    user_id: str,
    meetup_id: int,
):
    return db.query(
        MeetupParticipant
    ).filter(
        MeetupParticipant.user_id == user_id,
        MeetupParticipant.meetup_id == meetup_id
    ).first()

def meetup_to_response(
    db: Session,
    meetup: Meetup
):
    attendee_count = get_meetup_attendance(
        db,
        meetup.id
    )

    return MeetupResponse(
        id=meetup.id,
        title=meetup.title,
        location=meetup.location,
        event_date=meetup.event_date,
        description=meetup.description,
        max_attendees=meetup.max_attendees,
        image_url=meetup.image_url,
        host=meetup.host,
        attendee_count=attendee_count,
        spots_left=meetup.max_attendees - attendee_count,
        photos=meetup.photos
    )