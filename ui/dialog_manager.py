# ui/dialog_manager.py
import flet as ft
import asyncio


class DialogManager:
    def __init__(self, page: ft.Page):
        self.page = page
        self.dialog_stack = []
        self.is_closing = False
    
    def show_dialog(self, dialog: ft.AlertDialog, on_close_callback=None):
        try:
            self.dialog_stack.append({
                'dialog': dialog,
                'callback': on_close_callback
            })
            
            self.page.overlay.append(dialog)
            dialog.open = True
            self.page.update()
            
        except Exception as ex:
            import traceback
            traceback.print_exc()
    
    def close_current_dialog(self):
        if self.is_closing or not self.dialog_stack:
            return
        
        self.is_closing = True
        
        dialog_info = self.dialog_stack.pop()
        dialog = dialog_info['dialog']
        callback = dialog_info.get('callback')
        
        dialog.open = False
        self.page.update()
        
        self.page.run_task(self._delayed_remove_async, dialog, callback)
    
    async def _delayed_remove_async(self, dialog, callback):
        await asyncio.sleep(0.05)
        
        try:
            if dialog in self.page.overlay:
                self.page.overlay.remove(dialog)
            
            if callback:
                callback()
            
            self.page.update()
            
        except Exception:
            pass
        finally:
            self.is_closing = False
    
    def close_all_dialogs(self):
        self.page.run_task(self._close_all_async)
    
    async def _close_all_async(self):
        while self.dialog_stack:
            self.close_current_dialog()
            await asyncio.sleep(0.05)
    
    def has_open_dialogs(self) -> bool:
        return len(self.dialog_stack) > 0
    
    def get_current_dialog(self):
        if self.dialog_stack:
            return self.dialog_stack[-1]['dialog']
        return None