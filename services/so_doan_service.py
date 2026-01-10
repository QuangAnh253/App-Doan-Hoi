# services/so_doan_service.py
from core.supabase_client import supabase
from core.db_retry import retry_standard, retry_patient, retry_critical
from typing import List, Dict, Optional
from datetime import datetime


@retry_standard
def fetch_so_doan(
    search: str = "",
    page: int = 1,
    page_size: int = 100,
    trang_thai: str = ""
) -> List[Dict]:
    """Lấy danh sách Sổ Đoàn"""
    query = supabase.table("so_doan").select(
        "id, ho_ten, ngay_sinh, que_quan, noi_ket_nap, ngay_ket_nap, "
        "trang_thai, ghi_chu, created_at"
    )
    
    if search:
        query = query.or_(f"ho_ten.ilike.%{search}%,que_quan.ilike.%{search}%")
    
    if trang_thai:
        query = query.eq("trang_thai", trang_thai)
    
    start = (page - 1) * page_size
    end = start + page_size - 1
    
    res = query.order("trang_thai", desc=False)\
               .order("ngay_sinh", desc=True)\
               .range(start, end)\
               .execute()
    
    return res.data or []


@retry_standard
def count_so_doan(search: str = "", trang_thai: str = "") -> int:
    """Đếm tổng số"""
    query = supabase.table("so_doan").select("id", count="exact")
    
    if search:
        query = query.or_(f"ho_ten.ilike.%{search}%,que_quan.ilike.%{search}%")
    
    if trang_thai:
        query = query.eq("trang_thai", trang_thai)
    
    res = query.execute()
    return res.count or 0


@retry_standard
def get_so_doan_by_id(id: str) -> Optional[Dict]:
    """Lấy 1 record theo ID"""
    res = supabase.table("so_doan")\
        .select("*")\
        .eq("id", id)\
        .execute()
    
    return res.data[0] if res.data else None


@retry_patient
def create_so_doan(data: Dict) -> Dict:
    """Thêm Sổ Đoàn mới"""
    if "ho_ten" not in data or not data["ho_ten"]:
        raise ValueError("Thiếu họ tên")
    
    if "ngay_sinh" not in data or not data["ngay_sinh"]:
        raise ValueError("Thiếu ngày sinh")
    
    validated_data = _validate_so_doan_data(data, is_create=True)
    
    try:
        res = supabase.table("so_doan").insert(validated_data).execute()
        
        if res.data and len(res.data) > 0:
            return res.data[0]
        
        raise Exception("Không nhận được response data")
        
    except Exception as ex:
        raise Exception(f"Lỗi tạo sổ đoàn: {str(ex)}")


@retry_patient
def update_so_doan(id: str, data: Dict) -> Dict:
    """Cập nhật"""
    validated_data = _validate_so_doan_data(data)
    
    res = supabase.table("so_doan")\
        .update(validated_data)\
        .eq("id", id)\
        .execute()
    
    if not res.data or len(res.data) == 0:
        raise Exception(f"Không thể cập nhật ID: {id}")
    
    return res.data[0]


@retry_critical
def delete_so_doan(id: str) -> bool:
    """Xóa"""
    res = supabase.table("so_doan").delete().eq("id", id).execute()
    
    if not res.data or len(res.data) == 0:
        raise Exception(f"Không thể xóa ID: {id}")
    
    return True


@retry_patient
def bulk_update_so_doan(ids: List[str], data: Dict) -> int:
    """Cập nhật hàng loạt"""
    if not ids:
        raise ValueError("Danh sách IDs rỗng")
    
    if not data:
        raise ValueError("Dữ liệu update rỗng")
    
    validated_data = _validate_so_doan_data(data)
    
    success_count = 0
    errors = []
    
    for id in ids:
        try:
            update_so_doan(id, validated_data)
            success_count += 1
        except Exception as e:
            errors.append(f"ID {id}: {str(e)}")
    
    if errors:
        error_msg = "\n".join(errors[:5])
        if len(errors) > 5:
            error_msg += f"\n... và {len(errors) - 5} lỗi khác"
        raise Exception(f"Thất bại {len(errors)}/{len(ids)} bản ghi:\n{error_msg}")
    
    return success_count


@retry_standard
def get_so_doan_statistics() -> Dict:
    """Thống kê"""
    all_records = supabase.table("so_doan")\
        .select("trang_thai")\
        .execute()
    
    data = all_records.data or []
    
    stats = {
        "total": len(data),
        "dang_luu_vp": sum(1 for r in data if r.get("trang_thai") == "Đang lưu VP"),
        "da_tra": sum(1 for r in data if r.get("trang_thai") == "Đã trả"),
    }
    
    return stats


@retry_standard
def get_all_so_doan_for_export(ids: List[str] = None) -> List[Dict]:
    """Export"""
    query = supabase.table("so_doan").select("*")
    
    if ids:
        query = query.in_("id", ids)
    
    res = query.order("trang_thai", desc=False)\
               .order("ngay_sinh", desc=True)\
               .execute()
    
    return res.data or []


def _validate_so_doan_data(data: Dict, is_create: bool = False) -> Dict:
    """Validate"""
    validated = {}
    
    string_fields = ["ho_ten", "que_quan", "noi_ket_nap", "trang_thai", "ghi_chu"]
    for field in string_fields:
        if field in data:
            value = str(data[field]).strip() if data[field] else ""
            if value or not is_create:
                validated[field] = value
    
    date_fields = ["ngay_sinh", "ngay_ket_nap"]
    for field in date_fields:
        if field in data and data[field]:
            value = str(data[field]).strip()
            if value:
                try:
                    if "/" in value:
                        parts = value.split("/")
                        if len(parts) == 3:
                            value = f"{parts[2]}-{parts[1].zfill(2)}-{parts[0].zfill(2)}"
                    
                    datetime.strptime(value, "%Y-%m-%d")
                    validated[field] = value
                except ValueError:
                    raise ValueError(f"Ngày không hợp lệ: {value}")
    
    if is_create:
        validated.setdefault("trang_thai", "Đang lưu VP")
    
    return validated