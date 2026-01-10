# services/noi_bo_service.py
from core.supabase_client import supabase
from core.db_retry import retry_standard, retry_patient, retry_critical
from datetime import datetime, timedelta
from typing import List, Dict, Optional


@retry_standard
def fetch_can_bo_bvp_bch(
    loai: str = "",
    search: str = "",
    page: int = 1,
    page_size: int = 100
) -> List[Dict]:
    """Lấy danh sách cán bộ BVP/BCH"""
    try:
        query = supabase.table('can_bo_cap_truong').select('*')
        
        if loai:
            query = query.eq('loai_can_bo', loai)
        
        if search:
            search_term = search.strip()
            query = query.or_(
                f"ho_ten.ilike.%{search_term}%,"
                f"mssv.ilike.%{search_term}%,"
                f"sdt.ilike.%{search_term}%"
            )
        
        query = query.order('created_at', desc=True)
        
        start = (page - 1) * page_size
        end = start + page_size - 1
        query = query.range(start, end)
        
        response = query.execute()
        data = response.data or []
        
        return data
        
    except Exception as ex:
        raise Exception(f"Lỗi lấy danh sách cán bộ: {str(ex)}")


@retry_standard
def count_can_bo_bvp_bch(loai: str = "", search: str = "") -> int:
    """Đếm số lượng cán bộ"""
    try:
        query = supabase.table('can_bo_cap_truong').select('id', count='exact')
        
        if loai:
            query = query.eq('loai_can_bo', loai)
        
        if search:
            search_term = search.strip()
            query = query.or_(
                f"ho_ten.ilike.%{search_term}%,"
                f"mssv.ilike.%{search_term}%,"
                f"sdt.ilike.%{search_term}%"
            )
        
        response = query.execute()
        count = response.count or 0
        
        return count
        
    except Exception as ex:
        raise Exception(f"Lỗi đếm cán bộ: {str(ex)}")


@retry_standard
def get_can_bo_by_id(can_bo_id: str) -> Optional[Dict]:
    """Lấy 1 cán bộ theo ID"""
    try:
        res = supabase.table('can_bo_cap_truong')\
            .select('*')\
            .eq('id', can_bo_id)\
            .execute()
        
        return res.data[0] if res.data else None
        
    except Exception as ex:
        raise Exception(f"Lỗi lấy thông tin cán bộ: {str(ex)}")


@retry_patient
def create_can_bo(data: Dict) -> Dict:
    """Tạo cán bộ mới"""
    data['created_at'] = datetime.now().isoformat()
    
    res = supabase.table('can_bo_cap_truong').insert(data).execute()
    
    if not res.data:
        raise Exception("Không thể tạo cán bộ mới")
    
    return res.data[0]


@retry_patient
def update_can_bo(can_bo_id: str, data: Dict) -> Dict:
    """Cập nhật thông tin cán bộ"""
    data['updated_at'] = datetime.now().isoformat()
    
    res = supabase.table('can_bo_cap_truong')\
        .update(data)\
        .eq('id', can_bo_id)\
        .execute()
    
    if not res.data:
        raise Exception(f"Không thể cập nhật cán bộ ID: {can_bo_id}")
    
    return res.data[0]


@retry_critical
def delete_can_bo(can_bo_id: str) -> bool:
    """Xóa cán bộ"""
    res = supabase.table('can_bo_cap_truong')\
        .delete()\
        .eq('id', can_bo_id)\
        .execute()
    
    if not res.data:
        raise Exception(f"Không thể xóa cán bộ ID: {can_bo_id}")
    
    return True


@retry_patient
def bulk_update_can_bo(can_bo_ids: List[str], data: Dict) -> int:
    """Cập nhật hàng loạt cán bộ"""
    if not can_bo_ids:
        raise ValueError("Danh sách IDs rỗng")
    
    data['updated_at'] = datetime.now().isoformat()
    
    success_count = 0
    errors = []
    
    for can_bo_id in can_bo_ids:
        try:
            update_can_bo(can_bo_id, data)
            success_count += 1
        except Exception as e:
            errors.append(f"ID {can_bo_id}: {str(e)}")
    
    if errors:
        error_msg = "\n".join(errors[:5])
        if len(errors) > 5:
            error_msg += f"\n... và {len(errors) - 5} lỗi khác"
        raise Exception(f"Cập nhật thất bại {len(errors)}/{len(can_bo_ids)}:\n{error_msg}")
    
    return success_count


