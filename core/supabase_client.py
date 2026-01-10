# core/supabase_client.py
import os
from dotenv import load_dotenv
from supabase import create_client, Client

try:
    from secure_config import load_env_variables
    load_env_variables()  # Load từ file encrypted
except ImportError:
    # Fallback: Development mode
    from dotenv import load_dotenv
    load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL", "https://gelhujjzrxqvcxwfguvf.supabase.co")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY", "")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")

if not SUPABASE_ANON_KEY:
    raise ValueError("Thiếu SUPABASE_ANON_KEY trong environment variables")

_supabase: Client | None = None
_supabase_admin: Client | None = None


def get_supabase() -> Client:
    global _supabase
    if _supabase is None:
        _supabase = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
    return _supabase


def get_supabase_admin() -> Client | None:
    global _supabase_admin
    if not SUPABASE_SERVICE_ROLE_KEY:
        return None
    if _supabase_admin is None:
        _supabase_admin = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
    return _supabase_admin


supabase: Client = get_supabase()
supabase_admin: Client | None = get_supabase_admin()