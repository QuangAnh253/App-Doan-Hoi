# services/sync_google_sheet.py
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from core.supabase_client import supabase
from core.db_retry import retry_standard, retry_patient
from datetime import datetime, timedelta
from typing import Tuple, List, Dict, Optional
import re


SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']
CREDENTIALS_FILE = 'credentials.json'
SHEET_ID = '1nnFBZkEYtnhvQuiKDr94__hRNaNIb3JsAXyFqJTl8WE'

# Cấu trúc: Cột B=Thứ 2, C=Thứ 3, D=Thứ 4, E=Thứ 5, F=Thứ 6
RANGE_SANG = 'B6:F14'
RANGE_CHIEU = 'B17:F25'


def parse_cell_value(raw_value: str) -> Tuple[str, Optional[str], bool]:
    if not raw_value or str(raw_value).strip() == "":
        return ("", None, False)
    
    raw_value = str(raw_value).strip()
    
    separators = [' - ', ' -', '- ', '-', ' _ ', ' _', '_ ', '_']
    
    for sep in separators:
        if sep in raw_value:
            parts = raw_value.split(sep, 1)
            ten = parts[0].strip()
            sdt_part = parts[1].strip() if len(parts) > 1 else ""
            
            sdt_clean = re.sub(r'\D', '', sdt_part)
            
            if sdt_clean and 9 <= len(sdt_clean) <= 11:
                return (ten, sdt_clean, True)
            
            if ten:
                return (ten, None, True)
    
    match = re.search(r'^(.*?)\s+(\d{9,11})$', raw_value)
    if match:
        ten = match.group(1).strip()
        ten = re.sub(r'[-_]+$', '', ten).strip()
        sdt = match.group(2).strip()
        return (ten, sdt, True)
    
    return (raw_value, None, True)


def normalize_name(name: str) -> str:
    return re.sub(r'\s+', ' ', name.strip().lower())


@retry_standard
def find_can_bo_by_name(ho_ten: str) -> Optional[str]:
    if not ho_ten:
        return None
    
    ho_ten_normalized = normalize_name(ho_ten)
    
    try:
        result = supabase.table('can_bo_cap_truong')\
            .select('id, ho_ten')\
            .eq('trang_thai', 'Đang hoạt động')\
            .execute()
        
        if result.data:
            for can_bo in result.data:
                if normalize_name(can_bo['ho_ten']) == ho_ten_normalized:
                    return can_bo['id']
    except Exception:
        pass
    
    try:
        result = supabase.rpc('tim_can_bo_theo_ten', {'search_name': ho_ten_normalized}).execute()
        if result.data:
            return result.data
    except Exception:
        pass
    
    return None


def get_cell_address(col_idx: int, row_idx: int, ca_truc: str) -> str:
    col_letter = chr(ord('C') + col_idx)
    
    if ca_truc == 'Sáng':
        row_number = 5 + row_idx
    else:
        row_number = 11 + row_idx
    
    return f"{col_letter}{row_number}"


def get_monday_of_week(date: datetime = None) -> datetime:
    if date is None:
        date = datetime.now()
    
    days_since_monday = date.weekday()
    monday = date - timedelta(days=days_since_monday)
    
    return monday.replace(hour=0, minute=0, second=0, microsecond=0)


@retry_patient
def sync_one_range(
    service,
    range_name: str,
    ca_truc: str,
    week_start: datetime
) -> Tuple[int, int, List[str]]:
    try:
        result = service.spreadsheets().values().get(
            spreadsheetId=SHEET_ID,
            range=range_name
        ).execute()
        
        values = result.get('values', [])
        
        success_count = 0
        error_count = 0
        errors = []
        
        print(f"\n=== Sync {ca_truc} ===")
        print(f"Số hàng: {len(values)}")
        print(f"Tuần bắt đầu: {week_start.date()}")
        
        for row_idx, row in enumerate(values):
            
            for col_idx, cell_value in enumerate(row):
                
                if col_idx > 4:
                    continue

                ngay_truc = week_start + timedelta(days=col_idx)
                
                if not cell_value or str(cell_value).strip() == "":
                    continue
                
                cell_addr = get_cell_address(col_idx, row_idx, ca_truc)
                cell_str_val = str(cell_value)
                
                print(f"\n Cell {cell_addr} ({ngay_truc.strftime('%d/%m/%Y')}): '{cell_str_val}'")
                
                try:
                    ho_ten, sdt, is_valid = parse_cell_value(cell_str_val)
                    
                    print(f"  → Parsed: tên='{ho_ten}', sđt='{sdt}', valid={is_valid}")
                    
                    if not is_valid or not ho_ten:
                        error_msg = f"Parse thất bại hoặc không có tên"
                        print(f"{error_msg}")
                        error_count += 1
                        errors.append(f"{cell_addr} ({ngay_truc.strftime('%d/%m')}): {error_msg}")
                        continue
                    
                    can_bo_id = find_can_bo_by_name(ho_ten)
                    
                    if can_bo_id:
                        print(f"Tìm thấy cán bộ ID: {can_bo_id}")
                    else:
                        print(f"Không tìm thấy cán bộ trong DB")
                    
                    existing = supabase.table('lich_truc')\
                        .select('id, trang_thai')\
                        .eq('ngay_truc', ngay_truc.date().isoformat())\
                        .eq('ca_truc', ca_truc)\
                        .eq('ho_ten', ho_ten)\
                        .limit(1)\
                        .execute()
                    
                    data = {
                        'ngay_truc': ngay_truc.date().isoformat(),
                        'ca_truc': ca_truc,
                        'ho_ten': ho_ten,
                        'sdt': sdt if sdt else "",
                        'can_bo_id': can_bo_id,
                        'nguon': 'Google Sheet',
                        'google_sheet_cell': cell_addr,
                        'raw_value': cell_str_val,
                        'updated_at': datetime.now().isoformat()
                    }
                    
                    if existing.data:
                        record = existing.data[0]
                        
                        if record['trang_thai'] in ['Đã đăng ký']:
                            supabase.table('lich_truc')\
                                .update(data)\
                                .eq('id', record['id'])\
                                .execute()
                            print(f"Updated existing record (ID: {record['id']})")
                        else:
                            print(f"Skip: Trạng thái '{record['trang_thai']}' không cho phép update")
                    else:
                        data['trang_thai'] = 'Đã đăng ký'
                        data['created_at'] = datetime.now().isoformat()
                        supabase.table('lich_truc').insert(data).execute()
                        print(f"Inserted new record")
                    
                    success_count += 1
                
                except Exception as e:
                    error_msg = str(e)
                    print(f"Error: {error_msg}")
                    error_count += 1
                    errors.append(f"{cell_addr} ({ngay_truc.strftime('%d/%m')}): {error_msg}")
        
        print(f"\nKết quả {ca_truc}: {success_count} thành công, {error_count} lỗi")
        return (success_count, error_count, errors)
    
    except Exception as e:
        error_msg = f"Lỗi đọc range {range_name}: {str(e)}"
        print(f"{error_msg}")
        return (0, 1, [error_msg])


