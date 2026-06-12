"""Histórico de Vendas - FALL Construcoes (reestilizado + botoes proporcionais)"""
import tkinter as tk
from tkinter import ttk, messagebox
import subprocess, os, platform
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

try:
    from utils.danfe_generator import DanfeGenerator
    DANFE_AVAILABLE = True
except ImportError:
    DANFE_AVAILABLE = False
    print("[AVISO] ReportLab nao instalado. Usando fallback de comprovante texto.")


class HistoricoVendasView(BaseView):
    def __init__(self, parent, controllers):
        super().__init__(parent, None)
        self.controllers = controllers
        self.danfe_gen = DanfeGenerator(LOJA_CONFIG) if DANFE_AVAILABLE else None
        self.build()

    def build(self):
        self.frame = tk.Frame(self.parent, bg=ModernTheme.BG)

        # ESTATISTICAS RAPIDAS
        stats_frame = tk.Frame(self.frame, bg=ModernTheme.BG)
        stats_frame.pack(fill=tk.X, padx=16, pady=12)

        self.stats_labels = {}
        stats_config = [
            ("total",   "📋 Total Vendas",  ModernTheme.PRIMARY, "#1e40af"),
            ("pago",    "✅ Pagas",         ModernTheme.SUCCESS, "#15803d"),
            ("pendente", "⏳ Pendentes",    ModernTheme.WARNING, "#b45309"),
            ("cancelado", "❌ Canceladas",   ModernTheme.DANGER,  "#b91c1c"),
            ("valor",   "💰 Total em Vendas", ModernTheme.INFO, "#1e40af"),
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
                     font=("Segoe UI", 16, "bold"),
                     bg=ModernTheme.CARD_BG, fg=ModernTheme.TEXT)
            self.stats_labels[key].pack(anchor=tk.W)

        # CARD DE FILTROS
        filter_card = tk.Frame(self.frame, bg=ModernTheme.CARD_BG,
                               highlightbackground=ModernTheme.BORDER,
                               highlightthickness=1)
        filter_card.pack(fill=tk.X, padx=16, pady=8)
        tk.Frame(filter_card, bg=ModernTheme.PRIMARY, height=3).pack(fill=tk.X)

        inner = tk.Frame(filter_card, bg=ModernTheme.CARD_BG, padx=16, pady=12)
        inner.pack(fill=tk.X)

        search_box = tk.Frame(inner, bg=ModernTheme.CARD_BG,
                              highlightbackground=ModernTheme.BORDER,
                              highlightthickness=1)
        search_box.pack(side=tk.LEFT)

        tk.Label(search_box, text="🔍", font=("Segoe UI", 13),
                 bg=ModernTheme.CARD_BG, fg=ModernTheme.INFO).pack(
            side=tk.LEFT, padx=8)
        self.busca_entry = self.styled_entry(search_box,
                                              "Buscar por numero, cliente...",
                                              width=32)
        self.busca_entry.pack(side=tk.LEFT, padx=8)
        self.busca_entry.bind("<Return>", lambda e: self._load_vendas())

        btn_buscar = tk.Button(search_box, text="Buscar", command=self._load_vendas,
                               bg=ModernTheme.INFO, fg="white",
                               font=("Segoe UI", 9, "bold"),
                               bd=0, padx=16, pady=6, cursor="hand2",
                               activebackground="#1e40af")
        btn_buscar.pack(side=tk.LEFT)
        btn_buscar.bind("<Enter>", lambda e: btn_buscar.config(bg="#1e40af"))
        btn_buscar.bind("<Leave>", lambda e: btn_buscar.config(bg=ModernTheme.INFO))

        tk.Frame(inner, bg=ModernTheme.BORDER, width=1).pack(
            side=tk.LEFT, fill=tk.Y, padx=16, pady=4)

        tk.Label(inner, text="FILTRO:",
                 font=("Segoe UI", 9, "bold"),
                 bg=ModernTheme.CARD_BG, fg=ModernTheme.TEXT_MUTED).pack(
            side=tk.LEFT, padx=8)

        self.status_var = tk.StringVar(value="todos")
        status_opts = [
            ("Todas",      "todos",     ModernTheme.TEXT),
            ("✅ Pagas",   "pago",      ModernTheme.SUCCESS),
            ("⏳ Pendentes", "pendente", ModernTheme.WARNING),
            ("❌ Canceladas", "cancelado", ModernTheme.DANGER),
        ]
        for label, val, color in status_opts:
            rb = tk.Radiobutton(inner, text=label,
                                variable=self.status_var, value=val,
                                bg=ModernTheme.CARD_BG, fg=color,
                                font=("Segoe UI", 9, "bold"),
                                selectcolor=ModernTheme.CARD_BG,
                                activebackground=ModernTheme.CARD_BG,
                                command=self._load_vendas)
            rb.pack(side=tk.LEFT, padx=6)

        btn_atualizar = tk.Button(inner, text="🔄  Atualizar", command=self._load_vendas,
                                  bg=ModernTheme.INFO, fg="white",
                                  font=("Segoe UI", 9, "bold"),
                                  bd=0, padx=16, pady=6, cursor="hand2",
                                  activebackground="#1e40af")
        btn_atualizar.pack(side=tk.RIGHT)
        btn_atualizar.bind("<Enter>", lambda e: btn_atualizar.config(bg="#1e40af"))
        btn_atualizar.bind("<Leave>", lambda e: btn_atualizar.config(bg=ModernTheme.INFO))

        # TABELA DE VENDAS
        table_card = tk.Frame(self.frame, bg=ModernTheme.CARD_BG,
                              highlightbackground=ModernTheme.BORDER,
                              highlightthickness=1)
        table_card.pack(fill=tk.BOTH, expand=True, padx=16, pady=8)

        table_header = tk.Frame(table_card, bg=ModernTheme.PRIMARY, height=36)
        table_header.pack(fill=tk.X)
        tk.Label(table_header, text="📋  REGISTRO DE VENDAS",
                 font=("Segoe UI", 10, "bold"),
                 bg=ModernTheme.PRIMARY, fg="white").pack(
            side=tk.LEFT, padx=14, pady=6)

        self.contador_label = tk.Label(table_header, text="0 vendas",
                 font=("Segoe UI", 9),
                 bg=ModernTheme.PRIMARY, fg="white")
        self.contador_label.pack(side=tk.RIGHT, padx=14, pady=6)

        table_body = tk.Frame(table_card, bg=ModernTheme.CARD_BG)
        table_body.pack(fill=tk.BOTH, expand=True, padx=12, pady=12)

        columns = ("Nº", "Data", "Cliente", "Itens", "Total", "Pagamento", "Status")
        self.tree = ttk.Treeview(table_body, columns=columns,
                                 show="headings")
        for col, w in zip(columns, [130, 130, 180, 55, 100, 100, 120]):
            self.tree.heading(col, text=col)
            self.tree.column(col, width=w)

        self.tree.tag_configure("pago",      background="#f0fdf4", foreground="#15803d")
        self.tree.tag_configure("pendente",  background="#fffbeb", foreground="#b45309")
        self.tree.tag_configure("cancelado", background="#fef2f2", foreground="#dc2626")
        self.tree.tag_configure("even",      background="#f8fafc")
        self.tree.tag_configure("odd",       background="white")

        sb = ttk.Scrollbar(table_body, orient=tk.VERTICAL,
                           command=self.tree.yview)
        self.tree.configure(yscrollcommand=sb.set)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb.pack(side=tk.RIGHT, fill=tk.Y)

        self.tree.bind("<Double-1>", lambda e: self._ver_detalhes())

        # CARD DE ACOES - BOTOES PROPORCIONAIS
        action_card = tk.Frame(self.frame, bg=ModernTheme.CARD_BG,
                               highlightbackground=ModernTheme.BORDER,
                               highlightthickness=1)
        action_card.pack(fill=tk.X, padx=16, pady=(8, 16))
        tk.Frame(action_card, bg=ModernTheme.SUCCESS, height=4).pack(fill=tk.X)

        action_inner = tk.Frame(action_card, bg=ModernTheme.CARD_BG, padx=16, pady=14)
        action_inner.pack(fill=tk.X)

        tk.Label(action_inner, text="ACOES DA VENDA SELECIONADA",
                 font=("Segoe UI", 11, "bold"),
                 bg=ModernTheme.CARD_BG, fg=ModernTheme.TEXT).pack(
            side=tk.LEFT, padx=(0, 20))

        actions = [
            ("🖨️  Reimprimir",    ModernTheme.INFO,    "#1e40af",    self._reimprimir),
            ("✅  Marcar Pago",    ModernTheme.SUCCESS, "#15803d",    lambda: self._mudar_status("pago")),
            ("⏳  Marcar Pendente", ModernTheme.WARNING, "#b45309",    lambda: self._mudar_status("pendente")),
            ("❌  Cancelar",       ModernTheme.DANGER,  "#b91c1c",    lambda: self._mudar_status("cancelado")),
            ("🔍  Ver Detalhes",   ModernTheme.PRIMARY, "#1e40af",    self._ver_detalhes),
        ]

        for label, color, hover, cmd in actions:
            btn = tk.Button(action_inner, text=label, command=cmd,
                            bg=color, fg="white",
                            font=("Segoe UI", 10, "bold"),
                            bd=0, padx=18, pady=10,
                            cursor="hand2",
                            activebackground=hover)
            btn.pack(side=tk.LEFT, padx=4)
            btn.bind("<Enter>", lambda e, c=hover: btn.config(bg=c))
            btn.bind("<Leave>", lambda e, c=color: btn.config(bg=c))

        self._load_vendas()

    def _load_vendas(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        try:
            vendas = self.controllers["venda"].listar_vendas(100) or []

            contagem = {"total": 0, "pago": 0, "pendente": 0, "cancelado": 0}
            total_valor = 0

            for idx, v in enumerate(vendas):
                if not v or not isinstance(v, dict):
                    continue
                status = v.get("status", "pendente")
                contagem[status] = contagem.get(status, 0) + 1
                contagem["total"] += 1
                total_valor += float(v.get('total', 0) or 0)

                _icons = {"pago": "✔", "pendente": "⏳", "cancelado": "✖"}
                icon = _icons.get(status, "•")

                try:
                    vd = self.controllers["venda"].obter_venda(v["id"])
                    n_itens = len(vd.get("itens", [])) if vd else 0
                except Exception:
                    n_itens = 0

                row_tag = status if status in ("pago", "pendente", "cancelado") else "even"
                if not row_tag:
                    row_tag = "even" if idx % 2 == 0 else "odd"

                self.tree.insert("", tk.END, tags=(row_tag,), values=(
                    v.get("numero_venda", ""),
                    str(v.get("data_venda", ""))[:16],
                    str(v.get("cliente_nome") or "Avulso")[:22],
                    n_itens,
                    f"R$ {float(v.get('total', 0) or 0):.2f}",
                    v.get("forma_pagamento", ""),
                    f"{icon} {status}",
                ))

            self.stats_labels["total"].config(text=str(contagem["total"]))
            self.stats_labels["pago"].config(text=str(contagem["pago"]))
            self.stats_labels["pendente"].config(text=str(contagem["pendente"]))
            self.stats_labels["cancelado"].config(text=str(contagem["cancelado"]))
            self.stats_labels["valor"].config(text=f"R$ {total_valor:,.2f}")
            self.contador_label.config(text=f"{contagem['total']} vendas")

        except Exception as e:
            Logger.log(f"Erro ao carregar vendas: {e}", "ERROR")

    def _get_selected(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Aviso", "Selecione uma venda")
            return None
        numero = self.tree.item(sel[0])["values"][0]
        try:
            for v in (self.controllers["venda"].listar_vendas(100) or []):
                if v and v.get("numero_venda") == numero:
                    return v
        except Exception:
            pass
        return None

    def _reimprimir(self):
        v = self._get_selected()
        if not v:
            return
        self._escolher_tipo_comprovante(v["id"])

    def _escolher_tipo_comprovante(self, venda_id):
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

        tk.Label(dlg, text="Escolha como deseja reimprimir a venda:",
                 font=ModernTheme.FONT_BASE,
                 bg=ModernTheme.BG, fg=ModernTheme.TEXT_MUTED).pack(pady=(0, 16))

        btn_frame = tk.Frame(dlg, bg=ModernTheme.BG)
        btn_frame.pack(pady=8)

        def escolher_danfe():
            dlg.destroy()
            self._imprimir_danfe(venda_id)

        def escolher_cupom():
            dlg.destroy()
            self._imprimir_comprovante(venda_id)

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

    def _imprimir_danfe(self, venda_id=None):
        if venda_id is None:
            return

        venda = self.controllers["venda"].obter_venda(venda_id)
        if not venda:
            messagebox.showwarning("Aviso", "Venda nao encontrada.")
            return

        if not venda.get("itens"):
            vd = self.controllers["venda"].obter_venda(venda_id)
            if vd and vd.get("itens"):
                venda["itens"] = vd["itens"]

        if DANFE_AVAILABLE and self.danfe_gen:
            try:
                os.makedirs("comprovantes", exist_ok=True)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                pdf_path = f"comprovantes/DANFE_{venda.get('numero_venda', '000')}_{timestamp}.pdf"

                self.danfe_gen.gerar(venda, output_path=pdf_path)

                messagebox.showinfo(
                    "DANFE Gerado",
                    "Nota Fiscal PDF reimpressa com sucesso!\n\n" + pdf_path
                )
                self._abrir_pdf(pdf_path)
                return

            except Exception as e:
                Logger.log(f"Erro ao gerar DANFE: {e}", "ERROR")
                messagebox.showwarning(
                    "Erro no PDF",
                    "Nao foi possivel gerar o PDF DANFE.\n\nErro: " + str(e)
                )
        else:
            messagebox.showwarning(
                "DANFE Indisponivel",
                "ReportLab nao esta instalado.\nUse o Cupom Fiscal como alternativa."
            )

    def _imprimir_comprovante(self, venda_id=None):
        if venda_id is None:
            return

        venda = self.controllers["venda"].obter_venda(venda_id)
        if not venda:
            messagebox.showwarning("Aviso", "Venda nao encontrada.")
            return

        if not venda.get("itens"):
            vd = self.controllers["venda"].obter_venda(venda_id)
            if vd and vd.get("itens"):
                venda["itens"] = vd["itens"]

        if DANFE_AVAILABLE and self.danfe_gen:
            try:
                os.makedirs("comprovantes", exist_ok=True)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                pdf_path = f"comprovantes/CUPOM_{venda.get('numero_venda', '000')}_{timestamp}.pdf"

                self.danfe_gen.gerar(venda, output_path=pdf_path)

                messagebox.showinfo(
                    "Cupom Gerado",
                    "Comprovante PDF gerado com sucesso!\n\n" + pdf_path
                )
                self._abrir_pdf(pdf_path)
                return

            except Exception as e:
                Logger.log(f"Erro ao gerar PDF do cupom: {e}", "ERROR")
                messagebox.showwarning(
                    "Erro no PDF",
                    "Nao foi possivel gerar o PDF.\nUsando comprovante texto.\n\nErro: " + str(e)
                )

        self._janela_comprovante(venda)

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
                "Visualizacao",
                "PDF salvo em: " + pdf_path + "\nNao foi possivel abrir automaticamente."
            )

    def _mudar_status(self, status):
        v = self._get_selected()
        if v:
            ok, msg = self.controllers["venda"].mudar_status(v["id"], status)
            if ok:
                messagebox.showinfo("Sucesso", msg)
                self._load_vendas()
            else:
                messagebox.showerror("Erro", msg)

    def _ver_detalhes(self):
        v = self._get_selected()
        if not v:
            return
        vc = self.controllers["venda"].obter_venda(v["id"])
        if not vc:
            return

        dlg = self.make_dialog("📋  Detalhes da Venda", 540, 640)
        dlg.configure(bg=ModernTheme.BG)

        header = tk.Frame(dlg, bg=ModernTheme.PRIMARY, height=50)
        header.pack(fill=tk.X)
        tk.Label(header, text="📋  Venda " + v['numero_venda'],
                 font=("Segoe UI", 14, "bold"),
                 bg=ModernTheme.PRIMARY, fg="white").pack(
            side=tk.LEFT, padx=20, pady=10)

        status = v.get("status", "pendente")
        status_colors = {"pago": ModernTheme.SUCCESS, "pendente": ModernTheme.WARNING, "cancelado": ModernTheme.DANGER}
        status_color = status_colors.get(status, ModernTheme.TEXT_MUTED)
        tk.Label(header, text="● " + status.upper(),
                 font=("Segoe UI", 10, "bold"),
                 bg=ModernTheme.PRIMARY, fg=status_color).pack(
            side=tk.RIGHT, padx=20, pady=10)

        info_card = tk.Frame(dlg, bg=ModernTheme.CARD_BG,
                             highlightbackground=ModernTheme.BORDER,
                             highlightthickness=1)
        info_card.pack(fill=tk.X, padx=16, pady=12)
        tk.Frame(info_card, bg=ModernTheme.INFO, height=3).pack(fill=tk.X)

        info_inner = tk.Frame(info_card, bg=ModernTheme.CARD_BG, padx=16, pady=12)
        info_inner.pack(fill=tk.X)

        pairs = [
            ("📅 Data",       str(v.get("data_venda", ""))[:16]),
            ("👤 Cliente",    str(v.get("cliente_nome") or "Avulso")),
            ("💳 Pagamento",  v.get("forma_pagamento", "dinheiro")),
            ("💰 Subtotal",   f"R$ {float(v.get('subtotal', 0) or 0):.2f}"),
            ("🏷️ Desconto",   f"R$ {float(v.get('desconto', 0) or 0):.2f}"),
            ("💵 TOTAL",      f"R$ {float(v.get('total', 0) or 0):.2f}"),
        ]

        for i, (label, value) in enumerate(pairs):
            if i % 2 == 0:
                row = tk.Frame(info_inner, bg=ModernTheme.CARD_BG)
                row.pack(fill=tk.X, pady=3)

            col = tk.Frame(row, bg=ModernTheme.CARD_BG)
            col.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=12)

            is_total = "TOTAL" in label
            tk.Label(col, text=label,
                     font=("Segoe UI", 9, "bold" if not is_total else "bold"),
                     bg=ModernTheme.CARD_BG,
                     fg=ModernTheme.SUCCESS if is_total else ModernTheme.TEXT_MUTED).pack(anchor=tk.W)
            tk.Label(col, text=value,
                     font=("Segoe UI", 11, "bold" if is_total else "normal"),
                     bg=ModernTheme.CARD_BG,
                     fg=ModernTheme.SUCCESS if is_total else ModernTheme.TEXT).pack(anchor=tk.W)

        itens_card = tk.Frame(dlg, bg=ModernTheme.CARD_BG,
                              highlightbackground=ModernTheme.BORDER,
                              highlightthickness=1)
        itens_card.pack(fill=tk.BOTH, expand=True, padx=16, pady=12)
        tk.Frame(itens_card, bg=ModernTheme.WARNING, height=3).pack(fill=tk.X)

        itens_header = tk.Frame(itens_card, bg=ModernTheme.CARD_BG, padx=16, pady=10)
        itens_header.pack(fill=tk.X)
        tk.Label(itens_header, text="📦  ITENS DA VENDA",
                 font=("Segoe UI", 10, "bold"),
                 bg=ModernTheme.CARD_BG, fg=ModernTheme.WARNING).pack(anchor=tk.W)

        itens_body = tk.Frame(itens_card, bg=ModernTheme.CARD_BG, padx=16, pady=12)
        itens_body.pack(fill=tk.BOTH, expand=True)

        cols = ("Produto", "Qtd", "Preço Unit.", "Subtotal")
        tree = ttk.Treeview(itens_body, columns=cols, show="headings", height=8)
        for col, w in zip(cols, [280, 60, 100, 100]):
            tree.heading(col, text=col)
            tree.column(col, width=w, anchor=tk.CENTER if col != "Produto" else tk.W)
        tree.pack(fill=tk.BOTH, expand=True)
        tree.tag_configure("even", background="#f8fafc")
        tree.tag_configure("odd", background="white")

        for idx, item in enumerate(vc.get("itens", [])):
            tag = "even" if idx % 2 == 0 else "odd"
            tree.insert("", tk.END, tags=(tag,), values=(
                str(item.get("produto_nome", ""))[:35],
                item.get("quantidade", 0),
                f"R$ {float(item.get('preco_unitario', 0) or 0):.2f}",
                f"R$ {float(item.get('subtotal', 0) or 0):.2f}",
            ))

        btn_frame = tk.Frame(dlg, bg=ModernTheme.BG, padx=16, pady=12)
        btn_frame.pack(fill=tk.X)

        btn_reimprimir = tk.Button(btn_frame, text="🖨️  REIMPRIMIR",
                           command=lambda: self._reimprimir_from_detail(v),
                           bg=ModernTheme.PRIMARY, fg="white",
                           font=("Segoe UI", 10, "bold"),
                           bd=0, padx=20, pady=10, cursor="hand2",
                           activebackground="#1e40af")
        btn_reimprimir.pack(side=tk.LEFT, padx=4)
        btn_reimprimir.bind("<Enter>", lambda e: btn_reimprimir.config(bg="#1e40af"))
        btn_reimprimir.bind("<Leave>", lambda e: btn_reimprimir.config(bg=ModernTheme.PRIMARY))

        btn_fechar = tk.Button(btn_frame, text="Fechar", command=dlg.destroy,
                           bg=ModernTheme.SECONDARY, fg="white",
                           font=("Segoe UI", 10, "bold"),
                           bd=0, padx=20, pady=10, cursor="hand2")
        btn_fechar.pack(side=tk.LEFT, padx=4)

    def _reimprimir_from_detail(self, venda):
        self._escolher_tipo_comprovante(venda["id"])

    def _janela_comprovante(self, venda):
        comp = tk.Toplevel(self.parent)
        comp.title("Comprovante  " + venda.get('numero_venda', ''))
        comp.geometry("460x680")
        comp.configure(bg="white")

        txt = tk.Text(comp, font=("Courier", 11), bg="white",
                      fg="#1e293b", wrap=tk.WORD, padx=20, pady=20,
                      bd=0, relief=tk.FLAT)
        txt.pack(fill=tk.BOTH, expand=True)

        L = lambda s: txt.insert(tk.END, s + "\n")
        L("=" * 40)
        L("  " + LOJA_CONFIG['nome'])
        L("  CNPJ: " + LOJA_CONFIG['cnpj'])
        L("  " + LOJA_CONFIG['endereco'])
        L("=" * 40)
        L("")
        L("  CUPOM NAO FISCAL – REIMPRESSAO")
        L("  Venda:  " + venda.get('numero_venda', ''))
        L("  Data:   " + str(venda.get('data_venda', ''))[:16])
        if venda.get("cliente_nome"):
            L("  Cliente: " + venda['cliente_nome'])
        L("-" * 40)
        L("{:<22}{:>4}  {:>8}".format("ITEM", "QTD", "PRECO"))
        L("-" * 40)
        for item in venda.get("itens", []):
            nome = str(item.get("produto_nome", ""))[:20]
            qtd  = str(item.get("quantidade", 0))
            preco = f"{float(item.get('preco_unitario', 0) or 0):.2f}"
            L("{:<22}{:>4}  R${:>7}".format(nome, qtd, preco))
        L("-" * 40)
        L("{:<30}R$ {:.2f}".format("SUBTOTAL:", float(venda.get('subtotal', 0) or 0)))
        L("{:<30}R$ {:.2f}".format("DESCONTO:", float(venda.get('desconto', 0) or 0)))
        L("{:<30}R$ {:.2f}".format("TOTAL:", float(venda.get('total', 0) or 0)))
        L("-" * 40)
        L("  Pagamento: " + str(venda.get('forma_pagamento', '')).upper())
        L("")
        L("=" * 40)
        L("  OBRIGADO PELA PREFERENCIA!")
        L("=" * 40)
        txt.config(state=tk.DISABLED)

        btn_row = tk.Frame(comp, bg="white")
        btn_row.pack(pady=10)

        def _imprimir():
            try:
                tmp = os.path.join(os.environ.get("TEMP", "/tmp"),
                                   "reimpressao.txt")
                with open(tmp, "w", encoding="utf-8") as f:
                    f.write(txt.get(1.0, tk.END))
                if os.name == "nt":
                    os.startfile(tmp, "print")
                else:
                    subprocess.run(["lp", tmp])
                messagebox.showinfo("Impressao", "Enviado para a impressora!")
            except Exception as e:
                messagebox.showerror("Erro", str(e))

        def _salvar():
            from tkinter import filedialog
            fn = filedialog.asksaveasfilename(
                defaultextension=".txt",
                filetypes=[("Texto", "*.txt")],
                initialfile="venda_" + venda.get('numero_venda', '') + ".txt")
            if fn:
                with open(fn, "w", encoding="utf-8") as f:
                    f.write(txt.get(1.0, tk.END))
                messagebox.showinfo("Salvo", "Arquivo salvo em:\n" + fn)

        tk.Button(btn_row, text="🖨️  Imprimir", command=_imprimir,
                  bg=ModernTheme.PRIMARY, fg="white",
                  font=("Segoe UI", 10, "bold"),
                  bd=0, padx=16, pady=8, cursor="hand2").pack(side=tk.LEFT, padx=5)
        tk.Button(btn_row, text="💾  Salvar", command=_salvar,
                  bg=ModernTheme.SUCCESS, fg="white",
                  font=("Segoe UI", 10, "bold"),
                  bd=0, padx=16, pady=8, cursor="hand2").pack(side=tk.LEFT, padx=5)