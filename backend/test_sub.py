import asyncio
import os
import sys

# Ensure we can import app
sys.path.insert(0, os.path.abspath("."))
from app.supabase_auth import get_supabase_admin

async def test():
    try:
        res = get_supabase_admin().create_user({
            "email": "test3@example.com",
            "password": "password123",
            "email_confirm": True
        })
        print("Success!")
    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    asyncio.run(test())