@retry_patient
def sync_full_week(week_start: datetime = None) -> Dict:
    start_time = datetime.now()
    
    if week_start is None:
        week_start = get_monday_of_week()
    
    print(f"\n{'='*60}")
    print(f"BẮT ĐẦU ĐỒNG BỘ TUẦN {week_start.date()}")
    print(f"{'='*60}")
    
    try:
        # Khởi tạo Google Sheets API
        creds = Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=SCOPES)
        service = build('sheets', 'v4', credentials=creds)
        
        all_errors = []
        
        # 1. Sync Ca Sáng (C5:G9)
        print(f"\nĐang sync ca SÁNG...")
        success_sang, error_sang, errors_sang = sync_one_range(
            service, RANGE_SANG, "Sáng", week_start
        )
        all_errors.extend([f"[Sáng] {e}" for e in errors_sang])
        
        # 2. Sync Ca Chiều (C11:G15)
        print(f"\nĐang sync ca CHIỀU...")
        success_chieu, error_chieu, errors_chieu = sync_one_range(
            service, RANGE_CHIEU, "Chiều", week_start
        )
        all_errors.extend([f"[Chiều] {e}" for e in errors_chieu])
        
        # Tính toán tổng kết
        total_success = success_sang + success_chieu
        total_errors = error_sang + error_chieu
        duration = (datetime.now() - start_time).total_seconds()
        
        print(f"\n{'='*60}")
        print(f"KẾT QUẢ TỔNG HỢP:")
        print(f"Thành công: {total_success}")
        print(f"Lỗi: {total_errors}")
        print(f"Thời gian: {duration:.2f}s")
        print(f"{'='*60}\n")
        
        # ✅ Log vào database (không throw error nếu fail)
        try:
            supabase.table('google_sheet_sync_log').insert({
                'sheet_id': SHEET_ID,
                'sheet_name': f'Tuần {week_start.date()}',
                'range_sync': f'{RANGE_SANG}, {RANGE_CHIEU}',
                'so_dong_thanh_cong': total_success,
                'so_dong_loi': total_errors,
                'danh_sach_loi': str(all_errors)[:1000] if all_errors else None,
                'trang_thai': 'Success' if total_errors == 0 else ('Partial' if total_success > 0 else 'Failed'),
                'bat_dau': start_time.isoformat(),
                'ket_thuc': datetime.now().isoformat(),
                'thoi_gian_xu_ly': int(duration),
                'log_chi_tiet': f'Sáng: {success_sang}/{error_sang}, Chiều: {success_chieu}/{error_chieu}'
            }).execute()
            print("✅ Đã log kết quả vào database")
        except Exception as log_error:
            print(f"⚠️  Không thể log vào DB: {log_error}")
        
        return {
            'success': total_errors == 0,
            'sang': {'success': success_sang, 'errors': error_sang},
            'chieu': {'success': success_chieu, 'errors': error_chieu},
            'total_success': total_success,
            'total_errors': total_errors,
            'error_details': all_errors,  # ✅ Đảm bảo có field này
            'duration': duration
        }
    
    except Exception as e:
        error_msg = str(e)
        duration = (datetime.now() - start_time).total_seconds()
        
        print(f"\n{'='*60}")
        print(f"LỖI NGHIÊM TRỌNG: {error_msg}")
        print(f"{'='*60}\n")
        
        return {
            'success': False,
            'sang': {'success': 0, 'errors': 0},
            'chieu': {'success': 0, 'errors': 0},
            'total_success': 0,
            'total_errors': 1,
            'error_details': [f"Lỗi nghiêm trọng: {error_msg}"],
            'duration': duration
        }


@retry_patient
def sync_specific_week(year: int, month: int, day: int) -> Dict:
    """
    Sync tuần cụ thể (chỉ định ngày Thứ 2)
    
    Args:
        year: Năm
        month: Tháng
        day: Ngày (phải là Thứ 2)
    
    Returns:
        Dict: Kết quả sync (giống sync_full_week)
    
    Raises:
        ValueError: Nếu ngày không phải Thứ 2
    """
    week_start = datetime(year, month, day)
    
    if week_start.weekday() != 0:
        raise ValueError(f"Ngày {week_start.date()} không phải Thứ 2! (weekday={week_start.weekday()})")
    
    return sync_full_week(week_start)