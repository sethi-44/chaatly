import os
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

load_dotenv()

from app.routers import meetups, users, supabase_auth
# from app.routers import register, login  # DIY auth - commented out, using Supabase Auth instead
from app.rate_limit import setup_rate_limiting
from app.csrf import CSRFMiddleware, generate_csrf_token, set_csrf_cookie

app = FastAPI()

setup_rate_limiting(app)

FRONTEND_ORIGIN = os.getenv("FRONTEND_URL", "http://localhost:8081")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_ORIGIN],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*", "X-CSRF-Token"],
    expose_headers=["X-CSRF-Token"],
)

app.add_middleware(CSRFMiddleware)

app.include_router(meetups.router)
app.include_router(users.router)
# app.include_router(register.router)  # DIY auth - commented out
# app.include_router(login.router)     # DIY auth - commented out
app.include_router(supabase_auth.router)

@app.get("/")
def greet():
    return {"message": "Welcome to Chaatly"}

@app.get("/csrf-token")
def get_csrf_token(response: Response):
    token = generate_csrf_token()
    set_csrf_cookie(response, token)
    return {"csrf_token": token}