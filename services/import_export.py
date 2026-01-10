# services/import_export.py
import pandas as pd
from io import BytesIO
from datetime import datetime
from typing import Tuple, List
from services.students_service import get_students, get_student_by_mssv
from core.supabase_client import supabase


def import_students(
    file_bytes: bytes, 
    user_id: str = None, 
    user_email: str = None
) -> Tuple[int, List[str]]:
    errors = []
    success_count = 0
    
    df = pd.read_excel(BytesIO(file_bytes), sheet_name=0)
    
    df.columns = df.columns.str.strip().str.lower()
    
    required_cols = ["mssv", "ho_ten"]
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Thiếu các cột bắt buộc: {', '.join(missing_cols)}")
    
    for idx, row in df.iterrows():
        row_num = idx + 2
        
        try:
            mssv = str(row.get("mssv", "")).strip()
            if not mssv or pd.isna(row.get("mssv")):
                errors.append(f"Dòng {row_num}: MSSV rỗng")
                continue
            
            ho_ten = str(row.get("ho_ten", "")).strip()
            if not ho_ten or pd.isna(row.get("ho_ten")):
                errors.append(f"Dòng {row_num} (MSSV {mssv}): Họ tên rỗng")
                continue
            
            data = {
                "mssv": mssv,
                "ho_ten": ho_ten,
                "lop": str(row.get("lop", "")).strip() if not pd.isna(row.get("lop")) else "",
                "khoa": str(row.get("khoa", "")).strip() if not pd.isna(row.get("khoa")) else "",
                "ngay_sinh": str(row.get("ngay_sinh", "")).strip() if not pd.isna(row.get("ngay_sinh")) else "",
                "noi_sinh": str(row.get("noi_sinh", "")).strip() if not pd.isna(row.get("noi_sinh")) else "",
                "trang_thai_so": str(row.get("trang_thai_so", "Chưa tiếp nhận")).strip(),
                "vi_tri_luu_so": str(row.get("vi_tri_luu_so", "")).strip() if not pd.isna(row.get("vi_tri_luu_so")) else "",
                "ghi_chu": str(row.get("ghi_chu", "")).strip() if not pd.isna(row.get("ghi_chu")) else "",
            }
            
            data["da_nop_doan_phi"] = parse_boolean(row.get("da_nop_doan_phi", False))
            data["da_nop_hoi_phi"] = parse_boolean(row.get("da_nop_hoi_phi", False))
            
            existing = get_student_by_mssv(mssv)
            
            if existing:
                update_data = {k: v for k, v in data.items() if k not in ["mssv", "ho_ten"]}
                
                supabase.table("doan_vien_k74_k75")\
                    .update(update_data)\
                    .eq("mssv", mssv)\
                    .execute()
            else:
                supabase.table("doan_vien_k74_k75")\
                    .insert(data)\
                    .execute()
            
            success_count += 1
            
        except Exception as e:
            error_msg = f"Dòng {row_num} (MSSV {mssv if 'mssv' in locals() else '?'}): {str(e)}"
            errors.append(error_msg)
    
    if user_id or user_email:
        try:
            log_import_activity(user_id, user_email, success_count, len(errors))
        except Exception:
            pass
    
    return success_count, errors


def parse_boolean(value) -> bool:
    if pd.isna(value):
        return False
    
    if isinstance(value, bool):
        return value
    
    if isinstance(value, (int, float)):
        return value > 0
    
    if isinstance(value, str):
        value_lower = value.strip().lower()
        return value_lower in ["true", "yes", "có", "1", "x"]
    
    return False


def export_students(
    selected_mssv: List[str] = None,
    user_id: str = None,
    user_email: str = None
) -> bytes:
    if selected_mssv:
        data = []
        for mssv in selected_mssv:
            student = get_student_by_mssv(mssv)
            if student:
                data.append(student)
    else:
        data = []
        offset = 0
        batch_size = 1000
        
        while True:
            batch = get_students(limit=batch_size, offset=offset)
            if not batch:
                break
            data.extend(batch)
            offset += batch_size
            
            if len(batch) < batch_size:
                break
    
    if not data:
        raise ValueError("Không có dữ liệu để export")
    
    df = pd.DataFrame(data)
    
    column_mapping = {
        "mssv": "MSSV",
        "ho_ten": "Họ tên",
        "ngay_sinh": "Ngày sinh",
        "noi_sinh": "Nơi sinh",
        "lop": "Lớp",
        "khoa": "Khoa",
        "trang_thai_so": "Trạng thái sổ",
        "vi_tri_luu_so": "Vị trí lưu sổ",
        "da_nop_doan_phi": "Đã nộp đoàn phí",
        "da_nop_hoi_phi": "Đã nộp hội phí",
        "ghi_chu": "Ghi chú",
    }
    
    df = df[[col for col in column_mapping.keys() if col in df.columns]]
    df.rename(columns=column_mapping, inplace=True)
    
    for col in ["Đã nộp đoàn phí", "Đã nộp hội phí"]:
        if col in df.columns:
            df[col] = df[col].map(lambda x: "Có" if x else "Không")
    
    output = BytesIO()
    
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Sinh viên')
        
        worksheet = writer.sheets['Sinh viên']
        for idx, col in enumerate(df.columns, 1):
            max_length = max(
                df[col].astype(str).map(len).max(),
                len(str(col))
            )
            worksheet.column_dimensions[chr(64 + idx)].width = min(max_length + 2, 50)
    
    if user_id or user_email:
        try:
            log_export_activity(user_id, user_email, len(data))
        except Exception:
            pass
    
    return output.getvalue()


def log_import_activity(user_id: str, user_email: str, success_count: int, error_count: int):
    try:
        supabase.table("activity_logs").insert({
            "user_id": user_id,
            "user_email": user_email,
            "action": "IMPORT_STUDENTS",
            "details": {
                "success_count": success_count,
                "error_count": error_count,
            },
            "timestamp": datetime.now().isoformat(),
        }).execute()
    except Exception:
        pass


def log_export_activity(user_id: str, user_email: str, record_count: int):
    try:
        supabase.table("activity_logs").insert({
            "user_id": user_id,
            "user_email": user_email,
            "action": "EXPORT_STUDENTS",
            "details": {
                "record_count": record_count,
            },
            "timestamp": datetime.now().isoformat(),
        }).execute()
    except Exception:
        pass


def validate_import_file(file_bytes: bytes) -> Tuple[bool, str]:
    try:
        df = pd.read_excel(BytesIO(file_bytes), sheet_name=0)
        
        df.columns = df.columns.str.strip().str.lower()
        required_cols = ["mssv", "ho_ten"]
        missing_cols = [col for col in required_cols if col not in df.columns]
        
        if missing_cols:
            return False, f"Thiếu các cột bắt buộc: {', '.join(missing_cols)}"
        
        if len(df) == 0:
            return False, "File Excel không có dữ liệu"
        
        invalid_mssv = []
        for idx, row in df.head(10).iterrows():
            mssv = str(row.get("mssv", "")).strip()
            if not mssv or not mssv.isdigit():
                invalid_mssv.append(f"Dòng {idx + 2}: MSSV không hợp lệ")
        
        if invalid_mssv:
            return False, "\n".join(invalid_mssv[:3])
        
        return True, ""
        
    except Exception as e:
        return False, f"Lỗi đọc file: {str(e)}"