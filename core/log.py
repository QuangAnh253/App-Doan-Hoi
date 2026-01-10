# core/log.py
from datetime import datetime
from core.supabase_client import supabase


def write_audit_log(
    user_id: str,
    user_email: str,
    user_full_name: str,
    action: str,
    table_name: str,
    record_id: str = None,
    old_values: dict = None,
    new_values: dict = None,
    details: str = None,
):
    try:
        supabase.table("audit_logs").insert({
            "user_id": user_id,
            "user_email": user_email,
            "user_full_name": user_full_name,
            "action": action,
            "table_name": table_name,
            "record_id": record_id,
            "old_values": old_values,
            "new_values": new_values,
            "details": details,
            "timestamp": datetime.now().isoformat(),
        }).execute()
    except Exception:
        pass


def write_import_export_log(
    user_id: str,
    user_email: str,
    operation_type: str,
    table_name: str,
    record_count: int,
    file_name: str = None,
    file_size_kb: int = None,
    status: str = "SUCCESS",
    error_message: str = None,
):
    try:
        supabase.table("import_export_logs").insert({
            "user_id": user_id,
            "user_email": user_email,
            "operation_type": operation_type,
            "table_name": table_name,
            "record_count": record_count,
            "file_name": file_name,
            "file_size_kb": file_size_kb,
            "status": status,
            "error_message": error_message,
            "timestamp": datetime.now().isoformat(),
        }).execute()
    except Exception:
        pass