@retry_standard
def fetch_lich_truc(
    ca_truc: str = "",
    trang_thai: str = "",
    tu_ngay: str = "",
    den_ngay: str = "",
    page: int = 1,
    page_size: int = 100
) -> List[Dict]:
    """Lấy danh sách lịch trực"""
    try:
        query = supabase.table('lich_truc').select('*')
        
        if ca_truc:
            query = query.eq('ca_truc', ca_truc)
        
        if trang_thai:
            query = query.eq('trang_thai', trang_thai)
        
        if tu_ngay:
            query = query.gte('ngay_truc', tu_ngay)
        
        if den_ngay:
            query = query.lte('ngay_truc', den_ngay)
        
        query = query.order('ngay_truc', desc=True).order('ca_truc')
        
        start = (page - 1) * page_size
        end = start + page_size - 1
        query = query.range(start, end)
        
        response = query.execute()
        data = response.data or []
        
        return data
        
    except Exception as ex:
        return _fetch_lich_truc_with_python_filter(ca_truc, trang_thai, tu_ngay, den_ngay, page, page_size)


def _fetch_lich_truc_with_python_filter(
    ca_truc: str,
    trang_thai: str,
    tu_ngay: str,
    den_ngay: str,
    page: int,
    page_size: int
) -> List[Dict]:
    """Fallback: Filter dates in Python if Supabase date filter fails"""
    try:
        query = supabase.table('lich_truc').select('*')
        
        if ca_truc:
            query = query.eq('ca_truc', ca_truc)
        
        if trang_thai:
            query = query.eq('trang_thai', trang_thai)
        
        query = query.order('ngay_truc', desc=True).order('ca_truc')
        query = query.range(0, 999)
        
        response = query.execute()
        all_data = response.data or []
        
        filtered_data = []
        for record in all_data:
            ngay_str = str(record.get('ngay_truc', ''))
            if not ngay_str:
                continue
            
            if tu_ngay and ngay_str < tu_ngay:
                continue
            if den_ngay and ngay_str > den_ngay:
                continue
            
            filtered_data.append(record)
        
        start = (page - 1) * page_size
        end = start + page_size
        
        return filtered_data[start:end]
        
    except Exception as ex:
        raise Exception(f"Lỗi lấy lịch trực: {str(ex)}")


@retry_standard
def count_lich_truc(
    ca_truc: str = "",
    trang_thai: str = "",
    tu_ngay: str = "",
    den_ngay: str = ""
) -> int:
    """Đếm số lượng ca trực"""
    try:
        query = supabase.table('lich_truc').select('id', count='exact')
        
        if ca_truc:
            query = query.eq('ca_truc', ca_truc)
        
        if trang_thai:
            query = query.eq('trang_thai', trang_thai)
        
        if tu_ngay:
            query = query.gte('ngay_truc', tu_ngay)
        
        if den_ngay:
            query = query.lte('ngay_truc', den_ngay)
        
        response = query.execute()
        return response.count or 0
        
    except Exception as ex:
        try:
            data = _fetch_lich_truc_with_python_filter(ca_truc, trang_thai, tu_ngay, den_ngay, 1, 9999)
            return len(data)
        except:
            return 0


@retry_standard
def get_lich_truc_by_id(lich_truc_id: str) -> Optional[Dict]:
    """Lấy 1 lịch trực theo ID"""
    try:
        res = supabase.table('lich_truc')\
            .select('*')\
            .eq('id', lich_truc_id)\
            .execute()
        
        return res.data[0] if res.data else None
        
    except Exception as ex:
        raise Exception(f"Lỗi lấy lịch trực: {str(ex)}")


@retry_patient
def create_lich_truc(data: Dict) -> Dict:
    """Tạo lịch trực thủ công"""
    data['trang_thai'] = data.get('trang_thai', 'Đã đăng ký')
    data['nguon'] = 'Thủ công'
    data['created_at'] = datetime.now().isoformat()
    
    res = supabase.table('lich_truc').insert(data).execute()
    
    if not res.data:
        raise Exception("Không thể tạo lịch trực mới")
    
    return res.data[0]


@retry_patient
def update_lich_truc(lich_truc_id: str, data: Dict) -> Dict:
    """Cập nhật lịch trực"""
    data['updated_at'] = datetime.now().isoformat()
    
    res = supabase.table('lich_truc')\
        .update(data)\
        .eq('id', lich_truc_id)\
        .execute()
    
    if not res.data:
        raise Exception(f"Không thể cập nhật lịch trực ID: {lich_truc_id}")
    
    return res.data[0]


@retry_critical
def delete_lich_truc(lich_truc_id: str) -> bool:
    """Xóa lịch trực"""
    res = supabase.table('lich_truc')\
        .delete()\
        .eq('id', lich_truc_id)\
        .execute()
    
    if not res.data:
        raise Exception(f"Không thể xóa lịch trực ID: {lich_truc_id}")
    
    return True


