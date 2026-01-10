# services/profile_service.py
from core.supabase_client import supabase, supabase_admin
from core.db_retry import retry_standard, retry_patient, retry_critical
from typing import List, Dict, Optional
from datetime import datetime
import secrets
import string


@retry_standard
def get_user_profile(user_id: str) -> Optional[Dict]:
    """Lấy thông tin profile của user"""
    try:
        res = supabase.table('users')\
            .select('*')\
            .eq('id', user_id)\
            .execute()
        
        return res.data[0] if res.data else None
        
    except Exception as e:
        raise Exception(f"Lỗi lấy thông tin user: {str(e)}")


@retry_patient
def update_user_profile(user_id: str, data: Dict) -> Dict:
    """Cập nhật profile của user"""
    allowed_fields = ['full_name', 'phone', 'avatar_url', 'department']
    
    if 'password' in data:
        new_password = data.pop('password')
        
        if not supabase_admin:
            raise Exception("Không có quyền admin để đổi mật khẩu")
        
        try:
            supabase_admin.auth.admin.update_user_by_id(
                user_id,
                {"password": new_password}
            )
        except Exception as e:
            raise Exception(f"Lỗi cập nhật mật khẩu: {str(e)}")
    
    update_data = {k: v for k, v in data.items() if k in allowed_fields}
    
    if not update_data:
        return {"success": True}
    
    try:
        res = supabase.table('users')\
            .update(update_data)\
            .eq('id', user_id)\
            .execute()
        
        if not res.data:
            raise Exception(f"Không thể cập nhật profile cho user ID: {user_id}")
        
        return res.data[0]
        
    except Exception as e:
        raise Exception(f"Lỗi cập nhật profile: {str(e)}")


@retry_patient
def change_password(email: str, old_password: str, new_password: str) -> bool:
    """Đổi mật khẩu user"""
    try:
        auth_res = supabase.auth.sign_in_with_password({
            "email": email,
            "password": old_password
        })
        
        if not auth_res or not auth_res.user:
            raise Exception("Mật khẩu cũ không đúng")
        
        supabase.auth.update_user({
            "password": new_password
        })
        
        return True
        
    except Exception as e:
        raise Exception(f"Lỗi đổi mật khẩu: {str(e)}")


@retry_standard
def fetch_all_users(
    search: str = "",
    role_filter: str = "",
    department_filter: str = "",
    is_active_filter: Optional[bool] = None,
    page: int = 1,
    page_size: int = 100
) -> List[Dict]:
    """Lấy danh sách tất cả users (ADMIN only)"""
    try:
        query = supabase.table('users').select('*')
        
        if search:
            query = query.or_(
                f"full_name.ilike.%{search}%,"
                f"email.ilike.%{search}%,"
                f"username.ilike.%{search}%,"
                f"mssv.ilike.%{search}%"
            )
        
        if role_filter:
            query = query.eq('role', role_filter)
        
        if department_filter:
            query = query.eq('department', department_filter)
        
        if is_active_filter is not None:
            query = query.eq('is_active', is_active_filter)
        
        query = query.order('created_at', desc=True)
        
        start = (page - 1) * page_size
        end = start + page_size - 1
        query = query.range(start, end)
        
        res = query.execute()
        return res.data or []
        
    except Exception as e:
        raise Exception(f"Lỗi lấy danh sách users: {str(e)}")


@retry_standard
def count_all_users(
    search: str = "",
    role_filter: str = "",
    department_filter: str = "",
    is_active_filter: Optional[bool] = None
) -> int:
    """Đếm số lượng users"""
    try:
        query = supabase.table('users').select('id', count='exact')
        
        if search:
            query = query.or_(
                f"full_name.ilike.%{search}%,"
                f"email.ilike.%{search}%,"
                f"username.ilike.%{search}%,"
                f"mssv.ilike.%{search}%"
            )
        
        if role_filter:
            query = query.eq('role', role_filter)
        
        if department_filter:
            query = query.eq('department', department_filter)
        
        if is_active_filter is not None:
            query = query.eq('is_active', is_active_filter)
        
        res = query.execute()
        return res.count or 0
        
    except Exception as e:
        return 0


@retry_patient
def create_user_account(data: Dict) -> Dict:
    """Tạo tài khoản mới với Admin API (ADMIN only)"""
    try:
        required = ['full_name', 'username', 'role']
        for field in required:
            if not data.get(field):
                raise ValueError(f"Thiếu trường bắt buộc: {field}")
        
        username = data['username'].strip()
        password = data.get('password', 'Abc@123').strip()
        
        existing = supabase.table('users')\
            .select('id')\
            .eq('username', username)\
            .execute()
        
        if existing.data:
            raise Exception(f"Username '{username}' đã tồn tại")
        
        email = data.get('email', '').strip()
        if not email:
            email = f"{username}@doan-hoi.local"
        
        if not supabase_admin:
            raise Exception("Không có quyền admin. Vui lòng thêm SUPABASE_SERVICE_ROLE_KEY vào .env")
        
        try:
            auth_response = supabase_admin.auth.admin.create_user({
                "email": email,
                "password": password,
                "email_confirm": True,
                "user_metadata": {
                    "full_name": data['full_name'],
                    "username": username,
                    "role": data['role'],
                }
            })
            
            user_id = auth_response.user.id
            
        except Exception as auth_error:
            raise Exception(f"Lỗi tạo user trong authentication: {str(auth_error)}")
        
        user_data = {
            'id': user_id,
            'email': email,
            'username': username,
            'full_name': data['full_name'],
            'role': data['role'],
            'mssv': data.get('mssv', '').strip(),
            'chuc_vu': data.get('chuc_vu', '').strip(),
            'department': data.get('department', '').strip(),
            'phone': data.get('phone', '').strip(),
            'ghi_chu': data.get('ghi_chu', '').strip(),
            'is_active': True,
            'created_at': datetime.now().isoformat(),
        }
        
        res = supabase.table('users').insert(user_data).execute()
        
        if not res.data:
            raise Exception("Không thể tạo user record trong database")
        
        return res.data[0]
        
    except Exception as e:
        error_msg = str(e)
        
        if "duplicate" in error_msg.lower() or "unique" in error_msg.lower():
            if "email" in error_msg.lower():
                raise Exception(f"Email đã tồn tại")
            elif "username" in error_msg.lower():
                raise Exception(f"Username '{username}' đã tồn tại")
        
        raise Exception(f"Lỗi tạo tài khoản: {error_msg}")


