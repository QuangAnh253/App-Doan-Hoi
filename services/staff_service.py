# services/staff_service.py
from core.supabase_client import supabase
from core.db_retry import retry_standard, retry_patient, retry_critical


@retry_standard
def fetch_staff_with_filters(
    search: str = "",
    lop: str = "",
    khoa: str = "",
    page: int = 1,
    page_size: int = 100
) -> list[dict]:
    query = supabase.table("can_bo_lop").select(
        "id, csdt, khoa_vien, chi_doan, chuc_vu, ho_ten, mssv, "
        "ngay_sinh, sdt, email, ghi_chu"
    )
    
    if search:
        search_normalized = search.strip()
        if any(char.isdigit() for char in search_normalized):
            query = query.ilike("chi_doan", f"%{search_normalized}%")
        else:
            query = query.ilike("ho_ten", f"%{search_normalized}%")
    
    if lop:
        query = query.ilike("chi_doan", lop.strip())
    
    if khoa:
        query = query.ilike("khoa_vien", f"%{khoa.strip()}%")
    
    start = (page - 1) * page_size
    end = start + page_size - 1
    
    res = query.range(start, end).execute()
    return res.data or []


@retry_standard
def count_staff_with_filters(search: str = "", lop: str = "", khoa: str = "") -> int:
    query = supabase.table("can_bo_lop").select("id", count="exact")
    
    if search:
        search_normalized = search.strip()
        if any(char.isdigit() for char in search_normalized):
            query = query.ilike("chi_doan", f"%{search_normalized}%")
        else:
            query = query.ilike("ho_ten", f"%{search_normalized}%")
    
    if lop:
        query = query.ilike("chi_doan", lop.strip())
    
    if khoa:
        query = query.ilike("khoa_vien", f"%{khoa.strip()}%")
    
    res = query.execute()
    return res.count or 0


@retry_standard
def fetch_staff(search: str = "", page: int = 1, page_size: int = 100) -> list[dict]:
    return fetch_staff_with_filters(search=search, page=page, page_size=page_size)


@retry_standard
def count_staff(search: str = "") -> int:
    return count_staff_with_filters(search=search)


@retry_patient
def update_staff(staff_id: str, data: dict):
    if not staff_id:
        raise ValueError("ID cán bộ không được rỗng")
    
    if not data:
        raise ValueError("Không có dữ liệu để cập nhật")
    
    cleaned_data = {}
    for k, v in data.items():
        if isinstance(v, bool):
            cleaned_data[k] = v
        elif isinstance(v, str) and v.strip():
            cleaned_data[k] = v.strip()
        elif isinstance(v, (int, float)):
            cleaned_data[k] = v
    
    if not cleaned_data:
        raise ValueError("Không có dữ liệu hợp lệ để cập nhật")
    
    res = supabase.table("can_bo_lop")\
        .update(cleaned_data)\
        .eq("id", staff_id)\
        .execute()
    
    if not res.data:
        raise Exception(f"Không tìm thấy cán bộ với ID={staff_id}")
    
    return res.data[0]


@retry_patient
def bulk_update_staff(staff_ids: list[str], data: dict):
    if not staff_ids:
        raise ValueError("Danh sách cán bộ rỗng")
    
    if not data:
        raise ValueError("Không có dữ liệu để cập nhật")
    
    cleaned_data = {}
    for k, v in data.items():
        if isinstance(v, bool):
            cleaned_data[k] = v
        elif isinstance(v, str):
            cleaned_data[k] = v.strip()
        elif isinstance(v, (int, float)):
            cleaned_data[k] = v
    
    if not cleaned_data:
        raise ValueError("Không có dữ liệu hợp lệ để cập nhật")
    
    success_count = 0
    errors = []
    
    for staff_id in staff_ids:
        try:
            supabase.table("can_bo_lop")\
                .update(cleaned_data)\
                .eq("id", staff_id)\
                .execute()
            success_count += 1
        except Exception as e:
            errors.append(f"ID {staff_id}: {str(e)}")
    
    if errors:
        if success_count == 0:
            raise Exception(f"Cập nhật thất bại hoàn toàn. Lỗi:\n" + "\n".join(errors[:5]))
        else:
            error_summary = "\n".join(errors[:3])
            if len(errors) > 3:
                error_summary += f"\n... và {len(errors) - 3} lỗi khác"
            raise Exception(
                f"Cập nhật thành công {success_count}/{len(staff_ids)}.\n"
                f"Lỗi:\n{error_summary}"
            )
    
    return success_count


