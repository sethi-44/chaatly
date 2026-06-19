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
    password: str = Field(
        min_length=8,
        max_length=128
    )

class UserUpdate(BaseModel):
    username: str | None = None
    email: EmailStr | None = None


class UserResponse(BaseModel):
    username: str
    email: EmailStr

    model_config = {
        "from_attributes": True
    }

class MeetupResponse(BaseModel):
    id: int
    title: str
    description: str | None
    location: str
    max_attendees: int
    host: UserResponse
    attendee_count: int
    spots_left: int

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