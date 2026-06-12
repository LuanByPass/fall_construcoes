"""Tela de Movimentações - FALL Construções (reestilizada premium)"""
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, timedelta
from views.base_view import BaseView
from config import ModernTheme

try:
    from utils.logger import Logger
except Exception:
    class Logger:
        @classmethod
        def log(cls, msg, level="INFO"):
            print(f"[{level}] {msg}")


class MovimentacoesView(BaseView):
    def __init__(self, parent, controllers):
        super().__init__(parent, None)
        self.controllers = controllers
        self.build()

    def build(self):
        self.frame = tk.Frame(self.parent, bg=ModernTheme.BG)

        # ═══════════════════════════════════════════════════════════════════
        # ESTATÍSTICAS RÁPIDAS
        # ═══════════════════════════════════════════════════════════════════
        stats_frame = tk.Frame(self.frame, bg=ModernTheme.BG)
        stats_frame.pack(fill=tk.X, padx=16, pady=12)

        self.stats_labels = {}
        stats_config = [
            ("total",    "📜 Total",        ModernTheme.PRIMARY,  "#1e40af"),
            ("entrada",  "📥 Entradas",     ModernTheme.SUCCESS,  "#15803d"),
            ("saida",    "📤 Saídas",       ModernTheme.DANGER,   "#b91c1c"),
            ("venda",    "🛒 Vendas",       ModernTheme.INFO,     "#1e40af"),
            ("ajuste",   "⚙️ Ajustes",      ModernTheme.WARNING,  "#b45309"),
        ]
        for key, label, color, hover in stats_config:
            card = tk.Frame(stats_frame, bg=ModernTheme.CARD_BG,
                            highlightbackground=color,
                            highlightthickness=2)
            card.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=4)

            tk.Frame(card, bg=color, height=4).pack(fill=tk.X)
            inner = tk.Frame(card, bg=ModernTheme.CARD_BG, padx=16, pady=10)
            inner.pack(fill=tk.X)

            tk.Label(inner, text=label,
                     font=("Segoe UI", 9, "bold"),
                     bg=ModernTheme.CARD_BG, fg=color).pack(anchor=tk.W)
            self.stats_labels[key] = tk.Label(inner, text="0",
                     font=("Segoe UI", 18, "bold"),
                     bg=ModernTheme.CARD_BG, fg=ModernTheme.TEXT)
            self.stats_labels[key].pack(anchor=tk.W)

        # ═══════════════════════════════════════════════════════════════════
        # CARD DE FILTROS
        # ═══════════════════════════════════════════════════════════════════
        filter_card = tk.Frame(self.frame, bg=ModernTheme.CARD_BG,
                               highlightbackground=ModernTheme.BORDER,
                               highlightthickness=1)
        filter_card.pack(fill=tk.X, padx=16, pady=8)
        tk.Frame(filter_card, bg=ModernTheme.PRIMARY, height=3).pack(fill=tk.X)

        inner = tk.Frame(filter_card, bg=ModernTheme.CARD_BG, padx=16, pady=12)
        inner.pack(fill=tk.X)

        # Busca
        search_box = tk.Frame(inner, bg=ModernTheme.CARD_BG,
                              highlightbackground=ModernTheme.BORDER,
                              highlightthickness=1)
        search_box.pack(side=tk.LEFT)

        tk.Label(search_box, text="🔍", font=("Segoe UI", 13),
                 bg=ModernTheme.CARD_BG, fg=ModernTheme.INFO).pack(
            side=tk.LEFT, padx=8)
        self.busca_entry = self.styled_entry(search_box,
                                              "Produto, código, motivo...",
                                              width=32)
        self.busca_entry.pack(side=tk.LEFT, padx=8)
        self.busca_entry.bind("<Return>", lambda e: self.refresh())

        btn_buscar = tk.Button(search_box, text="Buscar", command=self.refresh,
                               bg=ModernTheme.INFO, fg="white",
                               font=("Segoe UI", 9, "bold"),
                               bd=0, padx=16, pady=6, cursor="hand2",
                               activebackground="#1e40af")
        btn_buscar.pack(side=tk.LEFT)
        btn_buscar.bind("<Enter>", lambda e: btn_buscar.config(bg="#1e40af"))
        btn_buscar.bind("<Leave>", lambda e: btn_buscar.config(bg=ModernTheme.INFO))

        # Separador
        tk.Frame(inner, bg=ModernTheme.BORDER, width=1).pack(
            side=tk.LEFT, fill=tk.Y, padx=16, pady=4)

        # Filtro tipo
        tk.Label(inner, text="TIPO:",
                 font=("Segoe UI", 9, "bold"),
                 bg=ModernTheme.CARD_BG, fg=ModernTheme.TEXT_MUTED).pack(
            side=tk.LEFT, padx=8)

        self.tipo_var = tk.StringVar(value="todos")
        tipo_opts = [
            ("Todos",      "todos",     ModernTheme.TEXT),
            ("📥 Entrada", "entrada",   ModernTheme.SUCCESS),
            ("📤 Saída",   "saida",     ModernTheme.DANGER),
            ("🛒 Venda",   "venda",     ModernTheme.INFO),
            ("⚙️ Ajuste",  "ajuste",    ModernTheme.WARNING),
        ]
        for label, val, color in tipo_opts:
            rb = tk.Radiobutton(inner, text=label,
                                variable=self.tipo_var, value=val,
                                bg=ModernTheme.CARD_BG, fg=color,
                                font=("Segoe UI", 9, "bold"),
                                selectcolor=ModernTheme.CARD_BG,
                                activebackground=ModernTheme.CARD_BG,
                                command=self.refresh)
            rb.pack(side=tk.LEFT, padx=6)

        # Separador
        tk.Frame(inner, bg=ModernTheme.BORDER, width=1).pack(
            side=tk.LEFT, fill=tk.Y, padx=16, pady=4)

        # Período
        tk.Label(inner, text="PERÍODO:",
                 font=("Segoe UI", 9, "bold"),
                 bg=ModernTheme.CARD_BG, fg=ModernTheme.TEXT_MUTED).pack(
            side=tk.LEFT, padx=8)

        self.periodo_var = tk.StringVar(value="todos")
        periodo_opts = [
            ("Todos",      "todos"),
            ("Hoje",       "hoje"),
            ("7 dias",     "7d"),
            ("30 dias",    "30d"),
        ]
        for label, val in periodo_opts:
            rb = tk.Radiobutton(inner, text=label,
                                variable=self.periodo_var, value=val,
                                bg=ModernTheme.CARD_BG, fg=ModernTheme.TEXT,
                                font=("Segoe UI", 9, "bold"),
                                selectcolor=ModernTheme.CARD_BG,
                                activebackground=ModernTheme.CARD_BG,
                                command=self.refresh)
            rb.pack(side=tk.LEFT, padx=4)

        # Botão Atualizar
        btn_atualizar = tk.Button(inner, text="🔄  Atualizar", command=self.refresh,
                                    bg=ModernTheme.INFO, fg="white",
                                    font=("Segoe UI", 9, "bold"),
                                    bd=0, padx=16, pady=6, cursor="hand2",
                                    activebackground="#1e40af")
        btn_atualizar.pack(side=tk.RIGHT)
        btn_atualizar.bind("<Enter>", lambda e: btn_atualizar.config(bg="#1e40af"))
        btn_atualizar.bind("<Leave>", lambda e: btn_atualizar.config(bg=ModernTheme.INFO))

        # ═══════════════════════════════════════════════════════════════════
        # TABELA DE MOVIMENTAÇÕES
        # ═══════════════════════════════════════════════════════════════════
        table_card = tk.Frame(self.frame, bg=ModernTheme.CARD_BG,
                              highlightbackground=ModernTheme.BORDER,
                              highlightthickness=1)
        table_card.pack(fill=tk.BOTH, expand=True, padx=16, pady=8)

        # Header da tabela
        table_header = tk.Frame(table_card, bg=ModernTheme.PRIMARY, height=36)
        table_header.pack(fill=tk.X)
        tk.Label(table_header, text="📜  REGISTRO DE MOVIMENTAÇÕES",
                 font=("Segoe UI", 10, "bold"),
                 bg=ModernTheme.PRIMARY, fg="white").pack(
            side=tk.LEFT, padx=14, pady=6)

        self.contador_label = tk.Label(table_header, text="0 registros",
                 font=("Segoe UI", 9),
                 bg=ModernTheme.PRIMARY, fg="white")
        self.contador_label.pack(side=tk.RIGHT, padx=14, pady=6)

        # Tabela
        table_body = tk.Frame(table_card, bg=ModernTheme.CARD_BG)
        table_body.pack(fill=tk.BOTH, expand=True, padx=12, pady=12)

        columns = ("Data", "Produto", "Código", "Tipo",
                   "Qtd", "Anterior", "Nova", "Motivo", "Usuário")
        self.tree = ttk.Treeview(table_body, columns=columns,
                                 show="headings", height=20)

        widths = [130, 200, 90, 100, 55, 60, 60, 220, 110]
        for col, w in zip(columns, widths):
            self.tree.heading(col, text=col)
            self.tree.column(col, width=w)

        # Tags de cor por tipo + zebra striping
        self.tree.tag_configure("entrada",   foreground=ModernTheme.SUCCESS)
        self.tree.tag_configure("saida",     foreground=ModernTheme.DANGER)
        self.tree.tag_configure("ajuste",    foreground=ModernTheme.WARNING)
        self.tree.tag_configure("venda",     foreground=ModernTheme.INFO)
        self.tree.tag_configure("even",      background="#f8fafc")
        self.tree.tag_configure("odd",       background="white")

        sb = ttk.Scrollbar(table_body, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=sb.set)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb.pack(side=tk.RIGHT, fill=tk.Y)

        self.refresh()

    def refresh(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        _icons = {
            "entrada": "📥 entrada",
            "saida":   "📤 saída",
            "ajuste":  "⚙️ ajuste",
            "venda":   "🛒 venda",
        }

        # Filtros
        filtro_tipo = self.tipo_var.get()
        filtro_periodo = self.periodo_var.get()
        busca = self.busca_entry.get().strip().lower()
        if busca == "produto, código, motivo...":
            busca = ""

        # Contadores para estatísticas
        contagem = {"total": 0, "entrada": 0, "saida": 0, "venda": 0, "ajuste": 0}

        movs = self.controllers["movimentacao"].listar(limit=200) or []

        for idx, mov in enumerate(movs):
            tipo = str(mov.get("tipo", "")).lower()

            # Filtro tipo
            if filtro_tipo != "todos" and tipo != filtro_tipo:
                continue

            # Filtro período
            data_mov = mov.get("created_at")
            if filtro_periodo != "todos" and data_mov:
                if isinstance(data_mov, str):
                    try:
                        data_mov = datetime.strptime(data_mov[:10], "%Y-%m-%d")
                    except Exception:
                        data_mov = None
                if data_mov:
                    hoje = datetime.now()
                    if filtro_periodo == "hoje" and data_mov.date() != hoje.date():
                        continue
                    elif filtro_periodo == "7d" and (hoje - data_mov).days > 7:
                        continue
                    elif filtro_periodo == "30d" and (hoje - data_mov).days > 30:
                        continue

            # Filtro busca
            if busca:
                campos_busca = [
                    str(mov.get("produto_nome", "")).lower(),
                    str(mov.get("codigo", "")).lower(),
                    str(mov.get("motivo", "")).lower(),
                    str(mov.get("usuario", "")).lower(),
                ]
                if not any(busca in c for c in campos_busca):
                    continue

            # Contagem
            contagem["total"] += 1
            if tipo in contagem:
                contagem[tipo] += 1

            data = ""
            if mov.get("created_at"):
                if isinstance(mov["created_at"], datetime):
                    data = mov["created_at"].strftime("%d/%m/%Y %H:%M")
                else:
                    data = str(mov["created_at"])[:16]

            # Zebra striping + cor do tipo
            tag = (tipo, "even" if idx % 2 == 0 else "odd")

            self.tree.insert("", tk.END, tags=tag, values=(
                data,
                mov.get("produto_nome", ""),
                mov.get("codigo", ""),
                _icons.get(tipo, tipo),
                mov.get("quantidade", 0),
                mov.get("quantidade_anterior", 0),
                mov.get("quantidade_nova", 0),
                mov.get("motivo", "") or "",
                mov.get("usuario", "Sistema") or "Sistema",
            ))

        # Atualiza estatísticas
        for key in self.stats_labels:
            self.stats_labels[key].config(text=str(contagem.get(key, 0)))
        self.contador_label.config(text=f"{contagem['total']} registros")