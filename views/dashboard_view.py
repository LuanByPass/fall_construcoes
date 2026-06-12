"""Dashboard - FALL Construções (identidade visual verde)"""
import tkinter as tk
from tkinter import ttk
from datetime import datetime
from views.base_view import BaseView
from config import ModernTheme, LOJA_CONFIG

try:
    from utils.logger import Logger
except Exception:
    class Logger:
        @classmethod
        def log(cls, msg, level="INFO"):
            print(f"[{level}] {msg}")


class DashboardView(BaseView):
    # Paleta verde FALL (mesma do login)
    FALL_GREEN      = "#064e3b"
    FALL_ACCENT     = "#10b981"
    FALL_ACCENT_HOVER = "#059669"
    FALL_LIGHT      = "#d1fae5"
    FALL_DARK       = "#022c22"

    def __init__(self, parent, controllers):
        super().__init__(parent, None)
        self.controllers = controllers
        self._setup_styles()
        self.build()

    def _setup_styles(self):
        """Configura estilos ttk para scrollbars verdes"""
        style = ttk.Style()
        # Scrollbar vertical
        style.configure("Green.Vertical.TScrollbar",
                        background=self.FALL_ACCENT,
                        troughcolor="#e2e8f0",
                        bordercolor="#e2e8f0",
                        arrowcolor="white",
                        width=12)
        style.map("Green.Vertical.TScrollbar",
                  background=[("active", self.FALL_ACCENT_HOVER),
                              ("pressed", self.FALL_ACCENT_HOVER)],
                  arrowcolor=[("active", "white")])

    def build(self):
        self.frame = tk.Frame(self.parent, bg=ModernTheme.BG)


        # ═══════════════════════════════════════════════════════════════════
        # FAIXA DE KPIs (verde)
        # ═══════════════════════════════════════════════════════════════════
        kpi_frame = tk.Frame(self.frame, bg=ModernTheme.BG)
        kpi_frame.pack(fill=tk.X, padx=16, pady=(16, 12))

        self.kpi_cards = {}
        kpi_config = [
            ("produtos",   "📦", "Produtos",       "Total em catálogo",   self.FALL_ACCENT),
            ("valor",      "💰", "Valor Estoque",  "Em mercadoria",       "#059669"),
            ("alertas",    "⚠️", "Alertas",        "Estoque crítico",     "#ef4444"),
            ("categorias", "🏷️", "Categorias",     "Segmentações",        "#0d9488"),
            ("vendas",     "📊", "Vendas Hoje",    "Transações",          "#f59e0b"),
            ("faturamento","💵", "Faturamento",    "Total em vendas",     self.FALL_ACCENT),
        ]

        for key, icon, title, subtitle, color in kpi_config:
            card = tk.Frame(kpi_frame, bg=ModernTheme.CARD_BG,
                            highlightbackground=color,
                            highlightthickness=2)
            card.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=4)

            tk.Frame(card, bg=color, height=4).pack(fill=tk.X)

            inner = tk.Frame(card, bg=ModernTheme.CARD_BG, padx=14, pady=12)
            inner.pack(fill=tk.BOTH, expand=True)

            header_row = tk.Frame(inner, bg=ModernTheme.CARD_BG)
            header_row.pack(fill=tk.X)

            tk.Label(header_row, text=icon,
                     font=("Segoe UI", 20),
                     bg=ModernTheme.CARD_BG, fg=color).pack(side=tk.LEFT)

            tk.Label(header_row, text=title,
                     font=("Segoe UI", 9, "bold"),
                     bg=ModernTheme.CARD_BG, fg=ModernTheme.TEXT_MUTED).pack(
                side=tk.LEFT, padx=(8, 0), pady=(4, 0))

            self.kpi_cards[key] = tk.Label(inner, text="—",
                     font=("Segoe UI", 22, "bold"),
                     bg=ModernTheme.CARD_BG, fg=ModernTheme.TEXT)
            self.kpi_cards[key].pack(anchor=tk.W, pady=(6, 2))

            tk.Label(inner, text=subtitle,
                     font=("Segoe UI", 8),
                     bg=ModernTheme.CARD_BG, fg=ModernTheme.TEXT_MUTED).pack(
                anchor=tk.W)

        # ═══════════════════════════════════════════════════════════════════
        # CONTEÚDO PRINCIPAL (2 colunas)
        # ═══════════════════════════════════════════════════════════════════
        content = tk.Frame(self.frame, bg=ModernTheme.BG)
        content.pack(fill=tk.BOTH, expand=True, padx=16, pady=8)

        # ── Coluna Esquerda: Estoque Crítico ───────────────────────────────
        left = tk.Frame(content, bg=ModernTheme.BG)
        left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 8))

        alert_card = tk.Frame(left, bg=ModernTheme.CARD_BG,
                              highlightbackground=ModernTheme.BORDER,
                              highlightthickness=1)
        alert_card.pack(fill=tk.BOTH, expand=True)

        # Header vermelho (alerta)
        alert_header = tk.Frame(alert_card, bg="#dc2626", height=40)
        alert_header.pack(fill=tk.X)
        alert_header.pack_propagate(False)

        tk.Label(alert_header, text="⚠️  ESTOQUE CRÍTICO",
                 font=("Segoe UI", 10, "bold"),
                 bg="#dc2626", fg="white").pack(
            side=tk.LEFT, padx=14, pady=8)

        self.alert_count = tk.Label(alert_header, text="0 alertas",
                 font=("Segoe UI", 9),
                 bg="#dc2626", fg="white")
        self.alert_count.pack(side=tk.RIGHT, padx=14, pady=8)

        # Corpo da tabela
        alert_body = tk.Frame(alert_card, bg=ModernTheme.CARD_BG)
        alert_body.pack(fill=tk.BOTH, expand=True, padx=12, pady=12)

        alert_cols = ("Código", "Produto", "Qtd", "Mín", "Status")
        self.alert_tree = ttk.Treeview(alert_body, columns=alert_cols,
                                       show="headings", height=12)
        for col, w in zip(alert_cols, [90, 220, 60, 60, 100]):
            self.alert_tree.heading(col, text=col)
            self.alert_tree.column(col, width=w)

        self.alert_tree.tag_configure("critico",
                                      background="#fef2f2",
                                      foreground="#dc2626")
        self.alert_tree.tag_configure("baixo",
                                      background="#fffbeb",
                                      foreground="#b45309")
        self.alert_tree.tag_configure("even", background="#f8fafc")
        self.alert_tree.tag_configure("odd", background="white")

        # ✅ SCROLLBAR VERDE
        sb_alert = ttk.Scrollbar(alert_body, orient=tk.VERTICAL,
                                   command=self.alert_tree.yview,
                                   style="Green.Vertical.TScrollbar")
        self.alert_tree.configure(yscrollcommand=sb_alert.set)
        self.alert_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb_alert.pack(side=tk.RIGHT, fill=tk.Y)

        # ── Coluna Direita: Últimas Vendas ─────────────────────────────────
        right = tk.Frame(content, bg=ModernTheme.BG)
        right.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(8, 0))

        venda_card = tk.Frame(right, bg=ModernTheme.CARD_BG,
                              highlightbackground=ModernTheme.BORDER,
                              highlightthickness=1)
        venda_card.pack(fill=tk.BOTH, expand=True)

        # Header verde (vendas)
        venda_header = tk.Frame(venda_card, bg=self.FALL_ACCENT, height=40)
        venda_header.pack(fill=tk.X)
        venda_header.pack_propagate(False)

        tk.Label(venda_header, text="🛒  ÚLTIMAS VENDAS",
                 font=("Segoe UI", 10, "bold"),
                 bg=self.FALL_ACCENT, fg="white").pack(
            side=tk.LEFT, padx=14, pady=8)

        self.venda_count = tk.Label(venda_header, text="0 vendas",
                 font=("Segoe UI", 9),
                 bg=self.FALL_ACCENT, fg="white")
        self.venda_count.pack(side=tk.RIGHT, padx=14, pady=8)

        # Corpo da tabela
        venda_body = tk.Frame(venda_card, bg=ModernTheme.CARD_BG)
        venda_body.pack(fill=tk.BOTH, expand=True, padx=12, pady=12)

        venda_cols = ("Nº", "Cliente", "Total", "Pagamento", "Status")
        self.venda_tree = ttk.Treeview(venda_body, columns=venda_cols,
                                       show="headings", height=12)
        for col, w in zip(venda_cols, [130, 150, 100, 100, 110]):
            self.venda_tree.heading(col, text=col)
            self.venda_tree.column(col, width=w)

        self.venda_tree.tag_configure("pago",
                                      foreground="#15803d")
        self.venda_tree.tag_configure("pendente",
                                      foreground="#b45309")
        self.venda_tree.tag_configure("cancelado",
                                      foreground="#dc2626")
        self.venda_tree.tag_configure("even", background="#f8fafc")
        self.venda_tree.tag_configure("odd", background="white")

        # ✅ SCROLLBAR VERDE
        sb_venda = ttk.Scrollbar(venda_body, orient=tk.VERTICAL,
                                 command=self.venda_tree.yview,
                                 style="Green.Vertical.TScrollbar")
        self.venda_tree.configure(yscrollcommand=sb_venda.set)
        self.venda_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb_venda.pack(side=tk.RIGHT, fill=tk.Y)

        # ═══════════════════════════════════════════════════════════════════
        # RODAPÉ: RESUMO + ATUALIZAR
        # ═══════════════════════════════════════════════════════════════════
        footer = tk.Frame(self.frame, bg=ModernTheme.BG)
        footer.pack(fill=tk.X, padx=16, pady=(12, 16))

        # Info de última atualização
        self.last_update = tk.Label(footer,
                 text="Última atualização: —",
                 font=("Segoe UI", 9),
                 bg=ModernTheme.BG, fg=ModernTheme.TEXT_MUTED)
        self.last_update.pack(side=tk.LEFT)

        # Botão atualizar (verde)
        btn = tk.Button(footer, text="🔄  ATUALIZAR DASHBOARD",
                        command=self.refresh,
                        bg=self.FALL_ACCENT, fg="white",
                        font=("Segoe UI", 10, "bold"),
                        bd=0, padx=20, pady=10, cursor="hand2",
                        activebackground=self.FALL_ACCENT_HOVER)
        btn.pack(side=tk.RIGHT)
        btn.bind("<Enter>", lambda e: btn.config(bg=self.FALL_ACCENT_HOVER))
        btn.bind("<Leave>", lambda e: btn.config(bg=self.FALL_ACCENT))

        self.refresh()

    # ─────────────────────────────────────────────────────────────────────────
    def refresh(self):
        # ── KPIs ───────────────────────────────────────────────────────────
        try:
            produtos = self.controllers["produto"].listar()
            total_produtos = len(produtos) if produtos else 0
        except Exception as e:
            Logger.log(f"Erro produtos: {e}", "ERROR")
            total_produtos = 0

        try:
            valor_total = self.controllers["produto"].valor_total() or 0
        except Exception as e:
            Logger.log(f"Erro valor_total: {e}", "ERROR")
            valor_total = 0

        try:
            baixo_list = self.controllers["produto"].baixo_estoque() or []
            baixo_qtd = len(baixo_list)
        except Exception as e:
            Logger.log(f"Erro baixo_estoque: {e}", "ERROR")
            baixo_list = []
            baixo_qtd = 0

        try:
            cats = self.controllers["categoria"].listar() or []
            total_cats = len(cats)
        except Exception as e:
            Logger.log(f"Erro categorias: {e}", "ERROR")
            total_cats = 0

        vendas = []
        faturamento = 0
        try:
            raw = self.controllers["venda"].listar_vendas(5) or []
            vendas = [v for v in raw if v]
            faturamento = sum(float(v.get("total", 0) or 0) for v in vendas)
        except Exception as e:
            Logger.log(f"Erro vendas: {e}", "ERROR")

        # Atualiza KPIs
        kpi_values = {
            "produtos":    str(total_produtos),
            "valor":       f"R$ {valor_total:,.2f}",
            "alertas":     str(baixo_qtd),
            "categorias":  str(total_cats),
            "vendas":      str(len(vendas)),
            "faturamento": f"R$ {faturamento:,.2f}",
        }
        for key, val in kpi_values.items():
            if key in self.kpi_cards:
                self.kpi_cards[key].config(text=val)

        # Alerta visual no KPI de alertas se houver críticos
        if baixo_qtd > 0:
            self.kpi_cards["alertas"].config(fg="#ef4444")
        else:
            self.kpi_cards["alertas"].config(fg=ModernTheme.TEXT)

        # ── Estoque Crítico ────────────────────────────────────────────────
        for row in self.alert_tree.get_children():
            self.alert_tree.delete(row)

        for idx, prod in enumerate((baixo_list or [])[:12]):
            if not prod or not isinstance(prod, dict):
                continue
            qtd = prod.get("quantidade", 0)
            status = "🔴 ESGOTADO" if qtd == 0 else "🟡 BAIXO"
            tag = "critico" if qtd == 0 else "baixo"
            row_tag = (tag, "even" if idx % 2 == 0 else "odd")

            self.alert_tree.insert("", tk.END, tags=row_tag, values=(
                prod.get("codigo", ""),
                str(prod.get("nome", ""))[:28],
                qtd,
                prod.get("quantidade_minima", 0),
                status,
            ))

        self.alert_count.config(text=f"{baixo_qtd} alertas")

        # ── Últimas Vendas ─────────────────────────────────────────────────
        for row in self.venda_tree.get_children():
            self.venda_tree.delete(row)

        _icons = {"pago": "✅", "pendente": "⏳", "cancelado": "❌"}
        for idx, v in enumerate(vendas):
            if not v or not isinstance(v, dict):
                continue
            status = v.get("status", "pendente")
            icon = _icons.get(status, "•")
            tag = (status, "even" if idx % 2 == 0 else "odd")

            try:
                self.venda_tree.insert("", tk.END, tags=tag, values=(
                    v.get("numero_venda", ""),
                    str(v.get("cliente_nome") or "Avulso")[:18],
                    f"R$ {float(v.get('total', 0) or 0):.2f}",
                    v.get("forma_pagamento", ""),
                    f"{icon} {status.upper()}",
                ))
            except Exception as e:
                Logger.log(f"Erro venda row: {e}", "ERROR")

        self.venda_count.config(text=f"{len(vendas)} vendas")

        # ── Timestamp ──────────────────────────────────────────────────────
        self.last_update.config(
            text=f"Última atualização: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}"
        )