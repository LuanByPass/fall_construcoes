"""Tela de Fornecedores e Contas a Pagar - FALL Construções (reestilizada premium)"""
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


class FornecedorView(BaseView):
    def __init__(self, parent, controllers):
        super().__init__(parent, None)
        self.controllers = controllers
        self.build()

    def build(self):
        self.frame = tk.Frame(self.parent, bg=ModernTheme.BG)


        self.notebook = ttk.Notebook(self.frame)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=16, pady=12)

        self.tab_forn   = tk.Frame(self.notebook, bg=ModernTheme.BG)
        self.tab_contas = tk.Frame(self.notebook, bg=ModernTheme.BG)
        self.tab_nova   = tk.Frame(self.notebook, bg=ModernTheme.BG)

        self.notebook.add(self.tab_forn,   text="🏭  Fornecedores")
        self.notebook.add(self.tab_contas, text="💰  Contas a Pagar")
        self.notebook.add(self.tab_nova,   text="➕  Nova Conta")

        self._build_fornecedores_tab()
        self._build_contas_tab()
        self._build_nova_conta_tab()

    # ── Aba Fornecedores ──────────────────────────────────────────────────────
    def _build_fornecedores_tab(self):
        # Toolbar
        toolbar = tk.Frame(self.tab_forn, bg=ModernTheme.BG)
        toolbar.pack(fill=tk.X, pady=(0, 8))

        search_box = tk.Frame(toolbar, bg=ModernTheme.CARD_BG,
                              highlightbackground=ModernTheme.BORDER,
                              highlightthickness=1)
        search_box.pack(side=tk.LEFT)
        tk.Label(search_box, text="🔍", font=("Segoe UI", 13),
                 bg=ModernTheme.CARD_BG,
                 fg=ModernTheme.INFO).pack(side=tk.LEFT, padx=(8, 2))
        self.forn_search = self.styled_entry(search_box,
                                             "Buscar fornecedor...", width=32)
        self.forn_search.pack(side=tk.LEFT, padx=(0, 6), pady=4)
        self.forn_search.bind("<Return>", lambda e: self._load_fornecedores())

        btn_buscar = tk.Button(search_box, text="Buscar", command=self._load_fornecedores,
                               bg=ModernTheme.INFO, fg="white",
                               font=("Segoe UI", 9, "bold"),
                               bd=0, padx=12, pady=4, cursor="hand2",
                               activebackground="#1e40af")
        btn_buscar.pack(side=tk.LEFT)
        btn_buscar.bind("<Enter>", lambda e: btn_buscar.config(bg="#1e40af"))
        btn_buscar.bind("<Leave>", lambda e: btn_buscar.config(bg=ModernTheme.INFO))

        tk.Button(toolbar, text="🏭  Novo Fornecedor", command=self._novo_fornecedor,
                  bg=ModernTheme.SUCCESS, fg="white",
                  font=("Segoe UI", 9, "bold"),
                  bd=0, padx=16, pady=6, cursor="hand2",
                  activebackground="#15803d").pack(side=tk.RIGHT)

        # Tabela
        card = tk.Frame(self.tab_forn, bg=ModernTheme.CARD_BG,
                        highlightbackground=ModernTheme.BORDER,
                        highlightthickness=1)
        card.pack(fill=tk.BOTH, expand=True, pady=(0, 4))

        table_header = tk.Frame(card, bg=ModernTheme.PRIMARY, height=36)
        table_header.pack(fill=tk.X)
        tk.Label(table_header, text="🏭  FORNECEDORES CADASTRADOS",
                 font=("Segoe UI", 10, "bold"),
                 bg=ModernTheme.PRIMARY, fg="white").pack(
            side=tk.LEFT, padx=14, pady=6)

        self.forn_contador = tk.Label(table_header, text="0 fornecedores",
                 font=("Segoe UI", 9),
                 bg=ModernTheme.PRIMARY, fg="white")
        self.forn_contador.pack(side=tk.RIGHT, padx=14, pady=6)

        table_body = tk.Frame(card, bg=ModernTheme.CARD_BG)
        table_body.pack(fill=tk.BOTH, expand=True, padx=12, pady=12)

        columns = ("Nome", "CNPJ", "Telefone", "Cidade", "Prazo", "Limite Crédito")
        self.forn_tree = ttk.Treeview(table_body, columns=columns,
                                      show="headings", height=20)
        for col, w in zip(columns, [220, 130, 120, 130, 70, 130]):
            self.forn_tree.heading(col, text=col)
            self.forn_tree.column(col, width=w)

        self.forn_tree.tag_configure("even", background="#f8fafc")
        self.forn_tree.tag_configure("odd",  background="white")

        sb = ttk.Scrollbar(table_body, orient=tk.VERTICAL,
                           command=self.forn_tree.yview)
        self.forn_tree.configure(yscrollcommand=sb.set)
        self.forn_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb.pack(side=tk.RIGHT, fill=tk.Y)

        self._load_fornecedores()

    # ── Aba Contas a Pagar ────────────────────────────────────────────────────
    def _build_contas_tab(self):
        # Estatísticas
        stats_frame = tk.Frame(self.tab_contas, bg=ModernTheme.BG)
        stats_frame.pack(fill=tk.X, pady=(0, 8))

        self.conta_stats = {}
        stats_config = [
            ("total",     "📋 Total",       ModernTheme.PRIMARY,  "#1e40af"),
            ("pendente",  "⏳ Pendentes",   ModernTheme.WARNING,  "#b45309"),
            ("atrasado",  "⚠️ Atrasadas",   ModernTheme.DANGER,   "#b91c1c"),
            ("pago",      "✅ Pagas",        ModernTheme.SUCCESS,  "#15803d"),
            ("valor",     "💰 Valor Total",  ModernTheme.INFO,     "#1e40af"),
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
            self.conta_stats[key] = tk.Label(inner, text="—",
                     font=("Segoe UI", 16, "bold"),
                     bg=ModernTheme.CARD_BG, fg=ModernTheme.TEXT)
            self.conta_stats[key].pack(anchor=tk.W)

        # Filtros
        filter_row = tk.Frame(self.tab_contas, bg=ModernTheme.CARD_BG,
                              highlightbackground=ModernTheme.BORDER,
                              highlightthickness=1)
        filter_row.pack(fill=tk.X, pady=8)
        tk.Frame(filter_row, bg=ModernTheme.PRIMARY, height=3).pack(fill=tk.X)

        inner = tk.Frame(filter_row, bg=ModernTheme.CARD_BG, padx=16, pady=10)
        inner.pack(fill=tk.X)

        tk.Label(inner, text="FILTRO:",
                 font=("Segoe UI", 9, "bold"),
                 bg=ModernTheme.CARD_BG, fg=ModernTheme.TEXT_MUTED).pack(
            side=tk.LEFT, padx=8)

        self.conta_status_var = tk.StringVar(value="todos")
        for val, label, color in [
            ("todos",    "Todas",      ModernTheme.TEXT),
            ("pendente", "⏳ Pendentes", ModernTheme.WARNING),
            ("atrasado", "⚠️ Atrasadas", ModernTheme.DANGER),
            ("pago",     "✅ Pagas",     ModernTheme.SUCCESS),
        ]:
            rb = tk.Radiobutton(inner, text=label,
                                variable=self.conta_status_var, value=val,
                                bg=ModernTheme.CARD_BG, fg=color,
                                font=("Segoe UI", 9, "bold"),
                                selectcolor=ModernTheme.CARD_BG,
                                activebackground=ModernTheme.CARD_BG,
                                command=self._load_contas)
            rb.pack(side=tk.LEFT, padx=6)

        btn_atualizar = tk.Button(inner, text="🔄  Atualizar", command=self._load_contas,
                                    bg=ModernTheme.INFO, fg="white",
                                    font=("Segoe UI", 9, "bold"),
                                    bd=0, padx=16, pady=6, cursor="hand2",
                                    activebackground="#1e40af")
        btn_atualizar.pack(side=tk.RIGHT)
        btn_atualizar.bind("<Enter>", lambda e: btn_atualizar.config(bg="#1e40af"))
        btn_atualizar.bind("<Leave>", lambda e: btn_atualizar.config(bg=ModernTheme.INFO))

        # Tabela
        card = tk.Frame(self.tab_contas, bg=ModernTheme.CARD_BG,
                        highlightbackground=ModernTheme.BORDER,
                        highlightthickness=1)
        card.pack(fill=tk.BOTH, expand=True, pady=(0, 4))

        table_header = tk.Frame(card, bg=ModernTheme.PRIMARY, height=36)
        table_header.pack(fill=tk.X)
        tk.Label(table_header, text="💰  CONTAS A PAGAR",
                 font=("Segoe UI", 10, "bold"),
                 bg=ModernTheme.PRIMARY, fg="white").pack(
            side=tk.LEFT, padx=14, pady=6)

        self.conta_contador = tk.Label(table_header, text="0 contas",
                 font=("Segoe UI", 9),
                 bg=ModernTheme.PRIMARY, fg="white")
        self.conta_contador.pack(side=tk.RIGHT, padx=14, pady=6)

        table_body = tk.Frame(card, bg=ModernTheme.CARD_BG)
        table_body.pack(fill=tk.BOTH, expand=True, padx=12, pady=12)

        columns = ("Fornecedor", "Descrição", "Documento",
                   "Valor", "Vencimento", "Status")
        self.contas_tree = ttk.Treeview(table_body, columns=columns,
                                        show="headings", height=16)
        for col, w in zip(columns, [160, 210, 110, 110, 110, 120]):
            self.contas_tree.heading(col, text=col)
            self.contas_tree.column(col, width=w)

        self.contas_tree.tag_configure("pago",     foreground=ModernTheme.SUCCESS)
        self.contas_tree.tag_configure("pendente", foreground=ModernTheme.WARNING)
        self.contas_tree.tag_configure("atrasado", foreground=ModernTheme.DANGER)
        self.contas_tree.tag_configure("even",     background="#f8fafc")
        self.contas_tree.tag_configure("odd",      background="white")

        sb = ttk.Scrollbar(table_body, orient=tk.VERTICAL,
                           command=self.contas_tree.yview)
        self.contas_tree.configure(yscrollcommand=sb.set)
        self.contas_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb.pack(side=tk.RIGHT, fill=tk.Y)

        # Ações
        action_bar = tk.Frame(self.tab_contas, bg=ModernTheme.CARD_BG,
                              highlightbackground=ModernTheme.BORDER,
                              highlightthickness=1)
        action_bar.pack(fill=tk.X, pady=8)
        tk.Frame(action_bar, bg=ModernTheme.SUCCESS, height=3).pack(fill=tk.X)

        action_inner = tk.Frame(action_bar, bg=ModernTheme.CARD_BG, padx=12, pady=10)
        action_inner.pack(fill=tk.X)

        tk.Label(action_inner, text="AÇÃO DA CONTA SELECIONADA",
                 font=("Segoe UI", 9, "bold"),
                 bg=ModernTheme.CARD_BG, fg=ModernTheme.TEXT_MUTED).pack(
            side=tk.LEFT, padx=12)

        tk.Button(action_inner, text="💰  Registrar Pagamento", command=self._pagar_conta,
                  bg=ModernTheme.SUCCESS, fg="white",
                  font=("Segoe UI", 9, "bold"),
                  bd=0, padx=16, pady=6, cursor="hand2",
                  activebackground="#15803d").pack(side=tk.LEFT, padx=4)

        self._load_contas()

    # ── Aba Nova Conta ────────────────────────────────────────────────────────
    def _build_nova_conta_tab(self):
        card = tk.Frame(self.tab_nova, bg=ModernTheme.CARD_BG,
                        highlightbackground=ModernTheme.BORDER,
                        highlightthickness=1)
        card.pack(fill=tk.BOTH, padx=0, pady=8)

        tk.Frame(card, bg=ModernTheme.PRIMARY, height=4).pack(fill=tk.X)

        body = tk.Frame(card, bg=ModernTheme.CARD_BG, padx=20, pady=16)
        body.pack(fill=tk.BOTH)

        tk.Label(body, text="➕  NOVA CONTA A PAGAR",
                 font=ModernTheme.FONT_LG,
                 bg=ModernTheme.CARD_BG, fg=ModernTheme.PRIMARY).pack(
            anchor=tk.W, pady=(0, 16))

        # Fornecedor
        tk.Label(body, text="FORNECEDOR",
                 font=("Segoe UI", 9, "bold"),
                 bg=ModernTheme.CARD_BG,
                 fg=ModernTheme.TEXT_MUTED).pack(anchor=tk.W, pady=(0, 4))
        self.conta_forn_var = tk.StringVar()
        fornecedores = self.controllers["fornecedor"].listar_fornecedores()
        combo = ttk.Combobox(body, textvariable=self.conta_forn_var,
                     values=[f"{f['id']} - {f['nome']}" for f in fornecedores],
                     state="readonly", font=ModernTheme.FONT_MD)
        combo.pack(fill=tk.X, pady=(0, 12))

        # Descrição
        tk.Label(body, text="DESCRIÇÃO",
                 font=("Segoe UI", 9, "bold"),
                 bg=ModernTheme.CARD_BG,
                 fg=ModernTheme.TEXT_MUTED).pack(anchor=tk.W, pady=(0, 4))
        self.desc_entry = self.styled_entry(body, width=60)
        self.desc_entry.pack(fill=tk.X, pady=(0, 12))

        # Linha: Documento / Valor / Vencimento
        row = tk.Frame(body, bg=ModernTheme.CARD_BG)
        row.pack(fill=tk.X, pady=(0, 12))

        for label, attr, w, default in [
            ("Nº DOCUMENTO",  "doc_entry",  12, ""),
            ("VALOR (R$)",    "valor_entry",12, ""),
            ("VENCIMENTO",    "venc_entry", 12,
             (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")),
        ]:
            col = tk.Frame(row, bg=ModernTheme.CARD_BG)
            col.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 16))
            tk.Label(col, text=label,
                     font=("Segoe UI", 9, "bold"),
                     bg=ModernTheme.CARD_BG,
                     fg=ModernTheme.TEXT_MUTED).pack(anchor=tk.W, pady=(0, 4))
            e = self.styled_entry(col, width=w)
            if default:
                e.insert(0, default)
            e.pack(fill=tk.X)
            setattr(self, attr, e)

        # Observações
        tk.Label(body, text="OBSERVAÇÕES",
                 font=("Segoe UI", 9, "bold"),
                 bg=ModernTheme.CARD_BG,
                 fg=ModernTheme.TEXT_MUTED).pack(anchor=tk.W, pady=(0, 4))
        self.obs_conta_entry = self.styled_entry(body, width=60)
        self.obs_conta_entry.pack(fill=tk.X, pady=(0, 16))

        btn_salvar = tk.Button(body, text="💾  SALVAR CONTA", command=self._salvar_conta,
                               bg=ModernTheme.SUCCESS, fg="white",
                               font=("Segoe UI", 12, "bold"),
                               bd=0, pady=12, cursor="hand2",
                               activebackground="#15803d")
        btn_salvar.pack(fill=tk.X)
        btn_salvar.bind("<Enter>", lambda e: btn_salvar.config(bg="#15803d"))
        btn_salvar.bind("<Leave>", lambda e: btn_salvar.config(bg=ModernTheme.SUCCESS))

    # ─────────────────────────────────────────────────────────────────────────
    def _load_fornecedores(self):
        for item in self.forn_tree.get_children():
            self.forn_tree.delete(item)
        busca = self.forn_search.get()
        if busca == "Buscar fornecedor...":
            busca = ""

        fornecedores = self.controllers["fornecedor"].listar_fornecedores(busca) or []
        for idx, f in enumerate(fornecedores):
            tag = "even" if idx % 2 == 0 else "odd"
            self.forn_tree.insert("", tk.END, tags=(tag,), values=(
                f["nome"], f.get("cnpj", ""), f.get("telefone", ""),
                f.get("cidade", ""),
                f"{f.get('prazo_pagamento', 30)} dias",
                f"R$ {float(f.get('limite_credito', 0) or 0):,.2f}",
            ))
        self.forn_contador.config(text=f"{len(fornecedores)} fornecedores")

    def _load_contas(self):
        for item in self.contas_tree.get_children():
            self.contas_tree.delete(item)

        status = self.conta_status_var.get()
        if status == "todos":
            status = None

        _icons = {"pendente": "⏳", "pago": "✔", "atrasado": "⚠️", "cancelado": "✖"}

        contagem = {"total": 0, "pendente": 0, "atrasado": 0, "pago": 0}
        total_valor = 0.0

        contas = self.controllers["fornecedor"].listar_contas(status) or []
        for idx, c in enumerate(contas):
            st = c.get("status", "pendente")
            contagem[st] = contagem.get(st, 0) + 1
            contagem["total"] += 1
            total_valor += float(c.get('valor', 0) or 0)

            venc = ""
            if c.get("data_vencimento"):
                if isinstance(c["data_vencimento"], datetime):
                    venc = c["data_vencimento"].strftime("%d/%m/%Y")
                else:
                    venc = str(c["data_vencimento"])[:10]

            tag = (st, "even" if idx % 2 == 0 else "odd")

            self.contas_tree.insert("", tk.END, tags=tag, values=(
                str(c.get("fornecedor_nome", ""))[:22],
                c["descricao"][:32],
                c.get("numero_documento", ""),
                f"R$ {float(c.get('valor', 0) or 0):.2f}",
                venc,
                f"{_icons.get(st, '•')} {st}",
            ))

        # Atualiza estatísticas
        for key in ["total", "pendente", "atrasado", "pago"]:
            self.conta_stats[key].config(text=str(contagem.get(key, 0)))
        self.conta_stats["valor"].config(text=f"R$ {total_valor:,.2f}")
        self.conta_contador.config(text=f"{contagem['total']} contas")

    def _salvar_conta(self):
        forn_str = self.conta_forn_var.get()
        if not forn_str:
            messagebox.showwarning("Aviso", "Selecione um fornecedor")
            return
        dados = {
            "fornecedor_id":   int(forn_str.split(" - ")[0]),
            "descricao":       self.desc_entry.get(),
            "numero_documento":self.doc_entry.get(),
            "valor":           self.valor_entry.get(),
            "data_vencimento": self.venc_entry.get(),
            "observacoes":     self.obs_conta_entry.get(),
        }
        ok, msg = self.controllers["fornecedor"].criar_conta(dados)
        if ok:
            messagebox.showinfo("Sucesso", msg)
            self._load_contas()
            self.notebook.select(self.tab_contas)
            # Limpa campos
            self.desc_entry.delete(0, tk.END)
            self.doc_entry.delete(0, tk.END)
            self.valor_entry.delete(0, tk.END)
            self.obs_conta_entry.delete(0, tk.END)
        else:
            messagebox.showerror("Erro", msg)

    def _pagar_conta(self):
        sel = self.contas_tree.selection()
        if not sel:
            messagebox.showwarning("Aviso", "Selecione uma conta")
            return

        dlg = self.make_dialog("💰  Registrar Pagamento", 360, 290)
        tk.Frame(dlg, bg=ModernTheme.SUCCESS, height=4).pack(fill=tk.X)
        tk.Label(dlg, text="Registrar Pagamento",
                 font=ModernTheme.FONT_XL,
                 bg=ModernTheme.BG, fg=ModernTheme.TEXT).pack(
            anchor=tk.W, padx=20, pady=14)

        valor_entry = self.form_field(dlg, "Valor Pago (R$)")
        data_entry  = self.form_field(dlg, "Data do Pagamento",
                                      value=datetime.now().strftime("%Y-%m-%d"))
        forma_var   = tk.StringVar(value="dinheiro")
        tk.Label(dlg, text="Forma",
                 font=("Segoe UI", 9, "bold"),
                 bg=ModernTheme.BG, fg=ModernTheme.TEXT_MUTED).pack(
            anchor=tk.W, padx=20, pady=(8, 2))
        ttk.Combobox(dlg, textvariable=forma_var,
                     values=["dinheiro", "pix", "transferencia",
                             "boleto", "cheque"],
                     state="readonly", font=ModernTheme.FONT_MD).pack(
            fill=tk.X, padx=20)

        tk.Frame(dlg, bg=ModernTheme.BORDER, height=1).pack(
            fill=tk.X, padx=20, pady=12)

        def confirmar():
            messagebox.showinfo("Sucesso", "Conta marcada como paga!")
            dlg.destroy()
            self._load_contas()

        btn = tk.Button(dlg, text="✔  CONFIRMAR PAGAMENTO", command=confirmar,
                        bg=ModernTheme.SUCCESS, fg="white",
                        font=("Segoe UI", 11, "bold"),
                        bd=0, pady=10, cursor="hand2",
                        activebackground="#15803d")
        btn.pack(fill=tk.X, padx=20)
        btn.bind("<Enter>", lambda e: btn.config(bg="#15803d"))
        btn.bind("<Leave>", lambda e: btn.config(bg=ModernTheme.SUCCESS))

    def _novo_fornecedor(self):
        dlg = self.make_dialog("🏭  Cadastro de Fornecedor", 520, 620)
        tk.Frame(dlg, bg=ModernTheme.PRIMARY, height=4).pack(fill=tk.X)
        tk.Label(dlg, text="🏭  Novo Fornecedor",
                 font=ModernTheme.FONT_XL,
                 bg=ModernTheme.BG, fg=ModernTheme.TEXT).pack(
            anchor=tk.W, padx=20, pady=14)

        canvas = tk.Canvas(dlg, bg=ModernTheme.BG, bd=0, highlightthickness=0)
        sb_v   = ttk.Scrollbar(dlg, orient=tk.VERTICAL, command=canvas.yview)
        inner  = tk.Frame(canvas, bg=ModernTheme.BG)
        inner.bind("<Configure>",
                   lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=inner, anchor="nw", width=500)
        canvas.configure(yscrollcommand=sb_v.set)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb_v.pack(side=tk.RIGHT, fill=tk.Y)

        fields = {}
        for label, key in [
            ("Nome *", "nome"), ("CNPJ", "cnpj"), ("Telefone", "telefone"),
            ("Email", "email"), ("Endereço", "endereco"), ("Cidade", "cidade"),
            ("Estado", "estado"), ("CEP", "cep"),
            ("Contato Nome", "contato_nome"),
            ("Contato Tel", "contato_telefone"),
            ("Prazo (dias)", "prazo_pagamento"),
            ("Limite Crédito", "limite_credito"),
        ]:
            tk.Label(inner, text=label.upper(),
                     font=("Segoe UI", 9, "bold"),
                     bg=ModernTheme.BG, fg=ModernTheme.TEXT_MUTED,
                     anchor=tk.W).pack(fill=tk.X, padx=20, pady=(10, 2))
            e = self.styled_entry(inner, width=50)
            e.pack(fill=tk.X, padx=20)
            fields[key] = e

        tk.Frame(inner, bg=ModernTheme.BORDER, height=1).pack(
            fill=tk.X, padx=20, pady=14)

        def save():
            dados = {k: v.get() for k, v in fields.items()}
            ok, msg = self.controllers["fornecedor"].criar_fornecedor(dados)
            if ok:
                messagebox.showinfo("Sucesso", msg)
                dlg.destroy()
                self._load_fornecedores()
            else:
                messagebox.showerror("Erro", msg)

        btn = tk.Button(inner, text="💾  SALVAR FORNECEDOR", command=save,
                        bg=ModernTheme.SUCCESS, fg="white",
                        font=("Segoe UI", 12, "bold"),
                        bd=0, pady=10, cursor="hand2",
                        activebackground="#15803d")
        btn.pack(fill=tk.X, padx=20, pady=8)
        btn.bind("<Enter>", lambda e: btn.config(bg="#15803d"))
        btn.bind("<Leave>", lambda e: btn.config(bg=ModernTheme.SUCCESS))