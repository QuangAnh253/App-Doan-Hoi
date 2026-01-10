# services/classes_service.py
from core.supabase_client import supabase
from typing import List, Dict, Optional
from core.db_retry import retry_standard, retry_patient, retry_critical


@retry_standard
def fetch_classes(
    search: str = "",
    page: int = 1,
    page_size: int = 100,
    trang_thai: str = ""
) -> List[Dict]:
    query = supabase.table("lop_k76").select(
        "id, chi_doan, si_so, doan_phi, hoi_phi, tien_da_nop, "
        "so_luong_da_ky, trang_thai_so, vi_tri_luu_so, ghi_chu"
    )
    
    if search:
        query = query.ilike("chi_doan", f"%{search}%")
    
    if trang_thai:
        query = query.eq("trang_thai_so", trang_thai)
    
    start = (page - 1) * page_size
    end = start + page_size - 1
    
    res = query.order("chi_doan").range(start, end).execute()
    
    return res.data or []


@retry_standard
def count_classes(
    search: str = "",
    trang_thai: str = ""
) -> int:
    query = supabase.table("lop_k76").select("id", count="exact")
    
    if search:
        query = query.ilike("chi_doan", f"%{search}%")
    
    if trang_thai:
        query = query.eq("trang_thai_so", trang_thai)
    
    res = query.execute()
    return res.count or 0


@retry_standard
def get_class_by_id(class_id: str) -> Optional[Dict]:
    res = supabase.table("lop_k76")\
        .select("*")\
        .eq("id", class_id)\
        .single()\
        .execute()
    
    return res.data if res.data else None


@retry_standard
def get_class_by_chi_doan(chi_doan: str) -> Optional[Dict]:
    res = supabase.table("lop_k76")\
        .select("*")\
        .eq("chi_doan", chi_doan)\
        .execute()
    
    return res.data[0] if res.data else None


@retry_patient
def update_class(class_id: str, data: Dict) -> Dict:
    validated_data = _validate_class_data(data)
    
    res = supabase.table("lop_k76")\
        .update(validated_data)\
        .eq("id", class_id)\
        .execute()
    
    if not res.data:
        raise Exception(f"Không thể cập nhật lớp ID: {class_id}")
    
    return res.data[0]


@retry_patient
def bulk_update_classes(class_ids: List[str], data: Dict) -> int:
    if not class_ids:
        raise ValueError("Danh sách class_ids không được rỗng")
    
    if not data:
        raise ValueError("Dữ liệu update không được rỗng")
    
    validated_data = _validate_class_data(data)
    
    success_count = 0
    errors = []
    
    for class_id in class_ids:
        try:
            update_class(class_id, validated_data)
            success_count += 1
        except Exception as e:
            errors.append(f"Lớp {class_id}: {str(e)}")
    
    if errors:
        error_msg = "\n".join(errors[:5])
        if len(errors) > 5:
            error_msg += f"\n... và {len(errors) - 5} lỗi khác"
        raise Exception(f"Cập nhật thất bại cho {len(errors)}/{len(class_ids)} lớp:\n{error_msg}")
    
    return success_count


@retry_patient
def create_class(data: Dict) -> Dict:
    if "chi_doan" not in data or not data["chi_doan"]:
        raise ValueError("Thiếu thông tin chi đoàn")
    
    existing = get_class_by_chi_doan(data["chi_doan"])
    if existing:
        raise Exception(f"Chi đoàn '{data['chi_doan']}' đã tồn tại")
    
    validated_data = _validate_class_data(data, is_create=True)
    
    res = supabase.table("lop_k76").insert(validated_data).execute()
    
    if not res.data:
        raise Exception("Không thể tạo lớp mới")
    
    return res.data[0]


@retry_critical
def delete_class(class_id: str) -> bool:
    res = supabase.table("lop_k76").delete().eq("id", class_id).execute()
    
    if not res.data:
        raise Exception(f"Không thể xóa lớp ID: {class_id}")
    
    return True


