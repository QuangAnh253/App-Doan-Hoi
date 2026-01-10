# ui/session_helper.py
import flet as ft
from typing import Optional, Any


def get_session_value(page: ft.Page, key: str, default: Any = None) -> Any:
    try:
        if hasattr(page, 'session') and hasattr(page.session, 'get'):
            value = page.session.get(key)
            if value is not None:
                return value
    except Exception:
        pass
    
    try:
        if hasattr(page, 'session'):
            value = getattr(page.session, key, None)
            if value is not None:
                return value
    except Exception:
        pass
    
    try:
        if hasattr(page, '_user_session') and isinstance(page._user_session, dict):
            value = page._user_session.get(key)
            if value is not None:
                return value
    except Exception:
        pass
    
    return default


def set_session_value(page: ft.Page, key: str, value: Any) -> None:
    success = False
    
    try:
        if hasattr(page, 'session') and hasattr(page.session, 'set'):
            page.session.set(key, value)
            success = True
    except Exception:
        pass
    
    try:
        if hasattr(page, 'session'):
            setattr(page.session, key, value)
            success = True
    except Exception:
        pass
    
    try:
        if not hasattr(page, '_user_session'):
            page._user_session = {}
        page._user_session[key] = value
        success = True
    except Exception:
        pass
    
    if not success:
        raise RuntimeError(f"Không thể ghi session key '{key}'")


def get_user_info(page: ft.Page) -> dict:
    return {
        'user_id': get_session_value(page, 'user_id', ''),
        'email': get_session_value(page, 'email', ''),
        'role': get_session_value(page, 'role', 'STAFF'),
        'full_name': get_session_value(page, 'full_name', 'User'),
    }


def debug_session(page: ft.Page):
    info = {}

    info['has_session'] = hasattr(page, 'session')
    if info['has_session']:
        try:
            info['session_type'] = str(type(page.session))
            if hasattr(page.session, '__dict__'):
                attrs = {k: v for k, v in page.session.__dict__.items() if not k.startswith('_')}
                info['session_attributes'] = attrs
        except Exception:
            info['session_attributes'] = None

    info['has__user_session'] = hasattr(page, '_user_session')
    if info['has__user_session']:
        try:
            info['_user_session'] = page._user_session
        except Exception:
            info['_user_session'] = None

    info['user_info'] = get_user_info(page)
    return info