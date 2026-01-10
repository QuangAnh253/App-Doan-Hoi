# services/students_service.py
from core.supabase_client import supabase
from core.db_retry import retry_standard, retry_patient, retry_critical


@retry_standard
def fetch_students(
    search: str = "", 
    lop: str = "",
    khoa: str = "",
    trang_thai: set = None,
    page: int = 1, 
    page_size: int = 100
) -> list[dict]:
    query = supabase.table("doan_vien_k74_k75").select(
        "mssv, ho_ten, ngay_sinh, noi_sinh, lop, khoa, trang_thai_so, "
        "da_nop_doan_phi, da_nop_hoi_phi, vi_tri_luu_so, ghi_chu"
    )
    
    sort_by_class_then_name = False
    sort_by_name_only = False
    
    if search:
        search_normalized = search.strip()
        if search_normalized.isdigit():
            query = query.ilike("mssv", f"{search_normalized}%")
        else:
            query = query.ilike("ho_ten", f"%{search_normalized}%")
            sort_by_name_only = True
    
    if lop:
        lop_normalized = lop.strip()
        query = query.ilike("lop", lop_normalized)
        
        if lop_normalized and lop_normalized[-1].isdigit():
            sort_by_name_only = True
        else:
            sort_by_class_then_name = True
    
    if khoa:
        query = query.ilike("khoa", f"%{khoa.strip()}%")
    
    if trang_thai:
        conditions = []
        
        if "dang_luu_vp" in trang_thai:
            conditions.append(("trang_thai_so", "eq", "Đang lưu VP"))
        if "da_tra_so" in trang_thai:
            conditions.append(("trang_thai_so", "eq", "Đã tiếp nhận"))
        if "chua_doan_phi" in trang_thai:
            conditions.append(("da_nop_doan_phi", "eq", False))
        if "chua_hoi_phi" in trang_thai:
            conditions.append(("da_nop_hoi_phi", "eq", False))
        
        if conditions:
            or_filters = ",".join([
                f"{field}.{op}.{value}" for field, op, value in conditions
            ])
            query = query.or_(or_filters)
    
    start = (page - 1) * page_size
    end = start + page_size - 1
    
    res = query.range(start, end).execute()
    data = res.data or []
    
    def normalize_vietnamese_for_sort(text: str) -> str:
        if not text:
            return ""
        return text.replace("Đ", "D~").replace("đ", "d~")
    
    def get_name_sort_key(ho_ten: str):
        if not ho_ten:
            return ("",)
        
        parts = ho_ten.strip().split()
        if len(parts) == 0:
            return ("",)
        elif len(parts) == 1:
            return (normalize_vietnamese_for_sort(parts[0]), "")
        elif len(parts) == 2:
            return (
                normalize_vietnamese_for_sort(parts[1]),
                normalize_vietnamese_for_sort(parts[0])
            )
        else:
            ten_chinh = parts[-1]
            ho = parts[0]
            ten_dem_list = parts[1:-1]
            
            return (
                normalize_vietnamese_for_sort(ten_chinh),
                normalize_vietnamese_for_sort(ho),
                *[normalize_vietnamese_for_sort(t) for t in ten_dem_list]
            )
    
    if sort_by_class_then_name:
        data.sort(key=lambda x: (
            x.get("lop", ""),
            get_name_sort_key(x.get("ho_ten", ""))
        ))
    elif sort_by_name_only:
        data.sort(key=lambda x: get_name_sort_key(x.get("ho_ten", "")))
    
    return data


