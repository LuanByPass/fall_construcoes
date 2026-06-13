"""
Tela de Entregas/Frete - FALL Construcoes
VERSAO COM SCROLLBAR VERTICAL na aba "Nova Entrega"
"""
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime, timedelta
from views import BaseView
from config import ModernTheme, LOJA_CONFIG
import subprocess
import os
import sys
import importlib.util

try:
    from utils.logger import Logger
except Exception:
    class Logger:
        @classmethod
        def log(cls, msg, level="INFO"):
            print("[" + level + "] " + msg)


def _carregar_gerador_pdf():
    views_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(views_dir)
    candidatos = [
        os.path.join(project_root, "geradores", "ordem_entrega.py"),
        os.path.join(views_dir, "ordem_entrega.py"),
        os.path.join(views_dir, "geradores", "ordem_entrega.py"),
        os.path.join(os.path.dirname(project_root), "geradores", "ordem_entrega.py"),
    ]
    for caminho in candidatos:
        if os.path.exists(caminho):
            try:
                spec = importlib.util.spec_from_file_location("ordem_entrega", caminho)
                mod = importlib.util.module_from_spec(spec)
                sys.modules["ordem_entrega"] = mod
                spec.loader.exec_module(mod)
                return mod.OrdemEntregaGenerator
            except Exception:
                continue
    raise ImportError(
        "Nao foi possivel encontrar 'ordem_entrega.py'.\n"
        "Procurado em:\n" + "\n".join("  - " + c for c in candidatos) + "\n\n"
        "Crie a pasta 'geradores/' na raiz do projeto e coloque o arquivo la."
    )


