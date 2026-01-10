# ui/message_manager.py
import flet as ft
import asyncio
from ui.icon_helper import CustomIcon


class MessageOverlay(ft.Container):
    def __init__(self, text: str, title: str, message_type: str = "success"):
        styles = {
            "success": {
                "icon": CustomIcon.SUCCESS_MESSAGE,
                "bg_color": ft.Colors.with_opacity(0.95, "#F6FFED"),
                "border_color": ft.Colors.with_opacity(0.9, "#B7EB8F"),
                "title_color": "#389E0D",
                "text_color": "#389E0D",
            },
            "warning": {
                "icon": CustomIcon.WARNING_MESSAGE,
                "bg_color": ft.Colors.with_opacity(0.95, "#FFFBE6"),
                "border_color": ft.Colors.with_opacity(0.9, "#FFE58F"),
                "title_color": "#D46B08",
                "text_color": "#D46B08",
            },
            "error": {
                "icon": CustomIcon.ERROR_MESSAGE,
                "bg_color": ft.Colors.with_opacity(0.95, "#FFF2F0"),
                "border_color": ft.Colors.with_opacity(0.9, "#FFCCC7"),
                "title_color": "#CF1322",
                "text_color": "#CF1322",
            },
            "info": {
                "icon": CustomIcon.INFO_MESSAGE,
                "bg_color": ft.Colors.with_opacity(0.95, "#E6F7FF"),
                "border_color": ft.Colors.with_opacity(0.9, "#91D5FF"),
                "title_color": "#0958D9",
                "text_color": "#0958D9",
            },
        }
        
        style = styles.get(message_type, styles["info"])
        
        super().__init__(
            content=ft.Row([
                CustomIcon.create(style["icon"], size=22),
                ft.Column([
                    ft.Text(title, size=14, weight=ft.FontWeight.W_600, color=style["title_color"]),
                    ft.Text(text, size=13, color=style["text_color"]),
                ], spacing=2, tight=True),
            ], spacing=12, tight=True),
            bgcolor=style["bg_color"],
            padding=ft.padding.symmetric(horizontal=16, vertical=12),
            border_radius=8,
            border=ft.border.all(1, style["border_color"]),
            shadow=ft.BoxShadow(
                blur_radius=12,
                spread_radius=0,
                color=ft.Colors.with_opacity(0.15, ft.Colors.BLACK),
                offset=ft.Offset(0, 4),
            ),
            animate_opacity=ft.Animation(300, ft.AnimationCurve.EASE_OUT),
        )


class MessageManager:
    def __init__(self, page: ft.Page, dialog_container: ft.Container = None):
        self.page = page
        self.dialog_container = dialog_container
        self._is_showing = False
        self._message_layer = None

    def set_dialog_container(self, container: ft.Container):
        self.dialog_container = container

    def show(self, text: str, title: str = "", message_type: str = "success", duration: int = 4000):
        if self._is_showing:
            return

        self._is_showing = True

        if not title:
            title_map = {
                "success": "Thành công",
                "warning": "Cảnh báo",
                "error": "Lỗi",
                "info": "Thông tin",
            }
            title = title_map.get(message_type, "Thông báo")

        overlay = MessageOverlay(text, title, message_type)
        wrapper = ft.Container(
            content=overlay,
            alignment=ft.Alignment(0, -0.85),
            margin=ft.margin.only(top=20, left=20, right=20),
            opacity=0,
            animate_opacity=ft.Animation(300, ft.AnimationCurve.EASE_OUT),
        )

        self._message_layer = wrapper

        if self.dialog_container:
            content = self.dialog_container.content
            if not isinstance(content, ft.Stack):
                self.dialog_container.content = ft.Stack([content, wrapper])
            else:
                content.controls.append(wrapper)
        else:
            self.page.overlay.append(wrapper)

        wrapper.opacity = 1
        self.page.update()

        self.page.run_task(self._auto_hide_async, duration / 1000)

    async def _auto_hide_async(self, delay_seconds: float):
        await asyncio.sleep(delay_seconds)

        if self._message_layer:
            self._message_layer.opacity = 0
            self.page.update()
            await asyncio.sleep(0.3)

        if self.dialog_container and isinstance(self.dialog_container.content, ft.Stack):
            if self._message_layer in self.dialog_container.content.controls:
                self.dialog_container.content.controls.remove(self._message_layer)
        elif self._message_layer in self.page.overlay:
            self.page.overlay.remove(self._message_layer)

        self.page.update()

        self._message_layer = None
        self._is_showing = False

    def success(self, text: str, title: str = "", duration: int = 4000):
        self.show(text, title or "Thành công", "success", duration)

    def error(self, text: str, title: str = "", duration: int = 5000):
        self.show(text, title or "Lỗi", "error", duration)

    def warning(self, text: str, title: str = "", duration: int = 4000):
        self.show(text, title or "Cảnh báo", "warning", duration)

    def info(self, text: str, title: str = "", duration: int = 4000):
        self.show(text, title or "Thông tin", "info", duration)