@retry_standard
def count_students(search: str = "", lop: str = "", khoa: str = "", trang_thai: set = None) -> int:
    query = supabase.table("doan_vien_k74_k75").select("mssv", count="exact")
    
    if search:
        search_normalized = search.strip()
        if search_normalized.isdigit():
            query = query.ilike("mssv", f"{search_normalized}%")
        else:
            query = query.ilike("ho_ten", f"%{search_normalized}%")
    
    if lop:
        query = query.ilike("lop", lop.strip())
    
    if khoa:
        query = query.ilike("khoa", f"%{khoa.strip()}%")
    
    if trang_thai:
        conditions = []
        if "dang_luu_vp" in trang_thai:
            conditions.append(("trang_thai_so", "eq", "Đang lưu VP"))
        if "da_tra_so" in trang_thai:
            conditions.append(("trang_thai_so", "eq", "Đã tiếp nhận"))
        if "chua_doan_phi" in trang_thai:
            conditions.append(("da_nop_doan_phi", "eq", False))
        if "chua_hoi_phi" in trang_thai:
            conditions.append(("da_nop_hoi_phi", "eq", False))
        
        if conditions:
            or_filters = ",".join([
                f"{field}.{op}.{value}" for field, op, value in conditions
            ])
            query = query.or_(or_filters)
    
    res = query.execute()
    return res.count or 0


@retry_standard
def get_students(limit: int = 100, offset: int = 0) -> list[dict]:
    res = supabase.table("doan_vien_k74_k75")\
        .select("*")\
        .order("mssv", desc=False)\
        .range(offset, offset + limit - 1)\
        .execute()
    return res.data or []


@retry_standard
def get_student_by_mssv(mssv: str) -> dict | None:
    res = supabase.table("doan_vien_k74_k75")\
        .select("*")\
        .eq("mssv", mssv)\
        .execute()
    return res.data[0] if res.data else None

@retry_patient
def add_student(data: dict):
    """Thêm sinh viên mới"""
    if not data:
        raise ValueError("Không có dữ liệu để thêm")
    
    # Validate required fields
    required_fields = ["mssv", "ho_ten", "lop", "khoa"]
    missing_fields = [field for field in required_fields if not data.get(field)]
    
    if missing_fields:
        raise ValueError(f"Thiếu thông tin bắt buộc: {', '.join(missing_fields)}")
    
    mssv = data.get("mssv", "").strip()
    if not mssv:
        raise ValueError("MSSV không được rỗng")
    
    # Check if MSSV already exists
    existing = supabase.table("doan_vien_k74_k75")\
        .select("mssv")\
        .eq("mssv", mssv)\
        .execute()
    
    if existing.data:
        raise ValueError(f"MSSV {mssv} đã tồn tại trong hệ thống")
    
    # Clean data
    cleaned_data = {}
    for k, v in data.items():
        if isinstance(v, bool):
            cleaned_data[k] = v
        elif isinstance(v, str):
            cleaned_data[k] = v.strip()
        elif isinstance(v, (int, float)):
            cleaned_data[k] = v
    
    # Set defaults for optional fields
    cleaned_data.setdefault("trang_thai_so", "Chưa tiếp nhận")
    cleaned_data.setdefault("da_nop_doan_phi", False)
    cleaned_data.setdefault("da_nop_hoi_phi", False)
    cleaned_data.setdefault("vi_tri_luu_so", "")
    cleaned_data.setdefault("ghi_chu", "")
    cleaned_data.setdefault("ngay_sinh", "")
    cleaned_data.setdefault("noi_sinh", "")
    
    # Insert into database
    result = supabase.table("doan_vien_k74_k75")\
        .insert(cleaned_data)\
        .execute()
    
    if not result.data:
        raise Exception("Không thể thêm sinh viên vào database")
    
    return result.data[0]

@retry_patient
def update_student(mssv: str, data: dict):
    if not mssv:
        raise ValueError("MSSV không được rỗng")
    
    if not data:
        raise ValueError("Không có dữ liệu để cập nhật")
    
    forbidden = {"mssv", "ho_ten"}
    forbidden_found = [k for k in data.keys() if k in forbidden]
    if forbidden_found:
        raise ValueError(f"Không được update: {', '.join(forbidden_found)}")
    
    cleaned_data = {}
    for k, v in data.items():
        if isinstance(v, bool):
            cleaned_data[k] = v
        elif isinstance(v, str):
            cleaned_data[k] = v.strip()
        elif isinstance(v, (int, float)):
            cleaned_data[k] = v
    
    if not cleaned_data:
        raise ValueError("Không có dữ liệu hợp lệ")
    
    check_query = supabase.table("doan_vien_k74_k75")\
        .select("mssv, ho_ten")\
        .eq("mssv", mssv)\
        .execute()
    
    if not check_query.data:
        raise Exception(
            f"Không tìm thấy sinh viên MSSV={mssv}. "
            f"Vui lòng reload trang (F5)."
        )
    
    supabase.table("doan_vien_k74_k75")\
        .update(cleaned_data)\
        .eq("mssv", mssv)\
        .execute()
    
    verify_query = supabase.table("doan_vien_k74_k75")\
        .select("*")\
        .eq("mssv", mssv)\
        .execute()
    
    if not verify_query.data:
        raise Exception(f"Không thể verify update cho MSSV={mssv}")
    
    return verify_query.data[0]