@retry_patient
def bulk_confirm_lich_truc(lich_truc_ids: List[str]) -> int:
    """Xác nhận hàng loạt ca trực"""
    data = {
        'trang_thai': 'Đã xác nhận',
        'updated_at': datetime.now().isoformat()
    }
    
    success_count = 0
    errors = []
    
    for lich_truc_id in lich_truc_ids:
        try:
            update_lich_truc(lich_truc_id, data)
            success_count += 1
        except Exception as e:
            errors.append(f"ID {lich_truc_id}: {str(e)}")
    
    if errors:
        error_msg = "\n".join(errors[:5])
        if len(errors) > 5:
            error_msg += f"\n... và {len(errors) - 5} lỗi khác"
        raise Exception(f"Xác nhận thất bại {len(errors)}/{len(lich_truc_ids)}:\n{error_msg}")
    
    return success_count


@retry_standard
def get_thong_ke_tong_quan() -> Dict:
    """Lấy thống kê tổng quan"""
    try:
        can_bo_response = supabase.table('can_bo_cap_truong')\
            .select('id', count='exact')\
            .execute()
        
        today = datetime.now()
        first_day = today.replace(day=1).date().isoformat()
        
        if today.month == 12:
            last_day = today.replace(year=today.year + 1, month=1, day=1).date().isoformat()
        else:
            last_day = today.replace(month=today.month + 1, day=1).date().isoformat()
        
        try:
            lich_truc_response = supabase.table('lich_truc')\
                .select('trang_thai', count='exact')\
                .gte('ngay_truc', first_day)\
                .lt('ngay_truc', last_day)\
                .execute()
            
            all_lich = lich_truc_response.data or []
        except:
            all_response = supabase.table('lich_truc')\
                .select('ngay_truc, trang_thai')\
                .range(0, 999)\
                .execute()
            
            all_lich = [
                lt for lt in (all_response.data or [])
                if lt.get('ngay_truc') and first_day <= str(lt['ngay_truc']) < last_day
            ]
        
        hoan_thanh = [
            lt for lt in all_lich
            if lt.get('trang_thai') == 'Đã trực'
        ]
        
        result = {
            'tong_can_bo': can_bo_response.count or 0,
            'tong_ca_truc_thang': len(all_lich),
            'ca_hoan_thanh': len(hoan_thanh),
            'ty_le_hoan_thanh': round(
                (len(hoan_thanh) / len(all_lich) * 100) 
                if len(all_lich) > 0 else 0, 
                1
            )
        }
        
        return result
        
    except Exception as ex:
        raise Exception(f"Lỗi lấy thống kê: {str(ex)}")


@retry_standard
def fetch_thong_ke_thang(year: int, month: int) -> List[Dict]:
    """Lấy thống kê theo tháng"""
    try:
        first_day = datetime(year, month, 1).date().isoformat()
        
        if month == 12:
            last_day = datetime(year + 1, 1, 1).date().isoformat()
        else:
            last_day = datetime(year, month + 1, 1).date().isoformat()
        
        try:
            lich_truc_response = supabase.table('lich_truc')\
                .select('can_bo_id, ho_ten, trang_thai, ngay_truc')\
                .gte('ngay_truc', first_day)\
                .lt('ngay_truc', last_day)\
                .execute()
            
            lich_thang = lich_truc_response.data or []
        except:
            all_response = supabase.table('lich_truc')\
                .select('can_bo_id, ho_ten, trang_thai, ngay_truc')\
                .range(0, 999)\
                .execute()
            
            lich_thang = [
                lt for lt in (all_response.data or [])
                if lt.get('ngay_truc') and first_day <= str(lt['ngay_truc']) < last_day
            ]
        
        stats = {}
        for lt in lich_thang:
            ho_ten = lt.get('ho_ten', '')
            if not ho_ten:
                continue
            
            if ho_ten not in stats:
                stats[ho_ten] = {
                    'ho_ten': ho_ten,
                    'tong_ca': 0,
                    'da_hoan_thanh': 0,
                    'vang': 0,
                }
            
            stats[ho_ten]['tong_ca'] += 1
            
            if lt.get('trang_thai') == 'Đã trực':
                stats[ho_ten]['da_hoan_thanh'] += 1
            elif lt.get('trang_thai') == 'Vắng':
                stats[ho_ten]['vang'] += 1
        
        result = list(stats.values())
        return result
        
    except Exception as ex:
        raise Exception(f"Lỗi lấy thống kê tháng: {str(ex)}")