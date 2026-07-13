import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog, messagebox
import threading
import json
import os
import sys
import time
import random
import webbrowser
from datetime import datetime
from pathlib import Path
import queue
import base64

# Optional imports with fallback
try:
    import customtkinter as ctk
    HAS_CTK = True
except ImportError:
    HAS_CTK = False

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.config import GhostConfig
from core.scanner import GitHubScanner
from core.analyzer import CodeAnalyzer
from core.exporter import DataExporter
from utils.shortcut import create_onedrive_shortcut
from utils.icon_gen import generate_app_icon, generate_small_icon

# ─── Russian hacker aesthetic theme ─────────────────────────────────────
THEME = {
    'bg': '#0a0a0a',
    'fg': '#00cc00',
    'fg_dim': '#006600',
    'fg_bright': '#00ff41',
    'fg_red': '#ff0033',
    'fg_cyan': '#00ffcc',
    'fg_yellow': '#ffcc00',
    'fg_white': '#c0c0c0',
    'select_bg': '#003300',
    'select_fg': '#00ff41',
    'button_bg': '#001a00',
    'button_fg': '#00ff41',
    'button_hover': '#003300',
    'entry_bg': '#000d00',
    'entry_fg': '#00ff41',
    'entry_inset': '#00ff41',
    'scroll_bg': '#000a00',
    'scroll_fg': '#003300',
    'tab_bg': '#000d00',
    'tab_fg': '#006600',
    'tab_sel_bg': '#001a00',
    'tab_sel_fg': '#00ff41',
    'progress_bg': '#000d00',
    'progress_fg': '#00ff41',
    'frame_bg': '#050505',
    'frame_border': '#003300',
    'font_family': 'Consolas',
    'font_size': 10,
    'title_font_size': 14,
}

BANNER_TEXT = r"""
  ╔══════════════════════════════════════════════════════╗
  ║          ▓▓▓▓▓ ▓▓▓ ▓▓▓▓▓▓▓ ▓▓▓▓▓ ▓▓▓▓▓▓▓          ║
  ║          ▓▓    ▓▓▓ ▓▓   ▓▓ ▓▓  ▓▓ ▓▓   ▓▓          ║
  ║          ▓▓▓▓  ▓▓▓ ▓▓▓▓▓▓▓ ▓▓▓▓▓ ▓▓▓▓▓▓▓          ║
  ║          ▓▓    ▓▓▓ ▓▓ ▓▓   ▓▓  ▓▓ ▓▓ ▓▓            ║
  ║          ▓▓    ▓▓▓ ▓▓  ▓▓  ▓▓  ▓▓ ▓▓  ▓▓           ║
  ║                                                        ║
  ║      ██ ██ █████ █████ ████  █████ █████ █████      ║
  ║      ██ ██ ██   ██   ██  ██ ██   ██   ██           ║
  ║      █████ █████ █████ █████ █████ █████ ████       ║
  ║        ██ ██   ██   ██ ██  ██ ██   ██   ██           ║
  ║        ██ █████ █████ ██  ██ █████ █████ █████      ║
  ║                                                        ║
  ║        █████ ██  ██ █████ █████ █████ █████          ║
  ║        ██   ██  ██ ██  ██ ██   ██   ██              ║
  ║        █████ █████ █████ █████ █████ ████            ║
  ║           ██ ██  ██ ██ ██    ██ ██   ██              ║
  ║        █████ ██  ██ ██  ██ █████ █████ █████         ║
  ║                                                        ║
  ╚══════════════════════════════════════════════════════╝
"""

JAKE_THE_SNAKE = [
    "     ====        ",
    "    /    \\       ",
    "   /      \\      ",
    "  /  ▄▄▄   \\     ",
    " |  █▄▄█    |    ",
    "  \\   ▀▀   /     ",
    "   \\  ▄▄  /      ",
    "    \\    /       ",
    "     ====        ",
    "    ██████       ",
    "   ████████      ",
    "    ██████       ",
    "  ╔══════╗       ",
    "  ║ VIPER ║       ",
    "  ╚══════╝       ",
]

RUSSIAN_QUOTES = [
    "The snake does not bite without reason.",
    "Darkness is not eternal, but code is.",
    "Fear is just a tool.",
    "In darkness we see more.",
    "Every snake dreams of becoming a dragon.",
    "Silence before the storm is just silence.",
    "Blood runs cold like steel.",
    "Systems fall, snakes rise.",
    "Your fear is my power.",
    "Code does not lie, but code hides.",
    "In every shadow lurks a snake.",
    "The eyes of the snake see in the dark.",
]

class ConsoleHandler:
    def __init__(self, text_widget, max_lines=1000):
        self.text = text_widget
        self.max_lines = max_lines
        self.queue = queue.Queue()
        self._running = True
        self._start_processing()

    def _start_processing(self):
        def process():
            while self._running:
                try:
                    msg, tag = self.queue.get(timeout=0.1)
                    self._append(msg, tag)
                except queue.Empty:
                    pass
        threading.Thread(target=process, daemon=True).start()

    def write(self, msg, tag='info'):
        self.queue.put((msg, tag))

    def _append(self, msg, tag):
        try:
            self.text.configure(state='normal')
            self.text.insert('end', msg + '\n', tag)
            self.text.see('end')
            line_count = int(self.text.index('end-1c').split('.')[0])
            if line_count > self.max_lines:
                self.text.delete('1.0', f'{line_count - self.max_lines}.0')
            self.text.configure(state='disabled')
        except:
            pass

    def stop(self):
        self._running = False


