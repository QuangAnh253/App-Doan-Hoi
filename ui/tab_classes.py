# ui/tab_classes.py
import flet as ft
import asyncio
from services.classes_service import (
    fetch_classes,
    count_classes,
    update_class,
    bulk_update_classes,
    create_class,
    delete_class,
)
from core.auth import is_admin
from ui.icon_helper import CustomIcon, elevated_button
from ui.message_manager import MessageManager

PAGE_SIZE = 100


def ClassesTab(page: ft.Page, role: str):
    
    message_manager = MessageManager(page)

    state = {
        "classes": [],
        "selected_ids": set(),
        "page_index": 1,
        "total_records": 0,
        "search_text": "",
        "filter_trang_thai": "",
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
            ft.DataColumn(ft.Text("Chi đoàn", weight=ft.FontWeight.BOLD)),
            ft.DataColumn(ft.Text("Sĩ số", weight=ft.FontWeight.BOLD)),
            ft.DataColumn(ft.Text("Đã ký", weight=ft.FontWeight.BOLD)),
            ft.DataColumn(ft.Text("Đoàn phí", weight=ft.FontWeight.BOLD)),
            ft.DataColumn(ft.Text("Hội phí", weight=ft.FontWeight.BOLD)),
            ft.DataColumn(ft.Text("Đã nộp", weight=ft.FontWeight.BOLD)),
            ft.DataColumn(ft.Text("Vị trí lưu", weight=ft.FontWeight.BOLD, size=14)),
            ft.DataColumn(ft.Text("Ghi chú", weight=ft.FontWeight.BOLD, size=14)),
            ft.DataColumn(ft.Text("Trạng thái", weight=ft.FontWeight.BOLD)),
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
            except Exception as ex:
                pass
        
        page.run_task(_close)

    async def load_data_async():
        """Load data async"""
        if state["is_loading"]:
            return
        
        state["is_loading"] = True
        loading_indicator.visible = True
        page.update()

        try:
            filters = {
                "search": state["search_text"],
                "trang_thai": state["filter_trang_thai"],
            }
            
            total = count_classes(**filters)
            classes = fetch_classes(
                page=state["page_index"],
                page_size=PAGE_SIZE,
                **filters
            )
            
            state["total_records"] = total
            state["classes"] = classes
            state["is_loading"] = False
            loading_indicator.visible = False
            
            table.rows.clear()
            for c in classes:
                table.rows.append(build_row(c))
            
            update_pagination()
            selected_count_text.value = f"Đã chọn: {len(state['selected_ids'])}"
            page.update()
            
        except Exception as load_error:
            error_msg = str(load_error)
            pagination_text.value = f"Lỗi: {error_msg}"
            state["is_loading"] = False
            loading_indicator.visible = False
            page.update()

    def open_add_dialog(e):
        dialog_container = ft.Container()
        dialog_message_manager = MessageManager(page, dialog_container)
        
        chi_doan_field = ft.TextField(label="Chi đoàn *", hint_text="VD: 76DCHT01", expand=True, autofocus=True)
        si_so_field = ft.TextField(label="Sĩ số", value="0", keyboard_type=ft.KeyboardType.NUMBER, expand=True)
        so_luong_da_ky_field = ft.TextField(label="Đã ký", value="0", keyboard_type=ft.KeyboardType.NUMBER, expand=True)
        
        doan_phi_field = ft.TextField(label="Đoàn phí", value="0", keyboard_type=ft.KeyboardType.NUMBER, expand=True)
        hoi_phi_field = ft.TextField(label="Hội phí", value="0", keyboard_type=ft.KeyboardType.NUMBER, expand=True)
        tien_da_nop_field = ft.TextField(label="Tiền đã nộp", value="0", keyboard_type=ft.KeyboardType.NUMBER, expand=True)
        
        ghi_chu_field = ft.TextField(label="Ghi chú", value="", multiline=True, min_lines=2, max_lines=4)
        
        vi_tri_field = ft.TextField(
            label="Vị trí lưu sổ",
            value="",
            hint_text="VD: Tủ A1",
            disabled=True,
            expand=True,
            bgcolor=ft.Colors.GREY_100
        )

        def on_status_change(e):
            is_saving = (e.control.value == "Đang lưu VP")
            vi_tri_field.disabled = not is_saving
            vi_tri_field.bgcolor = ft.Colors.WHITE if is_saving else ft.Colors.GREY_100
            
            if is_saving:
                vi_tri_field.focus()
            else:
                vi_tri_field.value = ""
            vi_tri_field.update()

        status_radio = ft.RadioGroup(
            content=ft.Row([
                ft.Radio(value="Chưa tiếp nhận", label="Chưa nhận"),
                ft.Radio(value="Đang lưu VP", label="Đang lưu VP"),
                ft.Radio(value="Đã tiếp nhận", label="Đã trả"),
            ], spacing=5),
            value="Chưa tiếp nhận",
            on_change=on_status_change
        )

        async def handle_submit(e):
            submit_btn.disabled = True
            cancel_btn.disabled = True
            page.update()

            try:
                chi_doan_val = (chi_doan_field.value or "").strip()
                if not chi_doan_val:
                    submit_btn.disabled = False
                    cancel_btn.disabled = False
                    dialog_message_manager.error("Vui lòng nhập chi đoàn")
                    return

                def p_int(v): return int(v) if v and v.strip().isdigit() else 0
                def p_float(v): 
                    try: return float(v) if v else 0.0
                    except: return 0.0

                vi_tri_val = (vi_tri_field.value or "").strip()
                ghi_chu_val = (ghi_chu_field.value or "").strip()

                payload = {
                    "chi_doan": chi_doan_val,
                    "si_so": p_int(si_so_field.value),
                    "so_luong_da_ky": p_int(so_luong_da_ky_field.value),
                    "doan_phi": p_float(doan_phi_field.value),
                    "hoi_phi": p_float(hoi_phi_field.value),
                    "tien_da_nop": p_float(tien_da_nop_field.value),
                    "trang_thai_so": status_radio.value,
                    "vi_tri_luu_so": vi_tri_val,
                    "ghi_chu": ghi_chu_val,
                }

                create_class(payload)
                
                close_dialog_safe()
                message_manager.success(f"Đã thêm lớp {chi_doan_val}")
                await load_data_async()
                
            except Exception as ex:
                submit_btn.disabled = False
                cancel_btn.disabled = False
                dialog_message_manager.error(f"Lỗi: {ex}")
                page.update()

        cancel_btn = ft.TextButton("Hủy", on_click=lambda _: close_dialog_safe())
        submit_btn = ft.ElevatedButton(
            "Thêm lớp", 
            on_click=lambda e: page.run_task(handle_submit, e),
            bgcolor=ft.Colors.GREEN_600, 
            color=ft.Colors.WHITE
        )

        content = ft.Container(
            width=650,
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
                            ft.Text("Thêm lớp mới", size=16, weight=ft.FontWeight.BOLD, color=ft.Colors.GREEN_900),
                            ft.Text("Nhập thông tin chi đoàn", size=12, color=ft.Colors.GREY_700),
                        ], spacing=2)
                    ], spacing=10),
                    padding=10, 
                    border=ft.border.all(1, ft.Colors.GREEN_100), 
                    border_radius=8, 
                    bgcolor=ft.Colors.GREEN_50
                ),
                ft.Divider(height=10, color=ft.Colors.TRANSPARENT),
                chi_doan_field,
                ft.Row([si_so_field, so_luong_da_ky_field], spacing=15),
                ft.Row([doan_phi_field, hoi_phi_field, tien_da_nop_field], spacing=15),
                ft.Divider(height=1, color=ft.Colors.GREY_100),
                ft.Container(
                    content=ft.Row([status_radio, vi_tri_field], spacing=15, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                    bgcolor=ft.Colors.GREY_50, 
                    padding=10, 
                    border_radius=8, 
                    border=ft.border.all(1, ft.Colors.GREY_200)
                ),
                ft.Divider(height=1, color=ft.Colors.GREY_100),
                ghi_chu_field
            ], spacing=12, scroll=ft.ScrollMode.AUTO, height=450)
        )
        
        dialog_container.content = ft.Stack([content])
        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Row([
                CustomIcon.create(CustomIcon.ADD, size=24), 
                ft.Text("Thêm lớp mới", weight=ft.FontWeight.BOLD)
            ], spacing=10),
            content=dialog_container,
            actions=[cancel_btn, submit_btn],
            bgcolor=ft.Colors.WHITE, 
            content_padding=24
        )
        show_dialog_safe(dialog)

    def open_edit_dialog(cls: dict):

        dialog_container = ft.Container()
        dialog_message_manager = MessageManager(page, dialog_container)

        def safe_str(val): 
            return str(val) if val is not None else "0"
        
        def safe_str_empty(val):
            return str(val) if val is not None else ""
        
        chi_doan = cls.get("chi_doan", "N/A")
        
        si_so_field = ft.TextField(label="Sĩ số", value=safe_str(cls.get("si_so")), keyboard_type=ft.KeyboardType.NUMBER, expand=True)
        so_luong_da_ky_field = ft.TextField(label="Đã ký", value=safe_str(cls.get("so_luong_da_ky")), keyboard_type=ft.KeyboardType.NUMBER, expand=True)
        
        doan_phi_field = ft.TextField(label="Đoàn phí", value=safe_str(cls.get("doan_phi")), keyboard_type=ft.KeyboardType.NUMBER, expand=True)
        hoi_phi_field = ft.TextField(label="Hội phí", value=safe_str(cls.get("hoi_phi")), keyboard_type=ft.KeyboardType.NUMBER, expand=True)
        tien_da_nop_field = ft.TextField(label="Tiền đã nộp", value=safe_str(cls.get("tien_da_nop")), keyboard_type=ft.KeyboardType.NUMBER, expand=True)
        
        ghi_chu_field = ft.TextField(label="Ghi chú", value=safe_str_empty(cls.get("ghi_chu")), multiline=True, min_lines=2, max_lines=4)

        current_trang_thai = cls.get("trang_thai_so", "Chưa tiếp nhận")
        
        vi_tri_field = ft.TextField(
            label="Vị trí lưu sổ",
            value=safe_str_empty(cls.get("vi_tri_luu_so")),
            hint_text="VD: Tủ A1",
            disabled=(current_trang_thai != "Đang lưu VP"),
            expand=True,
            bgcolor=ft.Colors.WHITE if current_trang_thai == "Đang lưu VP" else ft.Colors.GREY_100
        )

        def on_status_change(e):
            is_saving = (e.control.value == "Đang lưu VP")
            vi_tri_field.disabled = not is_saving
            vi_tri_field.bgcolor = ft.Colors.WHITE if is_saving else ft.Colors.GREY_100
            
            if is_saving:
                vi_tri_field.focus()
            else:
                vi_tri_field.value = ""
            
            vi_tri_field.update()

        status_radio = ft.RadioGroup(
            content=ft.Row([
                ft.Radio(value="Chưa tiếp nhận", label="Chưa nhận"),
                ft.Radio(value="Đang lưu VP", label="Đang lưu VP"),
                ft.Radio(value="Đã tiếp nhận", label="Đã trả"),
            ], spacing=5),
            value=current_trang_thai,
            on_change=on_status_change
        )

        async def handle_submit(e):
            submit_btn.disabled = True
            cancel_btn.disabled = True
            page.update()

            try:
                def p_int(v): return int(v) if v and v.strip().isdigit() else 0
                def p_float(v): 
                    try: return float(v) if v else 0.0
                    except: return 0.0

                vi_tri_val = (vi_tri_field.value or "").strip()
                ghi_chu_val = (ghi_chu_field.value or "").strip()

                payload = {
                    "si_so": p_int(si_so_field.value),
                    "so_luong_da_ky": p_int(so_luong_da_ky_field.value),
                    "doan_phi": p_float(doan_phi_field.value),
                    "hoi_phi": p_float(hoi_phi_field.value),
                    "tien_da_nop": p_float(tien_da_nop_field.value),
                    "trang_thai_so": status_radio.value,
                    "vi_tri_luu_so": vi_tri_val,
                    "ghi_chu": ghi_chu_val,
                }

                update_class(cls["id"], payload)
                
                close_dialog_safe()
                message_manager.success(f"Đã cập nhật lớp {chi_doan}")
                await load_data_async()
                
            except Exception as ex:
                submit_btn.disabled = False
                cancel_btn.disabled = False
                dialog_message_manager.error(f"Lỗi: {ex}")
                page.update()

        cancel_btn = ft.TextButton("Hủy", on_click=lambda _: close_dialog_safe())
        submit_btn = ft.ElevatedButton(
            "Lưu thay đổi", 
            on_click=lambda e: page.run_task(handle_submit, e),
            bgcolor=ft.Colors.BLUE_600, 
            color=ft.Colors.WHITE
        )

        content = ft.Container(
            width=650,
            content=ft.Column([
                ft.Container(
                    content=ft.Row([
                        ft.Container(
                            content=CustomIcon.create(CustomIcon.CLASS, size=24), 
                            padding=10, 
                            bgcolor=ft.Colors.BLUE_50, 
                            border_radius=50
                        ),
                        ft.Column([
                            ft.Text(chi_doan, size=16, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_900),
                            ft.Text("Chỉnh sửa thông tin chi đoàn", size=12, color=ft.Colors.GREY_700),
                        ], spacing=2)
                    ], spacing=10),
                    padding=10, 
                    border=ft.border.all(1, ft.Colors.BLUE_100), 
                    border_radius=8, 
                    bgcolor=ft.Colors.BLUE_50
                ),
                ft.Divider(height=10, color=ft.Colors.TRANSPARENT),
                ft.Row([si_so_field, so_luong_da_ky_field], spacing=15),
                ft.Row([doan_phi_field, hoi_phi_field, tien_da_nop_field], spacing=15),
                ft.Divider(height=1, color=ft.Colors.GREY_100),
                ft.Container(
                    content=ft.Row([status_radio, vi_tri_field], spacing=15, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                    bgcolor=ft.Colors.GREY_50, 
                    padding=10, 
                    border_radius=8, 
                    border=ft.border.all(1, ft.Colors.GREY_200)
                ),
                ft.Divider(height=1, color=ft.Colors.GREY_100),
                ghi_chu_field
            ], spacing=12, scroll=ft.ScrollMode.AUTO, height=450)
        )
        
        dialog_container.content = ft.Stack([content])
        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Row([
                CustomIcon.create(CustomIcon.EDIT, size=24), 
                ft.Text("Sửa thông tin lớp", weight=ft.FontWeight.BOLD)
            ], spacing=10),
            content=dialog_container,
            actions=[cancel_btn, submit_btn],
            bgcolor=ft.Colors.WHITE, 
            content_padding=24
        )
        show_dialog_safe(dialog)

    def open_delete_confirm_dialog(cls: dict):
        
        chi_doan = cls.get("chi_doan", "N/A")
        
        async def handle_delete(e):
            delete_btn.disabled = True
            cancel_btn.disabled = True
            page.update()
            
            try:
                delete_class(cls["id"])
                close_dialog_safe()
                message_manager.success(f"Đã xóa lớp {chi_doan}")
                await load_data_async()
                
            except Exception as ex:
                delete_btn.disabled = False
                cancel_btn.disabled = False
                message_manager.error(f"Lỗi xóa: {ex}")
                close_dialog_safe()
        
        cancel_btn = ft.TextButton("Hủy", on_click=lambda _: close_dialog_safe())
        delete_btn = ft.ElevatedButton(
            "Xóa", 
            on_click=lambda e: page.run_task(handle_delete, e),
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
                                ft.Text("Bạn có chắc chắn muốn xóa lớp này?", size=14, weight=ft.FontWeight.W_500),
                                ft.Text(chi_doan, size=16, weight=ft.FontWeight.BOLD, color=ft.Colors.RED_700),
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

    def build_row(c: dict):
        checkbox = ft.Checkbox(
            value=c["id"] in state["selected_ids"],
            on_change=lambda e, id=c["id"]: toggle_selection(id, e.control.value)
        )

        vi_tri = c.get("vi_tri_luu_so", "") or ""
        ghi_chu = c.get("ghi_chu", "") or ""
        
        return ft.DataRow(
            cells=[
                ft.DataCell(ft.Text(c["chi_doan"])),
                ft.DataCell(ft.Text(str(c.get("si_so", 0)))),
                ft.DataCell(ft.Text(str(c.get("so_luong_da_ky", 0)))),
                ft.DataCell(ft.Text(f"{c.get('doan_phi', 0):,.0f}")),
                ft.DataCell(ft.Text(f"{c.get('hoi_phi', 0):,.0f}")),
                ft.DataCell(ft.Text(f"{c.get('tien_da_nop', 0):,.0f}")),
                
                ft.DataCell(
                    ft.Text(
                        vi_tri[:25] + "..." if len(vi_tri) > 25 else vi_tri,
                        size=13,
                        color=ft.Colors.BLUE_GREY_700,
                        weight=ft.FontWeight.W_500,
                        tooltip=vi_tri if len(vi_tri) > 25 else None
                    )
                ),
                
                ft.DataCell(
                    ft.Text(
                        ghi_chu[:25] + "..." if len(ghi_chu) > 25 else ghi_chu,
                        size=13,
                        color=ft.Colors.GREY_600,
                        weight=ft.FontWeight.W_400,
                        tooltip=ghi_chu if len(ghi_chu) > 25 else None
                    )
                ),
                
                ft.DataCell(ft.Text(c.get("trang_thai_so", ""))),
                
                ft.DataCell(
                    ft.Row([
                        checkbox,
                        ft.Container(
                            content=CustomIcon.create(CustomIcon.EDIT, size=18),
                            on_click=lambda e, cls=c: open_edit_dialog(cls),
                            tooltip="Sửa lớp",
                            padding=8,
                            border_radius=4,
                            ink=True,
                        ),
                        ft.Container(
                            content=CustomIcon.create(CustomIcon.DELETE, size=18),
                            on_click=lambda e, cls=c: open_delete_confirm_dialog(cls),
                            tooltip="Xóa lớp",
                            padding=8,
                            border_radius=4,
                            ink=True,
                        ),
                    ], spacing=4)
                ),
            ],
        )
    
    def toggle_selection(id: str, selected: bool):
        if selected:
            state["selected_ids"].add(id)
        else:
            state["selected_ids"].discard(id)
        
        select_all_checkbox.value = (
            len(state["selected_ids"]) == len(state["classes"]) 
            and len(state["classes"]) > 0
        )
        
        selected_count_text.value = f"Đã chọn: {len(state['selected_ids'])}"
        page.update()
    
    def toggle_select_all(select_all: bool):
        if select_all:
            for c in state["classes"]:
                state["selected_ids"].add(c["id"])
        else:
            for c in state["classes"]:
                state["selected_ids"].discard(c["id"])
        
        table.rows.clear()
        for c in state["classes"]:
            table.rows.append(build_row(c))
        
        selected_count_text.value = f"Đã chọn: {len(state['selected_ids'])}"
        page.update()

    def on_search(e):
        state["search_text"] = e.control.value.strip()
        state["page_index"] = 1
        state["selected_ids"].clear()
        select_all_checkbox.value = False
        page.run_task(load_data_async)
    
    def on_filter_trang_thai(e):
        state["filter_trang_thai"] = e.control.value if e.control.value else ""
        state["page_index"] = 1
        state["selected_ids"].clear()
        select_all_checkbox.value = False
        page.run_task(load_data_async)

    def update_pagination():
        total_pages = max(1, (state["total_records"] + PAGE_SIZE - 1) // PAGE_SIZE)
        pagination_text.value = f"Trang {state['page_index']} / {total_pages} – Tổng {state['total_records']} lớp"

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

    def open_bulk_update_dialog(e):
        selected_count = len(state["selected_ids"])
        if not state["selected_ids"]:
            message_manager.warning("Chưa chọn lớp nào để cập nhật")
            return

        dialog_container = ft.Container()
        dialog_message_manager = MessageManager(page, dialog_container)
        
        field_states = {
            "trang_thai_so": False,
            "vi_tri_luu_so": False,
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

        enable_trang_thai = ft.Checkbox(value=False, on_change=lambda e: toggle_field("trang_thai_so", e.control.value))
        trang_thai_dropdown = ft.Dropdown(
            label="Trạng thái mới", value="Chưa tiếp nhận", disabled=True, expand=True, text_size=13, height=40, content_padding=10,
            options=[ft.dropdown.Option("Chưa tiếp nhận"), ft.dropdown.Option("Đang lưu VP"), ft.dropdown.Option("Đã tiếp nhận")]
        )

        enable_vi_tri = ft.Checkbox(value=False, on_change=lambda e: toggle_field("vi_tri_luu_so", e.control.value))
        vi_tri_field = ft.TextField(label="Vị trí mới", hint_text="Tủ A - Ngăn B", disabled=True, expand=True, text_size=13, height=40, content_padding=10)
        clear_vi_tri_btn = ft.IconButton(icon=ft.Icons.CLEAR, icon_size=16, tooltip="Xóa", visible=False, on_click=lambda e: set_field_value("vi_tri_luu_so", ""))

        def on_trang_thai_changed(e):
            if e.control.value == "Đang lưu VP" and not field_states["vi_tri_luu_so"]:
                enable_vi_tri.value = True
                toggle_field("vi_tri_luu_so", True)
        trang_thai_dropdown.on_change = on_trang_thai_changed

        enable_ghi_chu = ft.Checkbox(value=False, on_change=lambda e: toggle_field("ghi_chu", e.control.value))
        ghi_chu_field = ft.TextField(label="Ghi chú mới", hint_text="Nhập ghi chú...", multiline=True, min_lines=1, max_lines=3, disabled=True, expand=True, text_size=13, content_padding=10)
        clear_ghi_chu_btn = ft.IconButton(icon=ft.Icons.CLEAR, icon_size=16, tooltip="Xóa", visible=False, on_click=lambda e: set_field_value("ghi_chu", ""))

        field_controls = {
            "trang_thai_so": {"checkbox": enable_trang_thai, "input": trang_thai_dropdown},
            "vi_tri_luu_so": {"checkbox": enable_vi_tri, "input": vi_tri_field, "clear": clear_vi_tri_btn},
            "ghi_chu": {"checkbox": enable_ghi_chu, "input": ghi_chu_field, "clear": clear_ghi_chu_btn},
        }

        async def handle_submit(e):
            submit_btn.disabled = True
            cancel_btn.disabled = True
            page.update()
            
            try:
                payload = {}
                if field_states["trang_thai_so"]: 
                    payload["trang_thai_so"] = trang_thai_dropdown.value
                if field_states["vi_tri_luu_so"]: 
                    payload["vi_tri_luu_so"] = vi_tri_field.value.strip() if vi_tri_field.value else ""
                if field_states["ghi_chu"]: 
                    payload["ghi_chu"] = ghi_chu_field.value.strip() if ghi_chu_field.value else ""
                
                if not payload:
                    submit_btn.disabled = False
                    cancel_btn.disabled = False
                    dialog_message_manager.warning("Chưa chọn trường nào để cập nhật")
                    return
                
                bulk_update_classes(list(state["selected_ids"]), payload)
                
                state["selected_ids"].clear()
                select_all_checkbox.value = False
                close_dialog_safe()
                updated_fields = ", ".join(payload.keys())
                message_manager.success(f"Đã cập nhật {selected_count} lớp: {updated_fields}")
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
                                        ft.Text(f"Đang chọn {selected_count} lớp", weight=ft.FontWeight.BOLD, size=15, color=ft.Colors.BLUE_900),
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
                            build_field_row("Trạng thái sổ", enable_trang_thai, trang_thai_dropdown),
                            build_field_row("Vị trí lưu sổ", enable_vi_tri, vi_tri_field, clear_vi_tri_btn),
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

    def import_excel_dialog(e):
        async def select_and_import():
            try:
                import tkinter as tk
                from tkinter import filedialog

                root = tk.Tk()
                root.withdraw()
                root.attributes("-topmost", True)

                file_path = filedialog.askopenfilename(
                    title="Chọn file Excel - Import Quản lý Sinh viên",
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

                from utils.import_export import import_students

                with open(file_path, "rb") as f:
                    file_bytes = f.read()

                imported_count, errors = import_students(file_bytes)

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
                            f"Import xong, thêm {diff} sinh viên nhưng có lỗi"
                        )
                    else:
                        message_manager.error(
                            "Import thất bại, không có dữ liệu hợp lệ"
                        )

                else:
                    if diff > 0:
                        message_manager.success(
                            f"Import thành công {diff} sinh viên"
                        )
                    else:
                        message_manager.info(
                            "File không có sinh viên mới để import"
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
                    "mssv": ["74123456", "74123457", "74123458"],
                    "ho_ten": ["Nguyễn Văn A", "Trần Thị B", "Lê Văn C"],
                    "ngay_sinh": ["01/01/2005", "15/03/2005", "20/07/2005"],
                    "noi_sinh": ["Hà Nội", "Hồ Chí Minh", "Đà Nẵng"],
                    "lop": ["74DCHT22", "74DCHT22", "74DCHT23"],
                    "khoa": ["CNTT", "CNTT", "CNTT"],
                    "trang_thai_so": ["Chưa tiếp nhận", "Đang lưu VP", "Đã tiếp nhận"],
                    "vi_tri_luu_so": ["", "Tủ A3 - Ngăn 2", ""],
                    "ghi_chu": ["", "Cần kiểm tra", ""],
                    "da_nop_doan_phi": ["Có", "Có", "Chưa"],
                    "da_nop_hoi_phi": ["Có", "Chưa", "Chưa"],
                }
                
                df = pd.DataFrame(template_data)
                
                output = BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    df.to_excel(writer, index=False, sheet_name='Quản lý Sinh viên')
                    
                    worksheet = writer.sheets['Quản lý Sinh viên']
                    for idx, col in enumerate(df.columns, 1):
                        max_length = max(
                            df[col].astype(str).map(len).max(),
                            len(str(col))
                        )
                        col_letter = chr(64 + idx)
                        worksheet.column_dimensions[col_letter].width = min(max_length + 3, 40)
                
                downloads_folder = os.path.join(os.path.expanduser("~"), "Downloads")
                filename = "template_import_sinh_vien_K74_K75.xlsx"
                save_path = os.path.join(downloads_folder, filename)
                
                with open(save_path, "wb") as f:
                    f.write(output.getvalue())
                
                required_items = [
                    ("mssv", "Mã số sinh viên (bắt buộc, duy nhất)"),
                    ("ho_ten", "Họ và tên sinh viên"),
                    ("lop", "Tên lớp (VD: 74DCHT22)"),
                    ("khoa", "Tên khoa (VD: CNTT)"),
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
                    ("ngay_sinh", "dd/mm/yyyy (VD: 01/01/2005)"),
                    ("noi_sinh", "Nơi sinh"),
                    ("trang_thai_so", "Chưa tiếp nhận | Đang lưu VP | Đã tiếp nhận"),
                    ("vi_tri_luu_so", "Vị trí lưu hồ sơ (nếu đang lưu VP)"),
                    ("ghi_chu", "Ghi chú"),
                    ("da_nop_doan_phi", "Có | Chưa"),
                    ("da_nop_hoi_phi", "Có | Chưa"),
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
        if not state["selected_mssv"] or len(state["selected_mssv"]) == 0:
            warning_dialog = ft.AlertDialog(
                modal=True,
                title=ft.Row(
                    [
                        CustomIcon.create(CustomIcon.WARNING, size=24),
                        ft.Text("Chưa chọn sinh viên", size=18, weight=ft.FontWeight.BOLD),
                    ],
                    spacing=8,
                ),
                content=ft.Container(
                    width=420,
                    padding=15,
                    bgcolor=ft.Colors.ORANGE_50,
                    border_radius=8,
                    border=ft.border.all(1, ft.Colors.ORANGE_200),
                    content=ft.Text("Vui lòng chọn ít nhất một sinh viên để export.", size=14),
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
        
        selected = list(state["selected_mssv"])
        selected_count = len(selected)
        
        import os
        import datetime
        
        downloads_folder = os.path.join(os.path.expanduser("~"), "Downloads")
        filename = f"export_students_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        save_path = os.path.join(downloads_folder, filename)
        
        message_manager.info(f"Đang xuất {selected_count} sinh viên...")
        
        async def _export():
            try:
                from utils.import_export import export_students
                
                excel_bytes = export_students(selected)
                
                with open(save_path, "wb") as f:
                    f.write(excel_bytes)
                
                file_size = os.path.getsize(save_path) / 1024
                
                content = ft.Column([
                    ft.Row([
                        ft.Container(
                            content=ft.Column([
                                ft.Text("Số lượng", size=12, color=ft.Colors.GREY_700),
                                ft.Text(f"{selected_count} sinh viên", size=18, weight=ft.FontWeight.BOLD, color=ft.Colors.GREY_900),
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
        label="Tìm theo Chi đoàn",
        prefix_icon=ft.Icons.SEARCH,
        hint_text="VD: 76DCHT01",
        width=400,
        on_submit=on_search,
    )
    
    filter_trang_thai_dropdown = ft.Dropdown(
        label="Lọc trạng thái",
        width=180,
        options=[
            ft.dropdown.Option("Chưa tiếp nhận"),
            ft.dropdown.Option("Đang lưu VP"),
            ft.dropdown.Option("Đã tiếp nhận"),
        ],
    )

    filter_trang_thai_dropdown.on_change = on_filter_trang_thai

    buttons = []
    if is_admin(role):
        buttons.extend([
            elevated_button("Thêm lớp", CustomIcon.ADD, on_click=open_add_dialog),
            elevated_button("Tải mẫu", CustomIcon.DOCUMENT, on_click=download_template_dialog),
            elevated_button("Import Excel", CustomIcon.UPLOAD, on_click=import_excel_dialog),
            elevated_button("Export Excel", CustomIcon.DOWNLOAD, on_click=export_excel_action),
        ])
    buttons.append(elevated_button("Sửa hàng loạt", CustomIcon.EDIT, on_click=open_bulk_update_dialog))

    toolbar = ft.Column([
        ft.Row(
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            controls=[
                ft.Row([search_field, filter_trang_thai_dropdown, loading_indicator], spacing=8),
                ft.Row(spacing=8, controls=buttons),
            ],
        ),
        ft.Row([select_all_checkbox, selected_count_text], spacing=12),
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