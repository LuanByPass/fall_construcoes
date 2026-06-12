"""Tela de Relatórios - FALL Construções (sem aba Clientes)"""
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime, timedelta
from views.base_view import BaseView
from config import ModernTheme, LOJA_CONFIG
import subprocess
import os

try:
    from utils.logger import Logger
except Exception:
    class Logger:
        @classmethod
        def log(cls, msg, level="INFO"):
            print(f"[{level}] {msg}")


class RelatorioView(BaseView):
    def __init__(self, parent, controllers):
        super().__init__(parent, None)
        self.controllers = controllers
        self.build()

    def build(self):
        self.frame = tk.Frame(self.parent, bg=ModernTheme.BG)


        self.notebook = ttk.Notebook(self.frame)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=16, pady=(0, 16))

        self.tab_estoque  = tk.Frame(self.notebook, bg=ModernTheme.BG)
        self.tab_vendas   = tk.Frame(self.notebook, bg=ModernTheme.BG)
        self.tab_ranking  = tk.Frame(self.notebook, bg=ModernTheme.BG)

        self.notebook.add(self.tab_estoque,  text="📦  Estoque")
        self.notebook.add(self.tab_vendas,   text="🛒  Vendas")
        self.notebook.add(self.tab_ranking,  text="🏆  Ranking")

        self._build_estoque_tab()
        self._build_vendas_tab()
        self._build_ranking_tab()

    # ── Aba Estoque ───────────────────────────────────────────────────────────
    def _build_estoque_tab(self):
        toolbar = tk.Frame(self.tab_estoque, bg=ModernTheme.BG)
        toolbar.pack(fill=tk.X, padx=16, pady=8)

        tk.Button(toolbar, text="🔄 Atualizar", command=self._load_estoque,
                 bg=ModernTheme.PRIMARY, fg='white', bd=0, padx=15, pady=8,
                 font=('Segoe UI', 10, 'bold'), cursor='hand2').pack(side=tk.LEFT)
        tk.Button(toolbar, text="🖨️ Imprimir", command=self._imprimir_estoque,
                 bg=ModernTheme.INFO, fg='white', bd=0, padx=15, pady=8,
                 font=('Segoe UI', 10, 'bold'), cursor='hand2').pack(side=tk.LEFT, padx=6)

        # KPI strip de estoque
        self.estoque_kpi = tk.Frame(self.tab_estoque, bg=ModernTheme.BG)
        self.estoque_kpi.pack(fill=tk.X, padx=16, pady=(0, 8))

        # Tabela
        card = tk.Frame(self.tab_estoque, bg=ModernTheme.CARD_BG,
                        highlightbackground=ModernTheme.BORDER,
                        highlightthickness=1)
        card.pack(fill=tk.BOTH, expand=True, padx=16, pady=(0, 16))

        columns = ("Categoria", "Produtos", "Itens",
                   "Valor Custo", "Valor Venda", "Lucro Potencial")
        self.estoque_tree = ttk.Treeview(card, columns=columns,
                                         show="headings", height=15)
        for col, w in zip(columns, [160, 80, 80, 130, 130, 130]):
            self.estoque_tree.heading(col, text=col)
            self.estoque_tree.column(col, width=w)

        sb = ttk.Scrollbar(card, orient=tk.VERTICAL, command=self.estoque_tree.yview)
        self.estoque_tree.configure(yscrollcommand=sb.set)
        self.estoque_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb.pack(side=tk.RIGHT, fill=tk.Y)

        self._load_estoque()

    def _load_estoque(self):
        for w in self.estoque_kpi.winfo_children():
            w.destroy()
        for item in self.estoque_tree.get_children():
            self.estoque_tree.delete(item)

        try:
            from utils.relatorio import RelatorioController
            rel   = RelatorioController()
            dados = rel.estoque_atual()
            resumo = rel.resumo_financeiro()

            if resumo:
                r = resumo[0]
                kpis = [
                    ("📦", "Total Produtos",   str(r.get("total_produtos") or 0),    ModernTheme.PRIMARY),
                    ("📊", "Total Itens",      str(r.get("total_itens") or 0),       ModernTheme.INFO),
                    ("💸", "Valor Custo",      f"R$ {float(r.get('valor_estoque_custo') or 0):,.2f}", ModernTheme.DANGER),
                    ("💰", "Valor Venda",      f"R$ {float(r.get('valor_estoque_venda') or 0):,.2f}", ModernTheme.SUCCESS),
                    ("📈", "Lucro Potencial",  f"R$ {float(r.get('lucro_potencial') or 0):,.2f}",     ModernTheme.WARNING),
                ]
                for icon, title, val, color in kpis:
                    c = tk.Frame(self.estoque_kpi, bg=ModernTheme.CARD_BG,
                                 highlightbackground=ModernTheme.BORDER,
                                 highlightthickness=1)
                    c.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=4)
                    tk.Frame(c, bg=color, height=3).pack(fill=tk.X)
                    inner = tk.Frame(c, bg=ModernTheme.CARD_BG, padx=12, pady=10)
                    inner.pack()
                    tk.Label(inner, text=f"{icon}  {title}",
                             font=('Segoe UI', 9),
                             bg=ModernTheme.CARD_BG, fg=ModernTheme.CIMENTO).pack(anchor=tk.W)
                    tk.Label(inner, text=val,
                             font=("Segoe UI", 14, "bold"),
                             bg=ModernTheme.CARD_BG, fg=color).pack(anchor=tk.W)

            for d in dados:
                self.estoque_tree.insert("", tk.END, values=(
                    d["categoria"], d["total_produtos"], d["total_itens"],
                    f"R$ {float(d['valor_custo'] or 0):,.2f}",
                    f"R$ {float(d['valor_venda'] or 0):,.2f}",
                    f"R$ {float(d['lucro_potencial'] or 0):,.2f}",
                ))
        except Exception as e:
            Logger.log(f"Erro relatório estoque: {e}", "ERROR")

    def _imprimir_estoque(self):
        self._imprimir_relatorio("RELATÓRIO DE ESTOQUE", self.estoque_tree,
                                 ["Categoria", "Produtos", "Itens",
                                  "Valor Custo", "Valor Venda", "Lucro Potencial"])

    # ── Aba Vendas ────────────────────────────────────────────────────────────
    def _build_vendas_tab(self):
        toolbar = tk.Frame(self.tab_vendas, bg=ModernTheme.BG)
        toolbar.pack(fill=tk.X, padx=16, pady=8)

        tk.Label(toolbar, text="De:", bg=ModernTheme.BG,
                 font=('Segoe UI', 10),
                 fg=ModernTheme.CIMENTO).pack(side=tk.LEFT)
        self.data_inicio = tk.Entry(toolbar, font=('Segoe UI', 11), width=12, bd=2, relief=tk.SOLID)
        self.data_inicio.pack(side=tk.LEFT, padx=(4, 12))
        self.data_inicio.insert(0, (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d"))

        tk.Label(toolbar, text="Até:", bg=ModernTheme.BG,
                 font=('Segoe UI', 10),
                 fg=ModernTheme.CIMENTO).pack(side=tk.LEFT)
        self.data_fim = tk.Entry(toolbar, font=('Segoe UI', 11), width=12, bd=2, relief=tk.SOLID)
        self.data_fim.pack(side=tk.LEFT, padx=(4, 12))
        self.data_fim.insert(0, datetime.now().strftime("%Y-%m-%d"))

        tk.Button(toolbar, text="🔄 Atualizar", command=self._load_vendas,
                 bg=ModernTheme.PRIMARY, fg='white', bd=0, padx=15, pady=8,
                 font=('Segoe UI', 10, 'bold'), cursor='hand2').pack(side=tk.LEFT)
        tk.Button(toolbar, text="🖨️ Imprimir", command=self._imprimir_vendas,
                 bg=ModernTheme.INFO, fg='white', bd=0, padx=15, pady=8,
                 font=('Segoe UI', 10, 'bold'), cursor='hand2').pack(side=tk.LEFT, padx=6)

        card = tk.Frame(self.tab_vendas, bg=ModernTheme.CARD_BG,
                        highlightbackground=ModernTheme.BORDER,
                        highlightthickness=1)
        card.pack(fill=tk.BOTH, expand=True, padx=16, pady=(0, 16))

        columns = ("Dia", "Vendas", "Faturado", "Descontos", "Ticket Médio")
        self.vendas_tree = ttk.Treeview(card, columns=columns,
                                        show="headings", height=16)
        for col, w in zip(columns, [130, 80, 130, 130, 130]):
            self.vendas_tree.heading(col, text=col)
            self.vendas_tree.column(col, width=w)

        sb = ttk.Scrollbar(card, orient=tk.VERTICAL, command=self.vendas_tree.yview)
        self.vendas_tree.configure(yscrollcommand=sb.set)
        self.vendas_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb.pack(side=tk.RIGHT, fill=tk.Y)

        self._load_vendas()

    def _load_vendas(self):
        for item in self.vendas_tree.get_children():
            self.vendas_tree.delete(item)
        try:
            from utils.relatorio import RelatorioController
            rel   = RelatorioController()
            dados = rel.vendas_periodo(self.data_inicio.get(), self.data_fim.get())
            for d in dados:
                self.vendas_tree.insert("", tk.END, values=(
                    d["dia"], d["total_vendas"],
                    f"R$ {float(d['total_faturado'] or 0):,.2f}",
                    f"R$ {float(d['total_descontos'] or 0):,.2f}",
                    f"R$ {float(d['ticket_medio'] or 0):,.2f}",
                ))
        except Exception as e:
            Logger.log(f"Erro relatório vendas: {e}", "ERROR")

    def _imprimir_vendas(self):
        self._imprimir_relatorio("RELATÓRIO DE VENDAS", self.vendas_tree,
                                 ["Dia", "Vendas", "Faturado", "Descontos", "Ticket Médio"])

    # ── Aba Ranking ───────────────────────────────────────────────────────────
    def _build_ranking_tab(self):
        toolbar = tk.Frame(self.tab_ranking, bg=ModernTheme.BG)
        toolbar.pack(fill=tk.X, padx=16, pady=8)

        tk.Button(toolbar, text="🔄 Atualizar", command=self._load_ranking,
                 bg=ModernTheme.PRIMARY, fg='white', bd=0, padx=15, pady=8,
                 font=('Segoe UI', 10, 'bold'), cursor='hand2').pack(side=tk.LEFT)
        tk.Button(toolbar, text="🖨️ Imprimir", command=self._imprimir_ranking,
                 bg=ModernTheme.INFO, fg='white', bd=0, padx=15, pady=8,
                 font=('Segoe UI', 10, 'bold'), cursor='hand2').pack(side=tk.LEFT, padx=6)

        card = tk.Frame(self.tab_ranking, bg=ModernTheme.CARD_BG,
                        highlightbackground=ModernTheme.BORDER,
                        highlightthickness=1)
        card.pack(fill=tk.BOTH, expand=True, padx=16, pady=(0, 16))

        columns = ("Produto", "Código", "Qtd Vendida", "Faturado")
        self.ranking_tree = ttk.Treeview(card, columns=columns,
                                         show="headings", height=16)
        for col, w in zip(columns, [320, 110, 110, 130]):
            self.ranking_tree.heading(col, text=col)
            self.ranking_tree.column(col, width=w)

        sb = ttk.Scrollbar(card, orient=tk.VERTICAL, command=self.ranking_tree.yview)
        self.ranking_tree.configure(yscrollcommand=sb.set)
        self.ranking_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb.pack(side=tk.RIGHT, fill=tk.Y)

        self._load_ranking()

    def _load_ranking(self):
        for item in self.ranking_tree.get_children():
            self.ranking_tree.delete(item)
        try:
            from utils.relatorio import RelatorioController
            rel   = RelatorioController()
            dados = rel.ranking_produtos(20)
            for i, d in enumerate(dados, 1):
                medal = {1: "🥇", 2: "🥈", 3: "🥉"}.get(i, f"{i:>2}.")
                self.ranking_tree.insert("", tk.END, values=(
                    f"{medal}  {d['nome']}",
                    d["codigo"],
                    d.get("total_vendido") or 0,
                    f"R$ {float(d.get('total_faturado') or 0):,.2f}",
                ))
        except Exception as e:
            Logger.log(f"Erro ranking: {e}", "ERROR")

    def _imprimir_ranking(self):
        self._imprimir_relatorio("RANKING DE PRODUTOS", self.ranking_tree,
                                 ["Produto", "Código", "Qtd Vendida", "Faturado"])

    # ── Impressão genérica ────────────────────────────────────────────────────
    def _imprimir_relatorio(self, titulo, tree, colunas):
        comp = tk.Toplevel(self.parent)
        comp.title(f"Impressão — {titulo}")
        comp.geometry("640x720")
        comp.configure(bg="white")

        text = tk.Text(comp, font=("Courier", 10), bg="white",
                       wrap=tk.WORD, padx=20, pady=20)
        text.pack(fill=tk.BOTH, expand=True)

        ln = "=" * 56 + ""
        sl = "-" * 56 + ""

        text.insert(tk.END, ln)
        text.insert(tk.END, f"  {LOJA_CONFIG['nome']}")
        text.insert(tk.END, f"  {LOJA_CONFIG['endereco']}")
        text.insert(tk.END, f"  CNPJ: {LOJA_CONFIG['cnpj']}")
        text.insert(tk.END, ln + "")
        text.insert(tk.END, f"{titulo}")
        text.insert(tk.END,
            f"Gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M')}")

        header = " | ".join(f"{c:<14}" for c in colunas)
        text.insert(tk.END, header + "")
        text.insert(tk.END, sl)

        for item in tree.get_children():
            vals = tree.item(item)["values"]
            line = " | ".join(f"{str(v):<14}" for v in vals)
            text.insert(tk.END, line + "")

        text.insert(tk.END, sl)
        text.insert(tk.END, f"FIM DO RELATÓRIO")
        text.insert(tk.END, ln)

        text.config(state=tk.DISABLED)

        btn_frame = tk.Frame(comp, bg="white")
        btn_frame.pack(pady=10)

        for label, color, cmd in [
            ("🖨️ Imprimir (Padrão)",   ModernTheme.PRIMARY, lambda: self._imprimir_texto(text)),
            ("🖨️ Escolher Impressora", ModernTheme.INFO,    lambda: self._imprimir_dialogo(text)),
            ("💾 Salvar",              ModernTheme.SUCCESS,
             lambda: self._salvar_arquivo(text, titulo.replace(" ", "_").lower())),
        ]:
            tk.Button(btn_frame, text=label, command=cmd,
                      bg=color, fg="white", bd=0, padx=12, pady=8,
                      font=('Segoe UI', 10), cursor="hand2").pack(side=tk.LEFT, padx=4)

    def _imprimir_texto(self, text_widget):
        try:
            tmp = os.path.join(os.environ.get("TEMP", "/tmp"), "relatorio.txt")
            with open(tmp, "w", encoding="utf-8") as f:
                f.write(text_widget.get(1.0, tk.END))
            if os.name == "nt":
                os.startfile(tmp, "print")
            else:
                subprocess.run(["lp", tmp])
            messagebox.showinfo("Impressão", "Relatório enviado para impressora!")
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao imprimir: {e}")

    def _imprimir_dialogo(self, text_widget):
        try:
            tmp = os.path.join(os.environ.get("TEMP", "/tmp"), "relatorio.txt")
            with open(tmp, "w", encoding="utf-8") as f:
                f.write(text_widget.get(1.0, tk.END))
            if os.name == "nt":
                subprocess.Popen(["notepad", "/p", tmp])
            else:
                subprocess.Popen(["lpr", "-P", "lp", tmp])
            messagebox.showinfo("Impressão", "Diálogo de impressão aberto!")
        except Exception as e:
            messagebox.showerror("Erro", f"Erro: {e}")

    def _salvar_arquivo(self, text_widget, nome):
        filename = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Texto", "*.txt"), ("Todos", "*.*")],
            initialfile=f"{nome}_{datetime.now().strftime('%Y%m%d')}.txt"
        )
        if filename:
            with open(filename, "w", encoding="utf-8") as f:
                f.write(text_widget.get(1.0, tk.END))
            messagebox.showinfo("Salvo", f"Relatório salvo em: {filename}")