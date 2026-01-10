# utils/can_bo_import_export.py - Import/Export Excel cho cán bộ BVP/BCH
import pandas as pd
from io import BytesIO
from datetime import datetime
from typing import Tuple, List

def get_can_bo_by_id(can_bo_id: str) -> dict | None:
    """Lazy import để tránh circular dependency"""
    from services.noi_bo_service import get_can_bo_by_id as _get
    return _get(can_bo_id)

def get_can_bo_list(limit: int = 100, offset: int = 0) -> list[dict]:
    """Lazy import để tránh circular dependency"""
    from services.noi_bo_service import fetch_can_bo_bvp_bch
    return fetch_can_bo_bvp_bch(page_size=limit)

def get_supabase():
    """Lazy import Supabase client"""
    from core.supabase_client import supabase
    return supabase


# ===================== IMPORT EXCEL =====================
def import_can_bo(
    file_bytes: bytes, 
    user_id: str = None, 
    user_email: str = None
) -> Tuple[int, List[str]]:
    """
    Import cán bộ từ file Excel
    
    Args:
        file_bytes: Nội dung file Excel dạng bytes
        user_id: ID người thực hiện import (để log)
        user_email: Email người thực hiện import (để log)
    
    Returns:
        (số_lượng_import_thành_công, danh_sách_lỗi)
    
    Excel format yêu cầu:
        - ho_ten (bắt buộc)
        - chuc_vu (bắt buộc)
        - loai_can_bo (bắt buộc): Ban Văn phòng | BCH Đoàn | BCH Hội | CTV Ban Văn phòng
        - mssv
        - khoa_hoc
        - sdt
        - email
        - nhiem_ky
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
        required_cols = ["ho_ten", "chuc_vu", "loai_can_bo"]
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            raise ValueError(f"Thiếu các cột bắt buộc: {', '.join(missing_cols)}")
        
        print(f"📂 [IMPORT_CB] Processing {len(df)} rows...")
        
        # Process each row
        for idx, row in df.iterrows():
            row_num = idx + 2  # Excel row number (header = 1, data starts at 2)
            
            try:
                # Validate họ tên
                ho_ten = str(row.get("ho_ten", "")).strip()
                if not ho_ten or pd.isna(row.get("ho_ten")):
                    errors.append(f"Dòng {row_num}: Họ tên rỗng")
                    continue
                
                # Validate chức vụ
                chuc_vu = str(row.get("chuc_vu", "")).strip()
                if not chuc_vu or pd.isna(row.get("chuc_vu")):
                    errors.append(f"Dòng {row_num} ({ho_ten}): Chức vụ rỗng")
                    continue
                
                # Validate loại cán bộ
                loai_can_bo = str(row.get("loai_can_bo", "")).strip()
                valid_loai = ["Ban Văn phòng", "BCH Đoàn", "BCH Hội", "CTV Ban Văn phòng"]
                if loai_can_bo not in valid_loai:
                    errors.append(f"Dòng {row_num} ({ho_ten}): Loại cán bộ không hợp lệ")
                    continue
                
                # Build data dict
                data = {
                    "ho_ten": ho_ten,
                    "chuc_vu": chuc_vu,
                    "loai_can_bo": loai_can_bo,
                    "mssv": str(row.get("mssv", "")).strip() if not pd.isna(row.get("mssv")) else "",
                    "khoa_hoc": str(row.get("khoa_hoc", "")).strip() if not pd.isna(row.get("khoa_hoc")) else "",
                    "sdt": str(row.get("sdt", "")).strip() if not pd.isna(row.get("sdt")) else "",
                    "email": str(row.get("email", "")).strip() if not pd.isna(row.get("email")) else "",
                    "nhiem_ky": str(row.get("nhiem_ky", "")).strip() if not pd.isna(row.get("nhiem_ky")) else "",
                    "trang_thai": "Đang hoạt động",
                    "created_at": datetime.now().isoformat(),
                }
                
                # Check if exists by (ho_ten + loai_can_bo + chuc_vu)
                existing = supabase.table("can_bo_cap_truong")\
                    .select("id")\
                    .eq("ho_ten", ho_ten)\
                    .eq("loai_can_bo", loai_can_bo)\
                    .eq("chuc_vu", chuc_vu)\
                    .eq("trang_thai", "Đang hoạt động")\
                    .execute()
                
                if existing.data:
                    # Update existing
                    update_data = {k: v for k, v in data.items() if k not in ["ho_ten", "created_at"]}
                    update_data["updated_at"] = datetime.now().isoformat()
                    
                    supabase.table("can_bo_cap_truong")\
                        .update(update_data)\
                        .eq("id", existing.data[0]["id"])\
                        .execute()
                    
                    print(f"✅ [IMPORT_CB] Updated: {ho_ten}")
                else:
                    # Insert new
                    supabase.table("can_bo_cap_truong")\
                        .insert(data)\
                        .execute()
                    
                    print(f"✅ [IMPORT_CB] Inserted: {ho_ten}")
                
                success_count += 1
                
            except Exception as e:
                error_msg = f"Dòng {row_num} ({ho_ten if 'ho_ten' in locals() else '?'}): {str(e)}"
                errors.append(error_msg)
                print(f"❌ [IMPORT_CB] {error_msg}")
        
        # Log import activity
        if user_id or user_email:
            try:
                log_import_activity(user_id, user_email, success_count, len(errors))
            except Exception as e:
                print(f"⚠️ [IMPORT_CB] Cannot log activity: {e}")
        
        print(f"✅ [IMPORT_CB] Done: {success_count} success, {len(errors)} errors")
        return success_count, errors
        
    except Exception as e:
        print(f"❌ [IMPORT_CB] Fatal error: {e}")
        raise Exception(f"Lỗi đọc file Excel: {str(e)}")


# ===================== EXPORT EXCEL =====================
def export_can_bo(
    selected_ids: List[str] = None,
    user_id: str = None,
    user_email: str = None
) -> bytes:
    """
    Export cán bộ ra Excel
    
    Args:
        selected_ids: Danh sách ID cần export (None = export tất cả)
        user_id: ID người thực hiện export (để log)
        user_email: Email người thực hiện export (để log)
    
    Returns:
        bytes: Nội dung file Excel
    """
    try:
        print(f"💾 [EXPORT_CB] Starting... (selected: {len(selected_ids) if selected_ids else 'all'})")
        
        supabase = get_supabase()
        
        # Fetch data
        if selected_ids:
            # Export selected
            data = []
            for cb_id in selected_ids:
                result = supabase.table("can_bo_cap_truong")\
                    .select("*")\
                    .eq("id", cb_id)\
                    .execute()
                if result.data:
                    data.append(result.data[0])
        else:
            # Export all active
            result = supabase.table("can_bo_cap_truong")\
                .select("*")\
                .eq("trang_thai", "Đang hoạt động")\
                .order("loai_can_bo")\
                .order("chuc_vu")\
                .execute()
            data = result.data or []
        
        if not data:
            raise ValueError("Không có dữ liệu để export")
        
        print(f"💾 [EXPORT_CB] Fetched {len(data)} records")
        
        # Convert to DataFrame
        df = pd.DataFrame(data)
        
        # Reorder and rename columns
        column_mapping = {
            "loai_can_bo": "Loại cán bộ",
            "chuc_vu": "Chức vụ",
            "ho_ten": "Họ tên",
            "mssv": "MSSV",
            "khoa_hoc": "Khóa",
            "sdt": "SĐT",
            "email": "Email",
            "nhiem_ky": "Nhiệm kỳ",
        }
        
        # Select and rename columns
        available_cols = [col for col in column_mapping.keys() if col in df.columns]
        df = df[available_cols]
        df.rename(columns=column_mapping, inplace=True)
        
        # Write to Excel
        output = BytesIO()
        
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Cán bộ')
            
            # Auto-adjust column width
            worksheet = writer.sheets['Cán bộ']
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
                print(f"⚠️ [EXPORT_CB] Cannot log activity: {e}")
        
        print(f"✅ [EXPORT_CB] Done: {len(data)} records")
        return output.getvalue()
        
    except Exception as e:
        print(f"❌ [EXPORT_CB] Error: {e}")
        raise Exception(f"Lỗi export Excel: {str(e)}")


# ===================== LOGGING =====================
def log_import_activity(user_id: str, user_email: str, success_count: int, error_count: int):
    """Log import activity to audit table"""
    try:
        supabase = get_supabase()
        supabase.table("activity_logs").insert({
            "user_id": user_id,
            "user_email": user_email,
            "action": "IMPORT_CAN_BO",
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
            "action": "EXPORT_CAN_BO",
            "details": {
                "record_count": record_count,
            },
            "timestamp": datetime.now().isoformat(),
        }).execute()
    except Exception as e:
        print(f"⚠️ [LOG] Cannot log export: {e}")


# ===================== VALIDATION HELPERS =====================
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
        required_cols = ["ho_ten", "chuc_vu", "loai_can_bo"]
        missing_cols = [col for col in required_cols if col not in df.columns]
        
        if missing_cols:
            return False, f"Thiếu các cột bắt buộc: {', '.join(missing_cols)}"
        
        # Check empty
        if len(df) == 0:
            return False, "File Excel không có dữ liệu"
        
        # Check loại cán bộ hợp lệ
        valid_loai = ["Ban Văn phòng", "BCH Đoàn", "BCH Hội", "CTV Ban Văn phòng"]
        invalid_loai = []
        
        for idx, row in df.head(10).iterrows():
            loai = str(row.get("loai_can_bo", "")).strip()
            if loai and loai not in valid_loai:
                invalid_loai.append(f"Dòng {idx + 2}: Loại cán bộ '{loai}' không hợp lệ")
        
        if invalid_loai:
            return False, "\n".join(invalid_loai[:3])
        
        return True, ""
        
    except Exception as e:
        return False, f"Lỗi đọc file: {str(e)}"
