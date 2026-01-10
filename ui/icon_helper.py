# ui/icon_helper.py
import flet as ft

ICONS_DIR = "assets/icons"

class CustomIcon:
    # Hành động CRUD (Thêm/Sửa/Xóa/Lưu/Upload/Download/Refresh)
    ADD = f"{ICONS_DIR}/add.png"
    UPLOAD = f"{ICONS_DIR}/upload.png"
    DOWNLOAD = f"{ICONS_DIR}/download.png"
    EDIT = f"{ICONS_DIR}/edit.png"
    EDIT_CALENDAR = f"{ICONS_DIR}/edit_calendar.png"
    SAVE = f"{ICONS_DIR}/save.png"
    DELETE = f"{ICONS_DIR}/delete.png"
    DELETE1 = f"{ICONS_DIR}/delete1.png"
    DELETE_FOREVER = f"{ICONS_DIR}/delete_forever.png"
    REFRESH = f"{ICONS_DIR}/refresh.png"
    CHECK = f"{ICONS_DIR}/check.png"
    CHECK1 = f"{ICONS_DIR}/check1.png"
    CHECK_GREEN = f"{ICONS_DIR}/check_green.png"
    CHECK_WHITE = f"{ICONS_DIR}/check_white.png"
    CLOSE = f"{ICONS_DIR}/close.png"
    CLOSE1 = f"{ICONS_DIR}/close1.png"

    # Navigation / Chevron / Minimize / Window Controls
    CHEVRON_LEFT = f"{ICONS_DIR}/chevron_left.png"
    CHEVRON_RIGHT = f"{ICONS_DIR}/chevron_right.png"
    MINIMIZE = f"{ICONS_DIR}/minimize.png"

    # User / Account / Role / Permissions
    ACCOUNT_CIRCLE = f"{ICONS_DIR}/account_circle.png"
    PERSON = f"{ICONS_DIR}/person.png"
    PERSON_ADD = f"{ICONS_DIR}/person_add.png"
    ROLE = f"{ICONS_DIR}/role.png"
    LOCK = f"{ICONS_DIR}/lock.png"
    UNLOCK = f"{ICONS_DIR}/unlock.png"
    ADMIN = f"{ICONS_DIR}/admin.png"
    LOGOUT = f"{ICONS_DIR}/logout.png"

    # Class / School / Calendar / Work / Badge / Time
    CLASS = f"{ICONS_DIR}/class.png"
    SCHOOL = f"{ICONS_DIR}/school.png"
    PEOPLE = f"{ICONS_DIR}/people.png"
    BADGE = f"{ICONS_DIR}/badge.png"
    CALENDAR = f"{ICONS_DIR}/calendar.png"
    TODAY = f"{ICONS_DIR}/today.png"
    TIME = f"{ICONS_DIR}/time.png"
    WORK = f"{ICONS_DIR}/work.png"
    VIEW_WEEK = f"{ICONS_DIR}/view_week.png"
    EDIT_CALENDAR = f"{ICONS_DIR}/edit_calendar.png"
    MULTI_SELECT = f"{ICONS_DIR}/multi_select.png"
    SUNRISE = f"{ICONS_DIR}/sunrise.png"
    SUNSET = f"{ICONS_DIR}/sunset.png"

    # Status / Messages / Notifications
    SUCCESS_MESSAGE = f"{ICONS_DIR}/success_message.png"
    WARNING_MESSAGE = f"{ICONS_DIR}/warning_message.png"
    ERROR_MESSAGE = f"{ICONS_DIR}/error_message.png"
    INFO_MESSAGE = f"{ICONS_DIR}/info_message.png"
    WARNING = f"{ICONS_DIR}/warning.png"
    ERROR = f"{ICONS_DIR}/error.png"
    INFO = f"{ICONS_DIR}/info.png"
    INFO1 = f"{ICONS_DIR}/info1.png"

    # Misc / Document / Report / Crop / Storage / Search
    SEARCH = f"{ICONS_DIR}/search.png"
    FILTER = f"{ICONS_DIR}/filter.png"
    DOCUMENT = f"{ICONS_DIR}/document.png"
    REPORT = f"{ICONS_DIR}/report.png"
    CROP_SQUARE = f"{ICONS_DIR}/crop_square.png"
    STORAGE = f"{ICONS_DIR}/storage.png"
    
    @staticmethod
    def create(icon_path: str, size: int = 20, color: str = None):
        return ft.Image(
            src=icon_path,
            width=size,
            height=size,
        )
    
    @staticmethod
    def button_icon(icon_path: str, size: int = 20):
        return CustomIcon.create(icon_path, size)
    
    @staticmethod
    def prefix_icon(icon_path: str, size: int = 20):
        return ft.Container(
            content=CustomIcon.create(icon_path, size),
            padding=ft.padding.only(left=12, right=8),
        )


def icon_button(
    icon_path: str,
    tooltip: str = "",
    on_click=None,
    icon_size: int = 20,
    icon_color: str = None
):
    return ft.Container(
        content=CustomIcon.create(icon_path, icon_size),
        on_click=on_click,
        tooltip=tooltip,
        padding=8,
        border_radius=4,
        ink=True,
    )


def elevated_button(
    text: str,
    icon_path: str = None,
    on_click=None,
    icon_size: int = 20,
    **kwargs
):
    if icon_path:
        content = ft.Row(
            [
                CustomIcon.create(icon_path, icon_size),
                ft.Text(text),
            ],
            spacing=8,
            alignment=ft.MainAxisAlignment.CENTER,
            tight=True,
        )
        return ft.ElevatedButton(
            content=content,
            on_click=on_click,
            **kwargs
        )
    else:
        return ft.ElevatedButton(
            text=text,
            on_click=on_click,
            **kwargs
        )