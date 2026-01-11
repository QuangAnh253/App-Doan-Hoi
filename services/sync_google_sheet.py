from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from core.supabase_client import supabase
from core.db_retry import retry_standard, retry_patient
from datetime import datetime, timedelta
from typing import Tuple, List, Dict, Optional
import re
import os
import sys

# ============================================================================
# CREDENTIALS LOADING - Hỗ trợ cả encrypted và plain file
# ============================================================================
def get_credentials_file():
    """
    Lấy đường dẫn đến credentials.json
    - Ưu tiên: credentials.json.encrypted (production)
    - Fallback: credentials.json (development)
    """
    # Kiểm tra xem có encrypted config không
    try:
        from secure_config import get_credentials_path
        # Nếu có encrypted file, dùng nó
        creds_path = get_credentials_path()
        print(f"[SYNC] Using encrypted credentials: {creds_path}")
        return creds_path
    except FileNotFoundError:
        print(f"[SYNC] No encrypted credentials found, trying plain file...")
    except Exception as e:
        print(f"[SYNC] Error loading encrypted credentials: {e}")
    
    # Fallback: tìm file credentials.json thô (dev mode)
    if getattr(sys, 'frozen', False):
        base_path = os.path.dirname(sys.executable)
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))
    
    plain_creds = os.path.join(base_path, 'credentials.json')
    
    if os.path.exists(plain_creds):
        print(f"[SYNC] Using plain credentials (dev mode): {plain_creds}")
        return plain_creds
    
    # Không tìm thấy credentials nào
    raise FileNotFoundError(
        "Không tìm thấy credentials.json hoặc credentials.json.encrypted. "
        "Vui lòng đảm bảo file tồn tại hoặc đã chạy encrypt_config.py"
    )


SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']
SHEET_ID = '1nnFBZkEYtnhvQuiKDr94__hRNaNIb3JsAXyFqJTl8WE'

SHEET_NAME = 'Lịch làm việc'

RANGE_HEADER = f"'{SHEET_NAME}'!B3:F3"
RANGE_DATES = f"'{SHEET_NAME}'!B4:F4"
RANGE_SANG = f"'{SHEET_NAME}'!B6:F14"
RANGE_CHIEU = f"'{SHEET_NAME}'!B17:F25"


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


def parse_date_from_sheet(date_str: str, year: int = None) -> Optional[datetime]:
    if not date_str or not isinstance(date_str, str):
        return None
    
    date_str = date_str.strip()
    
    match = re.match(r'(\d{1,2})/(\d{1,2})', date_str)
    if not match:
        return None
    
    day = int(match.group(1))
    month = int(match.group(2))
    
    if year is None:
        year = datetime.now().year
    
    try:
        return datetime(year, month, day)
    except ValueError:
        return None


