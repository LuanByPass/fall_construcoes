"""FALL CONSTRUÇÕES - Sistema Completo de Estoque e Vendas
Arquivo principal - Sidebar compacta sem scrollbar, Sair sempre visível
"""
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
from utils.database import DatabaseConnection
from utils.logger import Logger, LogView
from controllers.auth_controller import AuthController
from controllers.categoria_controller import CategoriaController
from controllers.produto_controller import ProdutoController
from controllers.movimentacao_controller import MovimentacaoController
from controllers.venda_controller import VendaController
from controllers.orcamento_controller import OrcamentoController
from controllers.entrega_controller import EntregaController
from controllers.fornecedor_controller import FornecedorController
from controllers.cliente_controller import ClienteController
from views.login_view import LoginView
from views.dashboard_view import DashboardView
from views.produtos_view import ProdutosView
from views.categorias_view import CategoriasView
from views.movimentacoes_view import MovimentacoesView
from views.venda_view import VendaView
from views.historico_vendas_view import HistoricoVendasView
from views.orcamento_view import OrcamentoView
from views.entrega_view import EntregaView
from views.fornecedor_view import FornecedorView
from views.relatorio_view import RelatorioView
from views.clientes_view import ClientesView
from config import ModernTheme, LOJA_CONFIG, DB_CONFIG
import mysql.connector
from mysql.connector import Error


def init_database():
    """Cria o banco de dados se não existir"""
    try:
        conn = mysql.connector.connect(
            host=DB_CONFIG["host"],
            user=DB_CONFIG["user"],
            password=DB_CONFIG["password"],
        )
        cursor = conn.cursor()
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_CONFIG['database']}")
        conn.commit()
        cursor.close()
        conn.close()
        print(f"✅ Banco '{DB_CONFIG['database']}' verificado")
        return True
    except Error as e:
        print(f"❌ Erro ao criar banco: {e}")
        return False


