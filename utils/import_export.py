# utils/import_export.py - FIXED: Date format conversion
import pandas as pd
from io import BytesIO
from datetime import datetime
from typing import Tuple, List
from core.db_retry import retry_standard, retry_patient

# ✅ FIXED: Import đúng cách để tránh circular import
def get_student_by_mssv(mssv: str) -> dict | None:
    """Lazy import để tránh circular dependency"""
    from services.students_service import get_student_by_mssv as _get
    return _get(mssv)

def get_students_list(limit: int = 100, offset: int = 0) -> list[dict]:
    """Lazy import để tránh circular dependency"""
    from services.students_service import get_students
    return get_students(limit, offset)

def get_supabase():
    """Lazy import Supabase client"""
    from core.supabase_client import supabase
    return supabase


# ===================== DATE CONVERSION =====================
def convert_date_to_db_format(date_str: str) -> str:
    """
    Convert date từ nhiều format sang YYYY-MM-DD
    
    Hỗ trợ:
    - dd/mm/yyyy (Excel VN)
    - dd-mm-yyyy
    - yyyy-mm-dd (DB format)
    - Excel datetime object
    """
    if not date_str or pd.isna(date_str):
        return ""
    
    # Nếu là string rỗng
    if isinstance(date_str, str) and not date_str.strip():
        return ""
    
    # Nếu đã là datetime object từ pandas
    if isinstance(date_str, (pd.Timestamp, datetime)):
        return date_str.strftime("%Y-%m-%d")
    
    # Convert string
    date_str = str(date_str).strip()
    
    # Đã đúng format YYYY-MM-DD
    if len(date_str) == 10 and date_str[4] == '-' and date_str[7] == '-':
        return date_str
    
    # Try parse dd/mm/yyyy
    try:
        dt = datetime.strptime(date_str, "%d/%m/%Y")
        return dt.strftime("%Y-%m-%d")
    except ValueError:
        pass
    
    # Try parse dd-mm-yyyy
    try:
        dt = datetime.strptime(date_str, "%d-%m-%Y")
        return dt.strftime("%Y-%m-%d")
    except ValueError:
        pass
    
    # Try parse yyyy/mm/dd
    try:
        dt = datetime.strptime(date_str, "%Y/%m/%d")
        return dt.strftime("%Y-%m-%d")
    except ValueError:
        pass
    
    # Không parse được - return empty
    print(f"⚠️ [DATE] Cannot parse: {date_str}")
    return ""


