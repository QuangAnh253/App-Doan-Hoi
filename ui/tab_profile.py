# ui/tab_profile.py
import flet as ft
import threading
from typing import Optional
from services.profile_service import (
    get_user_profile,
    update_user_profile,
    change_password,
    fetch_all_users,
    count_all_users,
    create_user_account,
    update_user_account,
    delete_user_account,
    activate_user_account,
    reset_user_password,
    get_user_statistics,
    validate_username,
    validate_password_strength,
)
from ui.session_helper import get_user_info
from ui.icon_helper import CustomIcon, icon_button, elevated_button
from core.auth import is_admin


class ProfileTab:
    def __init__(self, page: ft.Page, role: str, dialog_manager=None, message_manager=None):
        self.page = page
        self.role = role
        self.user_info = get_user_info(page)
        self.user_id = self.user_info['user_id']
        
        if dialog_manager is None:
            raise ValueError("dialog_manager is required!")
        self.dialog_manager = dialog_manager
        
        if message_manager is None:
            raise ValueError("message_manager is required!")
        self.message_manager = message_manager
        self.profile_data = None
        self.current_subtab = 0
        self.content = self._build()
    
    # ===================== DIALOG MANAGEMENT =====================
    
    def show_dialog_safe(self, dialog):
        self.dialog_manager.show_dialog(dialog)
    
    def close_child_dialog(self):
        try:
            self.dialog_manager.close_current_dialog()
            self.safe_update()
        except Exception as e:
            print(f"[DIALOG] Close failed: {e}")
    
    def safe_update(self):
        try:
            if hasattr(self.page, 'run_thread'):
                self.page.run_thread(lambda: self.page.update())
            else:
                self.page.update()
        except:
            pass
    
    # ===================== BUILD UI =====================
    
    def _build(self) -> ft.Container:
        self._load_profile_data()
        
        if is_admin(self.role):
            return self._build_admin_view()
        else:
            return self._build_staff_view()
    
    def _load_profile_data(self):
        try:
            if not self.user_id:
                print("[PROFILE] No user_id found in session")
                self.profile_data = {
                    'full_name': self.user_info.get('full_name', 'User'),
                    'email': self.user_info.get('email', ''),
                }
                return
            
            print(f"[PROFILE] Loading profile for user_id: {self.user_id}")
            self.profile_data = get_user_profile(self.user_id)
            print(f"[PROFILE] Profile loaded: {self.profile_data.get('full_name', 'N/A')}")
            
        except Exception as e:
            print(f"[PROFILE] Error loading profile: {e}")
            import traceback
            traceback.print_exc()
            
            self.profile_data = {
                'full_name': self.user_info.get('full_name', 'User'),
                'email': self.user_info.get('email', ''),
            }
    
    # ===================== STAFF VIEW =====================
    
    def _build_staff_view(self) -> ft.Container:
        return ft.Container(
            content=ft.Column([
                self._build_profile_header(),
                ft.Container(height=20),
                self._build_profile_edit_form(),
            ], scroll=ft.ScrollMode.AUTO),
            padding=20,
        )
    
    # ===================== ADMIN VIEW =====================
    
    def _build_admin_view(self) -> ft.Container:
        
        self.profile_tab_btn = self._create_tab_button("Thông tin cá nhân", CustomIcon.PERSON, 0)
        self.user_mgmt_tab_btn = self._create_tab_button("Quản lý tài khoản", CustomIcon.ADMIN, 1)
        
        self._update_tab_button_states()
        
        tab_nav = ft.Container(
            content=ft.Row([
                self.profile_tab_btn,
                self.user_mgmt_tab_btn,
            ], spacing=8),
            padding=ft.padding.only(bottom=16),
        )
        
        self.admin_content_container = ft.Container(expand=True)
        self._switch_admin_tab(self.current_subtab)
        
        return ft.Container(
            content=ft.Column([
                tab_nav,
                self.admin_content_container,
            ], scroll=ft.ScrollMode.AUTO),
            padding=20,
            expand=True,
        )
    
    def _create_tab_button(self, text: str, icon: str, index: int) -> ft.Container:
        return ft.Container(
            content=ft.Row([
                CustomIcon.create(icon, size=18),
                ft.Text(text, size=14),
            ], spacing=8),
            padding=ft.padding.symmetric(horizontal=16, vertical=10),
            border_radius=8,
            on_click=lambda e: self._switch_admin_tab(index),
            ink=True,
        )
    
    def _update_tab_button_states(self):
        if self.current_subtab == 0:
            self.profile_tab_btn.bgcolor = ft.Colors.BLUE_600
            self.profile_tab_btn.content.controls[1].color = ft.Colors.WHITE
            self.user_mgmt_tab_btn.bgcolor = ft.Colors.GREY_300
            self.user_mgmt_tab_btn.content.controls[1].color = ft.Colors.GREY_800
        else:
            self.profile_tab_btn.bgcolor = ft.Colors.GREY_300
            self.profile_tab_btn.content.controls[1].color = ft.Colors.GREY_800
            self.user_mgmt_tab_btn.bgcolor = ft.Colors.BLUE_600
            self.user_mgmt_tab_btn.content.controls[1].color = ft.Colors.WHITE
    
    def _switch_admin_tab(self, index: int):
        self.current_subtab = index
        self._update_tab_button_states()
        
        if index == 0:
            self.admin_content_container.content = ft.Column([
                self._build_profile_header(),
                ft.Container(height=20),
                self._build_profile_edit_form(),
            ], scroll=ft.ScrollMode.AUTO)
        else:
            self.admin_content_container.content = self._build_user_management()
        
        self.safe_update()
    
    # ===================== PROFILE COMPONENTS =====================
    
    def _build_profile_header(self) -> ft.Container:
        avatar_url = self.profile_data.get('avatar_url') if self.profile_data else None
        full_name = self.profile_data.get('full_name', 'User') if self.profile_data else 'User'
        email = self.profile_data.get('email', '') if self.profile_data else ''
        
        return ft.Container(
            content=ft.Row([
                ft.Container(
                    content=ft.CircleAvatar(
                        foreground_image_src=avatar_url if avatar_url else None,
                        content=CustomIcon.create(CustomIcon.PERSON, size=40) if not avatar_url else None,
                        bgcolor=ft.Colors.BLUE_200,
                        radius=50,
                    ),
                ),
                ft.Container(width=20),
                ft.Column([
                    ft.Text(full_name, size=24, weight=ft.FontWeight.BOLD),
                    ft.Text(email, size=14, color=ft.Colors.GREY_600),
                    ft.Text(f"Vai trò: {self.role}", size=12, color=ft.Colors.BLUE_600),
                ], spacing=4),
            ], spacing=16),
            padding=20,
            bgcolor=ft.Colors.WHITE,
            border_radius=12,
        )
    
    def _build_profile_edit_form(self) -> ft.Container:
        
        if not hasattr(self, 'full_name_field'):
            self.full_name_field = ft.TextField(
                label="Họ tên",
                value=self.profile_data.get('full_name', '') if self.profile_data else '',
                border_radius=8,
            )
        
        if not hasattr(self, 'phone_field'):
            self.phone_field = ft.TextField(
                label="Số điện thoại",
                value=self.profile_data.get('phone', '') if self.profile_data else '',
                border_radius=8,
            )
        
        if not hasattr(self, 'department_field'):
            self.department_field = ft.TextField(
                label="Đơn vị",
                value=self.profile_data.get('department', '') if self.profile_data else '',
                border_radius=8,
            )
        
        if not hasattr(self, 'avatar_url_field'):
            self.avatar_url_field = ft.TextField(
                label="Link ảnh đại diện",
                value=self.profile_data.get('avatar_url', '') if self.profile_data else '',
                hint_text="https://...",
                border_radius=8,
            )
        
        if not hasattr(self, 'old_password_field'):
            self.old_password_field = ft.TextField(
                label="Mật khẩu cũ",
                password=True,
                can_reveal_password=True,
                border_radius=8,
            )
        
        if not hasattr(self, 'new_password_field'):
            self.new_password_field = ft.TextField(
                label="Mật khẩu mới",
                password=True,
                can_reveal_password=True,
                border_radius=8,
            )
        
        if not hasattr(self, 'confirm_password_field'):
            self.confirm_password_field = ft.TextField(
                label="Xác nhận mật khẩu mới",
                password=True,
                can_reveal_password=True,
                border_radius=8,
            )
        
        save_profile_btn = elevated_button(
            text="Lưu thay đổi",
            icon_path=CustomIcon.SAVE,
            on_click=self._handle_save_profile,
            icon_size=18,
            style=ft.ButtonStyle(bgcolor=ft.Colors.BLUE_600, color=ft.Colors.WHITE),
        )
        
        change_password_btn = elevated_button(
            text="Đổi mật khẩu",
            icon_path=CustomIcon.LOCK,
            on_click=self._handle_change_password,
            icon_size=18,
            style=ft.ButtonStyle(bgcolor=ft.Colors.ORANGE_600, color=ft.Colors.WHITE),
        )
        
        return ft.Container(
            content=ft.Column([
                ft.Text("Thông tin cá nhân", size=18, weight=ft.FontWeight.BOLD),
                ft.Container(height=10),
                self.full_name_field,
                self.phone_field,
                self.department_field,
                self.avatar_url_field,
                save_profile_btn,
                
                ft.Divider(height=40),
                
                ft.Text("Đổi mật khẩu", size=18, weight=ft.FontWeight.BOLD),
                ft.Container(height=10),
                self.old_password_field,
                self.new_password_field,
                self.confirm_password_field,
                change_password_btn,
                
            ], spacing=12),
            padding=20,
            bgcolor=ft.Colors.WHITE,
            border_radius=12,
        )
    
    def _handle_save_profile(self, e):
        def _process():
            try:
                print("💾 [PROFILE] Saving...")
                
                data = {
                    'full_name': (self.full_name_field.value or '').strip(),
                    'phone': (self.phone_field.value or '').strip(),
                    'department': (self.department_field.value or '').strip(),
                    'avatar_url': (self.avatar_url_field.value or '').strip(),
                }
                
                update_user_profile(self.user_id, data)
                
                print("[PROFILE] Saved")
                
                self.message_manager.success("Lưu thông tin thành công!")
                
            except Exception as ex:
                print(f"[PROFILE] Error: {ex}")
                self.message_manager.error(f"Lỗi: {str(ex)}")
        
        threading.Thread(target=_process, daemon=True).start()
    
    def _handle_change_password(self, e):
        
        old_pwd = self.old_password_field.value
        new_pwd = self.new_password_field.value
        confirm_pwd = self.confirm_password_field.value
        
        email = self.profile_data.get('email', self.user_info['email'])
        is_email_login = '@' in email and not old_pwd
        
        if is_email_login:
            if not new_pwd or not confirm_pwd:
                self.message_manager.warning("Vui lòng điền mật khẩu mới và xác nhận")
                return
        else:
            if not all([old_pwd, new_pwd, confirm_pwd]):
                self.message_manager.warning("Vui lòng điền đầy đủ thông tin")
                return
        
        if new_pwd != confirm_pwd:
            self.message_manager.error("Mật khẩu mới không khớp")
            return
        
        is_valid, msg = validate_password_strength(new_pwd)
        if not is_valid:
            self.message_manager.error(msg)
            return
        
        def _process():
            try:
                if is_email_login:
                    update_user_profile(self.user_id, {'password': new_pwd})
                else:
                    change_password(email, old_pwd, new_pwd)
                
                # Clear fields
                self.old_password_field.value = ""
                self.new_password_field.value = ""
                self.confirm_password_field.value = ""
                self.safe_update()
                
                # ✅ SỬ DỤNG MESSAGE MANAGER
                self.message_manager.success("Đổi mật khẩu thành công!")
                
            except Exception as ex:
                self.message_manager.error(f"Lỗi: {str(ex)}")
        
        threading.Thread(target=_process, daemon=True).start()
    
    # ===================== USER MANAGEMENT =====================
    
    def _build_user_management(self) -> ft.Column:
        """Build user management UI"""
        
        stats = get_user_statistics()
        
        stats_row = ft.Container(
            content=ft.Row([
                self._stat_card("Tổng tài khoản", str(stats['total']), ft.Colors.BLUE_600),
                self._stat_card("Đang hoạt động", str(stats['active']), ft.Colors.GREEN_600),
                self._stat_card("Đã khóa", str(stats['inactive']), ft.Colors.RED_600),
            ], spacing=16, scroll=ft.ScrollMode.AUTO),
            padding=ft.padding.only(bottom=16),
        )
        
        # Search fields
        if not hasattr(self, 'user_search_field'):
            self.user_search_field = ft.TextField(
                label="Tìm kiếm",
                hint_text="Tên, email, MSSV...",
                prefix=CustomIcon.create(CustomIcon.SEARCH, size=16),
                expand=True,
                border_radius=8,
            )
            self.user_search_field.on_submit = lambda e: self._handle_user_search()
        
        if not hasattr(self, 'role_filter_dropdown'):
            self.role_filter_dropdown = ft.Dropdown(
                label="Vai trò",
                options=[
                    ft.dropdown.Option("", "Tất cả"),
                    ft.dropdown.Option("ADMIN", "Admin"),
                    ft.dropdown.Option("STAFF", "Staff"),
                ],
                value="",
                width=150,
            )
            self.role_filter_dropdown.on_change = lambda e: self._handle_user_search()
        
        if not hasattr(self, 'department_filter_dropdown'):
            self.department_filter_dropdown = ft.Dropdown(
                label="Đơn vị",
                options=[
                    ft.dropdown.Option("", "Tất cả"),
                    ft.dropdown.Option("Ban văn phòng", "Ban văn phòng"),
                    ft.dropdown.Option("BCH Đoàn", "BCH Đoàn"),
                    ft.dropdown.Option("BCH Hội", "BCH Hội"),
                ],
                value="",
                width=180,
            )
            self.department_filter_dropdown.on_change = lambda e: self._handle_user_search()
        
        add_user_btn = elevated_button(
            text="Thêm tài khoản",
            icon_path=CustomIcon.PERSON_ADD,
            on_click=self._show_add_user_dialog,
            icon_size=18,
            style=ft.ButtonStyle(bgcolor=ft.Colors.GREEN_600, color=ft.Colors.WHITE),
        )
        
        search_bar = ft.Container(
            content=ft.Row([
                self.user_search_field,
                self.role_filter_dropdown,
                self.department_filter_dropdown,
                add_user_btn,
            ], spacing=12),
            padding=ft.padding.only(bottom=16),
        )
        
        if not hasattr(self, 'user_list_container'):
            self.user_list_container = ft.Container(
                content=ft.Column([], scroll=ft.ScrollMode.AUTO),
                bgcolor=ft.Colors.WHITE,
                border_radius=12,
                padding=16,
                expand=True,
            )
        
        self._load_users()
        
        return ft.Column([
            stats_row,
            search_bar,
            self.user_list_container,
        ], expand=True)
    
    def _stat_card(self, title: str, value: str, color: str) -> ft.Container:
        return ft.Container(
            content=ft.Column([
                ft.Text(title, size=12, color=ft.Colors.GREY_600),
                ft.Text(value, size=32, weight=ft.FontWeight.BOLD, color=color),
            ], spacing=4),
            padding=20,
            bgcolor=ft.Colors.WHITE,
            border_radius=12,
            expand=True,
        )
    
    def _load_users(self):
        """Load users list"""
        try:
            print("📋 [USER_MGMT] Loading users...")
            
            search = self.user_search_field.value if self.user_search_field.value else ""
            role_filter = self.role_filter_dropdown.value if self.role_filter_dropdown.value else ""
            dept_filter = self.department_filter_dropdown.value if self.department_filter_dropdown.value else ""
            
            users = fetch_all_users(
                search=search,
                role_filter=role_filter,
                department_filter=dept_filter,
                page=1,
                page_size=100,
            )
            
            print(f"✅ [USER_MGMT] Loaded {len(users)} users")
            
            user_rows = []
            for user in users:
                user_rows.append(self._build_user_row(user))
            
            if not user_rows:
                user_rows.append(
                    ft.Container(
                        content=ft.Text("Không có dữ liệu", italic=True, color=ft.Colors.GREY_600),
                        padding=20,
                        alignment=ft.alignment.center,
                    )
                )
            
            self.user_list_container.content = ft.Column(user_rows, spacing=8, scroll=ft.ScrollMode.AUTO)
            self.safe_update()
            
        except Exception as e:
            print(f"❌ [USER_MGMT] Error loading users: {e}")
            import traceback
            traceback.print_exc()
    
    def _build_user_row(self, user: dict) -> ft.Container:
        """Build user row"""
        is_active = user.get('is_active', True)
        avatar_url = user.get('avatar_url')
        
        return ft.Container(
            content=ft.Row([
                ft.CircleAvatar(
                    foreground_image_src=avatar_url if avatar_url else None,
                    content=CustomIcon.create(CustomIcon.PERSON, size=24) if not avatar_url else None,
                    bgcolor=ft.Colors.BLUE_200 if is_active else ft.Colors.GREY_400,
                    radius=20,
                ),
                ft.Column([
                    ft.Text(user.get('full_name', ''), size=14, weight=ft.FontWeight.BOLD,
                           color=ft.Colors.BLACK if is_active else ft.Colors.GREY_600),
                    ft.Text(f"{user.get('email', '')} • {user.get('role', 'STAFF')}",
                           size=12, color=ft.Colors.GREY_600),
                    ft.Text(f"MSSV: {user.get('mssv', 'N/A')} • {user.get('department', 'N/A')}",
                           size=11, color=ft.Colors.GREY_500),
                ], spacing=2, expand=True),
                ft.Container(
                    content=ft.Text("Hoạt động" if is_active else "Đã khóa",
                                   size=11, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                    padding=ft.padding.symmetric(horizontal=8, vertical=4),
                    bgcolor=ft.Colors.GREEN_600 if is_active else ft.Colors.RED_600,
                    border_radius=4,
                ),
                icon_button(icon_path=CustomIcon.EDIT, tooltip="Chỉnh sửa",
                           on_click=lambda e, u=user: self._show_edit_user_dialog(u), icon_size=18),
                icon_button(icon_path=CustomIcon.LOCK if is_active else CustomIcon.CHECK,
                           tooltip="Khóa" if is_active else "Mở khóa",
                           on_click=lambda e, u=user: self._toggle_user_status(u), icon_size=18
                           ) if user.get('role') != 'ADMIN' else ft.Container(width=40),
                icon_button(icon_path=CustomIcon.REFRESH, tooltip="Reset mật khẩu",
                           on_click=lambda e, u=user: self._reset_user_password(u), icon_size=18),
            ], spacing=12, alignment=ft.MainAxisAlignment.START),
            padding=12,
            border=ft.border.all(1, ft.Colors.GREY_300),
            border_radius=8,
        )
    
    def _handle_user_search(self):
        """Handle search"""
        self._load_users()
    
    # ===================== USER DIALOGS - ✅ CASE B: CÓ DIALOG =====================
    
    def _show_add_user_dialog(self, e):
        """✅ CASE B - ADD USER"""
        
        full_name_field = ft.TextField(label="Họ tên *", border_radius=8, autofocus=True)
        username_field = ft.TextField(label="Username *", border_radius=8)
        password_field = ft.TextField(label="Mật khẩu", value="Abc@123", border_radius=8)
        role_dropdown = ft.Dropdown(
            label="Vai trò *",
            value="STAFF",
            options=[
                ft.dropdown.Option("ADMIN", "Admin"),
                ft.dropdown.Option("STAFF", "Staff"),
            ],
            border_radius=8,
        )
        mssv_field = ft.TextField(label="MSSV", border_radius=8)
        chuc_vu_field = ft.TextField(label="Chức vụ", border_radius=8)
        department_field = ft.TextField(label="Đơn vị", border_radius=8)
        email_field = ft.TextField(label="Email", hint_text="Tùy chọn", border_radius=8)
        phone_field = ft.TextField(label="Số điện thoại", border_radius=8)
        ghi_chu_field = ft.TextField(label="Ghi chú", multiline=True, min_lines=2, border_radius=8)
        
        def handle_cancel(e):
            self.close_child_dialog()
        
        def handle_create(e):
            """✅ FLOW: 1) Đóng dialog, 2) Reload, 3) Message"""
            
            # Validate
            if not full_name_field.value or not full_name_field.value.strip():
                self.message_manager.warning("Vui lòng điền họ tên")
                return
            
            if not username_field.value or not username_field.value.strip():
                self.message_manager.warning("Vui lòng điền username")
                return
            
            if not validate_username(username_field.value.strip()):
                self.message_manager.error("Username không hợp lệ (3-30 ký tự, chỉ chữ, số, _, .)")
                return
            
            # ✅ 1. ĐÓNG DIALOG
            self.close_child_dialog()
            
            def _process():
                try:
                    data = {
                        'full_name': full_name_field.value.strip(),
                        'username': username_field.value.strip(),
                        'password': password_field.value.strip() if password_field.value else 'Abc@123',
                        'role': role_dropdown.value,
                        'mssv': mssv_field.value.strip() if mssv_field.value else '',
                        'chuc_vu': chuc_vu_field.value.strip() if chuc_vu_field.value else '',
                        'department': department_field.value.strip() if department_field.value else '',
                        'email': email_field.value.strip() if email_field.value else '',
                        'phone': phone_field.value.strip() if phone_field.value else '',
                        'ghi_chu': ghi_chu_field.value.strip() if ghi_chu_field.value else '',
                    }
                    
                    create_user_account(data)
                    
                    # ✅ 2. RELOAD
                    def _reload():
                        self._load_users()
                    
                    if hasattr(self.page, 'run_thread'):
                        self.page.run_thread(_reload)
                    else:
                        _reload()
                    
                    # ✅ 3. MESSAGE MANAGER
                    message = f"Tạo tài khoản thành công!\nUsername: {data['username']} | Mật khẩu: {data['password']}"
                    self.message_manager.success(message, duration=4000)
                    
                except Exception as ex:
                    self.message_manager.error(str(ex))
            
            threading.Thread(target=_process, daemon=True).start()
        
        cancel_btn = ft.TextButton(content=ft.Text("Hủy", size=14), on_click=handle_cancel)
        create_btn = ft.ElevatedButton(
            content=ft.Row([
                CustomIcon.create(CustomIcon.PERSON_ADD, size=16),
                ft.Text("Tạo", size=14, weight=ft.FontWeight.W_500)
            ], spacing=6, tight=True),
            on_click=handle_create,
            bgcolor=ft.Colors.GREEN_600,
            color=ft.Colors.WHITE,
        )
        
        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Row([
                CustomIcon.create(CustomIcon.PERSON_ADD, 24),
                ft.Text("Thêm tài khoản mới", size=18, weight=ft.FontWeight.BOLD)
            ], spacing=10),
            content=ft.Container(
                width=550,
                content=ft.Column([
                    full_name_field, username_field, password_field, role_dropdown,
                    mssv_field, chuc_vu_field, department_field, email_field, 
                    phone_field, ghi_chu_field,
                ], spacing=12, scroll=ft.ScrollMode.AUTO),
                height=500,
            ),
            actions=[cancel_btn, create_btn],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        
        self.show_dialog_safe(dialog)
    
    def _show_edit_user_dialog(self, user: dict):
        """✅ CASE B - EDIT USER (CHUẨN MESSAGE MANAGER)"""

        # ===== Fields =====
        full_name_field = ft.TextField(
            label="Họ tên",
            value=user.get("full_name", ""),
            border_radius=8,
            autofocus=True,
        )
        mssv_field = ft.TextField(label="MSSV", value=user.get("mssv") or "", border_radius=8)
        chuc_vu_field = ft.TextField(label="Chức vụ", value=user.get("chuc_vu") or "", border_radius=8)
        department_field = ft.TextField(label="Đơn vị", value=user.get("department") or "", border_radius=8)
        email_field = ft.TextField(label="Email", value=user.get("email") or "", border_radius=8)
        phone_field = ft.TextField(label="Số điện thoại", value=user.get("phone") or "", border_radius=8)
        role_dropdown = ft.Dropdown(
            label="Vai trò",
            value=user.get("role", "STAFF"),
            options=[
                ft.dropdown.Option("ADMIN", "Admin"),
                ft.dropdown.Option("STAFF", "Staff"),
            ],
            border_radius=8,
        )
        ghi_chu_field = ft.TextField(
            label="Ghi chú",
            value=user.get("ghi_chu") or "",
            multiline=True,
            min_lines=2,
            border_radius=8,
        )

        # ===== Actions =====
        def handle_cancel(e):
            self.close_child_dialog()

        def handle_update(e):
            """✅ FLOW CHUẨN:
            1) Đóng dialog
            2) Background update
            3) Reload list
            4) Message qua MessageManager
            """

            # ✅ 1. Đóng dialog NGAY
            self.close_child_dialog()

            def _process():
                try:
                    data = {
                        "full_name": full_name_field.value.strip() if full_name_field.value else "",
                        "mssv": mssv_field.value.strip() if mssv_field.value else "",
                        "chuc_vu": chuc_vu_field.value.strip() if chuc_vu_field.value else "",
                        "department": department_field.value.strip() if department_field.value else "",
                        "email": email_field.value.strip() if email_field.value else "",
                        "phone": phone_field.value.strip() if phone_field.value else "",
                        "role": role_dropdown.value,
                        "ghi_chu": ghi_chu_field.value.strip() if ghi_chu_field.value else "",
                    }

                    update_user_account(user["id"], data)

                    # ✅ 2. Reload danh sách (UI thread)
                    def _reload():
                        self._load_users()

                    if hasattr(self.page, "run_thread"):
                        self.page.run_thread(_reload)
                    else:
                        _reload()

                    # ✅ 3. Message (GLOBAL – không phụ thuộc dialog)
                    self.message_manager.success(
                        f"Cập nhật tài khoản '{user.get('full_name')}' thành công!"
                    )

                except Exception as ex:
                    self.message_manager.error(f"Lỗi cập nhật: {str(ex)}")

            threading.Thread(target=_process, daemon=True).start()

        # ===== Buttons =====
        cancel_btn = ft.TextButton("Hủy", on_click=handle_cancel)

        update_btn = ft.ElevatedButton(
            content=ft.Row(
                [
                    CustomIcon.create(CustomIcon.SAVE, size=16),
                    ft.Text("Lưu"),
                ],
                spacing=6,
                tight=True,
            ),
            on_click=handle_update,
            bgcolor=ft.Colors.BLUE_600,
            color=ft.Colors.WHITE,
        )

        # ===== Dialog =====
        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text(
                f"Sửa tài khoản: {user.get('full_name')}",
                size=18,
                weight=ft.FontWeight.BOLD,
            ),
            content=ft.Container(
                width=550,
                height=460,
                content=ft.Column(
                    [
                        full_name_field,
                        mssv_field,
                        chuc_vu_field,
                        department_field,
                        email_field,
                        phone_field,
                        role_dropdown,
                        ghi_chu_field,
                    ],
                    spacing=12,
                    scroll=ft.ScrollMode.AUTO,
                ),
            ),
            actions=[cancel_btn, update_btn],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        # ✅ Mở dialog qua DialogManager
        self.show_dialog_safe(dialog)

    def _toggle_user_status(self, user: dict):
        """✅ CASE B - TOGGLE STATUS (LOCK / UNLOCK USER)"""

        is_active = user.get('is_active', True)
        action_text = "khóa" if is_active else "mở khóa"

        def handle_cancel(e):
            self.close_child_dialog()

        def handle_confirm(e):
            # ✅ 1. ĐÓNG CHILD DIALOG TRƯỚC
            self.close_child_dialog()

            def _process():
                try:
                    # ✅ 2. BACKEND ACTION
                    if is_active:
                        delete_user_account(user['id'])
                    else:
                        activate_user_account(user['id'])

                    # ✅ 3. RELOAD USER LIST
                    def _reload():
                        self._load_users()

                    if hasattr(self.page, 'run_thread'):
                        self.page.run_thread(_reload)
                    else:
                        _reload()

                    # ✅ 4. MESSAGE MANAGER (HIỂN THỊ Ở MAIN_LAYOUT)
                    self.message_manager.success(
                        f"{action_text.capitalize()} tài khoản "
                        f"{user.get('full_name')} thành công!"
                    )

                except Exception as ex:
                    self.message_manager.error(f"Lỗi: {str(ex)}")

            threading.Thread(target=_process, daemon=True).start()

        cancel_btn = ft.TextButton("Hủy", on_click=handle_cancel)
        confirm_btn = ft.ElevatedButton(
            content=ft.Row([
                CustomIcon.create(
                    CustomIcon.LOCK if is_active else CustomIcon.CHECK,
                    size=16
                ),
                ft.Text("Xác nhận"),
            ], spacing=6),
            on_click=handle_confirm,
            bgcolor=ft.Colors.RED_600 if is_active else ft.Colors.GREEN_600,
            color=ft.Colors.WHITE,
        )

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text(f"Xác nhận {action_text}"),
            content=ft.Column([
                ft.Text(
                    f"Bạn có chắc muốn {action_text} tài khoản này?",
                    size=14
                ),
                ft.Container(height=8),
                ft.Container(
                    content=ft.Column([
                        ft.Text(f"• {user.get('full_name')}", size=13),
                        ft.Text(f"• {user.get('email')}", size=13),
                        ft.Text(f"• Vai trò: {user.get('role')}", size=13),
                    ], spacing=4),
                    bgcolor=ft.Colors.GREY_100,
                    padding=12,
                    border_radius=8,
                ),
            ], spacing=0, tight=True),
            actions=[cancel_btn, confirm_btn],
        )

        self.show_dialog_safe(dialog)

    
    def _reset_user_password(self, user: dict):
        """✅ CASE B - RESET PASSWORD"""

        def handle_cancel(e):
            self.close_child_dialog()

        def handle_reset(e):
            # ✅ 1. ĐÓNG CHILD DIALOG
            self.close_child_dialog()

            def _process():
                try:
                    reset_user_password(user['id'])

                    # ✅ 2. MESSAGE MANAGER (KHÔNG CẦN RELOAD)
                    self.message_manager.success(
                        f"Reset mật khẩu thành công!\n"
                        f"Tài khoản: {user.get('full_name')}\n"
                        f"Mật khẩu mới: Abc@123",
                        duration=4000
                    )

                except Exception as ex:
                    self.message_manager.error(f"Lỗi: {str(ex)}")

            threading.Thread(target=_process, daemon=True).start()

        cancel_btn = ft.TextButton("Hủy", on_click=handle_cancel)
        reset_btn = ft.ElevatedButton(
            content=ft.Row([
                CustomIcon.create(CustomIcon.REFRESH, size=16),
                ft.Text("Reset"),
            ], spacing=6),
            on_click=handle_reset,
            bgcolor=ft.Colors.ORANGE_600,
            color=ft.Colors.WHITE,
        )

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Reset mật khẩu"),
            content=ft.Column([
                ft.Text(
                    f"Reset mật khẩu cho: {user.get('full_name')}",
                    size=14
                ),
                ft.Container(height=12),
                ft.Container(
                    content=ft.Column([
                        ft.Text(
                            "Mật khẩu mới: Abc@123",
                            size=14,
                            weight=ft.FontWeight.BOLD,
                            color=ft.Colors.ORANGE_700,
                        ),
                        ft.Container(height=4),
                        ft.Text(
                            "User sẽ cần đổi mật khẩu sau lần đăng nhập đầu tiên",
                            size=11,
                            italic=True,
                        ),
                    ]),
                    bgcolor=ft.Colors.ORANGE_50,
                    padding=12,
                    border_radius=8,
                ),
            ], spacing=0, tight=True),
            actions=[cancel_btn, reset_btn],
        )

        self.show_dialog_safe(dialog)