class MainApplication:
    SIDEBAR_BG      = ModernTheme.SIDEBAR_BG
    SIDEBAR_HOVER   = ModernTheme.SIDEBAR_HOVER
    SIDEBAR_ACTIVE  = ModernTheme.SIDEBAR_ACTIVE
    HEADER_BG       = ModernTheme.DARK
    ACCENT          = ModernTheme.PRIMARY
    ACCENT_HOVER    = ModernTheme.PRIMARY_HOVER
    LIGHT           = ModernTheme.PRIMARY_LIGHT
    TEXT_ON_DARK    = ModernTheme.TEXT_ON_DARK
    TEXT_MUTED      = ModernTheme.TEXT_MUTED
    BG_CONTENT      = ModernTheme.BG
    CARD_BG         = ModernTheme.CARD_BG
    DANGER          = ModernTheme.DANGER
    DANGER_HOVER    = ModernTheme.DANGER_HOVER

    SIDEBAR_WIDTH = 260
    LOGO_HEIGHT   = 55

    def __init__(self, root):
        self.root = root
        self.root.title(f"{LOJA_CONFIG['nome']} - Sistema de Estoque e Vendas")
        self.root.geometry("1600x950")
        self.root.configure(bg=self.BG_CONTENT)

        self.controllers = {
            "auth": AuthController(),
            "cliente": ClienteController(),
            "categoria": CategoriaController(),
            "produto": ProdutoController(),
            "movimentacao": MovimentacaoController(),
            "venda": VendaController(),
            "orcamento": OrcamentoController(),
            "entrega": EntregaController(),
            "fornecedor": FornecedorController(),
        }

        self.container = tk.Frame(root, bg=self.BG_CONTENT)
        self.container.pack(fill=tk.BOTH, expand=True)

        self.views = {}
        self.current_view = None
        self.main_frame = None
        self.sidebar = None
        self.content = None
        self.content_header = None
        self.content_title = None
        self.menu_buttons = {}
        self.menu_indicators = {}
        self.menu_item_frames = {}
        self.logo_photo = None

        self.show_login()

    def show_login(self):
        self._clear_all()
        login_view = LoginView(self.container, self.controllers["auth"], self.on_login)
        login_view.show()
        self.views["login"] = login_view
        self.current_view = "login"

    def on_login(self, user):
        self._clear_all()
        self.setup_main_ui()
        self.show_view("dashboard")

    def setup_main_ui(self):
        self.main_frame = tk.Frame(self.container, bg=self.BG_CONTENT)
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        # ═══════════════════════════════════════════════════════════════════
        # SIDEBAR — grid com menu compacto (sem scrollbar)
        # ═══════════════════════════════════════════════════════════════════
        sidebar_container = tk.Frame(self.main_frame, bg=self.SIDEBAR_HOVER, width=self.SIDEBAR_WIDTH + 1)
        sidebar_container.pack(side=tk.LEFT, fill=tk.Y)
        sidebar_container.pack_propagate(False)

        self.sidebar = tk.Frame(sidebar_container, bg=self.SIDEBAR_BG, width=self.SIDEBAR_WIDTH)
        self.sidebar.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.sidebar.pack_propagate(False)

        self.sidebar.grid_rowconfigure(0, weight=0)
        self.sidebar.grid_rowconfigure(1, weight=0)
        self.sidebar.grid_rowconfigure(2, weight=0)
        self.sidebar.grid_rowconfigure(3, weight=0)
        self.sidebar.grid_rowconfigure(4, weight=1)
        self.sidebar.grid_rowconfigure(5, weight=0)
        self.sidebar.grid_columnconfigure(0, weight=1)

        self._build_sidebar_header()

        tk.Frame(self.sidebar, bg=self.SIDEBAR_HOVER, height=2).grid(
            row=1, column=0, sticky="ew", padx=16, pady=6)

        self._build_user_section()

        tk.Frame(self.sidebar, bg=self.SIDEBAR_HOVER, height=2).grid(
            row=3, column=0, sticky="ew", padx=16, pady=6)

        self._build_sidebar_menu()

        self._build_sidebar_footer()

        # ═══════════════════════════════════════════════════════════════════
        # ÁREA DE CONTEÚDO
        # ═══════════════════════════════════════════════════════════════════
        self.content = tk.Frame(self.main_frame, bg=self.BG_CONTENT)
        self.content.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        self.content_header = tk.Frame(self.content, bg=self.HEADER_BG, height=64)
        self.content_header.pack(fill=tk.X, side=tk.TOP)
        self.content_header.pack_propagate(False)

        tk.Frame(self.content_header, bg=self.ACCENT, height=2).pack(fill=tk.X, side=tk.BOTTOM)

        self.content_title = tk.Label(
            self.content_header,
            text="Dashboard",
            font=("Segoe UI", 16, "bold"),
            bg=self.HEADER_BG,
            fg="white",
            anchor=tk.W,
        )
        self.content_title.pack(side=tk.LEFT, padx=24, pady=(12, 0))

        self.content_subtitle = tk.Label(
            self.content_header,
            text="Painel de controle geral",
            font=("Segoe UI", 10),
            bg=self.HEADER_BG,
            fg=self.TEXT_ON_DARK,
            anchor=tk.W,
        )
        self.content_subtitle.pack(side=tk.LEFT, padx=(0, 24), pady=(12, 0))

        self.header_clock = tk.Label(
            self.content_header,
            text="",
            font=("Segoe UI", 10),
            bg=self.HEADER_BG,
            fg=self.TEXT_ON_DARK,
        )
        self.header_clock.pack(side=tk.RIGHT, padx=24, pady=(12, 0))
        self._update_clock()

        self.content_body = tk.Frame(self.content, bg=self.BG_CONTENT)
        self.content_body.pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True)

        self.views = {
            "dashboard":    DashboardView(self.content_body, self.controllers),
            "vendas":       VendaView(self.content_body, self.controllers),
            "historico":    HistoricoVendasView(self.content_body, self.controllers),
            "orcamentos":   OrcamentoView(self.content_body, self.controllers),
            "entregas":     EntregaView(self.content_body, self.controllers),
            "produtos":     ProdutosView(self.content_body, self.controllers),
            "fornecedores": FornecedorView(self.content_body, self.controllers),
            "clientes":     ClientesView(self.content_body, self.controllers),
            "categorias":   CategoriasView(self.content_body, self.controllers),
            "movimentacoes": MovimentacoesView(self.content_body, self.controllers),
            "relatorios":   RelatorioView(self.content_body, self.controllers),
            "logs":         LogView(self.content_body),
        }

        for view in self.views.values():
            if hasattr(view, "hide"):
                view.hide()

    def _build_sidebar_header(self):
        header = tk.Frame(self.sidebar, bg=self.SIDEBAR_BG)
        header.grid(row=0, column=0, sticky="ew", padx=16, pady=(16, 6))

        try:
            logo_path = "logo.png"
            logo_img = Image.open(logo_path).convert("RGBA")
            bg = Image.new("RGBA", logo_img.size, self.SIDEBAR_BG)
            logo_comp = Image.alpha_composite(bg, logo_img)
            ratio = logo_comp.width / logo_comp.height
            new_h = self.LOGO_HEIGHT
            new_w = int(new_h * ratio)
            logo_resized = logo_comp.resize((new_w, new_h), Image.LANCZOS)
            self.logo_photo = ImageTk.PhotoImage(logo_resized)

            logo_lbl = tk.Label(header, image=self.logo_photo, bg=self.SIDEBAR_BG)
            logo_lbl.pack(side=tk.LEFT)
        except Exception:
            circle = tk.Frame(header, bg=self.ACCENT, width=40, height=40)
            circle.pack(side=tk.LEFT)
            circle.pack_propagate(False)
            tk.Label(circle, text="FA", font=("Segoe UI", 14, "bold"),
                     bg=self.ACCENT, fg="white").place(relx=0.5, rely=0.5, anchor=tk.CENTER)

        name_frame = tk.Frame(header, bg=self.SIDEBAR_BG)
        name_frame.pack(side=tk.LEFT, padx=(10, 0))
        tk.Label(name_frame, text="FALL",
                 font=("Segoe UI", 14, "bold"),
                 bg=self.SIDEBAR_BG, fg="white").pack(anchor=tk.W)
        tk.Label(name_frame, text="Construções",
                 font=("Segoe UI", 10),
                 bg=self.SIDEBAR_BG, fg=self.TEXT_ON_DARK).pack(anchor=tk.W)

    def _build_user_section(self):
        user = self.controllers["auth"].get_user() or {}
        nome = user.get("nome", "").strip() or user.get("username", "Usuário")
        perfil = user.get("perfil", "Operador")

        user_frame = tk.Frame(self.sidebar, bg=self.SIDEBAR_BG)
        user_frame.grid(row=2, column=0, sticky="ew", padx=16, pady=2)

        avatar = tk.Frame(user_frame, bg=self.ACCENT, width=32, height=32)
        avatar.pack(side=tk.LEFT)
        avatar.pack_propagate(False)
        iniciais = "".join([p[0] for p in nome.split() if p])[:2].upper() if nome else "U"
        tk.Label(avatar, text=iniciais,
                 font=("Segoe UI", 10, "bold"),
                 bg=self.ACCENT, fg="white").place(relx=0.5, rely=0.5, anchor=tk.CENTER)

        info = tk.Frame(user_frame, bg=self.SIDEBAR_BG)
        info.pack(side=tk.LEFT, padx=(10, 0))
        tk.Label(info, text=nome,
                 font=("Segoe UI", 10, "bold"),
                 bg=self.SIDEBAR_BG, fg="white", anchor=tk.W).pack(fill=tk.X)
        tk.Label(info, text=perfil,
                 font=("Segoe UI", 8),
                 bg=self.SIDEBAR_BG, fg=self.TEXT_ON_DARK, anchor=tk.W).pack(fill=tk.X)

    def _build_sidebar_menu(self):
        menu_container = tk.Frame(self.sidebar, bg=self.SIDEBAR_BG)
        menu_container.grid(row=4, column=0, sticky="nsew", padx=0, pady=4)

        menu_items = [
            ("📊", "Dashboard",       "dashboard"),
            ("🛒", "Vendas (PDV)",    "vendas"),
            ("📜", "Histórico Vendas", "historico"),
            ("📋", "Orçamentos",      "orcamentos"),
            ("🚚", "Entregas",        "entregas"),
            ("📦", "Produtos",        "produtos"),
            ("🏭", "Fornecedores",    "fornecedores"),
            ("👥", "Clientes",        "clientes"),
            ("🔖", "Categorias",      "categorias"),
            ("📈", "Movimentações",   "movimentacoes"),
            ("📊", "Relatórios",      "relatorios"),
            ("📋", "Logs",            "logs"),
        ]

        self.menu_buttons = {}
        self.menu_indicators = {}
        self.menu_item_frames = {}

        for icon, text, view_name in menu_items:
            # Itens compactos: height=34, pady=0
            item_frame = tk.Frame(menu_container, bg=self.SIDEBAR_BG, height=34, cursor="hand2")
            item_frame.pack(fill=tk.X, pady=0)
            item_frame.pack_propagate(False)
            self.menu_item_frames[view_name] = item_frame

            indicator = tk.Frame(item_frame, bg=self.SIDEBAR_BG, width=3)
            indicator.pack(side=tk.LEFT, fill=tk.Y)
            self.menu_indicators[view_name] = indicator

            icon_lbl = tk.Label(
                item_frame,
                text=icon,
                font=("Segoe UI", 10),
                width=2,
                anchor=tk.CENTER,
                bg=self.SIDEBAR_BG,
                fg=self.TEXT_ON_DARK,
            )
            icon_lbl.pack(side=tk.LEFT, padx=(10, 4))

            text_lbl = tk.Label(
                item_frame,
                text=text,
                font=("Segoe UI", 9),
                anchor=tk.W,
                bg=self.SIDEBAR_BG,
                fg=self.TEXT_ON_DARK,
            )
            text_lbl.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            self.menu_buttons[view_name] = (item_frame, icon_lbl, text_lbl)

            for widget in (item_frame, icon_lbl, text_lbl):
                widget.bind("<Button-1>", lambda e, v=view_name: self.show_view(v))

            item_frame.bind("<Enter>", lambda e, v=view_name: self._on_menu_hover(v, True))
            item_frame.bind("<Leave>", lambda e, v=view_name: self._on_menu_leave(v))

    def _on_menu_hover(self, view_name, entering):
        if view_name not in self.menu_item_frames:
            return
        frame, icon_lbl, text_lbl = self.menu_buttons[view_name]
        if entering:
            frame.config(bg=self.SIDEBAR_HOVER)
            icon_lbl.config(bg=self.SIDEBAR_HOVER, fg="white")
            text_lbl.config(bg=self.SIDEBAR_HOVER, fg="white")
            if self.current_view != view_name:
                self.menu_indicators[view_name].config(bg=self.ACCENT)

    def _on_menu_leave(self, view_name):
        if view_name not in self.menu_item_frames:
            return
        frame, icon_lbl, text_lbl = self.menu_buttons[view_name]
        if self.current_view == view_name:
            frame.config(bg=self.SIDEBAR_HOVER)
            icon_lbl.config(bg=self.SIDEBAR_HOVER, fg="white")
            text_lbl.config(bg=self.SIDEBAR_HOVER, fg="white", font=("Segoe UI", 9, "bold"))
            self.menu_indicators[view_name].config(bg=self.LIGHT)
        else:
            frame.config(bg=self.SIDEBAR_BG)
            icon_lbl.config(bg=self.SIDEBAR_BG, fg=self.TEXT_ON_DARK)
            text_lbl.config(bg=self.SIDEBAR_BG, fg=self.TEXT_ON_DARK, font=("Segoe UI", 9))
            self.menu_indicators[view_name].config(bg=self.SIDEBAR_BG)

    def _build_sidebar_footer(self):
        footer = tk.Frame(self.sidebar, bg=self.SIDEBAR_BG)
        footer.grid(row=5, column=0, sticky="sew", padx=12, pady=10)

        tk.Frame(footer, bg=self.SIDEBAR_HOVER, height=2).pack(fill=tk.X, pady=(0, 8))

        btn_sair = tk.Button(
            footer,
            text="🚪  Sair do Sistema",
            font=("Segoe UI", 10, "bold"),
            bg=self.DANGER,
            fg="white",
            bd=0,
            padx=16,
            pady=10,
            anchor=tk.W,
            cursor="hand2",
            command=self.logout,
        )
        btn_sair.pack(fill=tk.X)
        btn_sair.bind("<Enter>", lambda e: btn_sair.config(bg=self.DANGER_HOVER))
        btn_sair.bind("<Leave>", lambda e: btn_sair.config(bg=self.DANGER))

    def show_view(self, view_name, title=None, subtitle=None):
        if view_name not in self.views:
            print(f"⚠️ View '{view_name}' não encontrada!")
            return

        if self.current_view and self.current_view in self.menu_buttons:
            prev_frame, prev_icon, prev_text = self.menu_buttons[self.current_view]
            prev_frame.config(bg=self.SIDEBAR_BG)
            prev_icon.config(bg=self.SIDEBAR_BG, fg=self.TEXT_ON_DARK)
            prev_text.config(bg=self.SIDEBAR_BG, fg=self.TEXT_ON_DARK, font=("Segoe UI", 9))
            self.menu_indicators[self.current_view].config(bg=self.SIDEBAR_BG)

        if (self.current_view
                and self.current_view in self.views
                and hasattr(self.views[self.current_view], "hide")):
            self.views[self.current_view].hide()

        self.current_view = view_name

        if view_name in self.menu_buttons:
            frame, icon_lbl, text_lbl = self.menu_buttons[view_name]
            frame.config(bg=self.SIDEBAR_HOVER)
            icon_lbl.config(bg=self.SIDEBAR_HOVER, fg="white")
            text_lbl.config(bg=self.SIDEBAR_HOVER, fg="white", font=("Segoe UI", 9, "bold"))
            self.menu_indicators[view_name].config(bg=self.LIGHT)

        # Título automático baseado no view_name
        titulos = {
            "dashboard": ("Dashboard", "Painel de controle geral"),
            "vendas": ("Vendas (PDV)", "Ponto de venda rápido"),
            "historico": ("Histórico Vendas", "Registro de transações"),
            "orcamentos": ("Orçamentos", "Propostas e orçamentos"),
            "entregas": ("Entregas", "Controle de logística"),
            "produtos": ("Produtos", "Catálogo e estoque"),
            "fornecedores": ("Fornecedores", "Gestão de fornecedores"),
            "clientes": ("Clientes", "Base de clientes"),
            "categorias": ("Categorias", "Segmentação de produtos"),
            "movimentacoes": ("Movimentações", "Entradas e saídas"),
            "relatorios": ("Relatórios", "Análises e exportações"),
            "logs": ("Logs", "Registro de eventos"),
        }
        t, s = titulos.get(view_name, (view_name.title(), ""))
        self.content_title.config(text=title or t)
        self.content_subtitle.config(text=subtitle or s)

        view = self.views[view_name]
        if hasattr(view, "show"):
            view.show()
        if hasattr(view, "refresh"):
            view.refresh()

    def _update_clock(self):
        try:
            from datetime import datetime
            now = datetime.now().strftime("%d/%m/%Y  %H:%M")
            self.header_clock.config(text=now)
            self.root.after(60000, self._update_clock)
        except Exception:
            pass

    def _clear_all(self):
        for widget in self.container.winfo_children():
            widget.destroy()
        self.views.clear()
        self.current_view = None
        self.menu_buttons.clear()
        self.menu_indicators.clear()
        self.menu_item_frames.clear()
        self.main_frame = None
        self.sidebar = None
        self.content = None
        self.content_header = None
        self.content_title = None
        self.logo_photo = None

    def logout(self):
        self.controllers["auth"].logout()
        self._clear_all()
        self.show_login()


if __name__ == "__main__":
    if not init_database():
        print("Configure as credenciais do MySQL em config.py")
        exit(1)

    root = tk.Tk()
    app = MainApplication(root)
    root.mainloop()