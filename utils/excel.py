# utils/excel.py
import pandas as pd
from io import BytesIO

def read_excel(file_bytes: bytes, sheet_name: str = 0) -> pd.DataFrame:
    """
    Đọc file Excel từ bytes
    """
    return pd.read_excel(BytesIO(file_bytes), sheet_name=sheet_name)


def write_excel(data: list[dict], columns: list[str] = None) -> bytes:
    """
    Ghi dữ liệu ra Excel dạng bytes
    """
    df = pd.DataFrame(data)
    if columns:
        df = df[columns]
    
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Data')
    
    return output.getvalue()


def validate_excel_columns(df: pd.DataFrame, required_columns: list[str]) -> tuple[bool, str]:
    """
    Kiểm tra các cột bắt buộc có đủ không
    Returns: (is_valid, error_message)
    """
    missing = set(required_columns) - set(df.columns)
    if missing:
        return False, f"Thiếu các cột: {', '.join(missing)}"
    return True, ""


def clean_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Làm sạch DataFrame:
    - Xóa khoảng trắng thừa
    - Thay NaN bằng None
    - Strip column names
    """
    df.columns = df.columns.str.strip()
    df = df.applymap(lambda x: x.strip() if isinstance(x, str) else x)
    df = df.where(pd.notnull(df), None)
    return df
