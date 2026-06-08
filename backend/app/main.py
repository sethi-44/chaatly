from fastapi import FastAPI,HTTPException
from pydantic import BaseModel, Field

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

next_meetup_id = 5
app=FastAPI()

def find_meetup(meetup_id: int):
    for meetup in meetups:
        if meetup["id"] == meetup_id:
            return meetup
    return None
@app.get("/")
def greet():
    return {
        "message":"Welcome to Chaatly"
    }
meetups = [
    {
        "id": 1,
        "title": "Momos Meetup",
        "description": "Let's eat momos and discuss startups.",
        "location": "Sector 17, Chandigarh",
        "max_attendees": 15,
        "current_attendees": 7,
        "host": "Harshit"
    },
    {
        "id": 2,
        "title": "Coffee & Coding",
        "description": "Casual coding session over coffee.",
        "location": "CP67 Mall, Mohali",
        "max_attendees": 10,
        "current_attendees": 4,
        "host": "Rohan"
    },
    {
        "id": 3,
        "title": "Pizza Night",
        "description": "Meet fellow students and enjoy pizza.",
        "location": "Elante Mall, Chandigarh",
        "max_attendees": 20,
        "current_attendees": 12,
        "host": "Ananya"
    },
    {
        "id": 4,
        "title": "Biryani Adda",
        "description": "Weekend biryani meetup for food lovers.",
        "location": "Phase 5, Mohali",
        "max_attendees": 25,
        "current_attendees": 18,
        "host": "Aman"
    }
]
@app.get("/meetups")
def get_meetups():
    return meetups

@app.get("/meetups/{meetup_id}")
def get_meetup(meetup_id:int):
    meetup = find_meetup(meetup_id)
    if not meetup:
        raise HTTPException(status_code=404, detail="Meetup not found")
    return meetup

@app.post("/meetups")
def create_meetup(meetup: MeetupCreate):
    global next_meetup_id
    new_meetup = {
        "id": next_meetup_id,
        "title": meetup.title,
        "description": meetup.description,
        "location": meetup.location,
        "max_attendees": meetup.max_attendees,
        "current_attendees": 0,
        "host": "Harshit"
    }
    meetups.append(new_meetup)
    next_meetup_id += 1
    return new_meetup

@app.delete("/meetups/{meetup_id}")
def delete_meetup(meetup_id: int):
    meetup = find_meetup(meetup_id)
    if not meetup:
        raise HTTPException(status_code=404, detail="Meetup not found")
    meetups.remove(meetup)
    return {"message": f"Meetup {meetup_id} deleted successfully"}

@app.put("/meetups/{meetup_id}")
def update_meetup(meetup_id: int, meetup: MeetupCreate):
    meetup_to_update = find_meetup(meetup_id)
    if not meetup_to_update:
        raise HTTPException(status_code=404, detail="Meetup not found")
    meetup_to_update["title"] = meetup.title
    meetup_to_update["description"] = meetup.description
    meetup_to_update["location"] = meetup.location
    meetup_to_update["max_attendees"] = meetup.max_attendees
    return meetup_to_update


@app.post("/meetups/{meetup_id}/join")
def join_meetup(meetup_id: int):
    meetup = find_meetup(meetup_id)
    if not meetup:
        raise HTTPException(status_code=404, detail="Meetup not found")
    if meetup["current_attendees"] < meetup["max_attendees"]:
        meetup["current_attendees"] += 1
        return {"message": f"Joined meetup {meetup_id} successfully"}
    else:
        raise HTTPException(status_code=400, detail="Meetup is full")