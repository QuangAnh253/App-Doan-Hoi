from typing import Callable, Optional
import flet as ft
import webbrowser
import threading
import time
import requests
from core.auth import (
    login, 
    login_with_oauth, 
    UserSession, 
    load_credentials, 
    save_credentials,
    clear_credentials
)
from core.supabase_client import supabase, SUPABASE_URL, SUPABASE_ANON_KEY
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs
from ui.icon_helper import CustomIcon, icon_button
from ui.custom_title_bar import CustomTitleBar


class LoginView:
    def __init__(self, on_login_success: Callable[[object], None], page: Optional[ft.Page] = None):
        self.on_login_success = on_login_success
        self.page = page

        saved_id, saved_pwd = load_credentials()
        self.has_saved = saved_id and saved_pwd

        self.email_field = ft.TextField(
            label="Email hoặc Username",
            hint_text="Nhập email hoặc username của bạn",
            value=saved_id if self.has_saved else "",
            border_radius=12,
            filled=True,
            bgcolor=ft.Colors.WHITE,
            border_color=ft.Colors.GREY_400,
            focused_border_color=ft.Colors.BLUE_600,
            text_size=14,
            height=56,
            width=float("inf"),
            color=ft.Colors.BLACK,
        )

        self.password_field = ft.TextField(
            label="Mật khẩu",
            hint_text="Nhập mật khẩu của bạn",
            value=saved_pwd if self.has_saved else "",
            password=True,
            can_reveal_password=True,
            border_radius=12,
            filled=True,
            bgcolor=ft.Colors.WHITE,
            border_color=ft.Colors.GREY_400,
            focused_border_color=ft.Colors.BLUE_600,
            text_size=14,
            height=56,
            width=float("inf"),
            on_submit=self._handle_login,
            color=ft.Colors.BLACK,
        )

        self.remember_checkbox_value = self.has_saved

        self.message_container = ft.Container(
            content=ft.Row([
                ft.Icon(ft.Icons.INFO_OUTLINED, size=20, color=ft.Colors.BLUE_700),
                ft.Text("", size=13, weight=ft.FontWeight.W_500, color=ft.Colors.BLUE_700),
            ], spacing=8),
            padding=12,
            border_radius=8,
            bgcolor=ft.Colors.BLUE_50,
            visible=False,
        )

        self.login_button = ft.ElevatedButton(
            content=ft.Text("Đăng nhập", size=15, weight=ft.FontWeight.W_600),
            on_click=self._handle_login,
            style=ft.ButtonStyle(
                color=ft.Colors.WHITE,
                bgcolor=ft.Colors.BLUE_600,
                padding=16,
                shape=ft.RoundedRectangleBorder(radius=12),
            ),
            height=56,
            width=float("inf"),
        )

        self.google_button = ft.ElevatedButton(
            content=ft.Row([
                ft.Image(src="assets/google.png", width=20, height=20),
                ft.Text("Đăng nhập với Google", color=ft.Colors.BLACK),
            ], alignment=ft.MainAxisAlignment.CENTER, spacing=10),
            on_click=lambda e: self._handle_oauth_login("google"),
            style=ft.ButtonStyle(
                bgcolor=ft.Colors.WHITE,
                padding=14,
                shape=ft.RoundedRectangleBorder(radius=12),
                side=ft.BorderSide(1, ft.Colors.GREY_400)
            ),
            height=52,
            width=float("inf"),
        )

        self.discord_button = ft.ElevatedButton(
            content=ft.Row([
                ft.Image(src="assets/discord.png", width=20, height=20),
                ft.Text("Đăng nhập với Discord", color=ft.Colors.BLACK),
            ], alignment=ft.MainAxisAlignment.CENTER, spacing=10),
            on_click=lambda e: self._handle_oauth_login("discord"),
            style=ft.ButtonStyle(
                bgcolor=ft.Colors.WHITE,
                padding=14,
                shape=ft.RoundedRectangleBorder(radius=12),
                side=ft.BorderSide(1, ft.Colors.GREY_400)
            ),
            height=52,
            width=float("inf"),
        )

        self.loading_overlay = None
        self.main_content = None
        self.container = None

    def _create_loading_overlay(self):
        return ft.Container(
            content=ft.Column([
                ft.Container(
                    content=ft.Image(src="assets/favicon.ico", width=120, height=120),
                    margin=ft.margin.only(bottom=24),
                ),
                ft.ProgressRing(
                    width=50, 
                    height=50, 
                    stroke_width=4, 
                    color=ft.Colors.BLUE_600
                ),
                ft.Container(height=20),
                ft.Text(
                    "Đang đăng nhập...",
                    size=18,
                    weight=ft.FontWeight.W_600,
                    color=ft.Colors.BLACK,
                ),
                ft.Text(
                    "Vui lòng đợi trong giây lát",
                    size=14,
                    color=ft.Colors.GREY_700,
                ),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=0,
            ),
            bgcolor=ft.Colors.WHITE,
            expand=True,
            alignment=ft.Alignment.CENTER,
            visible=True,
        )

    def _show_loading_screen(self):
        if self.loading_overlay and self.main_content:
            self.loading_overlay.visible = True
            self.main_content.visible = False
            if self.page:
                self.page.update()

    def _hide_loading_screen(self):
        if self.loading_overlay and self.main_content:
            self.loading_overlay.visible = False
            self.main_content.visible = True
            if self.page:
                self.page.update()

    def _reset_login_button(self):
        self.login_button.disabled = False
        self.login_button.content = ft.Text("Đăng nhập", size=15, weight=ft.FontWeight.W_600)
        if self.page:
            self.page.update()

    def _set_login_button_loading(self):
        self.login_button.disabled = True
        self.login_button.content = ft.Row([
            ft.ProgressRing(width=16, height=16, stroke_width=2, color=ft.Colors.WHITE),
            ft.Text("Đang đăng nhập...", size=15, weight=ft.FontWeight.W_600),
        ], alignment=ft.MainAxisAlignment.CENTER, spacing=8)
        if self.page:
            self.page.update()

    def build(self) -> ft.Control:
        
        logo = ft.Container(
            content=ft.Image(src="assets/favicon.ico", width=120, height=120),
            alignment=ft.Alignment.CENTER,
            margin=ft.margin.only(bottom=16),
        )

        remember_checkbox = ft.Checkbox(
            label="Ghi nhớ đăng nhập",
            value=self.remember_checkbox_value,
            on_change=lambda e: setattr(self, 'remember_checkbox_value', e.control.value),
            label_style=ft.TextStyle(
                color=ft.Colors.BLACK,
                size=14,
                weight=ft.FontWeight.W_500,
            ),
        )

        def reset_saved_credentials(e):
            clear_credentials()
            self.email_field.value = ""
            self.password_field.value = ""
            self.remember_checkbox_value = False
            remember_checkbox.value = False
            saved_hint.visible = False
            self._show_success("Đã xóa thông tin đăng nhập đã lưu")
            if self.page:
                self.page.update()
        
        saved_hint = ft.Container(
            content=ft.Row([
                ft.Icon(ft.Icons.INFO_OUTLINE, size=14, color=ft.Colors.BLUE_600),
                ft.Text(
                    "Đã lưu thông tin đăng nhập",
                    size=11,
                    color=ft.Colors.BLUE_600,
                    italic=True,
                ),
                ft.TextButton(
                    "Xóa",
                    on_click=reset_saved_credentials,
                    style=ft.ButtonStyle(
                        color=ft.Colors.RED_600,
                        padding=4,
                    ),
                ),
            ], spacing=4),
            padding=ft.padding.only(top=2, bottom=4),
            visible=self.remember_checkbox_value,
        )

        form_content = ft.Container(
            content=ft.Column([
                logo,
                ft.Text("Chào mừng trở lại", size=28, weight=ft.FontWeight.BOLD, color=ft.Colors.BLACK),
                ft.Text("Đăng nhập để tiếp tục", size=14, color=ft.Colors.GREY_700),
                ft.Container(height=20),
                self.email_field,
                ft.Container(height=4),
                self.password_field,
                ft.Container(height=8),
                remember_checkbox,
                saved_hint,
                self.message_container,
                ft.Container(height=4),
                self.login_button,
                ft.Container(
                    content=ft.Row(controls=[
                        ft.Container(height=1, bgcolor=ft.Colors.GREY_400, expand=True),
                        ft.Text("HOẶC", size=12, color=ft.Colors.GREY_700, weight=ft.FontWeight.W_500),
                        ft.Container(height=1, bgcolor=ft.Colors.GREY_400, expand=True),
                    ], alignment=ft.MainAxisAlignment.CENTER, spacing=12),
                    margin=ft.margin.symmetric(vertical=14),
                ),
                self.google_button,
                ft.Container(height=4),
                self.discord_button,
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=0,
            tight=True,
            ),
            width=480,
            padding=ft.padding.symmetric(horizontal=40, vertical=32),
            border_radius=16,
            bgcolor=ft.Colors.with_opacity(0.98, ft.Colors.WHITE),
            shadow=ft.BoxShadow(
                spread_radius=1,
                blur_radius=20,
                color=ft.Colors.with_opacity(0.15, ft.Colors.BLACK),
                offset=ft.Offset(0, 4),
            ),
        )

        background = ft.Container(
            content=ft.Image(
                src="assets/bg.png",
                width=9999,
                height=9999,
                fit="cover",
            ),
            expand=True,
        )

        self.main_content = ft.Stack(
            controls=[
                background,
                ft.Container(
                    content=form_content,
                    alignment=ft.Alignment.CENTER,
                    expand=True,
                ),
            ],
            expand=True,
        )
        main_container = ft.Container(
            content=self.main_content,
            expand=True,
            visible=False,
        )

        self.loading_overlay = self._create_loading_overlay()

        final_stack = ft.Stack(
            controls=[
                main_container,
                self.loading_overlay,
            ],
            expand=True,
        )

        self.main_content = main_container

        self.container = ft.Container(
            content=final_stack,
            expand=True,
            padding=0,
            margin=0,
            bgcolor=ft.Colors.WHITE,
        )

        if self.page:
            # hide native title bar so custom title bar can be used
            try:
                try:
                    self.page.window_title_bar_hidden = True
                except Exception:
                    pass
                try:
                    self.page.window_title_bar_buttons_hidden = True
                except Exception:
                    pass
            except Exception:
                pass

            threading.Thread(target=self._check_and_auto_login, daemon=True).start()

        # add custom title bar on top of login screen when page is available
        if self.page:
            try:
                title_bar = CustomTitleBar(
                    page=self.page,
                    title="HỆ THỐNG QUẢN LÝ ĐOÀN - HỘI",
                    logo_path="assets/favicon.ico",
                    user_name="",
                    user_email="",
                    user_role="",
                    on_profile_click=None,
                    on_user_management_click=None,
                    on_logout_click=None,
                ).build()

                return ft.Column(
                    spacing=0,
                    expand=True,
                    horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
                    controls=[
                        title_bar,
                        self.container,
                    ],
                )
            except Exception:
                return self.container

        return self.container

    def _check_and_auto_login(self):
        try:
            time.sleep(0.5)
            
            if not self.has_saved:
                print("[LOGIN] No saved credentials, showing login form")
                if self.page:
                    self.page.run_thread(self._hide_loading_screen)
                return
            
            identifier = self.email_field.value
            password = self.password_field.value
            
            if not identifier or not password:
                print("[LOGIN] Invalid saved credentials")
                if self.page:
                    self.page.run_thread(self._hide_loading_screen)
                return
            
            print(f"[LOGIN] Attempting auto-login for: {identifier}")
            session = login(identifier, password, remember=True)
            
            if session:
                print(f"[LOGIN] Auto-login successful!")
                time.sleep(0.3)
                
                try:
                    self.on_login_success(session)
                except Exception as callback_error:
                    print(f"[LOGIN] Callback error: {callback_error}")
                    import traceback
                    traceback.print_exc()
                    if self.page:
                        self.page.run_thread(self._hide_loading_screen)
                        self.page.run_thread(lambda: self._show_error("Lỗi xử lý đăng nhập"))
            else:
                print(f"[LOGIN] Auto-login failed - invalid credentials")
                if self.page:
                    self.page.run_thread(self._hide_loading_screen)
                    self.page.run_thread(lambda: self._show_error("Thông tin đăng nhập không hợp lệ. Vui lòng đăng nhập lại."))
                
        except Exception as e:
            print(f"[LOGIN] Auto-login error: {e}")
            import traceback
            traceback.print_exc()
            
            error_msg = str(e)
            if self.page:
                self.page.run_thread(self._hide_loading_screen)
                self.page.run_thread(lambda: self._show_error(f"Lỗi đăng nhập: {error_msg}"))

    def _handle_login(self, e=None):
        identifier = self.email_field.value
        password = self.password_field.value

        if not identifier or not password:
            self._show_error("Vui lòng nhập đầy đủ thông tin đăng nhập")
            return

        self._show_loading_screen()

        def do_login():
            try:
                time.sleep(0.3)
                
                remember = self.remember_checkbox_value
                session = login(identifier, password, remember=remember)
                
                if not remember:
                    clear_credentials()
                
                if session:
                    print(f"[LOGIN] Manual login successful")
                    time.sleep(0.2)
                    self.on_login_success(session)
                else:
                    if self.page:
                        self.page.run_thread(self._hide_loading_screen)
                        self.page.run_thread(lambda: self._show_error("Sai email/username hoặc mật khẩu"))
                        self.page.run_thread(self._reset_login_button)
                    
            except Exception as ex:
                error_msg = str(ex)
                if self.page:
                    self.page.run_thread(self._hide_loading_screen)
                    self.page.run_thread(lambda: self._show_error(f"Lỗi đăng nhập: {error_msg}"))
                    self.page.run_thread(self._reset_login_button)

        threading.Thread(target=do_login, daemon=True).start()

    def _handle_oauth_login(self, provider: str) -> None:
        try:
            from core.auth import login_with_oauth
            redirect = login_with_oauth(provider)
        except Exception as e:
            self._show_error(f"Lỗi OAuth: {e}")
            return

        if isinstance(redirect, str) and redirect.startswith("http"):
            server = None

            class _Handler(BaseHTTPRequestHandler):
                def do_GET(self):
                    if self.path.startswith('/auth/callback'):
                        self.send_response(200)
                        self.send_header('Content-Type', 'text/html; charset=utf-8')
                        self.end_headers()
                        html = '''
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Đăng nhập</title>
    <link rel="icon" type="image/png" href="https://gelhujjzrxqvcxwfguvf.supabase.co/storage/v1/object/public/app-doan-hoi/logo-removebg.png">
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            background-image: url('https://gelhujjzrxqvcxwfguvf.supabase.co/storage/v1/object/public/app-doan-hoi/bg.png');
            background-size: cover;
            background-position: center;
            background-repeat: no-repeat;
        }
        .container {
            background: rgba(255, 255, 255, 0.98);
            border-radius: 20px;
            padding: 60px 80px;
            box-shadow: 0 10px 40px rgba(0, 0, 0, 0.15);
            text-align: center;
            max-width: 500px;
            width: 90%;
        }
        .logo {
            width: 120px;
            height: 120px;
            margin: 0 auto 30px;
        }
        .logo img {
            width: 100%;
            height: 100%;
            object-fit: contain;
        }
        .spinner {
            width: 50px;
            height: 50px;
            margin: 30px auto;
            border: 4px solid #e3e3e3;
            border-top: 4px solid #2196F3;
            border-radius: 50%;
            animation: spin 1s linear infinite;
        }
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        h1 {
            color: #212121;
            font-size: 28px;
            margin-bottom: 10px;
            font-weight: 600;
        }
        p {
            color: #616161;
            font-size: 16px;
            line-height: 1.6;
        }
        .success {
            color: #4CAF50;
        }
        .error {
            color: #f44336;
        }
        .success-icon, .error-icon {
            font-size: 64px;
            margin-bottom: 20px;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="logo">
            <img src="https://gelhujjzrxqvcxwfguvf.supabase.co/storage/v1/object/public/app-doan-hoi/logo-removebg.png" alt="Logo">
        </div>
        <div id="status">
            <div class="spinner"></div>
            <h1>Đang xử lý đăng nhập...</h1>
            <p>Vui lòng đợi trong giây lát</p>
        </div>
    </div>
    <script>
        const params = new URLSearchParams(window.location.search);
        const code = params.get("code");
        
        if(code) {
            fetch("/token", {
                method: "POST",
                headers: {"Content-Type": "application/json"},
                body: JSON.stringify({code: code})
            })
            .then(() => {
                document.getElementById('status').innerHTML = `
                    <div class="success-icon">✓</div>
                    <h1 class="success">Đăng nhập thành công!</h1>
                    <p>Bạn có thể đóng cửa sổ này và quay lại ứng dụng.</p>
                `;
                setTimeout(() => window.close(), 2000);
            })
            .catch(() => {
                document.getElementById('status').innerHTML = `
                    <div class="error-icon">✕</div>
                    <h1 class="error">Đã xảy ra lỗi</h1>
                    <p>Vui lòng thử lại hoặc liên hệ hỗ trợ.</p>
                `;
            });
        } else {
            document.getElementById('status').innerHTML = `
                <div class="error-icon">✕</div>
                <h1 class="error">Không nhận được mã xác thực</h1>
                <p>Vui lòng thử đăng nhập lại.</p>
            `;
        }
    </script>
</body>
</html>
'''
                        self.wfile.write(html.encode('utf-8'))
                    else:
                        self.send_response(404)
                        self.end_headers()

                def do_POST(self):
                    if self.path == '/token':
                        length = int(self.headers.get('Content-Length', 0))
                        body = self.rfile.read(length).decode()
                        
                        try:
                            import json
                            data = json.loads(body)
                            code = data.get('code')
                            
                            if code:
                                try:
                                    from core.supabase_client import supabase
                                    
                                    session_response = supabase.auth.exchange_code_for_session({
                                        "auth_code": code
                                    })
                                    
                                    if session_response and session_response.user:
                                        user = session_response.user
                                        access_token = session_response.session.access_token if session_response.session else None
                                        
                                        if access_token:
                                            supabase.postgrest.auth(access_token)
                                        
                                        user_data = supabase.table('users').select('role, full_name, is_active').eq('id', user.id).execute()

                                        role = 'NEW_USER'  # ← MẶC ĐỊNH LÀ NEW_USER
                                        full_name = ''
                                        is_new_user = True

                                        if user_data and user_data.data:
                                            existing_role = user_data.data[0].get('role', 'NEW_USER')
                                            full_name = user_data.data[0].get('full_name', '')
                                            is_active = user_data.data[0].get('is_active', True)
                                            
                                            # Nếu user đã có trong DB và có role khác NEW_USER
                                            if existing_role and existing_role != 'NEW_USER':
                                                role = existing_role
                                                is_new_user = False
                                                
                                                # Kiểm tra tài khoản có bị khóa không
                                                if not is_active:
                                                    raise Exception("Tài khoản đã bị khóa. Vui lòng liên hệ admin.")
                                        else:
                                            # User mới hoàn toàn - tạo bản ghi với role NEW_USER
                                            full_name = user.user_metadata.get('full_name', '') if user.user_metadata else ''
                                            
                                            try:
                                                supabase.table('users').insert({
                                                    'id': user.id,
                                                    'email': user.email,
                                                    'full_name': full_name,
                                                    'role': 'NEW_USER',
                                                    'is_active': True,
                                                    'username': user.email.split('@')[0] if user.email else ''
                                                }).execute()
                                            except Exception as e:
                                                # Có thể user đã tồn tại, bỏ qua lỗi
                                                print(f"[OAuth] Insert user warning: {e}")
                                        
                                        server.user_info = {
                                            'id': user.id,
                                            'email': user.email,
                                            'role': role,
                                            'full_name': full_name
                                        }
                                    else:
                                        server.error = "Failed to exchange authorization code"
                                        
                                except Exception as e:
                                    print(f"[oauth-callback] Code exchange error: {e}")
                                    import traceback
                                    traceback.print_exc()
                                    server.error = str(e)
                            
                        except Exception as e:
                            print(f"[oauth-callback] POST handler error: {e}")
                            import traceback
                            traceback.print_exc()
                            server.error = str(e)

                        self.send_response(200)
                        self.end_headers()
                        self.wfile.write(b'OK')

                def log_message(self, format, *args):
                    pass

            try:
                server = ThreadingHTTPServer(('localhost', 8000), _Handler)
            except Exception as e:
                self._show_error(f"Không thể mở local callback server: {e}")
                return

            server.user_info = None
            server.error = None

            def run_server():
                try:
                    server.serve_forever()
                except Exception:
                    pass

            thread = threading.Thread(target=run_server, daemon=True)
            thread.start()

            try:
                webbrowser.open_new(redirect)
                self._show_info(f"Mở trang {provider} trên trình duyệt. Hoàn tất đăng nhập để tiếp tục.")
            except Exception as ex:
                self._show_error(f"Không thể mở browser: {str(ex)}")
                try:
                    server.shutdown()
                except Exception:
                    pass
                return

            deadline = time.time() + 60
            while time.time() < deadline:
                if server.error:
                    self._show_error(f"Lỗi OAuth: {server.error}")
                    break
                    
                if server.user_info:
                    try:
                        ui = server.user_info
                        from core.auth import UserSession
                        us = UserSession(
                            user_id=ui['id'],
                            email=ui['email'],
                            role=ui['role'],
                            full_name=ui['full_name']
                        )
                        
                        try:
                            if self.page:
                                try:
                                    self.page.run_thread(lambda: self.on_login_success(us))
                                except Exception:
                                    self.on_login_success(us)
                            else:
                                self.on_login_success(us)
                        except Exception as callback_error:
                            print(f"[oauth] Callback error: {callback_error}")
                        
                        break
                        
                    except Exception as e:
                        self._show_error(f"Lỗi xử lý thông tin: {str(e)}")
                        break

                time.sleep(0.5)

            try:
                server.shutdown()
            except Exception:
                pass
                
            if not server.user_info and not server.error:
                self._show_error("Đăng nhập không thành công (hết thời gian chờ). Vui lòng thử lại.")
            
            return

        if isinstance(redirect, UserSession):
            try:
                if self.page:
                    try:
                        self.page.run_thread(lambda: self.on_login_success(redirect))
                    except Exception:
                        self.on_login_success(redirect)
                else:
                    self.on_login_success(redirect)
            except Exception:
                pass
            return

        self._show_error(f"Đăng nhập {provider} thất bại")

    def _show_error(self, message: str) -> None:
        """Show error message"""
        if hasattr(self.message_container.content, 'controls'):
            self.message_container.content.controls[0] = ft.Icon(
                ft.Icons.ERROR_OUTLINE, 
                size=20, 
                color=ft.Colors.RED_700
            )
            self.message_container.content.controls[1].value = message
            self.message_container.content.controls[1].color = ft.Colors.RED_700
        
        self.message_container.bgcolor = ft.Colors.RED_50
        self.message_container.visible = True
        
        if self.page:
            self.page.update()

    def _show_info(self, message: str) -> None:
        """Show info message"""
        if hasattr(self.message_container.content, 'controls'):
            self.message_container.content.controls[0] = ft.Icon(
                ft.Icons.INFO_OUTLINED, 
                size=20, 
                color=ft.Colors.BLUE_700
            )
            self.message_container.content.controls[1].value = message
            self.message_container.content.controls[1].color = ft.Colors.BLUE_700
        
        self.message_container.bgcolor = ft.Colors.BLUE_50
        self.message_container.visible = True
        
        if self.page:
            self.page.update()

    def _show_success(self, message: str) -> None:
        """Show success message"""
        if hasattr(self.message_container.content, 'controls'):
            self.message_container.content.controls[0] = ft.Icon(
                ft.Icons.CHECK_CIRCLE_OUTLINE, 
                size=20, 
                color=ft.Colors.GREEN_700
            )
            self.message_container.content.controls[1].value = message
            self.message_container.content.controls[1].color = ft.Colors.GREEN_700
        
        self.message_container.bgcolor = ft.Colors.GREEN_50
        self.message_container.visible = True
        
        if self.page:
            self.page.update()