@retry_patient
def create_staff(data: dict):
    required = ["khoa_vien", "chi_doan", "chuc_vu", "ho_ten"]
    for field in required:
        if not data.get(field):
            raise ValueError(f"Thiếu trường bắt buộc: {field}")
    
    res = supabase.table("can_bo_lop").insert(data).execute()
    return res.data[0] if res.data else None


@retry_critical
def delete_staff(staff_id: str):
    if not staff_id:
        raise ValueError("ID cán bộ không được rỗng")
    
    res = supabase.table("can_bo_lop").delete().eq("id", staff_id).execute()
    return True


@retry_standard
def get_staff_by_id(staff_id: str) -> dict | None:
    res = supabase.table("can_bo_lop")\
        .select("*")\
        .eq("id", staff_id)\
        .execute()
    
    return res.data[0] if res.data else None

def export_staff_to_excel(staff_ids: list[str]) -> bytes:
    """Export danh sách cán bộ ra Excel"""
    import pandas as pd
    from io import BytesIO
    
    if not staff_ids:
        raise ValueError("Danh sách cán bộ rỗng")
    
    # Lấy data từ DB
    data = []
    for staff_id in staff_ids:
        staff = get_staff_by_id(staff_id)
        if staff:
            data.append({
                "Khoa/Viện": staff.get("khoa_vien", ""),
                "Lớp": staff.get("chi_doan", ""),
                "Họ tên": staff.get("ho_ten", ""),
                "Chức vụ": staff.get("chuc_vu", ""),
                "MSSV": staff.get("mssv", ""),
                "Ngày sinh": staff.get("ngay_sinh", ""),
                "SĐT": staff.get("sdt", ""),
                "Email": staff.get("email", ""),
                "CSĐT": staff.get("csdt", ""),
                "Ghi chú": staff.get("ghi_chu", ""),
            })
    
    df = pd.DataFrame(data)
    
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Cán bộ lớp')
        
        worksheet = writer.sheets['Cán bộ lớp']
        for idx, col in enumerate(df.columns, 1):
            max_length = max(df[col].astype(str).map(len).max(), len(str(col)))
            col_letter = chr(64 + idx)
            worksheet.column_dimensions[col_letter].width = min(max_length + 3, 40)
    
    return output.getvalue()


def import_staff_from_excel(file_bytes: bytes) -> tuple[int, list[str]]:
    """Import cán bộ từ Excel. Returns (số lượng thành công, danh sách lỗi)"""
    import pandas as pd
    from io import BytesIO
    
    errors = []
    success_count = 0
    
    try:
        df = pd.read_excel(BytesIO(file_bytes))
        
        # Chuẩn hóa tên cột
        df.columns = df.columns.str.strip()
        
        required_cols = ["ho_ten", "chuc_vu", "chi_doan", "khoa_vien"]
        
        for idx, row in df.iterrows():
            try:
                row_num = idx + 2
                
                # Validate required fields
                missing = []
                for col in required_cols:
                    if col not in row or pd.isna(row[col]) or str(row[col]).strip() == "":
                        missing.append(col)
                
                if missing:
                    errors.append(f"Dòng {row_num}: Thiếu {', '.join(missing)}")
                    continue
                
                # Build payload
                payload = {
                    "ho_ten": str(row["ho_ten"]).strip(),
                    "chuc_vu": str(row["chuc_vu"]).strip(),
                    "chi_doan": str(row["chi_doan"]).strip(),
                    "khoa_vien": str(row["khoa_vien"]).strip(),
                }
                
                if "mssv" in row and not pd.isna(row["mssv"]):
                    payload["mssv"] = str(row["mssv"]).strip()
                if "ngay_sinh" in row and not pd.isna(row["ngay_sinh"]):
                    payload["ngay_sinh"] = str(row["ngay_sinh"]).strip()
                if "sdt" in row and not pd.isna(row["sdt"]):
                    payload["sdt"] = str(row["sdt"]).strip()
                if "email" in row and not pd.isna(row["email"]):
                    payload["email"] = str(row["email"]).strip()
                if "csdt" in row and not pd.isna(row["csdt"]):
                    payload["csdt"] = str(row["csdt"]).strip()
                if "ghi_chu" in row and not pd.isna(row["ghi_chu"]):
                    payload["ghi_chu"] = str(row["ghi_chu"]).strip()
                
                create_staff(payload)
                success_count += 1
                
            except Exception as e:
                errors.append(f"Dòng {row_num}: {str(e)}")
        
        return success_count, errors
        
    except Exception as e:
        errors.append(f"Lỗi đọc file: {str(e)}")
        return 0, errors