class EntregaView(BaseView):
    def __init__(self, parent, controllers):
        super().__init__(parent, None)
        self.controllers = controllers
        self.build()

    def build(self):
        self.frame = tk.Frame(self.parent, bg=ModernTheme.BG)
        self.notebook = ttk.Notebook(self.frame)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=16, pady=12)

        self.tab_novo = tk.Frame(self.notebook, bg=ModernTheme.BG)
        self.notebook.add(self.tab_novo, text="+  Nova Entrega")

        self.tab_lista = tk.Frame(self.notebook, bg=ModernTheme.BG)
        self.notebook.add(self.tab_lista, text="  Entregas Agendadas")

        self._build_novo_tab()
        self._build_lista_tab()
        self.notebook.bind("<<NotebookTabChanged>>", self._on_tab_changed)

    def _on_tab_changed(self, event=None):
        try:
            aba_atual = self.notebook.index(self.notebook.select())
            if aba_atual == 0:
                self._recarregar_vendas()
            elif aba_atual == 1:
                self._load_entregas()
        except Exception as e:
            Logger.log("Erro ao trocar aba: " + str(e), "WARNING")

    def _build_novo_tab(self):
        container = tk.Frame(self.tab_novo, bg=ModernTheme.BG)
        container.pack(fill=tk.BOTH, expand=True)

        canvas_scroll = tk.Canvas(container, bg=ModernTheme.BG, highlightthickness=0)
        canvas_scroll.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scrollbar = ttk.Scrollbar(container, orient=tk.VERTICAL, command=canvas_scroll.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        canvas_scroll.configure(yscrollcommand=scrollbar.set)

        main = tk.Frame(canvas_scroll, bg=ModernTheme.BG)
        canvas_scroll.create_window((0, 0), window=main, anchor=tk.NW)

        def _on_frame_configure(event=None):
            canvas_scroll.configure(scrollregion=canvas_scroll.bbox("all"))

        main.bind("<Configure>", _on_frame_configure)

        def _on_canvas_configure(event):
            canvas_scroll.itemconfig(canvas_scroll.find_withtag("all")[0], width=event.width)

        canvas_scroll.bind("<Configure>", _on_canvas_configure)

        def _on_mousewheel(event):
            canvas_scroll.yview_scroll(int(-1 * (event.delta / 120)), "units")

        canvas_scroll.bind_all("<MouseWheel>", _on_mousewheel)
        canvas_scroll.bind_all("<Button-4>", lambda e: canvas_scroll.yview_scroll(-1, "units"))
        canvas_scroll.bind_all("<Button-5>", lambda e: canvas_scroll.yview_scroll(1, "units"))

        # CARD 1: Selecao da Venda
        card_venda = tk.Frame(main, bg=ModernTheme.CARD_BG,
                              highlightbackground=ModernTheme.SECONDARY,
                              highlightthickness=2)
        card_venda.pack(fill=tk.X, pady=(0, 10), padx=12)

        header_venda = tk.Frame(card_venda, bg=ModernTheme.SECONDARY, height=36)
        header_venda.pack(fill=tk.X)
        header_venda.pack_propagate(False)
        tk.Label(header_venda, text="  SELECIONAR VENDA",
                 font=("Segoe UI", 10, "bold"),
                 bg=ModernTheme.SECONDARY, fg="white").pack(side=tk.LEFT, padx=12, pady=8)

        btn_atualizar_vendas = tk.Button(
            header_venda, text="  Atualizar",
            command=self._recarregar_vendas,
            bg=ModernTheme.INFO, fg="white",
            font=("Segoe UI", 8, "bold"),
            bd=0, padx=10, pady=4, cursor="hand2",
            activebackground="#1e40af"
        )
        btn_atualizar_vendas.pack(side=tk.RIGHT, padx=8, pady=6)
        btn_atualizar_vendas.bind("<Enter>", lambda e: btn_atualizar_vendas.config(bg="#1e40af"))
        btn_atualizar_vendas.bind("<Leave>", lambda e: btn_atualizar_vendas.config(bg=ModernTheme.INFO))

        body_venda = tk.Frame(card_venda, bg=ModernTheme.CARD_BG, padx=14, pady=12)
        body_venda.pack(fill=tk.X)

        self.venda_var = tk.StringVar()
        self._vendas_lista = []
        self._vendas_dict = {}

        tk.Label(body_venda, text="Venda finalizada:",
                 font=("Segoe UI", 9, "bold"),
                 bg=ModernTheme.CARD_BG, fg=ModernTheme.TEXT_MUTED).pack(anchor=tk.W)

        self.venda_combo = ttk.Combobox(
            body_venda, textvariable=self.venda_var,
            values=[],
            state="readonly", font=("Segoe UI", 10), width=55
        )
        self.venda_combo.pack(fill=tk.X, pady=(4, 8))
        self.venda_combo.bind("<<ComboboxSelected>>", self._on_venda_selecionada)

        self.cliente_venda_label = tk.Label(
            body_venda,
            text="  Cliente: Nenhuma venda selecionada",
            font=("Segoe UI", 10, "bold"),
            bg=ModernTheme.CARD_BG, fg=ModernTheme.TEXT_MUTED
        )
        self.cliente_venda_label.pack(anchor=tk.W)

        self._recarregar_vendas()

        # CARD 2: Itens da Venda
        card_itens = tk.Frame(main, bg=ModernTheme.CARD_BG,
                              highlightbackground=ModernTheme.BORDER,
                              highlightthickness=1)
        card_itens.pack(fill=tk.X, pady=(0, 10), padx=12)

        header_itens = tk.Frame(card_itens, bg=ModernTheme.SECONDARY, height=32)
        header_itens.pack(fill=tk.X)
        tk.Label(header_itens, text="  ITENS DA VENDA",
                 font=("Segoe UI", 9, "bold"),
                 bg=ModernTheme.SECONDARY, fg="white").pack(side=tk.LEFT, padx=12, pady=6)

        body_itens = tk.Frame(card_itens, bg=ModernTheme.CARD_BG, padx=12, pady=8)
        body_itens.pack(fill=tk.X)

        cols_itens = ("Codigo", "Produto", "Qtd", "Preco Unit.", "Subtotal")
        self.itens_venda_tree = ttk.Treeview(
            body_itens, columns=cols_itens,
            show="headings", height=5
        )
        for col, w in zip(cols_itens, [90, 280, 50, 90, 90]):
            self.itens_venda_tree.heading(col, text=col)
            self.itens_venda_tree.column(
                col, width=w,
                anchor=tk.CENTER if col in ("Qtd", "Preco Unit.", "Subtotal") else tk.W
            )
        self.itens_venda_tree.pack(fill=tk.X)
        self.itens_venda_tree.tag_configure("even", background="#f8fafc")
        self.itens_venda_tree.tag_configure("odd", background="white")

        # CARD 3: Endereco de Entrega
        card_endereco = tk.Frame(main, bg=ModernTheme.CARD_BG,
                                 highlightbackground=ModernTheme.BORDER,
                                 highlightthickness=1)
        card_endereco.pack(fill=tk.X, pady=(0, 10), padx=12)

        header_end = tk.Frame(card_endereco, bg=ModernTheme.SECONDARY, height=32)
        header_end.pack(fill=tk.X)
        tk.Label(header_end, text="  ENDERECO DE ENTREGA",
                 font=("Segoe UI", 9, "bold"),
                 bg=ModernTheme.SECONDARY, fg="white").pack(side=tk.LEFT, padx=12, pady=6)

        body_end = tk.Frame(card_endereco, bg=ModernTheme.CARD_BG, padx=14, pady=12)
        body_end.pack(fill=tk.X)

        tk.Label(body_end, text="Logradouro / Endereco Completo",
                 font=("Segoe UI", 9, "bold"),
                 bg=ModernTheme.CARD_BG, fg=ModernTheme.TEXT_MUTED).pack(anchor=tk.W)
        self.endereco_entry = self.styled_entry(body_end, width=60)
        self.endereco_entry.pack(fill=tk.X, pady=(4, 10))

        row_end = tk.Frame(body_end, bg=ModernTheme.CARD_BG)
        row_end.pack(fill=tk.X)

        col_cid = tk.Frame(row_end, bg=ModernTheme.CARD_BG)
        col_cid.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 8))
        tk.Label(col_cid, text="Cidade",
                 font=("Segoe UI", 9, "bold"),
                 bg=ModernTheme.CARD_BG, fg=ModernTheme.TEXT_MUTED).pack(anchor=tk.W)
        self.cidade_entry = self.styled_entry(col_cid, width=20)
        self.cidade_entry.pack(fill=tk.X, pady=(4, 0))

        col_est = tk.Frame(row_end, bg=ModernTheme.CARD_BG)
        col_est.pack(side=tk.LEFT, padx=(0, 8))
        tk.Label(col_est, text="UF",
                 font=("Segoe UI", 9, "bold"),
                 bg=ModernTheme.CARD_BG, fg=ModernTheme.TEXT_MUTED).pack(anchor=tk.W)
        self.estado_entry = self.styled_entry(col_est, width=6)
        self.estado_entry.pack(pady=(4, 0))

        col_cep = tk.Frame(row_end, bg=ModernTheme.CARD_BG)
        col_cep.pack(side=tk.LEFT)
        tk.Label(col_cep, text="CEP",
                 font=("Segoe UI", 9, "bold"),
                 bg=ModernTheme.CARD_BG, fg=ModernTheme.TEXT_MUTED).pack(anchor=tk.W)
        self.cep_entry = self.styled_entry(col_cep, width=12)
        self.cep_entry.pack(pady=(4, 0))

        # CARD 4: Detalhes da Entrega
        card_detalhes = tk.Frame(main, bg=ModernTheme.CARD_BG,
                                 highlightbackground=ModernTheme.BORDER,
                                 highlightthickness=1)
        card_detalhes.pack(fill=tk.X, pady=(0, 10), padx=12)

        header_det = tk.Frame(card_detalhes, bg=ModernTheme.SECONDARY, height=32)
        header_det.pack(fill=tk.X)
        tk.Label(header_det, text="  DETALHES DA ENTREGA",
                 font=("Segoe UI", 9, "bold"),
                 bg=ModernTheme.SECONDARY, fg="white").pack(side=tk.LEFT, padx=12, pady=6)

        body_det = tk.Frame(card_detalhes, bg=ModernTheme.CARD_BG, padx=14, pady=12)
        body_det.pack(fill=tk.X)

        row1 = tk.Frame(body_det, bg=ModernTheme.CARD_BG)
        row1.pack(fill=tk.X, pady=(0, 8))

        col_data = tk.Frame(row1, bg=ModernTheme.CARD_BG)
        col_data.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 8))
        tk.Label(col_data, text="Data Agendada",
                 font=("Segoe UI", 9, "bold"),
                 bg=ModernTheme.CARD_BG, fg=ModernTheme.TEXT_MUTED).pack(anchor=tk.W)
        self.data_entry = self.styled_entry(col_data, width=12)
        self.data_entry.insert(0, (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d"))
        self.data_entry.pack(fill=tk.X, pady=(4, 0))

        col_hora = tk.Frame(row1, bg=ModernTheme.CARD_BG)
        col_hora.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 8))
        tk.Label(col_hora, text="Hora",
                 font=("Segoe UI", 9, "bold"),
                 bg=ModernTheme.CARD_BG, fg=ModernTheme.TEXT_MUTED).pack(anchor=tk.W)
        self.hora_entry = self.styled_entry(col_hora, width=8)
        self.hora_entry.insert(0, "08:00")
        self.hora_entry.pack(fill=tk.X, pady=(4, 0))

        col_veic = tk.Frame(row1, bg=ModernTheme.CARD_BG)
        col_veic.pack(side=tk.LEFT, fill=tk.X, expand=True)
        tk.Label(col_veic, text="Veiculo",
                 font=("Segoe UI", 9, "bold"),
                 bg=ModernTheme.CARD_BG, fg=ModernTheme.TEXT_MUTED).pack(anchor=tk.W)
        self.veiculo_var = tk.StringVar(value="Caminhonete")
        ttk.Combobox(col_veic, textvariable=self.veiculo_var,
                     values=["Moto", "Carro", "Caminhonete", "Caminhao", "Carreta"],
                     state="readonly", width=14,
                     font=("Segoe UI", 9)).pack(fill=tk.X, pady=(4, 0))

        row2 = tk.Frame(body_det, bg=ModernTheme.CARD_BG)
        row2.pack(fill=tk.X, pady=(0, 8))

        col_mot = tk.Frame(row2, bg=ModernTheme.CARD_BG)
        col_mot.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 8))
        tk.Label(col_mot, text="Motorista",
                 font=("Segoe UI", 9, "bold"),
                 bg=ModernTheme.CARD_BG, fg=ModernTheme.TEXT_MUTED).pack(anchor=tk.W)
        self.motorista_entry = self.styled_entry(col_mot, width=30)
        self.motorista_entry.pack(fill=tk.X, pady=(4, 0))

        col_placa = tk.Frame(row2, bg=ModernTheme.CARD_BG)
        col_placa.pack(side=tk.LEFT, fill=tk.X, expand=True)
        tk.Label(col_placa, text="Placa do Veiculo",
                 font=("Segoe UI", 9, "bold"),
                 bg=ModernTheme.CARD_BG, fg=ModernTheme.TEXT_MUTED).pack(anchor=tk.W)
        self.placa_entry = self.styled_entry(col_placa, width=12)
        self.placa_entry.pack(fill=tk.X, pady=(4, 0))

        row3 = tk.Frame(body_det, bg=ModernTheme.CARD_BG)
        row3.pack(fill=tk.X)

        col_frete = tk.Frame(row3, bg=ModernTheme.CARD_BG)
        col_frete.pack(side=tk.LEFT)
        tk.Label(col_frete, text="Valor do Frete (R$)",
                 font=("Segoe UI", 9, "bold"),
                 bg=ModernTheme.CARD_BG, fg=ModernTheme.TEXT_MUTED).pack(anchor=tk.W)
        self.frete_entry = self.styled_entry(col_frete, width=12)
        self.frete_entry.insert(0, "0.00")
        self.frete_entry.pack(pady=(4, 0))

        # CARD 5: Observacoes + Botao
        card_obs = tk.Frame(main, bg=ModernTheme.CARD_BG,
                            highlightbackground=ModernTheme.BORDER,
                            highlightthickness=1)
        card_obs.pack(fill=tk.X, pady=(0, 10), padx=12)

        body_obs = tk.Frame(card_obs, bg=ModernTheme.CARD_BG, padx=14, pady=10)
        body_obs.pack(fill=tk.X)

        tk.Label(body_obs, text="  Observacoes",
                 font=("Segoe UI", 9, "bold"),
                 bg=ModernTheme.CARD_BG, fg=ModernTheme.TEXT_MUTED).pack(anchor=tk.W)
        self.obs_entry = self.styled_entry(body_obs, width=60)
        self.obs_entry.pack(fill=tk.X, pady=(4, 0))

        # BOTAO AGENDAR
        btn_agendar = tk.Button(
            main, text="  AGENDAR ENTREGA",
            command=self._agendar,
            bg=ModernTheme.SUCCESS, fg="white",
            font=("Segoe UI", 12, "bold"),
            bd=0, relief=tk.FLAT, pady=12, cursor="hand2",
            activebackground="#15803d",
            activeforeground="white"
        )
        btn_agendar.pack(fill=tk.X, pady=(4, 12), padx=12)
        btn_agendar.bind("<Enter>", lambda e: btn_agendar.config(bg="#15803d"))
        btn_agendar.bind("<Leave>", lambda e: btn_agendar.config(bg=ModernTheme.PRIMARY_HOVER))

    def _recarregar_vendas(self):
        try:
            self._vendas_lista = self.controllers["venda"].listar_vendas(status="pago") or []
            vendas = self._vendas_lista

            valores = []
            for v in vendas:
                numero = v.get("numero_venda", "")
                cliente = v.get("cliente_nome", "Avulso")
                total = float(v.get("total", 0))
                valores.append(str(numero) + " | " + str(cliente) + " | R$ " + "{:.2f}".format(total))

            self.venda_combo["values"] = valores

            self._vendas_dict = {}
            for idx, v in enumerate(vendas):
                key = str(v.get("numero_venda", ""))
                self._vendas_dict[key] = v
                self._vendas_dict["idx_" + str(idx)] = v

            if not vendas:
                self.cliente_venda_label.config(
                    text="  Nenhuma venda finalizada disponivel",
                    fg=ModernTheme.DANGER
                )
            else:
                self.cliente_venda_label.config(
                    text="  Cliente: Nenhuma venda selecionada",
                    fg=ModernTheme.TEXT_MUTED
                )

            Logger.log("Vendas recarregadas: " + str(len(vendas)) + " vendas finalizadas", "INFO")

        except Exception as e:
            Logger.log("Erro ao recarregar vendas: " + str(e), "ERROR")
            self.cliente_venda_label.config(
                text="  Erro ao carregar vendas: " + str(e),
                fg=ModernTheme.DANGER
            )

    def _build_lista_tab(self):
        stats_frame = tk.Frame(self.tab_lista, bg=ModernTheme.BG)
        stats_frame.pack(fill=tk.X, padx=12, pady=(0, 8))

        self.stats_labels = {}
        stats_config = [
            ("total",     "  Total",       ModernTheme.PRIMARY,  "#1e40af"),
            ("agendada",  "  Agendadas",   ModernTheme.INFO,     "#1e40af"),
            ("transito",  "  Em Transito", ModernTheme.WARNING,  "#b45309"),
            ("entregue",  "  Entregues",    ModernTheme.SUCCESS,  "#15803d"),
        ]
        for key, label, color, hover in stats_config:
            card = tk.Frame(stats_frame, bg=ModernTheme.CARD_BG,
                            highlightbackground=color,
                            highlightthickness=2)
            card.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=4)

            tk.Frame(card, bg=color, height=4).pack(fill=tk.X)
            inner = tk.Frame(card, bg=ModernTheme.CARD_BG, padx=14, pady=10)
            inner.pack(fill=tk.X)

            tk.Label(inner, text=label,
                     font=("Segoe UI", 9, "bold"),
                     bg=ModernTheme.CARD_BG, fg=color).pack(anchor=tk.W)
            self.stats_labels[key] = tk.Label(inner, text="0",
                     font=("Segoe UI", 16, "bold"),
                     bg=ModernTheme.CARD_BG, fg=ModernTheme.TEXT)
            self.stats_labels[key].pack(anchor=tk.W)

        filter_card = tk.Frame(self.tab_lista, bg=ModernTheme.CARD_BG,
                               highlightbackground=ModernTheme.BORDER,
                               highlightthickness=1)
        filter_card.pack(fill=tk.X, padx=12, pady=8)
        tk.Frame(filter_card, bg=ModernTheme.PRIMARY, height=3).pack(fill=tk.X)

        inner = tk.Frame(filter_card, bg=ModernTheme.CARD_BG, padx=14, pady=10)
        inner.pack(fill=tk.X)

        tk.Label(inner, text="FILTRO:",
                 font=("Segoe UI", 9, "bold"),
                 bg=ModernTheme.CARD_BG, fg=ModernTheme.TEXT_MUTED).pack(side=tk.LEFT, padx=8)

        self.status_entrega_var = tk.StringVar(value="todos")
        for val, label, color in [
            ("todos",       "Todas",       ModernTheme.TEXT),
            ("agendada",    "  Agendadas", ModernTheme.INFO),
            ("em_transito", "  Transito",  ModernTheme.WARNING),
            ("entregue",    "  Entregues", ModernTheme.SUCCESS),
        ]:
            rb = tk.Radiobutton(inner, text=label,
                                variable=self.status_entrega_var, value=val,
                                bg=ModernTheme.CARD_BG, fg=color,
                                font=("Segoe UI", 9, "bold"),
                                selectcolor=ModernTheme.CARD_BG,
                                activebackground=ModernTheme.CARD_BG,
                                command=self._load_entregas)
            rb.pack(side=tk.LEFT, padx=6)

        btn_atualizar = tk.Button(inner, text="  Atualizar", command=self._load_entregas,
                                  bg=ModernTheme.INFO, fg="white",
                                  font=("Segoe UI", 9, "bold"),
                                  bd=0, padx=16, pady=6, cursor="hand2",
                                  activebackground="#1e40af")
        btn_atualizar.pack(side=tk.RIGHT)
        btn_atualizar.bind("<Enter>", lambda e: btn_atualizar.config(bg="#1e40af"))
        btn_atualizar.bind("<Leave>", lambda e: btn_atualizar.config(bg=ModernTheme.INFO))

        table_card = tk.Frame(self.tab_lista, bg=ModernTheme.CARD_BG,
                              highlightbackground=ModernTheme.BORDER,
                              highlightthickness=1)
        table_card.pack(fill=tk.BOTH, expand=True, padx=12, pady=8)

        table_header = tk.Frame(table_card, bg=ModernTheme.PRIMARY, height=36)
        table_header.pack(fill=tk.X)
        tk.Label(table_header, text="  ENTREGAS AGENDADAS",
                 font=("Segoe UI", 10, "bold"),
                 bg=ModernTheme.PRIMARY, fg="white").pack(
            side=tk.LEFT, padx=14, pady=6)

        self.contador_label = tk.Label(table_header, text="0 entregas",
                 font=("Segoe UI", 9),
                 bg=ModernTheme.PRIMARY, fg="white")
        self.contador_label.pack(side=tk.RIGHT, padx=14, pady=6)

        table_body = tk.Frame(table_card, bg=ModernTheme.CARD_BG)
        table_body.pack(fill=tk.BOTH, expand=True, padx=12, pady=12)

        columns = ("ID", "Cliente", "Endereco", "Data", "Veiculo", "Frete", "Status")
        self.entregas_tree = ttk.Treeview(table_body, columns=columns,
                                          show="headings", height=14)
        for col, w in zip(columns, [50, 150, 220, 100, 90, 80, 100]):
            self.entregas_tree.heading(col, text=col)
            self.entregas_tree.column(col, width=w)

        self.entregas_tree.tag_configure("agendada",    foreground=ModernTheme.INFO)
        self.entregas_tree.tag_configure("em_transito", foreground=ModernTheme.WARNING)
        self.entregas_tree.tag_configure("entregue",    foreground=ModernTheme.SUCCESS)
        self.entregas_tree.tag_configure("cancelada",   foreground=ModernTheme.DANGER)
        self.entregas_tree.tag_configure("even",        background="#f8fafc")
        self.entregas_tree.tag_configure("odd",         background="white")

        sb = ttk.Scrollbar(table_body, orient=tk.VERTICAL, command=self.entregas_tree.yview)
        self.entregas_tree.configure(yscrollcommand=sb.set)
        self.entregas_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb.pack(side=tk.RIGHT, fill=tk.Y)

        action_card = tk.Frame(self.tab_lista, bg=ModernTheme.CARD_BG,
                               highlightbackground=ModernTheme.BORDER,
                               highlightthickness=1)
        action_card.pack(fill=tk.X, padx=12, pady=8)
        tk.Frame(action_card, bg=ModernTheme.SUCCESS, height=3).pack(fill=tk.X)

        action_inner = tk.Frame(action_card, bg=ModernTheme.CARD_BG, padx=12, pady=10)
        action_inner.pack(fill=tk.X)

        tk.Label(action_inner, text="ACAO DA ENTREGA SELECIONADA",
                 font=("Segoe UI", 9, "bold"),
                 bg=ModernTheme.CARD_BG, fg=ModernTheme.TEXT_MUTED).pack(
            side=tk.LEFT, padx=12)

        for label, st, color, hover in [
            ("  Em Transito", "em_transito", ModernTheme.WARNING, "#b45309"),
            ("  Entregue",    "entregue",    ModernTheme.SUCCESS, "#15803d"),
            ("  Cancelar",    "cancelada",   ModernTheme.DANGER,  "#b91c1c"),
        ]:
            btn = tk.Button(action_inner, text=label,
                            command=lambda s=st: self._mudar_status(s),
                            bg=color, fg="white",
                            font=("Segoe UI", 9, "bold"),
                            bd=0, padx=12, pady=6, cursor="hand2",
                            activebackground=hover)
            btn.pack(side=tk.LEFT, padx=3)
            btn.bind("<Enter>", lambda e, c=hover: btn.config(bg=c))
            btn.bind("<Leave>", lambda e, c=color: btn.config(bg=c))

        tk.Button(action_inner, text="  Imprimir", command=self._imprimir_ordem,
                  bg=ModernTheme.INFO, fg="white",
                  font=("Segoe UI", 9, "bold"),
                  bd=0, padx=12, pady=6, cursor="hand2",
                  activebackground="#1e40af").pack(side=tk.LEFT, padx=3)

        tk.Button(action_inner, text="  Reimprimir", command=self._reimprimir_ordem,
                  bg=ModernTheme.SECONDARY, fg="white",
                  font=("Segoe UI", 9, "bold"),
                  bd=0, padx=12, pady=6, cursor="hand2",
                  activebackground="#475569").pack(side=tk.LEFT, padx=3)

        self._load_entregas()

    def _on_venda_selecionada(self, event=None):
        venda_str = self.venda_var.get()
        if not venda_str:
            return

        try:
            idx = self.venda_combo.current()
            venda = None
            if idx >= 0 and idx < len(self._vendas_lista):
                venda = self._vendas_lista[idx]

            if not venda:
                numero_venda = venda_str.split(" | ")[0].strip()
                for v in self._vendas_dict.values():
                    if str(v.get("numero_venda")) == numero_venda:
                        venda = v
                        break

            if not venda:
                return

            venda_completa = self.controllers["venda"].obter_venda(venda["id"])
            if not venda_completa:
                return

            cliente = None
            cliente_id = venda_completa.get("cliente_id")
            if cliente_id:
                cliente = self.controllers["venda"].obter_cliente(cliente_id)

            if not cliente:
                cliente = self._buscar_cliente_fallback(venda_completa)

            if cliente:
                nome_cliente = cliente.get("nome", "Nao informado")
                self.cliente_venda_label.config(text="  Cliente: " + nome_cliente)

                endereco = cliente.get("endereco", "") or cliente.get("logradouro", "")
                self.endereco_entry.delete(0, tk.END)
                self.endereco_entry.insert(0, endereco)

                self.cidade_entry.delete(0, tk.END)
                self.cidade_entry.insert(0, cliente.get("cidade", ""))

                self.estado_entry.delete(0, tk.END)
                self.estado_entry.insert(0, cliente.get("estado", "") or cliente.get("uf", ""))

                self.cep_entry.delete(0, tk.END)
                self.cep_entry.insert(0, cliente.get("cep", ""))
            else:
                self.cliente_venda_label.config(text="  Cliente: Consumidor Final (Avulso)")
                self.endereco_entry.delete(0, tk.END)
                self.cidade_entry.delete(0, tk.END)
                self.estado_entry.delete(0, tk.END)
                self.cep_entry.delete(0, tk.END)

            for item in self.itens_venda_tree.get_children():
                self.itens_venda_tree.delete(item)

            itens = venda_completa.get("itens", [])
            for idx, item in enumerate(itens):
                tag = "even" if idx % 2 == 0 else "odd"
                codigo = item.get("codigo", "---")
                nome = item.get("produto_nome", item.get("nome", "Item"))[:30]
                qtd = item.get("quantidade", 1)
                preco = float(item.get("preco_unitario", 0))
                subtotal = float(item.get("subtotal", 0))
                self.itens_venda_tree.insert("", tk.END, tags=(tag,), values=(
                    codigo,
                    nome,
                    qtd,
                    "R$ " + "{:.2f}".format(preco),
                    "R$ " + "{:.2f}".format(subtotal),
                ))

        except Exception as e:
            Logger.log("Erro ao carregar venda: " + str(e), "ERROR")

    def _buscar_cliente_fallback(self, venda_completa):
        cliente_id = venda_completa.get("cliente_id")
        cliente_nome = venda_completa.get("cliente_nome")

        if cliente_id:
            try:
                cliente = self.controllers["venda"].obter_cliente(cliente_id)
                if cliente:
                    return cliente
            except Exception:
                pass

        if cliente_nome and cliente_nome != "Avulso":
            try:
                clientes = self.controllers["venda"].listar_clientes(cliente_nome)
                for c in clientes:
                    if c.get("nome") == cliente_nome:
                        return c
            except Exception:
                pass

        if cliente_nome:
            return {
                "nome": cliente_nome,
                "endereco": venda_completa.get("cliente_endereco", ""),
                "cidade": venda_completa.get("cliente_cidade", ""),
                "estado": venda_completa.get("cliente_uf", ""),
                "cep": venda_completa.get("cliente_cep", ""),
            }
        return None

    def _agendar(self):
        venda_str = self.venda_var.get()
        if not venda_str:
            self.show_message("Aviso", "Selecione uma venda para entregar", "warning")
            return

        try:
            idx = self.venda_combo.current()
            venda = None
            if idx >= 0 and idx < len(self._vendas_lista):
                venda = self._vendas_lista[idx]

            if not venda:
                numero_venda = venda_str.split(" | ")[0].strip()
                for v in self._vendas_dict.values():
                    if str(v.get("numero_venda")) == numero_venda:
                        venda = v
                        break

            if not venda:
                self.show_message("Erro", "Venda nao encontrada", "error")
                return
            venda_id = venda["id"]
            cliente_id = venda.get("cliente_id")
        except Exception as e:
            self.show_message("Erro", "Erro ao processar venda: " + str(e), "error")
            return

        dados = {
            "venda_id":         venda_id,
            "cliente_id":       cliente_id,
            "endereco_entrega": self.endereco_entry.get(),
            "cidade":           self.cidade_entry.get(),
            "estado":           self.estado_entry.get(),
            "cep":              self.cep_entry.get(),
            "data_agendada":    self.data_entry.get(),
            "hora_agendada":    self.hora_entry.get(),
            "valor_frete":      self.frete_entry.get(),
            "tipo_veiculo":     self.veiculo_var.get(),
            "motorista":        self.motorista_entry.get(),
            "placa_veiculo":    self.placa_entry.get(),
            "observacoes":      self.obs_entry.get(),
        }
        success, msg = self.controllers["entrega"].criar_entrega(dados)
        if success:
            self.show_message("Sucesso", msg)
            self._load_entregas()
            self.notebook.select(self.tab_lista)
            self.venda_var.set("")
            for item in self.itens_venda_tree.get_children():
                self.itens_venda_tree.delete(item)
            self.cliente_venda_label.config(
                text="  Cliente: Nenhuma venda selecionada",
                fg=ModernTheme.TEXT_MUTED
            )
        else:
            self.show_message("Erro", msg, "error")

    def _load_entregas(self):
        for item in self.entregas_tree.get_children():
            self.entregas_tree.delete(item)

        status = self.status_entrega_var.get()
        if status == "todos":
            status = None

        contagem = {"total": 0, "agendada": 0, "em_transito": 0, "entregue": 0}

        entregas = self.controllers["entrega"].listar(status) or []
        for idx, e in enumerate(entregas):
            st = e.get("status", "agendada")
            contagem[st] = contagem.get(st, 0) + 1
            contagem["total"] += 1

            data = ""
            if e.get("data_agendada"):
                try:
                    data = e["data_agendada"].strftime("%d/%m/%Y")
                except Exception:
                    data = str(e["data_agendada"])[:10]

            tag = (st, "even" if idx % 2 == 0 else "odd")
            valor_frete = float(e.get("valor_frete", 0) or 0)

            self.entregas_tree.insert("", tk.END, tags=tag, values=(
                e["id"],
                str(e.get("cliente_nome", ""))[:18],
                str(e.get("endereco_entrega", ""))[:32],
                data,
                e.get("tipo_veiculo", ""),
                "R$ " + "{:.2f}".format(valor_frete),
                st,
            ))

        for key in self.stats_labels:
            self.stats_labels[key].config(text=str(contagem.get(key, 0)))
        self.contador_label.config(text=str(contagem["total"]) + " entregas")

    def _get_selected(self):
        sel = self.entregas_tree.selection()
        if not sel:
            self.show_message("Aviso", "Selecione uma entrega", "warning")
            return None
        return self.entregas_tree.item(sel[0])["values"][0]

    def _mudar_status(self, status):
        eid = self._get_selected()
        if eid:
            success, msg = self.controllers["entrega"].atualizar_status(eid, status)
            if success:
                self._load_entregas()
            else:
                self.show_message("Erro", msg, "error")

    def _imprimir_ordem(self):
        eid = self._get_selected()
        if not eid:
            return
        entrega = self.controllers["entrega"].obter(eid)
        if not entrega:
            self.show_message("Erro", "Entrega nao encontrada", "error")
            return
        self._gerar_pdf_entrega(entrega, titulo="ORDEM DE ENTREGA")

    def _reimprimir_ordem(self):
        eid = self._get_selected()
        if not eid:
            return
        entrega = self.controllers["entrega"].obter(eid)
        if not entrega:
            self.show_message("Erro", "Entrega nao encontrada", "error")
            return
        self._gerar_pdf_entrega(entrega, titulo="REIMPRESSAO - ORDEM DE ENTREGA")

    def _gerar_pdf_entrega(self, entrega, titulo="ORDEM DE ENTREGA"):
        try:
            OrdemEntregaGenerator = _carregar_gerador_pdf()
        except ImportError as e:
            messagebox.showerror(
                "Erro de Importacao",
                "Nao foi possivel carregar o gerador de PDF:\n\n" + str(e)
            )
            return

        venda = None
        try:
            venda_id = entrega.get("venda_id")
            if venda_id and "venda" in self.controllers:
                venda = self.controllers["venda"].obter_venda(venda_id)
        except Exception as e:
            Logger.log("Erro ao buscar venda para PDF: " + str(e), "WARNING")

        if venda:
            if not entrega.get("cliente_nome"):
                entrega["cliente_nome"] = venda.get("cliente_nome") or venda.get("cliente") or "Nao informado"
            if not entrega.get("telefone_contato"):
                entrega["telefone_contato"] = venda.get("cliente_telefone") or venda.get("telefone") or venda.get("fone") or ""
            if not entrega.get("cpf_cnpj"):
                for campo in ["cliente_cpf_cnpj", "cpf_cnpj", "cpf", "cnpj", "documento"]:
                    val = venda.get(campo)
                    if val and str(val).strip():
                        entrega["cpf_cnpj"] = val
                        break

        if not entrega.get("motorista"):
            entrega["motorista"] = ""
        if not entrega.get("placa_veiculo"):
            entrega["placa_veiculo"] = ""

        try:
            gerador = OrdemEntregaGenerator(LOJA_CONFIG)
            caminho_pdf = gerador.gerar(entrega, venda=venda)

            resposta = messagebox.askyesno(
                "PDF Gerado",
                "Ordem de entrega gerada com sucesso!\n\n"
                "Arquivo: " + caminho_pdf + "\n\n"
                "Deseja abrir o PDF agora?",
                icon="info"
            )
            if resposta:
                gerador.abrir_pdf(caminho_pdf)

        except Exception as e:
            Logger.log("Erro ao gerar PDF: " + str(e), "ERROR")
            messagebox.showerror(
                "Erro ao Gerar PDF",
                "Nao foi possivel gerar o PDF:\n\n" + str(e) + "\n\n"
                "Verifique se a biblioteca 'reportlab' esta instalada:\n"
                "pip install reportlab"
            )