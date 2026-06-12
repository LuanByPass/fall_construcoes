"""Tela de Login - FALL Construções (card compacto + rodapé visível)"""
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
from views.base_view import BaseView
from config import ModernTheme, LOJA_CONFIG


class LoginView(BaseView):
    # Paleta verde FALL
    FALL_GREEN      = "#064e3b"
    FALL_GREEN_DARK = "#022c22"
    FALL_ACCENT     = "#10b981"
    FALL_ACCENT_HOVER = "#059669"
    FALL_LIGHT      = "#d1fae5"
    FALL_CARD       = "#ffffff"

    def __init__(self, parent, auth_controller, on_login_success):
        super().__init__(parent, auth_controller)
        self.on_login_success = on_login_success
        self.build()

    def build(self):
        self.frame = tk.Frame(self.parent, bg=self.FALL_GREEN)

        # ── Fundo com pattern sutil ────────────────────────────────────────
        self._draw_bg_pattern()

        # ── Painel central ───────────────────────────────────────────────────
        center = tk.Frame(self.frame, bg=self.FALL_GREEN)
        center.place(relx=0.5, rely=0.5, anchor=tk.CENTER)

        # ── Logo real (PNG) ──────────────────────────────────────────────────
        try:
            logo_path = "logo.png"
            logo_img = Image.open(logo_path).convert("RGBA")
            bg = Image.new("RGBA", logo_img.size, self.FALL_GREEN)
            logo_composite = Image.alpha_composite(bg, logo_img)
            logo_resized = logo_composite.resize((90, 90), Image.LANCZOS)
            self.logo_photo = ImageTk.PhotoImage(logo_resized)

            logo_label = tk.Label(center, image=self.logo_photo, bg=self.FALL_GREEN)
            logo_label.pack()
        except Exception:
            logo_outer = tk.Frame(center, bg=self.FALL_ACCENT, width=90, height=90)
            logo_outer.pack()
            logo_outer.pack_propagate(False)
            logo_inner = tk.Frame(logo_outer, bg=self.FALL_CARD, width=82, height=82)
            logo_inner.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
            logo_inner.pack_propagate(False)
            tk.Label(logo_inner, text="FA",
                     font=("Segoe UI", 30, "bold"),
                     bg=self.FALL_CARD, fg=self.FALL_ACCENT).place(relx=0.5, rely=0.5, anchor=tk.CENTER)

        # Nome da empresa
        tk.Label(center, text=LOJA_CONFIG.get("nome", "FALL Construções"),
                 font=("Segoe UI", 24, "bold"),
                 bg=self.FALL_GREEN, fg="white").pack(pady=(12, 2))

        tk.Label(center, text="Sistema de Estoque e Vendas",
                 font=("Segoe UI", 11),
                 bg=self.FALL_GREEN, fg=self.FALL_LIGHT).pack(pady=(0, 12))

        # ═══════════════════════════════════════════════════════════════════
        # CARD BRANCO COMPACTO
        # ═══════════════════════════════════════════════════════════════════
        # pady interno REDUZIDO de 40 para 18 (menos altura)
        # padx interno REDUZIDO de 44 para 36 (um pouco mais estreito)
        card = tk.Frame(center, bg=self.FALL_CARD, padx=36, pady=18)
        card.pack(pady=12)  # pady externo reduzido de 28 para 12

        # Barra verde no topo do card
        tk.Frame(card, bg=self.FALL_ACCENT, height=4).pack(
            fill=tk.X, pady=(0, 16))  # pady reduzido de 28 para 16

        # Título do card
        tk.Label(card, text="Acesse sua conta",
                 font=("Segoe UI", 13, "bold"),
                 bg=self.FALL_CARD, fg="#1f2937").pack(anchor=tk.W, pady=(0, 12))  # reduzido de 20 para 12

        # Campo usuário
        user_row = tk.Frame(card, bg=self.FALL_CARD)
        user_row.pack(fill=tk.X, pady=(0, 10))  # reduzido de 16 para 10

        tk.Label(user_row, text="👤", font=("Segoe UI", 13),
                 bg=self.FALL_CARD, fg=self.FALL_ACCENT).pack(side=tk.LEFT, padx=(0, 8))

        user_col = tk.Frame(user_row, bg=self.FALL_CARD)
        user_col.pack(side=tk.LEFT, fill=tk.X, expand=True)

        tk.Label(user_col, text="USUÁRIO",
                 font=("Segoe UI", 9, "bold"),
                 bg=self.FALL_CARD, fg="#6b7280",
                 anchor=tk.W).pack(fill=tk.X)
        self.username_entry = tk.Entry(user_col,
                                         font=("Segoe UI", 11),
                                         bd=0, bg="#f3f4f6", fg="#1f2937",
                                         insertbackground=self.FALL_ACCENT,
                                         relief=tk.FLAT,
                                         highlightthickness=1,
                                         highlightcolor=self.FALL_ACCENT,
                                         highlightbackground="#e5e7eb",
                                         width=28)  # reduzido de 30 para 28
        self.username_entry.pack(fill=tk.X, pady=(4, 0), ipady=7)  # ipady 7 (era 8)
        self.username_entry.focus_set()

        # Campo senha
        pass_row = tk.Frame(card, bg=self.FALL_CARD)
        pass_row.pack(fill=tk.X, pady=(0, 14))  # reduzido de 24 para 14

        tk.Label(pass_row, text="🔒", font=("Segoe UI", 13),
                 bg=self.FALL_CARD, fg=self.FALL_ACCENT).pack(side=tk.LEFT, padx=(0, 8))

        pass_col = tk.Frame(pass_row, bg=self.FALL_CARD)
        pass_col.pack(side=tk.LEFT, fill=tk.X, expand=True)

        tk.Label(pass_col, text="SENHA",
                 font=("Segoe UI", 9, "bold"),
                 bg=self.FALL_CARD, fg="#6b7280",
                 anchor=tk.W).pack(fill=tk.X)
        self.password_entry = tk.Entry(pass_col,
                                       font=("Segoe UI", 11),
                                       bd=0, bg="#f3f4f6", fg="#1f2937",
                                       insertbackground=self.FALL_ACCENT,
                                       relief=tk.FLAT,
                                       highlightthickness=1,
                                       highlightcolor=self.FALL_ACCENT,
                                       highlightbackground="#e5e7eb",
                                       show="*", width=28)
        self.password_entry.pack(fill=tk.X, pady=(4, 0), ipady=7)

        # Botão entrar
        btn = tk.Button(card, text="ENTRAR NO SISTEMA",
                        command=self._login,
                        bg=self.FALL_ACCENT, fg="white",
                        font=("Segoe UI", 11, "bold"),
                        bd=0, relief=tk.FLAT,
                        padx=0, pady=10,  # pady interno reduzido de 12 para 10
                        cursor="hand2",
                        activebackground=self.FALL_ACCENT_HOVER,
                        activeforeground="white")
        btn.pack(fill=tk.X)
        btn.bind("<Enter>", lambda e: btn.config(bg=self.FALL_ACCENT_HOVER))
        btn.bind("<Leave>", lambda e: btn.config(bg=self.FALL_ACCENT))

        # Link esqueci senha
        forgot = tk.Label(card, text="Esqueceu a senha? Entre em contato com o administrador",
                          font=("Segoe UI", 9),
                          bg=self.FALL_CARD, fg="#9ca3af", cursor="hand2")
        forgot.pack(pady=(8, 0))  # reduzido de 12 para 8

        # Mensagem de erro
        self.status_label = tk.Label(card, text="",
                                     font=("Segoe UI", 10, "bold"),
                                     bg=self.FALL_CARD,
                                     fg="#ef4444")
        self.status_label.pack(pady=(8, 0))  # reduzido de 12 para 8

        # ── Rodapé (fora do card, agora visível!) ───────────────────────────
        footer_frame = tk.Frame(center, bg=self.FALL_GREEN)
        footer_frame.pack(fill=tk.X, pady=(10, 0))  # pady reduzido de 8 para 10, visível agora

        tk.Label(footer_frame,
                 text=f"© {LOJA_CONFIG.get('nome', 'FALL Construções')}  ·  {LOJA_CONFIG.get('telefone', '')}",
                 font=("Segoe UI", 9),
                 bg=self.FALL_GREEN, fg=self.FALL_LIGHT).pack()

        # Binds
        self.password_entry.bind("<Return>", lambda e: self._login())
        self.username_entry.bind("<Return>", lambda e: self.password_entry.focus_set())

    def _draw_bg_pattern(self):
        """Desenha linhas verticais sutil no fundo"""
        try:
            canvas = tk.Canvas(self.frame, bg=self.FALL_GREEN,
                               highlightthickness=0)
            canvas.place(x=0, y=0, relwidth=1, relheight=1)
            for x in range(80, self.frame.winfo_screenwidth(), 200):
                canvas.create_line(x, 0, x, self.frame.winfo_screenheight(),
                                   fill="#065f46", width=1)
            canvas.create_oval(-100, -100, 300, 300, fill="#065f46", outline="")
            w = self.frame.winfo_screenwidth()
            h = self.frame.winfo_screenheight()
            canvas.create_oval(w-250, h-250, w+50, h+50, fill="#065f46", outline="")
        except Exception:
            pass

    def _login(self):
        username = self.username_entry.get()
        password = self.password_entry.get()
        success, user = self.controller.login(username, password)
        if success:
            self.on_login_success(user)
        else:
            self.status_label.config(text="✗  Usuário ou senha incorretos")