from datetime import datetime
from socket import gethostname
from lib.MyFunctions import *
from multiprocessing.pool import ThreadPool
import json
from tkinter import *
from tkinter import ttk
from tkinter import messagebox

'''
TODO
    WW select order by latest
    Add gigabyte drivers
'''

paths, packages = {}, {}
my_platform_type = 'rvp' if 'RVP' in my_platform() else 'gigabyte'
try:
    with open(r'data\path_save.json') as infile:
        paths = json.load(infile)
except (ValueError, FileNotFoundError):
    messagebox.showwarning('Bad save file', 'It seems like the save file is missing/corrupted\nPlease reinstall the application')
    sys.exit()

try:
    error_out = open(r'X:\Users\azelezni\spider_reports\ERROR_%s.log' % datetime.utcnow().strftime('%d-%m-%y_%H-%M-%S'), 'a')
    log_out = open(r'X:\Users\azelezni\spider_reports\OUT_%s.log' % datetime.utcnow().strftime('%d-%m-%y_%H-%M-%S'), 'a')
except FileNotFoundError:
    messagebox.showerror('No network', 'It seems there is no connection to the server.\nCheck network connect and that X: driver is accessible.')
    sys.exit()

pool = ThreadPool(processes=4)


class MainApplication:
    def __init__(self, master):
        """
        Main Application
        :param master: root_tk
        :return: none
        """
        global my_platform_name
        '''  Local dictionaries for variable storage  '''
        self.var_base = {'rename_check': IntVar(),
                         'new_hostname': StringVar(),
                         'renamed': ['KBL', 'SKL', 'LPT', 'PC', 'ARDT', 'FRDT', 'TE', '-IT'],
                         'whitelist_platforms': ['RVP', 'GA-Z170X-UD5'],
                         'drivers_check': IntVar(),
                         'project': StringVar(),
                         'release': StringVar(),
                         'net_stat': IntVar()
                         }
        self.help_text = {'rename_check': 'Select to rename hostname',
                          'hostname_entry': 'Input new hostname',
                          'drivers_check': 'Select to install drivers',
                          'project_combobox': 'Select project',
                          'workweek_combobox': 'Select kit release',
                          'go_button': 'Start'}

        # Style holder
        # self.style = ttk.Style()
        # self.style.theme_use('winnative')

        # Local frames, mainframe and status bar are sitting on baseframe
        self.master = master
        self.baseframe = MyFrame(self.master, padding=0)
        self.mainframe = MyFrame(self.baseframe, padding='6 6 12 20')
        self.mainframe.grid(row=0, column=0, sticky=(N, W, E, S))
        self.status_bar = StatusBar(self.baseframe)
        self.status_bar.baseframe.grid(row=1, column=0, sticky=(W, E))

        # No Network notification
        self.no_net = ttk.Label(self.mainframe, text='Waiting for network')
        # Platform not supported notification
        self.plat_nosup = ttk.Label(self.mainframe, text='Platform isn\'t supported for driver installation')

        # Main logo image
        self.logo = PhotoImage(file='./img/Intel-logo.gif')
        ttk.Label(self.mainframe, image=self.logo).grid(row=0, column=0, columnspan=5)

        '''  Start rename hostname  '''
        self.rename_check = ttk.Checkbutton(self.mainframe, text="Rename Hostname", variable=self.var_base['rename_check'])
        self.rename_check['command'] = self.show_hostname_entry
        self.rename_check.bind('<Enter>', lambda event: self.status_bar.show_help(event, self.help_text['rename_check']))
        self.rename_check.bind('<Leave>', self.status_bar.clear_help)

        self.hostname_entry = ttk.Entry(self.mainframe, textvariable=self.var_base['new_hostname'], width=38)
        self.hostname_entry.bind('<Enter>', lambda event: self.status_bar.show_help(event, self.help_text['hostname_entry']))
        self.hostname_entry.bind('<Leave>', self.status_bar.clear_help)

        self.rename_check.grid(row=1, column=0, sticky=(W, E))
        if all(self.var_base['renamed'][x] not in gethostname() for x in range(0, len(self.var_base['renamed']))):
            self.var_base['rename_check'].set(1)
            self.rename_check.state(['disabled'])
            self.show_hostname_entry()
        '''  End rename hostname  '''

        '''  Start install drivers  '''
        self.drivers_check = ttk.Checkbutton(self.mainframe, text="Install Drivers", variable=self.var_base['drivers_check'])
        self.drivers_check['command'] = self.show_bkc_select
        self.drivers_check.bind('<Enter>', lambda event: self.status_bar.show_help(event, self.help_text['drivers_check']))
        self.drivers_check.bind('<Leave>', self.status_bar.clear_help)

        self.project_combobox = ttk.Combobox(self.mainframe, textvariable=self.var_base['project'], state='readonly', width=15)
        self.project_combobox.bind('<Enter>', lambda event: self.status_bar.show_help(event, self.help_text['project_combobox']))
        self.project_combobox.bind('<Leave>', self.status_bar.clear_help)

        self.workweek_combobox = ttk.Combobox(self.mainframe, textvariable=self.var_base['release'], state='readonly', width=25)
        self.workweek_combobox.bind('<Enter>', lambda event: self.status_bar.show_help(event, self.help_text['workweek_combobox']))
        self.workweek_combobox.bind('<Leave>', self.status_bar.clear_help)

        # if 'RVP' not in my_platform().upper():  # check if RVP platform
        if all(platform not in my_platform().upper() for platform in self.var_base['whitelist_platforms']):  # check if RVP platform
            self.plat_nosup.grid(row=2, column=0, columnspan=2, sticky=(W, E))
        else:
            self.net_thread = pool.apply_async(self.test_network)
            if self.var_base['net_stat'].get() == 1:
                self.drivers_check.grid(row=2, column=0, sticky=(W, E))
            else:
                self.no_net.grid(row=2, column=1, columnspan=2, sticky=(W, E))
        '''  End install drivers  '''

        '''  Start Go button  '''
        self.go_button = ttk.Button(self.mainframe, text='Go', command=self.go)
        self.go_button.bind('<Enter>', lambda event: self.show_help(event, self.help_text['go_button']))
        self.go_button.bind('<Leave>', self.clear_help)
        self.go_button.grid(row=4, column=0, columnspan=3)
        '''  End Go button  '''

    def show_hostname_entry(self):
        """
        Show new hostname input widget
        :return: none
        """
        self.var_base['new_hostname'].set(gethostname())
        if self.var_base['rename_check'].get() == 1:
            self.hostname_entry.grid(row=1, column=1, columnspan=2, sticky=(W, E))
        else:
            self.hostname_entry.grid_forget()

    def show_bkc_select(self):
        """
        Show BKC kit selection
        :return: none
        """
        if self.var_base['drivers_check'].get() == 0:
            self.project_combobox.grid_forget()
            self.workweek_combobox.grid_forget()
        else:
            self.project_combobox['values'] = list(set(packages[proj]['project'] for proj in packages))
            self.project_combobox.bind('<<ComboboxSelected>>', self.project_selected)

            self.project_combobox.grid(row=2, column=1, sticky=(W, E))
            self.workweek_combobox.grid(row=2, column=2, sticky=(W, E))

    def project_selected(self, *args):
        """
        Auto input Kit release when user selected project
        :param args:
        :return:
        """
        # Filter available kits based on selected project and detected platform
        # kits = sorted('_'.join([packages[pack]['win_ver'], packages[pack]['work_week']]) for pack in packages
        kits = sorted(packages[pack]['release'] for pack in packages
                      if self.var_base['project'].get() in pack and
                      get_platform()[self.var_base['project'].get()] in pack)
        self.workweek_combobox['values'] = kits
        try:
            self.workweek_combobox.set(max(kits))  # Show latest release
            return
        except IndexError:
            self.workweek_combobox.set('')
            return

    def show_help(self, event, text):
        """
        Show help about widget
        :param event: mouse hover event
        :param text: text to show
        :return: none
        """
        self.status_bar.var_base['help'].set(text)

    def clear_help(self, event):
        """
        Clear help text when mouse leaves widget area
        :param event: mouse leave event
        :return: none
        """
        self.status_bar.var_base['help'].set('')

    def test_network(self):
        """
        Check if network location is accessible.
         If not, show notification, after connection is available populate packages,
         remove no network notification and place driver check on grid
        :return: 1
        """
        self.no_net.grid(row=2, column=1, columnspan=2, sticky=(W, E))
        while not wait_for_net(paths['driver_pool'], paths['server_address']):
            self.var_base['net_stat'].set(0)
        self.var_base['net_stat'].set(1)
        get_packages()
        self.no_net.grid_forget()
        self.drivers_check.grid(row=2, column=0, sticky=(W, E))
        return 1

    def go(self):
        global packages
        # package = ''
        if self.var_base['rename_check'].get() == 1 and self.var_base['new_hostname'].get() == '':
            messagebox.showerror('No hostname', 'You did not input a hostname')
            return
        if self.var_base['drivers_check'].get() == 1:
            if self.var_base['release'].get() == '':
                messagebox.showerror('No selection', 'You did not select anything')
                return
            project = self.var_base['project'].get()  # get project
            platform = get_platform()[self.var_base['project'].get()]  # get platform
            drivers_package = self.var_base['release'].get()  # get kit release
            package = packages['_'.join((project, platform, drivers_package))]
        self.master.iconify()
        worker = WorkerChild(self.master, self.var_base['drivers_check'].get(), package,
                             self.var_base['rename_check'].get(), self.var_base['new_hostname'].get())