class GhostViperApp:
    def __init__(self):
        self.config = GhostConfig()
        self.scanner = None
        self.analyzer = CodeAnalyzer(self.config)
        self.exporter = DataExporter(self.config)
        self.search_results = []
        self.search_active = False
        self._theme_index = 0
        self._snake_frame = 0
        self._quote_index = 0

        if HAS_CTK:
            ctk.set_appearance_mode("dark")
            ctk.set_default_color_theme("green")

        self.root = tk.Tk()
        self.root.title("GHOST VIPER v4.2.0 - COBRA OSINT")
        self.root.geometry("1280x800")
        self.root.minsize(1024, 600)

        # Set icon
        try:
            ico_path = os.path.join(os.environ.get('GHOST_VIPER_ROOT', os.path.expanduser('~')),
                                     'assets', 'ghost_viper_small.ico')
            if os.path.exists(ico_path):
                self.root.iconbitmap(ico_path)
        except:
            pass

        self._apply_hacker_theme()
        self._build_ui()
        self._animate_snake()
        self._rotate_quotes()

        # Generate icon + shortcut + validate token on startup
        self.root.after(2000, self._post_init)

    def _post_init(self):
        threading.Thread(target=self._generate_assets, daemon=True).start()
        if self.config.github_token:
            threading.Thread(target=self._validate_token_on_startup, daemon=True).start()

    def _generate_assets(self):
        try:
            ico = generate_small_icon()
            self.console.write(f"[+] Icon generated: {ico}", 'success')
        except Exception as e:
            self.console.write(f"[!] Icon error: {e}", 'error')

        try:
            if self.config['one_drive_shortcut']:
                create_onedrive_shortcut(self.config)
                self.console.write("[+] Shortcut created on OneDrive Desktop", 'success')
        except Exception as e:
            self.console.write(f"[!] Shortcut error: {e}", 'warn')

    def _validate_token_on_startup(self):
        try:
            from core.scanner import GitHubScanner
            s = GitHubScanner(self.config, callback=self._log_callback)
            valid = s.validate_token()
            s.cleanup()
            if valid:
                self.root.after(0, lambda: self.token_indicator.config(text="TOKEN: VALID", fg=THEME['fg_bright']))
            else:
                self.root.after(0, lambda: self.token_indicator.config(text="TOKEN: INVALID", fg=THEME['fg_red']))
        except Exception as e:
            self.console.write(f"[!] Token check error: {e}", 'warn')

    def _apply_hacker_theme(self):
        self.root.configure(bg=THEME['bg'])
        style = ttk.Style()
        style.theme_use('clam')

        style.configure('.',
            background=THEME['bg'],
            foreground=THEME['fg'],
            fieldbackground=THEME['entry_bg'],
            selectbackground=THEME['select_bg'],
            selectforeground=THEME['select_fg'],
            font=(THEME['font_family'], THEME['font_size']))

        style.configure('TFrame', background=THEME['frame_bg'])
        style.configure('TLabel', background=THEME['bg'], foreground=THEME['fg'])
        style.configure('TButton',
            background=THEME['button_bg'],
            foreground=THEME['button_fg'],
            borderwidth=1,
            focuscolor='none',
            font=(THEME['font_family'], THEME['font_size']))
        style.map('TButton',
            background=[('active', THEME['button_hover']), ('pressed', '#004400')],
            foreground=[('active', THEME['fg_bright'])])

        style.configure('TMenubutton', background=THEME['button_bg'], foreground=THEME['fg'])
        style.configure('TEntry',
            fieldbackground=THEME['entry_bg'],
            foreground=THEME['entry_fg'],
            insertcolor=THEME['entry_inset'])
        style.configure('TNotebook',
            background=THEME['tab_bg'],
            foreground=THEME['tab_fg'])
        style.configure('TNotebook.Tab',
            background=THEME['tab_bg'],
            foreground=THEME['tab_fg'],
            padding=[8, 4])
        style.map('TNotebook.Tab',
            background=[('selected', THEME['tab_sel_bg'])],
            foreground=[('selected', THEME['tab_sel_fg'])])
        style.configure('Vertical.TScrollbar',
            background=THEME['scroll_bg'],
            troughcolor=THEME['bg'],
            bordercolor=THEME['scroll_fg'])

        style.configure('Green.Horizontal.TProgressbar',
            background=THEME['progress_fg'],
            troughcolor=THEME['progress_bg'])

        style.configure('Status.TLabel',
            background=THEME['bg'],
            foreground=THEME['fg_dim'],
            font=(THEME['font_family'], 8))

    def _build_ui(self):
        # ── Main container ──
        self.root.grid_rowconfigure(0, weight=0)
        self.root.grid_rowconfigure(1, weight=0)
        self.root.grid_rowconfigure(2, weight=1)
        self.root.grid_rowconfigure(3, weight=0)
        self.root.grid_columnconfigure(0, weight=1)

        # ── Header / Banner ──
        header = tk.Frame(self.root, bg=THEME['bg'])
        header.grid(row=0, column=0, sticky='ew', padx=2, pady=(2, 0))

        self.banner_label = tk.Label(header,
            text=BANNER_TEXT,
            font=(THEME['font_family'], 7),
            fg=THEME['fg'],
            bg=THEME['bg'],
            justify='left')
        self.banner_label.pack(side='left', padx=5)

        # Jake the Snake ASCII art
        self.snake_label = tk.Label(header,
            text='\n'.join(JAKE_THE_SNAKE),
            font=(THEME['font_family'], 7),
            fg=THEME['fg'],
            bg=THEME['bg'],
            justify='left')
        self.snake_label.pack(side='right', padx=5)

        # Quote ticker
        self.quote_label = tk.Label(header,
            text=random.choice(RUSSIAN_QUOTES),
            font=(THEME['font_family'], 8, 'italic'),
            fg=THEME['fg_dim'],
            bg=THEME['bg'])
        self.quote_label.pack(side='bottom', fill='x', pady=(0, 2))

        # ── Control bar ──
        controls = tk.Frame(self.root, bg=THEME['frame_bg'], bd=1,
                           relief='solid', highlightbackground=THEME['frame_border'],
                           highlightthickness=1)
        controls.grid(row=1, column=0, sticky='ew', padx=2, pady=2)
        controls.grid_columnconfigure(2, weight=1)

        tk.Label(controls, text="⚡ QUERY:", fg=THEME['fg_bright'],
                bg=THEME['frame_bg'],
                font=(THEME['font_family'], 10, 'bold')).grid(row=0, column=0, padx=(8, 4), pady=6)

        self.query_var = tk.StringVar(value="social media followers generator")
        self.query_entry = tk.Entry(controls,
            textvariable=self.query_var,
            bg=THEME['entry_bg'],
            fg=THEME['entry_fg'],
            insertbackground=THEME['entry_inset'],
            font=(THEME['font_family'], 11),
            bd=0,
            relief='flat',
            highlightthickness=1,
            highlightcolor=THEME['fg'],
            highlightbackground=THEME['frame_border'],
            width=50)
        self.query_entry.grid(row=0, column=1, padx=4, pady=6, sticky='ew')
        self.query_entry.bind('<Return>', lambda e: self._start_search())

        self.search_btn = tk.Button(controls,
            text="▶ SCAN",
            command=self._start_search,
            bg=THEME['button_bg'],
            fg=THEME['fg_bright'],
            font=(THEME['font_family'], 10, 'bold'),
            bd=1,
            relief='solid',
            highlightbackground=THEME['frame_border'],
            activebackground='#004400',
            activeforeground='#00ff41',
            cursor='hand2',
            padx=12)
        self.search_btn.grid(row=0, column=3, padx=(8, 4), pady=6)

        self.stop_btn = tk.Button(controls,
            text="■ STOP",
            command=self._stop_search,
            bg='#1a0000',
            fg=THEME['fg_red'],
            font=(THEME['font_family'], 10, 'bold'),
            bd=1,
            relief='solid',
            highlightbackground='#330000',
            activebackground='#330000',
            activeforeground='#ff0033',
            cursor='hand2',
            padx=12,
            state='disabled')
        self.stop_btn.grid(row=0, column=4, padx=4, pady=6)

        self.export_btn = tk.Button(controls,
            text="💾 EXPORT",
            command=self._export_results,
            bg=THEME['button_bg'],
            fg=THEME['fg_cyan'],
            font=(THEME['font_family'], 10, 'bold'),
            bd=1,
            relief='solid',
            highlightbackground=THEME['frame_border'],
            activebackground='#004400',
            activeforeground='#00ffcc',
            cursor='hand2',
            padx=12,
            state='disabled')
        self.export_btn.grid(row=0, column=5, padx=4, pady=6)

        # Config button
        self.config_btn = tk.Button(controls,
            text="⚙",
            command=self._show_config,
            bg=THEME['button_bg'],
            fg=THEME['fg_yellow'],
            font=(THEME['font_family'], 12, 'bold'),
            bd=1,
            relief='solid',
            activebackground='#333300',
            cursor='hand2',
            width=3)
        self.config_btn.grid(row=0, column=6, padx=4, pady=6)

        # ── Main content area ──
        content = tk.Frame(self.root, bg=THEME['bg'])
        content.grid(row=2, column=0, sticky='nsew', padx=2, pady=2)
        content.grid_columnconfigure(0, weight=3)
        content.grid_columnconfigure(1, weight=2)
        content.grid_rowconfigure(0, weight=1)

        # Left: Console / Log
        left_panel = tk.Frame(content, bg=THEME['frame_bg'],
                              bd=1, relief='solid',
                              highlightbackground=THEME['frame_border'],
                              highlightthickness=1)
        left_panel.grid(row=0, column=0, sticky='nsew', padx=(0, 2))
        left_panel.grid_rowconfigure(0, weight=0)
        left_panel.grid_rowconfigure(1, weight=1)
        left_panel.grid_columnconfigure(0, weight=1)

        tk.Label(left_panel, text="═══ CONSOLE ═══",
                fg=THEME['fg_dim'], bg=THEME['frame_bg'],
                font=(THEME['font_family'], 9)).grid(row=0, column=0, pady=(4, 0))

        self.console_text = tk.Text(left_panel,
            bg=THEME['entry_bg'],
            fg=THEME['fg'],
            insertbackground=THEME['entry_inset'],
            font=(THEME['font_family'], 10),
            bd=0,
            relief='flat',
            wrap='word',
            state='disabled',
            highlightthickness=0)
        self.console_text.grid(row=1, column=0, sticky='nsew', padx=2, pady=2)

        # Scrollbar for console
        scroll = tk.Scrollbar(left_panel, command=self.console_text.yview,
                            bg=THEME['scroll_bg'],
                            troughcolor=THEME['bg'],
                            activebackground=THEME['fg'])
        scroll.grid(row=1, column=1, sticky='ns')
        self.console_text.config(yscrollcommand=scroll.set)

        # Tags for colored output
        self.console_text.tag_config('info', foreground=THEME['fg'])
        self.console_text.tag_config('success', foreground=THEME['fg_bright'])
        self.console_text.tag_config('warn', foreground=THEME['fg_yellow'])
        self.console_text.tag_config('error', foreground=THEME['fg_red'])
        self.console_text.tag_config('highlight', foreground=THEME['fg_cyan'])
        self.console_text.tag_config('title', foreground=THEME['fg_bright'],
                                      font=(THEME['font_family'], 11, 'bold'))

        self.console = ConsoleHandler(self.console_text)

        # Right: Results panel
        right_panel = tk.Frame(content, bg=THEME['frame_bg'],
                               bd=1, relief='solid',
                               highlightbackground=THEME['frame_border'],
                               highlightthickness=1)
        right_panel.grid(row=0, column=1, sticky='nsew', padx=(2, 0))
        right_panel.grid_rowconfigure(1, weight=1)
        right_panel.grid_columnconfigure(0, weight=1)

        result_header = tk.Frame(right_panel, bg=THEME['frame_bg'])
        result_header.grid(row=0, column=0, sticky='ew', pady=(4, 0))
        result_header.grid_columnconfigure(1, weight=1)

        tk.Label(result_header, text="═══ RESULTS ═══",
                fg=THEME['fg_dim'], bg=THEME['frame_bg'],
                font=(THEME['font_family'], 9)).grid(row=0, column=0, padx=4)

        self.result_count = tk.Label(result_header, text="0",
                                     fg=THEME['fg_cyan'], bg=THEME['frame_bg'],
                                     font=(THEME['font_family'], 9, 'bold'))
        self.result_count.grid(row=0, column=1, sticky='e', padx=4)

        # Progress bar
        self.progress = ttk.Progressbar(right_panel,
            style='Green.Horizontal.TProgressbar',
            mode='indeterminate')
        self.progress.grid(row=0, column=0, sticky='ew', padx=4, pady=(4, 0))
        self.progress.grid_remove()

        # Results treeview
        tree_frame = tk.Frame(right_panel, bg=THEME['bg'])
        tree_frame.grid(row=1, column=0, sticky='nsew', padx=2, pady=2)
        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)

        style = ttk.Style()
        style.configure('Results.Treeview',
            background=THEME['entry_bg'],
            foreground=THEME['fg'],
            fieldbackground=THEME['entry_bg'],
            rowheight=24,
            font=(THEME['font_family'], 9),
            borderwidth=0)
        style.configure('Results.Treeview.Heading',
            background=THEME['button_bg'],
            foreground=THEME['fg_bright'],
            font=(THEME['font_family'], 9, 'bold'),
            borderwidth=1,
            relief='solid')
        style.map('Results.Treeview.Heading',
            background=[('active', THEME['button_hover'])])
        style.map('Results.Treeview',
            background=[('selected', THEME['select_bg'])],
            foreground=[('selected', THEME['select_fg'])])

        self.tree = ttk.Treeview(tree_frame,
            columns=('rank', 'name', 'stars', 'risk', 'platforms', 'purpose'),
            show='tree headings',
            style='Results.Treeview',
            height=12)
        self.tree.grid(row=0, column=0, sticky='nsew')

        self.tree.heading('rank', text='#', anchor='center')
        self.tree.heading('name', text='Repository', anchor='w')
        self.tree.heading('stars', text='★', anchor='center')
        self.tree.heading('risk', text='Risk', anchor='center')
        self.tree.heading('platforms', text='Platforms', anchor='w')
        self.tree.heading('purpose', text='Type', anchor='w')

        self.tree.column('rank', width=40, minwidth=30, stretch=False)
        self.tree.column('name', width=220, minwidth=150)
        self.tree.column('stars', width=50, minwidth=40, stretch=False)
        self.tree.column('risk', width=60, minwidth=50, stretch=False)
        self.tree.column('platforms', width=150, minwidth=100)
        self.tree.column('purpose', width=100, minwidth=80)

        tree_scroll = tk.Scrollbar(tree_frame, command=self.tree.yview,
                                 bg=THEME['scroll_bg'],
                                 troughcolor=THEME['bg'])
        tree_scroll.grid(row=0, column=1, sticky='ns')
        self.tree.config(yscrollcommand=tree_scroll.set)

        self.tree.bind('<<TreeviewSelect>>', self._on_result_select)

        # Detail panel (below tree)
        self.detail_text = tk.Text(right_panel,
            bg=THEME['entry_bg'],
            fg=THEME['fg_white'],
            font=(THEME['font_family'], 9),
            bd=0,
            relief='flat',
            wrap='word',
            height=6,
            state='disabled',
            highlightthickness=0)
        self.detail_text.grid(row=2, column=0, sticky='ew', padx=2, pady=(0, 2))

        self.detail_text.tag_config('header', foreground=THEME['fg_bright'],
                                    font=(THEME['font_family'], 9, 'bold'))
        self.detail_text.tag_config('field', foreground=THEME['fg_cyan'])
        self.detail_text.tag_config('value', foreground=THEME['fg_white'])
        self.detail_text.tag_config('danger', foreground=THEME['fg_red'])

        # ── Status bar ──
        status = tk.Frame(self.root, bg=THEME['bg'])
        status.grid(row=3, column=0, sticky='ew', padx=2, pady=(0, 2))
        status.grid_columnconfigure(0, weight=1)

        self.status_label = tk.Label(status,
            text="READY | Use a GitHub token for extended search",
            fg=THEME['fg_dim'],
            bg=THEME['bg'],
            font=(THEME['font_family'], 8),
            anchor='w')
        self.status_label.pack(side='left', fill='x')

        self.token_indicator = tk.Label(status,
            text="TOKEN: ---",
            fg=THEME['fg_dim'],
            bg=THEME['bg'],
            font=(THEME['font_family'], 7))
        self.token_indicator.pack(side='right', padx=(0, 8))

        self.ver_label = tk.Label(status,
            text="v4.2.0",
            fg=THEME['fg_dim'],
            bg=THEME['bg'],
            font=(THEME['font_family'], 7))
        self.ver_label.pack(side='right', padx=4)

        # Startup console messages (must be after status bar is built)
        self.console.write("╔═══════════════════════════════════════╗", 'title')
        self.console.write("║  GHOST VIPER v4.2.0 INITIALIZED  ║", 'title')
        self.console.write("╚═══════════════════════════════════════╝", 'title')
        self.console.write("")
        self.console.write("[*] Welcome. The snake is ready to hunt.", 'info')
        if self.config.github_token:
            self.console.write("[*] GitHub Token: present (will validate on first request)", 'info')
            self.token_indicator.config(text="TOKEN: SET", fg=THEME['fg_yellow'])
        else:
            self.console.write("[*] GitHub Token: not set (anonymous mode - strict rate limits)", 'warn')
            self.token_indicator.config(text="TOKEN: NONE", fg=THEME['fg_dim'])
        self.console.write(f"[*] Rate limit: {self.config['rate_limit']}s/request | Pages: {self.config['max_pages']}", 'info')
        self.console.write("")

    def _animate_snake(self):
        if hasattr(self, 'snake_label'):
            fg = THEME['fg_bright'] if self._snake_frame % 2 == 0 else THEME['fg_dim']
            txt = '\n'.join(JAKE_THE_SNAKE)
            self.snake_label.config(text=txt, fg=fg)
            self._snake_frame += 1
        self.root.after(800, self._animate_snake)

    def _rotate_quotes(self):
        if hasattr(self, 'quote_label'):
            self._quote_index = (self._quote_index + 1) % len(RUSSIAN_QUOTES)
            self.quote_label.config(text=RUSSIAN_QUOTES[self._quote_index])
            colors = [THEME['fg_dim'], THEME['fg'], THEME['fg_cyan'], THEME['fg_red']]
            self.quote_label.config(fg=colors[self._quote_index % len(colors)])
        self.root.after(5000, self._rotate_quotes)

    def _start_search(self):
        if self.search_active:
            return

        query = self.query_var.get().strip()
        if not query:
            messagebox.showwarning("Error", "Please enter a search query.")
            return

        self.search_active = True
        self.search_btn.config(state='disabled', text='▶ SCANNING...')
        self.stop_btn.config(state='normal')
        self.export_btn.config(state='disabled')
        self.progress.grid()
        self.progress.start(20)

        # Clear previous results
        for item in self.tree.get_children():
            self.tree.delete(item)
        self.result_count.config(text='0')
        self.search_results = []

        self.console.write("")
        self.console.write("═" * 50, 'highlight')
        self.console.write(f"[>] STARTING SCAN: {query}", 'highlight')
        self.console.write("═" * 50, 'highlight')

        threading.Thread(target=self._do_search, args=(query,), daemon=True).start()

    def _stop_search(self):
        self.search_active = False
        self.console.write("[!] SCAN STOPPED BY USER", 'warn')
        self._search_done()

    def _do_search(self, query):
        try:
            self.scanner = GitHubScanner(self.config, callback=self._log_callback)
            patterns = self.config['code_patterns'] + [query]
            file_types = self.config['file_types']

            results = self.scanner.advanced_search(query, patterns, file_types)

            if not self.search_active:
                return

            # Rank results
            ranked = self.analyzer.rank_repositories(results)
            self.search_results = ranked

            # Update UI
            self.root.after(0, self._populate_results, ranked)
            self.console.write(f"[+] SCAN COMPLETE: {len(ranked)} results", 'success')

        except Exception as e:
            self.console.write(f"[!] CRITICAL ERROR: {e}", 'error')
            import traceback
            self.console.write(traceback.format_exc(), 'error')
        finally:
            if self.scanner:
                self.scanner.cleanup()
            self.root.after(0, self._search_done)

    def _log_callback(self, msg, level='info'):
        tag_map = {'info': 'info', 'warn': 'warn', 'error': 'error', 'success': 'success'}
        self.console.write(msg, tag_map.get(level, 'info'))
        self.root.after(0, lambda: self.status_label.config(text=msg[:80]))

    def _populate_results(self, results):
        for i, r in enumerate(results[:200], 1):
            analysis = r.get('analysis', {})
            platforms = ', '.join(analysis.get('platforms_detected', [])[:3]) or '?'
            risk_level = analysis.get('risk_level', 'low').upper()
            risk_color = {'HIGH': 'CRITICAL', 'MEDIUM': 'MEDIUM', 'LOW': 'LOW'}.get(risk_level, '?')

            name = r['full_name']
            stars = r.get('stars', 0) or 0
            purpose = analysis.get('estimated_purpose', '?')

            tags = ()
            if risk_level == 'HIGH':
                tags = ('danger',)

            self.tree.insert('', 'end',
                values=(i, name, stars, risk_color, platforms, purpose),
                tags=tags)

        # Color high-risk rows
        self.tree.tag_configure('danger', foreground=THEME['fg_red'])

        self.result_count.config(text=str(len(results)))
        self.export_btn.config(state='normal' if results else 'disabled')

    def _search_done(self):
        self.search_active = False
        self.search_btn.config(state='normal', text='▶ SCAN')
        self.stop_btn.config(state='disabled')
        self.progress.stop()
        self.progress.grid_remove()
        self.status_label.config(text="READY")

    def _on_result_select(self, event):
        selection = self.tree.selection()
        if not selection:
            return
        item = self.tree.item(selection[0])
        values = item['values']
        if not values or len(values) < 2:
            return

        rank = values[0]
        name = values[1]

        # Find full result
        result = None
        for r in self.search_results:
            if r['full_name'] == name:
                result = r
                break

        if not result:
            return

        analysis = result.get('analysis', {})

        self.detail_text.configure(state='normal')
        self.detail_text.delete('1.0', 'end')

        self.detail_text.insert('end', f"══════ {result['full_name']} ══════\n", 'header')
        self.detail_text.insert('end', f"Description: ", 'field')
        self.detail_text.insert('end', f"{(result.get('description') or '?')[:200]}\n", 'value')
        self.detail_text.insert('end', f"URL: ", 'field')
        self.detail_text.insert('end', f"{result.get('url', result.get('html_url', ''))}\n", 'value')
        self.detail_text.insert('end', f"★ {result.get('stars', 0)} | ", 'field')
        self.detail_text.insert('end', f"Forks: {result.get('forks', 0)} | ", 'field')
        self.detail_text.insert('end', f"Language: {result.get('language', '?')}\n", 'field')
        self.detail_text.insert('end', f"Platforms: ", 'field')
        self.detail_text.insert('end', f"{', '.join(analysis.get('platforms_detected', ['?']))}\n", 'value')
        self.detail_text.insert('end', f"Risk: ", 'field')
        risk_level = analysis.get('risk_level', 'low').upper()
        risk_tag = 'danger' if risk_level == 'HIGH' else 'value'
        self.detail_text.insert('end', f"{risk_level} ({analysis.get('risk_score', 0)}%)\n", risk_tag)
        self.detail_text.insert('end', f"Type: ", 'field')
        self.detail_text.insert('end', f"{analysis.get('estimated_purpose', '?')}\n", 'value')
        self.detail_text.insert('end', f"Features: ", 'field')
        features = analysis.get('features', [])
        self.detail_text.insert('end', f"{', '.join(features[:5])}\n", 'value')

        self.detail_text.configure(state='disabled')

    def _export_results(self):
        if not self.search_results:
            return

        filename = filedialog.asksaveasfilename(
            defaultextension='.json',
            filetypes=[
                ('JSON', '*.json'),
                ('CSV', '*.csv'),
                ('Report TXT', '*.txt'),
                ('All formats', '*.*'),
            ],
            initialfile=f"ghost_viper_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            title='Export Results')

        if not filename:
            return

        ext = os.path.splitext(filename)[1].lower()
        try:
            if ext == '.json':
                path = self.exporter.export_json(self.search_results, filename)
            elif ext == '.csv':
                path = self.exporter.export_csv(self.search_results, filename)
            elif ext == '.txt':
                path = self.exporter.export_report(self.search_results, filename)
            else:
                path = self.exporter.export_json(self.search_results, filename)

            self.console.write(f"[+] Exported: {path}", 'success')
            self.status_label.config(text=f"Saved: {path}")

            open_folder = messagebox.askyesno("Success", f"Saved to:\n{path}\n\nOpen folder?")
            if open_folder:
                os.startfile(os.path.dirname(path))

        except Exception as e:
            self.console.write(f"[!] Export error: {e}", 'error')
            messagebox.showerror("Error", f"Failed to export:\n{e}")

    def _test_token(self, token_value, save_on_success=False):
        if not token_value:
            self.console.write("[!] Enter a token first.", 'warn')
            return
        token_value = token_value.strip()
        if '\n' in token_value or '\r' in token_value or ' ' in token_value:
            self.console.write("[!] Token contains whitespace or newlines — looks like an error message, not a token.", 'error')
            return
        self.console.write("[*] Testing token (user + code search)...", 'info')
        self.status_label.config(text="Testing token...")
        self.token_indicator.config(text="TOKEN: TESTING...", fg=THEME['fg_yellow'])
        def do_test():
            try:
                import requests
                h = {'Authorization': f'Bearer {token_value}', 'User-Agent': 'GhostViper/4.2.0', 'Accept': 'application/vnd.github.v3+json'}
                # Test user endpoint
                resp = requests.get('https://api.github.com/user', headers=h, timeout=15)
                if resp.status_code == 200:
                    user = resp.json()
                    scopes = resp.headers.get('X-OAuth-Scopes', 'unknown')
                    login = user.get('login', '?')
                    self.console.write(f"[+] User endpoint OK: {login} | Scopes: {scopes}", 'success')
                    if save_on_success:
                        self.config.github_token = token_value
                        self.config._data['github_token'] = 'enc:' + base64.b64encode(token_value.encode()).decode()
                        self.config.save()
                        self.console.write("[+] Token saved as default", 'success')

                    # Test code search endpoint
                    resp2 = requests.get('https://api.github.com/search/code?q=hello+world&per_page=1', headers=h, timeout=15)
                    if resp2.status_code == 200:
                        self.console.write("[+] Code search endpoint OK", 'success')
                        self.status_label.config(text=f"Token fully valid: {login}")
                        self.token_indicator.config(text="TOKEN: VALID", fg=THEME['fg_bright'])
                    elif resp2.status_code == 401:
                        detail = resp2.json().get('message', '')
                        self.console.write(f"[!] Code search needs extra scope: {detail}", 'warn')
                        self.console.write("[!] Your token works for basic auth but NOT code search.", 'warn')
                        self.console.write("[!] Create a classic token with 'repo' scope at github.com/settings/tokens", 'warn')
                        self.status_label.config(text=f"Token works but no code search scope")
                        self.token_indicator.config(text="TOKEN: NO CODE SEARCH", fg=THEME['fg_yellow'])
                    else:
                        self.console.write(f"[!] Code search: HTTP {resp2.status_code}", 'warn')
                        self.token_indicator.config(text="TOKEN: PARTIAL", fg=THEME['fg_yellow'])
                else:
                    detail = resp.json().get('message', resp.text[:100])
                    self.console.write(f"[!] Token invalid ({resp.status_code}): {detail}", 'error')
                    self.status_label.config(text="Token INVALID")
                    self.token_indicator.config(text="TOKEN: INVALID", fg=THEME['fg_red'])
            except Exception as e:
                self.console.write(f"[!] Test failed: {e}", 'error')
                self.token_indicator.config(text="TOKEN: ?", fg=THEME['fg_red'])
        threading.Thread(target=do_test, daemon=True).start()

    def _show_config(self):
        win = tk.Toplevel(self.root)
        win.title("⚙ GHOST VIPER SETTINGS")
        win.geometry("600x500")
        win.configure(bg=THEME['bg'])
        win.resizable(False, False)

        try:
            ico = os.path.join(os.environ.get('GHOST_VIPER_ROOT', os.path.expanduser('~')),
                                'assets', 'ghost_viper_small.ico')
            if os.path.exists(ico):
                win.iconbitmap(ico)
        except:
            pass

        win.transient(self.root)
        win.grab_set()

        notebook = ttk.Notebook(win)
        notebook.pack(fill='both', expand=True, padx=5, pady=5)

        # ── General tab ──
        gen_frame = tk.Frame(notebook, bg=THEME['bg'])
        notebook.add(gen_frame, text='General')
        gen_frame.grid_columnconfigure(1, weight=1)

        row = 0
        tk.Label(gen_frame, text="GitHub Token:", fg=THEME['fg'],
                bg=THEME['bg']).grid(row=row, column=0, sticky='w', padx=8, pady=4)
        token_var = tk.StringVar(value=self.config.github_token)
        token_entry = tk.Entry(gen_frame, textvariable=token_var, width=40,
                              bg=THEME['entry_bg'], fg=THEME['fg'],
                              insertbackground=THEME['entry_inset'],
                              show='*', bd=0, highlightthickness=1,
                              highlightcolor=THEME['fg'],
                              highlightbackground=THEME['frame_border'])
        token_entry.grid(row=row, column=1, sticky='ew', padx=8, pady=4)
        tk.Label(gen_frame, text="(optional, but recommended)",
                fg=THEME['fg_dim'], bg=THEME['bg'],
                font=(THEME['font_family'], 8)).grid(row=row, column=2, padx=4, sticky='w')

        test_token_btn = tk.Button(gen_frame, text="TEST && SAVE",
              command=lambda: self._test_token(token_var.get(), save_on_success=True),
              bg=THEME['button_bg'], fg=THEME['fg_cyan'],
              font=(THEME['font_family'], 8, 'bold'),
              bd=1, relief='solid', cursor='hand2', padx=6)
        test_token_btn.grid(row=row, column=3, padx=4)
        row += 1

        tk.Label(gen_frame, text="Delay (sec):", fg=THEME['fg'],
                bg=THEME['bg']).grid(row=row, column=0, sticky='w', padx=8, pady=4)
        rate_var = tk.DoubleVar(value=self.config['rate_limit'])
        tk.Scale(gen_frame, variable=rate_var, from_=0.1, to=5.0,
                resolution=0.1, orient='horizontal', length=200,
                bg=THEME['bg'], fg=THEME['fg'],
                troughcolor=THEME['entry_bg'],
                activebackground=THEME['fg'],
                bd=0, highlightthickness=0).grid(row=row, column=1, sticky='w', padx=8)
        row += 1

        tk.Label(gen_frame, text="Max pages:", fg=THEME['fg'],
                bg=THEME['bg']).grid(row=row, column=0, sticky='w', padx=8, pady=4)
        pages_var = tk.IntVar(value=self.config['max_pages'])
        tk.Scale(gen_frame, variable=pages_var, from_=1, to=100,
                orient='horizontal', length=200,
                bg=THEME['bg'], fg=THEME['fg'],
                troughcolor=THEME['entry_bg'],
                activebackground=THEME['fg'],
                bd=0, highlightthickness=0).grid(row=row, column=1, sticky='w', padx=8)
        row += 1

        tk.Label(gen_frame, text="Max results:", fg=THEME['fg'],
                bg=THEME['bg']).grid(row=row, column=0, sticky='w', padx=8, pady=4)
        max_var = tk.IntVar(value=self.config['max_results'])
        tk.Scale(gen_frame, variable=max_var, from_=10, to=500,
                orient='horizontal', length=200,
                bg=THEME['bg'], fg=THEME['fg'],
                troughcolor=THEME['entry_bg'],
                activebackground=THEME['fg'],
                bd=0, highlightthickness=0).grid(row=row, column=1, sticky='w', padx=8)
        row += 1

        # Checkboxes
        search_code_var = tk.BooleanVar(value=self.config['search_code'])
        tk.Checkbutton(gen_frame, text="Search code contents",
                      variable=search_code_var,
                      bg=THEME['bg'], fg=THEME['fg'],
                      selectcolor=THEME['entry_bg'],
                      activebackground=THEME['bg'],
                      activeforeground=THEME['fg']).grid(row=row, column=1, sticky='w', padx=8)
        row += 1

        search_readme_var = tk.BooleanVar(value=self.config['search_readme'])
        tk.Checkbutton(gen_frame, text="Analyze README files",
                      variable=search_readme_var,
                      bg=THEME['bg'], fg=THEME['fg'],
                      selectcolor=THEME['entry_bg'],
                      activebackground=THEME['bg'],
                      activeforeground=THEME['fg']).grid(row=row, column=1, sticky='w', padx=8)
        row += 1

        shortcut_var = tk.BooleanVar(value=self.config['one_drive_shortcut'])
        tk.Checkbutton(gen_frame, text="Create OneDrive Desktop shortcut",
                      variable=shortcut_var,
                      bg=THEME['bg'], fg=THEME['fg'],
                      selectcolor=THEME['entry_bg'],
                      activebackground=THEME['bg'],
                      activeforeground=THEME['fg']).grid(row=row, column=1, sticky='w', padx=8)
        row += 1

        # Pattern editor
        row += 1
        tk.Label(gen_frame, text="Search patterns (one per line):",
                fg=THEME['fg'], bg=THEME['bg'],
                font=(THEME['font_family'], 8)).grid(row=row, column=0, columnspan=2,
                                                      sticky='w', padx=8, pady=(8, 2))
        row += 1

        pattern_text = tk.Text(gen_frame, height=5, width=50,
                              bg=THEME['entry_bg'], fg=THEME['fg'],
                              insertbackground=THEME['entry_inset'],
                              bd=0, highlightthickness=1,
                              highlightcolor=THEME['fg'],
                              highlightbackground=THEME['frame_border'])
        pattern_text.grid(row=row, column=0, columnspan=2, sticky='ew', padx=8, pady=2)
        pattern_text.insert('1.0', '\n'.join(self.config['code_patterns']))

        # ── About tab ──
        about_frame = tk.Frame(notebook, bg=THEME['bg'])
        notebook.add(about_frame, text='About')

        about_text = f"""GHOST VIPER v4.2.0

GitHub OSINT Hunter Toolkit

Developer: Jake the Snake
Language: Python 3
License: FOR EDUCATIONAL PURPOSES ONLY

─────────────────────────────
  TECHNICAL SPECIFICATIONS
─────────────────────────────

• Multi-phase search (repositories + code + README)
• Source code content analysis
• Target platform identification
• Risk assessment and ranking
• Export to JSON / CSV / TXT
• Deep repository analysis
• GitHub API token support
• OneDrive Desktop integration
• Custom icon and theme

─────────────────────────────
  DISCLAIMER
─────────────────────────────

This tool is intended for educational
and research purposes only.

Use responsibly.

  THE SNAKE IS ALWAYS WATCHING.
"""
        about_label = tk.Label(about_frame, text=about_text,
                              fg=THEME['fg'], bg=THEME['bg'],
                              font=(THEME['font_family'], 10),
                              justify='left')
        about_label.pack(padx=10, pady=10, fill='both', expand=True)

        # Buttons
        btn_frame = tk.Frame(win, bg=THEME['bg'])
        btn_frame.pack(fill='x', padx=5, pady=5)

        def save_config():
            raw_token = token_var.get().strip()
            if '\n' in raw_token or '\r' in raw_token or ' ' in raw_token:
                self.console.write("[!] Token looks corrupted (whitespace/newlines). Not saving.", 'error')
                return
            self.config.github_token = raw_token
            self.config._data['rate_limit'] = rate_var.get()
            self.config._data['max_pages'] = int(pages_var.get())
            self.config._data['max_results'] = int(max_var.get())
            self.config._data['search_code'] = search_code_var.get()
            self.config._data['search_readme'] = search_readme_var.get()
            self.config._data['one_drive_shortcut'] = shortcut_var.get()
            patterns = pattern_text.get('1.0', 'end-1c').strip().split('\n')
            if patterns:
                self.config._data['code_patterns'] = patterns
            if self.config.save():
                self.console.write("[+] Settings saved successfully", 'success')
                tk_token = self.config.github_token
                if tk_token:
                    threading.Thread(target=lambda t=tk_token: self._test_token(t), daemon=True).start()
                win.destroy()
            else:
                self.console.write("[!] Failed to save config file!", 'error')
                messagebox.showerror("Save Error", "Could not write config file.\nCheck permissions.")

        tk.Button(btn_frame, text="SAVE",
                 command=save_config,
                 bg=THEME['button_bg'], fg=THEME['fg_bright'],
                 bd=1, relief='solid',
                 activebackground='#004400',
                 cursor='hand2').pack(side='right', padx=4)

        tk.Button(btn_frame, text="CANCEL",
                 command=win.destroy,
                 bg='#1a0000', fg=THEME['fg_red'],
                 bd=1, relief='solid',
                 activebackground='#330000',
                 cursor='hand2').pack(side='right', padx=4)

    def run(self):
        self.root.mainloop()
