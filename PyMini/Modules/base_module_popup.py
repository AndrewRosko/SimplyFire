from .base_module import BaseModule
from tkinter import Toplevel
from PyMini import app
class BaseModulePopup(Toplevel):
    def __init__(self,
                 module:BaseModule,
                 name:str=None
                 ) -> None:
        self.module = module
        self.show=None
        super().__init__(app.root)
        self.protocol('WM_DELETE_WINDOW', self._on_close)
        self.widgets = self.module.widgets
        self.name=name

    def show_window(self):
        self.show = True
        self.deiconify()

    def withdraw_window(self):
        self.show=False
        super().withdraw()
    def _on_close(self, event=None):
        self.show = False
        super().withdraw()