class DriversSelect:
    def __init__(self, master, package):
        self.help_text = {'project': 'Selected project',
                          'platform': 'Detected platform',
                          'bkc_release': 'BKC package release',
                          'toggle_all': 'Toggle all drivers',
                          'driver_check': 'Select to install driver',
                          'driver_name': 'Driver name',
                          'driver_version': 'Driver version',
                          'manual': 'Manual installation required, click to open driver path',
                          'go': 'Start'}
        self.master = master
        self.drivers = package['drivers']

        self.package = package
        # self.style = ttk.Style()
        # self.style.theme_use('winnative')

        self.baseframe = MyFrame(self.master)

        self.mainframe = MyFrame(self.baseframe)
        self.mainframe.grid(row=0, column=0, sticky=(N, W, E, S))

        self.status_bar = StatusBar(self.baseframe)
        self.status_bar.baseframe.grid(row=1, column=0, sticky=(W, E))

        ttk.Label(self.mainframe).grid(row=0, column=0)

        self.project_label = ttk.Label(self.mainframe, text='Project: %s' % self.package['project'])
        self.platform_label = ttk.Label(self.mainframe, text='platform: %s' % self.package['platform'])
        self.package_label = ttk.Label(self.mainframe, text='BKC release: %s' % self.package['release'])

        self.project_label.bind('<Enter>', lambda event: self.status_bar.show_help(event, self.help_text['project']))
        self.platform_label.bind('<Enter>', lambda event: self.status_bar.show_help(event, self.help_text['platform']))
        self.package_label.bind('<Enter>', lambda event: self.status_bar.show_help(event, self.help_text['bkc_release']))
        self.project_label.bind('<Leave>', self.status_bar.clear_help)
        self.platform_label.bind('<Leave>', self.status_bar.clear_help)
        self.package_label.bind('<Leave>', self.status_bar.clear_help)

        self.project_label.grid(row=1, column=0, sticky=W)
        self.platform_label.grid(row=2, column=0, sticky=W)
        self.package_label.grid(row=3, column=0, sticky=W)

        ttk.Label(self.mainframe).grid(row=4, column=0)

        self.driverframe = ScrollableBox(self.mainframe, text='Driver selection')
        self.driverframe.baseframe.grid(row=5, column=0, columnspan=2, sticky=(W, E))
        self.populate_drivers(self.driverframe.mainframe)
        self.driverframe.update()

        center_window(self.master.master, self.driverframe.mainframe.winfo_reqwidth()+43, int(self.master.winfo_screenheight())*0.6)

    def populate_drivers(self, frame):

        def toggle_all():
            if toggle_all_check.get():
                for _name in self.package['drivers']:
                    if _name.upper() not in manual_drivers and self.package['drivers'][_name]['manual']:
                        self.package['drivers'][_name]['todo'].set(1)
            else:
                for _name in self.package['drivers']:
                    self.package['drivers'][_name]['todo'].set(0)

        toggle_all_check = IntVar()
        must_drivers = ['GFX', 'CHIPSET']
        manual_drivers = ['LAN']
        y = 0
        toggle_all_button = ttk.Checkbutton(frame, text='Toggle all', variable=toggle_all_check, command=toggle_all)
        toggle_all_button.grid(row=y, column=0, sticky=(N, W))
        toggle_all_button.bind('<Enter>', lambda event: self.status_bar.show_help(event, self.help_text['toggle_all']))
        toggle_all_button.bind('<Leave>', self.status_bar.clear_help)
        y += 1
        ttk.Separator(frame, orient=HORIZONTAL).grid(row=y, column=0, columnspan=3, sticky=(W, E))
        y += 1

        sorted_names = sorted(self.package['drivers'], key=str.lower)
        for name in sorted_names:
            self.package['drivers'][name]['todo'] = IntVar()
            driver_check = ttk.Checkbutton(frame, text=name, variable=self.package['drivers'][name]['todo'])
            driver_check.grid(row=y, column=0, sticky=W)
            driver_check.bind('<Enter>', lambda event: self.status_bar.show_help(event, self.help_text['driver_check']))
            driver_check.bind('<Leave>', self.status_bar.clear_help)
            driver_version = ttk.Label(frame, text=self.package['drivers'][name]['version'])
            driver_version.grid(row=y, column=1, sticky=W)
            driver_version.bind('<Enter>', lambda event: self.status_bar.show_help(event, self.help_text['driver_version']))
            driver_version.bind('<Leave>', self.status_bar.clear_help)

            if self.package['drivers'][name]['manual'] == 0 or name.upper() in manual_drivers:
                driver_path = os.path.join(paths['driver_pool'], name, self.package['drivers'][name]['version'])
                open_path_button = ttk.Button(frame, text='Manual installation',
                                              command=lambda z=driver_path: subprocess.Popen(['explorer', z], shell=True))
                open_path_button.grid(row=y, column=2, sticky=W)
                open_path_button.bind('<Enter>', lambda event: self.status_bar.show_help(event, self.help_text['manual']))
                open_path_button.bind('<Leave>', self.status_bar.clear_help)
                self.package['drivers'][name]['todo'].set(0)
                driver_check.state(['disabled'])
            elif self.package['drivers'][name]['manual'] > 0:
                ttk.Label(frame, text='Ready').grid(row=y, column=2, sticky=W)
                if name.upper() in must_drivers:
                    self.package['drivers'][name]['todo'].set(1)
                else:
                    self.package['drivers'][name]['todo'].set(0)
            y += 1
            ttk.Separator(frame, orient=HORIZONTAL).grid(row=y, column=0, columnspan=3, sticky=(W, E))
            y += 1

    def get_drivers(self):
        todo_drivers = {}
        for driver in self.drivers:
            if self.drivers[driver]['todo'].get():
                todo_drivers[driver] = self.drivers[driver]
                todo_drivers[driver]['todo'] = todo_drivers[driver]['todo'].get()
        return todo_drivers


