from tkinter import ttk, filedialog
import tkinter as Tk
import yaml
from Backend import interpreter

from config import config

from Layout import font_bar, menubar, detector_tab, style_tab, setting_tab, navigation_tab, \
    sweep_tab, graph_panel, continuous_tab, adjust_tab, evoked_tab
from DataVisualizer import data_display, log_display, evoked_data_display

from utils import widget
import tracemalloc


event_filename = None
widgets = {}

##################################################
#                    Methods                     #
##################################################

def _on_close():
    """
    The function is called when the program is closing (pressing X)
    Uses the config module to write out user-defined parameters
    :return: None
    """
    print('closing')
    if widgets['config_autosave'].get():
        try:
            dump_user_setting()
        except:
            f = setting_tab.save_config_as()
            if f:
                widgets['config_user_path'].set(f)

    dump_config_var(key='key_', filename=config.config_keymap_path, title='Keymap')
    dump_system_setting()
    root.destroy()

def get_value(key, tab=None):
    try:
        v = widgets[key].get()
        return v
    except Exception as e:
        pass

def get_widget(key, tab=None):
    try:
        return widgets[key]
    except:
        pass


def set_value(key, value, tab=None):
    widgets[key].set(value)
    try:
        widgets[key].set(value)
        return
    except:
        raise
        None


def change_label(key, value, tab=None):
    try:
        tabs[tab].change_label(key, value)
        return True
    except:
        for t in tabs:
            try:
                tabs[t].change_label(key, value)
                return True
            except:
                pass
    return False

def load():
    tracemalloc.start()

    global root
    root = Tk.Tk()
    root.title('PyMini v{}'.format(config.version))
    root.geometry('{}x{}'.format(config.geometry[0], config.geometry[1]))

    config.load()
    root.bind('<Control-o>', lambda e:menubar.ask_open_trace())

    root.grid_rowconfigure(0, weight=1)
    root.grid_columnconfigure(0, weight=1)

    root.bind(config.key_reset_focus, lambda e: data_display.table.focus_set())

    global widgets

    pw = Tk.PanedWindow(
        root,
        orient=Tk.HORIZONTAL,
        showhandle=True,
        sashrelief=Tk.SUNKEN,
        handlesize=config.default_pw_handlesize
    )

    pw.grid(column=0, row=0, sticky='news')


    ##################################################
    #                   DATA PANEL                   #
    ##################################################

    # set up frame
    right = Tk.Frame(pw, background = 'pink')
    right.grid(column=0, row=0, sticky='news')
    right.columnconfigure(0, weight=1)
    right.rowconfigure(0, weight=1)

    dp_notebook = ttk.Notebook(right)
    dp_notebook.grid(column=0, row=0, sticky='news')

    global pw_2
    pw_2 = Tk.PanedWindow(
        right,
        orient=Tk.VERTICAL,
        showhandle=True,
        sashrelief=Tk.SUNKEN,
        handlesize=config.default_pw_handlesize
    )


    # must set up a graph object that can 'refresh' and 'plot' etc
    panel = graph_panel.load(None)
    pw_2.add(panel)
    pw_2.paneconfig(panel, height=config.gp_height)

    data_notebook = ttk.Notebook(pw_2)

    panel = data_display.load(None)
    data_notebook.add(panel, text='mini')
    panel = evoked_data_display.load(None)
    data_notebook.add(panel, text='evoked')

    pw_2.add(data_notebook)

    log_frame = log_display.load(None)

    dp_notebook.add(pw_2, text='data')
    dp_notebook.add(log_frame, text='log')


    ##################################################
    #                 CONTROL PANEL                  #
    ##################################################

    # set up frame
    left = Tk.Frame(pw, background='blue')
    left.grid(column=0, row=0, sticky='news')
    left.grid_rowconfigure(0, weight=1)
    left.grid_columnconfigure(0, weight=1)

    # insert control panel in to left panel
    # cp = Tk.Frame(left, bg='purple')
    # cp.grid_columnconfigure(0, weight=1)
    # cp.grid_rowconfigure(0, weight=1)
    # cp.grid(column=0 ,row=0, sticky='news')

    global cp_notebook
    cp_notebook = ttk.Notebook(left)
    cp_notebook.grid(column=0, row=0, sticky='news')

    #############################################################
    # Insert custom tabs here to include in the control panel
    #############################################################

    global tab_details
    tab_details = {
        'mini':        {
            'module': detector_tab,
            'text': 'Mini',
            'partner': ['evoked']
        },
        'evoked':
        {
            'module': evoked_tab,
            'text': 'Evoked',
            'partner': ['mini']
        },
        'continuous':
       {
            'module': continuous_tab,
            'text': 'Cont',
            'partner': ['overlay']
        },
        'overlay':
        {
            'module': sweep_tab,
            'text': 'Sweeps',
            'partner': ['continuous']
        },
        'adjust':
        {
            'module': adjust_tab,
            'text': 'Adjust',
            'partner': None
        },
        'navigation':
        {
            'module': navigation_tab,
            'text': 'Navi',
            'partner': None
        },
        'style':
        {
            'module': style_tab,
            'text': 'Style',
            'partner': None
        },
        'setting':
        {
            'module': setting_tab,
            'text': 'Setting',
            'partner': None
        }
    }

    for i, t in enumerate(tab_details):
        tab_details[t]['tab'] = tab_details[t]['module'].load(left)
        cp_notebook.add(tab_details[t]['tab'], text=tab_details[t]['text'])
        tab_details[t]['index'] = i


    # set focus rules
    for key in widgets:
        if type(widgets[key]) == widget.VarEntry:
            widgets[key].bind('<Return>', lambda e: data_display.table.focus_set(), add='+')
        if type(widgets[key]) == widget.VarCheckbutton:
            widgets[key].bind('<ButtonRelease>', lambda e: data_display.table.focus_set(), add='+')
        if type(widgets[key]) == widget.VarOptionmenu:
            widgets[key].bind('<ButtonRelease>', lambda e: data_display.table.focus_set(), add='+')
        if type(widgets[key]) == widget.VarCheckbutton:
            widgets[key].bind('<ButtonRelease>', lambda e: data_display.table.focus_set(), add='+')

    # set up font adjustment bar
    fb = font_bar.load(left)
    fb.grid(column=0, row=1, sticky='news')

    # set up progress bar
    global pb
    # pb = progress_bar.ProgressBar(left)
    pb = ttk.Progressbar(left, length=100,
                         mode='determinate',
                         orient=Tk.HORIZONTAL)
    pb.grid(column=0, row=2, stick='news')

    # finis up the pw setting:

    pw.grid(column=0, row=0, sticky='news')
    pw.add(left)
    pw.add(right)

    # adjust frame width
    # root.update()
    pw.paneconfig(left, width=int(config.cp_width))
    pw.bind('<ButtonPress>', print)


    ##################################################
    #                    MENU BAR                    #
    ##################################################

    # set up menubar
    menu = menubar.load_menubar(root)
    root.config(menu=menu)

    # set up closing sequence
    root.protocol('WM_DELETE_WINDOW', _on_close)

    # set up event bindings
    interpreter.initialize()

    # # finalize the data viewer - table
    root.update()
    data_display.fit_columns()



    return root


