# utils/validator.py
import re

def validate_mssv(mssv: str) -> bool:
    """
    Validate MSSV: chỉ cho phép số, 8-10 ký tự
    """
    if not mssv:
        return False
    return bool(re.match(r'^\d{8,10}$', str(mssv).strip()))


def validate_email(email: str) -> bool:
    """
    Validate email cơ bản
    """
    if not email:
        return True  # Email không bắt buộc
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email.strip()))


def validate_phone(phone: str) -> bool:
    """
    Validate số điện thoại VN: 10-11 số
    """
    if not phone:
        return True  # SĐT không bắt buộc
    return bool(re.match(r'^0\d{9,10}$', str(phone).strip()))


def validate_chi_doan(chi_doan: str) -> bool:
    """
    Validate tên chi đoàn: không được rỗng
    """
    return bool(chi_doan and len(chi_doan.strip()) > 0)


def validate_required_fields(data: dict, required: list[str]) -> tuple[bool, str]:
    """
    Kiểm tra các trường bắt buộc
    Returns: (is_valid, error_message)
    """
    missing = [field for field in required if not data.get(field)]
    if missing:
        return False, f"Thiếu trường bắt buộc: {', '.join(missing)}"
    return True, ""