# ===================== IMPORT EXCEL =====================
@retry_patient
def import_students(
    file_bytes: bytes, 
    user_id: str = None, 
    user_email: str = None
) -> Tuple[int, List[str]]:
    """
    Import sinh viên từ file Excel
    
    Args:
        file_bytes: Nội dung file Excel dạng bytes
        user_id: ID người thực hiện import (để log)
        user_email: Email người thực hiện import (để log)
    
    Returns:
        (số_lượng_import_thành_công, danh_sách_lỗi)
    
    Excel format yêu cầu:
        - MSSV (bắt buộc)
        - ho_ten (bắt buộc)
        - ngay_sinh (dd/mm/yyyy) - tự động convert sang YYYY-MM-DD
        - noi_sinh
        - lop, khoa
        - trang_thai_so
        - vi_tri_luu_so
        - da_nop_doan_phi (Có/Không hoặc TRUE/FALSE)
        - da_nop_hoi_phi (Có/Không hoặc TRUE/FALSE)
        - ghi_chu
    """
    errors = []
    success_count = 0
    supabase = get_supabase()
    
    try:
        # Đọc Excel
        df = pd.read_excel(BytesIO(file_bytes), sheet_name=0)
        
        # Clean column names
        df.columns = df.columns.str.strip().str.lower()
        
        # Validate required columns
        required_cols = ["mssv", "ho_ten"]
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            raise ValueError(f"Thiếu các cột bắt buộc: {', '.join(missing_cols)}")
        
        print(f"📂 [IMPORT] Processing {len(df)} rows...")
        
        # Process each row
        for idx, row in df.iterrows():
            row_num = idx + 2  # Excel row number (header = 1, data starts at 2)
            
            try:
                # Validate MSSV
                mssv = str(row.get("mssv", "")).strip()
                if not mssv or pd.isna(row.get("mssv")):
                    errors.append(f"Dòng {row_num}: MSSV rỗng")
                    continue
                
                # Validate họ tên
                ho_ten = str(row.get("ho_ten", "")).strip()
                if not ho_ten or pd.isna(row.get("ho_ten")):
                    errors.append(f"Dòng {row_num} (MSSV {mssv}): Họ tên rỗng")
                    continue
                
                # ✅ Convert ngày sinh sang DB format
                ngay_sinh_raw = row.get("ngay_sinh", "")
                ngay_sinh = convert_date_to_db_format(ngay_sinh_raw)
                
                # Build data dict
                data = {
                    "mssv": mssv,
                    "ho_ten": ho_ten,
                    "ngay_sinh": ngay_sinh,  # ✅ Đã convert sang YYYY-MM-DD
                    "noi_sinh": str(row.get("noi_sinh", "")).strip() if not pd.isna(row.get("noi_sinh")) else "",
                    "lop": str(row.get("lop", "")).strip() if not pd.isna(row.get("lop")) else "",
                    "khoa": str(row.get("khoa", "")).strip() if not pd.isna(row.get("khoa")) else "",
                    "trang_thai_so": str(row.get("trang_thai_so", "Chưa tiếp nhận")).strip(),
                    "vi_tri_luu_so": str(row.get("vi_tri_luu_so", "")).strip() if not pd.isna(row.get("vi_tri_luu_so")) else "",
                    "ghi_chu": str(row.get("ghi_chu", "")).strip() if not pd.isna(row.get("ghi_chu")) else "",
                }
                
                # Parse boolean fields
                data["da_nop_doan_phi"] = parse_boolean(row.get("da_nop_doan_phi", False))
                data["da_nop_hoi_phi"] = parse_boolean(row.get("da_nop_hoi_phi", False))
                
                # Check if student exists
                existing = get_student_by_mssv(mssv)
                
                if existing:
                    # Update existing student (exclude mssv and ho_ten)
                    update_data = {k: v for k, v in data.items() if k not in ["mssv", "ho_ten"]}
                    
                    supabase.table("doan_vien_k74_k75")\
                        .update(update_data)\
                        .eq("mssv", mssv)\
                        .execute()
                    
                    print(f"✅ [IMPORT] Updated: {mssv}")
                else:
                    # Insert new student
                    supabase.table("doan_vien_k74_k75")\
                        .insert(data)\
                        .execute()
                    
                    print(f"✅ [IMPORT] Inserted: {mssv}")
                
                success_count += 1
                
            except Exception as e:
                error_msg = f"Dòng {row_num} (MSSV {mssv if 'mssv' in locals() else '?'}): {str(e)}"
                errors.append(error_msg)
                print(f"❌ [IMPORT] {error_msg}")
        
        # Log import activity
        if user_id or user_email:
            try:
                log_import_activity(user_id, user_email, success_count, len(errors))
            except Exception as e:
                print(f"⚠️ [IMPORT] Cannot log activity: {e}")
        
        print(f"✅ [IMPORT] Done: {success_count} success, {len(errors)} errors")
        return success_count, errors
        
    except Exception as e:
        print(f"❌ [IMPORT] Fatal error: {e}")
        raise Exception(f"Lỗi đọc file Excel: {str(e)}")


def parse_boolean(value) -> bool:
    """Parse boolean từ nhiều format khác nhau"""
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


