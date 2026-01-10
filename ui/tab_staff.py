# ui/tab_staff.py
import flet as ft
import asyncio
from services.staff_service import (
    fetch_staff_with_filters,
    count_staff_with_filters,
    update_staff,
    bulk_update_staff,
    create_staff,
    delete_staff,
)
from core.auth import is_admin
from ui.icon_helper import CustomIcon, elevated_button
from ui.message_manager import MessageManager

PAGE_SIZE = 100

CHUC_VU_LIST = [
    "Lớp trưởng",
    "Lớp phó",
    "Lớp phó học tập",
    "Lớp phó đời sống",
    "Bí thư chi đoàn",
    "Phó BT chi đoàn",
    "Ủy viên BCH chi đoàn",
    "Chi hội trưởng",
    "Chi hội phó",
    "Ủy viên BCH chi hội",
]

CHUC_VU_ORDER = {
    "Lớp trưởng": 1,
    "lớp trưởng": 1,
    "Lop truong": 1,
    "Lớp phó": 2,
    "lớp phó": 2,
    "Lop pho": 2,
    "phó lớp": 2,
    "pho lop": 2,
    "Lớp  phó": 2,
    "lop  pho": 2,
    "Lớp phó học tập": 3,
    "lớp phó học tập": 3,
    "Lop pho hoc tap": 3,
    "phó lớp học tập": 3,
    "pho lop hoc tap": 3,
    "Lớp phó đời sống": 4,
    "lớp phó đời sống": 4,
    "Lop pho doi song": 4,
    "phó lớp đời sống": 4,
    "pho lop doi song": 4,
    "Bí thư chi đoàn": 5,
    "Bí thư chi Đoàn": 5,
    "bí thư chi đoàn": 5,
    "Bi thu chi doan": 5,
    "Phó BT chi đoàn": 6,
    "Phó BT chi Đoàn": 6,
    "phó BT chi đoàn": 6,
    "Pho BT chi doan": 6,
    "Ủy viên BCH chi đoàn": 7,
    "Uỷ viên BCH chi đoàn": 7,
    "ủy viên BCH chi đoàn": 7,
    "Uy vien BCH chi doan": 7,
    "Chi hội trưởng": 8,
    "chi hội trưởng": 8,
    "Chi hoi truong": 8,
    "Chi hội phó": 9,
    "chi hội phó": 9,
    "Chi hoi pho": 9,
    "Ủy viên BCH chi hội": 10,
    "Uỷ viên BCH chi hội": 10,
    "ủy viên BCH chi hội": 10,
    "Uy vien BCH chi hoi": 10,
}


