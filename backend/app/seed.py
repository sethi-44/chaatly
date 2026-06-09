from database import SessionLocal
from models import User

session=SessionLocal()

user=User(
    username="Harshit",
    email="harshit@gmail.com"
)

session.add(user)
session.commit()

print("User Created!")