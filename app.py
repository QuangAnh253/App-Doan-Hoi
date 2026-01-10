# app.py
import flet as ft
import asyncio
import os
import sys
try:
    print("[APP] Loading encrypted config...")
    from secure_config import load_env_variables
    load_env_variables()
    print("[APP] Encrypted config loaded successfully")
    USING_ENCRYPTED_CONFIG = True
except Exception as e:
    print(f"[APP]  Failed to load encrypted config: {e}")
    print("[APP] Falling back to regular .env file...")
    from dotenv import load_dotenv
    load_dotenv()
    USING_ENCRYPTED_CONFIG = False

from ui.login import LoginView
from ui.main_layout import MainLayout, ensure_fullscreen_on_activate


def get_icon_path():
    if getattr(sys, 'frozen', False):
        base_path = os.path.dirname(sys.executable)
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))
    
    # Try multiple icon paths
    icon_paths = [
        os.path.join(base_path, "assets", "favicon.ico"),
        os.path.join(base_path, "assets", "icon.png"),
        os.path.join(base_path, "assets", "icon.ico"),
    ]
    
    for path in icon_paths:
        if os.path.exists(path):
            print(f"[APP] Found icon: {path}")
            return path
    
    print(f"[APP] Icon not found. Searched in: {base_path}/assets/")
    return None


def main(page: ft.Page):
    page.title = "Quản lý Đoàn - Hội"
    page.padding = 0
    page.theme_mode = ft.ThemeMode.LIGHT

    # Set window icon
    try:
        icon_path = get_icon_path()
        if icon_path:
            page.window.icon = icon_path
            print(f"[APP] Set window icon: {icon_path}")
        else:
            print(f"[APP]  Icon not found in assets folder")
    except Exception as e:
        print(f"[APP] Failed to set icon: {e}")

    # Hide title bar (custom title bar)
    try:
        page.window.title_bar_hidden = True
        print("[APP] Hidden default title bar")
    except Exception as e:
        print(f"[APP]  Failed to hide title bar: {e}")

    # Set window properties
    page.window.width = 1400
    page.window.height = 900
    page.window.resizable = True
    page.window.maximizable = True
    page.window.minimizable = True
    page.update()
    try:
        page.window.maximized = True
        page.update()
        print("[APP] Window maximized")
    except Exception as e:
        print(f"[APP]  Failed to maximize window: {e}")

    # Log config status
    if USING_ENCRYPTED_CONFIG:
        print("[APP] Running with ENCRYPTED config (secure)")
    else:
        print("[APP] Running with PLAIN .env file (development mode)")

    def on_login_success(session):
        try:
            page.session.set("user_id", session.user_id)
            page.session.set("email", session.email)
            page.session.set("role", session.role)
            page.session.set("full_name", session.full_name)
        except AttributeError:
            try:
                page.session.__setitem__("user_id", session.user_id)
                page.session.__setitem__("email", session.email)
                page.session.__setitem__("role", session.role)
                page.session.__setitem__("full_name", session.full_name)
            except:
                if not hasattr(page, '_user_session'):
                    page._user_session = {}
                page._user_session["user_id"] = session.user_id
                page._user_session["email"] = session.email
                page._user_session["role"] = session.role
                page._user_session["full_name"] = session.full_name

        print(f"[APP] Login successful: {session.email} ({session.role})")

        try:
            page.window.title_bar_hidden = True
        except:
            pass

        page.controls.clear()
        
        # THÊM KIỂM TRA NEW_USER
        if session.role == 'NEW_USER':
            from ui.waiting_approval import WaitingApprovalView
            page.add(WaitingApprovalView(page, session.email, session.full_name).build())
        else:
            page.add(MainLayout(page, session.role))
        
        page.update()
        
        try:
            ensure_fullscreen_on_activate(page)
        except Exception as e:
            print(f"[APP] Failed to ensure fullscreen: {e}")

    login_view = LoginView(on_login_success, page)
    page.add(login_view.build())
    page.update()

    async def _maximize_window():
        delays = [0.01, 0.05, 0.1, 0.3, 0.6, 1.0, 1.5]
        
        for delay in delays:
            await asyncio.sleep(delay)
            
            try:
                # Hide title bar
                try:
                    page.window.title_bar_hidden = True
                except:
                    pass
                
                # Maximize window
                try:
                    page.window.maximized = True
                    page.window.resizable = True
                except:
                    pass
                
                page.update()
            except:
                pass
    
    page.run_task(_maximize_window)


if __name__ == "__main__":
    print("")
    print("="*60)
    print("QUẢN LÝ ĐOÀN - HỘI")
    print("="*60)
    print("")
    
    ft.app(target=main)