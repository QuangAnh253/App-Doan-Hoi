# ui/custom_title_bar.py
import flet as ft
from ui.icon_helper import CustomIcon


class CustomTitleBar:
    def __init__(
        self,
        page: ft.Page,
        title: str = "Hệ thống quản lý Đoàn - Hội",
        logo_path: str = "assets/favicon.ico",
        user_name: str = "User",
        user_email: str = "",
        user_role: str = "STAFF",
        on_profile_click=None,
        on_user_management_click=None,
        on_logout_click=None,
    ):
        self.page = page
        self.title = title
        self.logo_path = logo_path
        self.user_name = user_name
        self.user_email = user_email
        self.user_role = user_role
        self.on_profile_click = on_profile_click
        self.on_user_management_click = on_user_management_click
        self.on_logout_click = on_logout_click
        
    def build(self) -> ft.Container: 
        logo_widget = ft.Image(
            src=self.logo_path,
            width=36,
            height=36,
            fit="contain",
        )
        left_content = ft.Row(
            [
                logo_widget,
                ft.Text(
                    self.title,
                    size=15,
                    weight=ft.FontWeight.W_600,
                    color=ft.Colors.WHITE,
                ),
            ],
            spacing=12,
            alignment=ft.MainAxisAlignment.START,
        )
        draggable_area = ft.WindowDragArea(
            content=left_content,
            expand=True,
        )
        
        # Helper function để mở link
        def open_url(url: str):
            def _handler(e):
                try:
                    import webbrowser
                    webbrowser.open(url)
                except Exception as ex:
                    print(f"[TITLE_BAR] Error opening URL: {ex}")
            return _handler
        
        # Menu items luôn hiển thị (public)
        public_menu_items = [
            ft.PopupMenuItem(
                content=ft.Row([
                    CustomIcon.create(CustomIcon.DOCUMENT, size=16),
                    ft.Text("Hướng dẫn sử dụng", size=13),
                ], spacing=8),
                on_click=open_url("https://appdoanhoi.lequanganh.id.vn/guidelines"),
            ),
            ft.PopupMenuItem(
                content=ft.Row([
                    CustomIcon.create(CustomIcon.INFO, size=16),
                    ft.Text("About App", size=13),
                ], spacing=8),
                on_click=open_url("https://appdoanhoi.lequanganh.id.vn/"),
            ),
            ft.Divider(height=1),
        ]
        
        # Menu items cho user đã login
        user_menu_items = []
        
        user_menu_items.append(
            ft.PopupMenuItem(
                content=ft.Row([
                    CustomIcon.create(CustomIcon.PERSON, size=16),
                    ft.Text("Tài khoản cá nhân", size=13),
                ], spacing=8),
                on_click=self.on_profile_click,
            )
        )
        
        if self.user_role == "ADMIN":
            user_menu_items.append(
                ft.PopupMenuItem(
                    content=ft.Row([
                        CustomIcon.create(CustomIcon.ADMIN, size=16),
                        ft.Text("Quản lý tài khoản", size=13),
                    ], spacing=8),
                    on_click=self.on_user_management_click,
                )
            )
        
        user_menu_items.append(ft.Divider(height=1))
        user_menu_items.append(
            ft.PopupMenuItem(
                content=ft.Row([
                    CustomIcon.create(CustomIcon.LOGOUT, size=16),
                    ft.Text("Đăng xuất", size=13, color=ft.Colors.RED_400),
                ], spacing=8),
                on_click=self.on_logout_click,
            )
        )
        
        # Kết hợp: public items + user items
        all_menu_items = public_menu_items + user_menu_items
        
        user_menu = ft.PopupMenuButton(
            content=ft.Container(
                content=ft.Row([
                    ft.Container(
                        content=ft.Icon(
                            ft.Icons.ACCOUNT_CIRCLE,
                            size=26,
                            color=ft.Colors.WHITE,
                        ),
                        padding=ft.padding.only(right=8),
                    ),
                    ft.Column(
                        [
                            ft.Text(
                                self.user_name,
                                size=13,
                                weight=ft.FontWeight.W_600,
                                color=ft.Colors.WHITE,
                            ),
                            ft.Text(
                                f"{self.user_role} • {self.user_email}",
                                size=10,
                                color=ft.Colors.with_opacity(0.75, ft.Colors.WHITE),
                            ),
                        ],
                        spacing=2,
                        tight=True,
                    ),
                ], spacing=0, tight=True),
                padding=ft.padding.symmetric(horizontal=14, vertical=6),
                border_radius=8,
                shadow=ft.BoxShadow(
                    spread_radius=0,
                    blur_radius=8,
                    color=ft.Colors.with_opacity(0.3, ft.Colors.BLACK),
                    offset=ft.Offset(0, 2),
                ),
                bgcolor=ft.Colors.with_opacity(0.1, ft.Colors.WHITE),
                border=ft.border.all(1, ft.Colors.with_opacity(0.2, ft.Colors.WHITE)),
                animate=ft.Animation(150, ft.AnimationCurve.EASE_OUT),
            ),
            items=all_menu_items,
            menu_position=ft.PopupMenuPosition.UNDER,
        )
        
        def on_profile_hover(e):
            if e.data == "true":
                e.control.content.bgcolor = ft.Colors.with_opacity(0.2, ft.Colors.WHITE)
                e.control.content.shadow = ft.BoxShadow(
                    spread_radius=1,
                    blur_radius=12,
                    color=ft.Colors.with_opacity(0.4, ft.Colors.BLACK),
                    offset=ft.Offset(0, 3),
                )
            else:
                e.control.content.bgcolor = ft.Colors.with_opacity(0.1, ft.Colors.WHITE)
                e.control.content.shadow = ft.BoxShadow(
                    spread_radius=0,
                    blur_radius=8,
                    color=ft.Colors.with_opacity(0.3, ft.Colors.BLACK),
                    offset=ft.Offset(0, 2),
                )
            e.control.update()
        
        user_menu.on_hover = on_profile_hover
        
        window_controls = ft.Row(
            [
                ft.IconButton(
                    icon=ft.Icons.MINIMIZE,
                    icon_size=16,
                    icon_color=ft.Colors.WHITE,
                    tooltip="Thu nhỏ",
                    on_click=self._minimize_window,
                    style=ft.ButtonStyle(
                        padding=0,
                        shape=ft.RoundedRectangleBorder(radius=0),
                        overlay_color={
                            ft.ControlState.HOVERED: ft.Colors.with_opacity(0.15, ft.Colors.WHITE),
                        },
                    ),
                    width=52,
                    height=52,
                ),
                ft.IconButton(
                    icon=ft.Icons.CROP_SQUARE,
                    icon_size=16,
                    icon_color=ft.Colors.WHITE,
                    tooltip="Phóng to / Thu nhỏ",
                    on_click=self._toggle_maximize_window,
                    style=ft.ButtonStyle(
                        padding=0,
                        shape=ft.RoundedRectangleBorder(radius=0),
                        overlay_color={
                            ft.ControlState.HOVERED: ft.Colors.with_opacity(0.15, ft.Colors.WHITE),
                        },
                    ),
                    width=52,
                    height=52,
                ),
                ft.IconButton(
                    icon=ft.Icons.CLOSE,
                    icon_size=16,
                    icon_color=ft.Colors.WHITE,
                    tooltip="Đóng",
                    on_click=self._close_window,
                    style=ft.ButtonStyle(
                        padding=0,
                        shape=ft.RoundedRectangleBorder(radius=0),
                        overlay_color={
                            ft.ControlState.HOVERED: ft.Colors.RED_600,
                        },
                    ),
                    width=52,
                    height=52,
                ),
            ],
            spacing=0,
            tight=True,
        )
        title_bar = ft.Container(
            content=ft.Row(
                [
                    draggable_area,
                    user_menu,
                    window_controls,
                ],
                spacing=12,
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            height=52,
            bgcolor="#2C2C2C",
            padding=ft.padding.only(left=12, right=0),
            shadow=ft.BoxShadow(
                spread_radius=0,
                blur_radius=4,
                color=ft.Colors.with_opacity(0.3, ft.Colors.BLACK),
                offset=ft.Offset(0, 2),
            ),
        )
        
        return title_bar
    
    def _minimize_window(self, e):
        try:
            if hasattr(self.page, 'window') and hasattr(self.page.window, 'minimized'):
                self.page.window.minimized = True
            elif hasattr(self.page, 'window_minimized'):
                self.page.window_minimized = True
            self.page.update()
        except Exception as ex:
            print(f"[TITLE_BAR] Minimize error: {ex}")
    
    def _toggle_maximize_window(self, e):
        try:
            if hasattr(self.page, 'window') and hasattr(self.page.window, 'maximized'):
                self.page.window.maximized = not self.page.window.maximized
            elif hasattr(self.page, 'window_maximized'):
                self.page.window_maximized = not self.page.window_maximized
            self.page.update()
        except Exception as ex:
            print(f"[TITLE_BAR] Maximize error: {ex}")
    
    def _close_window(self, e):
        try:
            import asyncio
            
            async def _async_close():
                try:
                    if hasattr(self.page, 'window') and hasattr(self.page.window, 'close'):
                        close_fn = self.page.window.close
                        if asyncio.iscoroutinefunction(close_fn):
                            await close_fn()
                        else:
                            close_fn()
                    elif hasattr(self.page, 'window_close'):
                        self.page.window_close()
                    else:
                        if hasattr(self.page, 'window') and hasattr(self.page.window, 'destroy'):
                            self.page.window.destroy()
                except Exception as ex:
                    print(f"[TITLE_BAR] Async close error: {ex}")
                    import sys
                    sys.exit(0)
            
            self.page.run_task(_async_close)
            
        except Exception as ex:
            print(f"[TITLE_BAR] Close error: {ex}")
            import sys
            sys.exit(0)