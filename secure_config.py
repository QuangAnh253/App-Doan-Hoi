"""
Module giải mã và load config files một cách bảo mật

✅ SECURE VERSION:
- Obfuscated password/salt (giống encrypt_config.py)
- Tự động detect file path (dev vs production)
- Anti-injection validation
"""

import os
import sys
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


# ============================================================================
# 🔐 OBFUSCATED CREDENTIALS - PHẢI GIỐNG encrypt_config.py
# ============================================================================
def _get_password() -> str:
    """Obfuscated password - decode để lấy password thực"""
    # ⚠️ QUAN TRỌNG: Phải GIỐNG HỆT với encrypt_config.py
    obfuscated = "QXBwZG9hbmhvaUBRdWFuaDIwMjY="
    return base64.b64decode(obfuscated).decode()


def _get_salt() -> bytes:
    """Obfuscated salt - decode để lấy salt thực"""
    # ⚠️ QUAN TRỌNG: Phải GIỐNG HỆT với encrypt_config.py
    obfuscated = "TWFfaG9hX2FwcF9Eb2FuX0hvaQ=="
    return base64.b64decode(obfuscated)


# ============================================================================
# KEY GENERATION
# ============================================================================
def _generate_key() -> bytes:
    """Tạo key giải mã từ password obfuscated"""
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=_get_salt(),
        iterations=100000,
    )
    key = base64.urlsafe_b64encode(kdf.derive(_get_password().encode()))
    return key


# ============================================================================
# PATH HELPERS
# ============================================================================
def _get_base_path() -> str:
    """
    Lấy đường dẫn gốc của app
    - Development: thư mục chứa secure_config.py (là thư mục project root)
    - Production (PyInstaller): sys._MEIPASS
    """
    if getattr(sys, 'frozen', False):
        # PyInstaller EXE
        return sys._MEIPASS
    else:
        # Development - thư mục chứa file secure_config.py chính là root
        return os.path.dirname(os.path.abspath(__file__))


# ============================================================================
# DECRYPTION
# ============================================================================
def _decrypt_file(encrypted_path: str) -> bytes:
    """Giải mã file"""
    if not os.path.exists(encrypted_path):
        raise FileNotFoundError(f"Encrypted file not found: {encrypted_path}")
    
    key = _generate_key()
    fernet = Fernet(key)
    
    with open(encrypted_path, 'rb') as f:
        encrypted_data = f.read()
    
    try:
        decrypted_data = fernet.decrypt(encrypted_data)
        return decrypted_data
    except Exception as e:
        raise ValueError(
            f"Failed to decrypt {encrypted_path}. "
            f"Possible reasons: wrong password, corrupted file, or tampered data."
        ) from e


# ============================================================================
# LOAD .ENV
# ============================================================================
def load_env_variables() -> dict:
    """
    Load và giải mã .env file
    Returns: dict của environment variables
    """
    base_path = _get_base_path()
    encrypted_env_path = os.path.join(base_path, '.env.encrypted')
    
    print(f"📂 Loading encrypted .env from: {encrypted_env_path}")
    
    try:
        decrypted_data = _decrypt_file(encrypted_env_path)
        
        # Parse .env content
        env_vars = {}
        env_content = decrypted_data.decode('utf-8')
        
        for line in env_content.split('\n'):
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                key = key.strip()
                value = value.strip().strip('"').strip("'")
                env_vars[key] = value
                # Set to os.environ
                os.environ[key] = value
        
        print(f"✅ Loaded {len(env_vars)} environment variables")
        return env_vars
        
    except FileNotFoundError:
        print(f"❌ File .env.encrypted không tồn tại!")
        print(f"   Hãy chạy: python encrypt_config.py")
        raise
    except Exception as e:
        print(f"❌ Error loading .env: {e}")
        raise