def StaffTab(page: ft.Page, role: str):
    """Tab quản lý cán bộ lớp"""
    
    message_manager = MessageManager(page)
    
    state = {
        "staff": [],
        "selected_ids": set(),
        "page_index": 1,
        "total_records": 0,
        "search_text": "",
        "filter_lop": "",
        "filter_khoa": "",
        "is_loading": False,
        "active_dialog": None,
    }

    loading_indicator = ft.ProgressRing(visible=False, width=30, height=30)
    
    select_all_checkbox = ft.Checkbox(
        label="Chọn tất cả trang này",
        value=False,
        on_change=lambda e: toggle_select_all(e.control.value)
    )

    table = ft.DataTable(
        columns=[
            ft.DataColumn(ft.Text("Khoa/Viện", weight=ft.FontWeight.BOLD)),
            ft.DataColumn(ft.Text("Lớp", weight=ft.FontWeight.BOLD)),
            ft.DataColumn(ft.Text("Họ tên", weight=ft.FontWeight.BOLD)),
            ft.DataColumn(ft.Text("Chức vụ", weight=ft.FontWeight.BOLD)),
            ft.DataColumn(ft.Text("MSSV", weight=ft.FontWeight.BOLD)),
            ft.DataColumn(ft.Text("SĐT", weight=ft.FontWeight.BOLD)),
            ft.DataColumn(ft.Text("Email", weight=ft.FontWeight.BOLD)),
            ft.DataColumn(ft.Text("Ghi chú", weight=ft.FontWeight.BOLD)),
            ft.DataColumn(ft.Text("", weight=ft.FontWeight.BOLD)),
        ],
        rows=[],
        column_spacing=10,
        data_row_min_height=50,
    )

    pagination_text = ft.Text("Đang tải...", size=12, color=ft.Colors.GREY_600)
    selected_count_text = ft.Text("Đã chọn: 0", size=12, color=ft.Colors.BLUE_600, weight=ft.FontWeight.BOLD)

    def show_dialog_safe(dialog):
        """Mở dialog đồng bộ"""
        if state["active_dialog"] is not None:
            try:
                state["active_dialog"].open = False
                if state["active_dialog"] in page.overlay:
                    page.overlay.remove(state["active_dialog"])
            except:
                pass
        
        page.overlay.append(dialog)
        dialog.open = True
        state["active_dialog"] = dialog
        page.update()

    def close_dialog_safe():
        """Đóng dialog AN TOÀN"""
        if state["active_dialog"] is None:
            return
        
        async def _close():
            try:
                state["active_dialog"].open = False
                page.update()
                
                await page.sleep(0.05)
                
                if state["active_dialog"] in page.overlay:
                    page.overlay.remove(state["active_dialog"])
                state["active_dialog"] = None
                page.update()
            except Exception:
                pass
        
        page.run_task(_close)

    def get_chuc_vu_order(chuc_vu: str) -> int:
        """Lấy thứ tự ưu tiên của chức vụ"""
        return CHUC_VU_ORDER.get(chuc_vu, 999)

    def sort_staff_data(data: list[dict]) -> list[dict]:
        """
        Sắp xếp cán bộ theo:
        1. Lớp (chi_doan)
        2. Chức vụ (theo thứ tự ưu tiên)
        """
        return sorted(data, key=lambda x: (
            x.get("chi_doan", ""),
            get_chuc_vu_order(x.get("chuc_vu", "")),
        ))

    async def load_data_async():
        """Load dữ liệu async với sorting"""
        if state["is_loading"]:
            return
        
        state["is_loading"] = True
        loading_indicator.visible = True
        page.update()

        try:
            total = count_staff_with_filters(
                search=state["search_text"],
                lop=state["filter_lop"],
                khoa=state["filter_khoa"]
            )
            
            staff = fetch_staff_with_filters(
                search=state["search_text"],
                lop=state["filter_lop"],
                khoa=state["filter_khoa"],
                page=state["page_index"],
                page_size=PAGE_SIZE,
            )
            
            staff = sort_staff_data(staff)
            
            state["total_records"] = total
            state["staff"] = staff
            state["is_loading"] = False
            loading_indicator.visible = False
            
            table.rows.clear()
            for s in staff:
                table.rows.append(build_row(s))
            
            update_pagination()
            selected_count_text.value = f"Đã chọn: {len(state['selected_ids'])}"
            page.update()
            
        except Exception as load_error:
            error_msg = str(load_error)
            pagination_text.value = f"⚠️ Lỗi: {error_msg}"
            state["is_loading"] = False
            loading_indicator.visible = False
            page.update()

    def build_row(s: dict):
        """Build table row với đầy đủ cột theo thứ tự mới"""
        checkbox = ft.Checkbox(
            value=s["id"] in state["selected_ids"],
            on_change=lambda e, id=s["id"]: toggle_selection(id, e.control.value)
        )

        edit_btn = ft.Container(
            content=CustomIcon.create(CustomIcon.EDIT, size=18),
            on_click=lambda e, staff=s: open_edit_dialog(staff),
            tooltip="Sửa cán bộ",
            padding=8,
            border_radius=4,
            ink=True,
        )
        
        delete_btn = None
        if is_admin(role):
            delete_btn = ft.Container(
                content=CustomIcon.create(CustomIcon.DELETE, size=18),
                on_click=lambda e, staff=s: confirm_delete(staff),
                tooltip="Xóa cán bộ",
                padding=8,
                border_radius=4,
                ink=True,
            )

        action_buttons = [checkbox, edit_btn]
        if delete_btn:
            action_buttons.append(delete_btn)

        ghi_chu = s.get("ghi_chu", "") or ""
        
        return ft.DataRow(
            cells=[
                ft.DataCell(ft.Text(s.get("khoa_vien", "") or "")),
                ft.DataCell(ft.Text(s.get("chi_doan", "") or "")),
                ft.DataCell(ft.Text(s["ho_ten"])),
                ft.DataCell(ft.Text(s.get("chuc_vu", ""))),
                ft.DataCell(ft.Text(s.get("mssv", ""))),
                ft.DataCell(ft.Text(s.get("sdt", ""))),
                ft.DataCell(ft.Text(s.get("email", "") or "")),
                ft.DataCell(
                    ft.Text(
                        ghi_chu[:20] + "..." if len(ghi_chu) > 20 else ghi_chu,
                        size=11,
                        color=ft.Colors.GREY_600,
                        italic=True,
                        tooltip=ghi_chu if len(ghi_chu) > 20 else None
                    )
                ),
                ft.DataCell(ft.Row(action_buttons, spacing=4)),
            ],
        )
    
    def toggle_selection(id: str, selected: bool):
        if selected:
            state["selected_ids"].add(id)
        else:
            state["selected_ids"].discard(id)
        
        if len(state["selected_ids"]) == len(state["staff"]) and len(state["staff"]) > 0:
            select_all_checkbox.value = True
        else:
            select_all_checkbox.value = False
        
        selected_count_text.value = f"Đã chọn: {len(state['selected_ids'])}"
        page.update()
    
    def toggle_select_all(select_all: bool):
        if select_all:
            for s in state["staff"]:
                state["selected_ids"].add(s["id"])
        else:
            for s in state["staff"]:
                state["selected_ids"].discard(s["id"])
        
        table.rows.clear()
        for s in state["staff"]:
            table.rows.append(build_row(s))
        
        selected_count_text.value = f"Đã chọn: {len(state['selected_ids'])}"
        page.update()

    def on_search(e):
        state["search_text"] = e.control.value.strip()
        state["page_index"] = 1
        state["selected_ids"].clear()
        select_all_checkbox.value = False
        page.run_task(load_data_async)
    
    def on_filter_lop(e):
        state["filter_lop"] = e.control.value.strip()
        state["page_index"] = 1
        state["selected_ids"].clear()
        select_all_checkbox.value = False
        page.run_task(load_data_async)
    
    def on_filter_khoa(e):
        state["filter_khoa"] = e.control.value.strip()
        state["page_index"] = 1
        state["selected_ids"].clear()
        select_all_checkbox.value = False
        page.run_task(load_data_async)
    
    def clear_filters(e):
        state["search_text"] = ""
        state["filter_lop"] = ""
        state["filter_khoa"] = ""
        state["page_index"] = 1
        state["selected_ids"].clear()
        
        search_field.value = ""
        filter_lop_field.value = ""
        filter_khoa_field.value = ""
        select_all_checkbox.value = False
        
        page.run_task(load_data_async)

    def update_pagination():
        total_pages = max(1, (state["total_records"] + PAGE_SIZE - 1) // PAGE_SIZE)
        pagination_text.value = f"Trang {state['page_index']} / {total_pages} — Tổng {state['total_records']} cán bộ"

    def prev_page(e):
        if state["page_index"] > 1:
            state["page_index"] -= 1
            state["selected_ids"].clear()
            select_all_checkbox.value = False
            page.run_task(load_data_async)

    def next_page(e):
        if state["page_index"] * PAGE_SIZE < state["total_records"]:
            state["page_index"] += 1
            state["selected_ids"].clear()
            select_all_checkbox.value = False
            page.run_task(load_data_async)

    def open_create_dialog(e):
        """Thêm cán bộ mới"""
        
        dialog_container = ft.Container()
        dialog_message_manager = MessageManager(page, dialog_container)
        
        fields = {
            "ho_ten": ft.TextField(label="Họ tên *", autofocus=True),
            "chuc_vu": ft.Dropdown(
                label="Chức vụ *",
                options=[ft.dropdown.Option(cv) for cv in CHUC_VU_LIST],
            ),
            "chi_doan": ft.TextField(label="Lớp *", hint_text="VD: 74DCHT22"),
            "khoa_vien": ft.TextField(label="Khoa/Viện *", hint_text="VD: CNTT"),
            "csdt": ft.TextField(label="CSĐT"),
            "mssv": ft.TextField(label="MSSV", hint_text="VD: 74123456"),
            "sdt": ft.TextField(label="SĐT", hint_text="VD: 0123456789"),
            "email": ft.TextField(label="Email", hint_text="example@email.com"),
            "ghi_chu": ft.TextField(
                label="Ghi chú",
                hint_text="Ghi chú thêm",
                multiline=True,
                min_lines=2,
                max_lines=3,
            ),
        }

        async def submit(ev):
            submit_btn.disabled = True
            cancel_btn.disabled = True
            page.update()
            
            try:
                payload = {k: v.value for k, v in fields.items() if v.value}
                
                required = ["ho_ten", "chuc_vu", "chi_doan", "khoa_vien"]
                missing = [f for f in required if not payload.get(f)]
                if missing:
                    submit_btn.disabled = False
                    cancel_btn.disabled = False
                    dialog_message_manager.error(f"Thiếu trường bắt buộc: {', '.join(missing)}")
                    return
                
                create_staff(payload)
                
                close_dialog_safe()
                message_manager.success("Đã thêm cán bộ")
                await load_data_async()
                    
            except Exception as ex:
                submit_btn.disabled = False
                cancel_btn.disabled = False
                dialog_message_manager.error(f"Lỗi: {ex}")

        cancel_btn = ft.TextButton("Hủy", on_click=lambda e: close_dialog_safe())
        submit_btn = ft.ElevatedButton(
            "Thêm", 
            on_click=lambda e: page.run_task(submit, e),
            bgcolor=ft.Colors.GREEN_600,
            color=ft.Colors.WHITE
        )

        content = ft.Container(
            width=500,
            content=ft.Column([
                ft.Container(
                    content=ft.Row([
                        ft.Container(
                            content=CustomIcon.create(CustomIcon.ADD, size=24),
                            padding=10,
                            bgcolor=ft.Colors.GREEN_50,
                            border_radius=50
                        ),
                        ft.Column([
                            ft.Text("Thêm cán bộ mới", size=16, weight=ft.FontWeight.BOLD, color=ft.Colors.GREEN_900),
                            ft.Text("Nhập thông tin cán bộ", size=12, color=ft.Colors.GREY_700),
                        ], spacing=2)
                    ], spacing=10),
                    padding=10,
                    border=ft.border.all(1, ft.Colors.GREEN_100),
                    border_radius=8,
                    bgcolor=ft.Colors.GREEN_50
                ),
                ft.Divider(height=10, color=ft.Colors.TRANSPARENT),
                *list(fields.values())
            ], spacing=12, scroll=ft.ScrollMode.AUTO, height=400),
        )

        dialog_container.content = ft.Stack([content])

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Row([
                CustomIcon.create(CustomIcon.ADD, size=24),
                ft.Text("Thêm cán bộ mới", weight=ft.FontWeight.BOLD)
            ], spacing=10),
            content=dialog_container,
            actions=[cancel_btn, submit_btn],
            bgcolor=ft.Colors.WHITE,
            content_padding=24
        )

        show_dialog_safe(dialog)

    def open_edit_dialog(staff: dict):
        """Sửa thông tin cán bộ"""
        
        dialog_container = ft.Container()
        dialog_message_manager = MessageManager(page, dialog_container)
        
        fields = {
            "ho_ten": ft.TextField(label="Họ tên *", value=staff["ho_ten"]),
            "chuc_vu": ft.Dropdown(
                label="Chức vụ *",
                value=staff.get("chuc_vu", ""),
                options=[ft.dropdown.Option(cv) for cv in CHUC_VU_LIST],
            ),
            "chi_doan": ft.TextField(label="Lớp *", value=staff.get("chi_doan", "")),
            "khoa_vien": ft.TextField(label="Khoa/Viện *", value=staff.get("khoa_vien", "")),
            "csdt": ft.TextField(label="CSĐT", value=staff.get("csdt", "")),
            "mssv": ft.TextField(label="MSSV", value=staff.get("mssv", "")),
            "sdt": ft.TextField(label="SĐT", value=staff.get("sdt", "")),
            "email": ft.TextField(label="Email", value=staff.get("email", "")),
            "ghi_chu": ft.TextField(
                label="Ghi chú",
                value=staff.get("ghi_chu", ""),
                multiline=True,
                min_lines=2,
                max_lines=3,
            ),
        }

        async def submit(e):
            submit_btn.disabled = True
            cancel_btn.disabled = True
            page.update()
            
            try:
                payload = {k: v.value.strip() if isinstance(v.value, str) else v.value 
                          for k, v in fields.items() if v.value}
                
                update_staff(staff["id"], payload)
                
                close_dialog_safe()
                message_manager.success("Đã cập nhật")
                await load_data_async()
                    
            except Exception as ex:
                submit_btn.disabled = False
                cancel_btn.disabled = False
                dialog_message_manager.error(f"Lỗi: {ex}")

        cancel_btn = ft.TextButton("Hủy", on_click=lambda e: close_dialog_safe())
        submit_btn = ft.ElevatedButton(
            "Lưu", 
            on_click=lambda e: page.run_task(submit, e),
            bgcolor=ft.Colors.BLUE_600,
            color=ft.Colors.WHITE
        )

        content = ft.Container(
            width=500,
            content=ft.Column([
                ft.Container(
                    content=ft.Row([
                        ft.Container(
                            content=CustomIcon.create(CustomIcon.EDIT, size=24),
                            padding=10,
                            bgcolor=ft.Colors.BLUE_50,
                            border_radius=50
                        ),
                        ft.Column([
                            ft.Text(staff['ho_ten'], size=16, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_900),
                            ft.Text("Chỉnh sửa thông tin cán bộ", size=12, color=ft.Colors.GREY_700),
                        ], spacing=2)
                    ], spacing=10),
                    padding=10,
                    border=ft.border.all(1, ft.Colors.BLUE_100),
                    border_radius=8,
                    bgcolor=ft.Colors.BLUE_50
                ),
                ft.Divider(height=10, color=ft.Colors.TRANSPARENT),
                *list(fields.values())
            ], spacing=12, scroll=ft.ScrollMode.AUTO, height=400),
        )

        dialog_container.content = ft.Stack([content])

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Row([
                CustomIcon.create(CustomIcon.EDIT, size=24),
                ft.Text(f"Sửa cán bộ: {staff['ho_ten']}", weight=ft.FontWeight.BOLD)
            ], spacing=10),
            content=dialog_container,
            actions=[cancel_btn, submit_btn],
            bgcolor=ft.Colors.WHITE,
            content_padding=24
        )

        show_dialog_safe(dialog)

    def open_bulk_update_dialog(e):
        """Cập nhật hàng loạt"""
        selected_count = len(state["selected_ids"])
        if not state["selected_ids"]:
            message_manager.warning("Chưa chọn cán bộ nào")
            return

        dialog_container = ft.Container()
        dialog_message_manager = MessageManager(page, dialog_container)
        
        field_states = {
            "chuc_vu": False,
            "chi_doan": False,
            "khoa_vien": False,
            "sdt": False,
            "email": False,
            "ghi_chu": False,
        }
        
        def toggle_field(field_name: str, enabled: bool):
            field_states[field_name] = enabled
            controls = field_controls[field_name]
            controls["input"].disabled = not enabled
            if "clear" in controls:
                controls["clear"].visible = enabled
            page.update()
        
        def set_field_value(field_name: str, value: str):
            field_controls[field_name]["input"].value = value
            page.update()

        enable_chuc_vu = ft.Checkbox(value=False, on_change=lambda e: toggle_field("chuc_vu", e.control.value))
        chuc_vu_dropdown = ft.Dropdown(
            label="Giá trị mới",
            disabled=True,
            options=[ft.dropdown.Option(cv) for cv in CHUC_VU_LIST],
            expand=True,
            text_size=13,
            height=40,
            content_padding=10
        )
        
        enable_chi_doan = ft.Checkbox(value=False, on_change=lambda e: toggle_field("chi_doan", e.control.value))
        chi_doan_field = ft.TextField(label="Giá trị mới", disabled=True, expand=True, text_size=13, height=40, content_padding=10)
        clear_chi_doan_btn = ft.IconButton(icon=ft.Icons.CLEAR, icon_size=16, tooltip="Xóa", visible=False, on_click=lambda e: set_field_value("chi_doan", ""))
        
        enable_khoa_vien = ft.Checkbox(value=False, on_change=lambda e: toggle_field("khoa_vien", e.control.value))
        khoa_vien_field = ft.TextField(label="Giá trị mới", disabled=True, expand=True, text_size=13, height=40, content_padding=10)
        clear_khoa_vien_btn = ft.IconButton(icon=ft.Icons.CLEAR, icon_size=16, tooltip="Xóa", visible=False, on_click=lambda e: set_field_value("khoa_vien", ""))
        
        enable_sdt = ft.Checkbox(value=False, on_change=lambda e: toggle_field("sdt", e.control.value))
        sdt_field = ft.TextField(label="Giá trị mới", disabled=True, expand=True, text_size=13, height=40, content_padding=10)
        clear_sdt_btn = ft.IconButton(icon=ft.Icons.CLEAR, icon_size=16, tooltip="Xóa", visible=False, on_click=lambda e: set_field_value("sdt", ""))
        
        enable_email = ft.Checkbox(value=False, on_change=lambda e: toggle_field("email", e.control.value))
        email_field = ft.TextField(label="Giá trị mới", disabled=True, expand=True, text_size=13, height=40, content_padding=10)
        clear_email_btn = ft.IconButton(icon=ft.Icons.CLEAR, icon_size=16, tooltip="Xóa", visible=False, on_click=lambda e: set_field_value("email", ""))
        
        enable_ghi_chu = ft.Checkbox(value=False, on_change=lambda e: toggle_field("ghi_chu", e.control.value))
        ghi_chu_field = ft.TextField(
            label="Giá trị mới",
            disabled=True,
            expand=True,
            text_size=13,
            content_padding=10,
            multiline=True,
            min_lines=1,
            max_lines=3
        )
        clear_ghi_chu_btn = ft.IconButton(icon=ft.Icons.CLEAR, icon_size=16, tooltip="Xóa", visible=False, on_click=lambda e: set_field_value("ghi_chu", ""))
        
        field_controls = {
            "chuc_vu": {"checkbox": enable_chuc_vu, "input": chuc_vu_dropdown},
            "chi_doan": {"checkbox": enable_chi_doan, "input": chi_doan_field, "clear": clear_chi_doan_btn},
            "khoa_vien": {"checkbox": enable_khoa_vien, "input": khoa_vien_field, "clear": clear_khoa_vien_btn},
            "sdt": {"checkbox": enable_sdt, "input": sdt_field, "clear": clear_sdt_btn},
            "email": {"checkbox": enable_email, "input": email_field, "clear": clear_email_btn},
            "ghi_chu": {"checkbox": enable_ghi_chu, "input": ghi_chu_field, "clear": clear_ghi_chu_btn},
        }

        async def handle_submit(ev):
            submit_btn.disabled = True
            cancel_btn.disabled = True
            page.update()
            
            try:
                payload = {}
                
                if field_states["chuc_vu"]:
                    payload["chuc_vu"] = chuc_vu_dropdown.value
                if field_states["chi_doan"]:
                    payload["chi_doan"] = chi_doan_field.value.strip() if chi_doan_field.value else ""
                if field_states["khoa_vien"]:
                    payload["khoa_vien"] = khoa_vien_field.value.strip() if khoa_vien_field.value else ""
                if field_states["sdt"]:
                    payload["sdt"] = sdt_field.value.strip() if sdt_field.value else ""
                if field_states["email"]:
                    payload["email"] = email_field.value.strip() if email_field.value else ""
                if field_states["ghi_chu"]:
                    payload["ghi_chu"] = ghi_chu_field.value.strip() if ghi_chu_field.value else ""
                
                if not payload:
                    submit_btn.disabled = False
                    cancel_btn.disabled = False
                    dialog_message_manager.warning("Chưa chọn trường nào để cập nhật")
                    return
                
                bulk_update_staff(list(state["selected_ids"]), payload)
                
                state["selected_ids"].clear()
                select_all_checkbox.value = False
                close_dialog_safe()
                
                updated_fields = ", ".join(payload.keys())
                message_manager.success(f"Đã cập nhật {selected_count} cán bộ: {updated_fields}")
                await load_data_async()
                    
            except Exception as ex:
                submit_btn.disabled = False
                cancel_btn.disabled = False
                dialog_message_manager.error(f"Lỗi: {ex}")

        cancel_btn = ft.TextButton(
            "Hủy bỏ",
            on_click=lambda e: close_dialog_safe(),
            style=ft.ButtonStyle(color=ft.Colors.GREY_600)
        )
        submit_btn = ft.ElevatedButton(
            "Xác nhận cập nhật",
            on_click=lambda e: page.run_task(handle_submit, e),
            bgcolor=ft.Colors.BLUE_600,
            color=ft.Colors.WHITE,
            elevation=0
        )
        
        def build_field_row(label: str, checkbox: ft.Checkbox, input_control, clear_btn=None):
            """Helper tạo row đẹp hơn"""
            row_controls = [
                ft.Container(content=ft.Text(label, size=13, weight=ft.FontWeight.W_500, color=ft.Colors.GREY_800), width=130),
                ft.Container(content=checkbox, width=40),
                input_control,
            ]
            if clear_btn:
                row_controls.append(clear_btn)
            
            return ft.Container(
                content=ft.Row(controls=row_controls, spacing=10, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                padding=ft.padding.symmetric(vertical=2)
            )

        content_container = ft.Container(
            width=650,
            content=ft.Column(
                controls=[
                    ft.Container(
                        content=ft.Row(
                            controls=[
                                ft.Container(
                                    content=CustomIcon.create(CustomIcon.EDIT, size=24),
                                    padding=10,
                                    bgcolor=ft.Colors.WHITE,
                                    border_radius=50,
                                    border=ft.border.all(1, ft.Colors.BLUE_100)
                                ),
                                ft.Column(
                                    controls=[
                                        ft.Text(f"Đang chọn {selected_count} cán bộ", weight=ft.FontWeight.BOLD, size=15, color=ft.Colors.BLUE_900),
                                        ft.Text("Tích vào ô kiểm để chọn trường dữ liệu cần cập nhật đồng loạt.", size=13, color=ft.Colors.GREY_700),
                                    ],
                                    spacing=2, tight=True
                                )
                            ],
                            spacing=12,
                        ),
                        padding=12,
                        bgcolor=ft.Colors.BLUE_50,
                        border=ft.border.all(1, ft.Colors.BLUE_200),
                        border_radius=8,
                    ),
                    
                    ft.Divider(height=10, color=ft.Colors.TRANSPARENT),
                    ft.Container(
                        content=ft.Row([
                            ft.Container(ft.Text("TRƯỜNG DỮ LIỆU", size=11, weight=ft.FontWeight.BOLD, color=ft.Colors.GREY_600), width=130),
                            ft.Container(ft.Text("SỬA?", size=11, weight=ft.FontWeight.BOLD, color=ft.Colors.GREY_600), width=40),
                            ft.Text("GIÁ TRỊ MỚI", size=11, weight=ft.FontWeight.BOLD, color=ft.Colors.GREY_600),
                        ], spacing=10),
                        padding=ft.padding.only(bottom=5, left=5)
                    ),
                    ft.Divider(height=1, color=ft.Colors.GREY_200),
                    ft.Column(
                        controls=[
                            build_field_row("Chức vụ", enable_chuc_vu, chuc_vu_dropdown),
                            build_field_row("Lớp", enable_chi_doan, chi_doan_field, clear_chi_doan_btn),
                            build_field_row("Khoa/Viện", enable_khoa_vien, khoa_vien_field, clear_khoa_vien_btn),
                            build_field_row("SĐT", enable_sdt, sdt_field, clear_sdt_btn),
                            build_field_row("Email", enable_email, email_field, clear_email_btn),
                            ft.Divider(height=1, color=ft.Colors.GREY_100),
                            build_field_row("Ghi chú", enable_ghi_chu, ghi_chu_field, clear_ghi_chu_btn),
                        ],
                        scroll=ft.ScrollMode.AUTO,
                        height=300,
                        spacing=10
                    )
                ],
                spacing=10,
                tight=True
            )
        )

        dialog_container.content = ft.Stack([content_container])

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Row(
                [
                    CustomIcon.create(CustomIcon.EDIT, size=24),
                    ft.Text("Sửa hàng loạt", size=18, weight=ft.FontWeight.W_600, color=ft.Colors.GREY_900),
                ],
                spacing=10, tight=True
            ),
            content=dialog_container,
            actions=[cancel_btn, submit_btn],
            actions_alignment=ft.MainAxisAlignment.END,
            actions_padding=ft.padding.only(right=20, bottom=16),
            content_padding=ft.padding.all(24),
            shape=ft.RoundedRectangleBorder(radius=12),
            bgcolor=ft.Colors.WHITE,
        )
        
        show_dialog_safe(dialog)

    def confirm_delete(staff: dict):
        """Xác nhận xóa cán bộ"""
        
        async def do_delete(e):
            delete_btn.disabled = True
            cancel_btn.disabled = True
            page.update()
            
            try:
                delete_staff(staff["id"])
                
                close_dialog_safe()
                message_manager.success(f"Đã xóa cán bộ {staff['ho_ten']}")
                await load_data_async()
                    
            except Exception as ex:
                delete_btn.disabled = False
                cancel_btn.disabled = False
                close_dialog_safe()
                message_manager.error(f"Lỗi xóa: {ex}")

        cancel_btn = ft.TextButton("Hủy", on_click=lambda e: close_dialog_safe())
        delete_btn = ft.ElevatedButton(
            "Xóa",
            on_click=lambda e: page.run_task(do_delete, e),
            bgcolor=ft.Colors.RED_600,
            color=ft.Colors.WHITE
        )

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Row([
                CustomIcon.create(CustomIcon.WARNING, size=24),
                ft.Text("Xác nhận xóa", weight=ft.FontWeight.BOLD)
            ], spacing=10),
            content=ft.Container(
                width=400,
                content=ft.Column([
                    ft.Container(
                        content=ft.Row([
                            CustomIcon.create(CustomIcon.DELETE_FOREVER, size=48),
                            ft.Column([
                                ft.Text("Bạn có chắc chắn muốn xóa cán bộ này?", size=14, weight=ft.FontWeight.W_500),
                                ft.Text(staff['ho_ten'], size=16, weight=ft.FontWeight.BOLD, color=ft.Colors.RED_700),
                                ft.Text("Hành động này không thể hoàn tác!", size=12, color=ft.Colors.RED_600, italic=True),
                            ], spacing=4, expand=True)
                        ], spacing=15),
                        padding=15,
                        border=ft.border.all(2, ft.Colors.RED_200),
                        border_radius=8,
                        bgcolor=ft.Colors.RED_50
                    ),
                ], spacing=0, tight=True)
            ),
            actions=[cancel_btn, delete_btn],
            bgcolor=ft.Colors.WHITE,
            content_padding=24
        )

        show_dialog_safe(dialog)

    def import_excel_dialog(e):
        async def select_and_import():
            try:
                import tkinter as tk
                from tkinter import filedialog

                root = tk.Tk()
                root.withdraw()
                root.attributes("-topmost", True)

                file_path = filedialog.askopenfilename(
                    title="Chọn file Excel - Import Cán bộ lớp",
                    filetypes=[
                        ("Excel files", "*.xlsx *.xls"),
                        ("All files", "*.*"),
                    ],
                )

                root.destroy()

                if not file_path:
                    return

                before_total = state.get("total_records", 0)

                message_manager.info("Đang xử lý file import...")
                await asyncio.sleep(0)

                from services.staff_service import import_staff_from_excel

                with open(file_path, "rb") as f:
                    file_bytes = f.read()

                imported_count, errors = import_staff_from_excel(file_bytes)

                await load_data_async()
                update_pagination()
                await asyncio.sleep(0)

                after_total = state.get("total_records", 0)
                diff = after_total - before_total

                await message_manager.force_clear_async()
                if errors:
                    error_text = "\n".join(errors[:10])

                    if len(errors) > 10:
                        error_text += f"\n\n... và {len(errors) - 10} lỗi khác"

                    result_dialog = ft.AlertDialog(
                        modal=True,
                        title=ft.Row(
                            [
                                CustomIcon.create(CustomIcon.WARNING, size=24),
                                ft.Text(
                                    "Import có lỗi",
                                    size=18,
                                    weight=ft.FontWeight.BOLD,
                                ),
                            ],
                            spacing=10,
                        ),
                        content=ft.Container(
                            width=550,
                            content=ft.Column(
                                [
                                    ft.Row(
                                        [
                                            ft.Container(
                                                content=ft.Column(
                                                    [
                                                        ft.Text(
                                                            "Thêm mới",
                                                            size=12,
                                                            color=ft.Colors.GREEN_700,
                                                        ),
                                                        ft.Text(
                                                            str(max(diff, 0)),
                                                            size=20,
                                                            weight=ft.FontWeight.BOLD,
                                                        ),
                                                    ],
                                                    spacing=4,
                                                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                                ),
                                                bgcolor=ft.Colors.GREEN_50,
                                                padding=15,
                                                border_radius=8,
                                                expand=True,
                                            ),
                                            ft.Container(
                                                content=ft.Column(
                                                    [
                                                        ft.Text(
                                                            "Lỗi",
                                                            size=12,
                                                            color=ft.Colors.RED_700,
                                                        ),
                                                        ft.Text(
                                                            str(len(errors)),
                                                            size=20,
                                                            weight=ft.FontWeight.BOLD,
                                                        ),
                                                    ],
                                                    spacing=4,
                                                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                                ),
                                                bgcolor=ft.Colors.RED_50,
                                                padding=15,
                                                border_radius=8,
                                                expand=True,
                                            ),
                                        ],
                                        spacing=10,
                                    ),
                                    ft.Divider(),
                                    ft.Text(
                                        "Chi tiết lỗi:",
                                        weight=ft.FontWeight.BOLD,
                                    ),
                                    ft.Container(
                                        content=ft.Text(
                                            error_text,
                                            size=11,
                                            selectable=True,
                                            color=ft.Colors.RED_900,
                                        ),
                                        bgcolor=ft.Colors.RED_50,
                                        padding=12,
                                        border_radius=8,
                                        border=ft.border.all(
                                            1, ft.Colors.RED_200
                                        ),
                                        height=300,
                                    ),
                                ],
                                scroll=ft.ScrollMode.AUTO,
                            ),
                        ),
                        actions=[
                            ft.ElevatedButton(
                                content=ft.Row(
                                    [
                                        CustomIcon.create(
                                            CustomIcon.CHECK, size=16
                                        ),
                                        ft.Text("Đóng"),
                                    ],
                                    spacing=6,
                                ),
                                on_click=lambda _: close_dialog_safe(),
                            )
                        ],
                    )

                    show_dialog_safe(result_dialog)

                    if diff > 0:
                        message_manager.warning(
                            f"Import xong, thêm {diff} cán bộ nhưng có lỗi"
                        )
                    else:
                        message_manager.error(
                            "Import thất bại, không có dữ liệu hợp lệ"
                        )

                else:
                    if diff > 0:
                        message_manager.success(
                            f"Import thành công {diff} cán bộ"
                        )
                    else:
                        message_manager.info(
                            "File không có cán bộ mới để import"
                        )

            except ImportError:
                message_manager.error(
                    "Thiếu tkinter – không thể mở dialog chọn file"
                )
            except Exception as ex:
                message_manager.error(f"Lỗi import: {ex}")

        page.run_task(select_and_import)

    def download_template_dialog(e):
        async def create_and_save_template():
            try:
                import pandas as pd
                from io import BytesIO
                import os
                
                template_data = {
                    "ho_ten": ["Nguyễn Văn A", "Trần Thị B", "Lê Văn C"],
                    "chuc_vu": ["Lớp trưởng", "Lớp phó", "Bí thư chi đoàn"],
                    "chi_doan": ["74DCHT22", "74DCHT22", "74DCHT23"],
                    "khoa_vien": ["CNTT", "CNTT", "CNTT"],
                    "mssv": ["74123456", "74123457", "74123458"],
                    "ngay_sinh": ["01/01/2005", "15/03/2005", "20/07/2005"],
                    "sdt": ["0123456789", "0987654321", "0912345678"],
                    "email": ["nguyenvana@email.com", "tranthib@email.com", "levanc@email.com"],
                    "csdt": ["CSĐT 1", "CSĐT 2", "CSĐT 1"],
                    "ghi_chu": ["", "Cần kiểm tra", ""],
                }
                
                df = pd.DataFrame(template_data)
                
                output = BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    df.to_excel(writer, index=False, sheet_name='Cán bộ lớp')
                    
                    worksheet = writer.sheets['Cán bộ lớp']
                    for idx, col in enumerate(df.columns, 1):
                        max_length = max(
                            df[col].astype(str).map(len).max(),
                            len(str(col))
                        )
                        col_letter = chr(64 + idx)
                        worksheet.column_dimensions[col_letter].width = min(max_length + 3, 40)
                
                downloads_folder = os.path.join(os.path.expanduser("~"), "Downloads")
                filename = "template_import_can_bo_lop.xlsx"
                save_path = os.path.join(downloads_folder, filename)
                
                with open(save_path, "wb") as f:
                    f.write(output.getvalue())
                
                required_items = [
                    ("ho_ten", "Họ và tên cán bộ (bắt buộc)"),
                    ("chuc_vu", "Chức vụ (bắt buộc, VD: Lớp trưởng)"),
                    ("chi_doan", "Tên lớp (bắt buộc, VD: 74DCHT22)"),
                    ("khoa_vien", "Tên khoa/viện (bắt buộc, VD: CNTT)"),
                ]
                
                required_list = []
                for field, desc in required_items:
                    required_list.append(
                        ft.Column([
                            ft.Row([
                                ft.Text("•", size=12, color=ft.Colors.GREY_700),
                                ft.Text(field, size=11, weight=ft.FontWeight.W_600, color=ft.Colors.GREY_900),
                            ], spacing=6),
                            ft.Container(
                                content=ft.Text(desc, size=10, color=ft.Colors.GREY_600),
                                padding=ft.padding.only(left=14),
                            ),
                        ], spacing=2)
                    )
                
                optional_items = [
                    ("mssv", "Mã số sinh viên"),
                    ("ngay_sinh", "dd/mm/yyyy (VD: 01/01/2005)"),
                    ("sdt", "Số điện thoại (VD: 0123456789)"),
                    ("email", "Email liên hệ"),
                    ("csdt", "Cơ sở đào tạo"),
                    ("ghi_chu", "Ghi chú thêm"),
                ]
                
                optional_list = []
                for field, desc in optional_items:
                    optional_list.append(
                        ft.Column([
                            ft.Row([
                                ft.Text("•", size=12, color=ft.Colors.GREY_700),
                                ft.Text(field, size=11, weight=ft.FontWeight.W_600, color=ft.Colors.GREY_900),
                            ], spacing=6),
                            ft.Container(
                                content=ft.Text(desc, size=10, color=ft.Colors.GREY_600),
                                padding=ft.padding.only(left=14),
                            ),
                        ], spacing=2)
                    )
                
                content = ft.Column([
                    ft.Text("File mẫu đã được lưu tại:", size=12, weight=ft.FontWeight.W_500, color=ft.Colors.GREY_700),
                    ft.Container(height=6),
                    ft.Container(
                        content=ft.Text(save_path, size=11, selectable=True, color=ft.Colors.BLUE_800),
                        bgcolor=ft.Colors.BLUE_50,
                        padding=12,
                        border_radius=8,
                        border=ft.border.all(1, ft.Colors.BLUE_100),
                    ),
                    ft.Container(height=16),
                    
                    ft.Row([
                        CustomIcon.create(CustomIcon.DOCUMENT, size=18),
                        ft.Text("Cột bắt buộc:", size=13, weight=ft.FontWeight.BOLD, color=ft.Colors.GREY_900),
                    ], spacing=8),
                    ft.Container(height=10),
                    ft.Container(
                        content=ft.Column(required_list, spacing=8),
                        bgcolor=ft.Colors.ORANGE_50,
                        padding=14,
                        border_radius=8,
                        border=ft.border.all(1, ft.Colors.ORANGE_100),
                    ),
                    ft.Container(height=16),
                    
                    ft.Row([
                        CustomIcon.create(CustomIcon.REPORT, size=18),
                        ft.Text("Cột tùy chọn:", size=13, weight=ft.FontWeight.BOLD, color=ft.Colors.GREY_900),
                    ], spacing=8),
                    ft.Container(height=10),
                    ft.Container(
                        content=ft.Column(optional_list, spacing=8),
                        bgcolor=ft.Colors.BLUE_50,
                        padding=14,
                        border_radius=8,
                        border=ft.border.all(1, ft.Colors.BLUE_100),
                    ),
                ], spacing=0, scroll=ft.ScrollMode.AUTO)
                
                success_dialog = ft.AlertDialog(
                    modal=True,
                    title=ft.Row([
                        ft.Row([
                            ft.Container(
                                content=CustomIcon.create(CustomIcon.CHECK_GREEN, size=28),
                                bgcolor=ft.Colors.GREEN_50,
                                border_radius=50,
                                padding=6,
                            ),
                            ft.Text("Đã tải mẫu", size=18, weight=ft.FontWeight.BOLD, color=ft.Colors.GREY_900),
                        ], spacing=10),
                        ft.Container(
                            content=CustomIcon.create(CustomIcon.CLOSE1, size=18),
                            on_click=lambda _: close_dialog_safe(),
                            tooltip="Đóng",
                            padding=6,
                            border_radius=50,
                            ink=True,
                        ),
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    content=ft.Container(
                        content=content,
                        width=550,
                        height=550,
                        padding=20,
                    ),
                    actions=[
                        ft.Row([
                            ft.ElevatedButton(
                                content=ft.Row([
                                    CustomIcon.create(CustomIcon.CHECK_WHITE, size=16),
                                    ft.Text("Đóng", size=13, weight=ft.FontWeight.W_500),
                                ], spacing=6),
                                on_click=lambda _: close_dialog_safe(),
                                bgcolor=ft.Colors.BLUE_600,
                                color=ft.Colors.WHITE,
                            ),
                        ], alignment=ft.MainAxisAlignment.END)
                    ],
                    shape=ft.RoundedRectangleBorder(radius=12),
                    bgcolor=ft.Colors.WHITE,
                )
                
                show_dialog_safe(success_dialog)
                
            except Exception as ex:
                message_manager.error(f"Lỗi tạo mẫu: {ex}")
        
        page.run_task(create_and_save_template)

    def export_excel_action(e):
        if not state["selected_ids"] or len(state["selected_ids"]) == 0:
            warning_dialog = ft.AlertDialog(
                modal=True,
                title=ft.Row(
                    [
                        CustomIcon.create(CustomIcon.WARNING, size=24),
                        ft.Text("Chưa chọn cán bộ", size=18, weight=ft.FontWeight.BOLD),
                    ],
                    spacing=8,
                ),
                content=ft.Container(
                    width=420,
                    padding=15,
                    bgcolor=ft.Colors.ORANGE_50,
                    border_radius=8,
                    border=ft.border.all(1, ft.Colors.ORANGE_200),
                    content=ft.Text("Vui lòng chọn ít nhất một cán bộ để export.", size=14),
                ),
                actions=[
                    ft.ElevatedButton(
                        "Đã hiểu",
                        on_click=lambda _: close_dialog_safe(),
                    ),
                ],
            )
            show_dialog_safe(warning_dialog)
            return
        
        selected = list(state["selected_ids"])
        selected_count = len(selected)
        
        import os
        import datetime
        
        downloads_folder = os.path.join(os.path.expanduser("~"), "Downloads")
        filename = f"export_can_bo_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        save_path = os.path.join(downloads_folder, filename)
        
        message_manager.info(f"Đang xuất {selected_count} cán bộ...")
        
        async def _export():
            try:
                from services.staff_service import export_staff_to_excel
                
                excel_bytes = export_staff_to_excel(selected)
                
                with open(save_path, "wb") as f:
                    f.write(excel_bytes)
                
                file_size = os.path.getsize(save_path) / 1024
                
                content = ft.Column([
                    ft.Row([
                        ft.Container(
                            content=ft.Column([
                                ft.Text("Số lượng", size=12, color=ft.Colors.GREY_700),
                                ft.Text(f"{selected_count} cán bộ", size=18, weight=ft.FontWeight.BOLD, color=ft.Colors.GREY_900),
                            ], spacing=4, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                            bgcolor=ft.Colors.BLUE_50,
                            padding=15,
                            border_radius=8,
                            expand=True,
                        ),
                        ft.Container(
                            content=ft.Column([
                                ft.Text("Kích thước", size=12, color=ft.Colors.GREY_700),
                                ft.Text(f"{file_size:.1f} KB", size=18, weight=ft.FontWeight.BOLD, color=ft.Colors.GREY_900),
                            ], spacing=4, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                            bgcolor=ft.Colors.GREEN_50,
                            padding=15,
                            border_radius=8,
                            expand=True,
                        ),
                    ], spacing=10),
                    ft.Container(height=12),
                    ft.Divider(),
                    ft.Container(height=10),
                    ft.Text("Đã lưu tại:", size=13, weight=ft.FontWeight.BOLD, color=ft.Colors.GREY_900),
                    ft.Container(height=6),
                    ft.Container(
                        content=ft.Text(
                            save_path,
                            size=11,
                            selectable=True,
                            color=ft.Colors.BLUE_800
                        ),
                        bgcolor=ft.Colors.BLUE_50,
                        padding=12,
                        border_radius=8,
                        border=ft.border.all(1, ft.Colors.BLUE_100),
                    ),
                ], spacing=0, tight=True)
                
                success_dialog = ft.AlertDialog(
                    modal=True,
                    title=ft.Row([
                        ft.Row([
                            ft.Container(
                                content=CustomIcon.create(CustomIcon.CHECK_GREEN, size=28),
                                bgcolor=ft.Colors.GREEN_50,
                                border_radius=50,
                                padding=6,
                            ),
                            ft.Text("Xuất thành công", size=18, weight=ft.FontWeight.BOLD, color=ft.Colors.GREY_900),
                        ], spacing=10),
                        ft.Container(
                            content=CustomIcon.create(CustomIcon.CLOSE1, size=18),
                            on_click=lambda _: close_dialog_safe(),
                            tooltip="Đóng",
                            padding=6,
                            border_radius=50,
                            ink=True,
                        ),
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    content=ft.Container(
                        content=content,
                        width=450,
                        padding=20,
                    ),
                    actions=[
                        ft.Row([
                            ft.ElevatedButton(
                                content=ft.Row([
                                    CustomIcon.create(CustomIcon.CHECK_WHITE, size=16),
                                    ft.Text("Đóng", size=13, weight=ft.FontWeight.W_500),
                                ], spacing=6),
                                on_click=lambda _: close_dialog_safe(),
                                bgcolor=ft.Colors.BLUE_600,
                                color=ft.Colors.WHITE,
                            ),
                        ], alignment=ft.MainAxisAlignment.END)
                    ],
                    shape=ft.RoundedRectangleBorder(radius=12),
                    bgcolor=ft.Colors.WHITE,
                )
                
                show_dialog_safe(success_dialog)
                
            except Exception as ex:
                message_manager.error(f"Lỗi xuất file: {ex}")
        
        page.run_task(_export)

    search_field = ft.TextField(
        label="Tìm theo Họ tên / Lớp",
        prefix_icon=ft.Icons.SEARCH,
        hint_text="VD: Nguyễn Văn A hoặc 74DCHT22",
        width=420,
        on_submit=on_search,
    )
    
    filter_lop_field = ft.TextField(
        label="Lọc lớp",
        hint_text="74DCHT22",
        width=150,
        on_submit=on_filter_lop
    )
    
    filter_khoa_field = ft.TextField(
        label="Lọc khoa",
        hint_text="CNTT",
        width=150,
        on_submit=on_filter_khoa
    )

    buttons = []
    if is_admin(role):
        buttons.extend([
            elevated_button("Thêm cán bộ", CustomIcon.ADD, on_click=open_create_dialog),
            elevated_button("Tải mẫu", CustomIcon.DOCUMENT, on_click=download_template_dialog),
            elevated_button("Import Excel", CustomIcon.UPLOAD, on_click=import_excel_dialog),
            elevated_button("Export Excel", CustomIcon.DOWNLOAD, on_click=export_excel_action),
        ])
    buttons.append(elevated_button("Sửa hàng loạt", CustomIcon.EDIT, on_click=open_bulk_update_dialog))

    toolbar = ft.Column([
        ft.Row(
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            controls=[
                ft.Row([search_field, loading_indicator], spacing=8),
                ft.Row(spacing=8, controls=buttons),
            ],
        ),
        ft.Row([
            filter_lop_field,
            filter_khoa_field,
            ft.TextButton("Xóa lọc", on_click=clear_filters)
        ], spacing=8),
        ft.Row([
            select_all_checkbox,
            selected_count_text,
        ], spacing=12),
    ], spacing=8)

    footer = ft.Row(
        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        controls=[
            pagination_text,
            ft.Row(
                spacing=6,
                controls=[
                    ft.Container(
                        content=CustomIcon.create(CustomIcon.CHEVRON_LEFT, size=20),
                        on_click=prev_page,
                        padding=8,
                        border_radius=4,
                        ink=True,
                    ),
                    ft.Container(
                        content=CustomIcon.create(CustomIcon.CHEVRON_RIGHT, size=20),
                        on_click=next_page,
                        padding=8,
                        border_radius=4,
                        ink=True,
                    ),
                ],
            ),
        ],
    )

    result = ft.Column(
        expand=True,
        spacing=10,
        controls=[
            toolbar,
            ft.Divider(height=1),
            ft.Container(expand=True, content=ft.ListView(expand=True, controls=[table])),
            footer,
        ],
    )
    
    page.run_task(load_data_async)
    
    return result