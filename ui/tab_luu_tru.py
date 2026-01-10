# ui/tab_luu_tru.py
import flet as ft
import asyncio
import threading
import time
from datetime import datetime
from services.so_doan_service import (
    fetch_so_doan,
    count_so_doan,
    create_so_doan,
    update_so_doan,
    delete_so_doan,
    bulk_update_so_doan,
    get_all_so_doan_for_export,
)
from services.tai_san_service import (
    fetch_tai_san,
    count_tai_san,
    create_tai_san,
    update_tai_san,
    delete_tai_san,
    bulk_update_tai_san,
    get_all_tai_san_for_export,
)
from core.auth import is_admin
from ui.icon_helper import CustomIcon, elevated_button
from ui.message_manager import MessageManager

PAGE_SIZE = 100


def LuuTruTab(page: ft.Page, role: str):

    tab_state = {"current_index": 0}

    content_container = ft.Container(expand=True)

    def SoDoanTab():
        message_manager = MessageManager(page)
        
        state = {
            "records": [],
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
                ft.DataColumn(ft.Text("Họ tên", weight=ft.FontWeight.BOLD)),
                ft.DataColumn(ft.Text("Ngày sinh", weight=ft.FontWeight.BOLD)),
                ft.DataColumn(ft.Text("Quê quán", weight=ft.FontWeight.BOLD)),
                ft.DataColumn(ft.Text("Nơi kết nạp", weight=ft.FontWeight.BOLD)),
                ft.DataColumn(ft.Text("Ngày kết nạp", weight=ft.FontWeight.BOLD)),
                ft.DataColumn(ft.Text("Trạng thái", weight=ft.FontWeight.BOLD)),
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
                # Dialog open error suppressed in production
                pass
        
        def close_dialog_safe():
            if state["active_dialog"] is None:
                return
            
            try:
                state["active_dialog"].open = False
                page.update()
                
                async def _delayed_remove():
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
            if state["is_loading"]:
                return
            
            state["is_loading"] = True
            loading_indicator.visible = True
            page.update()
            
            try:
                total = count_so_doan(
                    search=state["search_text"],
                    trang_thai=state["filter_trang_thai"]
                )
                
                records = fetch_so_doan(
                    search=state["search_text"],
                    trang_thai=state["filter_trang_thai"],
                    page=state["page_index"],
                    page_size=PAGE_SIZE
                )
                
                state["total_records"] = total
                state["records"] = records
                state["is_loading"] = False
                loading_indicator.visible = False
                
                table.rows.clear()
                for r in records:
                    table.rows.append(build_row(r))
                
                update_pagination()
                selected_count_text.value = f"Đã chọn: {len(state['selected_ids'])}"
                page.update()
                
            except Exception as ex:
                pagination_text.value = f"Lỗi: {ex}"
                state["is_loading"] = False
                loading_indicator.visible = False
                page.update()
        
        def build_row(record: dict):
            checkbox = ft.Checkbox(
                value=record["id"] in state["selected_ids"],
                on_change=lambda e, id=record["id"]: toggle_selection(id, e.control.value)
            )
            
            edit_btn = ft.Container(
                content=CustomIcon.create(CustomIcon.EDIT, size=18),
                on_click=lambda e, r=record: open_edit_dialog(r),
                tooltip="Sửa",
                padding=8,
                border_radius=4,
                ink=True,
            )
            
            delete_btn = None
            if is_admin(role):
                delete_btn = ft.Container(
                    content=CustomIcon.create(CustomIcon.DELETE, size=18),
                    on_click=lambda e, r=record: confirm_delete(r),
                    tooltip="Xóa",
                    padding=8,
                    border_radius=4,
                    ink=True,
                )
            
            action_buttons = [checkbox, edit_btn]
            if delete_btn:
                action_buttons.append(delete_btn)
            
            ngay_sinh = record.get("ngay_sinh", "") or ""
            if ngay_sinh and "/" not in ngay_sinh:
                try:
                    dt = datetime.strptime(ngay_sinh, "%Y-%m-%d")
                    ngay_sinh = dt.strftime("%d/%m/%Y")
                except:
                    pass
            
            ngay_ket_nap = record.get("ngay_ket_nap", "") or ""
            if ngay_ket_nap and "/" not in ngay_ket_nap:
                try:
                    dt = datetime.strptime(ngay_ket_nap, "%Y-%m-%d")
                    ngay_ket_nap = dt.strftime("%d/%m/%Y")
                except:
                    pass
            
            trang_thai = record.get("trang_thai", "Đang lưu VP")
            trang_thai_color = ft.Colors.ORANGE_700 if trang_thai == "Đang lưu VP" else ft.Colors.GREEN_700
            
            ghi_chu = record.get("ghi_chu", "") or ""
            
            return ft.DataRow(
                cells=[
                    ft.DataCell(ft.Text(record.get("ho_ten", ""), size=13)),
                    ft.DataCell(ft.Text(ngay_sinh, size=12, color=ft.Colors.GREY_700)),
                    ft.DataCell(ft.Text(record.get("que_quan", "")[:30] + "..." if len(record.get("que_quan", "")) > 30 else record.get("que_quan", ""), size=12)),
                    ft.DataCell(ft.Text(record.get("noi_ket_nap", "")[:30] + "..." if len(record.get("noi_ket_nap", "")) > 30 else record.get("noi_ket_nap", ""), size=12)),
                    ft.DataCell(ft.Text(ngay_ket_nap, size=12, color=ft.Colors.GREY_700)),
                    ft.DataCell(ft.Text(trang_thai, size=12, weight=ft.FontWeight.BOLD, color=trang_thai_color)),
                    ft.DataCell(ft.Text(ghi_chu[:30] + "..." if len(ghi_chu) > 30 else ghi_chu, size=11, color=ft.Colors.GREY_600)),
                    ft.DataCell(ft.Row(action_buttons, spacing=4)),
                ],
            )
        
        def toggle_selection(id: str, selected: bool):
            if selected:
                state["selected_ids"].add(id)
            else:
                state["selected_ids"].discard(id)
            
            select_all_checkbox.value = (
                len(state["selected_ids"]) == len(state["records"]) 
                and len(state["records"]) > 0
            )
            
            selected_count_text.value = f"Đã chọn: {len(state['selected_ids'])}"
            page.update()
        
        def toggle_select_all(select_all: bool):
            if select_all:
                for r in state["records"]:
                    state["selected_ids"].add(r["id"])
            else:
                for r in state["records"]:
                    state["selected_ids"].discard(r["id"])
            
            table.rows.clear()
            for r in state["records"]:
                table.rows.append(build_row(r))
            
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
        
        def clear_filters(e):
            state["search_text"] = ""
            state["filter_trang_thai"] = ""
            state["page_index"] = 1
            state["selected_ids"].clear()
            
            search_field.value = ""
            filter_trang_thai_dropdown.value = ""
            select_all_checkbox.value = False
            
            page.run_task(load_data_async)
        
        def update_pagination():
            total_pages = max(1, (state["total_records"] + PAGE_SIZE - 1) // PAGE_SIZE)
            pagination_text.value = f"Trang {state['page_index']} / {total_pages} – Tổng {state['total_records']} bản ghi"
        
        def prev_page(e):
            if state["page_index"] > 1:
                state["page_index"] -= 1
                state["selected_ids"].clear()
                select_all_checkbox.value = False
                page.run_task(load_data_async)

        def next_page(e):
            total_pages = max(1, (state["total_records"] + PAGE_SIZE - 1) // PAGE_SIZE)
            if state["page_index"] < total_pages:
                state["page_index"] += 1
                state["selected_ids"].clear()
                select_all_checkbox.value = False
                page.run_task(load_data_async)
        
        def open_create_dialog(e):
            """Thêm Sổ Đoàn thất lạc"""
            dialog_container = ft.Container()
            dialog_message_manager = MessageManager(page, dialog_container)

            fields = {
                "ho_ten": ft.TextField(label="Họ tên *", autofocus=True),
                "ngay_sinh": ft.TextField(label="Ngày sinh *", hint_text="dd/mm/yyyy"),
                "que_quan": ft.TextField(label="Quê quán"),
                "noi_ket_nap": ft.TextField(label="Nơi kết nạp"),
                "ngay_ket_nap": ft.TextField(label="Ngày kết nạp", hint_text="dd/mm/yyyy"),
                "trang_thai": ft.Dropdown(
                    label="Trạng thái",
                    value="Đang lưu VP",
                    options=[ft.dropdown.Option("Đang lưu VP"), ft.dropdown.Option("Đã trả")],
                ),
                "ghi_chu": ft.TextField(label="Ghi chú", multiline=True, min_lines=2, max_lines=4),
            }

            async def submit(ev):
                submit_btn.disabled = True
                cancel_btn.disabled = True
                page.update()

                try:
                    payload = {k: v.value for k, v in fields.items() if v.value}

                    required = ["ho_ten", "ngay_sinh"]
                    missing = [f for f in required if not payload.get(f)]
                    if missing:
                        submit_btn.disabled = False
                        cancel_btn.disabled = False
                        dialog_message_manager.error(f"Thiếu trường bắt buộc: {', '.join(missing)}")
                        return

                    create_so_doan(payload)

                    close_dialog_safe()
                    message_manager.success("Đã thêm bản ghi")
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
                color=ft.Colors.WHITE,
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
                                border_radius=50,
                            ),
                            ft.Column([
                                ft.Text("Thêm Sổ Đoàn thất lạc", size=16, weight=ft.FontWeight.BOLD, color=ft.Colors.GREEN_900),
                                ft.Text("Nhập thông tin sổ đoàn", size=12, color=ft.Colors.GREY_700),
                            ], spacing=2),
                        ], spacing=10),
                        padding=10,
                        border=ft.border.all(1, ft.Colors.GREEN_100),
                        border_radius=8,
                        bgcolor=ft.Colors.GREEN_50,
                    ),
                    ft.Divider(height=10, color=ft.Colors.TRANSPARENT),
                    *list(fields.values()),
                ], spacing=12, scroll=ft.ScrollMode.AUTO, height=400),
            )

            dialog_container.content = ft.Stack([content])

            dialog = ft.AlertDialog(
                modal=True,
                title=ft.Row([CustomIcon.create(CustomIcon.ADD, size=24), ft.Text("Thêm Sổ Đoàn thất lạc", weight=ft.FontWeight.BOLD)], spacing=10),
                content=dialog_container,
                actions=[cancel_btn, submit_btn],
                bgcolor=ft.Colors.WHITE,
                content_padding=24,
            )

            show_dialog_safe(dialog)
        
        def open_edit_dialog(record: dict):
            dialog_container = ft.Container()
            dialog_message_manager = MessageManager(page, dialog_container)

            ngay_sinh = record.get("ngay_sinh", "")
            if ngay_sinh and "/" not in ngay_sinh:
                try:
                    dt = datetime.strptime(ngay_sinh, "%Y-%m-%d")
                    ngay_sinh = dt.strftime("%d/%m/%Y")
                except:
                    pass

            ngay_ket_nap = record.get("ngay_ket_nap", "")
            if ngay_ket_nap and "/" not in ngay_ket_nap:
                try:
                    dt = datetime.strptime(ngay_ket_nap, "%Y-%m-%d")
                    ngay_ket_nap = dt.strftime("%d/%m/%Y")
                except:
                    pass

            fields = {
                "ho_ten": ft.TextField(label="Họ tên *", value=record.get("ho_ten", "")),
                "ngay_sinh": ft.TextField(label="Ngày sinh *", value=ngay_sinh),
                "que_quan": ft.TextField(label="Quê quán", value=record.get("que_quan", "") or ""),
                "noi_ket_nap": ft.TextField(label="Nơi kết nạp", value=record.get("noi_ket_nap", "") or ""),
                "ngay_ket_nap": ft.TextField(label="Ngày kết nạp", value=ngay_ket_nap),
                "trang_thai": ft.Dropdown(
                    label="Trạng thái",
                    value=record.get("trang_thai", "Đang lưu VP"),
                    options=[ft.dropdown.Option("Đang lưu VP"), ft.dropdown.Option("Đã trả")],
                ),
                "ghi_chu": ft.TextField(label="Ghi chú", value=record.get("ghi_chu", "") or "", multiline=True, min_lines=2, max_lines=4),
            }

            async def submit(e):
                submit_btn.disabled = True
                cancel_btn.disabled = True
                page.update()

                try:
                    payload = {k: v.value.strip() if isinstance(v.value, str) else v.value for k, v in fields.items() if v.value}

                    update_so_doan(record["id"], payload)

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
                color=ft.Colors.WHITE,
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
                                border_radius=50,
                            ),
                            ft.Column([
                                ft.Text(f"{record.get('ho_ten', '')}", size=16, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_900),
                                ft.Text("Chỉnh sửa sổ đoàn", size=12, color=ft.Colors.GREY_700),
                            ], spacing=2),
                        ], spacing=10),
                        padding=10,
                        border=ft.border.all(1, ft.Colors.BLUE_100),
                        border_radius=8,
                        bgcolor=ft.Colors.BLUE_50,
                    ),
                    ft.Divider(height=10, color=ft.Colors.TRANSPARENT),
                    *list(fields.values()),
                ], spacing=12, scroll=ft.ScrollMode.AUTO, height=400),
            )

            dialog_container.content = ft.Stack([content])

            dialog = ft.AlertDialog(
                modal=True,
                title=ft.Row([CustomIcon.create(CustomIcon.EDIT, size=24), ft.Text(f"Sửa: {record.get('ho_ten', '')}", weight=ft.FontWeight.BOLD)], spacing=10),
                content=dialog_container,
                actions=[cancel_btn, submit_btn],
                bgcolor=ft.Colors.WHITE,
                content_padding=24,
            )

            show_dialog_safe(dialog)
        
        def confirm_delete(record: dict):
            """Xác nhận xóa sổ đoàn"""
            async def do_delete(e):
                delete_btn.disabled = True
                cancel_btn.disabled = True
                page.update()

                try:
                    delete_so_doan(record["id"])

                    close_dialog_safe()
                    message_manager.success(f"Đã xóa: {record.get('ho_ten', '')}")
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
                color=ft.Colors.WHITE,
            )

            dialog = ft.AlertDialog(
                modal=True,
                title=ft.Row([CustomIcon.create(CustomIcon.WARNING, size=24), ft.Text("Xác nhận xóa", weight=ft.FontWeight.BOLD)], spacing=10),
                content=ft.Container(
                    width=400,
                    content=ft.Column([
                        ft.Container(
                            content=ft.Row([
                                CustomIcon.create(CustomIcon.DELETE_FOREVER, size=48),
                                ft.Column([
                                    ft.Text("Bạn có chắc chắn muốn xóa bản ghi này?", size=14, weight=ft.FontWeight.W_500),
                                    ft.Text(record.get('ho_ten', ''), size=16, weight=ft.FontWeight.BOLD, color=ft.Colors.RED_700),
                                    ft.Text("Hành động này không thể hoàn tác!", size=12, color=ft.Colors.RED_600, italic=True),
                                ], spacing=4, expand=True)
                            ], spacing=15),
                            padding=15,
                            border=ft.border.all(2, ft.Colors.RED_200),
                            border_radius=8,
                            bgcolor=ft.Colors.RED_50,
                        ),
                    ], spacing=0, tight=True),
                ),
                actions=[cancel_btn, delete_btn],
                bgcolor=ft.Colors.WHITE,
                content_padding=24,
            )

            show_dialog_safe(dialog)
        
        def export_excel_action(e):
            if not state["selected_ids"]:
                message_manager.warning("Chưa chọn bản ghi")
                return

            import os
            import pandas as pd
            from io import BytesIO

            downloads_folder = os.path.join(os.path.expanduser("~"), "Downloads")
            filename = f"export_so_doan_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            save_path = os.path.join(downloads_folder, filename)

            message_manager.info(f"Đang xuất {len(state['selected_ids'])} bản ghi...")

            async def _export():
                try:
                    data = get_all_so_doan_for_export(list(state["selected_ids"]))

                    if not data:
                        raise ValueError("Không có dữ liệu để export")

                    df = pd.DataFrame(data)

                    columns = ["ho_ten", "ngay_sinh", "que_quan", "noi_ket_nap", "ngay_ket_nap", "trang_thai", "ghi_chu"]
                    df = df[[col for col in columns if col in df.columns]]

                    df.rename(columns={
                        "ho_ten": "Họ tên",
                        "ngay_sinh": "Ngày sinh",
                        "que_quan": "Quê quán",
                        "noi_ket_nap": "Nơi kết nạp",
                        "ngay_ket_nap": "Ngày kết nạp",
                        "trang_thai": "Trạng thái",
                        "ghi_chu": "Ghi chú",
                    }, inplace=True)

                    output = BytesIO()
                    with pd.ExcelWriter(output, engine='openpyxl') as writer:
                        df.to_excel(writer, index=False, sheet_name='Sổ Đoàn')

                    with open(save_path, "wb") as f:
                        f.write(output.getvalue())

                    file_size = os.path.getsize(save_path) / 1024

                    content = ft.Column([
                        ft.Row([
                            ft.Container(
                                content=ft.Column([
                                    ft.Text("Số lượng", size=12, color=ft.Colors.GREY_700),
                                    ft.Text(f"{len(state['selected_ids'])} bản ghi", size=18, weight=ft.FontWeight.BOLD, color=ft.Colors.GREY_900),
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
                            content=ft.Text(save_path, size=11, selectable=True, color=ft.Colors.BLUE_800),
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
                        content=ft.Container(content=content, width=450, padding=20),
                        actions=[
                            ft.Row([
                                ft.ElevatedButton(
                                    content=ft.Row([CustomIcon.create(CustomIcon.CHECK_WHITE, size=16), ft.Text("Đóng", size=13, weight=ft.FontWeight.W_500)], spacing=6),
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
                    message_manager.error(f"Lỗi: {ex}")

            page.run_task(_export)
        
        # ===================== BULK UPDATE =====================
        def open_bulk_update_dialog(e):
            """Cập nhật hàng loạt - UI Refactored"""
            selected_count = len(state["selected_ids"])
            if not state["selected_ids"]:
                message_manager.warning("Chưa chọn bản ghi nào để cập nhật")
                return

            dialog_container = ft.Container()
            dialog_message_manager = MessageManager(page, dialog_container)

            field_states = {
                "ngay_sinh": False, "que_quan": False, "trang_thai": False,
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

            enable_ngay_sinh = ft.Checkbox(value=False, on_change=lambda e: toggle_field("ngay_sinh", e.control.value))
            ngay_sinh_field = ft.TextField(label="Ngày sinh mới", hint_text="dd/mm/yyyy", disabled=True, expand=True, text_size=13, height=40, content_padding=10)
            clear_ngay_sinh_btn = ft.IconButton(icon=ft.Icons.CLEAR, icon_size=16, tooltip="Xóa", visible=False, on_click=lambda e: set_field_value("ngay_sinh", ""))

            enable_que_quan = ft.Checkbox(value=False, on_change=lambda e: toggle_field("que_quan", e.control.value))
            que_quan_field = ft.TextField(label="Quê quán mới", hint_text="Nhập quê quán", disabled=True, expand=True, text_size=13, height=40, content_padding=10)
            clear_que_quan_btn = ft.IconButton(icon=ft.Icons.CLEAR, icon_size=16, tooltip="Xóa", visible=False, on_click=lambda e: set_field_value("que_quan", ""))

            enable_trang_thai = ft.Checkbox(value=False, on_change=lambda e: toggle_field("trang_thai", e.control.value))
            trang_thai_dropdown = ft.Dropdown(label="Trạng thái mới", value="Đang lưu VP", disabled=True, expand=True, text_size=13, height=40, content_padding=10, options=[ft.dropdown.Option("Đang lưu VP"), ft.dropdown.Option("Đã trả")])

            enable_ghi_chu = ft.Checkbox(value=False, on_change=lambda e: toggle_field("ghi_chu", e.control.value))
            ghi_chu_field = ft.TextField(label="Ghi chú mới", hint_text="Nhập ghi chú...", multiline=True, min_lines=1, max_lines=3, disabled=True, expand=True, text_size=13, content_padding=10)
            clear_ghi_chu_btn = ft.IconButton(icon=ft.Icons.CLEAR, icon_size=16, tooltip="Xóa", visible=False, on_click=lambda e: set_field_value("ghi_chu", ""))

            field_controls = {
                "ngay_sinh": {"checkbox": enable_ngay_sinh, "input": ngay_sinh_field, "clear": clear_ngay_sinh_btn},
                "que_quan": {"checkbox": enable_que_quan, "input": que_quan_field, "clear": clear_que_quan_btn},
                "trang_thai": {"checkbox": enable_trang_thai, "input": trang_thai_dropdown},
                "ghi_chu": {"checkbox": enable_ghi_chu, "input": ghi_chu_field, "clear": clear_ghi_chu_btn},
            }

            async def handle_submit(e):
                submit_btn.disabled = True
                cancel_btn.disabled = True
                page.update()

                try:
                    payload = {}
                    if field_states["ngay_sinh"]: payload["ngay_sinh"] = ngay_sinh_field.value.strip()
                    if field_states["que_quan"]: payload["que_quan"] = que_quan_field.value.strip()
                    if field_states["trang_thai"]: payload["trang_thai"] = trang_thai_dropdown.value
                    if field_states["ghi_chu"]: payload["ghi_chu"] = ghi_chu_field.value.strip()

                    if not payload:
                        submit_btn.disabled = False; cancel_btn.disabled = False
                        dialog_message_manager.warning("Chưa chọn trường nào để cập nhật")
                        return

                    await asyncio.to_thread(bulk_update_so_doan, list(state["selected_ids"]), payload)

                    state["selected_ids"].clear()
                    select_all_checkbox.value = False
                    close_dialog_safe()
                    updated_fields = ", ".join(payload.keys())
                    message_manager.success(f"Đã cập nhật {selected_count} bản ghi: {updated_fields}")
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
                                            ft.Text(f"Đang chọn {selected_count} bản ghi", weight=ft.FontWeight.BOLD, size=15, color=ft.Colors.BLUE_900),
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
                                build_field_row("Quê quán", enable_que_quan, que_quan_field, clear_que_quan_btn),
                                build_field_row("Trạng thái", enable_trang_thai, trang_thai_dropdown),
                                ft.Divider(height=1, color=ft.Colors.GREY_100),

                                build_field_row("Ghi chú", enable_ghi_chu, ghi_chu_field, clear_ghi_chu_btn),
                                ft.Divider(height=1, color=ft.Colors.GREY_100),

                                build_field_row("Ngày sinh", enable_ngay_sinh, ngay_sinh_field, clear_ngay_sinh_btn),
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
                title=ft.Row([
                    CustomIcon.create(CustomIcon.EDIT, size=24),
                    ft.Text("Sửa hàng loạt", size=18, weight=ft.FontWeight.W_600, color=ft.Colors.GREY_900),
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
        
        # ===================== UI LAYOUT =====================
        search_field = ft.TextField(
            label="Tìm theo họ tên / quê quán",
            prefix=CustomIcon.prefix_icon(CustomIcon.SEARCH),
            hint_text="Nhập từ khóa...",
            width=400,
            on_submit=on_search,
        )
        
        filter_trang_thai_dropdown = ft.Dropdown(
            label="Lọc trạng thái",
            hint_text="Tất cả",
            width=200,
            options=[
                ft.dropdown.Option("Đang lưu VP"),
                ft.dropdown.Option("Đã trả"),
            ],
        )
        filter_trang_thai_dropdown.on_change = on_filter_trang_thai  # ✅ Gán sau
        
        buttons = []
        if is_admin(role):
            buttons.append(elevated_button("Thêm mới", CustomIcon.ADD, on_click=open_create_dialog))
        buttons.extend([
            elevated_button("Export", CustomIcon.DOWNLOAD, on_click=export_excel_action),
            elevated_button("Sửa hàng loạt", CustomIcon.EDIT, on_click=open_bulk_update_dialog),
        ])
        
        toolbar = ft.Column([
            ft.Row(
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                controls=[
                    ft.Row([search_field, loading_indicator], spacing=8),
                    ft.Row(spacing=8, controls=buttons),
                ],
            ),
            ft.Row([filter_trang_thai_dropdown, ft.TextButton("Xóa lọc", on_click=clear_filters)], spacing=8),
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
    
    def TaiSanTab():
        """Sub-tab: Tài sản trong phòng"""
        
        state = {
            "records": [],
            "selected_ids": set(),
            "page_index": 1,
            "total_records": 0,
            "search_text": "",
            "filter_trang_thai": "",
            "is_loading": False,
            "active_dialog": None,
        }
        
        # Message manager for inline dialog/messages
        message_manager = MessageManager(page)

        loading_indicator = ft.ProgressRing(visible=False, width=30, height=30)
        
        select_all_checkbox = ft.Checkbox(
            label="Chọn tất cả trang này",
            value=False,
            on_change=lambda e: toggle_select_all(e.control.value)
        )
        
        table = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("Mã TS", weight=ft.FontWeight.BOLD)),
                ft.DataColumn(ft.Text("Tên tài sản", weight=ft.FontWeight.BOLD)),
                ft.DataColumn(ft.Text("Số lượng", weight=ft.FontWeight.BOLD)),
                ft.DataColumn(ft.Text("Tình trạng", weight=ft.FontWeight.BOLD)),
                ft.DataColumn(ft.Text("Trạng thái", weight=ft.FontWeight.BOLD)),
                ft.DataColumn(ft.Text("Người mượn", weight=ft.FontWeight.BOLD)),
                ft.DataColumn(ft.Text("Ngày mượn", weight=ft.FontWeight.BOLD)),
                ft.DataColumn(ft.Text("Ghi chú", weight=ft.FontWeight.BOLD)),
                ft.DataColumn(ft.Text("", weight=ft.FontWeight.BOLD)),
            ],
            rows=[],
            column_spacing=10,
            data_row_min_height=50,
        )
        
        pagination_text = ft.Text("Đang tải...", size=12, color=ft.Colors.GREY_600)
        selected_count_text = ft.Text("Đã chọn: 0", size=12, color=ft.Colors.BLUE_600, weight=ft.FontWeight.BOLD)
        
        # ===================== DIALOG MANAGEMENT =====================
        def show_dialog_safe(dialog):
            def _show():
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
                except Exception as ex:
                    print(f"❌ [DIALOG] Open error: {ex}")
            
            if hasattr(page, 'run_thread'):
                page.run_thread(_show)
            else:
                _show()
        
        def close_dialog_safe():
            def _close():
                if state["active_dialog"] is None:
                    return
                
                try:
                    state["active_dialog"].open = False
                    page.update()
                    
                    def _delayed_remove():
                        try:
                            if state["active_dialog"] in page.overlay:
                                page.overlay.remove(state["active_dialog"])
                            state["active_dialog"] = None
                            page.update()
                        except Exception as ex:
                            print(f"⚠️ [DIALOG] Delayed remove error: {ex}")
                    
                    threading.Timer(0.05, lambda: page.run_thread(_delayed_remove) if hasattr(page, 'run_thread') else _delayed_remove()).start()
                    
                except Exception as ex:
                    print(f"⚠️ [DIALOG] Close error: {ex}")
            
            if hasattr(page, 'run_thread'):
                page.run_thread(_close)
            else:
                _close()
        
        def safe_update():
            try:
                if hasattr(page, 'run_thread'):
                    page.run_thread(lambda: page.update())
                else:
                    page.update()
            except:
                pass
        
        # ===================== DATA LOADING =====================
        async def load_data_async():
            """Load data using asyncio.to_thread for blocking DB calls."""
            if state["is_loading"]:
                return

            state["is_loading"] = True
            loading_indicator.visible = True
            safe_update()

            try:
                total = await asyncio.to_thread(count_tai_san,
                                                 search=state["search_text"],
                                                 trang_thai=state["filter_trang_thai"])

                records = await asyncio.to_thread(fetch_tai_san,
                                                   search=state["search_text"],
                                                   trang_thai=state["filter_trang_thai"],
                                                   page=state["page_index"],
                                                   page_size=PAGE_SIZE)

                state["total_records"] = total
                state["records"] = records
                state["is_loading"] = False
                loading_indicator.visible = False

                table.rows.clear()
                for r in records:
                    table.rows.append(build_row(r))

                # Update pagination text
                total_pages = max(1, (state["total_records"] + PAGE_SIZE - 1) // PAGE_SIZE)
                pagination_text.value = f"Trang {state['page_index']} / {total_pages} — Tổng {state['total_records']} tài sản"

                selected_count_text.value = f"Đã chọn: {len(state['selected_ids'])}"
                page.update()

            except Exception as ex:
                pagination_text.value = f"⚠️ Lỗi: {ex}"
                state["is_loading"] = False
                loading_indicator.visible = False
                page.update()
        
        # ===================== TABLE ROW BUILDER =====================
        def build_row(record: dict):
            checkbox = ft.Checkbox(
                value=record["id"] in state["selected_ids"],
                on_change=lambda e, id=record["id"]: toggle_selection(id, e.control.value)
            )
            
            edit_btn = ft.Container(
                content=CustomIcon.create(CustomIcon.EDIT, size=18),
                on_click=lambda e, r=record: open_edit_dialog(r),
                tooltip="Sửa",
                padding=8,
                border_radius=4,
                ink=True,
            )
            
            delete_btn = None
            if is_admin(role):
                delete_btn = ft.Container(
                    content=CustomIcon.create(CustomIcon.DELETE, size=18),
                    on_click=lambda e, r=record: confirm_delete(r),
                    tooltip="Xóa",
                    padding=8,
                    border_radius=4,
                    ink=True,
                )
            
            action_buttons = [checkbox, edit_btn]
            if delete_btn:
                action_buttons.append(delete_btn)
            
            # Format date
            ngay_muon = record.get("ngay_muon", "") or ""
            if ngay_muon and "/" not in ngay_muon:
                try:
                    dt = datetime.strptime(ngay_muon, "%Y-%m-%d")
                    ngay_muon = dt.strftime("%d/%m/%Y")
                except:
                    pass
            
            # Color code trạng thái
            trang_thai = record.get("trang_thai", "Trong phòng")
            if trang_thai == "Trong phòng":
                trang_thai_color = ft.Colors.GREEN_700
            elif trang_thai == "Đang cho mượn":
                trang_thai_color = ft.Colors.ORANGE_700
            else:
                trang_thai_color = ft.Colors.GREY_700
            
            ghi_chu = record.get("ghi_chu", "") or ""
            nguoi_muon = record.get("nguoi_muon", "") or ""
            
            return ft.DataRow(
                cells=[
                    ft.DataCell(ft.Text(record.get("ma_tai_san", ""), size=13, weight=ft.FontWeight.BOLD)),
                    ft.DataCell(ft.Text(record.get("ten_tai_san", ""), size=13)),
                    ft.DataCell(ft.Text(str(record.get("so_luong", 0)), size=13, color=ft.Colors.BLUE_700)),
                    ft.DataCell(ft.Text(record.get("tinh_trang", "")[:20] + "..." if len(record.get("tinh_trang", "")) > 20 else record.get("tinh_trang", ""), size=12)),
                    ft.DataCell(ft.Text(trang_thai, size=12, weight=ft.FontWeight.BOLD, color=trang_thai_color)),
                    ft.DataCell(ft.Text(nguoi_muon[:20] + "..." if len(nguoi_muon) > 20 else nguoi_muon, size=12)),
                    ft.DataCell(ft.Text(ngay_muon, size=12, color=ft.Colors.GREY_700)),
                    ft.DataCell(ft.Text(ghi_chu[:25] + "..." if len(ghi_chu) > 25 else ghi_chu, size=11, color=ft.Colors.GREY_600)),
                    ft.DataCell(ft.Row(action_buttons, spacing=4)),
                ],
            )
        
        # ===================== SELECTION =====================
        def toggle_selection(id: str, selected: bool):
            if selected:
                state["selected_ids"].add(id)
            else:
                state["selected_ids"].discard(id)
            
            select_all_checkbox.value = (
                len(state["selected_ids"]) == len(state["records"]) 
                and len(state["records"]) > 0
            )
            
            selected_count_text.value = f"Đã chọn: {len(state['selected_ids'])}"
            safe_update()
        
        def toggle_select_all(select_all: bool):
            if select_all:
                for r in state["records"]:
                    state["selected_ids"].add(r["id"])
            else:
                for r in state["records"]:
                    state["selected_ids"].discard(r["id"])
            
            table.rows.clear()
            for r in state["records"]:
                table.rows.append(build_row(r))
            
            selected_count_text.value = f"Đã chọn: {len(state['selected_ids'])}"
            safe_update()
        
        # ===================== FILTERS =====================
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
        
        def clear_filters(e):
            state["search_text"] = ""
            state["filter_trang_thai"] = ""
            state["page_index"] = 1
            state["selected_ids"].clear()
            
            search_field.value = ""
            filter_trang_thai_dropdown.value = ""
            select_all_checkbox.value = False
            
            page.run_task(load_data_async)
        
        # ===================== PAGINATION =====================
        def update_pagination():
            total_pages = max(1, (state["total_records"] + PAGE_SIZE - 1) // PAGE_SIZE)
            pagination_text.value = f"Trang {state['page_index']} / {total_pages} — Tổng {state['total_records']} tài sản"
        
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
        
        # ===================== CRUD DIALOGS - TÀI SẢN =====================
        def open_create_dialog(e):
            """Thêm tài sản mới"""
            dialog_container = ft.Container()
            dialog_message_manager = MessageManager(page, dialog_container)

            fields = {
                "ma_tai_san": ft.TextField(label="Mã tài sản *", autofocus=True, hint_text="VD: TS001"),
                "ten_tai_san": ft.TextField(label="Tên tài sản *", hint_text="VD: Máy chiếu Epson"),
                "so_luong": ft.TextField(label="Số lượng *", value="1", keyboard_type=ft.KeyboardType.NUMBER),
                "tinh_trang": ft.TextField(label="Tình trạng", hint_text="VD: Tốt, Cần bảo trì..."),
                "trang_thai": ft.Dropdown(label="Trạng thái", value="Trong phòng", options=[ft.dropdown.Option("Trong phòng"), ft.dropdown.Option("Đang cho mượn"), ft.dropdown.Option("Hỏng"), ft.dropdown.Option("Thanh lý")]),
                "nguoi_muon": ft.TextField(label="Người mượn", hint_text="Họ tên người mượn"),
                "ngay_muon": ft.TextField(label="Ngày mượn", hint_text="dd/mm/yyyy"),
                "ghi_chu": ft.TextField(label="Ghi chú", multiline=True, min_lines=2, max_lines=4),
            }

            async def submit(ev):
                submit_btn.disabled = True
                cancel_btn.disabled = True
                page.update()

                try:
                    payload = {k: v.value for k, v in fields.items() if v.value}

                    if not payload.get("ma_tai_san") or not payload.get("ten_tai_san"):
                        submit_btn.disabled = False
                        cancel_btn.disabled = False
                        dialog_message_manager.error("Thiếu mã hoặc tên tài sản")
                        return

                    await asyncio.to_thread(create_tai_san, payload)

                    close_dialog_safe()
                    message_manager.success("Đã thêm tài sản")
                    await load_data_async()

                except Exception as ex:
                    submit_btn.disabled = False
                    cancel_btn.disabled = False
                    dialog_message_manager.error(f"Lỗi: {ex}")

            cancel_btn = ft.TextButton("Hủy", on_click=lambda e: close_dialog_safe())
            submit_btn = ft.ElevatedButton("Thêm", on_click=lambda e: page.run_task(submit, e), bgcolor=ft.Colors.GREEN_600, color=ft.Colors.WHITE)

            content = ft.Container(
                width=500,
                content=ft.Column([
                    ft.Container(
                        content=ft.Row([
                            ft.Container(content=CustomIcon.create(CustomIcon.ADD, size=24), padding=10, bgcolor=ft.Colors.GREEN_50, border_radius=50),
                            ft.Column([ft.Text("Thêm tài sản mới", size=16, weight=ft.FontWeight.BOLD, color=ft.Colors.GREEN_900), ft.Text("Nhập thông tin tài sản", size=12, color=ft.Colors.GREY_700)], spacing=2),
                        ], spacing=10),
                        padding=10,
                        border=ft.border.all(1, ft.Colors.GREEN_100),
                        border_radius=8,
                        bgcolor=ft.Colors.GREEN_50,
                    ),
                    ft.Divider(height=10, color=ft.Colors.TRANSPARENT),
                    *list(fields.values()),
                ], spacing=12, scroll=ft.ScrollMode.AUTO, height=400),
            )

            dialog_container.content = ft.Stack([content])

            dialog = ft.AlertDialog(modal=True, title=ft.Row([CustomIcon.create(CustomIcon.ADD, size=24), ft.Text("Thêm tài sản mới", weight=ft.FontWeight.BOLD)], spacing=10), content=dialog_container, actions=[cancel_btn, submit_btn], bgcolor=ft.Colors.WHITE, content_padding=24)

            show_dialog_safe(dialog)
        
        def open_edit_dialog(record: dict):
            dialog_container = ft.Container()
            dialog_message_manager = MessageManager(page, dialog_container)

            ngay_muon = record.get("ngay_muon", "")
            if ngay_muon and "/" not in ngay_muon:
                try:
                    dt = datetime.strptime(ngay_muon, "%Y-%m-%d")
                    ngay_muon = dt.strftime("%d/%m/%Y")
                except:
                    pass

            fields = {
                "ma_tai_san": ft.TextField(label="Mã tài sản *", value=record.get("ma_tai_san", ""), disabled=True, bgcolor=ft.Colors.GREY_100),
                "ten_tai_san": ft.TextField(label="Tên tài sản *", value=record.get("ten_tai_san", "")),
                "so_luong": ft.TextField(label="Số lượng", value=str(record.get("so_luong", 1)), keyboard_type=ft.KeyboardType.NUMBER),
                "tinh_trang": ft.TextField(label="Tình trạng", value=record.get("tinh_trang", "") or ""),
                "trang_thai": ft.Dropdown(label="Trạng thái", value=record.get("trang_thai", "Trong phòng"), options=[ft.dropdown.Option("Trong phòng"), ft.dropdown.Option("Đang cho mượn"), ft.dropdown.Option("Hỏng"), ft.dropdown.Option("Thanh lý")]),
                "nguoi_muon": ft.TextField(label="Người mượn", value=record.get("nguoi_muon", "") or ""),
                "ngay_muon": ft.TextField(label="Ngày mượn", value=ngay_muon, hint_text="dd/mm/yyyy"),
                "ghi_chu": ft.TextField(label="Ghi chú", value=record.get("ghi_chu", "") or "", multiline=True, min_lines=2, max_lines=4),
            }

            async def submit(e):
                submit_btn.disabled = True
                cancel_btn.disabled = True
                page.update()

                try:
                    payload = {k: v.value.strip() if isinstance(v.value, str) else v.value for k, v in fields.items() if v.value and k != "ma_tai_san"}

                    await asyncio.to_thread(update_tai_san, record["id"], payload)

                    close_dialog_safe()
                    message_manager.success("Đã cập nhật")
                    await load_data_async()

                except Exception as ex:
                    submit_btn.disabled = False
                    cancel_btn.disabled = False
                    dialog_message_manager.error(f"Lỗi: {ex}")

            cancel_btn = ft.TextButton("Hủy", on_click=lambda e: close_dialog_safe())
            submit_btn = ft.ElevatedButton("Lưu", on_click=lambda e: page.run_task(submit, e), bgcolor=ft.Colors.BLUE_600, color=ft.Colors.WHITE)

            content = ft.Container(
                width=500,
                content=ft.Column([
                    ft.Container(
                        content=ft.Row([
                            ft.Container(content=CustomIcon.create(CustomIcon.EDIT, size=24), padding=10, bgcolor=ft.Colors.BLUE_50, border_radius=50),
                            ft.Column([ft.Text(f"{record.get('ten_tai_san', '')}", size=16, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_900), ft.Text("Chỉnh sửa tài sản", size=12, color=ft.Colors.GREY_700)], spacing=2),
                        ], spacing=10),
                        padding=10,
                        border=ft.border.all(1, ft.Colors.BLUE_100),
                        border_radius=8,
                        bgcolor=ft.Colors.BLUE_50,
                    ),
                    ft.Divider(height=10, color=ft.Colors.TRANSPARENT),
                    *list(fields.values()),
                ], spacing=12, scroll=ft.ScrollMode.AUTO, height=400),
            )

            dialog_container.content = ft.Stack([content])

            dialog = ft.AlertDialog(modal=True, title=ft.Row([CustomIcon.create(CustomIcon.EDIT, size=24), ft.Text(f"Sửa: {record.get('ten_tai_san', '')}", weight=ft.FontWeight.BOLD)], spacing=10), content=dialog_container, actions=[cancel_btn, submit_btn], bgcolor=ft.Colors.WHITE, content_padding=24)

            show_dialog_safe(dialog)
        
        def confirm_delete(record: dict):
            """Xác nhận xóa tài sản"""
            dialog_container = ft.Container()
            dialog_message_manager = MessageManager(page, dialog_container)

            async def do_delete(e):
                delete_btn.disabled = True
                cancel_btn.disabled = True
                page.update()

                try:
                    await asyncio.to_thread(delete_tai_san, record["id"])

                    close_dialog_safe()
                    message_manager.success(f"Đã xóa: {record.get('ten_tai_san', '')}")
                    await load_data_async()

                except Exception as ex:
                    delete_btn.disabled = False
                    cancel_btn.disabled = False
                    dialog_message_manager.error(f"Lỗi xóa: {ex}")

            cancel_btn = ft.TextButton("Hủy", on_click=lambda e: close_dialog_safe())
            delete_btn = ft.ElevatedButton("Xóa", on_click=lambda e: page.run_task(do_delete, e), bgcolor=ft.Colors.RED_600, color=ft.Colors.WHITE)

            dialog = ft.AlertDialog(
                modal=True,
                title=ft.Row([CustomIcon.create(CustomIcon.WARNING, 28), ft.Text("Xác nhận xóa", size=18)], spacing=10),
                content=ft.Container(
                    content=ft.Column([
                        ft.Container(
                            content=ft.Row([
                                CustomIcon.create(CustomIcon.DELETE_FOREVER, size=48),
                                ft.Column([
                                    ft.Text("Bạn có chắc muốn xóa tài sản này?", size=14, weight=ft.FontWeight.W_500),
                                    ft.Text(record.get('ten_tai_san', ''), size=16, weight=ft.FontWeight.BOLD, color=ft.Colors.RED_700),
                                    ft.Text("Hành động này không thể hoàn tác!", size=12, color=ft.Colors.RED_600, italic=True),
                                ], spacing=4, expand=True)
                            ], spacing=15),
                            padding=15,
                            border=ft.border.all(2, ft.Colors.RED_200),
                            border_radius=8,
                            bgcolor=ft.Colors.RED_50,
                        ),
                    ], spacing=0, tight=True),
                    width=400,
                ),
                actions=[cancel_btn, delete_btn],
                bgcolor=ft.Colors.WHITE,
                content_padding=24,
            )

            show_dialog_safe(dialog)
        
        # ===================== EXPORT - TÀI SẢN =====================
        def export_excel_action(e):
            if not state["selected_ids"]:
                message_manager.warning("Chưa chọn tài sản")
                return

            import os
            import pandas as pd
            from io import BytesIO

            downloads_folder = os.path.join(os.path.expanduser("~"), "Downloads")
            filename = f"export_tai_san_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            save_path = os.path.join(downloads_folder, filename)

            message_manager.info(f"Đang xuất {len(state['selected_ids'])} tài sản...")

            async def _export():
                try:
                    data = await asyncio.to_thread(get_all_tai_san_for_export, list(state["selected_ids"]))

                    if not data:
                        raise ValueError("Không có dữ liệu để export")

                    df = pd.DataFrame(data)

                    # Select columns
                    columns = ["ma_tai_san", "ten_tai_san", "so_luong", "tinh_trang",
                              "trang_thai", "nguoi_muon", "ngay_muon", "ghi_chu"]
                    df = df[[col for col in columns if col in df.columns]]

                    # Rename
                    df.rename(columns={
                        "ma_tai_san": "Mã tài sản",
                        "ten_tai_san": "Tên tài sản",
                        "so_luong": "Số lượng",
                        "tinh_trang": "Tình trạng",
                        "trang_thai": "Trạng thái",
                        "nguoi_muon": "Người mượn",
                        "ngay_muon": "Ngày mượn",
                        "ghi_chu": "Ghi chú",
                    }, inplace=True)

                    # Export to BytesIO then save
                    output = BytesIO()
                    with pd.ExcelWriter(output, engine='openpyxl') as writer:
                        df.to_excel(writer, index=False, sheet_name='Tài sản')

                    with open(save_path, "wb") as f:
                        f.write(output.getvalue())

                    file_size = os.path.getsize(save_path) / 1024

                    content = ft.Column([
                        ft.Row([
                            ft.Container(
                                content=ft.Column([
                                    ft.Text("Số lượng", size=12, color=ft.Colors.GREY_700),
                                    ft.Text(f"{len(state['selected_ids'])} tài sản", size=18, weight=ft.FontWeight.BOLD, color=ft.Colors.GREY_900),
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
                            content=ft.Text(save_path, size=11, selectable=True, color=ft.Colors.BLUE_800),
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
                        content=ft.Container(content=content, width=450, padding=20),
                        actions=[
                            ft.Row([
                                ft.ElevatedButton(
                                    content=ft.Row([CustomIcon.create(CustomIcon.CHECK_WHITE, size=16), ft.Text("Đóng", size=13, weight=ft.FontWeight.W_500)], spacing=6),
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
                    message_manager.error(f"Lỗi: {ex}")

            page.run_task(_export)
        
        # ===================== BULK UPDATE - TÀI SẢN =====================
        def open_bulk_update_dialog(e):
            """Cập nhật hàng loạt tài sản (sử dụng MessageManager, không dùng threading)"""
            if not state["selected_ids"]:
                MessageManager(page).warning("Chưa chọn tài sản", "Cảnh báo")
                return

            field_states = {"trang_thai": False, "tinh_trang": False, "ghi_chu": False}

            # Fields
            enable_trang_thai = ft.Checkbox(label="", value=False,
                on_change=lambda e: toggle_field("trang_thai", e.control.value))
            trang_thai_dropdown = ft.Dropdown(
                label="Giá trị mới",
                value="Trong phòng",
                disabled=True,
                options=[
                    ft.dropdown.Option("Trong phòng"),
                    ft.dropdown.Option("Đang cho mượn"),
                    ft.dropdown.Option("Hỏng"),
                    ft.dropdown.Option("Thanh lý"),
                ],
                width=200,
            )

            enable_tinh_trang = ft.Checkbox(label="", value=False,
                on_change=lambda e: toggle_field("tinh_trang", e.control.value))
            tinh_trang_field = ft.TextField(
                label="Giá trị mới",
                hint_text="VD: Tốt, Cần bảo trì",
                disabled=True,
                width=300,
            )
            clear_tinh_trang_btn = ft.Container(
                content=CustomIcon.create(CustomIcon.DELETE, size=18),
                tooltip="Xóa tình trạng",
                visible=False,
                on_click=lambda e: set_field_value("tinh_trang", ""),
                padding=8,
                border_radius=4,
                ink=True,
            )

            enable_ghi_chu = ft.Checkbox(label="", value=False,
                on_change=lambda e: toggle_field("ghi_chu", e.control.value))
            ghi_chu_field = ft.TextField(
                label="Giá trị mới",
                hint_text="Nhập ghi chú",
                multiline=True,
                min_lines=2,
                max_lines=3,
                disabled=True,
                width=300,
            )
            clear_ghi_chu_btn = ft.Container(
                content=CustomIcon.create(CustomIcon.DELETE, size=18),
                tooltip="Xóa ghi chú",
                visible=False,
                on_click=lambda e: set_field_value("ghi_chu", ""),
                padding=8,
                border_radius=4,
                ink=True,
            )

            field_controls = {
                "trang_thai": {"checkbox": enable_trang_thai, "input": trang_thai_dropdown},
                "tinh_trang": {"checkbox": enable_tinh_trang, "input": tinh_trang_field, "clear": clear_tinh_trang_btn},
                "ghi_chu": {"checkbox": enable_ghi_chu, "input": ghi_chu_field, "clear": clear_ghi_chu_btn},
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

            def handle_cancel(e):
                close_dialog_safe()

            async def _process_bulk_async():
                try:
                    payload = {}
                    if field_states["trang_thai"]:
                        payload["trang_thai"] = trang_thai_dropdown.value
                    if field_states["tinh_trang"]:
                        payload["tinh_trang"] = (tinh_trang_field.value or "").strip()
                    if field_states["ghi_chu"]:
                        payload["ghi_chu"] = (ghi_chu_field.value or "").strip()

                    if not payload:
                        MessageManager(page, dialog_container).warning("Chưa chọn trường nào để cập nhật", "Cảnh báo")
                        return

                    ids = list(state["selected_ids"])

                    # Run blocking DB update in thread via asyncio.to_thread
                    import asyncio
                    await asyncio.to_thread(bulk_update_tai_san, ids, payload)

                    # UI finalize
                    state["selected_ids"].clear()
                    select_all_checkbox.value = False
                    close_dialog_safe()
                    MessageManager(page).success(f"Cập nhật {len(ids)} tài sản: {', '.join(payload.keys())}")
                    await asyncio.sleep(0.05)
                    await load_data_async()

                except Exception as ex:
                    MessageManager(page).error(str(ex), "Lỗi")

            def handle_submit(e):
                # disable buttons until task completes
                submit_btn.disabled = True
                cancel_btn.disabled = True
                page.update()
                page.run_task(_process_bulk_async)

            cancel_btn = ft.TextButton(content=ft.Row([CustomIcon.create(CustomIcon.CLOSE, 16), ft.Text("Hủy")], spacing=8), on_click=handle_cancel)
            submit_btn = ft.ElevatedButton(content=ft.Row([CustomIcon.create(CustomIcon.CHECK, 16), ft.Text("Xác nhận")], spacing=8), on_click=handle_submit)

            def build_field_row(label: str, checkbox, input_control, clear_btn=None):
                controls = [
                    ft.Container(content=ft.Text(label, size=13, weight=ft.FontWeight.W_500), width=120),
                    checkbox,
                    input_control,
                ]
                if clear_btn:
                    controls.append(clear_btn)
                return ft.Row(controls=controls, alignment=ft.MainAxisAlignment.START, spacing=8)

            # Dialog content container (so MessageManager can layer into it)
            dialog_container = ft.Container(
                width=540,
                padding=ft.padding.all(12),
                border_radius=8,
                bgcolor=ft.Colors.WHITE,
                shadow=ft.BoxShadow(blur_radius=20, color=ft.Colors.with_opacity(0.12, ft.Colors.BLACK)),
                content=ft.Stack([
                    ft.Image(src=CustomIcon.STORAGE, fit="cover", opacity=0.03),
                    ft.Column([
                        ft.Row([ft.Container(width=120), ft.Container(content=ft.Text("Cập nhật?", size=11, weight=ft.FontWeight.BOLD), width=50), ft.Text("Giá trị mới", size=11, weight=ft.FontWeight.BOLD)], spacing=8),
                        ft.Divider(height=1),
                        build_field_row("Trạng thái", enable_trang_thai, trang_thai_dropdown),
                        build_field_row("Tình trạng", enable_tinh_trang, tinh_trang_field, clear_tinh_trang_btn),
                        build_field_row("Ghi chú", enable_ghi_chu, ghi_chu_field, clear_ghi_chu_btn),
                    ], spacing=12, scroll=ft.ScrollMode.AUTO, height=250)
                ])
            )

            dialog = ft.AlertDialog(modal=True, title=ft.Text(f"Cập nhật {len(state['selected_ids'])} tài sản"), content=dialog_container, actions=[cancel_btn, submit_btn])

            # show dialog and ensure MessageManager attaches to dialog container
            dialog_message_manager = MessageManager(page, dialog_container)
            show_dialog_safe(dialog)
        
        # ===================== UI LAYOUT - TÀI SẢN =====================
        search_field = ft.TextField(
            label="Tìm theo mã / tên tài sản",
            prefix=CustomIcon.prefix_icon(CustomIcon.SEARCH),
            hint_text="Nhập từ khóa...",
            width=400,
            on_submit=on_search,
        )
        
        filter_trang_thai_dropdown = ft.Dropdown(
            label="Lọc trạng thái",
            hint_text="Tất cả",
            width=200,
            options=[
                ft.dropdown.Option("Trong phòng"),
                ft.dropdown.Option("Đang cho mượn"),
                ft.dropdown.Option("Hỏng"),
                ft.dropdown.Option("Thanh lý"),
            ],
        )
        filter_trang_thai_dropdown.on_change = on_filter_trang_thai  # ✅ Thêm dòng này
        
        buttons = []
        if is_admin(role):
            buttons.append(elevated_button("Thêm mới", CustomIcon.ADD, on_click=open_create_dialog))
        buttons.extend([
            elevated_button("Export", CustomIcon.DOWNLOAD, on_click=export_excel_action),
            elevated_button("Sửa hàng loạt", CustomIcon.EDIT, on_click=open_bulk_update_dialog),
        ])
        
        toolbar = ft.Column([
            ft.Row(
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                controls=[
                    ft.Row([search_field, loading_indicator], spacing=8),
                    ft.Row(spacing=8, controls=buttons),
                ],
            ),
            ft.Row([filter_trang_thai_dropdown, ft.TextButton("Xóa lọc", on_click=clear_filters)], spacing=8),
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
            await asyncio.sleep(0.2)
            await load_data_async()

        page.run_task(_delayed_load)
        
        return result

    # MAIN TAB LAYOUT - SUB-TAB NAVIGATION
    sub_tab_buttons = []
    
    sub_tabs = [
        {"name": "Sổ Đoàn thất lạc", "icon": CustomIcon.BADGE, "content": SoDoanTab()},
        {"name": "Tài sản phòng", "icon": CustomIcon.WORK, "content": TaiSanTab()},
    ]
    
    def switch_sub_tab(index):
        """Chuyển đổi sub-tab"""
        tab_state["current_index"] = index
        content_container.content = sub_tabs[index]["content"]
        
        # Update màu của buttons
        for i, btn in enumerate(sub_tab_buttons):
            if i == index:
                btn.bgcolor = ft.Colors.BLUE_600
                btn.content.controls[1].color = ft.Colors.WHITE
            else:
                btn.bgcolor = ft.Colors.GREY_300
                btn.content.controls[1].color = ft.Colors.GREY_800
        
        page.update()
    
    # Tạo sub-tab buttons
    for i, tab in enumerate(sub_tabs):
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
            on_click=lambda e, idx=i: switch_sub_tab(idx),
            ink=True,
        )
        sub_tab_buttons.append(btn)
    
    # Sub-tab navigation bar
    sub_tab_nav = ft.Container(
        content=ft.Row(
            controls=sub_tab_buttons,
            spacing=8,
        ),
        padding=ft.padding.all(12),
        bgcolor=ft.Colors.WHITE,
        border=ft.border.only(bottom=ft.BorderSide(1, ft.Colors.GREY_300)),
    )
    
    # Set nội dung ban đầu
    content_container.content = sub_tabs[0]["content"]
    content_container.bgcolor = ft.Colors.GREY_100
    content_container.padding = ft.padding.all(20)
    
    # Return main layout
    return ft.Column(
        spacing=0,
        expand=True,
        controls=[
            sub_tab_nav,
            content_container,
        ],
    )