class WorkingLog:
    def __init__(self, master):
        self.var_base = {'total_progress': IntVar()}

        self.master = master
        self.baseframe = MyFrame(self.master, padding='3 3 12 12')

        self.mainframe = MyFrame(self.baseframe, padding='3 3 12 12')
        self.mainframe.grid(row=0, column=0, sticky=(N, W, E, S))

        # self.status_bar = StatusBar(self.baseframe)
        # self.status_bar.baseframe.grid(row=1, column=0, sticky=(W, E))

        ttk.Label(self.mainframe, text="Please wait, working...").grid(row=0, column=0)
        self.total_progress_bar = ttk.Progressbar(self.mainframe, orient=HORIZONTAL, length=80, mode='determinate', variable=self.var_base['total_progress'])
        self.total_progress_bar.grid(row=1, column=0, sticky=(W, E))

        self.log_listbox = Listbox(self.mainframe, height=20, width=80)
        self.log_listbox.grid(row=2, column=0, sticky=(N, W, E, S))

        # self.scroll_y = ttk.Scrollbar(self.mainframe, orient=VERTICAL, command=self.log_listbox.yview)
        # self.scroll_y.grid(row=2, column=1, sticky=(N, S))
        # self.log_listbox['yscrollcommand'] = self.scroll_y.set

    def log_out(self, text):
        self.log_listbox.insert(END, text)
        self.log_listbox.see(END)

    def set_progress(self, prog):
        self.var_base['total_progress'].set(prog)


