# services/tai_san_service.py
from core.supabase_client import supabase
from core.db_retry import retry_standard, retry_patient, retry_critical
from typing import List, Dict, Optional
from datetime import datetime


@retry_standard
def fetch_tai_san(
    search: str = "",
    page: int = 1,
    page_size: int = 100,
    trang_thai: str = ""
) -> List[Dict]:
    """Lấy danh sách Tài sản"""
    query = supabase.table("tai_san").select(
        "id, ma_tai_san, ten_tai_san, so_luong, tinh_trang, "
        "trang_thai, nguoi_muon, ngay_muon, ghi_chu, created_at"
    )
    
    if search:
        query = query.or_(f"ma_tai_san.ilike.%{search}%,ten_tai_san.ilike.%{search}%")
    
    if trang_thai:
        query = query.eq("trang_thai", trang_thai)
    
    start = (page - 1) * page_size
    end = start + page_size - 1
    
    res = query.order("ma_tai_san").range(start, end).execute()
    
    return res.data or []


@retry_standard
def count_tai_san(search: str = "", trang_thai: str = "") -> int:
    """Đếm tổng số"""
    query = supabase.table("tai_san").select("id", count="exact")
    
    if search:
        query = query.or_(f"ma_tai_san.ilike.%{search}%,ten_tai_san.ilike.%{search}%")
    
    if trang_thai:
        query = query.eq("trang_thai", trang_thai)
    
    res = query.execute()
    return res.count or 0


@retry_standard
def get_tai_san_by_id(id: str) -> Optional[Dict]:
    """Lấy 1 tài sản theo ID"""
    res = supabase.table("tai_san")\
        .select("*")\
        .eq("id", id)\
        .execute()
    
    return res.data[0] if res.data else None


@retry_standard
def get_tai_san_by_ma(ma_tai_san: str) -> Optional[Dict]:
    """Lấy tài sản theo mã"""
    res = supabase.table("tai_san")\
        .select("*")\
        .eq("ma_tai_san", ma_tai_san)\
        .execute()
    
    return res.data[0] if res.data else None


@retry_patient
def create_tai_san(data: Dict) -> Dict:
    """Thêm tài sản mới"""
    if "ma_tai_san" not in data or not data["ma_tai_san"]:
        raise ValueError("Thiếu mã tài sản")
    
    if "ten_tai_san" not in data or not data["ten_tai_san"]:
        raise ValueError("Thiếu tên tài sản")
    
    existing = get_tai_san_by_ma(data["ma_tai_san"])
    if existing:
        raise Exception(f"Mã '{data['ma_tai_san']}' đã tồn tại")
    
    validated_data = _validate_tai_san_data(data, is_create=True)
    
    try:
        res = supabase.table("tai_san").insert(validated_data).execute()
        
        if res.data and len(res.data) > 0:
            return res.data[0]
        
        raise Exception("Không nhận được response data")
        
    except Exception as ex:
        error_msg = str(ex)
        
        if "duplicate" in error_msg.lower() or "unique" in error_msg.lower():
            raise Exception(f"Mã '{data['ma_tai_san']}' đã tồn tại")
        
        raise Exception(f"Lỗi tạo tài sản: {error_msg}")


@retry_patient
def update_tai_san(id: str, data: Dict) -> Dict:
    """Cập nhật"""
    validated_data = _validate_tai_san_data(data)
    
    res = supabase.table("tai_san")\
        .update(validated_data)\
        .eq("id", id)\
        .execute()
    
    if not res.data or len(res.data) == 0:
        raise Exception(f"Không thể cập nhật ID: {id}")
    
    return res.data[0]


@retry_critical
def delete_tai_san(id: str) -> bool:
    """Xóa"""
    res = supabase.table("tai_san").delete().eq("id", id).execute()
    
    if not res.data or len(res.data) == 0:
        raise Exception(f"Không thể xóa ID: {id}")
    
    return True


@retry_patient
def bulk_update_tai_san(ids: List[str], data: Dict) -> int:
    """Cập nhật hàng loạt"""
    if not ids:
        raise ValueError("Danh sách IDs rỗng")
    
    if not data:
        raise ValueError("Dữ liệu update rỗng")
    
    validated_data = _validate_tai_san_data(data)
    
    success_count = 0
    errors = []
    
    for id in ids:
        try:
            update_tai_san(id, validated_data)
            success_count += 1
        except Exception as e:
            errors.append(f"ID {id}: {str(e)}")
    
    if errors:
        error_msg = "\n".join(errors[:5])
        if len(errors) > 5:
            error_msg += f"\n... và {len(errors) - 5} lỗi khác"
        raise Exception(f"Thất bại {len(errors)}/{len(ids)} tài sản:\n{error_msg}")
    
    return success_count


@retry_standard
def get_tai_san_statistics() -> Dict:
    """Thống kê"""
    all_records = supabase.table("tai_san")\
        .select("trang_thai, so_luong")\
        .execute()
    
    data = all_records.data or []
    
    stats = {
        "total": len(data),
        "total_so_luong": sum(r.get("so_luong", 0) or 0 for r in data),
        "by_trang_thai": {}
    }
    
    for r in data:
        status = r.get("trang_thai", "Trong phòng")
        stats["by_trang_thai"][status] = stats["by_trang_thai"].get(status, 0) + 1
    
    return stats


@retry_standard
def get_all_tai_san_for_export(ids: List[str] = None) -> List[Dict]:
    """Export"""
    query = supabase.table("tai_san").select("*")
    
    if ids:
        query = query.in_("id", ids)
    
    res = query.order("ma_tai_san").execute()
    
    return res.data or []


def _validate_tai_san_data(data: Dict, is_create: bool = False) -> Dict:
    """Validate"""
    validated = {}
    
    string_fields = ["ma_tai_san", "ten_tai_san", "tinh_trang", "trang_thai", "nguoi_muon", "ghi_chu"]
    for field in string_fields:
        if field in data:
            value = str(data[field]).strip() if data[field] else ""
            validated[field] = value
    
    if "so_luong" in data:
        try:
            so_luong = int(data["so_luong"]) if data["so_luong"] not in [None, ""] else 1
            validated["so_luong"] = so_luong
        except (ValueError, TypeError):
            raise ValueError("Số lượng phải là số nguyên")
    
    if "ngay_muon" in data and data["ngay_muon"]:
        value = str(data["ngay_muon"]).strip()
        if value:
            try:
                if "/" in value:
                    parts = value.split("/")
                    if len(parts) == 3:
                        value = f"{parts[2]}-{parts[1].zfill(2)}-{parts[0].zfill(2)}"
                
                datetime.strptime(value, "%Y-%m-%d")
                validated["ngay_muon"] = value
            except ValueError:
                raise ValueError(f"Ngày không hợp lệ: {value}")
    
    if is_create:
        validated.setdefault("so_luong", 1)
        validated.setdefault("trang_thai", "Trong phòng")
    
    return validated