def dump_user_setting(filename=None):
    ignore = ['config_', '_log', 'temp_']
    print('Writing out configuration variables....')
    if filename is None:
        filename = widgets['config_user_path'].get()
    with open(filename, 'w') as f:
        print('writing dump user config {}'.format(filename))
        f.write("#################################################################\n")
        f.write("# PyMini user configurations\n")
        f.write("#################################################################\n")
        f.write("\n")
        # pymini.pb.initiate()
        d = {}
        for key in widgets.keys():
            if key == 'adjust_base_sub_mode':
                print(widgets[key].get())
            try:
                for ig in ignore:
                    if ig in key:
                        break
                else:
                    d[key] = widgets[key].get()
            except:
                d[key] = widgets[key].get()


        f.write(yaml.safe_dump(d))
        # pymini.pb.clear()

        # f.write(yaml.safe_dump(user_vars))
    print('Completed')

def dump_system_setting():
    print('Saving config options....')
    with open(config.config_system_path, 'w') as f:
        print('dumping system config {}'.format(config.config_system_path))
        f.write("#################################################################\n")
        f.write("# PyMini system configurations\n")
        f.write("#################################################################\n")
        f.write("\n")

        f.write(yaml.safe_dump(dict([(key, widgets[key].get()) for key in widgets if 'config' in key])))
    print('Completed')

def dump_config_var(key, filename, title=None):
    print('Saving "{}" config values...'.format(key))
    print(filename)
    with open(filename, 'w') as f:
        f.write("#################################################################\n")
        f.write("# PyMini {} configurations\n".format(title))
        f.write("#################################################################\n")
        f.write("\n")
        f.write(yaml.safe_dump(dict([(n, getattr(config, n)) for n in config.user_vars if key in n])))
    print('Completed')

def load_config(e=None):
    f = filedialog.askopenfile()
    if not f:
        return None
    configs = yaml.safe_load(f)
    for c, v in configs.items():
        try:
            widgets[c].set(v)
        except:
            pass