class WorkerChild:
    def __init__(self, master, do_drivers, package, do_rename, new_hostname):
        self.to_do = {'drivers': package,
                      'rename': new_hostname
                      }
        self.package = package
        self.master = master
        # self.style = ttk.Style()
        # self.style.theme_use('winnative')

        self.child = Toplevel()
        self.child.focus_force()
        self.child.title("Working")
        self.child.grid_columnconfigure(0, weight=1)
        self.child.grid_rowconfigure(0, weight=1)
        self.child.resizable(0, 0)
        self.child.protocol("WM_DELETE_WINDOW", self.child_quit)

        self.baseframe = MyFrame(self.child, padding='3 3 12 12')
        self.baseframe.grid(row=0, column=0, sticky=(N, W, E, S))

        self.go_button = ttk.Button(self.baseframe, text='Go', command=lambda: pool.apply_async(self.go))
        self.decide(do_drivers, do_rename)

    def decide(self, do_drivers, do_rename):
        #  run rename script only
        if do_rename and not do_drivers:
            go_thread = pool.apply_async(self.go)
        #  run drivers script only
        elif do_drivers and not do_rename:
            self.driver_select = DriversSelect(self.baseframe, self.package)
            self.child.bind("<MouseWheel>", self.driver_select.driverframe.wheel)
            self.driver_select.baseframe.grid(row=0, column=0, columnspan=2, sticky=(N, W, E, S))
            self.go_button.grid(row=1, column=1, sticky=(E, S))
        # run both rename and drivers script
        elif do_rename and do_rename:
            self.driver_select = DriversSelect(self.baseframe, self.package)
            self.child.bind("<MouseWheel>", self.driver_select.driverframe.wheel)
            self.driver_select.baseframe.grid(row=0, column=0, columnspan=2, sticky=(N, W, E, S))
            self.go_button.grid(row=1, column=1, sticky=(E, S))

    def child_quit(self):
        self.child.destroy()
        self.master.deiconify()

    def go(self):

        self.child.unbind_all("<MouseWheel>")

        for widget in self.baseframe.winfo_children():
            widget.destroy()
        self.child.update_idletasks()
        self.log = WorkingLog(self.baseframe)
        self.log.baseframe.grid(row=0, column=0, sticky=(N, W, E, S))

        if self.to_do['rename']:
            while not renamer(self.to_do['rename'], self.log.log_out):
                pass

        if self.to_do['drivers']:
            while not driver_installer(os.path.join(paths['driver_pool'], paths[my_platform_type]), self.driver_select.get_drivers(), self.log.log_out, self.log.set_progress):
                pass

        if messagebox.askyesno('All Done', 'Finished installing all driver\'s \na reboot is required, would you like to reboot now?'):
            pool.terminate()
            restart(5)
            self.child.destroy()
            self.master.destroy()
            sys.stderr.close()
            sys.stdout.close()
        else:
            pool.terminate()
            self.child.destroy()
            self.master.destroy()
            sys.stderr.close()
            sys.stdout.close()
        return


