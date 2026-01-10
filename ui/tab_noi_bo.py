
# ui/tab_noi_bo.py
import flet as ft
import asyncio
from datetime import datetime, timedelta
from services.noi_bo_service import (
    fetch_can_bo_bvp_bch,
    count_can_bo_bvp_bch,
    create_can_bo,
    update_can_bo,
    delete_can_bo,
    fetch_lich_truc,
    count_lich_truc,
    create_lich_truc,
    update_lich_truc,
    bulk_confirm_lich_truc,
    fetch_thong_ke_thang,
    get_thong_ke_tong_quan,
)
from services.sync_google_sheet import sync_full_week
from core.auth import is_admin
from ui.icon_helper import CustomIcon, elevated_button
from ui.message_manager import MessageManager

PAGE_SIZE = 100


def NoiBoTab(page: ft.Page, role: str):
    """Tab chính: Nội bộ với 3 sub-tabs"""
    
    # State cho sub-tabs
    tab_state = {"current_index": 0}
    
    # Container để hiển thị content
    content_container = ft.Container(expand=True)
    
    # ============================================================
    # HELPER: Sắp xếp cán bộ theo tiêu chí
    # ============================================================
    def sort_can_bo(can_bo_list):
        """
        Sắp xếp cán bộ theo:
        1. Loại (BCH Hội -> BCH Đoàn -> Ban Văn phòng -> CTV Ban Văn phòng)
        2. Chức danh (theo thứ tự ưu tiên)
        3. Alphabet tiếng Việt
        """
        # Mapping loại cán bộ -> priority
        loai_priority = {
            "BCH Hội": 1,
            "BCH Đoàn": 2,
            "Ban Văn phòng": 3,
            "CTV Ban Văn phòng": 4,
        }
        
        # Mapping chức danh -> priority
        chuc_vu_priority = {
            # BCH Hội
            "Phó Chủ tịch": 1,
            "Phó chủ tịch, Trưởng Ban KT": 2,
            "UV Ban Thư ký, Phó Ban KT": 3,
            "UV Ban Thư ký": 4,
            "Ủy viên": 5,
            "UV Ban Kiểm tra": 6,
            
            # Ban Văn phòng
            "Trưởng Ban": 11,
            "Phó Ban": 12,
            "Đội trưởng đội CTV": 13,
            "Thành viên": 14,
            "Cộng tác viên": 15,
        }
        
        def sort_key(cb):
            loai = cb.get("loai_can_bo", "")
            chuc_vu = cb.get("chuc_vu", "")
            ho_ten = cb.get("ho_ten", "")
            
            # Priority 1: Loại cán bộ
            loai_pri = loai_priority.get(loai, 999)
            
            # Priority 2: Chức danh
            chuc_vu_pri = chuc_vu_priority.get(chuc_vu, 999)
            
            # Priority 3: Tên (alphabet)
            return (loai_pri, chuc_vu_pri, ho_ten.lower())
        
        return sorted(can_bo_list, key=sort_key)
    
    # ============================================================
    # SUB-TAB 1: DANH SÁCH BVP/BCH
    # ============================================================
    def CanBoTab():
        """Sub-tab: Danh sách cán bộ BVP/BCH"""
        
        message_manager = MessageManager(page)
        
        state = {
            "can_bo": [],
            "selected_ids": set(),
            "page_index": 1,
            "total_records": 0,
            "search_text": "",
            "filter_loai": "",
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
                ft.DataColumn(ft.Text("Loại", weight=ft.FontWeight.BOLD)),
                ft.DataColumn(ft.Text("Chức vụ", weight=ft.FontWeight.BOLD)),
                ft.DataColumn(ft.Text("Họ tên", weight=ft.FontWeight.BOLD)),
                ft.DataColumn(ft.Text("MSSV", weight=ft.FontWeight.BOLD)),
                ft.DataColumn(ft.Text("SĐT", weight=ft.FontWeight.BOLD)),
                ft.DataColumn(ft.Text("Email", weight=ft.FontWeight.BOLD)),
                ft.DataColumn(ft.Text("Nhiệm kỳ", weight=ft.FontWeight.BOLD)),
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
            if state["active_dialog"] is None:
                return
            
            async def _close():
                try:
                    state["active_dialog"].open = False
                    page.update()
                    
                    await asyncio.sleep(0.05)
                    
                    if state["active_dialog"] in page.overlay:
                        page.overlay.remove(state["active_dialog"])
                    state["active_dialog"] = None
                    page.update()
                except Exception:
                    state["active_dialog"] = None
            
            page.run_task(_close)
        
        # ===================== DATA LOADING =====================
        async def load_data_async():
            if state["is_loading"]:
                return
            
            state["is_loading"] = True
            loading_indicator.visible = True
            page.update()
            
            try:
                total = count_can_bo_bvp_bch(
                    loai=state["filter_loai"],
                    search=state["search_text"]
                )
                
                can_bo = fetch_can_bo_bvp_bch(
                    loai=state["filter_loai"],
                    search=state["search_text"],
                    page=state["page_index"],
                    page_size=PAGE_SIZE
                )
                
                can_bo = sort_can_bo(can_bo)
                
                state["total_records"] = total
                state["can_bo"] = can_bo
                state["is_loading"] = False
                loading_indicator.visible = False
                
                table.rows.clear()
                for cb in can_bo:
                    table.rows.append(build_row(cb))
                
                update_pagination()
                selected_count_text.value = f"Đã chọn: {len(state['selected_ids'])}"
                page.update()
            
            except Exception as ex:
                pagination_text.value = f"⚠️ Lỗi: {str(ex)}"
                state["is_loading"] = False
                loading_indicator.visible = False
                page.update()
        
        # ===================== TABLE ROW BUILDER =====================
        def build_row(cb: dict):
            checkbox = ft.Checkbox(
                value=cb["id"] in state["selected_ids"],
                on_change=lambda e, id=cb["id"]: toggle_selection(id, e.control.value)
            )
            
            edit_btn = ft.Container(
                content=CustomIcon.create(CustomIcon.EDIT, size=18),
                on_click=lambda e, can_bo=cb: open_edit_dialog(can_bo),
                tooltip="Sửa cán bộ",
                padding=8,
                border_radius=4,
                ink=True,
            )
            
            delete_btn = None
            if is_admin(role):
                delete_btn = ft.Container(
                    content=CustomIcon.create(CustomIcon.DELETE, size=18),
                    on_click=lambda e, can_bo=cb: confirm_delete(can_bo),
                    tooltip="Xóa cán bộ",
                    padding=8,
                    border_radius=4,
                    ink=True,
                )
            
            action_buttons = [checkbox, edit_btn]
            if delete_btn:
                action_buttons.append(delete_btn)
            
            return ft.DataRow(
                cells=[
                    ft.DataCell(ft.Text(cb.get("loai_can_bo", "") or "")),
                    ft.DataCell(ft.Text(cb.get("chuc_vu", ""))),
                    ft.DataCell(ft.Text(cb.get("ho_ten", ""))),
                    ft.DataCell(ft.Text(cb.get("mssv", "") or "")),
                    ft.DataCell(ft.Text(cb.get("sdt", "") or "")),
                    ft.DataCell(ft.Text(cb.get("email", "") or "")),
                    ft.DataCell(ft.Text(cb.get("nhiem_ky", "") or "")),
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
                len(state["selected_ids"]) == len(state["can_bo"]) 
                and len(state["can_bo"]) > 0
            )
            
            selected_count_text.value = f"Đã chọn: {len(state['selected_ids'])}"
            page.update()
        
        def toggle_select_all(select_all: bool):
            if select_all:
                for cb in state["can_bo"]:
                    state["selected_ids"].add(cb["id"])
            else:
                for cb in state["can_bo"]:
                    state["selected_ids"].discard(cb["id"])
            
            table.rows.clear()
            for cb in state["can_bo"]:
                table.rows.append(build_row(cb))
            
            selected_count_text.value = f"Đã chọn: {len(state['selected_ids'])}"
            page.update()
        
        # ===================== FILTERS =====================
        def apply_filters(e=None):
            """Áp dụng tất cả filters (search + loại)"""
            state["page_index"] = 1
            state["selected_ids"].clear()
            select_all_checkbox.value = False
            page.run_task(load_data_async)
        
        def on_search(e):
            state["search_text"] = e.control.value.strip()
            apply_filters()
        
        def on_filter_loai(e):
            state["filter_loai"] = e.control.value if e.control.value else ""
            apply_filters()
        
        # ===================== PAGINATION =====================
        def update_pagination():
            total_pages = max(1, (state["total_records"] + PAGE_SIZE - 1) // PAGE_SIZE)
            pagination_text.value = f"Trang {state['page_index']} / {total_pages} – Tổng {state['total_records']} cán bộ"

        def prev_page(e):
            if state["page_index"] > 1:
                state["page_index"] -= 1
                state["selected_ids"].clear()
                select_all_checkbox.value = False
                load_data_async()
        
        def next_page(e):
            if state["page_index"] * PAGE_SIZE < state["total_records"]:
                state["page_index"] += 1
                state["selected_ids"].clear()
                select_all_checkbox.value = False
                load_data_async()
            
        # ===================== IMPORT/EXPORT =====================
        def import_excel_dialog(e):
            async def select_and_import():
                try:
                    import tkinter as tk
                    from tkinter import filedialog
                    
                    root = tk.Tk()
                    root.withdraw()
                    root.attributes('-topmost', True)
                    
                    file_path = filedialog.askopenfilename(
                        title="Chọn file Excel - Import Cán bộ",
                        filetypes=[
                            ("Excel files", "*.xlsx *.xls"),
                            ("All files", "*.*")
                        ]
                    )
                    
                    root.destroy()
                    
                    if not file_path:
                        return
                    
                    before_total = state.get("total_records", 0)
                    
                    message_manager.info("Đang xử lý file import...")
                    await asyncio.sleep(0)
                    
                    try:
                        from utils.can_bo_import_export import import_can_bo
                        
                        with open(file_path, "rb") as f:
                            file_bytes = f.read()
                        
                        imported_count, errors = import_can_bo(file_bytes)
                        
                        await load_data_async()
                        update_pagination()
                        await asyncio.sleep(0)
                        
                        after_total = state.get("total_records", 0)
                        diff = after_total - before_total
                        
                        if errors:
                            error_text = "\n".join(errors[:10])
                            if len(errors) > 10:
                                error_text += f"\n\n... và {len(errors) - 10} lỗi khác"
                            
                            result_dialog = ft.AlertDialog(
                                modal=True,
                                title=ft.Row([
                                    CustomIcon.create(CustomIcon.WARNING, size=24),
                                    ft.Text("Import có lỗi", size=18, weight=ft.FontWeight.BOLD)
                                ], spacing=10),
                                content=ft.Container(
                                    width=550,
                                    content=ft.Column([
                                        ft.Row([
                                            ft.Container(
                                                content=ft.Column([
                                                    ft.Text("Thêm mới", size=12, color=ft.Colors.GREEN_700),
                                                    ft.Text(str(max(diff, 0)), size=20, weight=ft.FontWeight.BOLD)
                                                ], spacing=4, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                                                bgcolor=ft.Colors.GREEN_50,
                                                padding=15,
                                                border_radius=8,
                                                expand=True,
                                            ),
                                            ft.Container(
                                                content=ft.Column([
                                                    ft.Text("Lỗi", size=12, color=ft.Colors.RED_700),
                                                    ft.Text(str(len(errors)), size=20, weight=ft.FontWeight.BOLD)
                                                ], spacing=4, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                                                bgcolor=ft.Colors.RED_50,
                                                padding=15,
                                                border_radius=8,
                                                expand=True,
                                            ),
                                        ], spacing=10),
                                        ft.Divider(),
                                        ft.Text("Chi tiết lỗi:", weight=ft.FontWeight.BOLD),
                                        ft.Container(
                                            content=ft.Text(
                                                error_text,
                                                size=11,
                                                selectable=True,
                                                color=ft.Colors.RED_900
                                            ),
                                            bgcolor=ft.Colors.RED_50,
                                            padding=12,
                                            border_radius=8,
                                            border=ft.border.all(1, ft.Colors.RED_200),
                                            height=300,
                                        ),
                                    ], scroll=ft.ScrollMode.AUTO),
                                ),
                                actions=[
                                    ft.ElevatedButton(
                                        content=ft.Row([
                                            CustomIcon.create(CustomIcon.CHECK, size=16),
                                            ft.Text("Đóng")
                                        ], spacing=6),
                                        on_click=lambda _: close_dialog_safe(),
                                    )
                                ],
                            )
                            
                            show_dialog_safe(result_dialog)
                            
                            if diff > 0:
                                message_manager.warning(f"Import xong, thêm {diff} cán bộ nhưng có lỗi")
                            else:
                                message_manager.error("Import thất bại, không có dữ liệu hợp lệ")
                        else:
                            if diff > 0:
                                message_manager.success(f"Import thành công {diff} cán bộ")
                            else:
                                message_manager.info("File không có cán bộ mới để import")
                    
                    except Exception as ex:
                        message_manager.error(f"Lỗi import: {ex}")
                
                except ImportError:
                    message_manager.error("Thiếu tkinter – không thể mở dialog chọn file")
                except Exception as ex:
                    message_manager.error(f"Lỗi: {ex}")
            
            page.run_task(select_and_import)


        def download_template_dialog(e):
            async def create_and_save_template():
                try:
                    import pandas as pd
                    from io import BytesIO
                    import os
                    
                    template_data = {
                        "loai_can_bo": ["Ban Văn phòng", "BCH Đoàn", "BCH Hội"],
                        "chuc_vu": ["Trưởng Ban", "Phó Chủ tịch", "Ủy viên"],
                        "ho_ten": ["Nguyễn Văn A", "Trần Thị B", "Lê Văn C"],
                        "mssv": ["74123456", "74123457", ""],
                        "khoa_hoc": ["K74", "K74", "K75"],
                        "sdt": ["0123456789", "0987654321", ""],
                        "email": ["email1@example.com", "email2@example.com", ""],
                        "nhiem_ky": ["2024-2025", "2024-2025", "2024-2025"],
                    }
                    
                    df = pd.DataFrame(template_data)
                    
                    output = BytesIO()
                    with pd.ExcelWriter(output, engine='openpyxl') as writer:
                        df.to_excel(writer, index=False, sheet_name='Cán bộ')
                        
                        worksheet = writer.sheets['Cán bộ']
                        for idx, col in enumerate(df.columns, 1):
                            max_length = max(
                                df[col].astype(str).map(len).max(),
                                len(str(col))
                            )
                            col_letter = chr(64 + idx)
                            worksheet.column_dimensions[col_letter].width = min(max_length + 3, 40)
                    
                    downloads_folder = os.path.join(os.path.expanduser("~"), "Downloads")
                    filename = "template_import_can_bo.xlsx"
                    save_path = os.path.join(downloads_folder, filename)
                    
                    with open(save_path, "wb") as f:
                        f.write(output.getvalue())
                    
                    required_items = [
                        ("loai_can_bo", "Ban Văn phòng | BCH Đoàn | BCH Hội"),
                        ("chuc_vu", "Chức vụ của cán bộ"),
                        ("ho_ten", "Họ và tên cán bộ"),
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
                        ("khoa_hoc", "Khóa học (VD: K74, K75)"),
                        ("sdt", "Số điện thoại"),
                        ("email", "Email"),
                        ("nhiem_ky", "Nhiệm kỳ (VD: 2024-2025)"),
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
                    title=ft.Row([
                        CustomIcon.create(CustomIcon.WARNING, size=24),
                        ft.Text("Chưa chọn cán bộ", size=18, weight=ft.FontWeight.BOLD),
                    ], spacing=8),
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
                    from utils.can_bo_import_export import export_can_bo
                    
                    excel_bytes = export_can_bo(selected)
                    
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

        # ===================== BULK UPDATE =====================
        def open_bulk_update_dialog(e):
            """Cập nhật hàng loạt - UI Refactored"""
            selected_count = len(state["selected_ids"])
            if not state["selected_ids"]:
                message_manager.warning("Chưa chọn cán bộ nào để cập nhật")
                return

            dialog_container = ft.Container()
            dialog_message_manager = MessageManager(page, dialog_container)
            
            field_states = {
                "loai_can_bo": False,
                "chuc_vu": False,
                "mssv": False,
                "khoa_hoc": False,
                "sdt": False,
                "email": False,
                "nhiem_ky": False,
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

            enable_loai = ft.Checkbox(value=False, on_change=lambda e: toggle_field("loai_can_bo", e.control.value))
            loai_dropdown = ft.Dropdown(
                label="Loại cán bộ mới", value="Ban Văn phòng", disabled=True, expand=True, text_size=13, height=40, content_padding=10,
                options=[ft.dropdown.Option("Ban Văn phòng"), ft.dropdown.Option("BCH Đoàn"), ft.dropdown.Option("BCH Hội")]
            )

            enable_chuc_vu = ft.Checkbox(value=False, on_change=lambda e: toggle_field("chuc_vu", e.control.value))
            chuc_vu_field = ft.TextField(label="Chức vụ mới", hint_text="VD: Trưởng Ban", disabled=True, expand=True, text_size=13, height=40, content_padding=10)
            clear_chuc_vu_btn = ft.IconButton(icon=ft.Icons.CLEAR, icon_size=16, tooltip="Xóa", visible=False, on_click=lambda e: set_field_value("chuc_vu", ""))

            enable_mssv = ft.Checkbox(value=False, on_change=lambda e: toggle_field("mssv", e.control.value))
            mssv_field = ft.TextField(label="MSSV mới", hint_text="VD: 74123456", disabled=True, expand=True, text_size=13, height=40, content_padding=10)
            clear_mssv_btn = ft.IconButton(icon=ft.Icons.CLEAR, icon_size=16, tooltip="Xóa", visible=False, on_click=lambda e: set_field_value("mssv", ""))

            enable_khoa_hoc = ft.Checkbox(value=False, on_change=lambda e: toggle_field("khoa_hoc", e.control.value))
            khoa_hoc_field = ft.TextField(label="Khóa học mới", hint_text="VD: K74", disabled=True, expand=True, text_size=13, height=40, content_padding=10)
            clear_khoa_hoc_btn = ft.IconButton(icon=ft.Icons.CLEAR, icon_size=16, tooltip="Xóa", visible=False, on_click=lambda e: set_field_value("khoa_hoc", ""))

            enable_sdt = ft.Checkbox(value=False, on_change=lambda e: toggle_field("sdt", e.control.value))
            sdt_field = ft.TextField(label="SĐT mới", hint_text="VD: 0123456789", disabled=True, expand=True, text_size=13, height=40, content_padding=10)
            clear_sdt_btn = ft.IconButton(icon=ft.Icons.CLEAR, icon_size=16, tooltip="Xóa", visible=False, on_click=lambda e: set_field_value("sdt", ""))

            enable_email = ft.Checkbox(value=False, on_change=lambda e: toggle_field("email", e.control.value))
            email_field = ft.TextField(label="Email mới", hint_text="VD: email@example.com", disabled=True, expand=True, text_size=13, height=40, content_padding=10)
            clear_email_btn = ft.IconButton(icon=ft.Icons.CLEAR, icon_size=16, tooltip="Xóa", visible=False, on_click=lambda e: set_field_value("email", ""))

            enable_nhiem_ky = ft.Checkbox(value=False, on_change=lambda e: toggle_field("nhiem_ky", e.control.value))
            nhiem_ky_field = ft.TextField(label="Nhiệm kỳ mới", hint_text="VD: 2024-2025", disabled=True, expand=True, text_size=13, height=40, content_padding=10)
            clear_nhiem_ky_btn = ft.IconButton(icon=ft.Icons.CLEAR, icon_size=16, tooltip="Xóa", visible=False, on_click=lambda e: set_field_value("nhiem_ky", ""))

            field_controls = {
                "loai_can_bo": {"checkbox": enable_loai, "input": loai_dropdown},
                "chuc_vu": {"checkbox": enable_chuc_vu, "input": chuc_vu_field, "clear": clear_chuc_vu_btn},
                "mssv": {"checkbox": enable_mssv, "input": mssv_field, "clear": clear_mssv_btn},
                "khoa_hoc": {"checkbox": enable_khoa_hoc, "input": khoa_hoc_field, "clear": clear_khoa_hoc_btn},
                "sdt": {"checkbox": enable_sdt, "input": sdt_field, "clear": clear_sdt_btn},
                "email": {"checkbox": enable_email, "input": email_field, "clear": clear_email_btn},
                "nhiem_ky": {"checkbox": enable_nhiem_ky, "input": nhiem_ky_field, "clear": clear_nhiem_ky_btn},
            }

            async def handle_submit(e):
                submit_btn.disabled = True
                cancel_btn.disabled = True
                page.update()
                
                try:
                    payload = {}
                    if field_states["loai_can_bo"]: payload["loai_can_bo"] = loai_dropdown.value
                    if field_states["chuc_vu"]: payload["chuc_vu"] = chuc_vu_field.value.strip()
                    if field_states["mssv"]: payload["mssv"] = mssv_field.value.strip()
                    if field_states["khoa_hoc"]: payload["khoa_hoc"] = khoa_hoc_field.value.strip()
                    if field_states["sdt"]: payload["sdt"] = sdt_field.value.strip()
                    if field_states["email"]: payload["email"] = email_field.value.strip()
                    if field_states["nhiem_ky"]: payload["nhiem_ky"] = nhiem_ky_field.value.strip()
                    
                    if not payload:
                        submit_btn.disabled = False; cancel_btn.disabled = False
                        dialog_message_manager.warning("Chưa chọn trường nào để cập nhật")
                        return
                    
                    from services.noi_bo_service import bulk_update_can_bo
                    
                    bulk_update_can_bo(list(state["selected_ids"]), payload)
                    
                    state["selected_ids"].clear()
                    select_all_checkbox.value = False
                    close_dialog_safe()
                    updated_fields = ", ".join(payload.keys())
                    message_manager.success(f"Đã cập nhật {selected_count} cán bộ: {updated_fields}")
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
                                build_field_row("Loại cán bộ", enable_loai, loai_dropdown),
                                build_field_row("Chức vụ", enable_chuc_vu, chuc_vu_field, clear_chuc_vu_btn),
                                build_field_row("MSSV", enable_mssv, mssv_field, clear_mssv_btn),
                                ft.Divider(height=1, color=ft.Colors.GREY_100),
                                
                                build_field_row("Khóa học", enable_khoa_hoc, khoa_hoc_field, clear_khoa_hoc_btn),
                                build_field_row("SĐT", enable_sdt, sdt_field, clear_sdt_btn),
                                build_field_row("Email", enable_email, email_field, clear_email_btn),
                                ft.Divider(height=1, color=ft.Colors.GREY_100),
                                
                                build_field_row("Nhiệm kỳ", enable_nhiem_ky, nhiem_ky_field, clear_nhiem_ky_btn),
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

        # ===================== CRUD DIALOGS =====================
        def open_create_dialog(e):
            dialog_container = ft.Container()
            dialog_message_manager = MessageManager(page, dialog_container)
            
            fields = {
                "ho_ten": ft.TextField(label="Họ tên *", autofocus=True),
                "chuc_vu": ft.TextField(label="Chức vụ *", hint_text="VD: Chánh Văn phòng"),
                "loai_can_bo": ft.Dropdown(
                    label="Loại cán bộ *",
                    options=[
                        ft.dropdown.Option("Ban Văn phòng"),
                        ft.dropdown.Option("BCH Đoàn"),
                        ft.dropdown.Option("BCH Hội"),
                    ],
                ),
                "mssv": ft.TextField(label="MSSV", hint_text="VD: 74123456"),
                "khoa_hoc": ft.TextField(label="Khóa", hint_text="VD: K74"),
                "sdt": ft.TextField(label="SĐT", hint_text="VD: 0123456789"),
                "email": ft.TextField(label="Email", hint_text="example@email.com"),
                "nhiem_ky": ft.TextField(label="Nhiệm kỳ", hint_text="VD: 2024-2025"),
            }

            async def submit(ev):
                submit_btn.disabled = True
                cancel_btn.disabled = True
                page.update()
                
                try:
                    payload = {k: v.value for k, v in fields.items() if v.value}
                    
                    required = ["ho_ten", "chuc_vu", "loai_can_bo"]
                    missing = [f for f in required if not payload.get(f)]
                    if missing:
                        submit_btn.disabled = False
                        cancel_btn.disabled = False
                        dialog_message_manager.error(f"Thiếu trường bắt buộc: {', '.join(missing)}")
                        return
                    
                    create_can_bo(payload)
                    
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
        
        def open_edit_dialog(can_bo: dict):
            """Sửa thông tin cán bộ"""
            
            dialog_container = ft.Container()
            dialog_message_manager = MessageManager(page, dialog_container)
            
            fields = {
                "ho_ten": ft.TextField(label="Họ tên *", value=can_bo.get("ho_ten", "")),
                "chuc_vu": ft.TextField(label="Chức vụ *", value=can_bo.get("chuc_vu", "")),
                "loai_can_bo": ft.Dropdown(
                    label="Loại cán bộ *",
                    value=can_bo.get("loai_can_bo", ""),
                    options=[
                        ft.dropdown.Option("Ban Văn phòng"),
                        ft.dropdown.Option("BCH Đoàn"),
                        ft.dropdown.Option("BCH Hội"),
                    ],
                ),
                "mssv": ft.TextField(label="MSSV", value=can_bo.get("mssv", "")),
                "khoa_hoc": ft.TextField(label="Khóa", value=can_bo.get("khoa_hoc", "")),
                "sdt": ft.TextField(label="SĐT", value=can_bo.get("sdt", "")),
                "email": ft.TextField(label="Email", value=can_bo.get("email", "")),
                "nhiem_ky": ft.TextField(label="Nhiệm kỳ", value=can_bo.get("nhiem_ky", "")),
            }

            async def submit(e):
                submit_btn.disabled = True
                cancel_btn.disabled = True
                page.update()
                
                try:
                    payload = {k: v.value.strip() if isinstance(v.value, str) else v.value 
                              for k, v in fields.items() if v.value}
                    
                    update_can_bo(can_bo["id"], payload)
                    
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
                                ft.Text(can_bo['ho_ten'], size=16, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_900),
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
                    ft.Text(f"Sửa cán bộ: {can_bo['ho_ten']}", weight=ft.FontWeight.BOLD)
                ], spacing=10),
                content=dialog_container,
                actions=[cancel_btn, submit_btn],
                bgcolor=ft.Colors.WHITE,
                content_padding=24
            )

            show_dialog_safe(dialog)
        
        def confirm_delete(can_bo: dict):
            """Xác nhận xóa cán bộ"""
            
            async def do_delete(e):
                delete_btn.disabled = True
                cancel_btn.disabled = True
                page.update()
                
                try:
                    delete_can_bo(can_bo["id"])
                    
                    close_dialog_safe()
                    message_manager.success(f"Đã xóa cán bộ {can_bo['ho_ten']}")
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
                                    ft.Text(can_bo['ho_ten'], size=16, weight=ft.FontWeight.BOLD, color=ft.Colors.RED_700),
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

        # ===================== UI LAYOUT =====================
        search_field = ft.TextField(
            label="Tìm theo Họ tên / MSSV / SĐT",
            prefix=CustomIcon.prefix_icon(CustomIcon.SEARCH),
            hint_text="VD: Nguyễn Văn A",
            width=400,
            on_submit=on_search,
        )
        
        filter_loai_dropdown = ft.Dropdown(
            label="Lọc loại",
            width=200,
            options=[
                ft.dropdown.Option("Ban Văn phòng"),
                ft.dropdown.Option("BCH Đoàn"),
                ft.dropdown.Option("BCH Hội"),
            ],
        )
        filter_loai_dropdown.on_change = on_filter_loai
        
        apply_filter_btn = ft.ElevatedButton(
            "Áp dụng",
            icon=ft.Icons.SEARCH,
            on_click=apply_filters,
            bgcolor=ft.Colors.BLUE_600,
            color=ft.Colors.WHITE,
            height=40,
        )
        
        buttons = []
        if is_admin(role):
            buttons.extend([
                elevated_button("Thêm cán bộ", CustomIcon.ADD, on_click=open_create_dialog),
                elevated_button("Tải mẫu", CustomIcon.DOCUMENT, on_click=download_template_dialog),
                elevated_button("Import", CustomIcon.UPLOAD, on_click=import_excel_dialog),
                elevated_button("Export", CustomIcon.DOWNLOAD, on_click=export_excel_action),
            ])
        buttons.append(elevated_button("Sửa hàng loạt", CustomIcon.EDIT, on_click=open_bulk_update_dialog))
        
        toolbar = ft.Column([
            ft.Row(
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                controls=[
                    ft.Row([search_field, filter_loai_dropdown, apply_filter_btn, loading_indicator], spacing=8),
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
        
        async def _delayed_load():
            await asyncio.sleep(0.2)
            await load_data_async()
        
        page.run_task(_delayed_load)
        
        return result
    
    def LichTrucTab():
        """Sub-tab: Lịch trực văn phòng"""
        
        message_manager = MessageManager(page)
        
        state = {
            "lich_truc": [],
            "selected_ids": set(),
            "page_index": 1,
            "total_records": 0,
            "filter_ca": "",
            "filter_trang_thai": "",
            "tu_ngay": "",
            "den_ngay": "",
            "is_loading": False,
            "active_dialog": None,
            "view_mode": "list",
            "current_week_offset": 0,
        }
        
        loading_indicator = ft.ProgressRing(visible=False, width=30, height=30)
        
        # Loading overlay (cho sync)
        loading_overlay = ft.Container(
            visible=False,
            bgcolor=ft.Colors.with_opacity(0.7, ft.Colors.BLACK),
            content=ft.Column(
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.ProgressRing(width=60, height=60, color=ft.Colors.WHITE),
                    ft.Text("Đang đồng bộ...", size=18, color=ft.Colors.WHITE, weight=ft.FontWeight.BOLD),
                ],
            ),
        )
        
        select_all_checkbox = ft.Checkbox(
            label="Chọn tất cả trang này",
            value=False,
            on_change=lambda e: toggle_select_all(e.control.value)
        )
        
        table = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("Ngày", weight=ft.FontWeight.BOLD)),
                ft.DataColumn(ft.Text("Thứ", weight=ft.FontWeight.BOLD)),
                ft.DataColumn(ft.Text("Ca", weight=ft.FontWeight.BOLD)),
                ft.DataColumn(ft.Text("Họ tên", weight=ft.FontWeight.BOLD)),
                ft.DataColumn(ft.Text("SĐT", weight=ft.FontWeight.BOLD)),
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

        week_view_container = ft.Container()
        
        # ===================== HELPER: GET WEEK RANGE =====================
        def get_week_range(offset: int = 0):
            today = datetime.now().date()
            days_since_monday = today.weekday()  # 0=Monday, 6=Sunday
            current_monday = today - timedelta(days=days_since_monday)

            target_monday = current_monday + timedelta(weeks=offset)
            target_sunday = target_monday + timedelta(days=6)
            
            return target_monday, target_sunday
        
        # ===================== DIALOG MANAGEMENT =====================
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
                pass
            
            page.update()

        def close_dialog_safe():
            async def _close():
                if state["active_dialog"] is None:
                    return
                
                try:
                    state["active_dialog"].open = False
                    page.update()
                    
                    await asyncio.sleep(0.1)
                    
                    if state["active_dialog"] in page.overlay:
                        page.overlay.remove(state["active_dialog"])
                    
                    state["active_dialog"] = None
                    page.update()
                except Exception:
                    state["active_dialog"] = None
            
            page.run_task(_close)
        
        # ===================== SYNC GOOGLE SHEET =====================
        def handle_sync_sheet(e):
            def _build_stat_box(label, value, bg_color, text_color):
                return ft.Container(
                    content=ft.Column([
                        ft.Text(label, size=11, color=ft.Colors.GREY_700),
                        ft.Text(str(value), size=18, weight=ft.FontWeight.BOLD, color=text_color)
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=2),
                    bgcolor=bg_color, padding=10, border_radius=8, expand=True
                )
            async def run_sync_process(e):
                """Thực hiện sync với proper error handling"""
                # Disable nút để tránh click đúp
                sync_btn.disabled = True
                cancel_btn.disabled = True
                page.update()
                
                # Đóng dialog xác nhận trước
                try:
                    if state.get("active_dialog"):
                        state["active_dialog"].open = False
                        page.update()
                        await asyncio.sleep(0.1)
                        
                        if state["active_dialog"] in page.overlay:
                            page.overlay.remove(state["active_dialog"])
                        state["active_dialog"] = None
                except Exception:
                    pass
                
                # Hiện loading overlay
                loading_overlay.visible = True
                page.update()
                
                try:
                    # Chạy hàm sync nặng trong thread khác
                    result = await asyncio.to_thread(sync_full_week)
                    
                    # Tắt loading
                    loading_overlay.visible = False
                    page.update()
                    
                    # --- HIỂN THỊ KẾT QUẢ ---
                    await show_result_dialog(result)
                    
                except Exception as ex:
                    loading_overlay.visible = False
                    page.update()
                    message_manager.error(f"Lỗi hệ thống: {ex}")
            
            async def show_result_dialog(result):
                """Hiển thị dialog kết quả với error details"""
                is_success = result['success']
                total = result['total_success'] + result['total_errors']
                
                # Style cho dialog kết quả
                res_icon = CustomIcon.CHECK_GREEN if is_success else CustomIcon.WARNING
                res_bg = ft.Colors.GREEN_50 if is_success else ft.Colors.ORANGE_50
                res_border = ft.Colors.GREEN_200 if is_success else ft.Colors.ORANGE_200
                res_title = "Đồng bộ thành công" if is_success else "Đồng bộ có lỗi"
                res_text_color = ft.Colors.GREEN_900 if is_success else ft.Colors.ORANGE_900
                
                # Build content controls
                content_controls = [
                    # Header kết quả
                    ft.Container(
                        content=ft.Row([
                            ft.Container(
                                content=CustomIcon.create(res_icon, size=32),
                                padding=10, bgcolor=ft.Colors.WHITE, border_radius=50,
                                border=ft.border.all(1, res_border)
                            ),
                            ft.Column([
                                ft.Text(res_title, size=18, weight=ft.FontWeight.BOLD, color=res_text_color),
                                ft.Text(f"Thời gian xử lý: {result['duration']:.2f}s", size=12, color=ft.Colors.GREY_700),
                            ], spacing=2, tight=True)
                        ], spacing=15, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                        padding=15, bgcolor=res_bg, border_radius=10,
                        border=ft.border.all(1, res_border)
                    ),
                    
                    ft.Divider(height=20, color=ft.Colors.TRANSPARENT),
                    
                    # Thống kê chi tiết (Grid 3 cột)
                    ft.Row([
                        _build_stat_box("Tổng ca", total, ft.Colors.BLUE_50, ft.Colors.BLUE_700),
                        _build_stat_box("Thành công", result['total_success'], ft.Colors.GREEN_50, ft.Colors.GREEN_700),
                        _build_stat_box("Lỗi", result['total_errors'], ft.Colors.RED_50, ft.Colors.RED_700),
                    ], spacing=10),
                    
                    ft.Divider(height=10, color=ft.Colors.GREY_100),
                    
                    # Chi tiết Sáng/Chiều
                    ft.Row([
                        ft.Icon(ft.Icons.SUNNY, size=16, color=ft.Colors.ORANGE_500),
                        ft.Text(f"Sáng: {result['sang']['success']} ok / {result['sang']['errors']} lỗi", size=13),
                        ft.Container(width=10),
                        ft.Icon(ft.Icons.NIGHTLIGHT_ROUND, size=16, color=ft.Colors.BLUE_500),
                        ft.Text(f"Chiều: {result['chieu']['success']} ok / {result['chieu']['errors']} lỗi", size=13),
                    ], alignment=ft.MainAxisAlignment.CENTER)
                ]
                
                # ✅ Thêm chi tiết lỗi nếu có
                if not is_success and result.get('error_details'):
                    error_list = result['error_details']
                    error_text = "\n".join(error_list[:5])  # Chỉ hiện 5 lỗi đầu
                    if len(error_list) > 5:
                        error_text += f"\n\n... và {len(error_list) - 5} lỗi khác"
                    
                    content_controls.extend([
                        ft.Divider(height=10, color=ft.Colors.GREY_100),
                        ft.Container(
                            content=ft.Column([
                                ft.Row([
                                    CustomIcon.create(CustomIcon.WARNING, size=16),
                                    ft.Text("Chi tiết lỗi:", size=12, weight=ft.FontWeight.BOLD, color=ft.Colors.RED_900),
                                ], spacing=6),
                                ft.Container(height=6),
                                ft.Container(
                                    content=ft.Text(
                                        error_text,
                                        size=10,
                                        color=ft.Colors.RED_800,
                                        selectable=True,
                                    ),
                                    bgcolor=ft.Colors.RED_50,
                                    padding=10,
                                    border_radius=6,
                                    border=ft.border.all(1, ft.Colors.RED_200),
                                    height=120,
                                ),
                            ], spacing=4, tight=True),
                            padding=10,
                            bgcolor=ft.Colors.ORANGE_50,
                            border_radius=8,
                            border=ft.border.all(1, ft.Colors.ORANGE_200),
                        )
                    ])
                
                content_result = ft.Container(
                    width=500,
                    content=ft.Column(
                        controls=content_controls,
                        spacing=10, 
                        tight=True,
                        scroll=ft.ScrollMode.AUTO,
                    )
                )
                
                # ✅ Handler đóng dialog và reload
                async def handle_close_and_reload(e):
                    """Đóng dialog và reload data một cách an toàn"""
                    try:
                        # 1. Đóng dialog
                        if state.get("active_dialog"):
                            state["active_dialog"].open = False
                            page.update()
                            await asyncio.sleep(0.15)
                            
                            if state["active_dialog"] in page.overlay:
                                page.overlay.remove(state["active_dialog"])
                            state["active_dialog"] = None
                            page.update()
                        
                        # 2. Hiện loading
                        loading_indicator.visible = True
                        page.update()
                        
                        # 3. Reload data
                        if state["view_mode"] == "list":
                            await load_data_async()
                        else:
                            await load_week_view()
                        
                        # 4. Tắt loading
                        loading_indicator.visible = False
                        page.update()
                    
                    except Exception as ex:
                        # Force cleanup nếu lỗi
                        loading_indicator.visible = False
                        try:
                            page.overlay.clear()
                        except:
                            pass
                        state["active_dialog"] = None
                        page.update()
                        message_manager.error(f"Lỗi reload: {ex}")
                
                # Tạo dialog kết quả
                dialog_res = ft.AlertDialog(
                    modal=True,
                    title=ft.Row([
                        CustomIcon.create(CustomIcon.INFO, size=24),
                        ft.Text("Kết quả đồng bộ", weight=ft.FontWeight.BOLD, size=18)
                    ], spacing=10),
                    content=content_result,
                    actions=[
                        ft.ElevatedButton(
                            content=ft.Row([
                                CustomIcon.create(CustomIcon.CHECK_WHITE, size=16),
                                ft.Text("Đóng & Tải lại", size=14)
                            ], spacing=6, tight=True),
                            on_click=lambda e: page.run_task(handle_close_and_reload, e),
                            bgcolor=ft.Colors.BLUE_600, 
                            color=ft.Colors.WHITE,
                            height=42,
                        )
                    ],
                    actions_alignment=ft.MainAxisAlignment.END,
                    actions_padding=ft.padding.only(right=20, bottom=16),
                    content_padding=ft.padding.all(24),
                    bgcolor=ft.Colors.WHITE,
                    shape=ft.RoundedRectangleBorder(radius=12),
                )
                
                # Show dialog
                page.overlay.append(dialog_res)
                dialog_res.open = True
                state["active_dialog"] = dialog_res
                page.update()
            
            # 2. Tạo Dialog Xác nhận
            cancel_btn = ft.TextButton(
                "Hủy bỏ", 
                on_click=lambda _: close_dialog_safe(),
                style=ft.ButtonStyle(color=ft.Colors.GREY_700)
            )
            
            sync_btn = ft.ElevatedButton(
                content=ft.Row([
                    CustomIcon.create(CustomIcon.UPLOAD, size=18),
                    ft.Text("Bắt đầu đồng bộ", weight=ft.FontWeight.W_600)
                ], spacing=8, tight=True),
                on_click=lambda e: page.run_task(run_sync_process, e),
                bgcolor=ft.Colors.BLUE_600,
                color=ft.Colors.WHITE,
                style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8), elevation=0),
                height=42,
            )
            
            # Nội dung Dialog xác nhận
            content_confirm = ft.Container(
                width=450,
                content=ft.Column([
                    ft.Text("Bạn có chắc chắn muốn đồng bộ dữ liệu?", size=15, color=ft.Colors.GREY_800),
                    
                    # Info Box màu xanh
                    ft.Container(
                        content=ft.Row([
                            ft.Container(
                                content=CustomIcon.create(CustomIcon.UPLOAD, size=28),
                                padding=12, bgcolor=ft.Colors.WHITE, border_radius=50,
                                border=ft.border.all(1, ft.Colors.BLUE_100)
                            ),
                            ft.Column([
                                ft.Text("Nguồn: Google Sheet", weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_900),
                                ft.Text("Dữ liệu cũ sẽ được cập nhật.", size=12, color=ft.Colors.BLUE_700),
                            ], spacing=2)
                        ], spacing=15),
                        padding=15, bgcolor=ft.Colors.BLUE_50, 
                        border=ft.border.all(1, ft.Colors.BLUE_200), border_radius=10
                    ),
                    
                    # Warning Box màu cam
                    ft.Container(
                        content=ft.Row([
                            ft.Icon(ft.Icons.WARNING_AMBER, color=ft.Colors.ORANGE_800, size=20),
                            ft.Text("Lưu ý: Chỉ cập nhật các ca có trạng thái 'Đã đăng ký'", size=12, color=ft.Colors.ORANGE_900, italic=True)
                        ], spacing=10),
                        padding=10, bgcolor=ft.Colors.ORANGE_50, 
                        border=ft.border.all(1, ft.Colors.ORANGE_200), border_radius=8
                    )
                ], spacing=15, tight=True)
            )
            
            confirm_dialog = ft.AlertDialog(
                modal=True,
                title=ft.Row([
                    CustomIcon.create(CustomIcon.INFO, size=24),
                    ft.Text("Xác nhận đồng bộ", size=18, weight=ft.FontWeight.BOLD)
                ], spacing=10),
                content=content_confirm,
                actions=[cancel_btn, sync_btn],
                actions_alignment=ft.MainAxisAlignment.END,
                actions_padding=ft.padding.only(right=20, bottom=20),
                content_padding=ft.padding.all(24),
                shape=ft.RoundedRectangleBorder(radius=12),
                bgcolor=ft.Colors.WHITE
            )
            
            show_dialog_safe(confirm_dialog)
            
        # ===================== DELETE LICH TRUC =====================
        def delete_lich_truc_record(lich_id: str, lich_info: dict = None):
            """Xóa một dòng lịch trực"""
            from core.supabase_client import supabase
            
            async def do_delete(e):
                delete_btn.disabled = True
                cancel_btn.disabled = True
                page.update()
                
                try:
                    supabase.table('lich_truc').delete().eq('id', lich_id).execute()
                    
                    close_dialog_safe()
                    message_manager.success("Đã xóa lịch trực")
                    await load_data_async()
                        
                except Exception as process_ex:
                    delete_btn.disabled = False
                    cancel_btn.disabled = False
                    close_dialog_safe()
                    message_manager.error(f"Lỗi xóa: {str(process_ex)}")
            
            # Tạo nội dung chi tiết
            if lich_info:
                try:
                    ngay_obj = datetime.fromisoformat(str(lich_info.get("ngay_truc", "")))
                    ngay_str = ngay_obj.strftime("%d/%m/%Y")
                    thu_str = ["Thứ 2", "Thứ 3", "Thứ 4", "Thứ 5", "Thứ 6", "Thứ 7", "Chủ nhật"][ngay_obj.weekday()]
                except:
                    ngay_str = str(lich_info.get("ngay_truc", ""))
                    thu_str = ""
                
                ca_truc = lich_info.get('ca_truc', '')
                ca_icon = CustomIcon.SUNRISE if ca_truc == "Sáng" else CustomIcon.SUNSET
                
                content = ft.Column([
                    ft.Container(
                        content=ft.Row([
                            CustomIcon.create(CustomIcon.DELETE_FOREVER, size=48),
                            ft.Column([
                                ft.Text("Bạn có chắc chắn muốn xóa lịch trực này?", size=14, weight=ft.FontWeight.W_500),
                                ft.Text(lich_info.get('ho_ten', ''), size=16, weight=ft.FontWeight.BOLD, color=ft.Colors.RED_700),
                                ft.Text("Hành động này không thể hoàn tác!", size=12, color=ft.Colors.RED_600, italic=True),
                            ], spacing=4, expand=True)
                        ], spacing=15),
                        padding=15,
                        border=ft.border.all(2, ft.Colors.RED_200),
                        border_radius=8,
                        bgcolor=ft.Colors.RED_50
                    ),
                    ft.Container(height=12),
                    ft.Container(
                        content=ft.Column([
                            ft.Row([
                                CustomIcon.create(CustomIcon.CALENDAR, size=16),
                                ft.Text(f"{ngay_str} ({thu_str})", size=13, color=ft.Colors.GREY_700),
                            ], spacing=8),
                            ft.Row([
                                CustomIcon.create(ca_icon, size=16),
                                ft.Text(f"Ca {ca_truc}", size=13, color=ft.Colors.GREY_700),
                            ], spacing=8),
                            ft.Row([
                                CustomIcon.create(CustomIcon.PERSON, size=16),
                                ft.Text(lich_info.get('ho_ten', ''), size=13, color=ft.Colors.GREY_700),
                            ], spacing=8),
                        ], spacing=8),
                        padding=12,
                        bgcolor=ft.Colors.GREY_50,
                        border_radius=8,
                    ),
                ], spacing=0, tight=True)
            else:
                content = ft.Column([
                    ft.Container(
                        content=ft.Row([
                            CustomIcon.create(CustomIcon.DELETE_FOREVER, size=48),
                            ft.Column([
                                ft.Text("Bạn có chắc chắn muốn xóa lịch trực này?", size=14, weight=ft.FontWeight.W_500),
                                ft.Text("Hành động này không thể hoàn tác!", size=12, color=ft.Colors.RED_600, italic=True),
                            ], spacing=4, expand=True)
                        ], spacing=15),
                        padding=15,
                        border=ft.border.all(2, ft.Colors.RED_200),
                        border_radius=8,
                        bgcolor=ft.Colors.RED_50
                    ),
                ], spacing=0, tight=True)
            
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
                    content=content,
                ),
                actions=[cancel_btn, delete_btn],
                bgcolor=ft.Colors.WHITE,
                content_padding=24
            )
            
            show_dialog_safe(dialog)

        def open_create_lich_dialog(e):
            dialog_container = ft.Container()
            dialog_message_manager = MessageManager(page, dialog_container)

            # ==== Fetch cán bộ ====
            can_bo_options = []
            can_bo_map = {}
            try:
                can_bo_list = fetch_can_bo_bvp_bch(page_size=1000)
                for cb in can_bo_list:
                    can_bo_id = str(cb["id"])
                    can_bo_options.append(
                        ft.dropdown.Option(key=can_bo_id, text=cb["ho_ten"])
                    )
                    can_bo_map[can_bo_id] = cb
            except Exception as ex:
                pass

            # ==== State cho date picker ====
            selected_date = datetime.now().date()
            
            # ==== Form fields ====
            ngay_truc_display = ft.TextField(
                label="Ngày trực *",
                value=selected_date.strftime("%d/%m/%Y"),
                read_only=True,
                border_color=ft.Colors.BLUE_400,
                focused_border_color=ft.Colors.BLUE_700,
                prefix=CustomIcon.create(CustomIcon.CALENDAR, size=16),
            )
            
            def on_date_selected(e):
                nonlocal selected_date
                if date_picker.value:
                    selected_date = date_picker.value
                    ngay_truc_display.value = selected_date.strftime("%d/%m/%Y")
                    page.update()
            
            def on_date_dismiss(e):
                # Đóng date picker
                pass
            
            date_picker = ft.DatePicker(
                first_date=datetime(2024, 1, 1),
                last_date=datetime(2030, 12, 31),
                on_change=on_date_selected,
                on_dismiss=on_date_dismiss,
            )
            
            def open_date_picker(e):
                page.overlay.append(date_picker)
                date_picker.open = True
                page.update()
            
            ngay_truc_container = ft.Row(
                [
                    ft.Container(
                        content=ngay_truc_display,
                        expand=True,
                    ),
                    ft.Container(
                        content=CustomIcon.create(CustomIcon.EDIT_CALENDAR, size=18),
                        tooltip="Chọn ngày",
                        on_click=open_date_picker,
                        padding=8,
                        border_radius=6,
                        ink=True,
                    ),
                ],
                spacing=8,
                vertical_alignment=ft.CrossAxisAlignment.END,
            )
            
            fields = {
                "ca_truc": ft.Dropdown(
                    label="Ca trực *",
                    value="Sáng",
                    border_color=ft.Colors.BLUE_400,
                    focused_border_color=ft.Colors.BLUE_700,
                    options=[
                        ft.dropdown.Option("Sáng"),
                        ft.dropdown.Option("Chiều"),
                    ],
                ),
                "can_bo_id": ft.Dropdown(
                    label="Chọn cán bộ",
                    hint_text="Chọn từ danh sách hoặc nhập thủ công",
                    options=can_bo_options,
                    border_color=ft.Colors.BLUE_400,
                    focused_border_color=ft.Colors.BLUE_700,
                ),
                "ho_ten": ft.TextField(
                    label="Họ tên *",
                    hint_text="Tự động điền khi chọn cán bộ",
                    border_color=ft.Colors.BLUE_400,
                    focused_border_color=ft.Colors.BLUE_700,
                ),
                "sdt": ft.TextField(
                    label="SĐT",
                    hint_text="Tự động điền khi chọn cán bộ",
                    border_color=ft.Colors.BLUE_400,
                    focused_border_color=ft.Colors.BLUE_700,
                ),
                "trang_thai": ft.Dropdown(
                    label="Trạng thái",
                    value="Đã đăng ký",
                    border_color=ft.Colors.BLUE_400,
                    focused_border_color=ft.Colors.BLUE_700,
                    options=[
                        ft.dropdown.Option("Đã đăng ký"),
                        ft.dropdown.Option("Đã trực"),
                        ft.dropdown.Option("Vắng"),
                    ],
                ),
                "ghi_chu": ft.TextField(
                    label="Ghi chú",
                    multiline=True,
                    min_lines=2,
                    max_lines=4,
                    border_color=ft.Colors.BLUE_400,
                    focused_border_color=ft.Colors.BLUE_700,
                ),
            }

            # ✅ Auto-fill và disable fields khi chọn cán bộ
            def on_can_bo_change(e):
                if e.control.value:
                    cb = can_bo_map.get(e.control.value)
                    if cb:
                        fields["ho_ten"].value = cb.get("ho_ten", "")
                        fields["ho_ten"].disabled = True
                        fields["sdt"].value = cb.get("sdt", "") or ""
                        fields["sdt"].disabled = True
                else:
                    # Bỏ chọn -> enable lại
                    fields["ho_ten"].disabled = False
                    fields["sdt"].disabled = False
                
                page.update()
            
            fields["can_bo_id"].on_change = on_can_bo_change

            # ==== Close handler (định nghĩa trước để buttons có thể dùng) ====
            def handle_cancel(e):
                """Đóng dialog - simplified version"""
                try:
                    if state["active_dialog"]:
                        state["active_dialog"].open = False
                        state["active_dialog"] = None
                    page.update()
                except Exception as ex:
                    pass
                    try:
                        page.update()
                    except:
                        pass
            
            cancel_btn = ft.TextButton(
                content=ft.Text("Hủy", size=14),
                on_click=handle_cancel,
                style=ft.ButtonStyle(
                    color=ft.Colors.GREY_700,
                    overlay_color=ft.Colors.GREY_200,
                ),
            )

            submit_btn = ft.ElevatedButton(
                content=ft.Row([
                    CustomIcon.create(CustomIcon.ADD, size=16),
                    ft.Text("Thêm", size=14, weight=ft.FontWeight.W_500)
                ], spacing=6, tight=True),
                on_click=None,  # Sẽ gán sau
                bgcolor=ft.Colors.BLUE_600,
                color=ft.Colors.WHITE,
                style=ft.ButtonStyle(
                    shape=ft.RoundedRectangleBorder(radius=8),
                    elevation=2,
                ),
                height=42,
            )

            async def submit(ev):
                submit_btn.disabled = True
                cancel_btn.disabled = True
                
                submit_btn.content = ft.Row([
                    ft.ProgressRing(width=16, height=16, stroke_width=2, color=ft.Colors.WHITE),
                    ft.Text("Đang thêm...", size=14)
                ], spacing=8, tight=True)
                page.update()

                try:
                    payload = {}

                    payload["ngay_truc"] = selected_date.isoformat()
                    payload["ca_truc"] = fields["ca_truc"].value
                    
                    if not payload["ca_truc"]:
                        raise ValueError("Thiếu ca trực")

                    can_bo_id = fields["can_bo_id"].value
                    ho_ten_input = fields["ho_ten"].value.strip() if fields["ho_ten"].value else ""
                    
                    if can_bo_id:
                        payload["can_bo_id"] = can_bo_id
                        cb_info = can_bo_map.get(can_bo_id)
                        payload["ho_ten"] = cb_info.get("ho_ten", "") if cb_info else ho_ten_input
                        
                        if cb_info and cb_info.get("sdt"):
                            payload["sdt"] = cb_info.get("sdt")
                    elif ho_ten_input:
                        payload["ho_ten"] = ho_ten_input
                    else:
                        raise ValueError("Phải chọn cán bộ HOẶC nhập họ tên")

                    if fields["sdt"].value and fields["sdt"].value.strip() and not can_bo_id:
                        payload["sdt"] = fields["sdt"].value.strip()
                    
                    payload["trang_thai"] = fields["trang_thai"].value
                    
                    if fields["ghi_chu"].value and fields["ghi_chu"].value.strip():
                        payload["ghi_chu"] = fields["ghi_chu"].value.strip()

                    create_lich_truc(payload)

                    close_dialog_safe()
                    message_manager.success("Đã thêm lịch trực")
                    
                    if state["view_mode"] == "list":
                        await load_data_async()
                    else:
                        await load_week_view()

                except Exception as ex:
                    submit_btn.disabled = False
                    cancel_btn.disabled = False
                    submit_btn.content = ft.Row([
                        CustomIcon.create(CustomIcon.ADD, size=16),
                        ft.Text("Thêm", size=14, weight=ft.FontWeight.W_500)
                    ], spacing=6, tight=True)
                    dialog_message_manager.error(str(ex))
            
            submit_btn.on_click = lambda e: page.run_task(submit, e)

            # ==== Dialog ====
            content_container = ft.Container(
                width=500,
                content=ft.Column([
                    ft.Container(
                        content=ft.Row([
                            ft.Container(
                                content=CustomIcon.create(CustomIcon.ADD, size=24),
                                padding=10,
                                bgcolor=ft.Colors.GREEN_50,
                                border_radius=50,
                                border=ft.border.all(1, ft.Colors.GREEN_100)
                            ),
                            ft.Column([
                                ft.Text("Thêm lịch trực mới", size=16, weight=ft.FontWeight.BOLD, color=ft.Colors.GREEN_900),
                                ft.Text("Nhập thông tin ca trực", size=12, color=ft.Colors.GREY_700),
                            ], spacing=2)
                        ], spacing=10),
                        padding=10,
                        border=ft.border.all(1, ft.Colors.GREEN_100),
                        border_radius=8,
                        bgcolor=ft.Colors.GREEN_50
                    ),
                    ft.Divider(height=10, color=ft.Colors.TRANSPARENT),
                    ngay_truc_container,
                    *list(fields.values())
                ], spacing=12, scroll=ft.ScrollMode.AUTO, height=400),
            )
            
            dialog_container.content = ft.Stack([content_container])
            
            dialog = ft.AlertDialog(
                modal=True,
                title=ft.Row([
                    CustomIcon.create(CustomIcon.ADD, size=24),
                    ft.Text("Thêm lịch trực mới", weight=ft.FontWeight.BOLD)
                ], spacing=10),
                content=dialog_container,
                actions=[cancel_btn, submit_btn],
                bgcolor=ft.Colors.WHITE,
                content_padding=24
            )
            
            # ✅ Set dialog vào state TRƯỚC khi show
            state["active_dialog"] = dialog
            
            # Show dialog
            page.overlay.append(dialog)
            dialog.open = True
            page.update()

        # ===================== DATA LOADING =====================
        async def load_data_async():
            if state["is_loading"]:
                return
            
            state["is_loading"] = True
            loading_indicator.visible = True
            page.update()
            
            try:
                filters = {
                    "ca_truc": state["filter_ca"],
                    "trang_thai": state["filter_trang_thai"],
                    "tu_ngay": state["tu_ngay"],
                    "den_ngay": state["den_ngay"],
                }
                
                total = count_lich_truc(**filters)
                lich_truc = fetch_lich_truc(
                    page=state["page_index"],
                    page_size=PAGE_SIZE,
                    **filters
                )
                
                state["total_records"] = total
                state["lich_truc"] = lich_truc
                state["is_loading"] = False
                loading_indicator.visible = False
                
                table.rows.clear()
                for lt in lich_truc:
                    table.rows.append(build_row(lt))
                
                update_pagination()
                selected_count_text.value = f"Đã chọn: {len(state['selected_ids'])}"
                page.update()
            
            except Exception as ex:
                pagination_text.value = f"⚠️ Lỗi: {str(ex)}"
                state["is_loading"] = False
                loading_indicator.visible = False
                page.update()
        
        async def load_week_view():
            if state["is_loading"]:
                return
            
            state["is_loading"] = True
            loading_indicator.visible = True
            page.update()
            
            try:
                monday, sunday = get_week_range(state["current_week_offset"])
                
                lich_truc = fetch_lich_truc(
                    page=1,
                    page_size=200,
                    tu_ngay=monday.isoformat(),
                    den_ngay=sunday.isoformat(),
                )
                
                state["is_loading"] = False
                loading_indicator.visible = False
                
                week_content = build_week_view(lich_truc, monday, sunday)
                week_view_container.content = week_content
                
                week_view_container.visible = True
                list_view_container.visible = False
                
                page.update()
            
            except Exception as ex:
                state["is_loading"] = False
                loading_indicator.visible = False
                message_manager.error(f"⚠️ Lỗi: {str(ex)}")
        
        # ===================== WEEK VIEW BUILDER =====================
        def build_week_view(lich_truc_list: list, monday, sunday):
            """✅ IMPROVED: Xây dựng giao diện xem theo tuần - Full Width & Better UX"""
            
            # Tạo dict để group theo ngày và ca
            week_data = {}
            for i in range(7):
                date = monday + timedelta(days=i)
                week_data[date.isoformat()] = {"Sáng": [], "Chiều": []}
            
            # Phân loại data
            for lt in lich_truc_list:
                ngay = str(lt["ngay_truc"])
                ca = lt.get("ca_truc", "")
                if ngay in week_data and ca in week_data[ngay]:
                    week_data[ngay][ca].append(lt)
            
            # Build columns cho 7 ngày
            day_columns = []
            weekday_names = ["Thứ 2", "Thứ 3", "Thứ 4", "Thứ 5", "Thứ 6", "Thứ 7", "Chủ nhật"]
            
            for i in range(7):
                date = monday + timedelta(days=i)
                date_str = date.isoformat()
                is_today = date == datetime.now().date()
                
                # ✅ Header ngày với highlight cho ngày hiện tại
                header = ft.Container(
                    content=ft.Column([
                        ft.Text(
                            weekday_names[i], 
                            size=14, 
                            weight=ft.FontWeight.BOLD,
                            color=ft.Colors.WHITE if is_today else ft.Colors.GREY_900
                        ),
                        ft.Text(
                            date.strftime("%d/%m"), 
                            size=12, 
                            color=ft.Colors.WHITE if is_today else ft.Colors.GREY_700
                        ),
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=2),
                    bgcolor=ft.Colors.BLUE_700 if is_today else ft.Colors.BLUE_50,
                    padding=10,
                    border_radius=8,
                )
                
                # ✅ Ca Sáng - Full width text
                sang_items = []
                for lt in week_data[date_str]["Sáng"]:
                    sang_items.append(
                        ft.Container(
                            content=ft.Column([
                                ft.Text(
                                    lt.get("ho_ten", ""), 
                                    size=12, 
                                    weight=ft.FontWeight.W_500,
                                    overflow=ft.TextOverflow.ELLIPSIS,
                                    max_lines=2,
                                ),
                                ft.Text(
                                    lt.get("sdt", ""), 
                                    size=10, 
                                    color=ft.Colors.GREY_600,
                                    overflow=ft.TextOverflow.ELLIPSIS,
                                ),
                                ft.Container(
                                    content=ft.Text(
                                        lt.get("trang_thai", ""), 
                                        size=9,
                                        weight=ft.FontWeight.W_500,
                                        color=ft.Colors.WHITE,
                                    ),
                                    bgcolor=ft.Colors.GREEN_600 if lt.get("trang_thai") == "Đã trực" else ft.Colors.BLUE_600,
                                    padding=ft.padding.symmetric(horizontal=6, vertical=2),
                                    border_radius=4,
                                ),
                            ], spacing=4, tight=True, horizontal_alignment=ft.CrossAxisAlignment.START),
                            bgcolor=ft.Colors.YELLOW_50,
                            padding=10,
                            border_radius=6,
                            border=ft.border.all(1, ft.Colors.YELLOW_300),
                            expand=True,  # ✅ Full width
                        )
                    )
                
                # ✅ Ca Chiều - Full width text
                chieu_items = []
                for lt in week_data[date_str]["Chiều"]:
                    chieu_items.append(
                        ft.Container(
                            content=ft.Column([
                                ft.Text(
                                    lt.get("ho_ten", ""), 
                                    size=12, 
                                    weight=ft.FontWeight.W_500,
                                    overflow=ft.TextOverflow.ELLIPSIS,
                                    max_lines=2,
                                ),
                                ft.Text(
                                    lt.get("sdt", ""), 
                                    size=10, 
                                    color=ft.Colors.GREY_600,
                                    overflow=ft.TextOverflow.ELLIPSIS,
                                ),
                                ft.Container(
                                    content=ft.Text(
                                        lt.get("trang_thai", ""), 
                                        size=9,
                                        weight=ft.FontWeight.W_500,
                                        color=ft.Colors.WHITE,
                                    ),
                                    bgcolor=ft.Colors.GREEN_600 if lt.get("trang_thai") == "Đã trực" else ft.Colors.BLUE_600,
                                    padding=ft.padding.symmetric(horizontal=6, vertical=2),
                                    border_radius=4,
                                ),
                            ], spacing=4, tight=True, horizontal_alignment=ft.CrossAxisAlignment.START),
                            bgcolor=ft.Colors.ORANGE_50,
                            padding=10,
                            border_radius=6,
                            border=ft.border.all(1, ft.Colors.ORANGE_300),
                            expand=True,  # ✅ Full width
                        )
                    )
                
                # ✅ Column cho ngày này - Expand để chia đều
                day_col = ft.Container(
                    content=ft.Column([
                        header,
                        ft.Container(height=10),
                        
                        # Ca Sáng section
                        ft.Row([
                            CustomIcon.create(CustomIcon.SUNRISE, size=16),
                            ft.Text("Sáng", size=12, weight=ft.FontWeight.BOLD, color=ft.Colors.ORANGE_900),
                        ], spacing=6),
                        ft.Container(height=4),
                        ft.Column(
                            sang_items if sang_items else [
                                ft.Container(
                                    content=ft.Text("---", size=11, color=ft.Colors.GREY_400),
                                    padding=10,
                                    alignment=ft.Alignment.CENTER,
                                    bgcolor=ft.Colors.GREY_100,
                                    border_radius=6,
                                )
                            ], 
                            spacing=8,
                            expand=False,
                        ),
                        
                        ft.Container(height=12),
                        
                        # Ca Chiều section
                        ft.Row([
                            CustomIcon.create(CustomIcon.SUNSET, size=16),
                            ft.Text("Chiều", size=12, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_900),
                        ], spacing=6),
                        ft.Container(height=4),
                        ft.Column(
                            chieu_items if chieu_items else [
                                ft.Container(
                                    content=ft.Text("---", size=11, color=ft.Colors.GREY_400),
                                    padding=10,
                                    alignment=ft.Alignment.CENTER,
                                    bgcolor=ft.Colors.GREY_100,
                                    border_radius=6,
                                )
                            ], 
                            spacing=8,
                            expand=False,
                        ),
                    ], spacing=4, scroll=ft.ScrollMode.AUTO),
                    padding=12,
                    bgcolor=ft.Colors.WHITE,
                    border=ft.border.all(2, ft.Colors.BLUE_700 if is_today else ft.Colors.GREY_300),
                    border_radius=10,
                    expand=True,  # ✅ Chia đều cho 7 cột
                    shadow=ft.BoxShadow(
                        spread_radius=1,
                        blur_radius=4,
                        color=ft.Colors.with_opacity(0.1, ft.Colors.BLACK),
                        offset=ft.Offset(0, 2),
                    ) if is_today else None,
                )
                
                day_columns.append(day_col)
            
            # ✅ Week navigation with better styling
            week_title = ft.Text(
                f"📅 Tuần: {monday.strftime('%d/%m/%Y')} - {sunday.strftime('%d/%m/%Y')}",
                size=16,
                weight=ft.FontWeight.BOLD,
                color=ft.Colors.GREY_900,
            )
            
            nav_buttons = [
                ft.Container(
                    content=CustomIcon.create(CustomIcon.CHEVRON_LEFT, 20),
                    on_click=lambda e: prev_week(),
                    tooltip="Tuần trước",
                    padding=8,
                    border_radius=8,
                    bgcolor=ft.Colors.BLUE_50,
                    ink=True,
                ),
                week_title,
                ft.Container(
                    content=CustomIcon.create(CustomIcon.CHEVRON_RIGHT, 20),
                    on_click=lambda e: next_week(),
                    tooltip="Tuần sau",
                    padding=8,
                    border_radius=8,
                    bgcolor=ft.Colors.BLUE_50,
                    ink=True,
                ),
                ft.Container(
                    content=CustomIcon.create(CustomIcon.TODAY, 20),
                    on_click=lambda e: go_to_current_week(),
                    tooltip="Về tuần hiện tại",
                    padding=8,
                    border_radius=8,
                    bgcolor=ft.Colors.GREEN_50,
                    ink=True,
                ),
            ]
            
            return ft.Column([
                # Navigation bar
                ft.Container(
                    content=ft.Row(
                        nav_buttons,
                        alignment=ft.MainAxisAlignment.CENTER, 
                        spacing=12
                    ),
                    padding=12,
                    bgcolor=ft.Colors.WHITE,
                    border_radius=10,
                    border=ft.border.all(1, ft.Colors.GREY_300),
                ),
                
                ft.Container(height=10),
                
                # ✅ Week calendar - Row expand để các cột chia đều
                ft.Row(
                    day_columns,
                    spacing=12,
                    expand=True,  # ✅ Cho phép row expand
                    alignment=ft.MainAxisAlignment.START,
                ),
            ], spacing=0, expand=True)
        
        def prev_week():
            state["current_week_offset"] -= 1
            load_week_view()
        
        def next_week():
            state["current_week_offset"] += 1
            load_week_view()
        
        # ===================== SELECTION =====================
        def toggle_selection(id: str, selected: bool):
            if selected:
                state["selected_ids"].add(id)
            else:
                state["selected_ids"].discard(id)
            
            select_all_checkbox.value = (
                len(state["selected_ids"]) == len(state["lich_truc"]) 
                and len(state["lich_truc"]) > 0
            )
            
            selected_count_text.value = f"Đã chọn: {len(state['selected_ids'])}"
            page.update()
        
        def toggle_select_all(select_all: bool):
            if select_all:
                for lt in state["lich_truc"]:
                    state["selected_ids"].add(lt["id"])
            else:
                for lt in state["lich_truc"]:
                    state["selected_ids"].discard(lt["id"])
            
            table.rows.clear()
            for lt in state["lich_truc"]:
                table.rows.append(build_row(lt))
            
            selected_count_text.value = f"Đã chọn: {len(state['selected_ids'])}"
            page.update()
        
        # ===================== FILTERS =====================
        def on_filter_ca(e):
            state["filter_ca"] = e.control.value if e.control.value else ""
            state["page_index"] = 1
            if state["view_mode"] == "list":
                page.run_task(load_data_async)
            else:
                page.run_task(load_week_view)
        
        def on_filter_trang_thai(e):
            state["filter_trang_thai"] = e.control.value if e.control.value else ""
            state["page_index"] = 1
            if state["view_mode"] == "list":
                page.run_task(load_data_async)
            else:
                page.run_task(load_week_view)
        
        def update_pagination():
            total_pages = max(1, (state["total_records"] + PAGE_SIZE - 1) // PAGE_SIZE)
            pagination_text.value = f"Trang {state['page_index']} / {total_pages} – Tổng {state['total_records']} ca trực"
        
        def prev_page(e):
            if state["page_index"] > 1:
                state["page_index"] -= 1
                page.run_task(load_data_async)
        
        def next_page(e):
            if state["page_index"] * PAGE_SIZE < state["total_records"]:
                state["page_index"] += 1
                page.run_task(load_data_async)
        
        def go_to_current_week():
            state["current_week_offset"] = 0
            page.run_task(load_week_view)
        
        def toggle_view_mode(e):
            if state["view_mode"] == "list":
                state["view_mode"] = "week"
                page.run_task(load_week_view)
            else:
                state["view_mode"] = "list"
                page.run_task(load_data_async)
            
            view_toggle_btn.text = "📋 Xem danh sách" if state["view_mode"] == "week" else "📅 Xem theo tuần"
            
            list_view_container.visible = (state["view_mode"] == "list")
            week_view_container.visible = (state["view_mode"] == "week")
            page.update()
        
        # ===================== TABLE ROW BUILDER =====================
        def build_row(lt: dict):
            """Xây dựng một dòng trong bảng list view"""
            checkbox = ft.Checkbox(
                value=lt["id"] in state["selected_ids"],
                on_change=lambda e, id=lt["id"]: toggle_selection(id, e.control.value)
            )
            
            # Parse ngày
            try:
                ngay_obj = datetime.fromisoformat(str(lt["ngay_truc"]))
                ngay_str = ngay_obj.strftime("%d/%m")
                thu_str = ["T2", "T3", "T4", "T5", "T6", "T7", "CN"][ngay_obj.weekday()]
            except:
                ngay_str = str(lt["ngay_truc"])
                thu_str = ""
            
            edit_btn = ft.Container(
                content=CustomIcon.create(CustomIcon.EDIT, size=18),
                on_click=lambda e, lich=lt: open_edit_lich_dialog(lich),
                tooltip="Sửa lịch trực",
                padding=8,
                border_radius=4,
                ink=True,
            )
            
            # Nút xóa (chỉ admin)
            action_buttons = [checkbox, edit_btn]
            if is_admin(role):
                delete_btn = ft.Container(
                    content=CustomIcon.create(CustomIcon.DELETE, size=18),
                    on_click=lambda e, lich_id=lt["id"], info=lt: delete_lich_truc_record(lich_id, info),
                    tooltip="Xóa lịch trực",
                    padding=8,
                    border_radius=4,
                    ink=True,
                )
                action_buttons.append(delete_btn)
            
            return ft.DataRow(
                cells=[
                    ft.DataCell(ft.Text(ngay_str)),
                    ft.DataCell(ft.Text(thu_str)),
                    ft.DataCell(ft.Text(lt.get("ca_truc", ""))),
                    ft.DataCell(ft.Text(lt.get("ho_ten", ""))),
                    ft.DataCell(ft.Text(lt.get("sdt", "") or "")),
                    ft.DataCell(ft.Text(lt.get("trang_thai", ""))),
                    ft.DataCell(ft.Text(lt.get("ghi_chu", "") or "")),
                    ft.DataCell(ft.Row(action_buttons, spacing=4)),
                ],
            )
        
        def open_edit_lich_dialog(lich: dict):
            dialog_container = ft.Container()
            dialog_message_manager = MessageManager(page, dialog_container)
            
            fields = {
                "ho_ten": ft.TextField(label="Họ tên", value=lich.get("ho_ten", "")),
                "sdt": ft.TextField(label="SĐT", value=lich.get("sdt", "") or ""),
                "trang_thai": ft.Dropdown(
                    label="Trạng thái",
                    value=lich.get("trang_thai", "Đã đăng ký"),
                    options=[
                        ft.dropdown.Option("Đã đăng ký"),
                        ft.dropdown.Option("Đã trực"),
                        ft.dropdown.Option("Vắng"),
                    ],
                ),
                "ghi_chu": ft.TextField(
                    label="Ghi chú",
                    value=lich.get("ghi_chu", "") or "",
                    multiline=True,
                    min_lines=2,
                    max_lines=4,
                ),
            }
            
            async def submit(e):
                submit_btn.disabled = True
                cancel_btn.disabled = True
                page.update()
                
                try:
                    payload = {k: v.value for k, v in fields.items() if v.value}
                    update_lich_truc(lich["id"], payload)
                    
                    close_dialog_safe()
                    message_manager.success("Đã cập nhật lịch trực")
                    
                    if state["view_mode"] == "list":
                        await load_data_async()
                    else:
                        await load_week_view()
                
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
            
            try:
                ngay_obj = datetime.fromisoformat(str(lich.get("ngay_truc", "")))
                ngay_str = ngay_obj.strftime("%d/%m/%Y")
            except:
                ngay_str = str(lich.get("ngay_truc", ""))
            
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
                                border=ft.border.all(1, ft.Colors.BLUE_100)
                            ),
                            ft.Column([
                                ft.Text(lich.get('ho_ten', 'Lịch trực'), size=16, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_900),
                                ft.Text(f"Ngày: {ngay_str}", size=12, color=ft.Colors.GREY_700),
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
                    ft.Text(f"Sửa lịch trực", weight=ft.FontWeight.BOLD)
                ], spacing=10),
                content=dialog_container,
                actions=[cancel_btn, submit_btn],
                bgcolor=ft.Colors.WHITE,
                content_padding=24
            )
            
            show_dialog_safe(dialog)
        
        # ===================== BULK EDIT (thay thế bulk_confirm) =====================
        def bulk_edit_action(e):
            if not state["selected_ids"]:
                message_manager.warning("Chưa chọn ca trực")
                return
            
            dialog_container = ft.Container()
            dialog_message_manager = MessageManager(page, dialog_container)
            
            edit_fields = {
                "ngay_truc": ft.TextField(
                    label="Ngày trực",
                    hint_text="YYYY-MM-DD (để trống = không đổi)",
                ),
                "ca_truc": ft.Dropdown(
                    label="Ca trực",
                    hint_text="Chọn để thay đổi (để trống = không đổi)",
                    options=[
                        ft.dropdown.Option("Sáng"),
                        ft.dropdown.Option("Chiều"),
                    ],
                ),
                "trang_thai": ft.Dropdown(
                    label="Trạng thái",
                    hint_text="Chọn để thay đổi (để trống = không đổi)",
                    options=[
                        ft.dropdown.Option("Đã đăng ký"),
                        ft.dropdown.Option("Đã trực"),
                        ft.dropdown.Option("Vắng"),
                    ],
                ),
            }
            
            async def do_bulk_edit(confirm_e):
                submit_btn.disabled = True
                cancel_btn.disabled = True
                page.update()
                
                payload = {}
                
                if edit_fields["ngay_truc"].value and edit_fields["ngay_truc"].value.strip():
                    ngay_value = edit_fields["ngay_truc"].value.strip()
                    try:
                        datetime.strptime(ngay_value, "%Y-%m-%d")
                        payload["ngay_truc"] = ngay_value
                    except:
                        submit_btn.disabled = False
                        cancel_btn.disabled = False
                        dialog_message_manager.error("Ngày không đúng định dạng YYYY-MM-DD")
                        return
                
                if edit_fields["ca_truc"].value:
                    payload["ca_truc"] = edit_fields["ca_truc"].value
                if edit_fields["trang_thai"].value:
                    payload["trang_thai"] = edit_fields["trang_thai"].value
                
                if not payload:
                    submit_btn.disabled = False
                    cancel_btn.disabled = False
                    dialog_message_manager.warning("Bạn chưa chọn trường nào để sửa")
                    return
                
                try:
                    from core.supabase_client import supabase
                    
                    count = 0
                    errors = []
                    for lich_id in state["selected_ids"]:
                        try:
                            supabase.table('lich_truc').update(payload).eq('id', lich_id).execute()
                            count += 1
                        except Exception as update_ex:
                            errors.append(f"ID {lich_id}: {str(update_ex)}")
                    
                    state["selected_ids"].clear()
                    select_all_checkbox.value = False
                    close_dialog_safe()
                    
                    if errors:
                        message_manager.warning(f"Cập nhật {count}/{count + len(errors)} ca trực, {len(errors)} lỗi")
                    else:
                        message_manager.success(f"Đã cập nhật {count} ca trực")
                    
                    if state["view_mode"] == "list":
                        await load_data_async()
                    else:
                        await load_week_view()
                
                except Exception as ex:
                    submit_btn.disabled = False
                    cancel_btn.disabled = False
                    dialog_message_manager.error(f"Lỗi: {ex}")
            
            cancel_btn = ft.TextButton(
                "Hủy bỏ",
                on_click=lambda _: close_dialog_safe(),
                style=ft.ButtonStyle(color=ft.Colors.GREY_600)
            )
            submit_btn = ft.ElevatedButton(
                "Cập nhật",
                on_click=lambda e: page.run_task(do_bulk_edit, e),
                bgcolor=ft.Colors.BLUE_600,
                color=ft.Colors.WHITE,
                elevation=0
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
                                border=ft.border.all(1, ft.Colors.BLUE_100)
                            ),
                            ft.Column([
                                ft.Text(f"Đang chọn {len(state['selected_ids'])} ca trực", weight=ft.FontWeight.BOLD, size=15, color=ft.Colors.BLUE_900),
                                ft.Text("Chọn các trường muốn cập nhật đồng loạt.", size=13, color=ft.Colors.GREY_700),
                            ], spacing=2, tight=True)
                        ], spacing=12),
                        padding=12,
                        bgcolor=ft.Colors.BLUE_50,
                        border=ft.border.all(1, ft.Colors.BLUE_200),
                        border_radius=8,
                    ),
                    ft.Divider(height=10, color=ft.Colors.TRANSPARENT),
                    edit_fields["ngay_truc"],
                    edit_fields["ca_truc"],
                    edit_fields["trang_thai"],
                    ft.Container(
                        content=ft.Row([
                            CustomIcon.create(CustomIcon.INFO, size=16),
                            ft.Text(
                                "Các trường để trống sẽ không bị thay đổi",
                                size=12,
                                color=ft.Colors.BLUE_700,
                                italic=True
                            ),
                        ], spacing=6, tight=True),
                        padding=10,
                        bgcolor=ft.Colors.BLUE_50,
                        border_radius=8,
                        border=ft.border.all(1, ft.Colors.BLUE_100),
                    ),
                ], spacing=12, tight=True),
            )
            
            dialog_container.content = ft.Stack([content])
            
            confirm_dialog = ft.AlertDialog(
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
            
            show_dialog_safe(confirm_dialog)
        
        # ===================== UI LAYOUT (phần còn thiếu) =====================
        # Filter ca dropdown
        filter_ca_dropdown = ft.Dropdown(
            label="Lọc ca",
            width=150,
            options=[
                ft.dropdown.Option("Sáng"),
                ft.dropdown.Option("Chiều"),
            ],
        )
        filter_ca_dropdown.on_change = on_filter_ca
        
        # Footer với pagination
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

        # View toggle button
        view_toggle_btn = ft.ElevatedButton(
            content=ft.Row(
                [
                    CustomIcon.create(CustomIcon.VIEW_WEEK, size=20),
                    ft.Text("Xem theo tuần"),
                ],
                spacing=8,
                alignment=ft.MainAxisAlignment.CENTER,
            ),
            on_click=toggle_view_mode,
        )

        
        # Cập nhật filter dropdown với 3 trạng thái
        filter_trang_thai_dropdown = ft.Dropdown(
            label="Lọc trạng thái",
            width=180,
            options=[
                ft.dropdown.Option("Đã đăng ký"),
                ft.dropdown.Option("Đã trực"),
                ft.dropdown.Option("Vắng"),
            ],
        )
        filter_trang_thai_dropdown.on_change = on_filter_trang_thai
        
        # Buttons với view toggle
        buttons = []
        if is_admin(role):
            buttons.append(
                elevated_button("Thêm lịch trực", CustomIcon.ADD, on_click=open_create_lich_dialog)
            )
        
        buttons.extend([
            elevated_button("Đồng bộ Google Sheet", CustomIcon.UPLOAD, on_click=handle_sync_sheet),
            elevated_button("Sửa hàng loạt", CustomIcon.EDIT, on_click=bulk_edit_action),
        ])
        
        # Toolbar với view toggle button
        toolbar = ft.Column([
            ft.Row(
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                controls=[
                    ft.Row([filter_ca_dropdown, filter_trang_thai_dropdown, loading_indicator], spacing=8),
                    ft.Row(spacing=8, controls=[view_toggle_btn] + buttons),
                ],
            ),
            ft.Row([select_all_checkbox, selected_count_text], spacing=12),
        ], spacing=8)
        
        # List view container
        list_view_container = ft.Column(
            visible=True,
            expand=True,
            spacing=10,
            controls=[
                ft.Container(expand=True, content=ft.ListView(expand=True, controls=[table])),
                footer,
            ],
        )
        
        # Week view container
        week_view_container.visible = False
        week_view_container.expand = True
        
        # Main result với Stack (có loading overlay)
        result = ft.Stack([
            ft.Column(
                expand=True,
                spacing=10,
                controls=[
                    toolbar,
                    ft.Divider(height=1),
                    list_view_container,
                    week_view_container,
                ],
            ),
            loading_overlay,
        ], expand=True)
        
        async def _delayed_load():
            await asyncio.sleep(0.2)
            await load_data_async()
        
        page.run_task(_delayed_load)
        
        return result
    
    # ============================================================
    # SUB-TAB 3: THỐNG KÊ - ✅ Fixed Logic
    # ============================================================
    def ThongKeTab():
        """Sub-tab: Thống kê đơn giản - Theo dõi ai đã đi trực"""
        
        state = {
            "current_week_offset": 0,  # 0 = tuần hiện tại
            "week_stats": [],  # Danh sách ai đi trực trong tuần
            "is_loading": False,
            "sort_column": "loai_can_bo",  # loai_can_bo, chuc_vu, ho_ten, so_buoi
            "sort_order": "asc",  # asc, desc
        }
        
        message_container = ft.Container()
        message_manager = MessageManager(page, message_container)
        
        # ===================== HELPER: GET WEEK RANGE =====================
        def get_week_range(offset: int = 0):
            """Lấy ngày bắt đầu và kết thúc của tuần (Thứ 2 -> Chủ nhật)"""
            today = datetime.now().date()
            days_since_monday = today.weekday()  # 0=Monday, 6=Sunday
            current_monday = today - timedelta(days=days_since_monday)
            
            target_monday = current_monday + timedelta(weeks=offset)
            target_sunday = target_monday + timedelta(days=6)
            
            return target_monday, target_sunday
        
        # ===================== OVERVIEW CARDS =====================
        def create_overview_card(title: str, count_text: str, total: int, icon_path: str, bg_color: str):
            """Tạo card tổng quan đơn giản"""
            return ft.Container(
                content=ft.Column([
                    ft.Row([
                        CustomIcon.create(icon_path, size=40),
                        ft.Column([
                            ft.Text(title, size=14, weight=ft.FontWeight.BOLD, color=ft.Colors.GREY_800),
                            ft.Text(f"Tổng: {total} người", size=11, color=ft.Colors.GREY_600),
                        ], spacing=2, expand=True),
                    ], spacing=12),
                    ft.Container(height=12),
                    ft.Text(count_text, size=32, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_700),
                ], spacing=8),
                bgcolor=bg_color,
                padding=20,
                border_radius=12,
                expand=True,
                border=ft.border.all(2, ft.Colors.BLUE_200),
            )
        
        card_bch_hoi = create_overview_card(
            "BCH Hội SV", "... / 20", 20, CustomIcon.BADGE, ft.Colors.BLUE_50
        )
        
        card_bch_doan = create_overview_card(
            "BCH Đoàn", "... / 9", 9, CustomIcon.PEOPLE, ft.Colors.GREEN_50
        )
        
        card_ban_vp = create_overview_card(
            "Ban Văn phòng", "... / 26", 26, CustomIcon.WORK, ft.Colors.ORANGE_50
        )
        
        # ===================== WEEKLY TABLE =====================
        table = ft.DataTable(
            columns=[
                ft.DataColumn(
                    ft.Text("Họ tên", weight=ft.FontWeight.BOLD, size=13),
                    on_sort=lambda e: handle_sort("ho_ten"),
                ),
                ft.DataColumn(
                    ft.Text("Đơn vị", weight=ft.FontWeight.BOLD, size=13),
                    on_sort=lambda e: handle_sort("loai_can_bo"),
                ),
                ft.DataColumn(
                    ft.Text("Chức danh", weight=ft.FontWeight.BOLD, size=13),
                    on_sort=lambda e: handle_sort("chuc_vu"),
                ),
                ft.DataColumn(
                    ft.Text("Số buổi", weight=ft.FontWeight.BOLD, size=13),
                    numeric=True,
                    on_sort=lambda e: handle_sort("so_buoi"),
                ),
            ],
            rows=[],
            column_spacing=20,
            data_row_min_height=50,
            heading_row_height=45,
            border=ft.border.all(1, ft.Colors.GREY_300),
            border_radius=8,
            sort_column_index=None,
            sort_ascending=True,
        )
        
        # Loading overlay
        loading_overlay = ft.Container(
            visible=False,
            bgcolor=ft.Colors.with_opacity(0.8, ft.Colors.WHITE),
            content=ft.Column(
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.ProgressRing(width=50, height=50, color=ft.Colors.BLUE_700),
                    ft.Container(height=12),
                    ft.Text("📊 Đang tải...", size=14, color=ft.Colors.BLUE_700),
                ],
            ),
            expand=True,
        )
        
        # ===================== SORT HANDLER =====================
        def handle_sort(column: str):
            """Xử lý sort khi click vào header"""
            if state["sort_column"] == column:
                # Toggle order
                state["sort_order"] = "desc" if state["sort_order"] == "asc" else "asc"
            else:
                # New column
                state["sort_column"] = column
                state["sort_order"] = "asc"
            
            # Update UI
            update_table_with_current_data()
        
        # ===================== LOAD DATA =====================
        def load_week_stats():
            """Load thống kê theo tuần - ✅ FIXED LOGIC"""
            if state["is_loading"]:
                return
            
            state["is_loading"] = True
            loading_overlay.visible = True
            page.update()
            
            async def _fetch():
                try:
                    monday, sunday = get_week_range(state["current_week_offset"])
                    
                    # ✅ 1. Fetch danh sách cán bộ (để lấy thông tin đơn vị, chức danh)
                    can_bo_list = fetch_can_bo_bvp_bch(page_size=1000)
                    can_bo_map = {}  # Map: normalized_name -> {ho_ten_display, roles[]}
                    
                    def normalize_name(name: str) -> str:
                        """Normalize tên: lowercase + strip spaces + remove extra spaces"""
                        import re
                        name = name.strip().lower()
                        # Remove multiple spaces
                        name = re.sub(r'\s+', ' ', name)
                        return name
                    
                    for cb in can_bo_list:
                        ho_ten = cb.get('ho_ten', '').strip()
                        if not ho_ten:
                            continue
                        
                        loai = cb.get('loai_can_bo', '')
                        chuc_vu = cb.get('chuc_vu', '')
                        
                        # ✅ LOGIC CỨNG DUY NHẤT: UV Ban Kiểm tra KHÔNG tính (skip)
                        if chuc_vu == 'UV Ban Kiểm tra':
                            continue
                        
                        # ✅ Normalize tên để group đúng người
                        normalized = normalize_name(ho_ten)
                        
                        # ✅ Lưu tên display (ưu tiên tên đầu tiên gặp)
                        if normalized not in can_bo_map:
                            can_bo_map[normalized] = {
                                'ho_ten_display': ho_ten,  # Tên gốc để hiển thị
                                'roles': []
                            }
                        
                        # ✅ Thêm role (loại + chức vụ)
                        can_bo_map[normalized]['roles'].append({
                            'loai_can_bo': loai,
                            'chuc_vu': chuc_vu,
                        })
                    
                    # ✅ 2. Fetch lịch trực trong tuần
                    lich_truc = fetch_lich_truc(
                        page=1,
                        page_size=200,
                        tu_ngay=monday.isoformat(),
                        den_ngay=sunday.isoformat(),
                    )
                    
                    # ✅ 3. Group by họ tên (normalized) và đếm số buổi
                    stats = {}  # normalized_name -> {ho_ten_display, so_buoi, loai_can_bo[], chuc_vu[]}
                    
                    for lt in lich_truc:
                        ho_ten = lt.get('ho_ten', '').strip()
                        if not ho_ten:
                            continue
                        
                        # ✅ Normalize để group đúng
                        normalized = normalize_name(ho_ten)
                        
                        if normalized not in stats:
                            stats[normalized] = {
                                'ho_ten_display': ho_ten,  # Dùng tên từ lịch trực
                                'so_buoi': 0,
                                'loai_can_bo': [],
                                'chuc_vu': [],
                            }
                        
                        stats[normalized]['so_buoi'] += 1
                    
                    # ✅ 4. Enrichment: Thêm thông tin đơn vị, chức danh từ can_bo_map
                    for normalized, stat in stats.items():
                        if normalized in can_bo_map:
                            cb_info = can_bo_map[normalized]
                            
                            # Update display name (ưu tiên từ database)
                            if cb_info['ho_ten_display']:
                                stat['ho_ten_display'] = cb_info['ho_ten_display']
                            
                            # ✅ THÊM TẤT CẢ CÁC ROLE (không filter gì cả)
                            for role in cb_info['roles']:
                                loai = role['loai_can_bo']
                                chuc_vu = role['chuc_vu']
                                
                                if loai and loai not in stat['loai_can_bo']:
                                    stat['loai_can_bo'].append(loai)
                                if chuc_vu and chuc_vu not in stat['chuc_vu']:
                                    stat['chuc_vu'].append(chuc_vu)
                    
                    # ✅ 5. Convert to list và sort
                    week_stats = list(stats.values())
                    
                    # ✅ 6. Tính tổng quan (cho overview cards)
                    bch_hoi_set = set()
                    bch_doan_set = set()
                    ban_vp_set = set()
                    
                    for normalized, stat in stats.items():
                        loai_list = stat['loai_can_bo']
                        
                        # ✅ Đếm theo từng loại riêng biệt (không filter)
                        if 'BCH Hội' in loai_list:
                            bch_hoi_set.add(normalized)
                        if 'BCH Đoàn' in loai_list:
                            bch_doan_set.add(normalized)
                        if 'Ban Văn phòng' in loai_list or 'CTV Ban Văn phòng' in loai_list:
                            ban_vp_set.add(normalized)
                    
                    overview = {
                        'bch_hoi': len(bch_hoi_set),
                        'bch_doan': len(bch_doan_set),
                        'ban_vp': len(ban_vp_set),
                    }
                    
                    state["week_stats"] = week_stats
                    state["is_loading"] = False
                    loading_overlay.visible = False
                    
                    # Update overview cards
                    card_bch_hoi.content.controls[2].value = f"{overview['bch_hoi']} / 20"
                    card_bch_doan.content.controls[2].value = f"{overview['bch_doan']} / 9"
                    card_ban_vp.content.controls[2].value = f"{overview['ban_vp']} / 26"
                    
                    # Update table
                    update_table_with_current_data()
                    
                    # Update week title
                    week_title.value = f"📅 Tuần: {monday.strftime('%d/%m/%Y')} - {sunday.strftime('%d/%m/%Y')}"
                    
                    page.update()
                
                except Exception as ex:
                    error_msg = str(ex)
                    state["is_loading"] = False
                    loading_overlay.visible = False
                    message_manager.error(f"❌ Lỗi: {error_msg}")
            
            page.run_task(_fetch)
        
        # ===================== UPDATE TABLE =====================
        def update_table_with_current_data():
            """Update bảng với data hiện tại và sort"""
            week_stats = state["week_stats"]
            
            if not week_stats:
                table.rows.clear()
                page.update()
                return
            
            # ✅ Sort data
            def get_sort_key(stat):
                """Tạo sort key theo logic ưu tiên"""
                # Mapping loại cán bộ -> priority
                loai_priority = {
                    "BCH Hội": 1,
                    "BCH Đoàn": 2,
                    "Ban Văn phòng": 3,
                    "CTV Ban Văn phòng": 4,
                }
                
                # Mapping chức danh -> priority
                chuc_vu_priority = {
                    # BCH Hội
                    "Phó Chủ tịch": 1,
                    "Phó chủ tịch, Trưởng Ban KT": 2,
                    "UV Ban Thư ký, Phó Ban KT": 3,
                    "UV Ban Thư ký": 4,
                    "Ủy viên": 5,
                    
                    # BCH Đoàn
                    "Bí thư": 7,
                    "Phó Bí thư": 8,
                    
                    # Ban Văn phòng
                    "Trưởng Ban": 11,
                    "Phó Ban": 12,
                    "Đội trưởng đội CTV": 13,
                    "Thành viên": 14,
                    "Cộng tác viên": 15,
                }
                
                if state["sort_column"] == "loai_can_bo":
                    # Sort theo loại (lấy loại có priority cao nhất)
                    loai_list = stat['loai_can_bo']
                    if loai_list:
                        min_priority = min(loai_priority.get(l, 999) for l in loai_list)
                        return min_priority
                    return 999
                
                elif state["sort_column"] == "chuc_vu":
                    # Sort theo chức vụ (lấy chức vụ có priority cao nhất)
                    chuc_vu_list = stat['chuc_vu']
                    if chuc_vu_list:
                        min_priority = min(chuc_vu_priority.get(cv, 999) for cv in chuc_vu_list)
                        return min_priority
                    return 999
                
                elif state["sort_column"] == "ho_ten":
                    # Sort theo tên (alphabet)
                    return stat['ho_ten_display'].lower()
                
                else:  # so_buoi
                    # Sort theo số buổi
                    return stat['so_buoi']
            
            sorted_stats = sorted(
                week_stats,
                key=get_sort_key,
                reverse=(state["sort_order"] == "desc")
            )
            
            # ✅ Build table rows
            table.rows.clear()
            for stat in sorted_stats:
                ho_ten_display = stat['ho_ten_display']
                loai_list = stat['loai_can_bo']
                chuc_vu_list = stat['chuc_vu']
                so_buoi = stat['so_buoi']
                
                # Display: Join multiple loại/chức vụ với ", "
                loai_display = ", ".join(loai_list) if loai_list else "---"
                chuc_vu_display = ", ".join(chuc_vu_list) if chuc_vu_list else "---"
                
                # Color code based on số buổi
                so_buoi_color = ft.Colors.GREEN_700 if so_buoi >= 2 else ft.Colors.BLUE_700
                
                table.rows.append(ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text(ho_ten_display, size=13)),
                        ft.DataCell(ft.Text(loai_display, size=12)),
                        ft.DataCell(ft.Text(chuc_vu_display, size=12)),
                        ft.DataCell(
                            ft.Text(
                                str(so_buoi),
                                size=14,
                                weight=ft.FontWeight.BOLD,
                                color=so_buoi_color
                            )
                        ),
                    ],
                ))
            
            page.update()
        
        # ===================== WEEK NAVIGATION =====================
        def prev_week(e):
            state["current_week_offset"] -= 1
            load_week_stats()
        
        def next_week(e):
            state["current_week_offset"] += 1
            load_week_stats()
        
        def go_to_current_week(e):
            state["current_week_offset"] = 0
            load_week_stats()
        
        # ===================== UI LAYOUT =====================
        week_title = ft.Text(
            f"📅 Tuần: ...",
            size=16,
            weight=ft.FontWeight.BOLD,
            color=ft.Colors.GREY_900,
        )
        
        week_nav = ft.Container(
            content=ft.Row([
                ft.Container(
                    content=CustomIcon.create(CustomIcon.CHEVRON_LEFT, 20),
                    on_click=prev_week,
                    tooltip="Tuần trước",
                    padding=8,
                    border_radius=8,
                    bgcolor=ft.Colors.BLUE_50,
                    ink=True,
                ),
                week_title,
                ft.Container(
                    content=CustomIcon.create(CustomIcon.CHEVRON_RIGHT, 20),
                    on_click=next_week,
                    tooltip="Tuần sau",
                    padding=8,
                    border_radius=8,
                    bgcolor=ft.Colors.BLUE_50,
                    ink=True,
                ),
                ft.Container(
                    content=CustomIcon.create(CustomIcon.TODAY, 20),
                    on_click=go_to_current_week,
                    tooltip="Về tuần hiện tại",
                    padding=8,
                    border_radius=8,
                    bgcolor=ft.Colors.GREEN_50,
                    ink=True,
                ),
            ], alignment=ft.MainAxisAlignment.CENTER, spacing=12),
            padding=12,
            bgcolor=ft.Colors.WHITE,
            border_radius=10,
            border=ft.border.all(1, ft.Colors.GREY_300),
        )
        
        result_content = ft.Column(
            expand=True,
            spacing=20,
            scroll=ft.ScrollMode.AUTO,
            controls=[
                # Header
                ft.Row([
                    CustomIcon.create(CustomIcon.INFO, size=32),
                    ft.Text("THỐNG KÊ TRỰC", size=24, weight=ft.FontWeight.BOLD, color=ft.Colors.GREY_900),
                ], spacing=12),
                
                ft.Divider(height=1, color=ft.Colors.GREY_300),
                
                # Overview cards
                ft.Row([
                    card_bch_hoi,
                    card_bch_doan,
                    card_ban_vp,
                ], spacing=15),
                
                ft.Container(height=10),
                
                # Week navigation
                week_nav,
                
                # Table
                ft.Container(
                    content=ft.Column([
                        ft.Row([
                            ft.Text("👥 Danh sách đã đi trực", size=18, weight=ft.FontWeight.BOLD, color=ft.Colors.GREY_900),
                            ft.Text("(Click vào tiêu đề cột để sắp xếp)", size=11, color=ft.Colors.GREY_600, italic=True),
                        ], spacing=12),
                        ft.Container(height=8),
                        ft.Column([table], scroll=ft.ScrollMode.AUTO, expand=True),
                    ], spacing=0),
                    bgcolor=ft.Colors.WHITE,
                    padding=15,
                    border_radius=12,
                    border=ft.border.all(1, ft.Colors.GREY_300),
                    expand=True,
                ),
            ],
        )
        
        # Wrap in Stack with loading overlay
        result = ft.Stack(
            [
                result_content,
                loading_overlay,
            ],
            expand=True,
        )
        
        async def _delayed_load():
            await asyncio.sleep(0.2)
            load_week_stats()
        
        page.run_task(_delayed_load)
        
        return result

