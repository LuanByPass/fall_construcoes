"""Tela de Produtos - FALL Construções (reestilizada)"""
import tkinter as tk
from tkinter import ttk, messagebox
from views.base_view import BaseView
from config import ModernTheme

try:
    from utils.logger import Logger
except Exception:
    class Logger:
        @classmethod
        def log(cls, msg, level="INFO"):
            print(f"[{level}] {msg}")


class ProdutosView(BaseView):
    def __init__(self, parent, controllers):
        super().__init__(parent, None)
        self.controllers = controllers
        self.build()

    def build(self):
        self.frame = tk.Frame(self.parent, bg=ModernTheme.BG)

        # ═══════════════════════════════════════════════════════════════════
        # TOOLBAR - Card de busca + Ações principais
        # ═══════════════════════════════════════════════════════════════════
        toolbar = tk.Frame(self.frame, bg=ModernTheme.BG)
        toolbar.pack(fill=tk.X, padx=16, pady=12)

        # ── Card de Busca ──
        search_card = tk.Frame(toolbar, bg=ModernTheme.CARD_BG,
                               highlightbackground=ModernTheme.BORDER,
                               highlightthickness=1)
        search_card.pack(side=tk.LEFT)
        tk.Frame(search_card, bg=ModernTheme.INFO, height=3).pack(fill=tk.X)

        search_inner = tk.Frame(search_card, bg=ModernTheme.CARD_BG, padx=12, pady=8)
        search_inner.pack(fill=tk.X)

        tk.Label(search_inner, text="🔍", font=("Segoe UI", 13),
                 bg=ModernTheme.CARD_BG, fg=ModernTheme.INFO).pack(
            side=tk.LEFT, padx=(0, 8))
        self.search_entry = self.styled_entry(search_inner,
                                              "Buscar por nome, código ou código de barras...",
                                              width=42)
        self.search_entry.pack(side=tk.LEFT, padx=(0, 8))
        self.search_entry.bind("<Return>", lambda e: self._search())

        btn_buscar = tk.Button(search_inner, text="Buscar", command=self._search,
                               bg=ModernTheme.INFO, fg="white",
                               font=("Segoe UI", 9, "bold"),
                               bd=0, padx=16, pady=6, cursor="hand2",
                               activebackground="#1e40af")
        btn_buscar.pack(side=tk.LEFT)
        btn_buscar.bind("<Enter>", lambda e: btn_buscar.config(bg="#1e40af"))
        btn_buscar.bind("<Leave>", lambda e: btn_buscar.config(bg=ModernTheme.INFO))

        # ── Ações Principais ──
        actions_card = tk.Frame(toolbar, bg=ModernTheme.CARD_BG,
                                highlightbackground=ModernTheme.BORDER,
                                highlightthickness=1)
        actions_card.pack(side=tk.RIGHT)
        tk.Frame(actions_card, bg=ModernTheme.SUCCESS, height=3).pack(fill=tk.X)

        actions_inner = tk.Frame(actions_card, bg=ModernTheme.CARD_BG, padx=10, pady=8)
        actions_inner.pack(fill=tk.X)

        tk.Label(actions_inner, text="AÇÕES",
                 font=("Segoe UI", 8, "bold"),
                 bg=ModernTheme.CARD_BG, fg=ModernTheme.TEXT_MUTED).pack(
            side=tk.LEFT, padx=(0, 10))

        acoes = [
            ("➕  Novo",      self._open_form, ModernTheme.SUCCESS, "#15803d"),
            ("✏️  Editar",    self._editar,    ModernTheme.INFO,    "#1e40af"),
            ("📦  Movimentar", self._movimentar, ModernTheme.WARNING, "#b45309"),
            ("🗑️  Excluir",   self._excluir,   ModernTheme.DANGER,  "#b91c1c"),
        ]
        for label, cmd, color, hover in acoes:
            btn = tk.Button(actions_inner, text=label, command=cmd,
                            bg=color, fg="white",
                            font=("Segoe UI", 9, "bold"),
                            bd=0, padx=12, pady=6, cursor="hand2",
                            activebackground=hover)
            btn.pack(side=tk.LEFT, padx=3)
            btn.bind("<Enter>", lambda e, c=hover: btn.config(bg=c))
            btn.bind("<Leave>", lambda e, c=color: btn.config(bg=c))

        # ═══════════════════════════════════════════════════════════════════
        # ESTATÍSTICAS RÁPIDAS
        # ═══════════════════════════════════════════════════════════════════
        stats_frame = tk.Frame(self.frame, bg=ModernTheme.BG)
        stats_frame.pack(fill=tk.X, padx=16, pady=(0, 8))

        self.stats_labels = {}
        stats_config = [
            ("total", "📦 Total", ModernTheme.PRIMARY, "#1e40af"),
            ("baixo", "⚠️ Estoque Baixo", ModernTheme.WARNING, "#b45309"),
            ("valor", "💰 Valor Estoque", ModernTheme.SUCCESS, "#15803d"),
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
            self.stats_labels[key] = tk.Label(inner, text="—",
                     font=("Segoe UI", 18, "bold"),
                     bg=ModernTheme.CARD_BG, fg=ModernTheme.TEXT)
            self.stats_labels[key].pack(anchor=tk.W)

        # ═══════════════════════════════════════════════════════════════════
        # TABELA DE PRODUTOS - Card com header
        # ═══════════════════════════════════════════════════════════════════
        table_card = tk.Frame(self.frame, bg=ModernTheme.CARD_BG,
                              highlightbackground=ModernTheme.BORDER,
                              highlightthickness=1)
        table_card.pack(fill=tk.BOTH, expand=True, padx=16, pady=(0, 16))

        # Header da tabela
        table_header = tk.Frame(table_card, bg=ModernTheme.PRIMARY, height=36)
        table_header.pack(fill=tk.X)
        tk.Label(table_header, text="📦  LISTA DE PRODUTOS",
                 font=("Segoe UI", 10, "bold"),
                 bg=ModernTheme.PRIMARY, fg="white").pack(
            side=tk.LEFT, padx=14, pady=6)

        # Contador de itens
        self.contador_label = tk.Label(table_header, text="0 produtos",
                 font=("Segoe UI", 9),
                 bg=ModernTheme.PRIMARY, fg="white")
        self.contador_label.pack(side=tk.RIGHT, padx=14, pady=6)

        # Tabela
        table_body = tk.Frame(table_card, bg=ModernTheme.CARD_BG)
        table_body.pack(fill=tk.BOTH, expand=True, padx=12, pady=12)

        columns = ("ID", "Código", "Cód. Barras", "Nome", "Categoria",
                   "Qtd", "Mín", "Preço", "Atacado", "Local", "Marca")
        self.tree = ttk.Treeview(table_body, columns=columns,
                                 show="headings", height=18)

        widths = [40, 80, 110, 240, 120, 55, 50, 90, 90, 100, 100]
        for col, w in zip(columns, widths):
            self.tree.heading(col, text=col)
            self.tree.column(col, width=w)

        # Estilos para a tabela
        self.tree.tag_configure("baixo",
                                background="#fef2f2",
                                foreground="#dc2626")
        self.tree.tag_configure("even", background="#f8fafc")
        self.tree.tag_configure("odd", background="white")
        self.tree.tag_configure("destaque",
                                background="#eff6ff",
                                foreground="#1e40af")

        sb = ttk.Scrollbar(table_body, orient=tk.VERTICAL,
                           command=self.tree.yview)
        self.tree.configure(yscrollcommand=sb.set)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb.pack(side=tk.RIGHT, fill=tk.Y)

        self.tree.bind("<Double-1>", lambda e: self._editar())

        self.refresh()

    # ─────────────────────────────────────────────────────────────────────────
    def _search(self):
        busca = self.search_entry.get()
        placeholder = "Buscar por nome, código ou código de barras..."
        if busca in (placeholder, ""):
            busca = ""
        self.refresh(busca)

    def refresh(self, busca=""):
        for item in self.tree.get_children():
            self.tree.delete(item)

        produtos = self.controllers["produto"].listar(busca)
        total_valor = 0
        total_baixo = 0

        for idx, prod in enumerate(produtos):
            tag = "baixo" if prod["quantidade"] <= prod["quantidade_minima"] else ""
            if tag == "baixo":
                total_baixo += 1

            # Zebra striping + destaque para estoque baixo
            row_tag = tag if tag else ("even" if idx % 2 == 0 else "odd")

            total_valor += prod["quantidade"] * prod.get("preco_custo", prod["preco_venda"])

            self.tree.insert("", tk.END, tags=(row_tag,), values=(
                prod["id"], prod["codigo"],
                prod.get("codigo_barras", ""),
                prod["nome"],
                prod.get("categoria_nome", "—"),
                prod["quantidade"],
                prod["quantidade_minima"],
                f"R$ {prod['preco_venda']:.2f}",
                f"R$ {prod['preco_atacado']:.2f}" if prod.get("preco_atacado") else "—",
                prod.get("localizacao", ""),
                prod.get("marca", ""),
            ))

        # Atualiza estatísticas
        self.stats_labels["total"].config(text=str(len(produtos)))
        self.stats_labels["baixo"].config(text=str(total_baixo))
        self.stats_labels["valor"].config(text=f"R$ {total_valor:,.2f}")

        # Atualiza contador
        self.contador_label.config(text=f"{len(produtos)} produtos{' encontrados' if busca else ''}")

    def _get_selected(self):
        sel = self.tree.selection()
        if not sel:
            self.show_message("Aviso", "Selecione um produto", "warning")
            return None
        return self.tree.item(sel[0])["values"][0]

    # ─── Formulário novo / editar ─────────────────────────────────────────────
    def _open_form(self, produto_id=None):
        produto = self.controllers["produto"].obter(produto_id) if produto_id else None
        title   = "✏️  Editar Produto" if produto else "➕  Novo Produto"
        dlg     = self.make_dialog(title, width=580, height=720)

        # Header
        tk.Frame(dlg, bg=ModernTheme.PRIMARY, height=4).pack(fill=tk.X)
        tk.Label(dlg, text=title, font=ModernTheme.FONT_XL,
                 bg=ModernTheme.BG, fg=ModernTheme.TEXT).pack(
            anchor=tk.W, padx=20, pady=14)

        # Scroll
        canvas = tk.Canvas(dlg, bg=ModernTheme.BG, bd=0, highlightthickness=0)
        sb_v   = ttk.Scrollbar(dlg, orient=tk.VERTICAL, command=canvas.yview)
        inner  = tk.Frame(canvas, bg=ModernTheme.BG)
        inner.bind("<Configure>",
                   lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=inner, anchor="nw", width=560)
        canvas.configure(yscrollcommand=sb_v.set)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb_v.pack(side=tk.RIGHT, fill=tk.Y)

        fields = {}
        field_cfg = [
            ("codigo",            "Código *",            25),
            ("codigo_barras",     "Código de Barras",    25),
            ("nome",              "Nome *",               52),
            ("descricao",         "Descrição",            52),
            ("quantidade",        "Quantidade Inicial *", 25),
            ("quantidade_minima", "Qtd. Mínima",          25),
            ("preco_custo",       "Preço de Custo *",     25),
            ("preco_venda",       "Preço de Venda *",     25),
            ("preco_atacado",     "Preço Atacado",        25),
            ("unidade",           "Unidade (UN/SC/KG)",   25),
            ("localizacao",       "Localização",          52),
            ("fornecedor",        "Fornecedor",           52),
            ("peso_kg",           "Peso (kg)",            25),
            ("dimensoes",         "Dimensões",            25),
            ("marca",             "Marca",                25),
        ]

        row_frame = None
        for i, (key, label, _) in enumerate(field_cfg):
            if i % 2 == 0:
                row_frame = tk.Frame(inner, bg=ModernTheme.BG)
                row_frame.pack(fill=tk.X, padx=20, pady=4)

            col_frame = tk.Frame(row_frame, bg=ModernTheme.BG)
            col_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 8))

            tk.Label(col_frame, text=label,
                     font=("Segoe UI", 9, "bold"),
                     bg=ModernTheme.BG, fg=ModernTheme.TEXT_LIGHT,
                     anchor=tk.W).pack(fill=tk.X, pady=(0, 2))
            e = self.styled_entry(col_frame, width=24)
            if produto and produto.get(key):
                e.delete(0, tk.END)
                e.insert(0, str(produto[key]))
            e.pack(fill=tk.X)
            fields[key] = e

        # Categoria
        cat_frame = tk.Frame(inner, bg=ModernTheme.BG)
        cat_frame.pack(fill=tk.X, padx=20, pady=(8, 4))
        tk.Label(cat_frame, text="Categoria",
                 font=("Segoe UI", 9, "bold"),
                 bg=ModernTheme.BG, fg=ModernTheme.TEXT_LIGHT).pack(anchor=tk.W, pady=(0, 2))
        cats    = self.controllers["categoria"].listar()
        cat_var = tk.StringVar()
        cat_cb  = ttk.Combobox(cat_frame, textvariable=cat_var,
                               values=[c["nome"] for c in cats],
                               state="readonly", font=ModernTheme.FONT_MD)
        cat_cb.pack(fill=tk.X)
        if produto and produto.get("categoria_nome"):
            cat_cb.set(produto["categoria_nome"])

        def save():
            dados = {}
            placeholders = {v[0]: v[1] for v in field_cfg}
            for k, entry in fields.items():
                val = entry.get()
                if val and val != placeholders.get(k, ""):
                    dados[k] = val
            cat_id = next((c["id"] for c in cats
                           if c["nome"] == cat_var.get()), None)
            dados["categoria_id"] = cat_id
            if produto_id:
                ok, msg = self.controllers["produto"].atualizar(produto_id, dados)
            else:
                ok, msg = self.controllers["produto"].criar(dados)
            if ok:
                self.show_message("Sucesso", msg)
                dlg.destroy()
                self.refresh()
            else:
                self.show_message("Erro", msg, "error")

        tk.Frame(inner, bg=ModernTheme.BORDER, height=1).pack(
            fill=tk.X, padx=20, pady=12)
        self.styled_button(inner, "Salvar Produto", save,
                           ModernTheme.SUCCESS, icon="💾").pack(padx=20, pady=8)

    def _editar(self):
        pid = self._get_selected()
        if pid:
            self._open_form(pid)

    def _excluir(self):
        pid = self._get_selected()
        if not pid:
            return
        if messagebox.askyesno("Confirmar exclusão",
                               "Deseja realmente excluir este produto?"):
            ok, msg = self.controllers["produto"].deletar(pid)
            if ok:
                self.show_message("Sucesso", msg)
                self.refresh()
            else:
                self.show_message("Erro", msg, "error")

    def _movimentar(self):
        pid = self._get_selected()
        if not pid:
            return
        produto = self.controllers["produto"].obter(pid)
        if not produto:
            return

        dlg = self.make_dialog(f"📦  Movimentar Estoque", 420, 420)
        dlg.configure(bg=ModernTheme.BG)

        # Header colorido
        header = tk.Frame(dlg, bg=ModernTheme.PRIMARY, height=50)
        header.pack(fill=tk.X)
        tk.Label(header, text=f"📦  {produto['nome']}",
                 font=("Segoe UI", 14, "bold"),
                 bg=ModernTheme.PRIMARY, fg="white").pack(
            side=tk.LEFT, padx=20, pady=10)

        # Card de info do produto
        info_card = tk.Frame(dlg, bg=ModernTheme.CARD_BG,
                             highlightbackground=ModernTheme.BORDER,
                             highlightthickness=1)
        info_card.pack(fill=tk.X, padx=16, pady=12)
        tk.Frame(info_card, bg=ModernTheme.INFO, height=3).pack(fill=tk.X)

        info_inner = tk.Frame(info_card, bg=ModernTheme.CARD_BG, padx=16, pady=10)
        info_inner.pack(fill=tk.X)

        tk.Label(info_inner, text=f"Estoque Atual: {produto['quantidade']} {produto.get('unidade', 'UN')}",
                 font=("Segoe UI", 12, "bold"),
                 bg=ModernTheme.CARD_BG, fg=ModernTheme.INFO).pack(anchor=tk.W)
        tk.Label(info_inner, text=f"Preço: R$ {produto['preco_venda']:.2f}  |  Custo: R$ {produto.get('preco_custo', 0):.2f}",
                 font=("Segoe UI", 9),
                 bg=ModernTheme.CARD_BG, fg=ModernTheme.TEXT_MUTED).pack(anchor=tk.W)

        # Card de movimentação
        mov_card = tk.Frame(dlg, bg=ModernTheme.CARD_BG,
                            highlightbackground=ModernTheme.BORDER,
                            highlightthickness=1)
        mov_card.pack(fill=tk.X, padx=16, pady=(0, 12))
        tk.Frame(mov_card, bg=ModernTheme.WARNING, height=3).pack(fill=tk.X)

        mov_inner = tk.Frame(mov_card, bg=ModernTheme.CARD_BG, padx=16, pady=14)
        mov_inner.pack(fill=tk.X)

        # Tipo de movimentação
        tk.Label(mov_inner, text="TIPO DE MOVIMENTAÇÃO",
                 font=("Segoe UI", 9, "bold"),
                 bg=ModernTheme.CARD_BG, fg=ModernTheme.TEXT_MUTED).pack(anchor=tk.W, pady=(0, 8))

        tipo_var = tk.StringVar(value="entrada")
        tipos = [
            ("entrada", "📥  Entrada (Adicionar)",  ModernTheme.SUCCESS, "#15803d"),
            ("saida",   "📤  Saída (Remover)",    ModernTheme.DANGER,  "#b91c1c"),
            ("ajuste",  "⚙️  Ajuste (Corrigir)",   ModernTheme.WARNING, "#b45309"),
        ]

        for val, label, color, hover in tipos:
            rb = tk.Radiobutton(mov_inner, text=label, variable=tipo_var, value=val,
                           bg=ModernTheme.CARD_BG, fg=color,
                           font=("Segoe UI", 10, "bold"),
                           selectcolor=ModernTheme.CARD_BG,
                           activebackground=ModernTheme.CARD_BG)
            rb.pack(anchor=tk.W, pady=2)

        # Quantidade
        tk.Label(mov_inner, text="QUANTIDADE",
                 font=("Segoe UI", 9, "bold"),
                 bg=ModernTheme.CARD_BG, fg=ModernTheme.TEXT_MUTED).pack(
            anchor=tk.W, pady=(12, 4))
        qtd_entry = self.styled_entry(mov_inner, width=38)
        qtd_entry.pack(fill=tk.X)

        # Motivo
        tk.Label(mov_inner, text="MOTIVO / OBSERVAÇÃO",
                 font=("Segoe UI", 9, "bold"),
                 bg=ModernTheme.CARD_BG, fg=ModernTheme.TEXT_MUTED).pack(
            anchor=tk.W, pady=(12, 4))
        mot_entry = self.styled_entry(mov_inner, width=38)
        mot_entry.pack(fill=tk.X)

        def executar():
            try:
                qtd = int(qtd_entry.get())
            except ValueError:
                self.show_message("Erro", "Quantidade deve ser um número inteiro", "error")
                return
            ok, msg = self.controllers["produto"].movimentar(
                pid, tipo_var.get(), qtd, mot_entry.get())
            if ok:
                self.show_message("Sucesso", msg)
                dlg.destroy()
                self.refresh()
            else:
                self.show_message("Erro", msg, "error")

        # Botão de ação
        btn_frame = tk.Frame(dlg, bg=ModernTheme.BG, padx=16, pady=12)
        btn_frame.pack(fill=tk.X)

        btn_confirm = tk.Button(btn_frame, text="✔  CONFIRMAR MOVIMENTAÇÃO",
                            command=executar,
                            bg=ModernTheme.PRIMARY, fg="white",
                            font=("Segoe UI", 11, "bold"),
                            bd=0, padx=24, pady=12, cursor="hand2",
                            activebackground="#1e40af")
        btn_confirm.pack(side=tk.RIGHT)
        btn_confirm.bind("<Enter>", lambda e: btn_confirm.config(bg="#1e40af"))
        btn_confirm.bind("<Leave>", lambda e: btn_confirm.config(bg=ModernTheme.PRIMARY))