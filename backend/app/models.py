from sqlalchemy import (
    Column,
    Integer,
    String,
    CheckConstraint,
    ForeignKey
)
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


class Meetup(Base):
    __tablename__ = "meetups"

    __table_args__ = (
        CheckConstraint(
            "max_attendees > 0",
            name="positive_max_attendees"
        ),
    )

    id = Column(
        Integer,
        primary_key=True
    )

    title = Column(
        String(100),
        nullable=False
    )

    description = Column(
        String(500)
    )

    location = Column(
        String(100),
        nullable=False
    )

    max_attendees = Column(
        Integer,
        nullable=False
    )

    host_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False
    )


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True,nullable=False)
    email = Column(String(100), unique=True,nullable=False)
    password_hash = Column(String(255), nullable=False)

class MeetupParticipant(Base):
    __tablename__ = "meetup_participants"

    user_id = Column(
        Integer,
        ForeignKey("users.id"),
        primary_key=True
    )

    meetup_id = Column(
        Integer,
        ForeignKey("meetups.id"),
        primary_key=True
    )  