# ===================== EXPORT EXCEL =====================
@retry_standard
def export_students(
    selected_mssv: List[str] = None,
    user_id: str = None,
    user_email: str = None
) -> bytes:
    """
    Export sinh viên ra Excel
    
    Args:
        selected_mssv: Danh sách MSSV cần export (None = export tất cả)
        user_id: ID người thực hiện export (để log)
        user_email: Email người thực hiện export (để log)
    
    Returns:
        bytes: Nội dung file Excel
    """
    try:
        print(f"💾 [EXPORT] Starting... (selected: {len(selected_mssv) if selected_mssv else 'all'})")
        
        # Fetch data
        if selected_mssv:
            # Export selected students
            data = []
            for mssv in selected_mssv:
                student = get_student_by_mssv(mssv)
                if student:
                    data.append(student)
        else:
            # Export all students (in batches to avoid memory issues)
            data = []
            offset = 0
            batch_size = 1000
            
            while True:
                batch = get_students_list(limit=batch_size, offset=offset)
                if not batch:
                    break
                data.extend(batch)
                offset += batch_size
                
                if len(batch) < batch_size:
                    break
        
        if not data:
            raise ValueError("Không có dữ liệu để export")
        
        print(f"💾 [EXPORT] Fetched {len(data)} records")
        
        # Convert to DataFrame
        df = pd.DataFrame(data)
        
        # ✅ Convert ngày sinh về format dd/mm/yyyy cho Excel
        if "ngay_sinh" in df.columns:
            def format_date_for_excel(date_str):
                if not date_str or pd.isna(date_str):
                    return ""
                try:
                    # Parse YYYY-MM-DD
                    dt = datetime.strptime(str(date_str).strip()[:10], "%Y-%m-%d")
                    return dt.strftime("%d/%m/%Y")
                except:
                    return str(date_str)
            
            df["ngay_sinh"] = df["ngay_sinh"].apply(format_date_for_excel)
        
        # Reorder and rename columns
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
        
        # Select and rename columns
        df = df[[col for col in column_mapping.keys() if col in df.columns]]
        df.rename(columns=column_mapping, inplace=True)
        
        # Format boolean columns
        for col in ["Đã nộp đoàn phí", "Đã nộp hội phí"]:
            if col in df.columns:
                df[col] = df[col].map(lambda x: "Có" if x else "Không")
        
        # Write to Excel
        output = BytesIO()
        
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Sinh viên')
            
            # Auto-adjust column width
            worksheet = writer.sheets['Sinh viên']
            for idx, col in enumerate(df.columns, 1):
                max_length = max(
                    df[col].astype(str).map(len).max(),
                    len(str(col))
                )
                worksheet.column_dimensions[chr(64 + idx)].width = min(max_length + 2, 50)
        
        # Log export activity
        if user_id or user_email:
            try:
                log_export_activity(user_id, user_email, len(data))
            except Exception as e:
                print(f"⚠️ [EXPORT] Cannot log activity: {e}")
        
        print(f"✅ [EXPORT] Done: {len(data)} records")
        return output.getvalue()
        
    except Exception as e:
        print(f"❌ [EXPORT] Error: {e}")
        raise Exception(f"Lỗi export Excel: {str(e)}")


# ===================== LOGGING (OPTIONAL) =====================
def log_import_activity(user_id: str, user_email: str, success_count: int, error_count: int):
    """Log import activity to audit table"""
    try:
        supabase = get_supabase()
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
    except Exception as e:
        print(f"⚠️ [LOG] Cannot log import: {e}")


def log_export_activity(user_id: str, user_email: str, record_count: int):
    """Log export activity to audit table"""
    try:
        supabase = get_supabase()
        supabase.table("activity_logs").insert({
            "user_id": user_id,
            "user_email": user_email,
            "action": "EXPORT_STUDENTS",
            "details": {
                "record_count": record_count,
            },
            "timestamp": datetime.now().isoformat(),
        }).execute()
    except Exception as e:
        print(f"⚠️ [LOG] Cannot log export: {e}")


# ===================== VALIDATION HELPERS =====================
@retry_standard
def validate_import_file(file_bytes: bytes) -> Tuple[bool, str]:
    """
    Validate file Excel trước khi import
    
    Returns:
        (is_valid, error_message)
    """
    try:
        df = pd.read_excel(BytesIO(file_bytes), sheet_name=0)
        
        # Check columns
        df.columns = df.columns.str.strip().str.lower()
        required_cols = ["mssv", "ho_ten"]
        missing_cols = [col for col in required_cols if col not in df.columns]
        
        if missing_cols:
            return False, f"Thiếu các cột bắt buộc: {', '.join(missing_cols)}"
        
        # Check empty
        if len(df) == 0:
            return False, "File Excel không có dữ liệu"
        
        # Check MSSV format
        invalid_mssv = []
        for idx, row in df.head(10).iterrows():  # Check first 10 rows
            mssv = str(row.get("mssv", "")).strip()
            if not mssv or not mssv.isdigit():
                invalid_mssv.append(f"Dòng {idx + 2}: MSSV không hợp lệ")
        
        if invalid_mssv:
            return False, "\n".join(invalid_mssv[:3])
        
        return True, ""
        
    except Exception as e:
        return False, f"Lỗi đọc file: {str(e)}"