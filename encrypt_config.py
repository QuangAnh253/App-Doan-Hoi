"""
Script mã hóa .env và credentials.json
Chạy script này TRƯỚC KHI BUILD để tạo file encrypted

✅ SECURE VERSION:
- Obfuscated password/salt
- Không tạo encryption_info.json
- Tự động verify encryption
"""
import os
import json
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


# ============================================================================
# 🔐 OBFUSCATED CREDENTIALS
# ============================================================================
def _get_password() -> str:
    """Obfuscated password - decode để lấy password thực"""
    # Encoded: base64("QuanLyDoanHoi_2025_SecretKey_DoNotShare") reversed
    obfuscated = "QXBwZG9hbmhvaUBRdWFuaDIwMjY="
    return base64.b64decode(obfuscated).decode()


def _get_salt() -> bytes:
    """Obfuscated salt - decode để lấy salt thực"""
    # Encoded: base64(b"doan_hoi_salt_2025_secure") reversed
    obfuscated = "TWFfaG9hX2FwcF9Eb2FuX0hvaQ=="
    return base64.b64decode(obfuscated)


# ============================================================================
# ENCRYPTION FUNCTIONS
# ============================================================================
def generate_key_from_password(password: str, salt: bytes) -> bytes:
    """Tạo key mã hóa từ password"""
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
    )
    key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
    return key


def encrypt_file(file_path: str, output_path: str, key: bytes) -> bool:
    """Mã hóa một file - Returns True nếu thành công"""
    try:
        fernet = Fernet(key)
        
        with open(file_path, 'rb') as f:
            data = f.read()
        
        encrypted_data = fernet.encrypt(data)
        
        with open(output_path, 'wb') as f:
            f.write(encrypted_data)
        
        print(f"✅ Encrypted: {file_path} -> {output_path}")
        return True
    
    except FileNotFoundError:
        print(f"❌ File không tồn tại: {file_path}")
        return False
    except Exception as e:
        print(f"❌ Lỗi mã hóa {file_path}: {str(e)}")
        return False


def verify_decryption(encrypted_path: str, key: bytes, original_path: str) -> bool:
    """Kiểm tra xem file encrypted có thể decrypt được không"""
    try:
        fernet = Fernet(key)
        
        with open(encrypted_path, 'rb') as f:
            encrypted_data = f.read()
        
        decrypted_data = fernet.decrypt(encrypted_data)
        
        with open(original_path, 'rb') as f:
            original_data = f.read()
        
        if decrypted_data == original_data:
            print(f"✅ Xác thực: {encrypted_path} có thể decrypt")
            return True
        else:
            print(f"⚠️  Cảnh báo: Decrypt không khớp với gốc")
            return False
    
    except Exception as e:
        print(f"❌ Lỗi xác thực: {str(e)}")
        return False


# ============================================================================
# MAIN
# ============================================================================
def main():
    print("")
    print("="*60)
    print("  🔐 MÃ HÓA CONFIG FILES (SECURE)")
    print("="*60)
    print("")
    
    # Lấy credentials (obfuscated)
    PASSWORD = _get_password()
    SALT = _get_salt()
    
    print("🔑 Đã load encryption credentials (obfuscated)")
    print("")
    
    # Tạo encryption key
    key = generate_key_from_password(PASSWORD, SALT)
    
    # Files cần encrypt
    files_to_encrypt = [
        ('.env', '.env.encrypted'),
        ('credentials.json', 'credentials.json.encrypted'),
    ]
    
    success_count = 0
    failed_count = 0
    
    # Encrypt từng file
    for original, encrypted in files_to_encrypt:
        if not os.path.exists(original):
            print(f"⏭️  Bỏ qua: {original} (không tồn tại)")
            continue
        
        # Encrypt
        if encrypt_file(original, encrypted, key):
            # Verify
            if verify_decryption(encrypted, key, original):
                success_count += 1
            else:
                failed_count += 1
        else:
            failed_count += 1
    
    print("")
    print("="*60)
    print("  📊 KẾT QUẢ")
    print("="*60)
    print(f"✅ Thành công: {success_count}")
    print(f"❌ Thất bại: {failed_count}")
    print("")
    
    if success_count > 0:
        print("📁 Files đã tạo:")
        if os.path.exists('.env.encrypted'):
            size = os.path.getsize('.env.encrypted')
            print(f"   - .env.encrypted ({size} bytes)")
        if os.path.exists('credentials.json.encrypted'):
            size = os.path.getsize('credentials.json.encrypted')
            print(f"   - credentials.json.encrypted ({size} bytes)")
        print("")
        
        print("📝 Next steps:")
        print("   1. Chạy: .\\build.ps1")
        print("   2. Hoặc: pyinstaller --clean QuanLyDoanHoi.spec")
        print("")
        print("⚠️  QUAN TRỌNG:")
        print("   - XÓA .env và credentials.json gốc khỏi dist/ sau khi build")
        print("   - KHÔNG commit file .encrypted lên Git public")
        print("")
    else:
        print("❌ Không có file nào được mã hóa thành công!")
        print("   Kiểm tra lại .env và credentials.json có tồn tại không")
        print("")


# ============================================================================
# HELPER: Generate obfuscated credentials (chỉ dùng 1 lần khi setup)
# ============================================================================
def generate_obfuscated_credentials():
    """
    Helper để tạo obfuscated string từ password/salt mới
    Chạy: python encrypt_config.py --generate
    """
    print("\n🔧 GENERATE OBFUSCATED CREDENTIALS\n")
    
    password = input("Nhập PASSWORD mới: ")
    salt = input("Nhập SALT mới: ").encode()
    
    # Generate obfuscated
    password_obf = base64.b64encode(password.encode()).decode()[::-1]
    salt_obf = base64.b64encode(salt).decode()[::-1]
    
    print("\n✅ Copy đoạn code này vào _get_password() và _get_salt():\n")
    print(f'def _get_password() -> str:')
    print(f'    obfuscated = "{password_obf}"[::-1]')
    print(f'    return base64.b64decode(obfuscated).decode()')
    print()
    print(f'def _get_salt() -> bytes:')
    print(f'    obfuscated = "{salt_obf}"[::-1]')
    print(f'    return base64.b64decode(obfuscated)')
    print()
    print("⚠️  Nhớ cập nhật CÙNG LÚC vào secure_config.py!")
    print()


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--generate":
        # Chế độ generate obfuscated credentials
        generate_obfuscated_credentials()
    else:
        # Chế độ encrypt bình thường
        main()