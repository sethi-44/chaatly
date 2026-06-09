from backend.app.database import SessionLocal
from backend.app.models import User, Meetup, MeetupParticipant
from backend.app.security import hash_password

session = SessionLocal()

user = User(
    username="Varuna",
    email="varuna@gmail.com",
    password_hash=hash_password("varuna123")
)

session.add(user)
session.commit()
session.refresh(user)

meetup = Meetup(
    title="Burger Meetup",
    description="Let's eat burgers",
    location="Chandigarh",
    max_attendees=20,
    host_id=user.id
)

session.add(meetup)
session.commit()
session.refresh(meetup)

participant = MeetupParticipant(
    user_id=user.id,
    meetup_id=meetup.id
)

session.add(participant)
session.commit()

print("Seed data created!")