@retry_standard
def get_class_statistics() -> Dict:
    all_classes = supabase.table("lop_k76")\
        .select("si_so, so_luong_da_ky, doan_phi, hoi_phi, tien_da_nop, trang_thai_so")\
        .execute()
    
    data = all_classes.data or []
    
    stats = {
        "total_classes": len(data),
        "total_si_so": sum(c.get("si_so", 0) or 0 for c in data),
        "total_da_ky": sum(c.get("so_luong_da_ky", 0) or 0 for c in data),
        "total_doan_phi": sum(c.get("doan_phi", 0) or 0 for c in data),
        "total_hoi_phi": sum(c.get("hoi_phi", 0) or 0 for c in data),
        "total_da_nop": sum(c.get("tien_da_nop", 0) or 0 for c in data),
        "by_trang_thai": {}
    }
    
    for c in data:
        status = c.get("trang_thai_so", "Chưa tiếp nhận")
        stats["by_trang_thai"][status] = stats["by_trang_thai"].get(status, 0) + 1
    
    return stats


def _validate_class_data(data: Dict, is_create: bool = False) -> Dict:
    validated = {}
    
    string_fields = ["chi_doan", "trang_thai_so", "vi_tri_luu_so", "ghi_chu"]
    for field in string_fields:
        if field in data:
            value = str(data[field]).strip() if data[field] else ""
            if value or not is_create:
                validated[field] = value
    
    int_fields = ["si_so", "so_luong_da_ky"]
    for field in int_fields:
        if field in data:
            try:
                validated[field] = int(data[field]) if data[field] not in [None, ""] else 0
            except (ValueError, TypeError):
                raise ValueError(f"Trường '{field}' phải là số nguyên")
    
    float_fields = ["doan_phi", "hoi_phi", "tien_da_nop"]
    for field in float_fields:
        if field in data:
            try:
                validated[field] = float(data[field]) if data[field] not in [None, ""] else 0.0
            except (ValueError, TypeError):
                raise ValueError(f"Trường '{field}' phải là số")
    
    if is_create:
        validated.setdefault("si_so", 0)
        validated.setdefault("so_luong_da_ky", 0)
        validated.setdefault("doan_phi", 0.0)
        validated.setdefault("hoi_phi", 0.0)
        validated.setdefault("tien_da_nop", 0.0)
        validated.setdefault("trang_thai_so", "Chưa tiếp nhận")
    
    return validated


@retry_standard
def get_classes_by_ids(class_ids: List[str]) -> List[Dict]:
    if not class_ids:
        return []
    
    res = supabase.table("lop_k76")\
        .select("*")\
        .in_("id", class_ids)\
        .execute()
    
    return res.data or []


@retry_standard
def search_classes_advanced(
    chi_doan: str = "",
    min_si_so: int = None,
    max_si_so: int = None,
    trang_thai: str = "",
    limit: int = 100
) -> List[Dict]:
    query = supabase.table("lop_k76").select("*")
    
    if chi_doan:
        query = query.ilike("chi_doan", f"%{chi_doan}%")
    
    if min_si_so is not None:
        query = query.gte("si_so", min_si_so)
    
    if max_si_so is not None:
        query = query.lte("si_so", max_si_so)
    
    if trang_thai:
        query = query.eq("trang_thai_so", trang_thai)
    
    res = query.limit(limit).order("chi_doan").execute()
    
    return res.data or []

@retry_patient
def import_classes(file_bytes: bytes) -> tuple[int, list[str]]:
    """Import classes từ Excel file"""
    import pandas as pd
    from io import BytesIO
    
    errors = []
    success_count = 0
    
    try:
        df = pd.read_excel(BytesIO(file_bytes))
        
        # Validate required columns
        required_cols = ["chi_doan"]
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            raise ValueError(f"Thiếu cột bắt buộc: {', '.join(missing_cols)}")
        
        # Process each row
        for idx, row in df.iterrows():
            try:
                chi_doan = str(row.get("chi_doan", "")).strip()
                if not chi_doan:
                    errors.append(f"Dòng {idx + 2}: Thiếu chi đoàn")
                    continue
                
                # Check if already exists
                existing = get_class_by_chi_doan(chi_doan)
                if existing:
                    errors.append(f"Dòng {idx + 2}: Chi đoàn '{chi_doan}' đã tồn tại")
                    continue
                
                # Parse numeric fields
                def safe_int(val, default=0):
                    try:
                        return int(val) if pd.notna(val) and str(val).strip() else default
                    except:
                        return default
                
                def safe_float(val, default=0.0):
                    try:
                        return float(val) if pd.notna(val) and str(val).strip() else default
                    except:
                        return default
                
                def safe_str(val, default=""):
                    return str(val).strip() if pd.notna(val) else default
                
                # Build payload
                payload = {
                    "chi_doan": chi_doan,
                    "si_so": safe_int(row.get("si_so")),
                    "so_luong_da_ky": safe_int(row.get("so_luong_da_ky")),
                    "doan_phi": safe_float(row.get("doan_phi")),
                    "hoi_phi": safe_float(row.get("hoi_phi")),
                    "tien_da_nop": safe_float(row.get("tien_da_nop")),
                    "trang_thai_so": safe_str(row.get("trang_thai_so"), "Chưa tiếp nhận"),
                    "vi_tri_luu_so": safe_str(row.get("vi_tri_luu_so")),
                    "ghi_chu": safe_str(row.get("ghi_chu")),
                }
                
                # Validate trang_thai_so
                valid_statuses = ["Chưa tiếp nhận", "Đang lưu VP", "Đã tiếp nhận"]
                if payload["trang_thai_so"] not in valid_statuses:
                    payload["trang_thai_so"] = "Chưa tiếp nhận"
                
                create_class(payload)
                success_count += 1
                
            except Exception as e:
                errors.append(f"Dòng {idx + 2}: {str(e)}")
        
        return success_count, errors
        
    except Exception as e:
        raise Exception(f"Lỗi đọc file: {str(e)}")