class StatusBar:
    def __init__(self, master):
        self.var_base = {'help': StringVar()}
        self.baseframe = MyFrame(master)
        self.help = ttk.Label(self.baseframe, textvariable=self.var_base['help'], relief=SUNKEN)
        self.help.grid(row=0, column=0, sticky=(W, E))

    def show_help(self, event, text):
        """
        Show help about widget
        :param event: mouse hover event
        :param text: text to show
        :return: none
        """
        self.var_base['help'].set(text)

    def clear_help(self, event):
        """
        Clear help text when mouse leaves widget area
        :param event: mouse leave event
        :return: none
        """
        self.var_base['help'].set('')


class ScrollableBox:
    def __init__(self, master, **kw):
        self.screen_res = {'x': int(master.winfo_screenwidth()), 'y': int(master.winfo_screenheight())}
        self.master = master
        # self.master.master.master.master.bind("<MouseWheel>", self.wheel)
        self.baseframe = ttk.Labelframe(self.master, **kw)
        self.baseframe.grid_columnconfigure(0, weight=1)
        self.baseframe.grid_rowconfigure(0, weight=1)
        self.canvas = Canvas(self.baseframe)

        self.d_scroll_y = ttk.Scrollbar(self.baseframe, orient=VERTICAL, command=self.canvas.yview)
        self.x_scroll_x = ttk.Scrollbar(self.baseframe, orient=HORIZONTAL, command=self.canvas.xview)

        self.canvas.grid(row=0, column=0, sticky=(N, W, E, S))
        self.d_scroll_y.grid(row=0, column=1, sticky=(N, S))
        # self.x_scroll_x.grid(row=1, column=0, sticky=(W, E))

        self.canvas.config(yscrollcommand=self.d_scroll_y.set, xscrollcommand=self.x_scroll_x.set)
        self.mainframe = ttk.Frame(self.canvas)

    def update(self):
        self.master.update_idletasks()
        width = self.mainframe.winfo_reqwidth()
        height = self.mainframe.winfo_reqheight()
        self.canvas.config(width=width, height=self.screen_res['y']*0.46, scrollregion=(0, 0, width, height))
        self.canvas.create_window(width/2, height/2, anchor=CENTER, window=self.mainframe)
        self.master.update_idletasks()

    def wheel(self, event):
        """
            Mouse wheel binding for drivers canvas
            :param event: event to check
            :return: none
            """
        if event.num == 5 or event.delta == -120:
            self.canvas.yview('scroll', 1, 'units')
        if event.num == 4 or event.delta == 120:
            self.canvas.yview('scroll', -1, 'units')