@retry_patient
def update_user_account(user_id: str, data: Dict) -> Dict:
    """Cập nhật thông tin user với Admin API (ADMIN only)"""
    try:
        allowed_fields = [
            'full_name', 'mssv', 'chuc_vu', 'department',
            'phone', 'email', 'role', 'is_active', 'ghi_chu'
        ]
        
        update_data = {k: v for k, v in data.items() if k in allowed_fields}
        
        if not update_data:
            raise ValueError("Không có dữ liệu hợp lệ để cập nhật")
        
        if 'email' in update_data and supabase_admin:
            new_email = update_data['email']
            try:
                supabase_admin.auth.admin.update_user_by_id(
                    user_id,
                    {"email": new_email}
                )
            except Exception as e:
                pass
        
        res = supabase.table('users')\
            .update(update_data)\
            .eq('id', user_id)\
            .execute()
        
        if not res.data:
            raise Exception(f"Không thể cập nhật user ID: {user_id}")
        
        return res.data[0]
        
    except Exception as e:
        raise Exception(f"Lỗi cập nhật user: {str(e)}")


@retry_critical
def delete_user_account(user_id: str) -> bool:
    """Xóa tài khoản user (ADMIN only)"""
    try:
        res = supabase.table('users')\
            .update({'is_active': False})\
            .eq('id', user_id)\
            .execute()
        
        if not res.data:
            raise Exception(f"Không thể vô hiệu hóa user ID: {user_id}")
        
        return True
        
    except Exception as e:
        raise Exception(f"Lỗi xóa user: {str(e)}")


@retry_patient
def activate_user_account(user_id: str) -> bool:
    """Kích hoạt lại tài khoản đã bị vô hiệu hóa"""
    try:
        res = supabase.table('users')\
            .update({'is_active': True})\
            .eq('id', user_id)\
            .execute()
        
        if not res.data:
            raise Exception(f"Không thể kích hoạt user ID: {user_id}")
        
        return True
        
    except Exception as e:
        raise Exception(f"Lỗi kích hoạt user: {str(e)}")


@retry_patient
def reset_user_password(user_id: str, new_password: str = "Abc@123") -> bool:
    """Reset mật khẩu user với Admin API (ADMIN only)"""
    try:
        if not supabase_admin:
            raise Exception("Không có quyền admin. Vui lòng thêm SUPABASE_SERVICE_ROLE_KEY vào .env")
        
        user = supabase.table('users')\
            .select('email, username')\
            .eq('id', user_id)\
            .execute()
        
        if not user.data:
            raise Exception(f"Không tìm thấy user ID: {user_id}")
        
        supabase_admin.auth.admin.update_user_by_id(
            user_id,
            {"password": new_password}
        )
        
        return True
        
    except Exception as e:
        raise Exception(f"Lỗi reset mật khẩu: {str(e)}")


@retry_standard
def get_user_statistics() -> Dict:
    """Thống kê users (ADMIN only)"""
    try:
        all_users = supabase.table('users')\
            .select('role, department, is_active')\
            .execute()
        
        data = all_users.data or []
        
        stats = {
            'total': len(data),
            'active': sum(1 for u in data if u.get('is_active', True)),
            'inactive': sum(1 for u in data if not u.get('is_active', True)),
            'by_role': {},
            'by_department': {},
        }
        
        for u in data:
            role = u.get('role', 'STAFF')
            stats['by_role'][role] = stats['by_role'].get(role, 0) + 1
        
        for u in data:
            dept = u.get('department', 'Khác')
            if dept:
                stats['by_department'][dept] = stats['by_department'].get(dept, 0) + 1
        
        return stats
        
    except Exception as e:
        return {'total': 0, 'active': 0, 'inactive': 0, 'by_role': {}, 'by_department': {}}


def generate_random_password(length: int = 12) -> str:
    """Tạo mật khẩu ngẫu nhiên"""
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    password = ''.join(secrets.choice(alphabet) for _ in range(length))
    return password


def validate_username(username: str) -> bool:
    """Validate username format"""
    import re
    pattern = r'^[a-zA-Z0-9_.]{3,30}$'
    return bool(re.match(pattern, username))


def validate_password_strength(password: str) -> tuple[bool, str]:
    """Validate password strength"""
    if len(password) < 6:
        return False, "Mật khẩu phải có ít nhất 6 ký tự"
    
    if not any(c.isupper() for c in password):
        return False, "Mật khẩu phải có ít nhất 1 chữ hoa"
    
    if not any(c.islower() for c in password):
        return False, "Mật khẩu phải có ít nhất 1 chữ thường"
    
    if not any(c.isdigit() for c in password):
        return False, "Mật khẩu phải có ít nhất 1 số"
    
    return True, ""