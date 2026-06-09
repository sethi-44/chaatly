from app.models import Meetup, User,MeetupParticipant
from sqlalchemy.orm import Session

def find_meetup(db, meetup_id):
    return db.query(Meetup).filter(
        Meetup.id == meetup_id
    ).first()

def find_user(db, user_id):
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
    user_id: int,
    meetup_id: int
):
    return db.query(
        MeetupParticipant
    ).filter(
        MeetupParticipant.user_id == user_id,
        MeetupParticipant.meetup_id == meetup_id
    ).first()
