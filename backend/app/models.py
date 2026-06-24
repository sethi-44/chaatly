from sqlalchemy import DateTime
from sqlalchemy import (
    Column,
    Integer,
    String,
    CheckConstraint,
    ForeignKey,
    Boolean
)
from sqlalchemy.orm import DeclarativeBase, relationship


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

    event_date = Column(
        DateTime(timezone=True),
        nullable=True
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
        String(36),
        ForeignKey("users.id"),
        nullable=False
    )

    host = relationship("User")

    participants = relationship(
        "MeetupParticipant",
        back_populates="meetup",
        cascade="all, delete-orphan"
    )


class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    bio = Column(String(500), nullable=True)
    profile_picture_url = Column(String(255), nullable=True)
    is_verified = Column(Boolean, default=False)
    is_admin = Column(Boolean, default=False, nullable=False)

class MeetupParticipant(Base):
    __tablename__ = "meetup_participants"

    user = relationship("User")
    
    user_id = Column(
        String(36),
        ForeignKey("users.id"),
        primary_key=True
    )

    meetup_id = Column(
        Integer,
        ForeignKey("meetups.id"),
        primary_key=True
    )  

    meetup = relationship(
        "Meetup",
        back_populates="participants"
    )

class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id = Column(Integer, primary_key=True)

    token = Column(String, unique=True, nullable=False)

    user_id = Column(
        String(36),
        ForeignKey("users.id"),
        nullable=False
    )