@retry_patient
def sync_one_range(
    service,
    range_name: str,
    ca_truc: str,
    dates: List[datetime]
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
        print(f"Ngày: {[d.strftime('%d/%m/%Y') for d in dates]}")
        
        for row_idx, row in enumerate(values):
            for col_idx in range(min(len(row), 5)):
                cell_value = row[col_idx] if col_idx < len(row) else ""
                
                if not cell_value or str(cell_value).strip() == "":
                    continue
                
                if col_idx >= len(dates):
                    continue
                
                ngay_truc = dates[col_idx]
                
                col_letter = chr(ord('B') + col_idx)
                row_number = int(range_name.split('!')[1].split(':')[0][1:]) + row_idx
                cell_addr = f"{col_letter}{row_number}"
                
                cell_str_val = str(cell_value)
                
                print(f"\n  Cell {cell_addr} ({ngay_truc.strftime('%d/%m/%Y')}): '{cell_str_val}'")
                
                try:
                    ho_ten, sdt, is_valid = parse_cell_value(cell_str_val)
                    
                    print(f"    → Parsed: tên='{ho_ten}', sđt='{sdt}', valid={is_valid}")
                    
                    if not is_valid or not ho_ten:
                        error_msg = f"Parse thất bại hoặc không có tên"
                        print(f"{error_msg}")
                        error_count += 1
                        errors.append(f"{cell_addr} ({ngay_truc.strftime('%d/%m')}): {error_msg}")
                        continue
                    
                    can_bo_id = find_can_bo_by_name(ho_ten)
                    
                    if can_bo_id:
                        print(f"✓ Tìm thấy cán bộ ID: {can_bo_id}")
                    else:
                        print(f"✗ Không tìm thấy cán bộ trong DB")
                    
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
                            print(f"✓ Updated existing record (ID: {record['id']})")
                        else:
                            print(f"⊘ Skip: Trạng thái '{record['trang_thai']}' không cho phép update")
                    else:
                        data['trang_thai'] = 'Đã đăng ký'
                        data['created_at'] = datetime.now().isoformat()
                        supabase.table('lich_truc').insert(data).execute()
                        print(f"✓ Inserted new record")
                    
                    success_count += 1
                
                except Exception as e:
                    error_msg = str(e)
                    print(f"✗ Error: {error_msg}")
                    error_count += 1
                    errors.append(f"{cell_addr} ({ngay_truc.strftime('%d/%m')}): {error_msg}")
        
        print(f"\nKết quả {ca_truc}: {success_count} thành công, {error_count} lỗi")
        return (success_count, error_count, errors)
    
    except Exception as e:
        error_msg = f"Lỗi đọc range {range_name}: {str(e)}"
        print(f"✗ {error_msg}")
        return (0, 1, [error_msg])


@retry_patient
def sync_full_week() -> Dict:
    start_time = datetime.now()
    
    print(f"\n{'='*60}")
    print(f"BẮT ĐẦU ĐỒNG BỘ TUẦN")
    print(f"{'='*60}")
    
    try:
        # Lấy credentials file (encrypted hoặc plain)
        credentials_file = get_credentials_file()
        
        # Tạo credentials từ file
        creds = Credentials.from_service_account_file(credentials_file, scopes=SCOPES)
        service = build('sheets', 'v4', credentials=creds)
        
        print(f"\n✓ Đã kết nối Google Sheets API")
        print(f"Đọc ngày từ sheet...")
        
        date_result = service.spreadsheets().values().get(
            spreadsheetId=SHEET_ID,
            range=RANGE_DATES
        ).execute()
        
        date_values = date_result.get('values', [[]])[0] if date_result.get('values') else []
        
        dates = []
        current_year = datetime.now().year
        
        for date_str in date_values[:5]:
            parsed_date = parse_date_from_sheet(str(date_str), current_year)
            if parsed_date:
                dates.append(parsed_date)
            else:
                print(f"✗ Không parse được ngày: '{date_str}'")
        
        if len(dates) != 5:
            raise ValueError(f"Không đủ 5 ngày hợp lệ. Chỉ parse được {len(dates)} ngày: {date_values[:5]}")
        
        print(f"✓ Đã parse 5 ngày:")
        for i, d in enumerate(dates):
            weekday = ["Thứ 2", "Thứ 3", "Thứ 4", "Thứ 5", "Thứ 6", "Thứ 7", "Chủ nhật"][d.weekday()]
            print(f"  - {weekday}: {d.strftime('%d/%m/%Y')}")
        
        all_errors = []
        
        print(f"\nĐang sync ca SÁNG...")
        success_sang, error_sang, errors_sang = sync_one_range(
            service, RANGE_SANG, "Sáng", dates
        )
        all_errors.extend([f"[Sáng] {e}" for e in errors_sang])
        
        print(f"\nĐang sync ca CHIỀU...")
        success_chieu, error_chieu, errors_chieu = sync_one_range(
            service, RANGE_CHIEU, "Chiều", dates
        )
        all_errors.extend([f"[Chiều] {e}" for e in errors_chieu])
        
        total_success = success_sang + success_chieu
        total_errors = error_sang + error_chieu
        duration = (datetime.now() - start_time).total_seconds()
        
        print(f"\n{'='*60}")
        print(f"KẾT QUẢ TỔNG HỢP:")
        print(f"Thành công: {total_success}")
        print(f"Lỗi: {total_errors}")
        print(f"Thời gian: {duration:.2f}s")
        print(f"{'='*60}\n")
        
        try:
            week_str = f"{dates[0].strftime('%d/%m')} - {dates[-1].strftime('%d/%m/%Y')}"
            
            supabase.table('google_sheet_sync_log').insert({
                'sheet_id': SHEET_ID,
                'sheet_name': f'Tuần {week_str}',
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
            print("✓ Đã log kết quả vào database")
        except Exception as log_error:
            print(f"✗ Không thể log vào DB: {log_error}")
        
        return {
            'success': total_errors == 0,
            'sang': {'success': success_sang, 'errors': error_sang},
            'chieu': {'success': success_chieu, 'errors': error_chieu},
            'total_success': total_success,
            'total_errors': total_errors,
            'error_details': all_errors,
            'duration': duration,
            'week_range': f"{dates[0].strftime('%d/%m')} - {dates[-1].strftime('%d/%m/%Y')}"
        }
    
    except FileNotFoundError as e:
        error_msg = str(e)
        duration = (datetime.now() - start_time).total_seconds()
        
        print(f"\n{'='*60}")
        print(f"✗ LỖI: Không tìm thấy credentials")
        print(f"Chi tiết: {error_msg}")
        print(f"{'='*60}\n")
        
        return {
            'success': False,
            'sang': {'success': 0, 'errors': 0},
            'chieu': {'success': 0, 'errors': 0},
            'total_success': 0,
            'total_errors': 1,
            'error_details': [error_msg],
            'duration': duration
        }
    
    except Exception as e:
        error_msg = str(e)
        duration = (datetime.now() - start_time).total_seconds()
        
        print(f"\n{'='*60}")
        print(f"✗ LỖI NGHIÊM TRỌNG: {error_msg}")
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
    print(f"sync_specific_week() deprecated - redirecting to sync_full_week()")
    return sync_full_week()