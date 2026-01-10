# ui/main_layout.py
import flet as ft
import asyncio
from core.auth import is_admin, logout
from ui.tab_students import StudentsTab
from ui.tab_classes import ClassesTab
from ui.tab_staff import StaffTab
from ui.tab_noi_bo import NoiBoTab
from ui.tab_luu_tru import LuuTruTab
from ui.tab_profile import ProfileTab
from ui.icon_helper import CustomIcon, icon_button
from ui.session_helper import get_session_value, set_session_value, get_user_info, debug_session
from ui.dialog_manager import DialogManager
from ui.message_manager import MessageManager
from ui.custom_title_bar import CustomTitleBar


def MainLayout(page: ft.Page, role: str):
    
    user_info = get_user_info(page)
    full_name = user_info['full_name']
    email = user_info['email']
    session_role = user_info['role']
    
    actual_role = session_role if session_role else role
    
    if not full_name:
        full_name = "User"
    if not email:
        email = ""

    dialog_manager = DialogManager(page)

    def show_profile_popup(e):
        try:
            dialog_content = ft.Container(width=850, height=600)
            message_manager = MessageManager(page, dialog_content)
            profile_dialog = ft.AlertDialog(
                modal=True,
                title=ft.Row([
                    CustomIcon.create(CustomIcon.PERSON, size=24),
                    ft.Text("Tài khoản cá nhân", size=18, weight=ft.FontWeight.BOLD),
                ], spacing=12),
                content=dialog_content,
                actions=[],
                actions_alignment=ft.MainAxisAlignment.END,
            )
            profile_tab = ProfileTab(
                page, 
                actual_role, 
                dialog_manager=dialog_manager,
                message_manager=message_manager
            )
            dialog_content.content = profile_tab.content

            close_btn = ft.ElevatedButton(
                "Đóng",
                on_click=lambda _: dialog_manager.close_current_dialog(),
                style=ft.ButtonStyle(bgcolor=ft.Colors.GREY_300),
            )
            profile_dialog.actions = [close_btn]
            
            if is_admin(actual_role) and hasattr(profile_tab, '_switch_admin_tab'):
                profile_tab.current_subtab = 0
                profile_tab._switch_admin_tab(0)
            dialog_manager.show_dialog(profile_dialog)
            
        except Exception as ex:
            print(f"[POPUP] Error: {ex}")
            import traceback
            traceback.print_exc()

            page.snack_bar = ft.SnackBar(
                content=ft.Text(f"Lỗi: {str(ex)}"),
                bgcolor=ft.Colors.RED,
            )
            page.snack_bar.open = True
            page.update()

    def show_user_management_popup(e):
        try:
            dialog_content = ft.Container(width=1000, height=650)
            message_manager = MessageManager(page, dialog_content)

            mgmt_dialog = ft.AlertDialog(
                modal=True,
                title=ft.Row([
                    CustomIcon.create(CustomIcon.ADMIN, size=24),
                    ft.Text("Quản lý tài khoản", size=18, weight=ft.FontWeight.BOLD),
                ], spacing=12),
                content=dialog_content,
                actions=[],
                actions_alignment=ft.MainAxisAlignment.END,
            )

            profile_tab = ProfileTab(
                page, 
                actual_role, 
                dialog_manager=dialog_manager,
                message_manager=message_manager
            )
            
            dialog_content.content = profile_tab.content
            
            close_btn = ft.ElevatedButton(
                "Đóng",
                on_click=lambda _: dialog_manager.close_current_dialog(),
                style=ft.ButtonStyle(bgcolor=ft.Colors.GREY_300),
            )
            mgmt_dialog.actions = [close_btn]

            if hasattr(profile_tab, '_switch_admin_tab'):
                profile_tab.current_subtab = 1
                profile_tab._switch_admin_tab(1)
            
            dialog_manager.show_dialog(mgmt_dialog)
            
        except Exception as ex:
            import traceback
            traceback.print_exc()
            
            page.snack_bar = ft.SnackBar(
                content=ft.Text(f"Lỗi: {str(ex)}"),
                bgcolor=ft.Colors.RED,
            )
            page.snack_bar.open = True
            page.update()

    def handle_logout(e):
        dialog_manager.close_all_dialogs()
        
        logout()
        try:
            page.session.clear()
        except:
            if hasattr(page, '_user_session'):
                page._user_session.clear()
        
        page.controls.clear()
        from ui.login import LoginView
        
        def on_new_login(session):
            set_session_value(page, "user_id", session.user_id)
            set_session_value(page, "email", session.email)
            set_session_value(page, "role", session.role)
            set_session_value(page, "full_name", session.full_name)
            
            page.controls.clear()
            page.add(MainLayout(page, session.role))
            page.update()
        
        login_view = LoginView(on_new_login, page)
        page.add(login_view.build())
        page.update()

    user_menu_items = [
        ft.PopupMenuItem(
            content=ft.Row([
                CustomIcon.create(CustomIcon.PERSON, size=18),
                ft.Text("Tài khoản cá nhân", size=13),
            ], spacing=8),
            on_click=show_profile_popup,
        ),
    ]
    
    if is_admin(actual_role):
        user_menu_items.append(
            ft.PopupMenuItem(
                content=ft.Row([
                    CustomIcon.create(CustomIcon.ADMIN, size=18),
                    ft.Text("Quản lý tài khoản", size=13),
                ], spacing=8),
                on_click=show_user_management_popup,
            )
        )
    
    user_menu_items.append(ft.Divider())
    user_menu_items.append(
        ft.PopupMenuItem(
            content=ft.Row([
                CustomIcon.create(CustomIcon.LOGOUT, size=18),
                ft.Text("Đăng xuất", size=13),
            ], spacing=8),
            on_click=handle_logout,
        )
    )
    

    # CUSTOM TITLE BAR
    title_bar = CustomTitleBar(
        page=page,
        title="HỆ THỐNG QUẢN LÝ ĐOÀN - HỘI",
        logo_path="assets/favicon.ico",
        user_name=full_name,
        user_email=email,
        user_role=actual_role,
        on_profile_click=show_profile_popup,
        on_user_management_click=show_user_management_popup if is_admin(actual_role) else None,
        on_logout_click=handle_logout,
    ).build()

    tab_state = {"current_index": 0}
    tab_content_container = ft.Container(expand=True)
    
    tab_configs = [
        {
            "name": "Quản lý Sinh viên",
            "icon": CustomIcon.PEOPLE,
            "content": StudentsTab(page, actual_role),
            "visible": True,
        },
        {
            "name": "Quản lý Lớp",
            "icon": CustomIcon.CLASS,
            "content": ClassesTab(page, actual_role),
            "visible": actual_role in ["ADMIN", "STAFF"],
        },
        {
            "name": "Cán bộ lớp",
            "icon": CustomIcon.ADMIN,
            "content": StaffTab(page, actual_role),
            "visible": True,
        },
        {
            "name": "Nội bộ",
            "icon": CustomIcon.INFO,
            "content": NoiBoTab(page, actual_role),
            "visible": actual_role in ["ADMIN", "STAFF"],
        },
        {
            "name": "Lưu trữ",
            "icon": CustomIcon.STORAGE,
            "content": LuuTruTab(page, actual_role),
            "visible": actual_role in ["ADMIN", "STAFF"],
        },
    ]
    
    visible_tabs = [t for t in tab_configs if t["visible"]]
    
    tab_buttons = []
    
    def switch_tab(index):
        """Chuyển đổi tab"""
        dialog_manager.close_all_dialogs()
        
        tab_state["current_index"] = index
        tab_content_container.content = visible_tabs[index]["content"]
        
        for i, btn in enumerate(tab_buttons):
            if i == index:
                btn.bgcolor = ft.Colors.BLUE_600
                btn.content.controls[1].color = ft.Colors.WHITE
            else:
                btn.bgcolor = ft.Colors.GREY_300
                btn.content.controls[1].color = ft.Colors.GREY_800
        
        page.update()
    
    for i, tab in enumerate(visible_tabs):
        btn = ft.Container(
            content=ft.Row(
                [
                    CustomIcon.create(tab["icon"], size=18),
                    ft.Text(
                        tab["name"], 
                        size=14,
                        color=ft.Colors.WHITE if i == 0 else ft.Colors.GREY_800
                    ),
                ],
                spacing=8,
            ),
            padding=ft.padding.symmetric(horizontal=20, vertical=12),
            border_radius=8,
            bgcolor=ft.Colors.BLUE_600 if i == 0 else ft.Colors.GREY_300,
            on_click=lambda e, idx=i: switch_tab(idx),
            ink=True,
        )
        tab_buttons.append(btn)
    
    tab_nav = ft.Container(
        content=ft.Row(
            controls=tab_buttons,
            spacing=8,
            scroll=ft.ScrollMode.AUTO,
        ),
        padding=ft.padding.all(12),
        bgcolor=ft.Colors.WHITE,
        border=ft.border.only(bottom=ft.BorderSide(1, ft.Colors.GREY_300)),
    )
    
    tab_content_container.content = visible_tabs[0]["content"]
    tab_content_container.bgcolor = ft.Colors.GREY_100
    tab_content_container.padding = ft.padding.all(20)
    
    return ft.Column(
        spacing=0,
        expand=True,
        horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
        controls=[
            title_bar,
            tab_nav,
            tab_content_container,
        ],
    )


def ensure_fullscreen_on_activate(page: ft.Page) -> None:
    async def _apply_maximize():
        delays = [0.01, 0.1, 0.3, 0.8, 1.5]
        
        for delay in delays:
            await asyncio.sleep(delay)
            
            try:
                if hasattr(page, 'window'):
                    try:
                        page.window.full_screen = False
                    except:
                        pass
                    try:
                        page.window.maximized = True
                    except:
                        pass
                    try:
                        page.window.resizable = True
                    except:
                        pass
                
                if hasattr(page, 'window_maximized'):
                    try:
                        page.window_maximized = True
                    except:
                        pass
                
                page.update()
            except:
                pass
    
    page.run_task(_apply_maximize)