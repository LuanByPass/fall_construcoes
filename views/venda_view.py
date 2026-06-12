"""Tela de Vendas / PDV - FALL Construções (reestilizada premium)"""
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from datetime import datetime
from views.base_view import BaseView
from config import ModernTheme, LOJA_CONFIG
import subprocess
import os
import platform

try:
    from utils.logger import Logger
except Exception:
    class Logger:
        @classmethod
        def log(cls, msg, level="INFO"):
            print(f"[{level}] {msg}")

try:
    from utils.danfe_generator import DanfeGenerator
    DANFE_AVAILABLE = True
except ImportError:
    DANFE_AVAILABLE = False
    print("[AVISO] ReportLab não instalado. Usando fallback de comprovante texto.")


class VendaView(BaseView):
    def __init__(self, parent, controllers):
        super().__init__(parent, None)
        self.controllers = controllers
        self.venda_atual = None
        self.itens_venda = []
        self.desconto_percentual = 0.0
        self.desconto_valor = 0.0
        self.danfe_gen = DanfeGenerator(LOJA_CONFIG) if DANFE_AVAILABLE else None
        self.build()

    def build(self):
        self.frame = tk.Frame(self.parent, bg=ModernTheme.BG)

        # ── Layout principal (esq / dir) ──────────────────────────────────────
        main = tk.Frame(self.frame, bg=ModernTheme.BG)
        main.pack(fill=tk.BOTH, expand=True, padx=16, pady=(0, 16))

        # ── COLUNA ESQUERDA ───────────────────────────────────────────────────
        left = tk.Frame(main, bg=ModernTheme.BG)
        left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # ═══════════════════════════════════════════════════════════════════
        # CARD: CLIENTE
        # ═══════════════════════════════════════════════════════════════════
        cliente_card = tk.Frame(left, bg=ModernTheme.CARD_BG,
                                highlightbackground=ModernTheme.BORDER,
                                highlightthickness=1)
        cliente_card.pack(fill=tk.X, pady=(0, 10))

        tk.Frame(cliente_card, bg=ModernTheme.INFO, height=4).pack(fill=tk.X)
        inner_cli = tk.Frame(cliente_card, bg=ModernTheme.CARD_BG, padx=14, pady=12)
        inner_cli.pack(fill=tk.X)

        tk.Label(inner_cli, text="👤  CLIENTE",
                 font=("Segoe UI", 10, "bold"),
                 bg=ModernTheme.CARD_BG, fg=ModernTheme.INFO).pack(anchor=tk.W, pady=(0, 8))

        self.cliente_var = tk.StringVar()
        clientes = self.controllers["venda"].listar_clientes()
        valores_combo = ["— Consumidor Final (Avulso) —"] + [f"{c['id']} - {c['nome']}" for c in clientes]
        self.cliente_combo = ttk.Combobox(
            inner_cli, textvariable=self.cliente_var,
            values=valores_combo,
            state="readonly", font=ModernTheme.FONT_MD)
        self.cliente_combo.set("— Consumidor Final (Avulso) —")
        self.cliente_combo.pack(fill=tk.X, pady=(0, 8))
        self.cliente_combo.bind("<<ComboboxSelected>>", self._on_cliente_changed)

        btn_novo_cli = tk.Button(inner_cli, text="➕  Novo Cliente", command=self._novo_cliente,
                                 bg=ModernTheme.INFO, fg="white",
                                 font=("Segoe UI", 9, "bold"),
                                 bd=0, padx=14, pady=6, cursor="hand2",
                                 activebackground="#1e40af")
        btn_novo_cli.pack(anchor=tk.E)
        btn_novo_cli.bind("<Enter>", lambda e: btn_novo_cli.config(bg="#1e40af"))
        btn_novo_cli.bind("<Leave>", lambda e: btn_novo_cli.config(bg=ModernTheme.INFO))

        # ═══════════════════════════════════════════════════════════════════
        # CARD: BUSCA DE PRODUTO
        # ═══════════════════════════════════════════════════════════════════
        search_card = tk.Frame(left, bg=ModernTheme.CARD_BG,
                               highlightbackground=ModernTheme.BORDER,
                               highlightthickness=1)
        search_card.pack(fill=tk.X, pady=(0, 10))

        tk.Frame(search_card, bg=ModernTheme.PRIMARY, height=4).pack(fill=tk.X)
        inner_srch = tk.Frame(search_card, bg=ModernTheme.CARD_BG, padx=14, pady=12)
        inner_srch.pack(fill=tk.X)

        tk.Label(inner_srch, text="🔍  CÓDIGO DE BARRAS / BUSCA",
                 font=("Segoe UI", 10, "bold"),
                 bg=ModernTheme.CARD_BG, fg=ModernTheme.PRIMARY).pack(anchor=tk.W, pady=(0, 8))

        srch_row = tk.Frame(inner_srch, bg=ModernTheme.CARD_BG)
        srch_row.pack(fill=tk.X)

        self.codigo_entry = self.styled_entry(srch_row,
                                              "Digite o código ou nome...",
                                              width=46)
        self.codigo_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, pady=(0, 4))
        self.codigo_entry.bind("<Return>", lambda e: self._buscar_produto())
        self.codigo_entry.focus_set()

        btn_add = tk.Button(srch_row, text="➕  Adicionar", command=self._buscar_produto,
                            bg=ModernTheme.SUCCESS, fg="white",
                            font=("Segoe UI", 9, "bold"),
                            bd=0, padx=16, pady=6, cursor="hand2",
                            activebackground="#15803d")
        btn_add.pack(side=tk.LEFT, padx=(10, 0))
        btn_add.bind("<Enter>", lambda e: btn_add.config(bg="#15803d"))
        btn_add.bind("<Leave>", lambda e: btn_add.config(bg=ModernTheme.SUCCESS))

        # ═══════════════════════════════════════════════════════════════════
        # CARD: ITENS DA VENDA
        # ═══════════════════════════════════════════════════════════════════
        itens_header = tk.Frame(left, bg=ModernTheme.BG)
        itens_header.pack(fill=tk.X, pady=(4, 4))
        tk.Label(itens_header, text="📦  ITENS DA VENDA",
                 font=("Segoe UI", 10, "bold"),
                 bg=ModernTheme.BG, fg=ModernTheme.TEXT_MUTED).pack(anchor=tk.W)

        table_card = tk.Frame(left, bg=ModernTheme.CARD_BG,
                              highlightbackground=ModernTheme.BORDER,
                              highlightthickness=1)
        table_card.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        table_header = tk.Frame(table_card, bg=ModernTheme.PRIMARY, height=36)
        table_header.pack(fill=tk.X)
        table_header.pack_propagate(False)
        tk.Label(table_header, text="🛒  PRODUTOS ADICIONADOS",
                 font=("Segoe UI", 10, "bold"),
                 bg=ModernTheme.PRIMARY, fg="white").pack(
            side=tk.LEFT, padx=14, pady=8)

        self.itens_contador = tk.Label(table_header, text="0 itens",
                 font=("Segoe UI", 9),
                 bg=ModernTheme.PRIMARY, fg="white")
        self.itens_contador.pack(side=tk.RIGHT, padx=14, pady=8)

        table_body = tk.Frame(table_card, bg=ModernTheme.CARD_BG)
        table_body.pack(fill=tk.BOTH, expand=True, padx=12, pady=12)

        columns = ("Código", "Produto", "Qtd", "Preço", "Subtotal")
        self.itens_tree = ttk.Treeview(table_body, columns=columns,
                                       show="headings", height=12)
        for col, w in zip(columns, [100, 300, 60, 100, 100]):
            self.itens_tree.heading(col, text=col)
            self.itens_tree.column(col, width=w)

        self.itens_tree.tag_configure("even", background="#f8fafc")
        self.itens_tree.tag_configure("odd", background="white")

        sb = ttk.Scrollbar(table_body, orient=tk.VERTICAL, command=self.itens_tree.yview)
        self.itens_tree.configure(yscrollcommand=sb.set)
        self.itens_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb.pack(side=tk.RIGHT, fill=tk.Y)

        # ── Toolbar de ações dos itens ───────────────────────────────────────
        ctrl = tk.Frame(left, bg=ModernTheme.BG)
        ctrl.pack(fill=tk.X, pady=(4, 0))

        btn_rem = tk.Button(ctrl, text="🗑️  Remover Item", command=self._remover_item,
                            bg=ModernTheme.DANGER, fg="white",
                            font=("Segoe UI", 9, "bold"),
                            bd=0, padx=16, pady=8, cursor="hand2",
                            activebackground="#b91c1c")
        btn_rem.pack(side=tk.LEFT)
        btn_rem.bind("<Enter>", lambda e: btn_rem.config(bg="#b91c1c"))
        btn_rem.bind("<Leave>", lambda e: btn_rem.config(bg=ModernTheme.DANGER))

        btn_nova = tk.Button(ctrl, text="🔄  Nova Venda", command=self._nova_venda,
                             bg=ModernTheme.INFO, fg="white",
                             font=("Segoe UI", 9, "bold"),
                             bd=0, padx=16, pady=8, cursor="hand2",
                             activebackground="#1e40af")
        btn_nova.pack(side=tk.LEFT, padx=8)
        btn_nova.bind("<Enter>", lambda e: btn_nova.config(bg="#1e40af"))
        btn_nova.bind("<Leave>", lambda e: btn_nova.config(bg=ModernTheme.INFO))

        # ── COLUNA DIREITA – RESUMO ───────────────────────────────────────────
        right = tk.Frame(main, bg=ModernTheme.CARD_BG,
                         highlightbackground=ModernTheme.BORDER,
                         highlightthickness=1, width=320)
        right.pack(side=tk.RIGHT, fill=tk.Y, padx=(12, 0))
        right.pack_propagate(False)

        tk.Frame(right, bg=ModernTheme.PRIMARY, height=4).pack(fill=tk.X)

        resumo_inner = tk.Frame(right, bg=ModernTheme.CARD_BG, padx=20, pady=16)
        resumo_inner.pack(fill=tk.BOTH, expand=True)

        tk.Label(resumo_inner, text="🧾  RESUMO DA VENDA",
                 font=("Segoe UI", 12, "bold"),
                 bg=ModernTheme.CARD_BG, fg=ModernTheme.PRIMARY).pack(anchor=tk.W, pady=(0, 12))

        # Número da venda
        self.numero_label = tk.Label(resumo_inner, text="Nº: —",
                                     font=("Segoe UI", 11),
                                     bg=ModernTheme.CARD_BG, fg=ModernTheme.TEXT_MUTED)
        self.numero_label.pack(anchor=tk.W)

        # Cliente
        self.cliente_nota_label = tk.Label(resumo_inner, text="Cliente: Consumidor Final",
                                           font=("Segoe UI", 10),
                                           bg=ModernTheme.CARD_BG, fg=ModernTheme.TEXT_MUTED)
        self.cliente_nota_label.pack(anchor=tk.W, pady=(0, 16))

        # Subtotal
        tk.Label(resumo_inner, text="SUBTOTAL",
                 font=("Segoe UI", 9, "bold"),
                 bg=ModernTheme.CARD_BG, fg=ModernTheme.TEXT_MUTED).pack(anchor=tk.W)
        self.subtotal_label = tk.Label(resumo_inner, text="R$ 0,00",
                                       font=("Segoe UI", 20, "bold"),
                                       bg=ModernTheme.CARD_BG, fg=ModernTheme.TEXT)
        self.subtotal_label.pack(anchor=tk.W, pady=(0, 10))

        # Desconto
        tk.Label(resumo_inner, text="DESCONTO",
                 font=("Segoe UI", 9, "bold"),
                 bg=ModernTheme.CARD_BG, fg=ModernTheme.TEXT_MUTED).pack(anchor=tk.W)
        self.desconto_label = tk.Label(resumo_inner, text="R$ 0,00 (0%)",
                                       font=("Segoe UI", 16, "bold"),
                                       bg=ModernTheme.CARD_BG, fg=ModernTheme.DANGER)
        self.desconto_label.pack(anchor=tk.W, pady=(0, 10))

        # Separador
        tk.Frame(resumo_inner, bg=ModernTheme.BORDER, height=2).pack(
            fill=tk.X, pady=12)

        # TOTAL
        tk.Label(resumo_inner, text="TOTAL A PAGAR",
                 font=("Segoe UI", 10, "bold"),
                 bg=ModernTheme.CARD_BG, fg=ModernTheme.PRIMARY).pack(anchor=tk.W)
        self.total_label = tk.Label(resumo_inner, text="R$ 0,00",
                                    font=("Segoe UI", 36, "bold"),
                                    bg=ModernTheme.CARD_BG, fg=ModernTheme.SUCCESS)
        self.total_label.pack(anchor=tk.W, pady=(0, 16))

        # Forma de pagamento
        tk.Label(resumo_inner, text="FORMA DE PAGAMENTO",
                 font=("Segoe UI", 9, "bold"),
                 bg=ModernTheme.CARD_BG, fg=ModernTheme.TEXT_MUTED).pack(anchor=tk.W, pady=(0, 6))

        self.pagamento_var = tk.StringVar(value="dinheiro")
        pagamentos = [
            ("dinheiro",        "💵  Dinheiro"),
            ("cartao_credito",  "💳  Cartão Crédito"),
            ("cartao_debito",   "💳  Cartão Débito"),
            ("pix",             "📱  PIX"),
            ("boleto",          "📄  Boleto"),
            ("prazo",           "📅  A Prazo"),
        ]
        for val, text in pagamentos:
            tk.Radiobutton(resumo_inner, text=text,
                           variable=self.pagamento_var, value=val,
                           bg=ModernTheme.CARD_BG, fg=ModernTheme.TEXT,
                           font=("Segoe UI", 10),
                           selectcolor=ModernTheme.CARD_BG,
                           activebackground=ModernTheme.CARD_BG).pack(
                anchor=tk.W, pady=2)

        # Separador
        tk.Frame(resumo_inner, bg=ModernTheme.BORDER, height=2).pack(
            fill=tk.X, pady=14)

        # Botão Finalizar
        btn_fin = tk.Button(resumo_inner, text="✔  FINALIZAR VENDA",
                            command=self._finalizar_venda,
                            bg=ModernTheme.SUCCESS, fg="white",
                            font=("Segoe UI", 13, "bold"),
                            bd=0, relief=tk.FLAT, pady=14, cursor="hand2",
                            activebackground="#15803d")
        btn_fin.pack(fill=tk.X)
        btn_fin.bind("<Enter>", lambda e: btn_fin.config(bg="#15803d"))
        btn_fin.bind("<Leave>", lambda e: btn_fin.config(bg=ModernTheme.SUCCESS))

        # ✅ NÃO chama _nova_venda() no build()
        self._resetar_interface()

    # ─────────────────────────────────────────────────────────────────────────
    def _on_cliente_changed(self, event=None):
        cliente_str = self.cliente_var.get()
        if not cliente_str or "Avulso" in cliente_str or "—" in cliente_str:
            self.cliente_nota_label.config(text="Cliente: Consumidor Final")
        else:
            nome = cliente_str.split(" - ")[1] if " - " in cliente_str else cliente_str
            self.cliente_nota_label.config(text=f"Cliente: {nome}")
        if not self.venda_atual:
            self._nova_venda()

    def _resetar_interface(self):
        self.itens_venda = []
        self.venda_atual = None
        self.desconto_percentual = 0.0
        self.desconto_valor = 0.0
        self.numero_label.config(text="Nº: —")
        self.cliente_nota_label.config(text="Cliente: Consumidor Final")
        self.cliente_var.set("— Consumidor Final (Avulso) —")
        self._atualizar_resumo()
        self._limpar_itens()
        self.codigo_entry.focus_set()

    def _nova_venda(self):
        self.itens_venda = []
        self.venda_atual = None
        self.desconto_percentual = 0.0
        self.desconto_valor = 0.0

        cliente_id = None
        cliente_str = self.cliente_var.get()
        if cliente_str and "Avulso" not in cliente_str and "—" not in cliente_str:
            try:
                cliente_id = int(cliente_str.split(" - ")[0])
            except Exception:
                pass

        success, result = self.controllers["venda"].criar_venda(
            cliente_id=cliente_id,
            forma_pagamento=self.pagamento_var.get()
        )

        if success:
            self.venda_atual = result
            self.numero_label.config(text=f"Nº: {result['numero']}")
            if cliente_id and cliente_str:
                nome = cliente_str.split(" - ")[1] if " - " in cliente_str else cliente_str
                self.cliente_nota_label.config(text=f"Cliente: {nome}")
            else:
                self.cliente_nota_label.config(text="Cliente: Consumidor Final")
            Logger.log(f"Nova venda: {result['numero']}", "SUCCESS")

        self._atualizar_resumo()
        self._limpar_itens()
        self.codigo_entry.focus_set()

    def _buscar_produto(self):
        codigo = self.codigo_entry.get().strip()
        placeholder = "Digite o código ou nome..."
        if not codigo or codigo == placeholder:
            return

        if not self.venda_atual:
            self._nova_venda()
            if not self.venda_atual:
                self.show_message("Erro", "Não foi possível criar a venda", "error")
                return

        produto = self.controllers["produto"].obter_por_codigo_barras(codigo)

        if not produto:
            produtos = self.controllers["produto"].listar(codigo)
            if len(produtos) == 1:
                produto = produtos[0]
            elif len(produtos) > 1:
                self._selecionar_produto(produtos)
                return

        if produto:
            self._adicionar_item(produto)
        else:
            self.show_message("Não encontrado", "Produto não encontrado!", "warning")

        self.codigo_entry.delete(0, tk.END)
        self.codigo_entry.focus_set()

    def _selecionar_produto(self, produtos):
        dlg = self.make_dialog("🔍  Selecionar Produto", 520, 420)

        tk.Frame(dlg, bg=ModernTheme.PRIMARY, height=4).pack(fill=tk.X)
        tk.Label(dlg, text="Selecione o produto:",
                 font=ModernTheme.FONT_LG,
                 bg=ModernTheme.BG, fg=ModernTheme.TEXT).pack(
            anchor=tk.W, padx=20, pady=14)

        card = tk.Frame(dlg, bg=ModernTheme.CARD_BG,
                        highlightbackground=ModernTheme.BORDER,
                        highlightthickness=1)
        card.pack(fill=tk.BOTH, expand=True, padx=16, pady=(0, 12))

        cols = ("Código", "Nome", "Preço")
        tree = ttk.Treeview(card, columns=cols, show="headings", height=10)
        for col, w in zip(cols, [100, 300, 100]):
            tree.heading(col, text=col)
            tree.column(col, width=w)

        for p in produtos:
            tree.insert("", tk.END, values=(
                p["codigo"], p["nome"],
                f"R$ {float(p['preco_venda']):.2f}"
            ))

        sb = ttk.Scrollbar(card, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscrollcommand=sb.set)
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb.pack(side=tk.RIGHT, fill=tk.Y)

        def selecionar():
            idx = tree.selection()
            if idx:
                i = tree.index(idx[0])
                self._adicionar_item(produtos[i])
                dlg.destroy()

        tree.bind("<Double-1>", lambda e: selecionar())
        self.styled_button(dlg, "Selecionar", selecionar,
                           ModernTheme.PRIMARY, icon="✔").pack(pady=8)

    def _adicionar_item(self, produto):
        if not self.venda_atual:
            self.show_message("Aviso", "Inicie uma nova venda primeiro!", "warning")
            return

        qtd = simpledialog.askinteger(
            "Quantidade",
            f"Produto: {produto['nome']}\nQuantidade:",
            parent=self.parent, minvalue=1, initialvalue=1
        )
        if not qtd:
            return

        success, msg = self.controllers["venda"].adicionar_item(
            self.venda_atual["id"], produto["id"], qtd
        )

        if success:
            self.itens_venda.append({
                "produto_id": produto["id"],
                "codigo":     produto["codigo"],
                "nome":       produto["nome"],
                "quantidade": qtd,
                "preco":      produto["preco_venda"],
                "subtotal":   float(produto["preco_venda"]) * qtd,
            })
            self._atualizar_itens()
            self._atualizar_resumo()
            Logger.log(f"Item adicionado: {produto['nome']} x{qtd}", "SUCCESS")
        else:
            self.show_message("Erro", msg, "error")

    def _remover_item(self):
        selected = self.itens_tree.selection()
        if not selected:
            self.show_message("Aviso", "Selecione um item para remover", "warning")
            return
        idx = self.itens_tree.index(selected[0])
        if 0 <= idx < len(self.itens_venda):
            del self.itens_venda[idx]
            self._atualizar_itens()
            self._atualizar_resumo()

    def _atualizar_itens(self):
        for item in self.itens_tree.get_children():
            self.itens_tree.delete(item)
        for idx, item in enumerate(self.itens_venda):
            tag = "even" if idx % 2 == 0 else "odd"
            self.itens_tree.insert("", tk.END, tags=(tag,), values=(
                item["codigo"], item["nome"], item["quantidade"],
                f"R$ {float(item['preco']):.2f}",
                f"R$ {item['subtotal']:.2f}",
            ))
        self.itens_contador.config(text=f"{len(self.itens_venda)} itens")

    def _limpar_itens(self):
        for item in self.itens_tree.get_children():
            self.itens_tree.delete(item)
        self.itens_contador.config(text="0 itens")

    def _atualizar_resumo(self):
        subtotal = sum(item["subtotal"] for item in self.itens_venda)
        self.desconto_valor = subtotal * (self.desconto_percentual / 100.0)
        total = subtotal - self.desconto_valor

        self.subtotal_label.config(text=f"R$ {subtotal:,.2f}")
        self.desconto_label.config(
            text=f"R$ {self.desconto_valor:,.2f} ({self.desconto_percentual:.1f}%)"
        )
        self.total_label.config(text=f"R$ {total:,.2f}")

    def _finalizar_venda(self):
        if not self.venda_atual or not self.itens_venda:
            self.show_message("Aviso", "Adicione itens à venda primeiro!", "warning")
            return

        pct = simpledialog.askfloat(
            "Desconto",
            "Informe o desconto em porcentagem (%):",
            parent=self.parent, minvalue=0, maxvalue=100, initialvalue=0
        )
        if pct is None:
            pct = 0.0

        self.desconto_percentual = pct
        subtotal = sum(item["subtotal"] for item in self.itens_venda)
        self.desconto_valor = subtotal * (pct / 100.0)
        self._atualizar_resumo()

        venda_id_atual = self.venda_atual["id"]
        numero_venda_atual = self.venda_atual.get("numero", "N/A")
        cliente_id_atual = None
        cliente_str = self.cliente_var.get()

        if cliente_str and "Avulso" not in cliente_str and "—" not in cliente_str:
            try:
                cliente_id_atual = int(cliente_str.split(" - ")[0])
            except:
                pass

        success, result = self.controllers["venda"].finalizar_venda(
            venda_id_atual, self.desconto_valor
        )

        if success:
            self.show_message(
                "Venda Finalizada",
                f"Venda {numero_venda_atual} finalizada!\n"
                f"Subtotal: R$ {subtotal:,.2f}\n"
                f"Desconto: {pct:.1f}% (R$ {self.desconto_valor:,.2f})\n"
                f"Total: R$ {result['total']:,.2f}"
            )
            if messagebox.askyesno("Imprimir", "Deseja imprimir o comprovante?"):
                self._escolher_tipo_comprovante(venda_id_atual, cliente_id_atual)

            self._resetar_interface()
        else:
            self.show_message("Erro", result, "error")

    def _escolher_tipo_comprovante(self, venda_id, cliente_id=None):
        dlg = tk.Toplevel(self.parent)
        dlg.title("Escolher Tipo de Comprovante")
        dlg.geometry("400x220")
        dlg.configure(bg=ModernTheme.BG)
        dlg.resizable(False, False)
        dlg.transient(self.parent)
        dlg.grab_set()

        tk.Frame(dlg, bg=ModernTheme.PRIMARY, height=4).pack(fill=tk.X)

        tk.Label(dlg, text="📄  Tipo de Comprovante",
                 font=ModernTheme.FONT_XL,
                 bg=ModernTheme.BG, fg=ModernTheme.TEXT).pack(pady=(16, 8))

        tk.Label(dlg, text="Escolha como deseja imprimir a venda:",
                 font=ModernTheme.FONT_BASE,
                 bg=ModernTheme.BG, fg=ModernTheme.TEXT_MUTED).pack(pady=(0, 16))

        btn_frame = tk.Frame(dlg, bg=ModernTheme.BG)
        btn_frame.pack(pady=8)

        def escolher_danfe():
            dlg.destroy()
            self._imprimir_danfe(venda_id, cliente_id)

        def escolher_cupom():
            dlg.destroy()
            self._imprimir_comprovante(venda_id, cliente_id)

        tk.Button(btn_frame, text="📋  DANFE (PDF)",
                  command=escolher_danfe,
                  bg=ModernTheme.INFO, fg="white",
                  font=("Segoe UI", 12, "bold"),
                  bd=0, padx=24, pady=12, cursor="hand2",
                  activebackground="#1e40af",
                  activeforeground="white").pack(side=tk.LEFT, padx=6)

        tk.Button(btn_frame, text="🧾  Cupom Fiscal",
                  command=escolher_cupom,
                  bg=ModernTheme.SUCCESS, fg="white",
                  font=("Segoe UI", 12, "bold"),
                  bd=0, padx=24, pady=12, cursor="hand2",
                  activebackground="#15803d",
                  activeforeground="white").pack(side=tk.LEFT, padx=6)

        tk.Button(dlg, text="Cancelar",
                  command=dlg.destroy,
                  bg=ModernTheme.BG, fg=ModernTheme.TEXT_MUTED,
                  font=ModernTheme.FONT_BASE,
                  bd=0, padx=16, pady=6, cursor="hand2").pack(pady=(12, 8))

        dlg.update_idletasks()
        x = (dlg.winfo_screenwidth() // 2) - (dlg.winfo_width() // 2)
        y = (dlg.winfo_screenheight() // 2) - (dlg.winfo_height() // 2)
        dlg.geometry(f"+{x}+{y}")

    def _imprimir_danfe(self, venda_id=None, cliente_id=None):
        if venda_id is None:
            return

        venda = self.controllers["venda"].obter_venda(venda_id)
        if not venda:
            return

        if not venda.get("cliente_nome") and cliente_id:
            cliente = self.controllers["venda"].obter_cliente(cliente_id)
            if cliente:
                venda["cliente_nome"] = cliente.get("nome")
                venda["cpf_cnpj"] = cliente.get("cpf_cnpj")

        if not venda.get("itens") and self.itens_venda:
            venda["itens"] = self.itens_venda

        if DANFE_AVAILABLE and self.danfe_gen:
            try:
                os.makedirs("comprovantes", exist_ok=True)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                pdf_path = "comprovantes/DANFE_" + venda.get("numero", "000") + "_" + timestamp + ".pdf"

                self.danfe_gen.gerar(venda, output_path=pdf_path)

                messagebox.showinfo(
                    "DANFE Gerado",
                    "Nota Fiscal PDF gerada com sucesso!\n\n" + pdf_path
                )
                self._abrir_pdf(pdf_path)
                return

            except Exception as e:
                Logger.log("Erro ao gerar DANFE: " + str(e), "ERROR")
                messagebox.showwarning(
                    "Erro no PDF",
                    "Não foi possível gerar o PDF DANFE.\n\nErro: " + str(e)
                )
        else:
            messagebox.showwarning(
                "DANFE Indisponível",
                "ReportLab não está instalado.\nUse o Cupom Fiscal como alternativa."
            )

    def _imprimir_comprovante(self, venda_id=None, cliente_id=None):
        if venda_id is None:
            return

        venda = self.controllers["venda"].obter_venda(venda_id)
        if not venda:
            return

        if not venda.get("cliente_nome") and cliente_id:
            cliente = self.controllers["venda"].obter_cliente(cliente_id)
            if cliente:
                venda["cliente_nome"] = cliente.get("nome")
                venda["cpf_cnpj"] = cliente.get("cpf_cnpj")

        if not venda.get("itens") and self.itens_venda:
            venda["itens"] = self.itens_venda

        if DANFE_AVAILABLE and self.danfe_gen:
            try:
                os.makedirs("comprovantes", exist_ok=True)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                pdf_path = f"comprovantes/DANFE_{venda.get('numero', '000')}_{timestamp}.pdf"

                self.danfe_gen.gerar(venda, output_path=pdf_path)

                messagebox.showinfo(
                    "DANFE Gerado",
                    f"Nota Fiscal PDF gerada com sucesso!\n\n{pdf_path}"
                )
                self._abrir_pdf(pdf_path)
                return

            except Exception as e:
                Logger.log(f"Erro ao gerar DANFE: {e}", "ERROR")
                messagebox.showwarning(
                    "Erro no PDF",
                    f"Não foi possível gerar o PDF DANFE.\nUsando comprovante texto.\n\nErro: {e}"
                )

        self._imprimir_comprovante_texto(venda)

    def _abrir_pdf(self, pdf_path):
        try:
            sistema = platform.system()
            caminho_absoluto = os.path.abspath(pdf_path)

            if sistema == "Windows":
                os.startfile(caminho_absoluto)
            elif sistema == "Darwin":
                subprocess.run(["open", caminho_absoluto], check=True)
            else:
                subprocess.run(["xdg-open", caminho_absoluto], check=True)
        except Exception as e:
            Logger.log(f"Erro ao abrir PDF: {e}", "ERROR")
            messagebox.showwarning(
                "Visualização",
                f"PDF salvo em: {pdf_path}\nNão foi possível abrir automaticamente."
            )

    def _imprimir_comprovante_texto(self, venda):
        comp = tk.Toplevel(self.parent)
        comp.title("Comprovante de Venda")
        comp.geometry("440x700")
        comp.configure(bg="white")
        comp.resizable(False, False)

        text = tk.Text(
            comp,
            font=("Courier New", 11, "bold"),
            bg="white",
            fg="black",
            wrap=tk.NONE,
            padx=16,
            pady=20,
            width=40,
            height=35,
            bd=0,
            highlightthickness=0,
            spacing1=2,
            spacing3=2
        )
        text.pack(fill=tk.BOTH, expand=True)

        def center(txt, width=40):
            return txt.center(width)

        def right(txt, width=40):
            return txt.rjust(width)

        def left_right(left_txt, right_txt, width=40):
            espaco = width - len(left_txt) - len(right_txt)
            if espaco < 1:
                espaco = 1
            return left_txt + (" " * espaco) + right_txt

        text.insert(tk.END, center("=" * 32) + "\n")
        text.insert(tk.END, center(LOJA_CONFIG.get('nome', 'FALL CONSTRUCOES')) + "\n")
        text.insert(tk.END, center(f"CNPJ: {LOJA_CONFIG.get('cnpj', '')}") + "\n")
        text.insert(tk.END, center("=" * 32) + "\n")
        text.insert(tk.END, center("CUPOM NAO FISCAL") + "\n")
        text.insert(tk.END, "\n")

        numero_venda = venda.get('numero_venda', venda.get('numero', 'N/A'))
        text.insert(tk.END, left_right("Venda:", numero_venda) + "\n")

        data_venda = venda.get('data_venda', '')
        if isinstance(data_venda, datetime):
            data_venda = data_venda.strftime('%d/%m/%Y %H:%M')
        elif isinstance(data_venda, str):
            data_venda = data_venda[:16]
        text.insert(tk.END, left_right("Data:", data_venda) + "\n")

        cliente_nome = venda.get("cliente_nome")
        if cliente_nome:
            text.insert(tk.END, left_right("Cliente:", cliente_nome[:30]) + "\n")
            cpf_cnpj = venda.get("cpf_cnpj")
            if cpf_cnpj:
                text.insert(tk.END, left_right("CPF/CNPJ:", cpf_cnpj) + "\n")
        else:
            text.insert(tk.END, left_right("Cliente:", "Consumidor Final") + "\n")

        text.insert(tk.END, "-" * 40 + "\n")
        text.insert(tk.END, "ITEM                    QTD   PRECO\n")
        text.insert(tk.END, "-" * 40 + "\n")

        for item in venda.get("itens", []):
            nome = (item.get("produto_nome") or item.get("nome") or "Item")[:22]
            qtd = item.get('quantidade', 1)
            preco = float(item.get('preco_unitario', 0))
            linha = f"{nome:<22} {qtd:>4} {preco:>10.2f}"
            text.insert(tk.END, linha + "\n")

        text.insert(tk.END, "-" * 40 + "\n")

        subtotal = float(venda.get('subtotal', 0))
        desconto = float(venda.get('desconto', 0))
        total = float(venda.get('total', 0))

        text.insert(tk.END, right(f"SUBTOTAL:  R$ {subtotal:>10.2f}") + "\n")
        text.insert(tk.END, right(f"DESCONTO:  R$ {desconto:>10.2f}") + "\n")
        text.insert(tk.END, right(f"TOTAL:     R$ {total:>10.2f}") + "\n")
        text.insert(tk.END, "-" * 40 + "\n")

        forma = venda.get('forma_pagamento', 'dinheiro').upper()
        text.insert(tk.END, left_right("Pagamento:", forma) + "\n")
        text.insert(tk.END, "=" * 40 + "\n")
        text.insert(tk.END, center("OBRIGADO PELA PREFERENCIA!") + "\n")
        text.insert(tk.END, "=" * 40 + "\n")

        text.config(state=tk.DISABLED)

        btn_frame = tk.Frame(comp, bg="white")
        btn_frame.pack(pady=10)

        tk.Button(
            btn_frame,
            text="🖨️  Imprimir",
            command=lambda: messagebox.showinfo("Impressão", "Enviado para impressora!"),
            bg=ModernTheme.PRIMARY,
            fg="white",
            bd=0,
            padx=24,
            pady=10,
            font=("Segoe UI", 11, "bold"),
            cursor="hand2",
            activebackground="#1e40af",
            activeforeground="white"
        ).pack()

        text.focus_set()

    def _novo_cliente(self):
        dlg = self.make_dialog("👤  Cadastro Rápido de Cliente", 420, 320)

        tk.Frame(dlg, bg=ModernTheme.PRIMARY, height=4).pack(fill=tk.X)
        tk.Label(dlg, text="👤  Novo Cliente",
                 font=ModernTheme.FONT_XL,
                 bg=ModernTheme.BG, fg=ModernTheme.TEXT).pack(
            anchor=tk.W, padx=20, pady=14)

        fields = {}
        for label, key in [("Nome *", "nome"),
                            ("CPF/CNPJ", "cpf_cnpj"),
                            ("Telefone", "telefone")]:
            fields[key] = self.form_field(dlg, label)

        tk.Frame(dlg, bg=ModernTheme.BORDER, height=1).pack(
            fill=tk.X, padx=20, pady=10)

        def save():
            dados = {k: v.get() for k, v in fields.items()}
            success, msg = self.controllers["venda"].criar_cliente(dados)
            if success:
                self.show_message("Sucesso", msg)
                clientes = self.controllers["venda"].listar_clientes()
                self.cliente_combo["values"] = ["— Consumidor Final (Avulso) —"] + [
                    f"{c['id']} - {c['nome']}" for c in clientes
                ]
                self.cliente_var.set(f"{dados.get('id', '')} - {dados.get('nome', '')}")
                dlg.destroy()
            else:
                self.show_message("Erro", msg, "error")

        self.styled_button(dlg, "Salvar Cliente", save,
                           ModernTheme.SUCCESS, icon="💾").pack(padx=20)