@retry_standard
def export_classes(class_ids: List[str]) -> bytes:
    """Export classes sang Excel file"""
    import pandas as pd
    from io import BytesIO
    
    if not class_ids:
        raise ValueError("Danh sách class_ids rỗng")
    
    # Fetch classes data
    classes = get_classes_by_ids(class_ids)
    
    if not classes:
        raise ValueError("Không tìm thấy dữ liệu để export")
    
    # Prepare data for export
    export_data = []
    for cls in classes:
        export_data.append({
            "chi_doan": cls.get("chi_doan", ""),
            "si_so": cls.get("si_so", 0),
            "so_luong_da_ky": cls.get("so_luong_da_ky", 0),
            "doan_phi": cls.get("doan_phi", 0.0),
            "hoi_phi": cls.get("hoi_phi", 0.0),
            "tien_da_nop": cls.get("tien_da_nop", 0.0),
            "trang_thai_so": cls.get("trang_thai_so", ""),
            "vi_tri_luu_so": cls.get("vi_tri_luu_so", ""),
            "ghi_chu": cls.get("ghi_chu", ""),
        })
    
    # Create DataFrame
    df = pd.DataFrame(export_data)
    
    # Write to Excel
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Quản lý Lớp K76')
        
        # Auto-adjust column widths
        worksheet = writer.sheets['Quản lý Lớp K76']
        for idx, col in enumerate(df.columns, 1):
            max_length = max(
                df[col].astype(str).map(len).max(),
                len(str(col))
            )
            col_letter = chr(64 + idx)
            worksheet.column_dimensions[col_letter].width = min(max_length + 3, 40)
    
    output.seek(0)
    return output.getvalue()


@retry_standard
def generate_class_template() -> bytes:
    """Tạo file Excel mẫu để import classes"""
    import pandas as pd
    from io import BytesIO
    
    template_data = {
        "chi_doan": ["76DCHT01", "76DCHT02", "76DCHT03"],
        "si_so": [45, 42, 48],
        "so_luong_da_ky": [40, 38, 45],
        "doan_phi": [100000, 100000, 100000],
        "hoi_phi": [50000, 50000, 50000],
        "tien_da_nop": [150000, 150000, 150000],
        "trang_thai_so": ["Chưa tiếp nhận", "Đang lưu VP", "Đã tiếp nhận"],
        "vi_tri_luu_so": ["", "Tủ B1 - Ngăn 3", ""],
        "ghi_chu": ["", "Cần kiểm tra sĩ số", ""],
    }
    
    df = pd.DataFrame(template_data)
    
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Quản lý Lớp K76')
        
        # Auto-adjust column widths
        worksheet = writer.sheets['Quản lý Lớp K76']
        for idx, col in enumerate(df.columns, 1):
            max_length = max(
                df[col].astype(str).map(len).max(),
                len(str(col))
            )
            col_letter = chr(64 + idx)
            worksheet.column_dimensions[col_letter].width = min(max_length + 3, 40)
    
    output.seek(0)
    return output.getvalue()