# ============================================================================
# LOAD CREDENTIALS.JSON
# ============================================================================
def load_credentials_json() -> dict:
    """
    Load và giải mã credentials.json
    Returns: dict của credentials
    """
    base_path = _get_base_path()
    encrypted_cred_path = os.path.join(base_path, 'credentials.json.encrypted')
    
    print(f"📂 Loading encrypted credentials from: {encrypted_cred_path}")
    
    try:
        decrypted_data = _decrypt_file(encrypted_cred_path)
        
        import json
        credentials = json.loads(decrypted_data.decode('utf-8'))
        
        print(f"✅ Loaded credentials successfully")
        return credentials
        
    except FileNotFoundError:
        print(f"❌ File credentials.json.encrypted không tồn tại!")
        print(f"   Hãy chạy: python encrypt_config.py")
        raise
    except Exception as e:
        print(f"❌ Error loading credentials: {e}")
        raise


# ============================================================================
# GET CREDENTIALS PATH (for libraries requiring file path)
# ============================================================================
def get_credentials_path() -> str:
    """
    Tạo file credentials.json tạm từ encrypted file
    Trả về đường dẫn đến file tạm
    (Cần thiết cho các thư viện yêu cầu file path như Google API)
    """
    import tempfile
    import json
    
    credentials = load_credentials_json()
    
    # Tạo temp file
    temp_dir = tempfile.gettempdir()
    temp_cred_path = os.path.join(temp_dir, 'credentials.json')
    
    with open(temp_cred_path, 'w') as f:
        json.dump(credentials, f)
    
    return temp_cred_path


# ============================================================================
# ANTI-INJECTION VALIDATION
# ============================================================================
def validate_env_value(key: str, value: str) -> bool:
    """
    Kiểm tra giá trị env có chứa ký tự nguy hiểm không
    """
    dangerous_patterns = [
        ';', '&&', '||', '`', '$(',  # Command injection
        '<', '>',                     # Redirection
        '../',                        # Path traversal
        '\n', '\r',                   # Newline injection
    ]
    
    for pattern in dangerous_patterns:
        if pattern in value:
            print(f"⚠️  WARNING: Suspicious pattern '{pattern}' in {key}")
            return False
    
    return True


def load_env_variables_safe() -> dict:
    """Load .env với validation chống injection"""
    env_vars = load_env_variables()
    
    validated = {}
    for key, value in env_vars.items():
        if validate_env_value(key, value):
            validated[key] = value
        else:
            raise ValueError(f"Potentially malicious value detected in {key}")
    
    return validated


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================
def get_supabase_config() -> dict:
    """Lấy Supabase config từ .env"""
    env = load_env_variables()
    return {
        'url': env.get('SUPABASE_URL', ''),
        'anon_key': env.get('SUPABASE_ANON_KEY', ''),
        'service_role_key': env.get('SUPABASE_SERVICE_ROLE_KEY', ''),
    }


def get_email_config() -> dict:
    """Lấy Email config từ .env"""
    env = load_env_variables()
    return {
        'smtp_server': env.get('SMTP_SERVER', ''),
        'smtp_port': int(env.get('SMTP_PORT', '587')),
        'email': env.get('EMAIL_ADDRESS', ''),
        'password': env.get('EMAIL_PASSWORD', ''),
    }


# ============================================================================
# TESTING (chỉ dùng khi develop)
# ============================================================================
if __name__ == "__main__":
    print("\n🧪 TESTING SECURE CONFIG\n")
    
    try:
        print("Testing .env decryption...")
        env_vars = load_env_variables()
        print(f"✅ Loaded {len(env_vars)} variables")
        print(f"   Keys: {', '.join(env_vars.keys())}")
        print()
        
        print("Testing credentials.json decryption...")
        creds = load_credentials_json()
        print(f"✅ Loaded credentials")
        print(f"   Keys: {', '.join(creds.keys())}")
        print()
        
        print("Testing temp credentials path...")
        temp_path = get_credentials_path()
        print(f"✅ Created temp file: {temp_path}")
        print()
        
        print("🎉 ALL TESTS PASSED!")
        
    except Exception as e:
        print(f"❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()