# ============================================================
    # MAIN UI: SUB-TAB NAVIGATION
    # ============================================================
    
    # Tạo sub-tab buttons
    sub_tab_buttons = []
    
    def switch_sub_tab(index):
        """Chuyển đổi sub-tab"""
        tab_state["current_index"] = index
        
        if index == 0:
            content_container.content = CanBoTab()
        elif index == 1:
            content_container.content = LichTrucTab()
        else:
            content_container.content = ThongKeTab()
        
        # Update màu của sub-tab buttons
        for i, btn in enumerate(sub_tab_buttons):
            if i == index:
                btn.bgcolor = ft.Colors.BLUE_600
                btn.content.controls[1].color = ft.Colors.WHITE
            else:
                btn.bgcolor = ft.Colors.GREY_300
                btn.content.controls[1].color = ft.Colors.GREY_800
        
        page.update()
    
    # Tạo 3 sub-tab buttons
    sub_tabs = [
        {"name": "Danh sách BVP/BCH", "icon": CustomIcon.PEOPLE},
        {"name": "Lịch trực", "icon": CustomIcon.CALENDAR},
        {"name": "Thống kê", "icon": CustomIcon.INFO},
    ]
    
    for i, tab in enumerate(sub_tabs):
        btn = ft.Container(
            content=ft.Row([
                CustomIcon.create(tab["icon"], size=18),
                ft.Text(
                    tab["name"], 
                    size=14,
                    color=ft.Colors.WHITE if i == 0 else ft.Colors.GREY_800
                ),
            ], spacing=8),
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
    
    # Set nội dung ban đầu (Cán bộ tab)
    content_container.content = CanBoTab()
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