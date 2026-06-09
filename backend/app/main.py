from fastapi import FastAPI

from app.routers import meetups,users,register,login

app = FastAPI()

app.include_router(meetups.router)
app.include_router(users.router)
app.include_router(register.router)
app.include_router(login.router)

@app.get("/")
def greet():
    return {"message": "Welcome to Chaatly"}