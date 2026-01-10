# core/auth.py
import os
import json
import time
from typing import Optional, Tuple
from dataclasses import dataclass

from core.supabase_client import supabase

CREDENTIALS_FILE = "user_credentials.json"


@dataclass
class UserSession:
    user_id: str
    email: str
    role: str
    full_name: str = ""


def retry_on_error(max_retries=3, delay=2):
    def decorator(func):
        def wrapper(*args, **kwargs):
            last_error = None
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    error_msg = str(e).lower()
                    is_network_error = any(keyword in error_msg for keyword in 
                        ['disconnect', 'timeout', 'connection', 'network', 'unavailable'])
                    
                    if is_network_error and attempt < max_retries - 1:
                        wait_time = delay * (attempt + 1)
                        time.sleep(wait_time)
                        last_error = e
                        continue
                    else:
                        raise
            raise last_error if last_error else Exception("Max retries reached")
        return wrapper
    return decorator


def save_credentials(identifier: str, password: str) -> None:
    try:
        data = {'identifier': identifier, 'password': password}
        with open(CREDENTIALS_FILE, 'w') as f:
            json.dump(data, f)
    except Exception:
        pass


def load_credentials() -> Tuple[Optional[str], Optional[str]]:
    try:
        if os.path.exists(CREDENTIALS_FILE):
            with open(CREDENTIALS_FILE, 'r') as f:
                data = json.load(f)
                identifier = data.get('identifier')
                password = data.get('password')
                if identifier and password:
                    return identifier, password
    except Exception:
        pass
    return None, None


def clear_credentials() -> None:
    try:
        if os.path.exists(CREDENTIALS_FILE):
            os.remove(CREDENTIALS_FILE)
    except Exception:
        pass


@retry_on_error(max_retries=3, delay=2)
def login(identifier: str, password: str, remember: bool = False) -> Optional[UserSession]:
    is_email = '@' in identifier
    
    if is_email:
        auth_response = supabase.auth.sign_in_with_password({
            "email": identifier,
            "password": password
        })
        
        if not auth_response or not auth_response.user:
            return None
        
        user_id = auth_response.user.id
        email = auth_response.user.email
        
    else:
        user_result = supabase.table('users')\
            .select('id, email, username')\
            .eq('username', identifier)\
            .eq('is_active', True)\
            .execute()
        
        if not user_result.data:
            return None
        
        user_data = user_result.data[0]
        user_id = user_data['id']
        email = user_data['email']
        
        try:
            auth_response = supabase.auth.sign_in_with_password({
                "email": email,
                "password": password
            })
            
            if not auth_response or not auth_response.user:
                return None
            
        except Exception:
            return None
    
    user_details = supabase.table('users')\
        .select('role, full_name, is_active')\
        .eq('id', user_id)\
        .execute()
    
    if not user_details.data:
        return None
    
    user_info = user_details.data[0]
    
    if not user_info.get('is_active', True):
        raise Exception("Tài khoản đã bị khóa. Vui lòng liên hệ admin.")
    
    role = user_info.get('role', 'NEW_USER')
    full_name = user_info.get('full_name', '')
    
    if remember:
        save_credentials(identifier, password)
    else:
        clear_credentials()
    
    return UserSession(
        user_id=user_id,
        email=email,
        role=role,
        full_name=full_name
    )


@retry_on_error(max_retries=3, delay=2)
def login_with_oauth(provider: str) -> str:
    redirect_to = os.getenv('OAUTH_REDIRECT_URL', 'http://localhost:8000/auth/callback')
    
    response = supabase.auth.sign_in_with_oauth({
        "provider": provider,
        "options": {
            "redirect_to": redirect_to
        }
    })
    
    if response and hasattr(response, 'url'):
        return response.url
    
    raise Exception(f"Could not generate OAuth URL for {provider}")


def logout() -> None:
    try:
        supabase.auth.sign_out()
        clear_credentials()
    except Exception:
        pass


def is_admin(role: str) -> bool:
    return role == "ADMIN"


def get_current_user() -> Optional[dict]:
    try:
        user = supabase.auth.get_user()
        if user:
            return user.user
        return None
    except Exception:
        return None


@retry_on_error(max_retries=3, delay=2)
def exchange_code_for_session(code: str):
    response = supabase.auth.exchange_code_for_session({
        "auth_code": code
    })
    
    if response and response.user:
        return response
    
    raise Exception("Failed to exchange code for session")