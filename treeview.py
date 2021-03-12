from modules import *


class FileTree(ttk.Frame):
    """
        LeftPanel ... containing treeView, leftButtonFrame, Buttons
    """

    def __init__(self, master=None, textbox=None, opencommand=None, path=os.path.expanduser('~')):
        super().__init__(master)
        self.destinationItem = None
        self.sourceItem = None
        self.tree = ttk.Treeview(self)
        yscroll, xscroll = ttk.Scrollbar(self, command=self.tree.yview), \
                           ttk.Scrollbar(self, command=self.tree.xview, orient='horizontal')
        yscroll.pack(side='right', fill='y')
        xscroll.pack(side='bottom', fill='x')
        self.tree['yscrollcommand'] = yscroll.set
        self.tree['xscrollcommand'] = xscroll.set
        self.dir = ''
        self.selected = []
        self.master = master
        self.textbox = textbox
        self.path = str(path)
        self.opencommand = opencommand
        topframe = ttk.Frame(self)
        topframe.pack(side='top', anchor='nw')
        self.actioncombobox = ttk.Combobox(topframe, state='readonly',
                                           values=['Parent Directory', 'New File',
                                                   'New Directory', 'Refresh'])
        self.actioncombobox.set('Parent Directory')
        self.actioncombobox.pack(anchor='nw', side='left')
        ttk.Button(topframe, text='>>', command=self.do_action).pack(side='left', anchor='nw')

        self.pack(side='left', fill='both', expand=1)
        self.initUI()
        self.tree.tag_configure('row', background='black', foreground='white')
        self.tree.tag_configure('folder', background='black', foreground='yellow')
        self.tree.tag_configure('subfolder', background='black', foreground='#448dc4')

    def do_action(self):
        action = self.actioncombobox.get()
        if action == 'Parent Directory':
            self.change_parent_dir()
        elif action == 'New File':
            self.new_file()
        elif action == 'New Directory':
            self.new_dir()
        elif action == 'Refresh':
            self.initUI()

    def new_file(self):
        _filename = simpledialog.askstring('New file', 'File Name:')
        file_abspath = os.path.join(self.path, _filename)
        if os.path.exists(file_abspath):
            if messagebox.askyesno('Confirm', 'This file already exists, do you want to overwrite?'):
                with open(file_abspath, 'w') as f:
                    f.write('')
                self.opencommand(file_abspath)
                return
            return
        else:
            with open(file_abspath, 'w') as f:
                f.write('')
            self.opencommand(file_abspath)
            return

    def new_dir(self):
        dirname = simpledialog.askstring('New directory', 'Directory Name:')
        dir_abspath = os.path.join(self.path, dirname)
        try:
            os.mkdir(dir_abspath)
        except FileExistsError:
            if messagebox.askyesno('Confirm', 'This directory already exists, do you want to overwrite?'):
                shutil.rmtree(dir_abspath, ignore_errors=True)
                os.mkdir(dir_abspath)
            else:
                return

    def initUI(self, _=None):
        path = os.path.abspath(__file__)
        path_list = path.split('/')[:-1]
        for item in path_list:
            self.dir += item + '/'

        self.tree.delete(*self.tree.get_children())
        self.tree.bind("<Double-1>", self.on_double_click_treeview)
        self.tree.bind('<Alt-Right>', self.change_to_textbox)
        self.tree.heading('#0', text='Directory Structure')
        self.tree.update()

        abspath = os.path.abspath(path)
        root_node = self.tree.insert('', 'end', text=abspath, open=True, tags='folder')
        self.process_directory(root_node, abspath)

        self.tree.pack(side='bottom', expand=True, fill='both', anchor='nw')

        self.refreshTree()

    def change_to_textbox(self, _=None):
        if self.textbox:
            self.textbox.focus_set()

    def change_parent_dir(self):
        self.path = str(Path(os.path.abspath(self.path)).parent)
        self.refreshTree()

    def process_directory(self, parent, path):
        try:
            ls = []
            for p in os.listdir(path):
                abspath = os.path.join(path, p)
                isdir = os.path.isdir(abspath)

                if isdir:
                    item = '\u2514 ' + str(p)
                    ls.append(item)
                    continue

                else:
                    item = str(p)
                    ls.append(item)
            ls.sort()

            for items in ls:
                if items.startswith('\u2514'):
                    self.tree.insert(parent, 'end', text=str(items), open=False, tags='subfolder')
                else:
                    self.tree.insert(parent, 'end', text=str(items), open=False, tags='row')

        except Exception:
            return

    def on_double_click_treeview(self, event):
        item = self.tree.identify('item', event.x, event.y)
        if self.tree.item(item, "text").startswith('\u2514'):
            root = self.path
            sub = self.tree.item(item, "text").split()[1]
            dir = os.path.join(root, sub)
            self.path = dir
            self.refreshTree()

        else:
            file = self.tree.item(item, "text")
            dir = self.path
            dir = self.checkPath(dir)
            _filename = dir + '/' + file
            self.selected = []
            try:
                self.opencommand(_filename)
            except Exception:
                pass

            self.tree.update()
            self.textbox.mark_set("insert", "1.0")
            self.textbox.focus_set()

            # workaround 
            # step 2
            self.refreshTree()
            self.tree.update()

        self.refreshTree()

    @staticmethod
    def checkPath(path):
        if '\\' in path:
            path = path.replace('\\', '/')
        return path

    def refreshTree(self):
        for i in self.tree.get_children():
            self.tree.delete(i)
        path = self.path
        abspath = os.path.abspath(path)
        root_node = self.tree.insert('', 'end', text=abspath, open=True, tags='folder')
        self.process_directory(root_node, abspath)
