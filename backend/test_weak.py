import asyncio
import os
import sys

sys.path.insert(0, os.path.abspath("."))
from app.supabase_auth import get_supabase_admin

async def test():
    try:
        res = get_supabase_admin().create_user({
            "email": "weak_pass_123@example.com",
            "password": "password",
            "email_confirm": True
        })
        print("Success!")
    except Exception as e:
        print("Error:", repr(e))

if __name__ == "__main__":
    asyncio.run(test())
