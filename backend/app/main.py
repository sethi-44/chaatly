from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import meetups,users,register,login

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(meetups.router)
app.include_router(users.router)
app.include_router(register.router)
app.include_router(login.router)

@app.get("/")
def greet():
    return {"message": "Welcome to Chaatly"}