@retry_patient
def bulk_update_students(student_ids: list[str], data: dict):
    if not student_ids:
        raise ValueError("Danh sách sinh viên rỗng")
    
    if not data:
        raise ValueError("Không có dữ liệu để cập nhật")
    
    forbidden = {"mssv", "ho_ten"}
    forbidden_found = [k for k in data.keys() if k in forbidden]
    if forbidden_found:
        raise ValueError(f"Không được bulk update: {', '.join(forbidden_found)}")
    
    cleaned_data = {}
    for k, v in data.items():
        if isinstance(v, bool):
            cleaned_data[k] = v
        elif isinstance(v, str):
            cleaned_data[k] = v.strip()
        elif isinstance(v, (int, float)):
            cleaned_data[k] = v
    
    if not cleaned_data:
        raise ValueError("Không có dữ liệu hợp lệ")

    success_count = 0
    errors = []
    
    for mssv in student_ids:
        try:
            supabase.table("doan_vien_k74_k75")\
                .update(cleaned_data)\
                .eq("mssv", mssv)\
                .execute()
            
            verify = supabase.table("doan_vien_k74_k75")\
                .select("mssv")\
                .eq("mssv", mssv)\
                .execute()
            
            if verify.data:
                success_count += 1
            else:
                errors.append(f"MSSV {mssv}: Không verify được")
                
        except Exception as e:
            error_msg = f"MSSV {mssv}: {str(e)}"
            errors.append(error_msg)
    
    if errors:
        if success_count == 0:
            raise Exception(f"Thất bại hoàn toàn:\n" + "\n".join(errors[:5]))
        else:
            error_summary = "\n".join(errors[:3])
            if len(errors) > 3:
                error_summary += f"\n... và {len(errors) - 3} lỗi khác"
            raise Exception(
                f"Thành công {success_count}/{len(student_ids)}\n"
                f"Lỗi:\n{error_summary}"
            )
    
    return success_count


@retry_critical
def delete_student(mssv: str) -> bool:
    if not mssv:
        raise ValueError("MSSV không được rỗng")
    
    check_query = supabase.table("doan_vien_k74_k75")\
        .select("mssv, ho_ten")\
        .eq("mssv", mssv)\
        .execute()
    
    if not check_query.data:
        raise ValueError(f"Không tìm thấy sinh viên MSSV={mssv}")
    
    supabase.table("doan_vien_k74_k75")\
        .delete()\
        .eq("mssv", mssv)\
        .execute()
    
    return True


@retry_critical
def bulk_delete_students(student_ids: list[str]) -> tuple[int, list[str]]:
    if not student_ids:
        raise ValueError("Danh sách rỗng")
    
    success_count = 0
    errors = []
    
    for mssv in student_ids:
        try:
            check_query = supabase.table("doan_vien_k74_k75")\
                .select("mssv, ho_ten")\
                .eq("mssv", mssv)\
                .execute()
            
            if not check_query.data:
                errors.append(f"MSSV {mssv}: Không tồn tại")
                continue
            
            supabase.table("doan_vien_k74_k75")\
                .delete()\
                .eq("mssv", mssv)\
                .execute()
            
            success_count += 1
            
        except Exception as e:
            error_msg = f"MSSV {mssv}: {str(e)}"
            errors.append(error_msg)
    
    if errors and success_count == 0:
        raise Exception("Xóa thất bại hoàn toàn:\n" + "\n".join(errors[:5]))
    
    return success_count, errors