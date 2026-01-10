# ui/waiting_approval.py
import flet as ft
import threading
import time
from core.auth import logout
from ui.custom_title_bar import CustomTitleBar
from ui.icon_helper import CustomIcon


class WaitingApprovalView:
    def __init__(self, page: ft.Page, user_email: str, full_name: str):
        self.page = page
        self.user_email = user_email
        self.full_name = full_name
        
        # Message container giống login.py
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
        
        # Loading overlay
        self.loading_overlay = None
        self.main_content = None
    
    def _create_loading_overlay(self):
        """Tạo loading overlay giống login.py"""
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
                    "Đang kiểm tra trạng thái...",
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
            visible=False,
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
    
    def _show_error(self, message: str) -> None:
        """Show error message giống login.py"""
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
        """Show info message giống login.py"""
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
        """Show success message giống login.py"""
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
    
    def build(self) -> ft.Control:
        
        def handle_logout(e):
            logout()
            try:
                self.page.session.clear()
            except:
                if hasattr(self.page, '_user_session'):
                    self.page._user_session.clear()
            
            self.page.controls.clear()
            from ui.login import LoginView
            
            def on_new_login(session):
                from ui.session_helper import set_session_value
                set_session_value(self.page, "user_id", session.user_id)
                set_session_value(self.page, "email", session.email)
                set_session_value(self.page, "role", session.role)
                set_session_value(self.page, "full_name", session.full_name)
                
                # Kiểm tra lại role sau khi login lại
                if session.role == 'NEW_USER':
                    self.page.controls.clear()
                    self.page.add(WaitingApprovalView(self.page, session.email, session.full_name).build())
                else:
                    from ui.main_layout import MainLayout
                    self.page.controls.clear()
                    self.page.add(MainLayout(self.page, session.role))
                
                self.page.update()
            
            login_view = LoginView(on_new_login, self.page)
            self.page.add(login_view.build())
            self.page.update()
        
        def handle_refresh(e):
            """Kiểm tra lại trạng thái tài khoản"""
            self._show_loading_screen()
            
            def do_refresh():
                try:
                    time.sleep(1)
                    
                    # Kiểm tra role trong DB
                    from core.supabase_client import supabase
                    from ui.session_helper import get_session_value
                    
                    user_id = get_session_value(self.page, "user_id")
                    if user_id:
                        user_data = supabase.table('users').select('role, full_name, is_active').eq('id', user_id).execute()
                        
                        if user_data and user_data.data:
                            role = user_data.data[0].get('role', 'NEW_USER')
                            is_active = user_data.data[0].get('is_active', True)
                            
                            if not is_active:
                                if self.page:
                                    self.page.run_thread(self._hide_loading_screen)
                                    self.page.run_thread(lambda: self._show_error("Tài khoản đã bị khóa. Vui lòng liên hệ admin."))
                                return
                            
                            if role != 'NEW_USER':
                                # Đã được duyệt! Chuyển sang màn hình chính
                                from ui.session_helper import set_session_value
                                set_session_value(self.page, "role", role)
                                
                                if self.page:
                                    def switch_to_main():
                                        from ui.main_layout import MainLayout
                                        self.page.controls.clear()
                                        self.page.add(MainLayout(self.page, role))
                                        self.page.update()
                                    
                                    self.page.run_thread(switch_to_main)
                                return
                    
                    # Vẫn chưa được duyệt
                    if self.page:
                        self.page.run_thread(self._hide_loading_screen)
                        self.page.run_thread(lambda: self._show_info("Tài khoản vẫn đang chờ phê duyệt. Vui lòng thử lại sau."))
                    
                except Exception as ex:
                    error_msg = str(ex)
                    if self.page:
                        self.page.run_thread(self._hide_loading_screen)
                        self.page.run_thread(lambda: self._show_error(f"Lỗi kiểm tra: {error_msg}"))
            
            threading.Thread(target=do_refresh, daemon=True).start()
        
        # Custom title bar
        title_bar = CustomTitleBar(
            page=self.page,
            title="HỆ THỐNG QUẢN LÝ ĐOÀN - HỘI",
            logo_path="assets/favicon.ico",
            user_name=self.full_name if self.full_name else "User",
            user_email=self.user_email,
            user_role="NEW_USER",
            on_profile_click=None,
            on_user_management_click=None,
            on_logout_click=handle_logout,
        ).build()
        
        # Logo
        logo = ft.Container(
            content=ft.Image(src="assets/favicon.ico", width=120, height=120),
            alignment=ft.Alignment.CENTER,
            margin=ft.margin.only(bottom=24),
        )
        
        # Main form content - giống login.py
        form_content = ft.Container(
            content=ft.Column([
                logo,
                
                # Icon hourglass
                ft.Container(
                    content=CustomIcon.create(
                        CustomIcon.INFO,
                        size=80,
                        color=ft.Colors.ORANGE_600
                    ),
                    alignment=ft.Alignment.CENTER,
                    margin=ft.margin.only(bottom=20),
                ),
                
                # Title
                ft.Text(
                    "Tài khoản đang chờ phê duyệt",
                    size=28,
                    weight=ft.FontWeight.BOLD,
                    color=ft.Colors.BLACK,
                    text_align=ft.TextAlign.CENTER,
                ),
                
                ft.Container(height=8),
                
                # Subtitle
                ft.Text(
                    f"Xin chào {self.full_name}!",
                    size=16,
                    color=ft.Colors.GREY_800,
                    text_align=ft.TextAlign.CENTER,
                    weight=ft.FontWeight.W_500,
                ),
                
                ft.Container(height=20),
                
                # Description
                ft.Container(
                    content=ft.Column([
                        ft.Text(
                            "Tài khoản của bạn đã được tạo thành công nhưng chưa được kích hoạt.",
                            size=14,
                            color=ft.Colors.GREY_700,
                            text_align=ft.TextAlign.CENTER,
                        ),
                        ft.Container(height=8),
                        ft.Text(
                            "Vui lòng liên hệ với Quản trị viên (Admin) để được cấp quyền truy cập.",
                            size=14,
                            color=ft.Colors.GREY_700,
                            text_align=ft.TextAlign.CENTER,
                            weight=ft.FontWeight.W_500,
                        ),
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=0,
                    ),
                ),
                
                ft.Container(height=24),
                
                # Info box
                ft.Container(
                    content=ft.Column([
                        ft.Row([
                            CustomIcon.create(CustomIcon.INFO, size=18, color=ft.Colors.BLUE_700),
                            ft.Text(
                                "Thông tin tài khoản",
                                size=15,
                                weight=ft.FontWeight.W_600,
                                color=ft.Colors.BLUE_900,
                            ),
                        ], spacing=8),
                        
                        ft.Divider(height=16, color=ft.Colors.BLUE_200),
                        
                        ft.Row([
                            ft.Text("Email:", size=14, weight=ft.FontWeight.W_500, color=ft.Colors.GREY_700, width=80),
                            ft.Text(self.user_email, size=14, color=ft.Colors.BLACK),
                        ], spacing=8),
                        
                        ft.Container(height=8),
                        
                        ft.Row([
                            ft.Text("Trạng thái:", size=14, weight=ft.FontWeight.W_500, color=ft.Colors.GREY_700, width=80),
                            ft.Container(
                                content=ft.Text("Chờ phê duyệt", size=12, color=ft.Colors.WHITE, weight=ft.FontWeight.W_500),
                                bgcolor=ft.Colors.ORANGE_600,
                                padding=ft.padding.symmetric(horizontal=12, vertical=4),
                                border_radius=12,
                            ),
                        ], spacing=8),
                    ],
                    spacing=8,
                    ),
                    padding=16,
                    border_radius=12,
                    bgcolor=ft.Colors.BLUE_50,
                    border=ft.border.all(1, ft.Colors.BLUE_200),
                ),
                
                ft.Container(height=20),
                
                # Message container
                self.message_container,
                
                ft.Container(height=4),
                
                # Refresh button
                ft.ElevatedButton(
                    content=ft.Row([
                        CustomIcon.create(CustomIcon.REFRESH, size=18),
                        ft.Text("Kiểm tra lại", size=15, weight=ft.FontWeight.W_600),
                    ], spacing=8, alignment=ft.MainAxisAlignment.CENTER),
                    on_click=handle_refresh,
                    style=ft.ButtonStyle(
                        color=ft.Colors.WHITE,
                        bgcolor=ft.Colors.BLUE_600,
                        padding=16,
                        shape=ft.RoundedRectangleBorder(radius=12),
                    ),
                    height=56,
                    width=float("inf"),
                ),
                
                ft.Container(height=12),
                
                # Logout button
                ft.ElevatedButton(
                    content=ft.Row([
                        CustomIcon.create(CustomIcon.LOGOUT, size=18),
                        ft.Text("Đăng xuất", size=15, weight=ft.FontWeight.W_600),
                    ], spacing=8, alignment=ft.MainAxisAlignment.CENTER),
                    on_click=handle_logout,
                    style=ft.ButtonStyle(
                        color=ft.Colors.BLACK,
                        bgcolor=ft.Colors.GREY_300,
                        padding=16,
                        shape=ft.RoundedRectangleBorder(radius=12),
                    ),
                    height=56,
                    width=float("inf"),
                ),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=0,
            tight=True,
            ),
            width=520,
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
        
        # Background giống login.py
        background = ft.Container(
            content=ft.Image(
                src="assets/bg.png",
                width=9999,
                height=9999,
                fit="cover",
            ),
            expand=True,
        )
        
        # Main content stack
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
        
        container = ft.Container(
            content=final_stack,
            expand=True,
            padding=0,
            margin=0,
            bgcolor=ft.Colors.WHITE,
        )
        
        return ft.Column(
            spacing=0,
            expand=True,
            horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
            controls=[
                title_bar,
                container,
            ],
        )