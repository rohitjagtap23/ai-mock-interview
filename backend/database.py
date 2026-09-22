import os

from dotenv import load_dotenv
from supabase import create_client, Client


load_dotenv()


SUPABASE_URL = os.getenv("SUPABASE_URL")

SUPABASE_SECRET_KEY = (
    os.getenv("SUPABASE_SECRET_KEY")
    or os.getenv("SUPABASE_SERVICE_ROLE_KEY")
)


if not SUPABASE_URL:
    raise ValueError(
        "SUPABASE_URL is missing from backend .env"
    )


if not SUPABASE_SECRET_KEY:
    raise ValueError(
        "SUPABASE_SECRET_KEY is missing from backend .env"
    )


SUPABASE_URL = SUPABASE_URL.strip().strip('"').strip("'")
SUPABASE_SECRET_KEY = (
    SUPABASE_SECRET_KEY
    .strip()
    .strip('"')
    .strip("'")
)


supabase: Client = create_client(
    SUPABASE_URL,
    SUPABASE_SECRET_KEY
)


print("Supabase client created successfully!")