from pydantic import BaseModel, Field, EmailStr
from datetime import datetime
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

    event_date: datetime | None = None

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
    password: str = Field(
        min_length=8,
        max_length=128
    )

class UserUpdate(BaseModel):
    username: str | None = None
    email: EmailStr | None = None
    bio: str | None = None
    profile_picture_url: str | None = None


class UserResponse(BaseModel):
    username: str
    email: EmailStr
    bio: str | None = None
    profile_picture_url: str | None = None

    model_config = {
        "from_attributes": True
    }

class MeetupPhotoResponse(BaseModel):
    id: int
    image_url: str
    user_id: str
    created_at: datetime
    
    model_config = {
        "from_attributes": True
    }

class MeetupResponse(BaseModel):
    id: int
    title: str
    description: str | None
    location: str
    event_date: datetime | None
    max_attendees: int
    image_url: str | None = None
    host: UserResponse
    attendee_count: int
    spots_left: int
    photos: list[MeetupPhotoResponse] = []

    model_config = {
        "from_attributes": True
    }

class ChangePasswordRequest(BaseModel):
    current_password: str=Field(
        min_length=8,
        max_length=128
    )
    new_password: str=Field(
        min_length=8,
        max_length=128
    )

class RefreshRequest(BaseModel):
    refresh_token: str

class VerifyEmailRequest(BaseModel):
    token: str

class RequestPasswordResetRequest(BaseModel):
    email: EmailStr

class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(
        min_length=8,
        max_length=128
    )

class DiscussionMessageCreate(BaseModel):
    content: str = Field(min_length=1, max_length=500)

class DiscussionMessageUpdate(BaseModel):
    content: str = Field(min_length=1, max_length=500)

class DiscussionAuthor(BaseModel):
    id: str
    username: str
    profile_picture_url: str | None = None

    model_config = {"from_attributes": True}

class DiscussionReplyResponse(BaseModel):
    id: int
    meetup_id: int
    content: str
    created_at: datetime
    updated_at: datetime
    author: DiscussionAuthor

    model_config = {"from_attributes": True}

class DiscussionMessageResponse(BaseModel):
    id: int
    meetup_id: int
    content: str
    created_at: datetime
    updated_at: datetime
    author: DiscussionAuthor
    reply_count: int
    replies: list[DiscussionReplyResponse] = []

    model_config = {"from_attributes": True}

class DiscussionPaginatedResponse(BaseModel):
    messages: list[DiscussionMessageResponse]
    page: int
    pages: int
    limit: int
    total: int