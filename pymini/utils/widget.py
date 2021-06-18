import tkinter as Tk
from tkinter import ttk, font
from config import config
from utils import validation
from matplotlib.backends.backend_tkagg import NavigationToolbar2Tk

import textwrap
import pymini

class LinkedWidget():
    """
    This is a parent class for making modified tkinter widgets
    The modified widget allows for easy getter and setter access to the Tk.StringVar associated with the widget
    The widget can store a default value
    The widget can revert to the previously accepted value if the validation does not return True
    """
    def __init__(
            self,
            parent,
            name,
            value="",
            default=""
    ):
        self.parent = parent
        self.name = name
        self.var = Tk.StringVar()
        self.var.set(value)
        self.default = default
        self.prev = value
        self.widget = None

    def get(self):
        return self.var.get()

    def get_widget(self):
        return self.widget

    def set(self, value):
        self.var.set(value)
        self.prev = value

    def get_default(self):
        return self.default

    def set_to_default(self):
        self.set(self.default)

    def revert(self):
        self.set(self.prev)

    def grid(self, *args, **kargs):
        self.widget.grid(*args, **kargs)




class LinkedEntry(LinkedWidget):
    def __init__(
            self,
            parent,
            name="",
            value="",
            default="",
            validate_type=""
        ):
        super().__init__(parent, name, value, default)
        self.widget = Tk.Entry(
            master=parent,
            textvariable=self.var,
            width=config.entry_width,
            justify=Tk.RIGHT
        )
        self.widget.bind('<FocusOut>', lambda e, v=validate_type: self.validate(e, v), add='+')

    def set(self, value=""):
        # cannot use Tk.StringVar.set() due to validatecommand conflict
        self.widget.delete(0, len(self.get()))
        self.widget.insert(0, value)
        print(value)

    def validate(self, event, validation_type, c=None):
        value = self.get()
        if validation.validate(validation_type, self.get()):
            self.prev = value
            return True
        elif validation_type == 'int':
            try:
                new_value = str(int(float(value)))
                self.set(new_value)
                return True
            except:
                self.revert()
                return False
        else:
            self.revert()
            return False

class LinkedOptionMenu(LinkedWidget):
    def __init__(self, parent, name, value, default=None, options=None, command=None):
        super().__init__(parent, name, value, default)

        if options is None:
            options = []

        if value is None:
            value = default
            print("lom: {}, {}".format(value, default))

        self.command = command
        self.widget = ttk.OptionMenu(
            parent,
            self.var,
            value,
            *options,
            command=command
        )

    def replace_options(self, options=None):
        if options is None:
            options = []
        self.widget['menu'].delete(0, 'end')
        for i in options:
            self.widget['menu'].add_command(
                label=i,
                command=self.command
            )

class LinkedText(LinkedWidget):
    def __init__(self,
            parent,
            name="",
            value="",
            default=""
                 ):
        super().__init__(parent=parent,
                         name=name,
                         value=value,
                         default=default)
        self.widget = Tk.Text(master=parent)
        self.set(value)

    def set(self, value):
        disable = False
        if self.widget['state'] == 'disabled':
            disable = True
            self.widget.config(state='normal')
        self.widget.delete(1.0, Tk.END)
        self.widget.insert(1.0, value)
        self.var.set(value)
        if disable:
            self.widget.config(state='disabled')

class LinkedScale(LinkedWidget):
    def __init__(self,
                 parent,
                 name="",
                 value="",
                 default='',
                 from_=0,
                 to=100,
                 orient=Tk.VERTICAL,
                 command=None):
        super().__init__(parent=parent,
                         name=name,
                         value="",
                         default=""
                         )
        self.var = Tk.DoubleVar()
        self.widget = ttk.Scale(master=parent,
                                 variable=self.var,
                                 from_=from_,
                                 to=to,
                                 orient=orient,
                                 command=command)





