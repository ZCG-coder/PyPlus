#!/usr/local/bin/python3.7
# coding: utf-8
"""
+ =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-= +
| pyplus.py -- the editor's ONLY file                 |
| The somehow-professional editor                     |
| It's extremely small! (around 80 kB)                |
| You can visit my site for more details!             |
| +---------------------------------------------+     |
| | http://ZCG-coder.github.io/NWSOFT/PyPlusWeb |     |
| +---------------------------------------------+     |
| You can also contribute it on github!               |
| Note: Some parts are adapted from stack overflow.   |
+ =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-= +
Also, it's cross-compatible!
"""
# These modules are from the base directory
from console import *
from customenotebook import *
from functions import *
from hexview import *
from tktext import *
from treeview import *

os.chdir(APPDIR)
logger = logging.getLogger(__name__)
logging.basicConfig(filename='pyplus.log', filemode='w', level=logging.DEBUG)

logger.info(f'Tkinter version: {tk.TkVersion}')
logger.debug('All modules imported')


class Document:
    """Helper class, for the editor"""

    def __init__(self, _, TextWidget, FileDir):
        self.file_dir = FileDir
        self.textbox = TextWidget


class Editor:
    """The editor class."""

    def __init__(self):
        """The editor object, the entire thing that goes in the
window.
Lacks these MacOS support:
* The file selector does not work.
"""
        try:
            self.settings_class = Settings()
            self.file_setting_class = Filetype()
            self.linter_setting_class = Linter()
            self.cmd_setting_class = RunCommand()
            self.theme = self.settings_class.get_settings('theme')
            logger.debug('Settings loaded')

            self.master = tk.Tk()
            if OSX:
                PyTouchBar.prepare_tk_windows(self.master)
                open_button = PyTouchBar.TouchBarItems.Button(title='Open File', action=self._open)
                save_as_button = PyTouchBar.TouchBarItems.Button(title='Save As', action=self.save_as)
                space = PyTouchBar.TouchBarItems.Space.Flexible()
                run_button = PyTouchBar.TouchBarItems.Button(title='Run', action=self.run)
                PyTouchBar.set_touchbar([open_button, save_as_button, space, run_button])
            self.master.focus_force()
            self.master.geometry('900x600')
            ttkthemes.ThemedStyle(self.master).set_theme(self.theme)
            self.master.title('PyPlus')
            self.master.iconphoto(True, tk.PhotoImage(data=ICON))
            # Base64 image, this probably decreases the repo size.
            logger.debug('Theme loaded')

            self.filetypes = self.settings_class.get_settings('file_type')

            self.tabs = {}

            self.nb = ClosableNotebook(self.master, self.close_tab)
            self.nb.bind('<B1-Motion>', self.move_tab)
            self.nb.pack(expand=1, fill='both')
            self.nb.enable_traversal()

            self.master.protocol(
                'WM_DELETE_WINDOW', lambda: self.exit(force=False)
            )  # When the window is closed, or quit from Mac, do exit action

            menubar = tk.Menu(self.master)
            # Name can be apple only, don't really know why!
            app_menu = tk.Menu(menubar, name='apple', tearoff=0)

            app_menu.add_command(label='About PyPlus', command=self._version)
            preferences = tk.Menu(app_menu, tearoff=0)
            preferences.add_command(
                label="General Settings",
                command=lambda: self.open_file(APPDIR + '/Settings/general-settings'
                                                        '.json'))
            preferences.add_command(
                label="Lexer Settings",
                command=lambda: self.open_file(APPDIR + '/Settings/lexer-settings'
                                                        '.json'))
            preferences.add_command(
                label="Linter Settings",
                command=lambda: self.open_file(APPDIR + '/Settings/linter-settings'
                                                        '.json'))
            preferences.add_command(
                label="Run Command Settings",
                command=lambda: self.open_file(APPDIR + '/Settings/cmd-settings'
                                                        '.json'))
            app_menu.add_cascade(label="Preferences", menu=preferences)
            app_menu.add_separator()
            app_menu.add_command(label='Exit Editor', command=self.exit)
            app_menu.add_command(label='Restart app', command=self.restart)
            app_menu.add_command(label='Check for updates',
                                 command=self.check_updates)

            filemenu = tk.Menu(menubar, tearoff=0)
            filemenu.add_command(label='New Tab',
                                 command=self.new_file,
                                 accelerator=f'{MAIN_KEY}-n')
            filemenu.add_command(label='Open File',
                                 command=self.open_file,
                                 accelerator=f'{MAIN_KEY}-o')
            filemenu.add_command(label='Save Copy to...',
                                 command=self.save_as,
                                 accelerator=f'{MAIN_KEY}-Shift-S')
            filemenu.add_command(label='Close Tab',
                                 command=self.close_tab,
                                 accelerator=f'{MAIN_KEY}-w')
            filemenu.add_command(label='Reload from disk',
                                 command=self.reload,
                                 accelerator=f'{MAIN_KEY}-r')
            filemenu.add_separator()
            filemenu.add_command(label='Startup scren', command=self.start_screen)

            editmenu = tk.Menu(menubar, tearoff=0)
            editmenu.add_command(label='Undo',
                                 command=self.undo,
                                 accelerator=f'{MAIN_KEY}-z')
            editmenu.add_command(label='Redo',
                                 command=self.redo,
                                 accelerator=f'{MAIN_KEY}-Shift-z')
            editmenu.add_separator()
            editmenu.add_command(label='Cut',
                                 command=self.cut,
                                 accelerator=f'{MAIN_KEY}-x')
            editmenu.add_command(label='Copy',
                                 command=self.copy,
                                 accelerator=f'{MAIN_KEY}-c')
            editmenu.add_command(label='Paste',
                                 command=self.paste,
                                 accelerator=f'{MAIN_KEY}-v')
            editmenu.add_command(label='Delete Selected', command=self.delete)
            editmenu.add_command(label='Select All',
                                 command=self.select_all,
                                 accelerator=f'{MAIN_KEY}-a')

            self.codemenu = tk.Menu(menubar, tearoff=0)
            self.codemenu.add_command(label='Indent',
                                      command=lambda: self.indent('indent'),
                                      accelerator='Alt-Tab')
            self.codemenu.add_command(label='Unident',
                                      command=lambda: self.indent('unindent'),
                                      accelerator='Alt-Shift-Tab')
            self.codemenu.add_separator()
            self.codemenu.add_command(label='Run',
                                      command=self.run,
                                      accelerator=f'{MAIN_KEY}-b')
            self.codemenu.add_command(label='Lint', command=self.lint_source)
            self.codemenu.add_command(label='Auto-format', command=self.autopep)
            self.codemenu.add_separator()
            self.codemenu.add_command(label='Find and replace',
                                      command=self.search,
                                      accelerator=f'{MAIN_KEY}-f')
            self.codemenu.add_separator()
            self.codemenu.add_command(label='Open Python Shell',
                                      command=self.open_shell)
            self.codemenu.add_command(label='Open System Shell',
                                      command=self.system_shell)

            navmenu = tk.Menu(menubar, tearoff=0)
            navmenu.add_command(label='Go to ...',
                                command=self.goto,
                                accelerator=f'{MAIN_KEY}-Shift-N')
            navmenu.add_command(label='-1 char', command=self.nav_1cb)
            navmenu.add_command(label='+1 char', command=self.nav_1cf)
            gitmenu = tk.Menu(menubar, tearoff=0)
            gitmenu.add_command(label='Initialize',
                                command=lambda: self.git('init'))
            gitmenu.add_command(label='Add all',
                                command=lambda: self.git('addall'))
            gitmenu.add_command(label='Add selected',
                                command=lambda: self.git('addsel'))
            gitmenu.add_command(label='Commit', command=lambda: self.git('commit'))
            gitmenu.add_command(label='Clone', command=lambda: self.git('clone'))
            gitmenu.add_command(label='Other', command=lambda: self.git('other'))

            menubar.add_cascade(label='App', menu=app_menu)  # App menu
            menubar.add_cascade(label='File', menu=filemenu)
            menubar.add_cascade(label='Edit', menu=editmenu)
            menubar.add_cascade(label='Code', menu=self.codemenu)
            menubar.add_cascade(label='Navigate', menu=navmenu)
            menubar.add_cascade(label='Git', menu=gitmenu)
            self.master.config(menu=menubar)
            logger.debug('Menu created')
            self.right_click_menu = tk.Menu(self.master, tearoff=0)
            self.right_click_menu.add_command(label='Undo', command=self.undo)
            self.right_click_menu.add_command(label='Redo', command=self.redo)
            self.right_click_menu.add_separator()
            self.right_click_menu.add_command(label='Cut', command=self.cut)
            self.right_click_menu.add_command(label='Copy', command=self.copy)
            self.right_click_menu.add_command(label='Paste', command=self.paste)
            self.right_click_menu.add_command(label='Delete', command=self.delete)
            self.right_click_menu.add_separator()
            self.right_click_menu.add_command(label='Select All',
                                              command=self.select_all)
            logger.debug('Right-click menu created')

            self.tab_right_click_menu = tk.Menu(self.master, tearoff=0)
            self.tab_right_click_menu.add_command(label='New Tab',
                                                  command=self.new_file)
            self.tab_right_click_menu.add_command(label='Close Tab',
                                                  command=self.close_tab)
            logger.debug('Tab right-click menu created')

            self.nb.bind(('<Button-2>' if OSX else '<Button-3>'),
                         self.right_click_tab)

            # Keyboard bindings
            self.master.bind(f'<{MAIN_KEY}-w>', self.close_tab)
            self.master.bind(f'<{MAIN_KEY}-o>', self._open)
            self.master.bind(f'<{MAIN_KEY}-r>', self.reload)
            self.master.bind(f'<{MAIN_KEY}-b>', self.run)
            self.master.bind(f'<{MAIN_KEY}-f>', self.search)
            self.master.bind(f'<{MAIN_KEY}-n>', self.new_file)
            self.master.bind(f'<{MAIN_KEY}-N>', self.goto)
            self.master.bind(f'<{MAIN_KEY}-S>', self.save_as)
            self.master.bind('Alt-Shift-Tab>',
                             lambda _=None: self.indent('unindent'))
            self.master.bind('<Alt-Tab>', lambda _=None: self.indent('indent'))
            logger.debug('Bindings created')

            self.master.bind("<<MouseEvent>>", self.mouse)
            self.master.event_add("<<MouseEvent>>", "<ButtonRelease>")
            for x in ['"', "'", '(', '[', '{']:
                self.master.bind(x, self.autoinsert)
            self.start_screen()
            self.master.focus_force()
            self.master.mainloop()  # This line can be here only
        except Exception:
            logger.exception('Error when initializing:')

    def start_screen(self):
        first_tab = tk.Canvas(self.nb, background='white')
        img = tk.PhotoImage(data=ICON)
        first_tab.create_text(10,
                              10,
                              anchor='nw',
                              text='Welcome to PyPlus!',
                              font='Arial 50')
        first_tab.create_image(0, 0, anchor='nw', image=img)
        label1 = ttk.Label(first_tab,
                           text='Open file',
                           foreground='blue',
                           background='white')
        label2 = ttk.Label(first_tab,
                           text='New tab',
                           foreground='blue',
                           background='white')
        label3 = ttk.Label(first_tab,
                           text='Exit',
                           foreground='blue',
                           background='white')
        label1.bind('<Button>', self._open)
        label2.bind('<Button>', self.new_file)
        label3.bind('<Button>', self.exit)

        first_tab.create_window(50, 100, window=label1, anchor='nw')
        first_tab.create_window(50, 140, window=label2, anchor='nw')
        first_tab.create_window(50, 180, window=label3, anchor='nw')
        self.nb.add(first_tab, text='Start')
        logger.debug('Start screen created')

    def create_text_widget(self, frame):
        """Creates a text widget in a frame."""

        def tab(_=None):
            self.tabs[self.get_tab()].textbox.insert(
                'insert', ' ' * 4)  # Convert tabs to spaces
            # Quit quickly, before a char is being inserted.
            return 'break'

        textframe = EnhancedTextFrame(
            frame)  # The one with line numbers and a nice dark theme
        textframe.pack(fill='both', expand=1, side='right')

        textbox = textframe.text  # text widget
        textbox.frame = frame  # The text will be packed into the frame.
        textbox.lexer = PythonLexer()
        textbox.lint_cmd = None
        textbox.bind('<Return>', self.autoindent)
        textbox.bind("<<KeyEvent>>", self.key)
        textbox.event_add("<<KeyEvent>>", "<KeyRelease>")
        textbox.bind('<Tab>', tab)
        textbox.statusbar = ttk.Label(frame,
                                      text='PyPlus',
                                      justify='right',
                                      anchor='e')
        textbox.statusbar.pack(side='bottom', fill='x', anchor='nw')
        textbox.bind(('<Button-2>' if OSX else '<Button-3>'),
                     self.right_click)
        textbox.focus_set()
        logger.debug('Textbox created')
        return textbox

    def settitle(self, _=None):
        try:
            if len(self.tabs) == 0:
                self.master.title('PyPlus -- No file open')
                logger.debug('settitle: No file open')
                return "break"
            self.master.title(
                f'PyPlus -- {self.tabs[self.get_tab()].file_dir}')
            logger.debug('settitle: OK')
            return 'break'
        except Exception:
            self.master.title(f'PyPlus')
            return 'break'

    def key(self, _=None):
        """Event when a key is pressed."""
        try:
            currtext = self.tabs[self.get_tab()].textbox
            self.create_tags()
            self.recolorize()
            currtext.statusbar.config(
                text=f'PyPlus | file {self.nb.tab(self.get_tab())["text"]} |'
                     f' ln {int(float(currtext.index("insert")))}'
                     f' | col {str(int(currtext.index("insert").split(".")[1:][0]))}'
            )
            # Update statusbar and title bar
            self.settitle()
            # Auto-save
            self.save_file()
        except Exception:
            pass

    def mouse(self, _=None):
        """The action done when the mouse is clicked"""
        try:
            currtext = self.tabs[self.get_tab()].textbox
            currtext.statusbar.config(
                text=f'PyPlus | file {self.nb.tab(self.get_tab())["text"]} |'
                     f' ln {int(float(currtext.index("insert")))}'
                     f' | col {str(int(currtext.index("insert").split(".")[1:][0]))}'
            )
            # Update statusbar and title bar
            self.settitle()
        except Exception:
            pass

    def create_tags(self):
        """
The method creates the tags associated with each distinct style element of the
source code 'dressing'
"""
        if len(self.tabs) == 0:
            return
        currtext = self.tabs[self.get_tab()].textbox
        bold_font = font.Font(currtext, currtext.cget("font"))
        bold_font.configure(weight=font.BOLD)
        italic_font = font.Font(currtext, currtext.cget("font"))
        italic_font.configure(slant=font.ITALIC)
        bold_italic_font = font.Font(currtext, currtext.cget("font"))
        bold_italic_font.configure(weight=font.BOLD, slant=font.ITALIC)
        style = get_style_by_name(self.settings_class.get_settings('pygments'))

        for ttype, ndef in style:
            tag_font = None

            if ndef['bold'] and ndef['italic']:
                tag_font = bold_italic_font
            elif ndef['bold']:
                tag_font = bold_font
            elif ndef['italic']:
                tag_font = italic_font

            if ndef['color']:
                foreground = "#%s" % ndef['color']
            else:
                foreground = None

            currtext.tag_configure(str(ttype),
                                   foreground=foreground,
                                   font=tag_font)

    def recolorize(self):
        """
This method colors and styles the prepared tags
"""
        if len(self.tabs) == 0:
            return
        currtext = self.tabs[self.get_tab()].textbox
        _code = currtext.get("1.0", "end-1c")
        tokensource = currtext.lexer.get_tokens(_code)
        start_line = 1
        start_index = 0
        end_line = 1
        end_index = 0

        for ttype, value in tokensource:
            if "\n" in value:
                end_line += value.count("\n")
                end_index = len(value.rsplit("\n", 1)[1])
            else:
                end_index += len(value)

            if value not in (" ", "\n"):
                index1 = f"{start_line}.{start_index}"
                index2 = f"{end_line}.{end_index}"

                for tagname in currtext.tag_names(index1):
                    if tagname != 'sel':
                        currtext.tag_remove(tagname, index1, index2)

                currtext.tag_add(str(ttype), index1, index2)

            start_line = end_line
            start_index = end_index
            currtext.tag_configure('sel', foreground='black')

    def open_file(self, file=''):
        """Opens a file
If a file is not provided, a messagebox'll
pop up to ask the user to select the path.
"""
        if not file:
            file_dir = (tkinter.filedialog.askopenfilename(
                master=self.master,
                initialdir='/',
                title='Select file',
                filetypes=self.filetypes))
        else:
            file_dir = file

        if file_dir:
            try:  # If the file is in binary, ask the user to open in Hex editor
                if is_binary_string(open(file_dir, 'rb').read()):
                    if messagebox.askyesno(
                            'Error', 'This file is in binary format, \n'
                                     'which this editor does not edit. \n'
                                     'Would you like to view it in Hex Editor?\n'):
                        logger.info('HexView: opened')
                        app = ttk.Frame(self.master)
                        app.focus_set()
                        window = HexView(app)
                        window.open(file_dir)
                        self.nb.add(app, text='Hex Viewer')
                        self.nb.select(app)
                        return
                    else:
                        logging.info('User pressed No.')
                        return
                file = open(file_dir)
                extens = file_dir.split('.')[-1]

                new_tab = ttk.Frame(self.nb)
                panedwin = ttk.Panedwindow(new_tab, orient='horizontal')
                panedwin.pack(fill='both', expand=1)
                textbox = self.create_text_widget(new_tab)
                self.tabs[new_tab] = Document(new_tab,
                                              textbox,
                                              file_dir)
                self.nb.add(new_tab, text=os.path.basename(file_dir))
                self.nb.select(new_tab)

                # Puts the contents of the file into the text widget.
                currtext = self.tabs[new_tab].textbox
                tree = FileTree(new_tab, currtext, self.open_file, path=Path(file_dir).parent)
                panedwin.add(tree, weight=1)
                panedwin.add(textbox.master, weight=10)
                currtext.insert('end', file.read().replace('\t', ' ' * 4))
                # Inserts file content, replacing tabs with four spaces
                currtext.focus_set()
                self.mouse()
                currtext.lexer = self.file_setting_class.get_lexer_settings(
                    extens)
                currtext.lint_cmd = self.linter_setting_class.get_linter_settings(
                    extens)
                currtext.cmd = self.cmd_setting_class.get_command_settings(
                    extens)
                self.create_tags()
                self.recolorize()
                currtext.see('insert')
                currtext.focus_set()
                logging.info('File opened')
                return 'break'
            except Exception:
                logger.exception('Error when opening file:')

    def _open(self, _=None):
        """This method just prompts the user to open a file when C-O is pressed"""
        self.open_file()

    def save_as(self, _=None):
        if len(self.tabs) > 0:
            curr_tab = self.get_tab()
            file_dir = (tkinter.filedialog.asksaveasfilename(
                master=self.master,
                initialdir='/',
                title='Save As...',
                filetypes=self.filetypes))
            if not file_dir:
                self.close_tab()
                return
            if not os.access(file_dir, os.W_OK):
                messagebox.showerror('Error', 'File read only.')

            self.tabs[curr_tab].file_dir = file_dir
            self.nb.tab(curr_tab, text=os.path.basename(file_dir))
            file = open(file_dir, 'w')
            file.write(self.tabs[curr_tab].textbox.get(1.0, 'end'))
            file.close()
            self.settitle()
            self.reload()

    def save_file(self, _=None):
        """Saves an *existing* file"""
        try:
            curr_tab = self.get_tab()
            if self.tabs[curr_tab].file_dir == 'None':
                self.save_as()
                return
            if os.access(self.tabs[curr_tab].file_dir, os.W_OK):
                with open(self.tabs[curr_tab].file_dir, 'w') as file:
                    file.write(self.tabs[curr_tab].textbox.get(1.0,
                                                               'end').strip())
            else:
                messagebox.showerror('Error', 'File read only')
        except Exception:
            pass

    def new_file(self, _=None):
        """Creates a new tab(file)."""
        new_tab = ttk.Frame(self.nb)
        panedwin = ttk.Panedwindow(new_tab, orient='horizontal')
        panedwin.pack(fill='both', expand=1)
        textbox = self.create_text_widget(new_tab)
        self.tabs[new_tab] = Document(new_tab,
                                      textbox, 'None')
        filetree = FileTree(master=new_tab, textbox=textbox, opencommand=self.open_file)
        panedwin.add(filetree)
        panedwin.add(textbox.master)
        self.nb.add(new_tab, text='None')
        self.nb.select(new_tab)
        self.settitle()

    def copy(self):
        try:
            sel = self.tabs[self.get_tab()].textbox.get(
                tk.SEL_FIRST, tk.SEL_LAST)
            self.tabs[self.get_tab()].textbox.clipboard_clear()
            self.tabs[self.get_tab()].textbox.clipboard_append(sel)
        except Exception:
            pass

    def delete(self):
        try:
            self.tabs[self.get_tab()].textbox.delete(tk.SEL_FIRST, tk.SEL_LAST)
            self.key()
        except Exception:
            pass

    def cut(self, textbox=None):
        try:
            currtext = self.tabs[self.get_tab()].textbox
            sel = currtext.get(tk.SEL_FIRST, tk.SEL_LAST)
            textbox.clipboard_clear()
            textbox.clipboard_append(sel)
            currtext.delete(tk.SEL_FIRST, tk.SEL_LAST)
            self.key()
        except Exception:
            pass

    def paste(self):
        try:
            self.tabs[self.get_tab()].textbox.insert(
                tk.INSERT,
                self.tabs[self.get_tab()].textbox.clipboard_get().replace(
                    '\t', ' ' * 4))
        except Exception:
            pass

    def select_all(self, _=None):
        try:
            curr_tab = self.get_tab()
            self.tabs[curr_tab].textbox.tag_add(tk.SEL, '1.0', tk.END)
            self.tabs[curr_tab].textbox.mark_set(tk.INSERT, tk.END)
            self.tabs[curr_tab].textbox.see(tk.INSERT)
        except Exception:
            pass

    def run(self, _=None):
        """Runs the file
Steps:
1) Writes run code into the batch file.
2) Linux only: uses chmod to make the sh execuable
3) Runs the run file"""
        try:
            if WINDOWS:  # Windows
                with open(APPDIR + '/run.bat', 'w') as f:
                    f.write((RUN_BATCH.format(
                        dir=APPDIR,
                        file=self.tabs[self.get_tab()].file_dir,
                        cmd=self.tabs[self.get_tab()].textbox.cmd)))
                run_in_terminal('run.bat && del run.bat && exit', cwd=APPDIR)
            else:
                with open(APPDIR + '/run.sh', 'w') as f:
                    f.write((RUN_BATCH.format(
                        dir=APPDIR,
                        file=self.tabs[self.get_tab()].file_dir,
                        cmd=self.tabs[self.get_tab()].textbox.cmd,
                        script_dir=Path(
                            self.tabs[self.get_tab()].file_dir).parent)))
                run_in_terminal('chmod 700 run.sh && ./run.sh && rm run.sh && exit', cwd=APPDIR)
        except Exception:
            pass

    @staticmethod
    def system_shell():
        open_system_shell()

    def open_shell(self):
        root = tk.Toplevel()
        root.title('Python Shell')
        ttkthemes.ThemedStyle(root).set_theme(self.theme)
        main_window = Console(root, None, root.destroy)
        main_window.pack(fill=tk.BOTH, expand=True)
        root.mainloop()

    def autoinsert(self, event=None):
        """Auto-inserts a symbol
* ' -> ''
* " -> ""
* ( -> ()
* [ -> []
* { -> {}"""
        if len(self.tabs) == 0:
            return
        currtext = self.tabs[self.get_tab()].textbox
        # Strings
        if event.char not in ['(', '[', '{']:
            currtext.insert('insert', event.char)
            currtext.mark_set(
                'insert', '%d.%s' %
                          (int(float(currtext.index('insert'))),
                           str(int(currtext.index('insert').split('.')[1:][0]) - 1)))
            self.key()
        # Others
        elif event.char == '(':
            currtext.insert('insert', ')')
            currtext.mark_set(
                'insert', '%d.%s' %
                          (int(float(currtext.index('insert'))),
                           str(int(currtext.index('insert').split('.')[1:][0]) - 1)))
            return 'break'
        elif event.char == '[':
            currtext.insert('insert', ']')
            currtext.mark_set(
                'insert', '%d.%s' %
                          (int(float(currtext.index('insert'))),
                           str(int(currtext.index('insert').split('.')[1:][0]) - 1)))
            return 'break'
        elif event.char == '{':
            currtext.insert('insert', '}')
            currtext.mark_set(
                'insert', '%d.%s' %
                          (int(float(currtext.index('insert'))),
                           str(int(currtext.index('insert').split('.')[1:][0]) - 1)))
            return 'break'

    def autoindent(self, _=None):
        """Auto-indents the next line"""
        currtext = self.tabs[self.get_tab()].textbox
        indentation = ""
        lineindex = currtext.index("insert").split(".")[0]
        linetext = currtext.get(lineindex + ".0", lineindex + ".end")
        for character in linetext:
            if character in [" ", "\t"]:
                indentation += character
            else:
                break

        if linetext.endswith(":"):
            indentation += " " * 4
        if linetext.endswith("\\"):
            indentation += " " * 4
        if 'return' in linetext or 'break' in linetext:
            indentation = indentation[4:]
        if linetext.endswith('(') or linetext.endswith(
                ', ') or linetext.endswith(','):
            indentation += " " * 4

        currtext.insert(currtext.index("insert"), "\n" + indentation)
        self.key()
        return "break"

    def search(self, _=None):
        global case
        global regexp
        global start, end
        global starts
        if len(self.tabs) == 0:
            return
        case = 0
        regexp = 0
        start = tk.FIRST if not tk.SEL_FIRST else tk.SEL_FIRST
        end = tk.END if not tk.SEL_LAST else tk.SEL_LAST
        starts = []
        search_frame = ttk.Frame(self.tabs[self.get_tab()].textbox.frame)
        style = ThemedStyle(search_frame)
        style.set_theme(self.theme)

        search_frame.pack(anchor='nw')
        ttk.Label(search_frame, text='Search: ').pack(side='left',
                                                      anchor='nw',
                                                      fill='y')
        content = tk.Entry(search_frame,
                           background='black',
                           foreground='white',
                           insertbackground='white',
                           highlightthickness=0)
        content.pack(side='left', fill='both')

        forward = ttk.Button(search_frame, text='<', width=1)
        forward.pack(side='left')

        backward = ttk.Button(search_frame, text='>', width=1)
        backward.pack(side='left')

        ttk.Label(search_frame, text='Replacement: ').pack(side='left',
                                                           anchor='nw',
                                                           fill='y')
        repl = tk.Entry(search_frame,
                        background='black',
                        foreground='white',
                        insertbackground='white',
                        highlightthickness=0)
        repl.pack(side='left', fill='both')

        repl_button = ttk.Button(search_frame, text='Replace all')
        repl_button.pack(side='left')
        clear_button = ttk.Button(search_frame, text='Clear All')
        clear_button.pack(side='left')

        case_button = ttk.Button(search_frame, text='Case Sensitive[0]')
        case_button.pack(side='left')

        reg_button = ttk.Button(search_frame, text='RegExp[0]')
        reg_button.pack(side='left')

        def find(_=None):
            global starts
            found = tk.IntVar()
            text = self.tabs[self.get_tab()].textbox
            text.tag_remove('found', '1.0', 'end')
            s = content.get()
            starts.clear()
            if s != '\\':
                idx = '1.0'
                while 1:
                    idx = text.search(s,
                                      idx,
                                      nocase=(not case),
                                      stopindex='end',
                                      regexp=(not regexp),
                                      count=found)
                    if not idx:
                        break
                    lastidx = '%s+%dc' % (idx, len(s))
                    text.tag_add('found', idx, lastidx)
                    starts.append(idx)
                    text.mark_set('insert', idx)
                    text.focus_set()
                    idx = lastidx
                text.tag_config('found', foreground='red', background='yellow')
            text.see('insert')
            text.statusbar.config(text=f'Found {found.get()} matches')

        def replace():
            text = self.tabs[self.get_tab()].textbox
            text.tag_remove('found', '1.0', 'end')
            s = content.get()
            r = repl.get()
            if s != '\\':
                idx = '1.0'
                while 1:
                    idx = text.search(s,
                                      idx,
                                      nocase=(not case),
                                      stopindex='end',
                                      regexp=(not regexp))
                    if not idx:
                        break
                    lastidx = '%s+%dc' % (idx, len(s))
                    text.delete(idx, lastidx)
                    text.insert(idx, r)
                    idx = lastidx

        def clear():
            text = self.tabs[self.get_tab()].textbox
            text.tag_remove('found', '1.0', 'end')

        def case_yn():
            global case
            case = not case
            case_button.config(text=f'Case Sensitive[{int(case)}]')
            find()

        def regexp_yn():
            global regexp
            regexp = not regexp
            reg_button.config(text=f'RegExp[{int(regexp)}]')
            find()

        def nav_forward():
            try:
                global starts
                text = self.tabs[self.get_tab()].textbox
                curpos = text.index('insert')
                if curpos in starts:
                    prev = starts.index(curpos) - 1
                    text.mark_set('insert', starts[prev])
                    text.see('insert')
                    text.focus_set()
            except Exception:
                pass

        def nav_backward():
            try:
                global starts
                text = self.tabs[self.get_tab()].textbox
                curpos = text.index('insert')
                if curpos in starts:
                    prev = starts.index(curpos) + 1
                    text.mark_set('insert', starts[prev])
                    text.see('insert')
                    text.focus_set()
            except Exception:
                pass

        clear_button.config(command=clear)
        case_button.config(command=case_yn)
        reg_button.config(command=regexp_yn)
        repl_button.config(command=replace)
        forward.config(command=nav_forward)
        backward.config(command=nav_backward)
        content.bind('<KeyRelease>', find)

        def _exit():
            search_frame.pack_forget()
            clear()
            self.tabs[self.get_tab()].textbox.focus_set()

        ttk.Button(search_frame, text='x', command=_exit,
                   width=1).pack(side='right', anchor='ne')

    def undo(self, _=None):
        try:
            self.tabs[self.get_tab()].textbox.edit_undo()
        except Exception:
            pass

    def redo(self, _=None):
        try:
            self.tabs[self.get_tab()].textbox.edit_redo()
        except Exception:
            pass

    def right_click(self, event):
        self.right_click_menu.post(event.x_root, event.y_root)

    def right_click_tab(self, event):
        self.tab_right_click_menu.post(event.x_root, event.y_root)

    def close_tab(self, event=None):
        global selected_tab
        try:
            if self.nb.index("end"):
                # Close the current tab if close is selected from file menu, or
                # keyboard shortcut.
                if event is None or event.type == str(2):
                    selected_tab = self.get_tab()
                # Otherwise close the tab based on coordinates of center-click.
                else:
                    try:
                        index = event.widget.index('@%d,%d' %
                                                   (event.x, event.y))
                        selected_tab = self.nb.nametowidget(
                            self.nb.tabs()[index])
                    except tk.TclError:
                        return

            self.nb.forget(selected_tab)
            self.tabs.pop(selected_tab)
            self.mouse()
        except Exception:
            pass

    def reload(self):
        if len(self.tabs) == 0:
            return
        tabs = []
        self.nb.select(self.nb.index('end') - 1)
        for value in self.tabs.items():
            tabs.append(value[1])
        for tab in tabs:
            file = tab.file_dir
            try:
                self.close_tab()
                self.get_tab()
                self.open_file(file)
            except Exception:
                self.new_file()

    def exit(self, force=False):
        if not force:
            self.master.destroy()
            logger.info('Window is destroyed')
        else:
            sys.exit(0)

    def restart(self):
        self.exit()
        self.__init__()

    def get_tab(self):
        return self.nb.nametowidget(self.nb.select())

    def move_tab(self, event):
        if self.nb.index('end') > 1:
            y = self.get_tab().winfo_y() - 5

            try:
                self.nb.insert(event.widget.index('@%d,%d' % (event.x, y)),
                               self.nb.select())
            except tk.TclError:
                return

    def _version(self):
        """Shows the version and related info of the editor."""
        ver = tk.Toplevel()
        ver.resizable(0, 0)
        ver.title('About PyPlus')
        img = tk.PhotoImage(data=ICON)
        ttk.Label(ver, image=img).pack(fill='both')
        ttk.Label(ver, text=f'Version {VERSION}',
                  font='Arial 30 bold').pack(fill='both')
        if self.check_updates(popup=False)[0]:
            update = ttk.Label(ver,
                               text='Updates available',
                               foreground="blue",
                               cursor="hand2")
            update.pack(fill='both')
            update.bind(
                "<Button-1>", lambda e: webbrowser.open_new_tab(
                    self.check_updates(popup=False)[1]))
        else:
            ttk.Label(ver, text='No updates available').pack(fill='both')
        ver.mainloop()

    def update_settings(self):
        self.filetypes = self.settings_class.get_settings('file_type')
        self.create_tags()
        self.recolorize()

    def lint_source(self):
        if len(self.tabs) == 0:
            return
        if self.tabs[self.get_tab()].textbox.lint_cmd:
            currdir = self.tabs[self.get_tab()].file_dir
            if WINDOWS:
                with open('lint.bat', 'w') as f:
                    f.write(
                        LINT_BATCH.format(
                            cmd=self.tabs[self.get_tab()].textbox.lint_cmd))
                subprocess.run(f'lint.bat "{currdir}"', shell=True)
                os.remove('lint.bat')
            else:
                with open('lint.sh', 'w') as f:
                    f.write(
                        LINT_BATCH.format(
                            cmd=self.tabs[self.get_tab()].textbox.lint_cmd))
                subprocess.run(f'chmod 700 lint.sh && ./lint.sh "{currdir}"',
                               shell=True)
                os.remove('lint.sh')
            self.open_file('results.txt')
            os.remove('results.txt')
        else:
            messagebox.showerror('Error', 'This language is not supported')
            return

    def autopep(self):
        """Auto Pretty-Format the document"""
        # TODO: ADD MORE SUPPORTED LANGUAGES
        currdir = self.tabs[self.get_tab()].file_dir
        subprocess.run(f'autopep8 "{currdir}" --in-place', shell=True)
        # Add the --in-place argument to disable output to console
        self.reload()

    def goto(self, _=None):
        if len(self.tabs) == 0:
            return
        goto_frame = ttk.Frame(self.tabs[self.get_tab()].textbox.frame)
        style = ttkthemes.ThemedStyle(goto_frame)
        style.set_theme(self.theme)
        goto_frame.pack(anchor='nw')
        ttk.Label(goto_frame,
                  text='Go to place: [Ln].[Col] ').pack(side='left')
        place = tk.Entry(goto_frame,
                         background='black',
                         foreground='white',
                         insertbackground='white',
                         highlightthickness=0)
        place.focus_set()
        place.pack(side='left')

        def _goto():
            currtext = self.tabs[self.get_tab()].textbox
            currtext.mark_set('insert', place.get())
            currtext.see('insert')
            _exit()

        def _exit():
            goto_frame.pack_forget()
            self.tabs[self.get_tab()].textbox.focus_set()

        goto_button = ttk.Button(goto_frame, command=_goto, text='>> Go to')
        goto_button.pack(side='left')
        ttk.Button(goto_frame, text='x', command=_exit,
                   width=1).pack(side='right', anchor='se')

    def nav_1cf(self):
        currtext = self.tabs[self.get_tab()].textbox
        currtext.mark_set('insert', 'insert+1c')

    def nav_1cb(self):
        currtext = self.tabs[self.get_tab()].textbox
        currtext.mark_set('insert', 'insert-1c')

    def check_updates(self, popup=True):
        if 'DEV' in VERSION:
            messagebox.showerror(
                "Updates", "Updates aren't supported by develop builds,\n\
            since you're always on the latest version!"
            )  # If you're on the developer run, you don't need updates!
            return
        download_file(
            url="https://zcg-coder.github.io/NWSOFT/PyPlusWeb/ver.json")
        with open('ver.json') as f:
            newest = json.load(f)
        version = newest["version"]
        if not popup:
            os.remove('ver.json')
            return [bool(version != VERSION), newest["url"]]
        updatewin = tk.Toplevel(self.master)
        updatewin.title('Updates')
        updatewin.resizable(0, 0)
        updatewin.transient(self.master)
        ttkthemes.ThemedStyle(updatewin)
        if version != VERSION:
            ttk.Label(updatewin, text='Update available!',
                      font='Arial 30').pack(fill='both')
            ttk.Label(updatewin, text=version).pack(fill='both')
            ttk.Label(updatewin, text=newest["details"]).pack(fill='both')
            url = newest["url"]
            ttk.Button(updatewin,
                       text='Get this update',
                       command=lambda: webbrowser.open(url)).pack()
        else:
            ttk.Label(updatewin, text='No updates available',
                      font='Arial 30').pack(fill='both')
        os.remove('ver.json')
        updatewin.mainloop()

    def git(self, action=None):
        if len(self.tabs) == 0:
            return
        elif action is None:
            raise EditorErr('Invalid action -- ' + str(action))
        currdir = Path(self.tabs[self.get_tab()].file_dir).parent
        if action == 'init':
            if os.path.isdir(os.path.join(currdir, '.git')):
                if messagebox.askokcancel(
                        "Error!",
                        "This is already a git repository!\nDo you want to re-initialize?"
                ):
                    os.remove(os.path.join(currdir, '.git'))
            else:
                run_in_terminal(
                    cwd=currdir,
                    cmd='git init && git add . && git commit -am \"Added files\"')
        elif action == 'addall':
            run_in_terminal(cwd=currdir,
                            cmd='git add . && git commit -am "Added files"')
        elif action == 'addsel':
            files = tk.filedialog.askopenfilenames(master=self.master,
                                                   initialdir='/',
                                                   title='Select file',
                                                   filetypes=self.filetypes)
            for x in files:
                run_in_terminal(cwd=currdir, cmd=f'git add {x}')
        elif action == 'commit':
            message = simpledialog.askstring('Commit', 'Commit message')
            run_in_terminal(f'git commit -am "{message}"')
        elif action == 'other':
            action = simpledialog.askstring('Advanced Action', 'git <command>:')
            run_in_terminal(f'git {action}')
        elif action == 'clone':
            url = simpledialog.askstring('Clone from remote', 'URL:')
            run_in_terminal(f'git clone {url}')

    def indent(self, action='indent'):
        """Indent/unindent feature"""
        if len(self.tabs) == 0:
            return
        currtext = self.tabs[self.get_tab()].textbox
        sel_start = currtext.index('sel.first linestart')
        sel_end = currtext.index('sel.last lineend')
        if action == 'indent':
            selected_text = currtext.get(sel_start, sel_end)
            indented = []
            for line in selected_text.splitlines():
                indented.append(' ' * 4 + line)
            currtext.delete(sel_start, sel_end)
            currtext.insert(sel_start, '\n'.join(indented))
            currtext.tag_remove('sel', '1.0', 'end')
            currtext.tag_add('sel', sel_start, f'{sel_end} +4c')
            self.key()
        elif action == 'unindent':
            selected_text = currtext.get(sel_start, sel_end)
            unindented = []
            for line in selected_text.splitlines():
                if line.startswith(' ' * 4):
                    unindented.append(line[4:])
                else:
                    return
            currtext.delete(sel_start, sel_end)
            currtext.insert(sel_start, '\n'.join(unindented))
            currtext.tag_remove('sel', '1.0', 'end')
            currtext.tag_add('sel', sel_start, sel_end)
            self.key()
        else:
            raise EditorErr('Action undefined.')


if __name__ == '__main__':
    Editor()
