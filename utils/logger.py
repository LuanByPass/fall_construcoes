"""Sistema de logging para FALL Construcoes"""
import tkinter as tk
from tkinter import scrolledtext
from datetime import datetime
from config import ModernTheme

class Logger:
    """Singleton logger"""
    _instance = None
    _log_widget = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @classmethod
    def set_widget(cls, widget):
        cls._log_widget = widget

    @classmethod
    def log(cls, message, level='INFO'):
        timestamp = datetime.now().strftime('%H:%M:%S')
        log_line = "[" + timestamp + "] [" + level + "] " + message + "\n"
        print(log_line.strip())

        if cls._log_widget:
            def update():
                cls._log_widget.insert(tk.END, log_line)
                cls._log_widget.see(tk.END)
                if level == 'ERROR':
                    cls._log_widget.tag_add('error', cls._log_widget.index('end-2l linestart'), cls._log_widget.index('end-1c'))
                elif level == 'SQL':
                    cls._log_widget.tag_add('sql', cls._log_widget.index('end-2l linestart'), cls._log_widget.index('end-1c'))
                elif level == 'SUCCESS':
                    cls._log_widget.tag_add('success', cls._log_widget.index('end-2l linestart'), cls._log_widget.index('end-1c'))

            try:
                cls._log_widget.after(0, update)
            except:
                pass

class LogView:
    def __init__(self, parent):
        self.parent = parent
        self.frame = None
        self.build()

    def build(self):
        self.frame = tk.Frame(self.parent, bg=ModernTheme.BG)

        header = tk.Frame(self.frame, bg=ModernTheme.DARK, height=45)
        header.pack(fill=tk.X)
        header.pack_propagate(False)
        tk.Label(header, text="Console de Logs", font=('Segoe UI', 12, 'bold'),
                bg=ModernTheme.DARK, fg='white').pack(side=tk.LEFT, padx=15, pady=8)

        tk.Button(self.frame, text="Limpar", command=self._clear,
                 bg=ModernTheme.DANGER, fg='white', bd=0, padx=15, pady=5,
                 cursor='hand2', font=('Segoe UI', 9)).pack(anchor=tk.E, padx=10, pady=5)

        self.log_text = scrolledtext.ScrolledText(
            self.frame, 
            wrap=tk.WORD,
            font=('Consolas', 10),
            bg='#0f172a',
            fg='#e2e8f0',
            insertbackground='white',
            height=30
        )
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        self.log_text.tag_config('error', foreground='#ef4444')
        self.log_text.tag_config('sql', foreground='#38bdf8')
        self.log_text.tag_config('success', foreground='#22c55e')

        Logger.set_widget(self.log_text)

        Logger.log("Sistema FALL Construcoes iniciado", 'SUCCESS')
        Logger.log("Aguardando comandos...", 'INFO')

    def _clear(self):
        self.log_text.delete(1.0, tk.END)
        Logger.log("Logs limpos", 'INFO')

    def show(self):
        self.frame.pack(fill=tk.BOTH, expand=True)

    def hide(self):
        self.frame.pack_forget()
