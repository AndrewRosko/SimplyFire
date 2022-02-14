from simplyfire import app
from simplyfire.loader import config
import pkg_resources
import os
import yaml
from tkinter import ttk, messagebox
import tkinter as Tk
from simplyfire.utils.scrollable_option_frame import ScrollableOptionFrame
import textwrap
from packaging.version import parse
import importlib

def load():
    global plugin_vars
    plugin_vars = {}
    global active_plugins
    active_plugins = []
    global window
    window = Tk.Toplevel(app.root)

    window.withdraw()
    window.geometry('400x600')
    app.menubar.plugin_menu.add_command(label='Manage plug-ins', command=window.deiconify)
    window.protocol('WM_DELETE_WINDOW', _on_close)

    window.grid_columnconfigure(0, weight=1)
    window.grid_rowconfigure(0, weight=1)
    optionframe = ScrollableOptionFrame(window)
    optionframe.grid(column=0, row=0, sticky='news')

    global frame
    frame = optionframe.frame
    frame.grid_columnconfigure(0, weight=0)
    frame.grid_columnconfigure(1, weight=1)
    frame.grid_columnconfigure(0, weight=0)

    label = Tk.Label(master=frame, text='name', relief='groove')
    label.grid(column=0, row=0, sticky='news')
    label = Tk.Label(master=frame, text='description', relief='groove')
    label.grid(column=1, row=0, sticky='news')
    label = Tk.Label(master=frame, text='on/off', relief='groove')
    label.grid(column=2, row=0, sticky='news')

    button_frame = Tk.Frame(window)
    button_frame.grid(column=0, row=1, sticky='news')
    button_frame.grid_columnconfigure(0, weight=1)
    button_frame.grid_columnconfigure(1, weight=1)

    ttk.Button(button_frame, text='Apply', command=apply).grid(column=0, row=0, sticky='nse')
    ttk.Button(button_frame, text='Cancel', command=cancel).grid(column=1, row=0, sticky='nsw')

    _populate_plugins()


    active_plugins = [p for p in config.active_plugins]

def apply():
    messagebox.showwarning('Warning', 'Please reopen the software to apply changes')
    global active_plugins
    active_plugins = [plugin_name for plugin_name in plugin_vars.keys() if plugin_vars[plugin_name].get()]
    window.withdraw()

def cancel():
    window.withdraw()
    for plugin_name, var in plugin_vars.items():
        if plugin_name in active_plugins:
            var.set(True)
        else:
            var.set(False)

def _on_close():
    window.withdraw()
    # add commands to cancel the changes made on the window

def _populate_plugins():
    app.plugin_manager.load_manifests()
    i = 1
    # make plugin control GUI
    manifests = app.plugin_manager.manifests
    for plugin_name in manifests.keys():
        # load the plugin control GUI
        label = Tk.Label(master=frame, text=plugin_name, relief='groove')
        label.grid(column=0, row=i, sticky='news')

        description = manifests[plugin_name]['description']
        # add warning
        requirements = manifests[plugin_name].get('requirements', None)
        first = True
        if requirements:
            for r in requirements:
                if r not in manifests.keys():
                    if first:
                        description += '\nWarning: Missing requirements - '
                    description += f' {r},'

        if parse(manifests[plugin_name]['minimumCoreVersion']) > parse(config.version):
            description += f'\nWarning: Minimum core requirement not met!'

        label = Tk.Text(master=frame, height=4)
        label.insert(Tk.INSERT,description)
        label.config(state='disabled')
        label.grid(column=1, row=i, sticky='news')

        var = Tk.BooleanVar(frame)
        plugin_vars[plugin_name] = var
        var.set(False)
        checkbutton = ttk.Checkbutton(frame, var=var, onvalue=True, offvalue=False)
        checkbutton.grid(column=2, row=i, sticky='news')
        i += 1

def get_plugins():
    return [plugin_name for plugin_name in plugin_vars.keys() if plugin_vars[plugin_name].get()]

#
#
# def _load_plugin(self, plugin_name):
#     # set toggle ON
#     self.plugins[plugin_name]['toggle'].set(True)
#     # load using the manifest
#     manifest = self.plugins[plugin_name]
#     requirements = manifest.get('requirements', [])
#     for r in requirements:
#         if not self.plugins[r].get('loaded', False):
#             self._load_plugin(r)
#     sources = manifest.get('sources', [])
#     directory = config.PLUGIN_DIR
#     for filename in sources:
#         source_path = os.path.join(directory, filename)
#         importlib.import_module(source_path)
#     manifest['loaded'] = True
#     pass







