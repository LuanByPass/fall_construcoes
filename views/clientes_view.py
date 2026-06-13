"""Tela de Clientes - FALL Construções
ATUALIZADO: CRUD completo + busca local + estatísticas sincronizadas + detecção automática de campos
+ CORREÇÃO: Scroll touchpad + Número/Data da venda + BUG sorted(venda.keys())
"""
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from datetime import datetime
from views.base_view import BaseView
from config import ModernTheme

try:
    from utils.logger import Logger
except:
    class Logger:
        @classmethod
        def log(cls, msg, level='INFO'):
            print(f"[{level}] {msg}")


class ClientesView(BaseView):
    def __init__(self, parent, controllers):
        super().__init__(parent, None)
        self.controllers = controllers
        self.cliente_selecionado = None
        self._todos_clientes = []
        self.build()

    def build(self):
        self.frame = tk.Frame(self.parent, bg=ModernTheme.BG)

        self.notebook = ttk.Notebook(self.frame)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)

        self.tab_lista = tk.Frame(self.notebook, bg=ModernTheme.BG)
        self.notebook.add(self.tab_lista, text="📋 Todos os Clientes")
        self._build_lista_tab()

        self.tab_detalhes = tk.Frame(self.notebook, bg=ModernTheme.BG)
        self.notebook.add(self.tab_detalhes, text="👤 Detalhes")
        self._build_detalhes_tab()

    def _build_lista_tab(self):
        search_frame = tk.Frame(self.tab_lista, bg=ModernTheme.BG)
        search_frame.pack(fill=tk.X, padx=10, pady=10)

        tk.Label(search_frame, text="🔍 Buscar:", font=('Segoe UI', 11, 'bold'),
                bg=ModernTheme.BG).pack(side=tk.LEFT)
        self.busca_var = tk.StringVar()
        self.busca_entry = tk.Entry(search_frame, textvariable=self.busca_var,
                                    font=('Segoe UI', 12), width=40, bd=2, relief=tk.SOLID)
        self.busca_entry.pack(side=tk.LEFT, padx=10)
        self.busca_var.trace('w', lambda *args: self._buscar_clientes())

        tk.Button(search_frame, text="🔄 Atualizar", command=self._load_clientes,
                 bg=ModernTheme.PRIMARY, fg='white', bd=0, padx=15, pady=5,
                 font=('Segoe UI', 10, 'bold')).pack(side=tk.LEFT, padx=5)

        tk.Button(search_frame, text="➕ Novo Cliente", command=self._novo_cliente,
                 bg=ModernTheme.SUCCESS, fg='white', bd=0, padx=15, pady=5,
                 font=('Segoe UI', 10, 'bold')).pack(side=tk.RIGHT, padx=5)

        columns = ('ID', 'Nome', 'CPF/CNPJ', 'Telefone', 'Cidade', 'Compras', 'Total')
        self.clientes_tree = ttk.Treeview(self.tab_lista, columns=columns, show='headings', height=20)
        for col, w in zip(columns, [50, 200, 120, 120, 120, 80, 100]):
            self.clientes_tree.heading(col, text=col)
            self.clientes_tree.column(col, width=w)
        self.clientes_tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        self.clientes_tree.bind('<Double-1>', lambda e: self._ver_detalhes_cliente())
        self.clientes_tree.bind('<Return>', lambda e: self._ver_detalhes_cliente())

        btn_frame = tk.Frame(self.tab_lista, bg=ModernTheme.BG)
        btn_frame.pack(fill=tk.X, padx=10, pady=10)

        tk.Button(btn_frame, text="👤 Ver Detalhes", command=self._ver_detalhes_cliente,
                 bg=ModernTheme.INFO, fg='white', bd=0, padx=15, pady=8,
                 font=('Segoe UI', 10, 'bold')).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="✏️ Editar", command=self._editar_cliente,
                 bg=ModernTheme.WARNING, fg='white', bd=0, padx=15, pady=8,
                 font=('Segoe UI', 10, 'bold')).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="🗑️ Excluir", command=self._excluir_cliente,
                 bg=ModernTheme.DANGER, fg='white', bd=0, padx=15, pady=8,
                 font=('Segoe UI', 10, 'bold')).pack(side=tk.LEFT, padx=5)

        self._load_clientes()

    def _build_detalhes_tab(self):
        self.detalhes_frame = tk.Frame(self.tab_detalhes, bg=ModernTheme.BG)
        self.detalhes_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.detalhes_label = tk.Label(self.detalhes_frame, 
                                      text="Selecione um cliente na aba 'Todos os Clientes' para ver os detalhes",
                                      font=('Segoe UI', 14), bg=ModernTheme.BG, fg=ModernTheme.CIMENTO)
        self.detalhes_label.pack(expand=True)

    def _buscar_clientes(self):
        termo = self.busca_var.get().strip().lower()
        if len(termo) < 2:
            self._render_clientes(self._todos_clientes)
            return

        filtrados = []
        for c in self._todos_clientes:
            campos = [
                str(c.get('nome', '')).lower(),
                str(c.get('cpf_cnpj', '')).lower(),
                str(c.get('telefone', '')).lower(),
                str(c.get('cidade', '')).lower(),
                str(c.get('email', '')).lower(),
            ]
            if any(termo in campo for campo in campos):
                filtrados.append(c)

        self._render_clientes(filtrados)

    def _load_clientes(self):
        self._todos_clientes = self.controllers['cliente'].listar_todos() or []
        self._render_clientes(self._todos_clientes)

    def _render_clientes(self, clientes):
        for item in self.clientes_tree.get_children():
            self.clientes_tree.delete(item)
        for c in clientes:
            self._inserir_cliente_na_tree(c)

    def _inserir_cliente_na_tree(self, c):
        stats = self.controllers['cliente'].get_estatisticas(c['id'])
        self.clientes_tree.insert('', tk.END, values=(
            c['id'],
            c.get('nome', ''),
            c.get('cpf_cnpj', ''),
            c.get('telefone', ''),
            c.get('cidade', ''),
            stats.get('total_compras', 0),
            f"R$ {float(stats.get('total_gasto', 0)):.2f}"
        ))

    def _get_selected_cliente(self):
        selected = self.clientes_tree.selection()
        if not selected:
            messagebox.showwarning("Aviso", "Selecione um cliente")
            return None
        item = self.clientes_tree.item(selected[0])
        cliente_id = item['values'][0]
        return self.controllers['cliente'].obter(cliente_id)

    def _ver_detalhes_cliente(self):
        cliente = self._get_selected_cliente()
        if not cliente:
            return

        self.cliente_selecionado = cliente
        self.notebook.select(self.tab_detalhes)
        self._mostrar_detalhes(cliente)

    # ─────────────────────────────────────────────────────────────────────────
    # DETECÇÃO AUTOMÁTICA DE CAMPOS (resolve problema de nomes diferentes no backend)
    # ─────────────────────────────────────────────────────────────────────────

    def _extrair_numero_venda(self, venda):
        """Tenta extrair o número da venda de qualquer campo disponível"""
        campos_prioridade = [
            'numero_venda', 'numero', 'id', 'venda_id', 'pedido', 
            'pedido_numero', 'codigo', 'nota', 'nota_fiscal', 'seq',
            'numero_nota', 'numero_pedido', 'num_venda', 'n_venda',
            'venda_numero', 'pedido_id', 'ordem', 'ordem_id'
        ]
        for campo in campos_prioridade:
            val = venda.get(campo)
            if val is not None and str(val).strip() not in ('', 'None', 'null', '0'):
                return str(val)

        # CORREÇÃO: Usar venda.items() em vez de venda.keys()
        for k, v in sorted(venda.items()):
            k_lower = str(k).lower()
            if any(x in k_lower for x in ['num', 'nro', 'cod', 'seq', 'ped', 'nota', 'ordem']):
                if v is not None and str(v).strip() not in ('', 'None', 'null', '0'):
                    return str(v)
        return 'N/A'

    def _extrair_data_venda(self, venda):
        """Tenta extrair a data da venda de qualquer campo disponível"""
        campos_data = [
            'data_hora', 'data_venda', 'created_at', 'data', 'datetime', 
            'dt', 'data_criacao', 'timestamp', 'data_emissao', 'dt_venda',
            'data_pedido', 'dt_pedido', 'data_compra', 'dt_compra',
            'venda_data', 'pedido_data', 'data_finalizacao', 'dt_finalizacao'
        ]
        for campo in campos_data:
            val = venda.get(campo)
            if val is not None and str(val).strip() not in ('', 'None', 'null'):
                return val

        # CORREÇÃO: Usar venda.items() em vez de venda.keys()
        for k, v in sorted(venda.items()):
            k_lower = str(k).lower()
            if any(x in k_lower for x in ['data', 'date', 'time', 'dt', 'hora', 'criado', 'created']):
                if v is not None and str(v).strip() not in ('', 'None', 'null'):
                    return v
        return None

    def _parse_data(self, raw):
        """Converte qualquer formato de data para datetime ou None"""
        if not raw:
            return None
        if isinstance(raw, datetime):
            return raw

        s = str(raw).strip()
        formatos = [
            '%Y-%m-%d %H:%M:%S',
            '%Y-%m-%d %H:%M',
            '%Y-%m-%d',
            '%d/%m/%Y %H:%M:%S',
            '%d/%m/%Y %H:%M',
            '%d/%m/%Y',
            '%d-%m-%Y',
            '%Y/%m/%d %H:%M:%S',
            '%Y/%m/%d',
            '%m/%d/%Y %H:%M:%S',
            '%m/%d/%Y',
        ]
        for fmt in formatos:
            try:
                return datetime.strptime(s[:len(fmt)+10], fmt)
            except ValueError:
                continue

        # Tenta ISO format
        try:
            return datetime.fromisoformat(s.replace('Z', '+00:00').replace('T', ' '))
        except Exception:
            pass

        # Tenta detectar data em string genérica
        import re
        match = re.search(r'(\d{4}-\d{2}-\d{2})', s)
        if match:
            try:
                return datetime.strptime(match.group(1), '%Y-%m-%d')
            except ValueError:
                pass

        return None

    def _calcular_estatisticas_reais(self, compras):
        """Calcula estatísticas diretamente do histórico de compras"""
        total_compras = 0
        total_gasto = 0.0
        produtos_diferentes = set()
        ultima_compra = None

        for venda in compras:
            status = str(venda.get('status', '')).lower()
            if status == 'cancelado':
                continue

            total_compras += 1
            total_gasto += float(venda.get('total', 0) or 0)

            itens = venda.get('itens', [])
            if itens:
                for item in itens:
                    pid = item.get('produto_id')
                    if pid:
                        produtos_diferentes.add(pid)
            else:
                qtd = int(venda.get('total_itens', 0) or 0)
                if qtd > 0:
                    produtos_diferentes.add(f"venda_{venda.get('id', '')}")

            # Data da venda
            raw_data = self._extrair_data_venda(venda)
            data_dt = self._parse_data(raw_data)
            if data_dt:
                if ultima_compra is None or data_dt > ultima_compra:
                    ultima_compra = data_dt

        return {
            'total_compras': total_compras,
            'total_gasto': total_gasto,
            'produtos_diferentes': len(produtos_diferentes),
            'ultima_compra': ultima_compra.strftime('%d/%m/%Y') if ultima_compra else 'Nunca'
        }

    def _mostrar_detalhes(self, cliente):
        for widget in self.detalhes_frame.winfo_children():
            widget.destroy()

        # CORREÇÃO: Canvas com scroll universal (mouse + touchpad)
        canvas = tk.Canvas(self.detalhes_frame, bg=ModernTheme.BG)
        scrollbar = ttk.Scrollbar(self.detalhes_frame, orient="vertical", command=canvas.yview)
        scroll_frame = tk.Frame(canvas, bg=ModernTheme.BG)

        scroll_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scroll_frame, anchor="nw", width=750)
        canvas.configure(yscrollcommand=scrollbar.set)

        # CORREÇÃO: Bindings para scroll com mouse wheel e touchpad
        def _on_mousewheel(event):
            """Handler universal para scroll com mouse e touchpad"""
            if event.delta:
                canvas.yview_scroll(int(-1*(event.delta/120)), "units")
            elif event.num == 4:
                canvas.yview_scroll(-1, "units")
            elif event.num == 5:
                canvas.yview_scroll(1, "units")

        # Bindings para Windows (mouse wheel + touchpad)
        canvas.bind_all("<MouseWheel>", _on_mousewheel)
        # Bindings para Linux (scroll wheel)
        canvas.bind_all("<Button-4>", _on_mousewheel)
        canvas.bind_all("<Button-5>", _on_mousewheel)
        # Bindings para Linux touchpad (scroll horizontal convertido para vertical)
        canvas.bind_all("<Shift-MouseWheel>", _on_mousewheel)

        # Cleanup bindings quando a aba muda
        def _cleanup_bindings(event=None):
            canvas.unbind_all("<MouseWheel>")
            canvas.unbind_all("<Button-4>")
            canvas.unbind_all("<Button-5>")
            canvas.unbind_all("<Shift-MouseWheel>")

        self.notebook.bind("<<NotebookTabChanged>>", lambda e: _cleanup_bindings() if self.notebook.index(self.notebook.select()) != 1 else None)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # DADOS DO CLIENTE
        card_info = tk.Frame(scroll_frame, bg=ModernTheme.CARD_BG, bd=0,
                            highlightbackground=ModernTheme.BORDER, highlightthickness=1)
        card_info.pack(fill=tk.X, padx=10, pady=10)

        tk.Label(card_info, text=f"👤 {cliente.get('nome', 'Cliente')}", 
                font=('Segoe UI', 18, 'bold'), bg=ModernTheme.CARD_BG, fg=ModernTheme.PRIMARY).pack(anchor=tk.W, padx=15, pady=(10, 5))

        info_grid = tk.Frame(card_info, bg=ModernTheme.CARD_BG)
        info_grid.pack(fill=tk.X, padx=15, pady=5)

        campos = [
            ("CPF/CNPJ:", cliente.get('cpf_cnpj', 'N/A')),
            ("Telefone:", cliente.get('telefone', 'N/A')),
            ("Email:", cliente.get('email', 'N/A')),
            ("Endereço:", f"{cliente.get('endereco', '')}, {cliente.get('cidade', '')} - {cliente.get('estado', '')}"),
            ("CEP:", cliente.get('cep', 'N/A')),
        ]

        for label, valor in campos:
            row = tk.Frame(info_grid, bg=ModernTheme.CARD_BG)
            row.pack(fill=tk.X, pady=2)
            tk.Label(row, text=label, font=('Segoe UI', 10, 'bold'), 
                    bg=ModernTheme.CARD_BG, fg=ModernTheme.DARK, width=12, anchor='w').pack(side=tk.LEFT)
            tk.Label(row, text=valor, font=('Segoe UI', 10), 
                    bg=ModernTheme.CARD_BG, fg=ModernTheme.TEXT).pack(side=tk.LEFT, padx=5)

        # HISTÓRICO DE COMPRAS
        compras = self.controllers['cliente'].get_compras(cliente['id']) or []

        # ESTATÍSTICAS CALCULADAS A PARTIR DO HISTÓRICO REAL
        stats = self._calcular_estatisticas_reais(compras)

        card_stats = tk.Frame(scroll_frame, bg=ModernTheme.CARD_BG, bd=0,
                             highlightbackground=ModernTheme.BORDER, highlightthickness=1)
        card_stats.pack(fill=tk.X, padx=10, pady=10)

        tk.Label(card_stats, text="📊 Estatísticas", 
                font=('Segoe UI', 14, 'bold'), bg=ModernTheme.CARD_BG, fg=ModernTheme.PRIMARY).pack(anchor=tk.W, padx=15, pady=(10, 5))

        stats_grid = tk.Frame(card_stats, bg=ModernTheme.CARD_BG)
        stats_grid.pack(fill=tk.X, padx=15, pady=10)

        stat_cards = [
            ("🛒 Total de Compras", str(stats['total_compras']), ModernTheme.PRIMARY),
            ("💰 Total Gasto", f"R$ {float(stats['total_gasto']):.2f}", ModernTheme.SUCCESS),
            ("📦 Produtos Diferentes", str(stats['produtos_diferentes']), ModernTheme.INFO),
            ("⭐ Última Compra", stats['ultima_compra'], ModernTheme.WARNING),
        ]

        for titulo, valor, cor in stat_cards:
            card = tk.Frame(stats_grid, bg=cor, padx=15, pady=10)
            card.pack(side=tk.LEFT, expand=True, fill=tk.BOTH, padx=5)
            tk.Label(card, text=titulo, font=('Segoe UI', 9), bg=cor, fg='white').pack()
            tk.Label(card, text=valor, font=('Segoe UI', 16, 'bold'), bg=cor, fg='white').pack()

        # HISTÓRICO DE COMPRAS
        card_compras = tk.Frame(scroll_frame, bg=ModernTheme.CARD_BG, bd=0,
                               highlightbackground=ModernTheme.BORDER, highlightthickness=1)
        card_compras.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        tk.Label(card_compras, text="🛍️ Histórico de Compras", 
                font=('Segoe UI', 14, 'bold'), bg=ModernTheme.CARD_BG, fg=ModernTheme.PRIMARY).pack(anchor=tk.W, padx=15, pady=(10, 5))

        columns = ('Nº Venda', 'Data', 'Itens', 'Total', 'Pagamento', 'Status')
        compras_tree = ttk.Treeview(card_compras, columns=columns, show='headings', height=12)
        for col, w in zip(columns, [100, 120, 50, 100, 120, 100]):
            compras_tree.heading(col, text=col)
            compras_tree.column(col, width=w)
        compras_tree.pack(fill=tk.BOTH, expand=True, padx=15, pady=10)

        compras_tree.tag_configure('pago', foreground=ModernTheme.SUCCESS)
        compras_tree.tag_configure('pendente', foreground=ModernTheme.WARNING)
        compras_tree.tag_configure('cancelado', foreground=ModernTheme.DANGER)

        for venda in compras:
            # ✅ NÚMERO: detecção automática de qualquer campo disponível
            numero_venda = self._extrair_numero_venda(venda)

            # ✅ DATA: detecção automática de qualquer campo disponível
            raw_data = self._extrair_data_venda(venda)
            data_dt = self._parse_data(raw_data)
            if data_dt:
                data_venda = data_dt.strftime('%d/%m/%Y')
            else:
                data_venda = str(raw_data)[:10] if raw_data else 'N/A'

            status = str(venda.get('status', 'N/A')).lower()
            tag = status if status in ('pago', 'pendente', 'cancelado') else ''

            compras_tree.insert('', tk.END, tags=(tag,), values=(
                numero_venda,
                data_venda,
                venda.get('total_itens', 0),
                f"R$ {float(venda.get('total', 0) or 0):.2f}",
                venda.get('forma_pagamento', 'N/A'),
                venda.get('status', 'N/A').upper()
            ))

        # Botão voltar
        tk.Button(scroll_frame, text="⬅️ Voltar para Lista", 
                 command=lambda: self.notebook.select(self.tab_lista),
                 bg=ModernTheme.PRIMARY, fg='white', bd=0, padx=20, pady=10,
                 font=('Segoe UI', 10, 'bold')).pack(pady=15)

    def _editar_cliente(self):
        cliente = self._get_selected_cliente()
        if not cliente:
            return

        dialog = tk.Toplevel(self.parent)
        dialog.title(f"✏️ Editar Cliente - {cliente.get('nome', '')}")
        dialog.geometry("500x550")
        dialog.configure(bg=ModernTheme.BG)
        dialog.transient(self.parent)
        dialog.grab_set()

        tk.Label(dialog, text="✏️ Editar Cliente", 
                font=('Segoe UI', 16, 'bold'), bg=ModernTheme.BG, fg=ModernTheme.PRIMARY).pack(pady=15)

        campos = [
            ("Nome:", "nome", cliente.get('nome', '')),
            ("CPF/CNPJ:", "cpf_cnpj", cliente.get('cpf_cnpj', '')),
            ("Telefone:", "telefone", cliente.get('telefone', '')),
            ("Email:", "email", cliente.get('email', '')),
            ("Endereço:", "endereco", cliente.get('endereco', '')),
            ("Cidade:", "cidade", cliente.get('cidade', '')),
            ("Estado:", "estado", cliente.get('estado', '')),
            ("CEP:", "cep", cliente.get('cep', '')),
        ]

        entries = {}
        for label, key, valor in campos:
            row = tk.Frame(dialog, bg=ModernTheme.BG)
            row.pack(fill=tk.X, padx=20, pady=5)
            tk.Label(row, text=label, font=('Segoe UI', 11, 'bold'), 
                    bg=ModernTheme.BG, width=12, anchor='w').pack(side=tk.LEFT)
            entry = tk.Entry(row, font=('Segoe UI', 11), width=35)
            entry.insert(0, str(valor) if valor else '')
            entry.pack(side=tk.LEFT, padx=5)
            entries[key] = entry

        def salvar():
            dados = {k: e.get().strip() for k, e in entries.items()}
            if not dados['nome']:
                messagebox.showwarning("Aviso", "Nome é obrigatório")
                return

            success, msg = self.controllers['cliente'].atualizar(cliente['id'], dados)
            if success:
                messagebox.showinfo("Sucesso", msg)
                self._load_clientes()
                dialog.destroy()
            else:
                messagebox.showerror("Erro", msg)

        tk.Button(dialog, text="💾 Salvar Alterações", command=salvar,
                 bg=ModernTheme.SUCCESS, fg='white', bd=0, padx=20, pady=10,
                 font=('Segoe UI', 12, 'bold')).pack(pady=20)

    def _novo_cliente(self):
        dialog = tk.Toplevel(self.parent)
        dialog.title("➕ Novo Cliente")
        dialog.geometry("500x500")
        dialog.configure(bg=ModernTheme.BG)
        dialog.transient(self.parent)
        dialog.grab_set()

        campos = [
            ("Nome:", "nome", ""),
            ("CPF/CNPJ:", "cpf_cnpj", ""),
            ("Telefone:", "telefone", ""),
            ("Email:", "email", ""),
            ("Endereço:", "endereco", ""),
            ("Cidade:", "cidade", ""),
            ("Estado:", "estado", ""),
            ("CEP:", "cep", ""),
        ]

        entries = {}
        for label, key, default in campos:
            row = tk.Frame(dialog, bg=ModernTheme.BG)
            row.pack(fill=tk.X, padx=20, pady=5)
            tk.Label(row, text=label, font=('Segoe UI', 11, 'bold'), 
                    bg=ModernTheme.BG, width=12, anchor='w').pack(side=tk.LEFT)
            entry = tk.Entry(row, font=('Segoe UI', 11), width=35)
            entry.insert(0, default)
            entry.pack(side=tk.LEFT, padx=5)
            entries[key] = entry

        def salvar():
            dados = {k: e.get().strip() for k, e in entries.items()}
            if not dados['nome']:
                messagebox.showwarning("Aviso", "Nome é obrigatório")
                return
            success, msg = self.controllers['cliente'].criar(dados)
            if success:
                messagebox.showinfo("Sucesso", msg)
                self._load_clientes()
                dialog.destroy()
            else:
                messagebox.showerror("Erro", msg)

        tk.Button(dialog, text="💾 Salvar", command=salvar,
                 bg=ModernTheme.SUCCESS, fg='white', bd=0, padx=20, pady=10,
                 font=('Segoe UI', 12, 'bold')).pack(pady=20)

    def _excluir_cliente(self):
        cliente = self._get_selected_cliente()
        if not cliente:
            return

        confirm = messagebox.askyesno(
            "⚠️ Confirmar Exclusão",
            f"Deseja excluir o cliente '{cliente.get('nome')}'?"
            "⚠️ Isso também removerá todas as vendas e orçamentos vinculados!",
            icon='warning'
        )
        if not confirm:
            return

        success, msg = self.controllers['cliente'].deletar(cliente['id'])
        if success:
            messagebox.showinfo("Sucesso", msg)
            self._load_clientes()
        else:
            messagebox.showerror("Erro", msg)

    def refresh(self):
        self._load_clientes()