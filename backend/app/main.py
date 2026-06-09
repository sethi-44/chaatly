from fastapi import FastAPI

from app.routers import meetups
from app.routers import users

app = FastAPI()

app.include_router(meetups.router)
app.include_router(users.router)

@app.get("/")
def greet():
    return {"message": "Welcome to Chaatly"}