class LabeledWidget():
    def __init__(self,
                 parent,
                 name,
                 label,
                 value="",
                 default="",
                 command=None):
        self.parent = parent
        self.name = name
        self.frame = Tk.Frame(parent)
        self.frame.grid_columnconfigure(0, weight=1)
        self.frame.grid_columnconfigure(1, weight=0)

        # Format the label text - wrap text according to specified length
        wrapped_label = textwrap.wrap(label, width=config.default_label_length)
        text = '\n'.join(wrapped_label)
        self.label = ttk.Label(self.frame, text=text)

        # self.label.config(width=20)
        # self.label.bind('<Configure>', self.adjust_width)

        self.var = Tk.StringVar()
        self.var.set(value)
        self.default = default
        self.prev = value
        self.widget = None
        self.command = command

        self.label.grid(column=0, row=0, sticky='news')

    def get(self):
        return self.var.get()

    def get_default(self):
        return self.default

    def set(self, value=""):
        self.var.set(value)

    def set_to_default(self):
        self.set(self.default)

    def grid(self, *args, **kwargs):
        self.frame.grid(*args, **kwargs)

    def revert(self):
        print('revert')
        self.set(self.prev)

    def get_widget(self):
        return self.widget


    def bind(self, command):
        try:
            self.widget.bind(command)
        except:
            pass


class LabeledEntry(LabeledWidget):
    def __init__(self,
                 parent,
                 name,
                 label="Enter value",
                 value="default value",
                 default=None,
                 validate_type="float",
                 command=None):
        LabeledWidget.__init__(
            self,
            parent,
            name,
            label,
            value,
            default,
        )

        self.widget = Tk.Entry(
            self.frame,
            textvariable=self.var,
            width=config.entry_width,
            justify=Tk.RIGHT,
            command=command
        )

        self.widget.grid(column=1, row=0, sticky='sew')
        self.widget.bind('<FocusOut>', lambda e, v=validate_type: self.validate(e, v), add='+')

    def set(self, value=""):
        # cannot use Tk.StringVar.set() due to validatecommand conflict
        self.widget.delete(0, len(self.get()))
        self.widget.insert(0, value)

    def validate(self, event, validation_type, c=None):
        value = self.get()
        if validation.validate(validation_type, self.get()):
            self.prev = value
            return True
        elif validation_type == 'int':
            try:
                new_value = str(int(float(value)))
                self.set(new_value)
                self.prev = new_value
                return True
            except:
                self.revert()
                return False
        else:
            self.revert()
            return False


class LabeledOptionMenu(LabeledWidget):
    def __init__(
            self,
            parent,
            name=None,
            label="",
            value="",
            default=None,
            options=[],
            command=None
    ):
        LabeledWidget.__init__(
            self,
            parent,
            name=name,
            label=label,
            value=value,
            default=default
        )

        if value is None:
            value = default

        self.widget = ttk.OptionMenu(
            self.frame,
            self.var,
            value,
            *options,
            command=command
        )
        # self.widget.bind('<FocusOut>', self.test, add='+')
        self.widget.grid(column=1, row=0, sticky='ews')

    def replace_options(self, options=None):
        self.widget['menu'].delete(0, 'end')
        if options is None:
            return
        for i in options:
            self.widget['menu'].add_command(
                label=i,
                command=self.command
            )

    def test(self, event=None):
        print('testing')


class LabeledCheckbox(LabeledWidget):
    def __init__(
            self,
            parent,
            name,
            label=None,
            value=None,
            default=None,
            command=None
    ):
        LabeledWidget.__init__(
            self,
            parent,
            name,
            label,
            value,
            default,
        )
        self.widget = ttk.Checkbutton(
            self.frame,
            variable=self.var,
            command=command
        )
        if value is None:
            value = default
        self.set(value)

        self.bind(command)
        self.widget.grid(column=1, row=0, sticky='ews')

class NavigationToolbar(NavigationToolbar2Tk):
    def __init__(self, canvas, parent):
        self.toolitems = [t for t in self.toolitems if t[0] in ('Pan', 'Zoom', 'Save')]
        NavigationToolbar2Tk.__init__(self, canvas, parent)



