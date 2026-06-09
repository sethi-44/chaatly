from backend.app.database import SessionLocal
from backend.app.models import User

session=SessionLocal()

user=User(
    username="Varuna",
    email="varuna@gmail.com"
)

session.add(user)
session.commit()

print("User Created!")