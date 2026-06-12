"""Tela de Categorias - FALL Construções (reestilizada premium)"""
import tkinter as tk
from tkinter import ttk, messagebox
from views.base_view import BaseView
from config import ModernTheme
from datetime import datetime

try:
    from utils.logger import Logger
except Exception:
    class Logger:
        @classmethod
        def log(cls, msg, level="INFO"):
            print(f"[{level}] {msg}")


class CategoriasView(BaseView):
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
            ("total",     "🏷️ Categorias",    ModernTheme.PRIMARY,  "#1e40af"),
            ("produtos",  "📦 Produtos",       ModernTheme.INFO,     "#1e40af"),
            ("estoque",   "📊 Estoque Total",  ModernTheme.SUCCESS,  "#15803d"),
            ("valor",     "💰 Valor Estoque",  ModernTheme.WARNING,  "#b45309"),
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
        # TOOLBAR
        # ═══════════════════════════════════════════════════════════════════
        toolbar = tk.Frame(self.frame, bg=ModernTheme.BG)
        toolbar.pack(fill=tk.X, padx=16, pady=8)

        self.styled_button(toolbar, "➕  Nova Categoria", self._open_form,
                           ModernTheme.SUCCESS, icon="").pack(side=tk.LEFT)
        self.styled_button(toolbar, "✏️  Editar", self._editar,
                           ModernTheme.INFO, icon="").pack(side=tk.LEFT, padx=6)
        self.styled_button(toolbar, "🗑️  Excluir", self._excluir,
                           ModernTheme.DANGER, icon="").pack(side=tk.LEFT)
        self.styled_button(toolbar, "🔄  Atualizar", self.refresh,
                           icon="").pack(side=tk.RIGHT)

        # ═══════════════════════════════════════════════════════════════════
        # TABELA
        # ═══════════════════════════════════════════════════════════════════
        card = tk.Frame(self.frame, bg=ModernTheme.CARD_BG,
                        highlightbackground=ModernTheme.BORDER,
                        highlightthickness=1)
        card.pack(fill=tk.BOTH, expand=True, padx=16, pady=(0, 16))

        # Header
        table_header = tk.Frame(card, bg=ModernTheme.PRIMARY, height=36)
        table_header.pack(fill=tk.X)
        tk.Label(table_header, text="🏷️  CATEGORIAS CADASTRADAS",
                 font=("Segoe UI", 10, "bold"),
                 bg=ModernTheme.PRIMARY, fg="white").pack(
            side=tk.LEFT, padx=14, pady=6)

        self.contador_label = tk.Label(table_header, text="0 categorias",
                 font=("Segoe UI", 9),
                 bg=ModernTheme.PRIMARY, fg="white")
        self.contador_label.pack(side=tk.RIGHT, padx=14, pady=6)

        # Body
        table_body = tk.Frame(card, bg=ModernTheme.CARD_BG)
        table_body.pack(fill=tk.BOTH, expand=True, padx=12, pady=12)

        columns = ("ID", "Nome", "Descrição", "Produtos", "Criado em")
        self.tree = ttk.Treeview(table_body, columns=columns,
                                 show="headings", height=22)

        widths = [60, 220, 340, 80, 140]
        for col, w in zip(columns, widths):
            self.tree.heading(col, text=col)
            self.tree.column(col, width=w)

        self.tree.tag_configure("even", background="#f8fafc")
        self.tree.tag_configure("odd",  background="white")

        sb = ttk.Scrollbar(table_body, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=sb.set)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb.pack(side=tk.RIGHT, fill=tk.Y)

        self.tree.bind("<Double-1>", lambda e: self._editar())
        self.refresh()

    # ─────────────────────────────────────────────────────────────────────────
    def refresh(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        categorias = self.controllers["categoria"].listar() or []
        total_produtos = 0
        total_estoque = 0
        total_valor = 0.0

        for idx, cat in enumerate(categorias):
            # Busca estatísticas da categoria se disponível
            stats = {}
            try:
                stats = self.controllers["categoria"].get_estatisticas(cat["id"]) or {}
            except Exception:
                pass

            qtd_produtos = stats.get('total_produtos', 0)
            estoque = stats.get('estoque_total', 0)
            valor = float(stats.get('valor_estoque', 0) or 0)

            total_produtos += qtd_produtos
            total_estoque += estoque
            total_valor += valor

            data = ""
            if cat.get("created_at"):
                if isinstance(cat["created_at"], datetime):
                    data = cat["created_at"].strftime("%d/%m/%Y")
                else:
                    data = str(cat["created_at"])[:10]

            tag = "even" if idx % 2 == 0 else "odd"

            self.tree.insert("", tk.END, tags=(tag,), values=(
                cat["id"],
                cat["nome"],
                cat.get("descricao", ""),
                qtd_produtos,
                data,
            ))

        # Atualiza estatísticas
        self.stats_labels["total"].config(text=str(len(categorias)))
        self.stats_labels["produtos"].config(text=str(total_produtos))
        self.stats_labels["estoque"].config(text=str(total_estoque))
        self.stats_labels["valor"].config(text=f"R$ {total_valor:,.2f}")
        self.contador_label.config(text=f"{len(categorias)} categorias")

    def _get_selected(self):
        sel = self.tree.selection()
        if not sel:
            self.show_message("Aviso", "Selecione uma categoria", "warning")
            return None
        return self.tree.item(sel[0])["values"][0]

    def _open_form(self, cat_id=None):
        cat = None
        if cat_id:
            for c in self.controllers["categoria"].listar():
                if c["id"] == cat_id:
                    cat = c
                    break

        title = "✏️  Editar Categoria" if cat else "➕  Nova Categoria"
        dlg = self.make_dialog(title, 440, 320)

        tk.Frame(dlg, bg=ModernTheme.PRIMARY, height=4).pack(fill=tk.X)
        tk.Label(dlg, text=title, font=ModernTheme.FONT_XL,
                 bg=ModernTheme.BG, fg=ModernTheme.TEXT).pack(
            anchor=tk.W, padx=20, pady=14)

        nome_entry = self.form_field(dlg, "Nome *",
                                     value=cat["nome"] if cat else "")
        desc_entry = self.form_field(dlg, "Descrição",
                                     value=cat.get("descricao", "") if cat else "")

        tk.Frame(dlg, bg=ModernTheme.BORDER, height=1).pack(
            fill=tk.X, padx=20, pady=12)

        def save():
            if cat_id:
                ok, msg = self.controllers["categoria"].atualizar(
                    cat_id, nome_entry.get(), desc_entry.get())
            else:
                ok, msg = self.controllers["categoria"].criar(
                    nome_entry.get(), desc_entry.get())
            if ok:
                self.show_message("Sucesso", msg)
                dlg.destroy()
                self.refresh()
            else:
                self.show_message("Erro", msg, "error")

        btn = tk.Button(dlg, text="💾  SALVAR", command=save,
                        bg=ModernTheme.SUCCESS, fg="white",
                        font=("Segoe UI", 12, "bold"),
                        bd=0, pady=10, cursor="hand2",
                        activebackground="#15803d")
        btn.pack(fill=tk.X, padx=20)
        btn.bind("<Enter>", lambda e: btn.config(bg="#15803d"))
        btn.bind("<Leave>", lambda e: btn.config(bg=ModernTheme.SUCCESS))

    def _editar(self):
        cid = self._get_selected()
        if cid:
            self._open_form(cid)

    def _excluir(self):
        cid = self._get_selected()
        if not cid:
            return
        if messagebox.askyesno("Confirmar", "Deseja excluir esta categoria?"):
            ok, msg = self.controllers["categoria"].deletar(cid)
            if ok:
                self.show_message("Sucesso", msg)
                self.refresh()
            else:
                self.show_message("Erro", msg, "error")