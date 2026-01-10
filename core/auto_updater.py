# core/auto_updater.py
"""
Hệ thống tự động cập nhật cho app Quản lý Đoàn - Hội
Kiểm tra version mới từ GitHub Releases và tải về
"""

import os
import sys
import json
import requests
import subprocess
import tempfile
from datetime import datetime
from pathlib import Path
from packaging import version as pkg_version
import flet as ft
import asyncio
import threading
from ui.icon_helper import CustomIcon


class AutoUpdater:
    """Auto-update manager cho ứng dụng"""
    
    def __init__(self, 
                 current_version: str,
                 github_repo: str,
                 update_check_file: str = "last_update_check.json"):
        self.current_version = current_version
        self.github_repo = github_repo
        self.update_check_file = update_check_file
        self.api_url = f"https://api.github.com/repos/{github_repo}/releases/latest"
    
    def should_check_update(self, check_interval_hours: int = 24) -> bool:
        """Kiểm tra xem đã đến lúc check update chưa"""
        try:
            if not os.path.exists(self.update_check_file):
                return True
            
            with open(self.update_check_file, 'r') as f:
                data = json.load(f)
                last_check = datetime.fromisoformat(data.get('last_check', '2000-01-01'))
                hours_since = (datetime.now() - last_check).total_seconds() / 3600
                return hours_since >= check_interval_hours
        except:
            return True
    
    def save_check_time(self):
        """Lưu thời gian check update"""
        try:
            with open(self.update_check_file, 'w') as f:
                json.dump({
                    'last_check': datetime.now().isoformat(),
                    'current_version': self.current_version
                }, f)
        except:
            pass
    
    def check_for_update(self) -> dict:
        """
        Kiểm tra version mới trên GitHub
        Returns: dict chứa thông tin update
        """
        result = {
            'has_update': False,
            'latest_version': self.current_version,
            'download_url': None,
            'release_notes': '',
            'file_size': 0,
            'error': None
        }
        
        try:
            response = requests.get(self.api_url, timeout=10)
            response.raise_for_status()
            release_data = response.json()
            
            latest_version = release_data['tag_name'].lstrip('v')
            result['latest_version'] = latest_version
            result['release_notes'] = release_data.get('body', '')
            
            if pkg_version.parse(latest_version) > pkg_version.parse(self.current_version):
                result['has_update'] = True
                
                for asset in release_data.get('assets', []):
                    if asset['name'].endswith('.exe'):
                        result['download_url'] = asset['browser_download_url']
                        result['file_size'] = asset['size']
                        break
                
                if not result['download_url']:
                    result['error'] = "Không tìm thấy file cài đặt"
                    result['has_update'] = False
            
            self.save_check_time()
            
        except requests.RequestException as e:
            result['error'] = f"Lỗi kết nối: {str(e)}"
        except Exception as e:
            result['error'] = f"Lỗi kiểm tra: {str(e)}"
        
        return result
    
    def download_update(self, download_url: str, progress_callback=None) -> str:
        """Tải file cập nhật về"""
        temp_dir = tempfile.gettempdir()
        filename = download_url.split('/')[-1]
        filepath = os.path.join(temp_dir, filename)
        
        response = requests.get(download_url, stream=True)
        response.raise_for_status()
        
        total_size = int(response.headers.get('content-length', 0))
        downloaded = 0
        
        with open(filepath, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    
                    if progress_callback:
                        progress_callback(downloaded, total_size)
        
        return filepath
    
    def install_update(self, installer_path: str):
        """Chạy installer và thoát app"""
        if sys.platform == 'win32':
            subprocess.Popen([installer_path], shell=True)
        elif sys.platform == 'darwin':
            subprocess.Popen(['open', installer_path])
        else:
            subprocess.Popen(['xdg-open', installer_path])
        
        sys.exit(0)


class UpdateDialog:
    """Dialog hiển thị thông báo cập nhật - UI đẹp giống Login"""
    
    def __init__(self, page: ft.Page, updater: AutoUpdater):
        self.page = page
        self.updater = updater
        self.download_progress = None
    
    def show_update_available(self, update_info: dict):
        """Hiển thị dialog có bản cập nhật mới - UI đẹp"""
        
        latest_version = update_info['latest_version']
        release_notes = update_info['release_notes']
        file_size_mb = update_info['file_size'] / (1024 * 1024)
        
        # Progress components
        progress_bar = ft.ProgressBar(
            value=0,
            width=450,
            visible=False,
            color=ft.Colors.BLUE_600,
            bgcolor=ft.Colors.BLUE_100,
            height=8,
            border_radius=4,
        )
        
        progress_text = ft.Text(
            "",
            size=13,
            color=ft.Colors.GREY_700,
            visible=False,
            text_align=ft.TextAlign.CENTER,
        )
        
        self.download_progress = {
            'bar': progress_bar,
            'text': progress_text
        }
        
        # Release notes box - giống style login
        notes_content = ft.Container(
            content=ft.Column([
                ft.Row([
                    CustomIcon.create(CustomIcon.INFO, size=16),
                    ft.Text(
                        "✨ Tính năng mới:",
                        size=14,
                        weight=ft.FontWeight.BOLD,
                        color=ft.Colors.GREY_900
                    ),
                ], spacing=8),
                ft.Container(height=6),
                ft.Container(
                    content=ft.Text(
                        release_notes[:400] + ("..." if len(release_notes) > 400 else ""),
                        size=13,
                        color=ft.Colors.GREY_700,
                        selectable=True,
                    ),
                    padding=12,
                    bgcolor=ft.Colors.WHITE,
                    border_radius=8,
                    border=ft.border.all(1, ft.Colors.GREY_200),
                ),
            ], spacing=0, scroll=ft.ScrollMode.AUTO),
            padding=16,
            bgcolor=ft.Colors.BLUE_50,
            border_radius=10,
            border=ft.border.all(1, ft.Colors.BLUE_200),
            height=180,
        )
        
        # Buttons - giống style login
        update_btn = ft.ElevatedButton(
            content=ft.Row([
                ft.Icon(ft.Icons.DOWNLOAD, size=18, color=ft.Colors.WHITE),
                ft.Text("Tải về và cài đặt", size=14, weight=ft.FontWeight.W_600)
            ], spacing=8, tight=True, alignment=ft.MainAxisAlignment.CENTER),
            on_click=lambda e: self._start_download(e, update_info['download_url'], dialog),
            style=ft.ButtonStyle(
                color=ft.Colors.WHITE,
                bgcolor=ft.Colors.BLUE_600,
                padding=16,
                shape=ft.RoundedRectangleBorder(radius=12),
            ),
            height=52,
            width=float("inf"),
        )
        
        later_btn = ft.TextButton(
            "Để sau",
            on_click=lambda e: self._close_dialog(dialog),
            style=ft.ButtonStyle(
                color=ft.Colors.GREY_700,
                padding=16,
            ),
        )
        
        # Dialog content - giống layout login
        content = ft.Container(
            width=520,
            content=ft.Column([
                # Header với logo
                ft.Container(
                    content=ft.Image(src="assets/favicon.ico", width=80, height=80),
                    alignment=ft.Alignment.CENTER,
                    margin=ft.margin.only(bottom=16),
                ),
                
                # Title
                ft.Text(
                    "🎉 Đã có bản cập nhật mới!",
                    size=24,
                    weight=ft.FontWeight.BOLD,
                    color=ft.Colors.BLACK,
                    text_align=ft.TextAlign.CENTER,
                ),
                
                # Version info
                ft.Container(
                    content=ft.Column([
                        ft.Text(
                            f"Phiên bản {latest_version}",
                            size=16,
                            weight=ft.FontWeight.W_600,
                            color=ft.Colors.BLUE_700,
                        ),
                        ft.Text(
                            f"Dung lượng: {file_size_mb:.1f} MB",
                            size=13,
                            color=ft.Colors.GREY_600,
                        ),
                    ], spacing=4, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                    padding=12,
                    bgcolor=ft.Colors.BLUE_50,
                    border_radius=8,
                    border=ft.border.all(1, ft.Colors.BLUE_200),
                ),
                
                ft.Container(height=12),
                
                # Release notes
                notes_content,
                
                ft.Container(height=16),
                
                # Progress section
                progress_bar,
                ft.Container(height=6, visible=False, ref=ft.Ref[ft.Container]()),
                progress_text,
                
                ft.Container(height=16),
                
                # Buttons
                update_btn,
                ft.Container(height=8),
                later_btn,
                
            ], spacing=0, tight=True, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            padding=ft.padding.symmetric(horizontal=40, vertical=32),
            border_radius=16,
            bgcolor=ft.Colors.WHITE,
            shadow=ft.BoxShadow(
                spread_radius=1,
                blur_radius=20,
                color=ft.Colors.with_opacity(0.15, ft.Colors.BLACK),
                offset=ft.Offset(0, 4),
            ),
        )
        
        # Background giống login
        background = ft.Container(
            content=ft.Image(
                src="assets/bg.png",
                width=9999,
                height=9999,
                fit="cover",
            ),
            expand=True,
        )
        
        dialog_stack = ft.Stack(
            controls=[
                background,
                ft.Container(
                    content=content,
                    alignment=ft.Alignment.CENTER,
                    expand=True,
                ),
            ],
            expand=True,
        )
        
        dialog = ft.AlertDialog(
            modal=True,
            content=ft.Container(
                content=dialog_stack,
                width=600,
                height=650,
            ),
            bgcolor=ft.Colors.TRANSPARENT,
            content_padding=0,
        )
        
        self.page.overlay.append(dialog)
        dialog.open = True
        self.page.update()
        
        return dialog
    
    def _start_download(self, e, download_url: str, dialog: ft.AlertDialog):
        """Bắt đầu tải file"""
        
        # Disable update button
        dialog.content.content.controls[1].content.controls[-3].disabled = True
        dialog.content.content.controls[1].content.controls[-1].disabled = True
        
        # Hiện progress
        self.download_progress['bar'].visible = True
        self.download_progress['text'].visible = True
        self.page.update()
        
        def download_thread():
            try:
                def progress_callback(downloaded, total):
                    progress = downloaded / total if total > 0 else 0
                    self.download_progress['bar'].value = progress
                    self.download_progress['text'].value = f"Đã tải: {downloaded / (1024*1024):.1f} MB / {total / (1024*1024):.1f} MB ({progress*100:.0f}%)"
                    self.page.update()
                
                installer_path = self.updater.download_update(download_url, progress_callback)
                self.page.run_task(lambda: self._show_install_button(dialog, installer_path))
                
            except Exception as ex:
                self.page.run_task(lambda: self._show_download_error(dialog, str(ex)))
        
        threading.Thread(target=download_thread, daemon=True).start()
    
    def _show_install_button(self, dialog: ft.AlertDialog, installer_path: str):
        """Hiển thị nút cài đặt sau khi tải xong"""
        
        self.download_progress['text'].value = "✅ Tải xuống hoàn tất!"
        self.download_progress['text'].color = ft.Colors.GREEN_700
        self.download_progress['text'].weight = ft.FontWeight.BOLD
        
        # Thay nút update bằng nút install
        content_container = dialog.content.content.controls[1].content
        content_container.controls[-3] = ft.ElevatedButton(
            content=ft.Row([
                ft.Icon(ft.Icons.INSTALL_DESKTOP, size=18, color=ft.Colors.WHITE),
                ft.Text("Cài đặt ngay", size=14, weight=ft.FontWeight.W_600)
            ], spacing=8, tight=True, alignment=ft.MainAxisAlignment.CENTER),
            on_click=lambda e: self.updater.install_update(installer_path),
            style=ft.ButtonStyle(
                color=ft.Colors.WHITE,
                bgcolor=ft.Colors.GREEN_600,
                padding=16,
                shape=ft.RoundedRectangleBorder(radius=12),
            ),
            height=52,
            width=float("inf"),
        )
        
        content_container.controls[-1].visible = False  # Ẩn nút "Để sau"
        
        self.page.update()
    
    def _show_download_error(self, dialog: ft.AlertDialog, error: str):
        """Hiển thị lỗi tải xuống"""
        
        self.download_progress['bar'].visible = False
        self.download_progress['text'].value = f"❌ Lỗi: {error}"
        self.download_progress['text'].color = ft.Colors.RED_700
        self.download_progress['text'].weight = ft.FontWeight.BOLD
        self.download_progress['text'].visible = True
        
        # Enable lại buttons
        dialog.content.content.controls[1].content.controls[-3].disabled = False
        dialog.content.content.controls[1].content.controls[-1].disabled = False
        
        self.page.update()
    
    def _close_dialog(self, dialog: ft.AlertDialog):
        """Đóng dialog"""
        dialog.open = False
        if dialog in self.page.overlay:
            self.page.overlay.remove(dialog)
        self.page.update()


def show_check_update_button(page: ft.Page, current_version: str, github_repo: str):
    """
    Hiển thị nút "Kiểm tra cập nhật" trong menu/settings
    Gọi hàm này trong UI settings hoặc profile
    """
    
    def manual_check_update(e):
        updater = AutoUpdater(current_version, github_repo)
        
        # Loading dialog
        loading = ft.AlertDialog(
            modal=True,
            content=ft.Container(
                content=ft.Row([
                    ft.ProgressRing(width=30, height=30, stroke_width=3),
                    ft.Text("Đang kiểm tra cập nhật...", size=14)
                ], spacing=12, tight=True),
                padding=20,
            ),
            bgcolor=ft.Colors.WHITE,
        )
        page.overlay.append(loading)
        loading.open = True
        page.update()
        
        async def do_check():
            update_info = await asyncio.to_thread(updater.check_for_update)
            
            loading.open = False
            page.overlay.remove(loading)
            page.update()
            
            if update_info['error']:
                error_dlg = ft.AlertDialog(
                    modal=True,
                    title=ft.Row([
                        ft.Icon(ft.Icons.ERROR_OUTLINE, color=ft.Colors.RED_600, size=24),
                        ft.Text("Lỗi kiểm tra cập nhật", size=16, weight=ft.FontWeight.BOLD),
                    ], spacing=10),
                    content=ft.Text(update_info['error'], size=13),
                    actions=[
                        ft.TextButton("Đóng", on_click=lambda e: close_dlg(error_dlg))
                    ],
                    bgcolor=ft.Colors.WHITE,
                )
                page.overlay.append(error_dlg)
                error_dlg.open = True
                page.update()
            
            elif update_info['has_update']:
                dialog_mgr = UpdateDialog(page, updater)
                dialog_mgr.show_update_available(update_info)
            
            else:
                ok_dlg = ft.AlertDialog(
                    modal=True,
                    title=ft.Row([
                        ft.Icon(ft.Icons.CHECK_CIRCLE, color=ft.Colors.GREEN_600, size=24),
                        ft.Text("Đã cập nhật", size=16, weight=ft.FontWeight.BOLD),
                    ], spacing=10),
                    content=ft.Text(
                        f"Bạn đang dùng phiên bản mới nhất ({current_version})",
                        size=13
                    ),
                    actions=[
                        ft.TextButton("Đóng", on_click=lambda e: close_dlg(ok_dlg))
                    ],
                    bgcolor=ft.Colors.WHITE,
                )
                page.overlay.append(ok_dlg)
                ok_dlg.open = True
                page.update()
        
        def close_dlg(dlg):
            dlg.open = False
            page.overlay.remove(dlg)
            page.update()
        
        page.run_task(do_check)
    
    return ft.ElevatedButton(
        content=ft.Row([
            ft.Icon(ft.Icons.SYSTEM_UPDATE, size=18),
            ft.Text("Kiểm tra cập nhật", size=13)
        ], spacing=8, tight=True),
        on_click=manual_check_update,
        style=ft.ButtonStyle(
            bgcolor=ft.Colors.GREEN_600,
            color=ft.Colors.WHITE,
        ),
    )


async def check_update_on_startup(page: ft.Page, current_version: str, github_repo: str):
    """
    Tự động kiểm tra cập nhật khi mở app
    Gọi hàm này trong main() của app.py
    """
    await asyncio.sleep(3)
    
    updater = AutoUpdater(current_version, github_repo)
    
    # Chỉ check nếu đã qua 24h
    if not updater.should_check_update(check_interval_hours=24):
        return
    
    try:
        update_info = await asyncio.to_thread(updater.check_for_update)
        
        if update_info['has_update']:
            dialog = UpdateDialog(page, updater)
            dialog.show_update_available(update_info)
    except Exception as e:
        print(f"[UPDATE] Auto-check failed: {e}")