class MyFrame(ttk.Frame):
    def __init__(self, master, **kw):
        ttk.Frame.__init__(self, master, **kw)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        # self.style = ttk.Style()

    # def change_style(self, **kw):
    #     self.style.configure('My.TFrame', **kw)
    #     self['style'] = 'My.TFrame'


def center_window(window, w=1, h=1):
    """
    Place specified window in the middle of the screen
    :param window: window to center/resize
    :param w: width to resize to
    :param h: height to resize to
    :return: none
    """
    # get screen width and height
    ws = window.winfo_screenwidth()
    hs = window.winfo_screenheight()
    # calculate position x, y
    xx = (ws/2) - (w/2)
    yy = (hs/2) - (h/2)
    window.geometry('%dx%d+%d+%d' % (w, h, xx, yy))
    return


def get_packages():
    global packages, my_platform_type
    for package in os.listdir(os.path.join(paths['driver_pool'], paths[my_platform_type], 'MAP_files')):
        with open(os.path.join(paths['driver_pool'], paths[my_platform_type], 'MAP_files', package), 'r') as in_package:
            packages[package.strip('.json')] = json.load(in_package)


def logger():
    # my_info = subprocess.check_output('systeminfo')
    my_info = subprocess.Popen(['systeminfo'], shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    my_info.wait()
    out = my_info.stdout.read()

    error_out.flush()
    error_out.write(out.decode('utf-8'))
    error_out.write('\n-----------------------------------\n')
    log_out.flush()
    log_out.write(out.decode('utf-8'))
    log_out.write('\n-----------------------------------\n')
    return


def main():
    """
    Main function
    :return: none
    """
    def root_quit():
        """
        Destroy mainloop and terminate tread pool
        :return: none
        """
        pool.terminate()
        root_tk.destroy()
        sys.stderr.close()
        sys.stdout.close()
        return 1

    sys.stderr = error_out
    sys.stdout = log_out

    root_tk = Tk()
    root_tk.title('IT Spider')
    root_tk.option_add('*tearOff', FALSE)
    root_tk.iconbitmap(r"./img\\tachk.ico")
    root_tk.grid_columnconfigure(0, weight=1)
    root_tk.grid_rowconfigure(0, weight=1)
    root_tk.resizable(0, 0)
    root_tk.protocol("WM_DELETE_WINDOW", root_quit)

    app = MainApplication(root_tk)
    app.baseframe.grid(row=0, column=0, sticky=(N, W, E, S))

    center_window(root_tk, 420, 300)
    logger_thread = pool.apply_async(logger)
    # check if User Account Control is active
    if str(reg_read('HKLM', 'SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System', 'EnableLUA')) == '1':
        messagebox.showwarning('UAC enabled', 'UAC is enabled\nIt is recommended to disable UAC for the program to work properly'
                               '\nCheck the help file under "Advanced-Disable UAC" for instructions on how to disable UAC\n'
                               'or consult your Admin')
    root_tk.mainloop()

if __name__ == '__main__':
    main()
