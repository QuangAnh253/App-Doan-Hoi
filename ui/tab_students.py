# ui/tab_students.py
import flet as ft
import asyncio
from services.students_service import (
    fetch_students,
    count_students,
    bulk_update_students,
    update_student,
    delete_student,
)
from core.auth import is_admin
from ui.icon_helper import CustomIcon, elevated_button
from ui.message_manager import MessageManager

PAGE_SIZE = 100


def StudentsTab(page: ft.Page, role: str):
    
    message_manager = MessageManager(page)
    
    state = {
        "students": [],
        "selected_mssv": set(),
        "page_index": 1,
        "total_records": 0,
        "search_text": "",
        "filter_lop": "",
        "filter_khoa": "",
        "is_loading": False,
        "active_dialog": None,
        "filter_trang_thai": set(),
    }

    loading_indicator = ft.ProgressRing(visible=False, width=30, height=30)
    
    select_all_checkbox = ft.Checkbox(
        label="Chọn tất cả trang này",
        value=False,
        on_change=lambda e: toggle_select_all(e.control.value)
    )
    
    table = ft.DataTable(
        columns=[
            ft.DataColumn(ft.Text("MSSV", weight=ft.FontWeight.BOLD)),
            ft.DataColumn(ft.Text("Họ tên", weight=ft.FontWeight.BOLD)),
            ft.DataColumn(ft.Text("Ngày sinh", weight=ft.FontWeight.BOLD)),
            ft.DataColumn(ft.Text("Nơi sinh", weight=ft.FontWeight.BOLD)),
            ft.DataColumn(ft.Text("Lớp", weight=ft.FontWeight.BOLD)),
            ft.DataColumn(ft.Text("Khoa", weight=ft.FontWeight.BOLD)),
            ft.DataColumn(ft.Text("Trạng thái sổ", weight=ft.FontWeight.BOLD)),
            ft.DataColumn(ft.Text("Vị trí lưu", weight=ft.FontWeight.BOLD)),
            ft.DataColumn(ft.Text("Ghi chú", weight=ft.FontWeight.BOLD)),
            ft.DataColumn(ft.Text("Đoàn phí", weight=ft.FontWeight.BOLD)),
            ft.DataColumn(ft.Text("Hội phí", weight=ft.FontWeight.BOLD)),
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
        try:
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
            
        except Exception:
            pass

    def close_dialog_safe():
        """Đóng dialog an toàn"""
        if state["active_dialog"] is None:
            return
        
        try:
            state["active_dialog"].open = False
            page.update()
            
            async def _delayed_remove():
                import asyncio
                await asyncio.sleep(0.05)
                try:
                    if state["active_dialog"] in page.overlay:
                        page.overlay.remove(state["active_dialog"])
                    state["active_dialog"] = None
                    page.update()
                except:
                    pass
            
            page.run_task(_delayed_remove)
            
        except Exception as ex:
            pass

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
                "lop": state["filter_lop"],
                "khoa": state["filter_khoa"],
                "trang_thai": state["filter_trang_thai"] or None,
            }
            
            total = count_students(**filters)
            students = fetch_students(
                page=state["page_index"],
                page_size=PAGE_SIZE,
                **filters
            )
            
            state["total_records"] = total
            state["students"] = students
            state["is_loading"] = False
            loading_indicator.visible = False
            
            table.rows.clear()
            for s in students:
                table.rows.append(build_row(s))
            
            update_pagination()
            selected_count_text.value = f"Đã chọn: {len(state['selected_mssv'])}"
            page.update()
            
        except Exception as ex:
            pagination_text.value = f"Lỗi: {ex}"
            state["is_loading"] = False
            loading_indicator.visible = False
            page.update()

    def open_add_student_dialog(e):
        """Thêm sinh viên mới"""
        dialog_container = ft.Container()
        dialog_message_manager = MessageManager(page, dialog_container)
        
        # Basic info fields
        mssv_field = ft.TextField(
            label="MSSV *", 
            hint_text="VD: 74123456", 
            expand=True, 
            autofocus=True,
            text_size=13, 
            height=45, 
            content_padding=12
        )
        ho_ten_field = ft.TextField(
            label="Họ tên *", 
            hint_text="Nhập họ và tên",
            expand=True,
            text_size=13, 
            height=45, 
            content_padding=12
        )
        
        ngay_sinh_field = ft.TextField(
            label="Ngày sinh", 
            hint_text="dd/mm/yyyy",
            expand=True,
            text_size=13, 
            height=45, 
            content_padding=12
        )
        noi_sinh_field = ft.TextField(
            label="Nơi sinh", 
            hint_text="Nhập nơi sinh",
            expand=True,
            text_size=13, 
            height=45, 
            content_padding=12
        )
        
        lop_field = ft.TextField(
            label="Lớp *", 
            hint_text="VD: 74DCHT22",
            expand=True,
            text_size=13, 
            height=45, 
            content_padding=12
        )
        khoa_field = ft.TextField(
            label="Khoa *", 
            hint_text="VD: CNTT",
            expand=True,
            text_size=13, 
            height=45, 
            content_padding=12
        )
        
        # Status fields
        vi_tri_field = ft.TextField(
            label="Vị trí lưu sổ",
            hint_text="VD: Tủ A - Ngăn 2",
            disabled=True,
            expand=True,
            text_size=13,
            height=45,
            content_padding=12,
            bgcolor=ft.Colors.GREY_100
        )
        
        async def on_status_change(e):
            status = e.control.value
            is_saving = (status == "Đang lưu VP")
            
            vi_tri_field.disabled = not is_saving
            vi_tri_field.bgcolor = ft.Colors.WHITE if is_saving else ft.Colors.GREY_100
            
            if not is_saving:
                vi_tri_field.value = ""
            else:
                try:
                    await vi_tri_field.focus_async()
                except:
                    pass
            
            vi_tri_field.update()
        
        status_radio_group = ft.RadioGroup(
            content=ft.Row([
                ft.Radio(value="Chưa tiếp nhận", label="Chưa nhận"),
                ft.Radio(value="Đang lưu VP", label="Đang lưu VP"),
                ft.Radio(value="Đã tiếp nhận", label="Đã trả SV"),
            ], spacing=10),
            value="Chưa tiếp nhận",
            on_change=on_status_change
        )
        
        da_nop_doan_phi = ft.Switch(label="Đã nộp Đoàn phí", value=False)
        da_nop_hoi_phi = ft.Switch(label="Đã nộp Hội phí", value=False)
        
        ghi_chu_field = ft.TextField(
            label="Ghi chú",
            multiline=True,
            min_lines=2,
            max_lines=4,
            text_size=13,
            content_padding=12
        )
        
        async def handle_submit(e):
            submit_btn.disabled = True
            cancel_btn.disabled = True
            page.update()
            
            try:
                def safe_val(val):
                    return val.strip() if val else ""
                
                mssv = safe_val(mssv_field.value)
                ho_ten = safe_val(ho_ten_field.value)
                lop = safe_val(lop_field.value)
                khoa = safe_val(khoa_field.value)
                
                if not mssv:
                    submit_btn.disabled = False
                    cancel_btn.disabled = False
                    dialog_message_manager.warning("Vui lòng nhập MSSV")
                    return
                
                if not ho_ten:
                    submit_btn.disabled = False
                    cancel_btn.disabled = False
                    dialog_message_manager.warning("Vui lòng nhập họ tên")
                    return
                
                if not lop:
                    submit_btn.disabled = False
                    cancel_btn.disabled = False
                    dialog_message_manager.warning("Vui lòng nhập lớp")
                    return
                
                if not khoa:
                    submit_btn.disabled = False
                    cancel_btn.disabled = False
                    dialog_message_manager.warning("Vui lòng nhập khoa")
                    return
                
                from services.students_service import add_student
                
                payload = {
                    "mssv": mssv,
                    "ho_ten": ho_ten,
                    "ngay_sinh": safe_val(ngay_sinh_field.value),
                    "noi_sinh": safe_val(noi_sinh_field.value),
                    "lop": lop,
                    "khoa": khoa,
                    "trang_thai_so": status_radio_group.value,
                    "vi_tri_luu_so": safe_val(vi_tri_field.value),
                    "ghi_chu": safe_val(ghi_chu_field.value),
                    "da_nop_doan_phi": da_nop_doan_phi.value,
                    "da_nop_hoi_phi": da_nop_hoi_phi.value,
                }
                
                add_student(payload)
                
                close_dialog_safe()
                message_manager.success(f"Đã thêm sinh viên: {ho_ten}")
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
            "Thêm sinh viên",
            on_click=lambda e: page.run_task(handle_submit, e),
            bgcolor=ft.Colors.BLUE_600,
            color=ft.Colors.WHITE,
            elevation=0
        )
        
        content_container = ft.Container(
            width=650,
            content=ft.Column(
                controls=[
                    ft.Container(
                        content=ft.Row([
                            ft.Container(
                                content=ft.Icon(ft.Icons.PERSON_ADD, color=ft.Colors.BLUE_700),
                                padding=10,
                                bgcolor=ft.Colors.WHITE,
                                border_radius=50,
                                border=ft.border.all(1, ft.Colors.BLUE_100)
                            ),
                            ft.Column([
                                ft.Text("Thêm sinh viên mới", weight=ft.FontWeight.BOLD, size=16, color=ft.Colors.BLUE_900),
                                ft.Text("Vui lòng điền đầy đủ thông tin bắt buộc (*)", size=13, color=ft.Colors.GREY_700),
                            ], spacing=2, tight=True)
                        ], spacing=12),
                        padding=12,
                        bgcolor=ft.Colors.BLUE_50,
                        border=ft.border.all(1, ft.Colors.BLUE_200),
                        border_radius=8
                    ),
                    ft.Divider(height=10, color=ft.Colors.TRANSPARENT),
                    ft.Row([mssv_field, ho_ten_field], spacing=15),
                    ft.Row([ngay_sinh_field, noi_sinh_field], spacing=15),
                    ft.Row([lop_field, khoa_field], spacing=15),
                    ft.Divider(height=1, color=ft.Colors.GREY_100),
                    ft.Text("Trạng thái hồ sơ", size=12, weight=ft.FontWeight.BOLD, color=ft.Colors.GREY_600),
                    ft.Container(
                        content=ft.Column([
                            status_radio_group,
                            ft.Container(height=5),
                            vi_tri_field
                        ], spacing=10),
                        bgcolor=ft.Colors.GREY_50,
                        padding=15,
                        border_radius=8,
                        border=ft.border.all(1, ft.Colors.GREY_200)
                    ),
                    ft.Divider(height=1, color=ft.Colors.GREY_100),
                    ft.Row([da_nop_doan_phi, da_nop_hoi_phi], spacing=30),
                    ghi_chu_field,
                ],
                spacing=12,
                scroll=ft.ScrollMode.AUTO,
                height=500,
            )
        )
        
        dialog_container.content = ft.Stack([content_container])
        
        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Row([
                CustomIcon.create(CustomIcon.ADD, size=24),
                ft.Text("Thêm sinh viên", size=18, weight=ft.FontWeight.W_600)
            ], spacing=10, tight=True),
            content=dialog_container,
            actions=[cancel_btn, submit_btn],
            actions_alignment=ft.MainAxisAlignment.END,
            actions_padding=ft.padding.only(right=20, bottom=16),
            content_padding=ft.padding.all(24),
            shape=ft.RoundedRectangleBorder(radius=12),
            bgcolor=ft.Colors.WHITE,
        )
        
        show_dialog_safe(dialog)
        page.update()

    def open_edit_dialog(student: dict):
        """Mở dialog sửa sinh viên - Fix lỗi Async Focus & NoneType Strip"""
        
        mssv = student["mssv"]
        ho_ten = student.get("ho_ten", "Không tên")
        
        dialog_container = ft.Container()
        dialog_message_manager = MessageManager(page, dialog_container)

        ngay_sinh_field = ft.TextField(
            label="Ngày sinh", value=student.get("ngay_sinh") or "", hint_text="dd/mm/yyyy",
            expand=True, text_size=13, height=45, content_padding=12
        )
        noi_sinh_field = ft.TextField(
            label="Nơi sinh", value=student.get("noi_sinh") or "", hint_text="Nhập nơi sinh",
            expand=True, text_size=13, height=45, content_padding=12
        )
        
        lop_field = ft.TextField(
            label="Lớp", value=student.get("lop") or "",
            expand=True, text_size=13, height=45, content_padding=12
        )
        khoa_field = ft.TextField(
            label="Khoa", value=student.get("khoa") or "",
            expand=True, text_size=13, height=45, content_padding=12
        )

        current_trang_thai = student.get("trang_thai_so", "Chưa tiếp nhận")
        
        vi_tri_field = ft.TextField(
            label="Vị trí lưu sổ",
            value=student.get("vi_tri_luu_so") or "",
            hint_text="VD: Tủ A - Ngăn 2",
            disabled=(current_trang_thai != "Đang lưu VP"),
            expand=True, text_size=13, height=45, content_padding=12,
            bgcolor=ft.Colors.WHITE if current_trang_thai == "Đang lưu VP" else ft.Colors.GREY_100
        )

        async def on_status_change(e):
            status = e.control.value
            is_saving = (status == "Đang lưu VP")
            
            vi_tri_field.disabled = not is_saving
            vi_tri_field.bgcolor = ft.Colors.WHITE if is_saving else ft.Colors.GREY_100
            
            if not is_saving:
                vi_tri_field.value = ""
            else:
                try:
                    await vi_tri_field.focus_async() 
                except:
                    pass
                
            vi_tri_field.update()

        status_radio_group = ft.RadioGroup(
            content=ft.Row([
                ft.Radio(value="Chưa tiếp nhận", label="Chưa nhận"),
                ft.Radio(value="Đang lưu VP", label="Đang lưu VP"),
                ft.Radio(value="Đã tiếp nhận", label="Đã trả SV"),
            ], spacing=10),
            value=current_trang_thai,
            on_change=on_status_change
        )

        da_nop_doan_phi = ft.Switch(label="Đã nộp Đoàn phí", value=student.get("da_nop_doan_phi", False))
        da_nop_hoi_phi = ft.Switch(label="Đã nộp Hội phí", value=student.get("da_nop_hoi_phi", False))

        ghi_chu_field = ft.TextField(
            label="Ghi chú", value=student.get("ghi_chu") or "",
            multiline=True, min_lines=2, max_lines=4,
            text_size=13, content_padding=12
        )

        async def handle_submit(e):
            submit_btn.disabled = True
            cancel_btn.disabled = True
            page.update()

            try:
                selected_status = status_radio_group.value 

                def safe_val(val):
                    return val.strip() if val else ""

                payload = {
                    "ngay_sinh": safe_val(ngay_sinh_field.value),
                    "noi_sinh": safe_val(noi_sinh_field.value),
                    "lop": safe_val(lop_field.value),
                    "khoa": safe_val(khoa_field.value),
                    "trang_thai_so": selected_status,
                    "vi_tri_luu_so": safe_val(vi_tri_field.value),
                    "ghi_chu": safe_val(ghi_chu_field.value),
                    "da_nop_doan_phi": da_nop_doan_phi.value,
                    "da_nop_hoi_phi": da_nop_hoi_phi.value,
                }

                update_student(mssv, payload)

                close_dialog_safe()
                message_manager.success(f"Đã cập nhật: {ho_ten}")
                await load_data_async()

            except Exception as ex:
                submit_btn.disabled = False
                cancel_btn.disabled = False
                dialog_message_manager.error(f"Lỗi: {ex}")
                page.update()

        cancel_btn = ft.TextButton("Hủy bỏ", on_click=lambda e: close_dialog_safe(), style=ft.ButtonStyle(color=ft.Colors.GREY_600))
        submit_btn = ft.ElevatedButton("Lưu thay đổi", on_click=lambda e: page.run_task(handle_submit, e), bgcolor=ft.Colors.BLUE_600, color=ft.Colors.WHITE, elevation=0)

        content_container = ft.Container(
            width=650,
            content=ft.Column(
                controls=[
                    ft.Container(
                        content=ft.Row(
                            [
                                ft.Container(
                                    content=ft.Icon(ft.Icons.PERSON, color=ft.Colors.BLUE_700),
                                    padding=10, bgcolor=ft.Colors.WHITE, border_radius=50,
                                    border=ft.border.all(1, ft.Colors.BLUE_100)
                                ),
                                ft.Column(
                                    [
                                        ft.Text(ho_ten, weight=ft.FontWeight.BOLD, size=16, color=ft.Colors.BLUE_900),
                                        ft.Text(f"MSSV: {mssv}", size=13, color=ft.Colors.GREY_700),
                                    ],
                                    spacing=2, tight=True
                                )
                            ],
                            spacing=12,
                        ),
                        padding=12, bgcolor=ft.Colors.BLUE_50,
                        border=ft.border.all(1, ft.Colors.BLUE_200), border_radius=8
                    ),
                    ft.Divider(height=10, color=ft.Colors.TRANSPARENT),
                    ft.Row([ngay_sinh_field, noi_sinh_field], spacing=15),
                    ft.Row([lop_field, khoa_field], spacing=15),
                    ft.Divider(height=1, color=ft.Colors.GREY_100),
                    ft.Text("Trạng thái hồ sơ", size=12, weight=ft.FontWeight.BOLD, color=ft.Colors.GREY_600),
                    ft.Container(
                        content=ft.Column([
                            status_radio_group,
                            ft.Container(height=5),
                            vi_tri_field
                        ], spacing=10),
                        bgcolor=ft.Colors.GREY_50, padding=15, border_radius=8,
                        border=ft.border.all(1, ft.Colors.GREY_200)
                    ),
                    ft.Divider(height=1, color=ft.Colors.GREY_100),
                    ft.Row([da_nop_doan_phi, da_nop_hoi_phi], spacing=30),
                    ghi_chu_field,
                ],
                spacing=12, scroll=ft.ScrollMode.AUTO, height=500,
            )
        )
        dialog_container.content = ft.Stack([content_container])
        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Row([CustomIcon.create(CustomIcon.EDIT, size=24), ft.Text("Chỉnh sửa thông tin", size=18, weight=ft.FontWeight.W_600)], spacing=10, tight=True),
            content=dialog_container,
            actions=[cancel_btn, submit_btn],
            actions_alignment=ft.MainAxisAlignment.END,
            actions_padding=ft.padding.only(right=20, bottom=16),
            content_padding=ft.padding.all(24),
            shape=ft.RoundedRectangleBorder(radius=12),
            bgcolor=ft.Colors.WHITE,
        )
        show_dialog_safe(dialog)
        page.update()

    def open_filter_trang_thai_dialog(e):
        dialog_container = ft.Container()
        dialog_message_manager = MessageManager(page, dialog_container)
        
        current_filters = state["filter_trang_thai"].copy()
        
        checkbox_dang_luu = ft.Checkbox(
            label="Đang lưu sổ tại văn phòng",
            value="dang_luu_vp" in current_filters
        )
        checkbox_da_tra = ft.Checkbox(
            label="Đã trả sổ",
            value="da_tra_so" in current_filters
        )
        checkbox_chua_doan_phi = ft.Checkbox(
            label="Chưa đóng đoàn phí",
            value="chua_doan_phi" in current_filters
        )
        checkbox_chua_hoi_phi = ft.Checkbox(
            label="Chưa đóng hội phí",
            value="chua_hoi_phi" in current_filters
        )
        
        async def handle_apply(e):
            apply_btn.disabled = True
            cancel_btn.disabled = True
            page.update()
            
            try:
                selected = set()
                if checkbox_dang_luu.value:
                    selected.add("dang_luu_vp")
                if checkbox_da_tra.value:
                    selected.add("da_tra_so")
                if checkbox_chua_doan_phi.value:
                    selected.add("chua_doan_phi")
                if checkbox_chua_hoi_phi.value:
                    selected.add("chua_hoi_phi")
                
                if not selected:
                    apply_btn.disabled = False
                    cancel_btn.disabled = False
                    dialog_message_manager.warning("Chưa chọn trạng thái nào")
                    return
                
                state["filter_trang_thai"] = selected
                state["page_index"] = 1
                state["selected_mssv"].clear()
                select_all_checkbox.value = False
                
                close_dialog_safe()
                message_manager.success(f"Đã áp dụng lọc {len(selected)} trạng thái")
                update_filter_button_color()
                await load_data_async()
                
            except Exception as ex:
                apply_btn.disabled = False
                cancel_btn.disabled = False
                dialog_message_manager.error(f"Lỗi: {ex}")
        
        def handle_clear(e):
            state["filter_trang_thai"].clear()
            state["page_index"] = 1
            state["selected_mssv"].clear()
            select_all_checkbox.value = False
            close_dialog_safe()
            message_manager.info("Đã xóa bộ lọc trạng thái")
            update_filter_button_color()
            page.run_task(load_data_async)
        
        cancel_btn = ft.TextButton("Hủy", on_click=lambda _: close_dialog_safe())
        clear_btn = ft.TextButton(
            "Xóa lọc", 
            on_click=handle_clear,
            style=ft.ButtonStyle(color=ft.Colors.ORANGE_600)
        )
        apply_btn = ft.ElevatedButton(
            "Áp dụng",
            on_click=lambda e: page.run_task(handle_apply, e),
            bgcolor=ft.Colors.BLUE_600,
            color=ft.Colors.WHITE
        )
        
        content = ft.Container(
            width=450,
            content=ft.Column([
                ft.Container(
                    content=ft.Row([
                        ft.Container(
                            content=CustomIcon.create(CustomIcon.FILTER, size=24),
                            padding=10,
                            bgcolor=ft.Colors.BLUE_50,
                            border_radius=50
                        ),
                        ft.Column([
                            ft.Text("Lọc theo trạng thái", size=16, weight=ft.FontWeight.BOLD),
                            ft.Text("Chọn một hoặc nhiều trạng thái", size=12, color=ft.Colors.GREY_700),
                        ], spacing=2)
                    ], spacing=10),
                    padding=10,
                    border=ft.border.all(1, ft.Colors.BLUE_100),
                    border_radius=8,
                    bgcolor=ft.Colors.BLUE_50
                ),
                ft.Divider(height=10, color=ft.Colors.TRANSPARENT),
                ft.Column([
                    checkbox_dang_luu,
                    checkbox_da_tra,
                    ft.Divider(height=1, color=ft.Colors.GREY_200),
                    checkbox_chua_doan_phi,
                    checkbox_chua_hoi_phi,
                ], spacing=10)
            ], spacing=12, scroll=ft.ScrollMode.AUTO, height=280)
        )
        
        dialog_container.content = ft.Stack([content])
        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Row([
                CustomIcon.create(CustomIcon.FILTER, size=24),
                ft.Text("Lọc trạng thái", weight=ft.FontWeight.BOLD)
            ], spacing=10),
            content=dialog_container,
            actions=[cancel_btn, clear_btn, apply_btn],
            bgcolor=ft.Colors.WHITE,
            content_padding=24
        )
        show_dialog_safe(dialog)

    def build_row(s: dict):
        checkbox = ft.Checkbox(
            value=s["mssv"] in state["selected_mssv"],
            on_change=lambda e, mssv=s["mssv"]: toggle_selection(mssv, e.control.value)
        )

        vi_tri = s.get("vi_tri_luu_so", "") or ""
        ghi_chu = s.get("ghi_chu", "") or ""
        ngay_sinh = s.get("ngay_sinh", "") or ""
        noi_sinh = s.get("noi_sinh", "") or ""
        
        def delete_single_student(e, student: dict):
            mssv = student["mssv"]
            ho_ten = student.get("ho_ten", "")

            def handle_cancel(e):
                close_dialog_safe()

            async def handle_confirm(e):
                confirm_btn.disabled = True
                cancel_btn.disabled = True
                page.update()

                try:
                    delete_student(mssv)
                    close_dialog_safe()
                    message_manager.success(f"Đã xóa {mssv}")
                    state["selected_mssv"].discard(mssv)
                    await load_data_async()
                except Exception as ex:
                    confirm_btn.disabled = False
                    cancel_btn.disabled = False
                    message_manager.error(f"Lỗi: {ex}")
                    page.update()

            cancel_btn = ft.TextButton(
                "Hủy bỏ",
                on_click=handle_cancel,
                style=ft.ButtonStyle(color=ft.Colors.GREY_600)
            )

            confirm_btn = ft.ElevatedButton(
                "Xác nhận xóa",
                on_click=lambda e: page.run_task(handle_confirm, e),
                bgcolor=ft.Colors.RED_600,
                color=ft.Colors.WHITE,
                elevation=0
            )

            content_container = ft.Container(
                width=400,
                content=ft.Column(
                    controls=[
                        ft.Text("Bạn có chắc chắn muốn xóa sinh viên này?", size=14, color=ft.Colors.GREY_800),
                        ft.Container(
                            content=ft.Row(
                                controls=[
                                    ft.Container(
                                        content=CustomIcon.create(CustomIcon.DELETE, size=24),
                                        padding=10,
                                        bgcolor=ft.Colors.WHITE,
                                        border_radius=50,
                                    ),
                                    ft.Column(
                                        controls=[
                                            ft.Text(mssv, weight=ft.FontWeight.BOLD, size=15, color=ft.Colors.RED_900),
                                            ft.Text(ho_ten, size=14, color=ft.Colors.GREY_800),
                                        ],
                                        spacing=2,
                                        tight=True,
                                    )
                                ],
                                spacing=12,
                            ),
                            padding=12,
                            bgcolor=ft.Colors.RED_50,
                            border=ft.border.all(1, ft.Colors.RED_100),
                            border_radius=8,
                        ),

                        ft.Row(
                            controls=[
                                ft.Icon(ft.Icons.INFO_OUTLINE, size=14, color=ft.Colors.RED_400),
                                ft.Text("Dữ liệu sẽ bị xóa vĩnh viễn.", size=12, color=ft.Colors.RED_400, italic=True),
                            ],
                            spacing=6,
                            tight=True,
                        )
                    ],
                    spacing=16, 
                    tight=True,
                ),
            )

            delete_dialog = ft.AlertDialog(
                modal=True,
                title=ft.Row(
                    [
                        CustomIcon.create(CustomIcon.WARNING, size=24),
                        ft.Text("Xác nhận xóa", size=18, weight=ft.FontWeight.W_600),
                    ],
                    spacing=10,
                    tight=True,
                ),
                content=content_container,
                actions=[cancel_btn, confirm_btn],
                actions_alignment=ft.MainAxisAlignment.END,
                actions_padding=ft.padding.only(right=20, bottom=16),
                content_padding=ft.padding.all(24),
                shape=ft.RoundedRectangleBorder(radius=12),
                bgcolor=ft.Colors.WHITE,
            )

            show_dialog_safe(delete_dialog)

        
        action_buttons = ft.Row([
            checkbox,
            ft.Container(
                content=CustomIcon.create(CustomIcon.EDIT, size=18),
                on_click=lambda e, student=s: open_edit_dialog(student),
                tooltip="Sửa sinh viên",
                padding=8,
                border_radius=4,
                ink=True,
            ),
        ], spacing=4)
        
        if is_admin(role):
            action_buttons.controls.append(
                ft.Container(
                    content=CustomIcon.create(CustomIcon.DELETE, size=18),
                    on_click=lambda e, student=s: delete_single_student(e, student),
                    tooltip="Xóa sinh viên",
                    padding=8,
                    border_radius=4,
                    ink=True,
                )
            )
        
        return ft.DataRow(
            cells=[
                ft.DataCell(ft.Text(s["mssv"])),
                ft.DataCell(ft.Text(s["ho_ten"] or "")),
                ft.DataCell(
                    ft.Text(
                        ngay_sinh,
                        size=11,
                        color=ft.Colors.GREY_700,
                    )
                ),
                ft.DataCell(
                    ft.Text(
                        noi_sinh[:20] + "..." if len(noi_sinh) > 20 else noi_sinh,
                        size=11,
                        color=ft.Colors.GREY_700,
                        tooltip=noi_sinh if len(noi_sinh) > 20 else None
                    )
                ),
                ft.DataCell(ft.Text(s["lop"] or "")),
                ft.DataCell(ft.Text(s["khoa"] or "")),
                ft.DataCell(ft.Text(s.get("trang_thai_so", ""))),
                ft.DataCell(
                    ft.Text(
                        vi_tri[:25] + "..." if len(vi_tri) > 25 else vi_tri,
                        size=11,
                        color=ft.Colors.BLUE_GREY_700,
                        tooltip=vi_tri if len(vi_tri) > 25 else None
                    )
                ),
                ft.DataCell(
                    ft.Text(
                        ghi_chu[:25] + "..." if len(ghi_chu) > 25 else ghi_chu,
                        size=11,
                        color=ft.Colors.GREY_600,
                        italic=True,
                        tooltip=ghi_chu if len(ghi_chu) > 25 else None
                    )
                ),
                ft.DataCell(
                    CustomIcon.create(
                        CustomIcon.CHECK if s.get("da_nop_doan_phi") else CustomIcon.CLOSE,
                        size=20
                    )
                ),
                ft.DataCell(
                    CustomIcon.create(
                        CustomIcon.CHECK if s.get("da_nop_hoi_phi") else CustomIcon.CLOSE,
                        size=20
                    )
                ),
                ft.DataCell(action_buttons),
            ],
        )
    
    def toggle_selection(mssv: str, selected: bool):
        if selected:
            state["selected_mssv"].add(mssv)
        else:
            state["selected_mssv"].discard(mssv)
        
        select_all_checkbox.value = (
            len(state["selected_mssv"]) == len(state["students"]) 
            and len(state["students"]) > 0
        )
        
        selected_count_text.value = f"Đã chọn: {len(state['selected_mssv'])}"
        page.update()
    
    def toggle_select_all(select_all: bool):
        if select_all:
            for s in state["students"]:
                state["selected_mssv"].add(s["mssv"])
        else:
            for s in state["students"]:
                state["selected_mssv"].discard(s["mssv"])
        
        table.rows.clear()
        for s in state["students"]:
            table.rows.append(build_row(s))
        
        selected_count_text.value = f"Đã chọn: {len(state['selected_mssv'])}"
        page.update()

    def on_search(e):
        state["search_text"] = e.control.value.strip()
        state["page_index"] = 1
        state["selected_mssv"].clear()
        select_all_checkbox.value = False
        page.run_task(load_data_async)
    
    def on_filter_lop(e):
        state["filter_lop"] = e.control.value.strip()
        state["page_index"] = 1
        state["selected_mssv"].clear()
        select_all_checkbox.value = False
        page.run_task(load_data_async)
    
    def on_filter_khoa(e):
        state["filter_khoa"] = e.control.value.strip()
        state["page_index"] = 1
        state["selected_mssv"].clear()
        select_all_checkbox.value = False
        page.run_task(load_data_async)
    
    def clear_filters(e):
        state["search_text"] = ""
        state["filter_lop"] = ""
        state["filter_khoa"] = ""
        state["filter_trang_thai"].clear()
        state["page_index"] = 1
        state["selected_mssv"].clear()
        message_manager.info("Đã xóa bộ lọc trạng thái")
        search_field.value = ""
        filter_lop_field.value = ""
        filter_khoa_field.value = ""
        select_all_checkbox.value = False
        
        update_filter_button_color()
        page.run_task(load_data_async)

    def update_pagination():
        total_pages = max(1, (state["total_records"] + PAGE_SIZE - 1) // PAGE_SIZE)
        pagination_text.value = f"Trang {state['page_index']} / {total_pages} – Tổng {state['total_records']} sinh viên"

    def update_filter_button_color():
        has_filter = len(state["filter_trang_thai"]) > 0
        filter_trang_thai_btn.bgcolor = ft.Colors.BLUE_600 if has_filter else ft.Colors.BLUE_50
        filter_trang_thai_btn.icon_color = ft.Colors.WHITE if has_filter else ft.Colors.BLUE_600
        filter_trang_thai_btn.update()

    def prev_page(e):
        if state["page_index"] > 1:
            state["page_index"] -= 1
            state["selected_mssv"].clear()
            select_all_checkbox.value = False
            page.run_task(load_data_async)

    def next_page(e):
        if state["page_index"] * PAGE_SIZE < state["total_records"]:
            state["page_index"] += 1
            state["selected_mssv"].clear()
            select_all_checkbox.value = False
            page.run_task(load_data_async)

    def open_bulk_update_dialog(e):
        """Cập nhật hàng loạt - UI Refactored"""
        selected_count = len(state["selected_mssv"])
        if not state["selected_mssv"]:
            message_manager.warning("Chưa chọn sinh viên nào để cập nhật")
            return

        dialog_container = ft.Container()
        dialog_message_manager = MessageManager(page, dialog_container)
        
        field_states = {
            "ngay_sinh": False, "noi_sinh": False, "trang_thai_so": False,
            "vi_tri_luu_so": False, "ghi_chu": False, "da_nop_doan_phi": False,
            "da_nop_hoi_phi": False, "lop": False, "khoa": False,
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

        enable_ngay_sinh = ft.Checkbox(value=False, on_change=lambda e: toggle_field("ngay_sinh", e.control.value))
        ngay_sinh_field = ft.TextField(label="Ngày sinh mới", hint_text="dd/mm/yyyy", disabled=True, expand=True, text_size=13, height=40, content_padding=10)
        clear_ngay_sinh_btn = ft.IconButton(icon=ft.Icons.CLEAR, icon_size=16, tooltip="Xóa", visible=False, on_click=lambda e: set_field_value("ngay_sinh", ""))

        enable_noi_sinh = ft.Checkbox(value=False, on_change=lambda e: toggle_field("noi_sinh", e.control.value))
        noi_sinh_field = ft.TextField(label="Nơi sinh mới", hint_text="Nhập nơi sinh", disabled=True, expand=True, text_size=13, height=40, content_padding=10)
        clear_noi_sinh_btn = ft.IconButton(icon=ft.Icons.CLEAR, icon_size=16, tooltip="Xóa", visible=False, on_click=lambda e: set_field_value("noi_sinh", ""))

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

        enable_doan_phi = ft.Checkbox(value=False, on_change=lambda e: toggle_field("da_nop_doan_phi", e.control.value))
        doan_phi_dropdown = ft.Dropdown(label="Đoàn phí", value="Có", disabled=True, width=120, text_size=13, height=40, content_padding=10, options=[ft.dropdown.Option("Có"), ft.dropdown.Option("Chưa")])
        
        enable_hoi_phi = ft.Checkbox(value=False, on_change=lambda e: toggle_field("da_nop_hoi_phi", e.control.value))
        hoi_phi_dropdown = ft.Dropdown(label="Hội phí", value="Có", disabled=True, width=120, text_size=13, height=40, content_padding=10, options=[ft.dropdown.Option("Có"), ft.dropdown.Option("Chưa")])

        enable_lop = ft.Checkbox(value=False, on_change=lambda e: toggle_field("lop", e.control.value))
        lop_field = ft.TextField(label="Lớp mới", hint_text="VD: 74DCHT22", disabled=True, expand=True, text_size=13, height=40, content_padding=10)
        clear_lop_btn = ft.IconButton(icon=ft.Icons.CLEAR, icon_size=16, tooltip="Xóa", visible=False, on_click=lambda e: set_field_value("lop", ""))
        
        enable_khoa = ft.Checkbox(value=False, on_change=lambda e: toggle_field("khoa", e.control.value))
        khoa_field = ft.TextField(label="Khoa mới", hint_text="VD: CNTT", disabled=True, expand=True, text_size=13, height=40, content_padding=10)
        clear_khoa_btn = ft.IconButton(icon=ft.Icons.CLEAR, icon_size=16, tooltip="Xóa", visible=False, on_click=lambda e: set_field_value("khoa", ""))

        field_controls = {
            "ngay_sinh": {"checkbox": enable_ngay_sinh, "input": ngay_sinh_field, "clear": clear_ngay_sinh_btn},
            "noi_sinh": {"checkbox": enable_noi_sinh, "input": noi_sinh_field, "clear": clear_noi_sinh_btn},
            "trang_thai_so": {"checkbox": enable_trang_thai, "input": trang_thai_dropdown},
            "vi_tri_luu_so": {"checkbox": enable_vi_tri, "input": vi_tri_field, "clear": clear_vi_tri_btn},
            "ghi_chu": {"checkbox": enable_ghi_chu, "input": ghi_chu_field, "clear": clear_ghi_chu_btn},
            "da_nop_doan_phi": {"checkbox": enable_doan_phi, "input": doan_phi_dropdown},
            "da_nop_hoi_phi": {"checkbox": enable_hoi_phi, "input": hoi_phi_dropdown},
            "lop": {"checkbox": enable_lop, "input": lop_field, "clear": clear_lop_btn},
            "khoa": {"checkbox": enable_khoa, "input": khoa_field, "clear": clear_khoa_btn},
        }

        async def handle_submit(e):
            submit_btn.disabled = True
            cancel_btn.disabled = True
            page.update()
            
            try:
                payload = {}
                if field_states["ngay_sinh"]: payload["ngay_sinh"] = ngay_sinh_field.value.strip()
                if field_states["noi_sinh"]: payload["noi_sinh"] = noi_sinh_field.value.strip()
                if field_states["trang_thai_so"]: payload["trang_thai_so"] = trang_thai_dropdown.value
                if field_states["da_nop_doan_phi"]: payload["da_nop_doan_phi"] = (doan_phi_dropdown.value == "Có")
                if field_states["da_nop_hoi_phi"]: payload["da_nop_hoi_phi"] = (hoi_phi_dropdown.value == "Có")
                if field_states["vi_tri_luu_so"]: payload["vi_tri_luu_so"] = vi_tri_field.value.strip()
                if field_states["ghi_chu"]: payload["ghi_chu"] = ghi_chu_field.value.strip()
                if field_states["lop"]: payload["lop"] = lop_field.value.strip()
                if field_states["khoa"]: payload["khoa"] = khoa_field.value.strip()
                
                if not payload:
                    submit_btn.disabled = False; cancel_btn.disabled = False
                    dialog_message_manager.warning("Chưa chọn trường nào để cập nhật")
                    return
                
                bulk_update_students(list(state["selected_mssv"]), payload)
                
                state["selected_mssv"].clear()
                select_all_checkbox.value = False
                close_dialog_safe()
                updated_fields = ", ".join(payload.keys())
                message_manager.success(f"Đã cập nhật {selected_count} SV: {updated_fields}")
                await load_data_async()
                
            except Exception as ex:
                submit_btn.disabled = False; cancel_btn.disabled = False
                dialog_message_manager.error(f"Lỗi: {ex}")
        
        cancel_btn = ft.TextButton(
            "Hủy bỏ", 
            on_click=lambda e: close_dialog_safe(),
            style=ft.ButtonStyle(color=ft.Colors.GREY_600)
        )
        submit_btn = ft.ElevatedButton(
            "Xác nhận cập nhật", 
            on_click=lambda e: page.run_task(handle_submit, e),
            bgcolor=ft.Colors.BLUE_600, color=ft.Colors.WHITE, elevation=0
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
                                    padding=10, bgcolor=ft.Colors.WHITE, border_radius=50,
                                    border=ft.border.all(1, ft.Colors.BLUE_100)
                                ),
                                ft.Column(
                                    controls=[
                                        ft.Text(f"Đang chọn {selected_count} sinh viên", weight=ft.FontWeight.BOLD, size=15, color=ft.Colors.BLUE_900),
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
                            
                            build_field_row("Đoàn phí", enable_doan_phi, doan_phi_dropdown),
                            build_field_row("Hội phí", enable_hoi_phi, hoi_phi_dropdown),
                            ft.Divider(height=1, color=ft.Colors.GREY_100),

                            build_field_row("Lớp", enable_lop, lop_field, clear_lop_btn),
                            build_field_row("Khoa", enable_khoa, khoa_field, clear_khoa_btn),
                            ft.Divider(height=1, color=ft.Colors.GREY_100),

                            build_field_row("Ngày sinh", enable_ngay_sinh, ngay_sinh_field, clear_ngay_sinh_btn),
                            build_field_row("Nơi sinh", enable_noi_sinh, noi_sinh_field, clear_noi_sinh_btn),
                            build_field_row("Ghi chú", enable_ghi_chu, ghi_chu_field, clear_ghi_chu_btn),
                        ],
                        scroll=ft.ScrollMode.AUTO,
                        height=400,
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
        label="Tìm theo MSSV / Họ tên",
        prefix=CustomIcon.prefix_icon(CustomIcon.SEARCH),
        hint_text="VD: 74123456",
        width=400,
        on_submit=on_search,
    )
    
    filter_trang_thai_btn = ft.IconButton(
        icon=ft.Icons.FILTER_ALT,
        icon_size=24,
        tooltip="Lọc theo trạng thái",
        on_click=open_filter_trang_thai_dialog,
        bgcolor=ft.Colors.BLUE_50 if not state["filter_trang_thai"] else ft.Colors.BLUE_600,
        icon_color=ft.Colors.BLUE_600 if not state["filter_trang_thai"] else ft.Colors.WHITE,
    )

    filter_lop_field = ft.TextField(label="Lọc lớp", hint_text="74DCHT22", width=150, on_submit=on_filter_lop)
    filter_khoa_field = ft.TextField(label="Lọc khoa", hint_text="CNTT", width=150, on_submit=on_filter_khoa)

    buttons = []
    if is_admin(role):
        buttons.extend([
            elevated_button("Thêm Sinh viên", CustomIcon.ADD, on_click=open_add_student_dialog),
            elevated_button("Tải mẫu", CustomIcon.DOCUMENT, on_click=download_template_dialog),
            elevated_button("Import", CustomIcon.UPLOAD, on_click=import_excel_dialog),
            elevated_button("Export", CustomIcon.DOWNLOAD, on_click=export_excel_action),
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
        ft.Row([filter_lop_field, filter_khoa_field, filter_trang_thai_btn, ft.TextButton("Xóa lọc", on_click=clear_filters)], spacing=8),
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
    
    async def _delayed_load():
        import asyncio
        await asyncio.sleep(0.2)
        await load_data_async()
    
    page.run_task(_delayed_load)
    
    return result