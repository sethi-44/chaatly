import os
from dotenv import load_dotenv
load_dotenv()
from supabase import create_client

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
try:
    supabase.storage.create_bucket("profile-pictures", {"public": True})
    print("Bucket created successfully")
except Exception as e:
    print("Error (might already exist):", e)
