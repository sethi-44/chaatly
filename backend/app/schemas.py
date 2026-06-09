from pydantic import BaseModel, Field, EmailStr
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