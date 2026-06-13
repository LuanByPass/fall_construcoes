"""Tela de Orçamentos - FALL Construções (reestilizada + PDF)"""
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, filedialog
from datetime import datetime, timedelta
from views import BaseView
from config import ModernTheme, LOJA_CONFIG
import os
import subprocess

# ═══════════════════════════════════════════════════════════════════
# GERADOR DE PDF - Recibo/Comprovante
# ═══════════════════════════════════════════════════════════════════
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas


class ReciboPDFGenerator:
    """Gera PDF de Recibo/Comprovante de Venda/Orçamento"""

    def __init__(self, loja_config):
        self.loja_config = loja_config
        self.page_width, self.page_height = A4
        self.margin = 10 * mm

    def _safe_str(self, value, default=""):
        if value is None:
            return default
        result = str(value).strip()
        return result if result else default

    def _safe_float(self, value, default=0.0):
        if value is None:
            return default
        try:
            return float(value)
        except (ValueError, TypeError):
            return default

    def _get_val(self, venda, *keys, default=""):
        for key in keys:
            val = venda.get(key) if isinstance(venda, dict) else getattr(venda, key, None)
            if val is not None and str(val).strip():
                return val
        return default

    def gerar(self, venda, output_path="recibo.pdf", tipo_documento="ORÇAMENTO"):
        """Gera o PDF do recibo/comprovante"""
        try:
            print(f"[PDF] Iniciando: {output_path}")

            if isinstance(venda, dict):
                venda = dict(venda)
                if 'tipo_documento' not in venda:
                    venda['tipo_documento'] = tipo_documento

            c = canvas.Canvas(output_path, pagesize=A4)
            numero_doc = self._safe_str(self._get_val(venda, 'numero', 'numero_venda', 'numero_orcamento'), '000')
            c.setTitle(f"Recibo - {numero_doc}")

            y = self.page_height - self.margin

            y = self._draw_header(c, venda, y)
            y -= 3 * mm

            y = self._draw_emitente(c, y)
            y -= 3 * mm

            y = self._draw_destinatario(c, venda, y)
            y -= 3 * mm

            y = self._draw_resumo(c, venda, y)
            y -= 3 * mm

            y = self._draw_produtos(c, venda, y)
            y -= 3 * mm

            self._draw_dados_adicionais(c, venda, y)

            c.save()
            print(f"[PDF] Sucesso: {output_path}")
            return output_path

        except Exception as e:
            print(f"[PDF] ERRO: {e}")
            import traceback
            traceback.print_exc()
            raise

    def _text_center(self, c, x, y, text, font="Helvetica", size=8, bold=False):
        if bold:
            font = font + "-Bold"
        c.setFont(font, size)
        tw = c.stringWidth(str(text), font, size)
        c.drawString(x - tw / 2, y, str(text))

    def _label_value(self, c, x, y, label, value, label_size=6, value_size=8, value_bold=False):
        c.setFillColorRGB(0.3, 0.3, 0.3)
        c.setFont("Helvetica-Bold", label_size)
        c.drawString(x, y, str(label))
        c.setFillColorRGB(0, 0, 0)
        font = "Helvetica-Bold" if value_bold else "Helvetica"
        c.setFont(font, value_size)
        c.drawString(x, y - value_size - 1, str(value))

    def _draw_header(self, c, venda, y_start):
        x = self.margin
        y = y_start
        w_total = self.page_width - 2 * self.margin
        h = 24 * mm

        c.setFillColorRGB(0.95, 0.95, 0.95)
        c.rect(x, y - h, w_total, h, stroke=0, fill=1)
        c.setFillColorRGB(0, 0, 0)
        c.setLineWidth(1)
        c.rect(x, y - h, w_total, h, stroke=1, fill=0)

        cx = x + w_total / 2
        cy = y - 6 * mm
        self._text_center(c, cx, cy, "RECIBO / COMPROVANTE", size=14, bold=True)
        cy -= 5 * mm
        numero_doc = self._safe_str(self._get_val(venda, 'numero', 'numero_venda', 'numero_orcamento'), '000')
        self._text_center(c, cx, cy, f"Nº {numero_doc}", size=12, bold=True)
        cy -= 4 * mm
        self._text_center(c, cx, cy, "DOCUMENTO NÃO FISCAL", size=8)

        # STATUS BADGE
        status = self._safe_str(self._get_val(venda, 'status'), 'PENDENTE').upper()
        tipo_doc = self._safe_str(self._get_val(venda, 'tipo_documento'), 'ORÇAMENTO').upper()

        status_colors = {
            'PENDENTE': (0.95, 0.65, 0.15), 'APROVADO': (0.22, 0.65, 0.22),
            'REJEITADO': (0.85, 0.20, 0.20), 'PAGO': (0.15, 0.55, 0.85),
            'CONVERTIDO': (0.45, 0.30, 0.75), 'ENTREGUE': (0.10, 0.60, 0.50),
            'CANCELADO': (0.50, 0.50, 0.50),
        }
        tipo_colors = {
            'VENDA': (0.15, 0.55, 0.85), 'ORÇAMENTO': (0.85, 0.55, 0.15),
            'PEDIDO': (0.45, 0.30, 0.75),
        }

        st_color = status_colors.get(status, (0.50, 0.50, 0.50))
        tp_color = tipo_colors.get(tipo_doc, (0.30, 0.30, 0.30))

        badge_w = 30 * mm
        badge_h = 6 * mm
        badge_x = x + w_total - badge_w - 3 * mm
        badge_y = y - 6 * mm

        c.setFillColorRGB(*tp_color)
        c.roundRect(badge_x, badge_y - badge_h, badge_w, badge_h, 2*mm, stroke=0, fill=1)
        c.setFillColorRGB(1, 1, 1)
        c.setFont("Helvetica-Bold", 8)
        tw = c.stringWidth(tipo_doc, "Helvetica-Bold", 8)
        c.drawString(badge_x + (badge_w - tw)/2, badge_y - badge_h + 2.2*mm, tipo_doc)

        badge_y2 = y - 13 * mm
        c.setFillColorRGB(*st_color)
        c.roundRect(badge_x, badge_y2 - badge_h, badge_w, badge_h, 2*mm, stroke=0, fill=1)
        c.setFillColorRGB(1, 1, 1)
        c.setFont("Helvetica-Bold", 8)
        tw = c.stringWidth(status, "Helvetica-Bold", 8)
        c.drawString(badge_x + (badge_w - tw)/2, badge_y2 - badge_h + 2.2*mm, status)

        c.setFillColorRGB(0, 0, 0)
        return y - h

    def _draw_emitente(self, c, y_start):
        x = self.margin
        y = y_start
        w = self.page_width - 2 * self.margin
        h = 24 * mm
        c.setLineWidth(1)
        c.rect(x, y - h, w, h, stroke=1, fill=0)
        c.setLineWidth(0.5)
        c.line(x, y - h / 2, x + w, y - h / 2)
        col1 = x + w * 0.50
        col2 = x + w * 0.75
        c.line(col1, y, col1, y - h / 2)
        c.line(col2, y, col2, y - h / 2)
        c.line(col1, y - h / 2, col1, y - h)
        c.line(col2, y - h / 2, col2, y - h)
        ly = y - 5 * mm
        self._label_value(c, x + 2 * mm, ly, "NOME / RAZÃO SOCIAL",
                          self._safe_str(self.loja_config.get('nome'), 'FALL CONSTRUÇÕES'))
        self._label_value(c, col1 + 2 * mm, ly, "CNPJ",
                          self._safe_str(self.loja_config.get('cnpj'), '57.839.618/0001-67'))
        self._label_value(c, col2 + 2 * mm, ly, "INSCRIÇÃO ESTADUAL",
                          self._safe_str(self.loja_config.get('ie'), 'ISENTO'))
        ly2 = y - h / 2 - 5 * mm
        self._label_value(c, x + 2 * mm, ly2, "ENDEREÇO",
                          self._safe_str(self.loja_config.get('endereco'), 'Av. Dom Helder Câmara, 3691'))
        self._label_value(c, col1 + 2 * mm, ly2, "MUNICÍPIO",
                          self._safe_str(self.loja_config.get('cidade'), 'Teresina'))
        self._label_value(c, col2 + 2 * mm, ly2, "UF",
                          self._safe_str(self.loja_config.get('uf'), 'PI'))
        return y - h

    def _draw_destinatario(self, c, venda, y_start):
        x = self.margin
        y = y_start
        w = self.page_width - 2 * self.margin
        h = 34 * mm
        c.setLineWidth(1)
        c.rect(x, y - h, w, h, stroke=1, fill=0)
        c.setLineWidth(0.5)
        c.line(x, y - h / 3, x + w, y - h / 3)
        c.line(x, y - 2 * h / 3, x + w, y - 2 * h / 3)
        col1 = x + w * 0.50
        col2 = x + w * 0.75
        c.line(col1, y, col1, y - h / 3)
        c.line(col2, y, col2, y - h / 3)
        col3 = x + w * 0.35
        col4 = x + w * 0.60
        col5 = x + w * 0.80
        c.line(col3, y - h / 3, col3, y - 2 * h / 3)
        c.line(col4, y - h / 3, col4, y - 2 * h / 3)
        c.line(col5, y - h / 3, col5, y - 2 * h / 3)

        cliente_nome = self._safe_str(self._get_val(venda, 'cliente_nome', 'nome_cliente', 'cliente'), "CONSUMIDOR")
        cpf_cnpj = self._safe_str(self._get_val(venda, 'cpf_cnpj', 'cpf', 'cnpj'), '---')
        data_str = datetime.now().strftime('%d/%m/%Y')
        endereco = self._safe_str(self._get_val(venda, 'cliente_endereco', 'endereco'), 'Não informado')
        cidade = self._safe_str(self._get_val(venda, 'cliente_cidade', 'cidade'), 'Não informado')
        uf = self._safe_str(self._get_val(venda, 'cliente_uf', 'uf'), 'PI')
        telefone = self._safe_str(self._get_val(venda, 'cliente_telefone', 'telefone'), '---')
        forma_pgto = self._safe_str(self._get_val(venda, 'forma_pagamento'), '---').upper()
        vendedor = self._safe_str(self._get_val(venda, 'vendedor', 'usuario'), '---')

        ly = y - 5 * mm
        self._label_value(c, x + 2 * mm, ly, "NOME / RAZÃO SOCIAL", cliente_nome)
        self._label_value(c, col1 + 2 * mm, ly, "CNPJ / CPF", cpf_cnpj)
        self._label_value(c, col2 + 2 * mm, ly, "DATA DA EMISSÃO", data_str)
        ly2 = y - h / 3 - 5 * mm
        self._label_value(c, x + 2 * mm, ly2, "ENDEREÇO", endereco)
        self._label_value(c, col3 + 2 * mm, ly2, "MUNICÍPIO", cidade)
        self._label_value(c, col4 + 2 * mm, ly2, "UF", uf)
        self._label_value(c, col5 + 2 * mm, ly2, "TELEFONE", telefone)
        ly3 = y - 2 * h / 3 - 5 * mm
        hora_str = datetime.now().strftime('%H:%M:%S')
        self._label_value(c, x + 2 * mm, ly3, "DATA DA SAÍDA", data_str)
        self._label_value(c, col3 + 2 * mm, ly3, "HORA DA SAÍDA", hora_str)
        self._label_value(c, col4 + 2 * mm, ly3, "FORMA PAGAMENTO", forma_pgto)
        self._label_value(c, col5 + 2 * mm, ly3, "VENDEDOR", vendedor)
        return y - h

    def _draw_resumo(self, c, venda, y_start):
        x = self.margin
        y = y_start
        w = self.page_width - 2 * self.margin
        h = 20 * mm
        c.setLineWidth(1)
        c.rect(x, y - h, w, h, stroke=1, fill=0)
        c.setLineWidth(0.5)
        col1 = x + w * 0.35
        col2 = x + w * 0.70
        c.line(col1, y, col1, y - h)
        c.line(col2, y, col2, y - h)
        subtotal = self._safe_float(self._get_val(venda, 'subtotal'), 0)
        desconto = self._safe_float(self._get_val(venda, 'desconto'), 0)
        total = self._safe_float(self._get_val(venda, 'total'), 0)
        ly = y - 5 * mm
        c.setFillColorRGB(0.3, 0.3, 0.3)
        c.setFont("Helvetica-Bold", 5)
        c.drawString(x + 2 * mm, ly, "SUBTOTAL")
        c.drawString(col1 + 2 * mm, ly, "DESCONTO")
        c.drawString(col2 + 2 * mm, ly, "TOTAL GERAL")
        c.setFillColorRGB(0, 0, 0)
        c.setFont("Helvetica-Bold", 9)
        c.drawString(x + 2 * mm, ly - 10, f"R$ {subtotal:.2f}")
        c.drawString(col1 + 2 * mm, ly - 10, f"R$ {desconto:.2f}")
        c.drawString(col2 + 2 * mm, ly - 10, f"R$ {total:.2f}")
        return y - h

    def _draw_produtos(self, c, venda, y_start):
        x = self.margin
        y = y_start
        w = self.page_width - 2 * self.margin
        itens = venda.get("itens", [])
        row_height = 6 * mm
        header_height = 8 * mm
        h = header_height + len(itens) * row_height + 2 * mm
        if h < 30 * mm:
            h = 30 * mm
        c.setLineWidth(1)
        c.rect(x, y - h, w, h, stroke=1, fill=0)
        c.setFillColorRGB(0.9, 0.9, 0.9)
        c.rect(x, y - header_height, w, header_height, stroke=0, fill=1)
        c.setFillColorRGB(0, 0, 0)
        cols_x = [x, x + 20*mm, x + 95*mm, x + 110*mm, x + 125*mm, x + 150*mm, x + w]
        c.setLineWidth(0.5)
        for cx in cols_x[1:-1]:
            c.line(cx, y, cx, y - h)
        c.line(x, y - header_height, x + w, y - header_height)
        headers = ["CÓDIGO", "DESCRIÇÃO", "UN", "QTD", "V. UNIT.", "V. TOTAL"]
        for i, h_text in enumerate(headers):
            if i >= len(cols_x) - 1: break
            cx = cols_x[i] + 1 * mm
            c.setFont("Helvetica-Bold", 6)
            c.drawString(cx, y - 5 * mm, h_text)
        c.setFont("Helvetica", 6)
        for idx, item in enumerate(itens):
            iy = y - header_height - (idx + 1) * row_height + 2 * mm
            nome = self._safe_str(item.get('produto_nome', item.get('nome', 'Item')))[:40]
            codigo = self._safe_str(item.get('codigo', '---'))
            qtd = self._safe_float(item.get('quantidade', 1))
            preco = self._safe_float(item.get('preco_unitario', 0))
            total_item = self._safe_float(item.get('subtotal', preco * qtd))
            vals = [str(codigo)[:12], nome[:38], "UN", str(int(qtd)), f"R$ {preco:.2f}", f"R$ {total_item:.2f}"]
            for i, val in enumerate(vals):
                if i >= len(cols_x) - 1: break
                cx = cols_x[i] + 1 * mm
                if i >= 4:
                    tw = c.stringWidth(val, "Helvetica", 6)
                    c.drawString(cx + 15*mm - tw - 2*mm, iy, val)
                else:
                    c.drawString(cx, iy, val)
            c.setLineWidth(0.3)
            c.line(x, y - header_height - (idx + 1) * row_height, x + w, y - header_height - (idx + 1) * row_height)
        return y - h

    def _draw_dados_adicionais(self, c, venda, y_start):
        x = self.margin
        y = y_start
        w = self.page_width - 2 * self.margin
        h = 28 * mm
        c.setLineWidth(1)
        c.rect(x, y - h, w, h, stroke=1, fill=0)
        c.setLineWidth(0.5)
        c.line(x + w * 0.65, y, x + w * 0.65, y - h)
        c.setFillColorRGB(0.9, 0.9, 0.9)
        c.rect(x, y - 5 * mm, w * 0.65, 5 * mm, stroke=0, fill=1)
        c.rect(x + w * 0.65, y - 5 * mm, w * 0.35, 5 * mm, stroke=0, fill=1)
        c.setFillColorRGB(0, 0, 0)
        c.setFont("Helvetica-Bold", 6)
        c.drawString(x + 2 * mm, y - 3.5 * mm, "OBSERVAÇÕES / INFORMAÇÕES COMPLEMENTARES")
        c.drawString(x + w * 0.65 + 2 * mm, y - 3.5 * mm, "ASSINATURA DO CLIENTE")
        forma = self._safe_str(self._get_val(venda, 'forma_pagamento'), 'dinheiro').upper()
        numero = self._safe_str(self._get_val(venda, 'numero', 'numero_orcamento'), '---')
        vendedor = self._safe_str(self._get_val(venda, 'vendedor', 'usuario'), '---')
        obs = self._safe_str(self._get_val(venda, 'observacao', 'obs'), '')
        info = f"FORMA: {forma} | Nº: {numero} | VENDEDOR: {vendedor}"
        if obs:
            info += f" | OBS: {obs}"
        if len(info) > 120:
            info = info[:117] + "..."
        c.setFont("Helvetica", 5.5)
        c.drawString(x + 2 * mm, y - 10 * mm, info)
        c.drawString(x + 2 * mm, y - 14 * mm, "FALL CONSTRUÇÕES - Documento não fiscal para controle interno")
        c.drawString(x + 2 * mm, y - 18 * mm, "Não possui valor fiscal. Conserve este comprovante para eventuais trocas.")
        c.drawString(x + 2 * mm, y - 22 * mm, "Trocas em até 7 dias com este documento e produto sem uso.")
        c.line(x + w * 0.65 + 5 * mm, y - 15 * mm, x + w - 5 * mm, y - 15 * mm)
        c.setFont("Helvetica", 5)
        c.drawString(x + w * 0.65 + 5 * mm, y - 18 * mm, "Assinatura do Cliente / Recebedor")


try:
    from utils.logger import Logger
except Exception:
    class Logger:
        @classmethod
        def log(cls, msg, level="INFO"):
            print(f"[{level}] {msg}")

class OrcamentoView(BaseView):
    def __init__(self, parent, controllers):
        super().__init__(parent, None)
        self.controllers = controllers
        self.orcamento_atual = None
        self.itens_orcamento = []
        self.build()

    def build(self):
        self.frame = tk.Frame(self.parent, bg=ModernTheme.BG)
        self.notebook = ttk.Notebook(self.frame)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=16, pady=(0, 16))

        self.tab_novo  = tk.Frame(self.notebook, bg=ModernTheme.BG)
        self.tab_lista = tk.Frame(self.notebook, bg=ModernTheme.BG)
        self.notebook.add(self.tab_novo,  text="➕  Novo Orçamento")
        self.notebook.add(self.tab_lista, text="📋  Listar Orçamentos")

        self._build_novo_tab()
        self._build_lista_tab()

    # ─────────────────────────────────────────────────────────────────────────
    def _build_novo_tab(self):
        # Card: cliente + validade
        info_card = tk.Frame(self.tab_novo, bg=ModernTheme.CARD_BG,
                             highlightbackground=ModernTheme.BORDER,
                             highlightthickness=1)
        info_card.pack(fill=tk.X, padx=12, pady=(12, 0))
        tk.Frame(info_card, bg=ModernTheme.PRIMARY, height=3).pack(fill=tk.X)

        info_body = tk.Frame(info_card, bg=ModernTheme.CARD_BG, padx=14, pady=10)
        info_body.pack(fill=tk.X)

        # Linha: cliente / validade / botão iniciar
        row = tk.Frame(info_body, bg=ModernTheme.CARD_BG)
        row.pack(fill=tk.X)

        cli_col = tk.Frame(row, bg=ModernTheme.CARD_BG)
        cli_col.pack(side=tk.LEFT, fill=tk.X, expand=True)
        tk.Label(cli_col, text="CLIENTE",
                 font=("Segoe UI", 9, "bold"),
                 bg=ModernTheme.CARD_BG, fg=ModernTheme.TEXT_MUTED).pack(anchor=tk.W, pady=(0, 4))
        self.cliente_var = tk.StringVar()
        clientes = self.controllers["orcamento"].listar_clientes()
        self.cliente_combo = ttk.Combobox(
            cli_col, textvariable=self.cliente_var,
            values=[f"{c['id']} - {c['nome']}" for c in clientes],
            state="readonly", font=ModernTheme.FONT_MD)
        self.cliente_combo.pack(fill=tk.X)

        val_col = tk.Frame(row, bg=ModernTheme.CARD_BG)
        val_col.pack(side=tk.LEFT, padx=(16, 16))
        tk.Label(val_col, text="VALIDADE (DIAS)",
                 font=("Segoe UI", 9, "bold"),
                 bg=ModernTheme.CARD_BG, fg=ModernTheme.TEXT_MUTED).pack(anchor=tk.W, pady=(0, 4))
        self.validade_entry = self.styled_entry(val_col, width=6)
        self.validade_entry.insert(0, "7")
        self.validade_entry.pack()

        self.styled_button(row, "Iniciar Orçamento", self._novo_orcamento,
                           ModernTheme.SUCCESS, icon="🆕").pack(
            side=tk.LEFT, anchor=tk.S, pady=2)

        # ── Busca de produtos ─────────────────────────────────────────────────
        search_card = tk.Frame(self.tab_novo, bg=ModernTheme.CARD_BG,
                               highlightbackground=ModernTheme.BORDER,
                               highlightthickness=1)
        search_card.pack(fill=tk.X, padx=12, pady=8)
        tk.Frame(search_card, bg=ModernTheme.INFO, height=3).pack(fill=tk.X)

        search_body = tk.Frame(search_card, bg=ModernTheme.CARD_BG, padx=14, pady=10)
        search_body.pack(fill=tk.X)

        tk.Label(search_body, text="🔍  Código de Barras / Busca",
                 font=ModernTheme.FONT_LG,
                 bg=ModernTheme.CARD_BG, fg=ModernTheme.TEXT).pack(anchor=tk.W, pady=(0, 6))

        srch_row = tk.Frame(search_body, bg=ModernTheme.CARD_BG)
        srch_row.pack(fill=tk.X)

        self.busca_entry = self.styled_entry(srch_row,
                                             "Digite o código ou nome...",
                                             width=46)
        self.busca_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, pady=(0, 4))
        self.busca_entry.bind("<Return>", lambda e: self._buscar_e_adicionar())
        self.busca_entry.focus_set()

        self.styled_button(srch_row, "Adicionar", self._buscar_e_adicionar,
                           ModernTheme.SUCCESS, icon="➕").pack(side=tk.LEFT, padx=(8, 0))

        # ── Itens do orçamento ────────────────────────────────────────────────
        tk.Label(self.tab_novo, text="Itens do Orçamento",
                 font=ModernTheme.FONT_LG,
                 bg=ModernTheme.BG, fg=ModernTheme.TEXT).pack(
            anchor=tk.W, padx=14, pady=(4, 4))

        itens_card = tk.Frame(self.tab_novo, bg=ModernTheme.CARD_BG,
                              highlightbackground=ModernTheme.BORDER,
                              highlightthickness=1)
        itens_card.pack(fill=tk.BOTH, expand=True, padx=12, pady=(0, 4))

        cols_i = ("Código", "Produto", "Qtd", "Preço", "Subtotal")
        self.itens_tree = ttk.Treeview(itens_card, columns=cols_i,
                                       show="headings", height=8)
        for col, w in zip(cols_i, [100, 320, 60, 110, 110]):
            self.itens_tree.heading(col, text=col)
            self.itens_tree.column(col, width=w)

        sb = ttk.Scrollbar(itens_card, orient=tk.VERTICAL, command=self.itens_tree.yview)
        self.itens_tree.configure(yscrollcommand=sb.set)
        self.itens_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb.pack(side=tk.RIGHT, fill=tk.Y)

        # ── Rodapé: resumo + botões ───────────────────────────────────────────
        resumo_card = tk.Frame(self.tab_novo, bg=ModernTheme.CARD_BG,
                               highlightbackground=ModernTheme.BORDER,
                               highlightthickness=1)
        resumo_card.pack(fill=tk.X, padx=12, pady=4)

        res_inner = tk.Frame(resumo_card, bg=ModernTheme.CARD_BG, padx=14, pady=10)
        res_inner.pack(fill=tk.X)

        self.numero_label = tk.Label(res_inner, text="Nº: —",
                                     font=ModernTheme.FONT_BASE,
                                     bg=ModernTheme.CARD_BG, fg=ModernTheme.TEXT_MUTED)
        self.numero_label.pack(side=tk.LEFT)

        self.subtotal_label = tk.Label(res_inner, text="Subtotal: R$ 0,00",
                                       font=ModernTheme.FONT_MD,
                                       bg=ModernTheme.CARD_BG, fg=ModernTheme.TEXT_LIGHT)
        self.subtotal_label.pack(side=tk.LEFT, padx=30)

        self.total_label = tk.Label(res_inner, text="TOTAL: R$ 0,00",
                                    font=("Segoe UI", 18, "bold"),
                                    bg=ModernTheme.CARD_BG, fg=ModernTheme.PRIMARY)
        self.total_label.pack(side=tk.RIGHT)

        # Botões de ação
        btn_bar = self.make_toolbar(self.tab_novo)
        self.styled_button(btn_bar, "Remover Item", self._remover_item,
                           ModernTheme.DANGER, icon="🗑️").pack(side=tk.LEFT)
        self.styled_button(btn_bar, "Cancelar Orçamento", self._cancelar_orcamento_atual,
                           ModernTheme.WARNING, icon="❌").pack(side=tk.LEFT, padx=6)
        self.styled_button(btn_bar, "Imprimir", self._abrir_dialogo_impressao,
                           ModernTheme.INFO, icon="🖨️").pack(side=tk.RIGHT, padx=6)
        self.styled_button(btn_bar, "Finalizar Orçamento", self._finalizar,
                           ModernTheme.SUCCESS, icon="✅").pack(side=tk.RIGHT)

    # ─────────────────────────────────────────────────────────────────────────
    def _build_lista_tab(self):
        # Toolbar filtros
        toolbar = self.make_toolbar(self.tab_lista)

        self.status_var = tk.StringVar(value="todos")
        _opts = [("todos", "Todos"), ("pendente", "Pendentes"),
                 ("aprovado", "Aprovados"), ("rejeitado", "Rejeitados"),
                 ("convertido", "Convertidos")]

        for val, text in _opts:
            tk.Radiobutton(toolbar, text=text, variable=self.status_var, value=val,
                           bg=ModernTheme.BG, fg=ModernTheme.TEXT,
                           font=ModernTheme.FONT_BASE,
                           selectcolor=ModernTheme.BG,
                           activebackground=ModernTheme.BG,
                           command=self._load_orcamentos).pack(side=tk.LEFT, padx=4)

        self.styled_button(toolbar, "Atualizar", self._load_orcamentos,
                           icon="🔄").pack(side=tk.RIGHT)

        # Tabela
        card = tk.Frame(self.tab_lista, bg=ModernTheme.CARD_BG,
                        highlightbackground=ModernTheme.BORDER,
                        highlightthickness=1)
        card.pack(fill=tk.BOTH, expand=True, padx=12, pady=(0, 4))

        columns = ("Nº", "Cliente", "Data", "Validade", "Total", "Status")
        self.orcamentos_tree = ttk.Treeview(card, columns=columns,
                                            show="headings", height=18)
        for col, w in zip(columns, [130, 210, 110, 110, 110, 130]):
            self.orcamentos_tree.heading(col, text=col)
            self.orcamentos_tree.column(col, width=w)

        self.orcamentos_tree.tag_configure("pendente",   foreground=ModernTheme.WARNING)
        self.orcamentos_tree.tag_configure("aprovado",   foreground=ModernTheme.SUCCESS)
        self.orcamentos_tree.tag_configure("rejeitado",  foreground=ModernTheme.DANGER)
        self.orcamentos_tree.tag_configure("convertido", foreground=ModernTheme.INFO)

        sb = ttk.Scrollbar(card, orient=tk.VERTICAL, command=self.orcamentos_tree.yview)
        self.orcamentos_tree.configure(yscrollcommand=sb.set)
        self.orcamentos_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb.pack(side=tk.RIGHT, fill=tk.Y)

        # Botões de ação
        acoes = self.make_toolbar(self.tab_lista)
        self.styled_button(acoes, "✅ Aprovar",          self._aprovar,
                           ModernTheme.SUCCESS).pack(side=tk.LEFT, padx=3)
        self.styled_button(acoes, "❌ Rejeitar",         self._rejeitar,
                           ModernTheme.DANGER).pack(side=tk.LEFT, padx=3)
        self.styled_button(acoes, "🖨️ Imprimir",        self._imprimir_orcamento_lista,
                           ModernTheme.INFO).pack(side=tk.LEFT, padx=3)
        self.styled_button(acoes, "🛒 Converter em Venda", self._converter_venda,
                           ModernTheme.PRIMARY).pack(side=tk.LEFT, padx=3)

        self._load_orcamentos()

    # ── Busca e adição de produto (igual à tela de vendas) ───────────────────
    def _buscar_e_adicionar(self):
        if not self.orcamento_atual:
            self.show_message("Aviso", "Inicie um orçamento primeiro", "warning")
            return

        codigo = self.busca_entry.get().strip()
        placeholder = "Digite o código ou nome..."
        if not codigo or codigo == placeholder:
            return

        produto = self.controllers["produto"].obter_por_codigo_barras(codigo)

        if not produto:
            produtos = self.controllers["produto"].listar(codigo)
            if len(produtos) == 1:
                produto = produtos[0]
            elif len(produtos) > 1:
                self._selecionar_produto(produtos)
                return
            else:
                self.show_message("Não encontrado", "Produto não encontrado!", "warning")
                self.busca_entry.delete(0, tk.END)
                self.busca_entry.focus_set()
                return

        if produto:
            self._adicionar_item(produto)

        self.busca_entry.delete(0, tk.END)
        self.busca_entry.focus_set()

    def _selecionar_produto(self, produtos):
        """Janela externa para seleção de produto (igual tela de vendas)"""
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
        if not self.orcamento_atual:
            self.show_message("Aviso", "Inicie um orçamento primeiro!", "warning")
            return

        qtd = simpledialog.askinteger(
            "Quantidade",
            f"Produto: {produto['nome']}\nQuantidade:",
            parent=self.parent, minvalue=1, initialvalue=1
        )
        if not qtd:
            return

        success, msg = self.controllers["orcamento"].adicionar_item(
            self.orcamento_atual["id"], produto["id"], qtd
        )
        if success:
            self.itens_orcamento.append({
                "produto_id": produto["id"],
                "codigo":     produto.get("codigo", ""),
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

    # ── Controles do orçamento ────────────────────────────────────────────────
    def _novo_orcamento(self):
        # ✅ CORREÇÃO: evita orçamentos fantasmas
        if self.orcamento_atual is not None:
            resposta = messagebox.askyesno(
                "Orçamento em Andamento",
                f"Já existe um orçamento em andamento ({self.orcamento_atual.get('numero', 'N/A')}).\n\n"
                "Deseja cancelar o atual e criar um novo?"
            )
            if not resposta:
                return
            # Tenta cancelar o orçamento anterior no backend
            try:
                self.controllers["orcamento"].rejeitar(self.orcamento_atual["id"])
                Logger.log(f"Orçamento anterior cancelado: {self.orcamento_atual['numero']}", "INFO")
            except Exception as e:
                Logger.log(f"Não foi possível cancelar orçamento anterior: {e}", "WARNING")
            # Limpa a referência local independente do backend
            self._limpar_orcamento_atual()

        cliente_str = self.cliente_var.get()
        if not cliente_str:
            self.show_message("Aviso", "Selecione um cliente", "warning")
            return
        cliente_id = int(cliente_str.split(" - ")[0])
        dias = int(self.validade_entry.get() or 7)

        success, result = self.controllers["orcamento"].criar_orcamento(
            cliente_id, None, dias)
        if success:
            self.orcamento_atual = result
            self.itens_orcamento = []
            self.numero_label.config(text=f"Nº: {result['numero']}")
            self._atualizar_itens()
            self._atualizar_resumo()
            Logger.log(f"Orçamento iniciado: {result['numero']}", "SUCCESS")

    def _cancelar_orcamento_atual(self):
        """Cancela o orçamento em andamento sem finalizar"""
        if not self.orcamento_atual:
            self.show_message("Aviso", "Nenhum orçamento em andamento", "warning")
            return
        if messagebox.askyesno(
            "Cancelar Orçamento",
            f"Deseja cancelar o orçamento {self.orcamento_atual.get('numero', 'N/A')}?\n"
            "Todos os itens serão perdidos."
        ):
            try:
                self.controllers["orcamento"].rejeitar(self.orcamento_atual["id"])
            except Exception as e:
                Logger.log(f"Erro ao cancelar no backend: {e}", "WARNING")
            self._limpar_orcamento_atual()
            self.show_message("Cancelado", "Orçamento cancelado com sucesso")

    def _limpar_orcamento_atual(self):
        """Reseta o estado local do orçamento atual"""
        self.orcamento_atual = None
        self.itens_orcamento = []
        self.numero_label.config(text="Nº: —")
        self.subtotal_label.config(text="Subtotal: R$ 0,00")
        self.total_label.config(text="TOTAL: R$ 0,00")
        for item in self.itens_tree.get_children():
            self.itens_tree.delete(item)

    def _remover_item(self):
        selected = self.itens_tree.selection()
        if selected:
            idx = self.itens_tree.index(selected[0])
            if 0 <= idx < len(self.itens_orcamento):
                del self.itens_orcamento[idx]
                self._atualizar_itens()
                self._atualizar_resumo()

    def _atualizar_itens(self):
        for item in self.itens_tree.get_children():
            self.itens_tree.delete(item)
        for item in self.itens_orcamento:
            self.itens_tree.insert("", tk.END, values=(
                item["codigo"], item["nome"], item["quantidade"],
                f"R$ {item['preco']:.2f}", f"R$ {item['subtotal']:.2f}",
            ))

    def _atualizar_resumo(self):
        subtotal = sum(i["subtotal"] for i in self.itens_orcamento)
        self.subtotal_label.config(text=f"Subtotal: R$ {subtotal:,.2f}")
        self.total_label.config(text=f"TOTAL: R$ {subtotal:,.2f}")

    def _finalizar(self):
        if not self.orcamento_atual or not self.itens_orcamento:
            self.show_message("Aviso", "Adicione itens ao orçamento", "warning")
            return
        desconto = simpledialog.askfloat(
            "Desconto", "Valor do desconto (R$):",
            parent=self.parent, minvalue=0, initialvalue=0
        )
        if desconto is None:
            desconto = 0
        success, result = self.controllers["orcamento"].finalizar_orcamento(
            self.orcamento_atual["id"], desconto)
        if success:
            self.show_message("Sucesso",
                              f"Orçamento finalizado! Total: R$ {result['total']:,.2f}")
            self._limpar_orcamento_atual()
            self._load_orcamentos()

    # ── Lista ─────────────────────────────────────────────────────────────────
    def _load_orcamentos(self):
        for item in self.orcamentos_tree.get_children():
            self.orcamentos_tree.delete(item)

        status = self.status_var.get()
        if status == "todos":
            status = None

        _icons = {"pendente": "⏳", "aprovado": "✅",
                  "rejeitado": "❌", "convertido": "🛒"}

        for o in self.controllers["orcamento"].listar(status):
            st = o.get("status", "pendente")
            icon = _icons.get(st, "•")

            data_orc = ""
            if o.get("data_orcamento"):
                try:
                    data_orc = o["data_orcamento"].strftime("%d/%m/%Y")
                except Exception:
                    data_orc = str(o["data_orcamento"])[:10]

            data_val = ""
            if o.get("data_validade"):
                try:
                    data_val = o["data_validade"].strftime("%d/%m/%Y")
                except Exception:
                    data_val = str(o["data_validade"])[:10]

            self.orcamentos_tree.insert("", tk.END, tags=(st,), values=(
                o["numero_orcamento"],
                str(o.get("cliente_nome", "Avulso"))[:22],
                data_orc, data_val,
                f"R$ {float(o.get('total') or 0):.2f}",
                f"{icon} {st}",
            ))

    def _get_selected_orcamento(self):
        sel = self.orcamentos_tree.selection()
        if not sel:
            self.show_message("Aviso", "Selecione um orçamento", "warning")
            return None
        return self.orcamentos_tree.item(sel[0])["values"][0]

    def _aprovar(self):
        numero = self._get_selected_orcamento()
        if numero:
            for o in self.controllers["orcamento"].listar():
                if o["numero_orcamento"] == numero:
                    self.controllers["orcamento"].aprovar(o["id"])
                    self._load_orcamentos()
                    break

    def _rejeitar(self):
        numero = self._get_selected_orcamento()
        if numero:
            for o in self.controllers["orcamento"].listar():
                if o["numero_orcamento"] == numero:
                    self.controllers["orcamento"].rejeitar(o["id"])
                    self._load_orcamentos()
                    break

    def _converter_venda(self):
        numero = self._get_selected_orcamento()
        if numero:
            for o in self.controllers["orcamento"].listar():
                if o["numero_orcamento"] == numero:
                    success, result = self.controllers["orcamento"].converter_em_venda(
                        o["id"], self.controllers["venda"])
                    if success:
                        self.show_message("Sucesso",
                                          f"Orçamento convertido em venda {result['numero']}!")
                        self._load_orcamentos()
                    else:
                        self.show_message("Erro", result, "error")
                    break

    # ── Impressão ─────────────────────────────────────────────────────────────
    def _imprimir_orcamento_lista(self):
        numero = self._get_selected_orcamento()
        if not numero:
            return
        for o in self.controllers["orcamento"].listar():
            if o["numero_orcamento"] == numero:
                orc = self.controllers["orcamento"].obter(o["id"])
                self._abrir_dialogo_impressao_completo(orc)
                break

    def _abrir_dialogo_impressao(self):
        if not self.orcamento_atual:
            self.show_message("Aviso", "Inicie um orçamento primeiro", "warning")
            return
        orc = self.controllers["orcamento"].obter(self.orcamento_atual["id"])
        if orc:
            self._abrir_dialogo_impressao_completo(orc)

    def _abrir_dialogo_impressao_completo(self, orcamento):
        """Gera PDF profissional"""
        import tempfile
        import traceback

        try:
            # Usa diretório temp do sistema (sempre existe e tem permissão)
            temp_dir = tempfile.gettempdir()
            pdf_path = os.path.join(temp_dir, "orcamento_fall.pdf")

            print(f"[PDF] Gerando em: {pdf_path}")
            Logger.log(f"Gerando PDF em: {pdf_path}", "INFO")

            # Cria gerador
            gerador = ReciboPDFGenerator(LOJA_CONFIG)

            # Gera PDF
            resultado = gerador.gerar(orcamento, output_path=pdf_path, tipo_documento="ORÇAMENTO")
            print(f"[PDF] Resultado: {resultado}")

            # Verifica se foi criado
            if os.path.exists(pdf_path):
                tamanho = os.path.getsize(pdf_path)
                print(f"[PDF] Arquivo existe! Tamanho: {tamanho}")

                if tamanho > 0:
                    Logger.log(f"PDF criado: {pdf_path} ({tamanho} bytes)", "SUCCESS")

                    # Abre o PDF
                    try:
                        if os.name == "nt":
                            os.startfile(pdf_path)
                            print("[PDF] Aberto automaticamente")
                    except Exception as e2:
                        print(f"[PDF] Não abriu: {e2}")

                    messagebox.showinfo(
                        "PDF Gerado",
                        f"Orçamento salvo em PDF!\n\nLocal: {pdf_path}\nTamanho: {tamanho} bytes"
                    )
                else:
                    raise Exception("PDF criado mas está vazio (0 bytes)")
            else:
                raise Exception(f"Arquivo não foi criado em: {pdf_path}")

        except Exception as e:
            erro_msg = str(e)
            Logger.log(f"Erro PDF: {erro_msg}", "ERROR")
            traceback_str = traceback.format_exc()
            print(f"[PDF] ERRO: {erro_msg}")
            print(f"[PDF] Traceback: {traceback_str}")

            messagebox.showerror(
                "Erro ao Gerar PDF",
                f"Não foi possível gerar o PDF.\n\nErro: {erro_msg}\n\n"
                f"Verifique se 'reportlab' está instalado:\n"
                f"pip install reportlab"
            )

    def _imprimir_cupom(self, orcamento):
        comp = tk.Toplevel(self.parent)
        comp.title("Cupom Fiscal — Orçamento")
        comp.geometry("330x620")
        comp.configure(bg="white")

        text = tk.Text(comp, font=("Courier", 10), bg="white",
                       wrap=tk.WORD, padx=10, pady=10, width=40)
        text.pack(fill=tk.BOTH, expand=True)

        def fmt(v, d=""): return str(v) if v is not None else d
        def fmtm(v): return f"R$ {float(v or 0):,.2f}"

        text.insert(tk.END, "\n")
        text.insert(tk.END, f"  {fmt(LOJA_CONFIG.get('nome'))}\n")
        text.insert(tk.END, f"  {fmt(LOJA_CONFIG.get('endereco'))}\n")
        text.insert(tk.END, f"  Tel: {fmt(LOJA_CONFIG.get('telefone'))}\n")
        text.insert(tk.END, "-" * 32 + "\n")
        text.insert(tk.END, "        ORÇAMENTO\n")
        text.insert(tk.END, f"  Nº: {fmt(orcamento.get('numero_orcamento'))}\n")
        text.insert(tk.END,
            f"  Emissão: {datetime.now().strftime('%d/%m/%Y %H:%M')}\n")
        text.insert(tk.END,
            f"  Validade: {fmt(orcamento.get('data_validade'))}\n")
        text.insert(tk.END, "-" * 32 + "\n")
        text.insert(tk.END,
            f"  CLIENTE: {fmt(orcamento.get('cliente_nome', 'Avulso'))}\n")
        text.insert(tk.END, "-" * 32 + "\n")
        text.insert(tk.END, "  COD    DESCRIÇÃO    QTD   TOTAL\n")
        text.insert(tk.END, "-" * 32 + "\n")

        for item in orcamento.get("itens", []):
            nome  = fmt(item.get("produto_nome", ""))[:14]
            qtd   = float(item.get("quantidade", 1))
            preco = float(item.get("preco_unitario", 0))
            tot   = float(item.get("subtotal", 0))
            text.insert(tk.END, f"  {nome}\n")
            text.insert(tk.END, f"  {qtd:>3.0f} x {preco:>6.2f} = {tot:>8.2f}\n")

        text.insert(tk.END, "-" * 32 + "\n")
        subtotal = float(orcamento.get("subtotal", 0))
        desconto = float(orcamento.get("desconto", 0))
        total    = float(orcamento.get("total", 0))

        text.insert(tk.END, f"  SUBTOTAL:       {fmtm(subtotal)}\n")
        if desconto > 0:
            text.insert(tk.END, f"  DESCONTO:      -{fmtm(desconto)}\n")
        text.insert(tk.END, f"  TOTAL:          {fmtm(total)}\n")
        text.insert(tk.END, "-" * 32 + "\n")
        text.insert(tk.END, "  Não tem valor fiscal.\n")
        text.insert(tk.END,
            f"  Status: {fmt(orcamento.get('status', 'pendente')).upper()}\n\n")
        text.insert(tk.END, "  ____________________________\n")
        text.insert(tk.END, "  ASSINATURA DO CLIENTE\n")

        text.config(state=tk.DISABLED)

        btn_frame = tk.Frame(comp, bg="white")
        btn_frame.pack(pady=8)

        for label, color, cmd in [
            ("🖨️ Imprimir", ModernTheme.PRIMARY,
             lambda: self._imprimir_texto(text)),
            ("💾 Salvar TXT", ModernTheme.SUCCESS,
             lambda: self._salvar_arquivo(text,
                f"orcamento_{orcamento.get('numero_orcamento', '000')}")),
        ]:
            tk.Button(btn_frame, text=label, command=cmd,
                      bg=color, fg="white", bd=0, padx=12, pady=7,
                      font=ModernTheme.FONT_BASE, cursor="hand2").pack(
                side=tk.LEFT, padx=4)

    # ── A4 ────────────────────────────────────────────────────────────────────
    def _imprimir_a4(self, orcamento):
        comp = tk.Toplevel(self.parent)
        comp.title("Orçamento A4")
        comp.geometry("720x920")
        comp.configure(bg="white")

        canvas    = tk.Canvas(comp, bg="white", bd=0, highlightthickness=0)
        scrollbar = ttk.Scrollbar(comp, orient="vertical", command=canvas.yview)
        sf        = tk.Frame(canvas, bg="white")

        sf.bind("<Configure>",
                lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=sf, anchor="nw", width=700)
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        def lbl(parent, text, size=11, bold=False,
                color=ModernTheme.TEXT, pady=2, anchor="w"):
            tk.Label(parent, text=text,
                     font=("Segoe UI", size, "bold" if bold else "normal"),
                     bg="white", fg=color, anchor=anchor,
                     justify=tk.LEFT).pack(fill=tk.X, pady=pady, padx=24)

        def sep():
            tk.Frame(sf, bg=ModernTheme.BORDER, height=1).pack(
                fill=tk.X, padx=24, pady=6)

        def fmt(v, d=""): return str(v) if v is not None else d
        def fmtm(v): return f"R$ {float(v or 0):,.2f}"

        # Cabeçalho
        lbl(sf, LOJA_CONFIG.get("nome", ""), 20, True, ModernTheme.PRIMARY, 6, "center")
        lbl(sf, LOJA_CONFIG.get("endereco", ""), 10, False, ModernTheme.CIMENTO, 2, "center")
        lbl(sf, f"Tel: {LOJA_CONFIG.get('telefone','')} | CNPJ: {LOJA_CONFIG.get('cnpj','')}",
            9, False, ModernTheme.CIMENTO, 2, "center")

        tk.Frame(sf, bg="white", height=12).pack()
        lbl(sf, "ORÇAMENTO", 22, True, ModernTheme.PRIMARY, 10, "center")
        sep()

        # Info
        info_row = tk.Frame(sf, bg="white")
        info_row.pack(fill=tk.X, padx=24, pady=8)
        tk.Label(info_row,
                 text=f"Número: {fmt(orcamento.get('numero_orcamento'))}",
                 font=("Segoe UI", 12, "bold"), bg="white",
                 fg=ModernTheme.TEXT).pack(side=tk.LEFT)
        tk.Label(info_row,
                 text=f"Emissão: {datetime.now().strftime('%d/%m/%Y %H:%M')}",
                 font=("Segoe UI", 11), bg="white",
                 fg=ModernTheme.CIMENTO).pack(side=tk.RIGHT)
        sep()

        # Cliente
        lbl(sf, "DADOS DO CLIENTE", 13, True, ModernTheme.PRIMARY, 8)
        for key, label in [
            ("cliente_nome",      "Nome"),
            ("cliente_cpf_cnpj",  "CPF/CNPJ"),
            ("cliente_telefone",  "Telefone"),
            ("cliente_endereco",  "Endereço"),
        ]:
            val = fmt(orcamento.get(key, ""))
            if val:
                lbl(sf, f"{label}: {val}")
        sep()

        # Tabela de itens
        lbl(sf, "ITENS DO ORÇAMENTO", 13, True, ModernTheme.PRIMARY, 8)

        itens_frame = tk.Frame(sf, bg="white")
        itens_frame.pack(fill=tk.X, padx=24, pady=4)

        headers = ["#", "Código", "Descrição", "Qtd", "Un.", "Preço Unit.", "Total"]
        widths  = [3, 10, 28, 5, 5, 12, 12]

        hdr_row = tk.Frame(itens_frame, bg=ModernTheme.PRIMARY)
        hdr_row.pack(fill=tk.X)
        for h, w in zip(headers, widths):
            tk.Label(hdr_row, text=h,
                     font=("Segoe UI", 10, "bold"),
                     bg=ModernTheme.PRIMARY, fg="white",
                     width=w, anchor="w").pack(side=tk.LEFT, padx=2)

        for i, item in enumerate(orcamento.get("itens", []), 1):
            row_bg = "white" if i % 2 == 0 else ModernTheme.BG
            r = tk.Frame(itens_frame, bg=row_bg)
            r.pack(fill=tk.X)
            vals = [
                str(i),
                fmt(item.get("produto_codigo", "")),
                fmt(item.get("produto_nome", ""))[:28],
                str(item.get("quantidade", 1)),
                fmt(item.get("unidade", "UN")),
                fmtm(item.get("preco_unitario", 0)),
                fmtm(item.get("subtotal", 0)),
            ]
            for v, w in zip(vals, widths):
                tk.Label(r, text=v, font=("Segoe UI", 10),
                         bg=row_bg, width=w, anchor="w").pack(
                    side=tk.LEFT, padx=2)

        sep()

        # Totais
        totais = tk.Frame(sf, bg="white")
        totais.pack(fill=tk.X, padx=24, pady=6)

        subtotal = float(orcamento.get("subtotal", 0))
        desconto = float(orcamento.get("desconto", 0))
        total    = float(orcamento.get("total", 0))

        for label, val, color in [
            ("Subtotal:", fmtm(subtotal), ModernTheme.TEXT),
            *(([("Desconto:", f"− {fmtm(desconto)}", ModernTheme.DANGER)]
               if desconto > 0 else [])),
        ]:
            tk.Label(totais, text=f"{label}  {val}",
                     font=("Segoe UI", 12),
                     bg="white", fg=color).pack(anchor="e")

        tk.Label(totais, text=f"TOTAL:  {fmtm(total)}",
                 font=("Segoe UI", 18, "bold"),
                 bg="white", fg=ModernTheme.PRIMARY).pack(anchor="e", pady=(6, 0))
        sep()

        # Condições e status
        lbl(sf, "CONDIÇÕES", 13, True, ModernTheme.PRIMARY, 8)
        for cond in [
            f"• Validade: {fmt(orcamento.get('data_validade', '7 dias'))}",
            "• Preços sujeitos a alteração sem aviso prévio",
            "• Orçamento não tem valor fiscal",
            "• Pagamento conforme condições combinadas",
        ]:
            lbl(sf, cond)

        status = orcamento.get("status", "pendente").upper()
        sc = {"PENDENTE": ModernTheme.WARNING, "APROVADO": ModernTheme.SUCCESS,
              "REJEITADO": ModernTheme.DANGER, "CONVERTIDO": ModernTheme.INFO}
        tk.Frame(sf, bg="white", height=10).pack()
        lbl(sf, f"STATUS: {status}", 14, True, sc.get(status, ModernTheme.CIMENTO),
            10, "center")
        sep()

        # Assinaturas
        ass = tk.Frame(sf, bg="white")
        ass.pack(fill=tk.X, padx=24, pady=20)
        for s in ["Assinatura do Cliente", "Assinatura do Vendedor"]:
            col = tk.Frame(ass, bg="white")
            col.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=20)
            tk.Frame(col, bg=ModernTheme.TEXT, height=1).pack(fill=tk.X, pady=(40, 4))
            tk.Label(col, text=s, font=("Segoe UI", 10),
                     bg="white", fg=ModernTheme.CIMENTO).pack()

        lbl(sf, "Obrigado pela preferência!", 11, False, ModernTheme.CIMENTO, 10, "center")

        # Botões
        btn_frame = tk.Frame(comp, bg="white")
        btn_frame.pack(pady=8)

        for label, color, cmd in [
            ("🖨️ Imprimir",    ModernTheme.PRIMARY, lambda: self._imprimir_texto_widget(sf)),
            ("💾 Salvar HTML", ModernTheme.SUCCESS, lambda: self._salvar_html(orcamento, sf)),
        ]:
            tk.Button(btn_frame, text=label, command=cmd,
                      bg=color, fg="white", bd=0, padx=12, pady=7,
                      font=ModernTheme.FONT_BASE, cursor="hand2").pack(
                side=tk.LEFT, padx=4)

    # ── Auxiliares de impressão ───────────────────────────────────────────────
    def _imprimir_texto(self, text_widget):
        try:
            tmp = os.path.join(os.environ.get("TEMP", "/tmp"), "orcamento.txt")
            with open(tmp, "w", encoding="utf-8") as f:
                f.write(text_widget.get(1.0, tk.END))
            if os.name == "nt":
                os.startfile(tmp, "print")
            else:
                subprocess.run(["lp", tmp])
            messagebox.showinfo("Impressão", "Orçamento enviado para impressora!")
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao imprimir: {e}")

    def _imprimir_texto_widget(self, widget):
        try:
            tmp = os.path.join(os.environ.get("TEMP", "/tmp"), "orcamento_a4.html")
            self._salvar_html({"numero_orcamento": "temp"}, widget)
            messagebox.showinfo("Impressão",
                                "Arquivo HTML gerado! Abra no navegador para imprimir.")
        except Exception as e:
            messagebox.showerror("Erro", f"Erro: {e}")

    def _salvar_arquivo(self, text_widget, nome):
        filename = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Texto", "*.txt"), ("Todos", "*.*")],
            initialfile=f"{nome}.txt"
        )
        if filename:
            with open(filename, "w", encoding="utf-8") as f:
                f.write(text_widget.get(1.0, tk.END))
            messagebox.showinfo("Salvo", f"Salvo em: {filename}")

    def _salvar_html(self, orcamento, parent_widget=None):
        numero   = orcamento.get("numero_orcamento", "000")
        filename = filedialog.asksaveasfilename(
            defaultextension=".html",
            filetypes=[("HTML", "*.html"), ("Todos", "*.*")],
            initialfile=f"orcamento_{numero}.html"
        )
        if not filename:
            return

        def fmt(v, d=""): return str(v) if v is not None else d
        def fmtm(v): return f"R$ {float(v or 0):,.2f}"

        itens = orcamento.get("itens", [])
        itens_html = ""
        for i, item in enumerate(itens, 1):
            bg = "#f8f9fa" if i % 2 == 0 else "#fff"
            itens_html += (
                f'<tr style="background:{bg}">'
                f'<td>{i}</td>'
                f'<td>{fmt(item.get("produto_codigo",""))}</td>'
                f'<td>{fmt(item.get("produto_nome",""))}</td>'
                f'<td style="text-align:center">{item.get("quantidade",1)}</td>'
                f'<td style="text-align:center">{fmt(item.get("unidade","UN"))}</td>'
                f'<td style="text-align:right">{fmtm(item.get("preco_unitario",0))}</td>'
                f'<td style="text-align:right">{fmtm(item.get("subtotal",0))}</td>'
                f'</tr>'
            )

        subtotal = float(orcamento.get("subtotal", 0))
        desconto = float(orcamento.get("desconto", 0))
        total    = float(orcamento.get("total", 0))
        status   = orcamento.get("status", "pendente").upper()
        sc = {"PENDENTE": "#f97316", "APROVADO": "#16a34a",
              "REJEITADO": "#dc2626", "CONVERTIDO": "#2563eb"}
        sc_color = sc.get(status, "#94a3b8")

        html = f"""<!DOCTYPE html>
<html><head><meta charset="UTF-8">
<title>Orçamento {numero}</title>
<style>
  body{{font-family:'Segoe UI',Arial,sans-serif;margin:40px;color:#0f172a}}
  .header{{text-align:center;margin-bottom:24px}}
  .header h1{{color:{ModernTheme.PRIMARY};margin:0;font-size:26px}}
  .header p{{color:#94a3b8;margin:4px 0}}
  .title{{text-align:center;font-size:22px;color:#1e293b;margin:18px 0;
    border-top:2px solid {ModernTheme.PRIMARY};border-bottom:2px solid {ModernTheme.PRIMARY};padding:8px}}
  h3{{color:{ModernTheme.PRIMARY};border-bottom:1px solid #e2e8f0;padding-bottom:4px}}
  table{{width:100%;border-collapse:collapse;margin:12px 0}}
  th{{background:{ModernTheme.PRIMARY};color:white;padding:9px;text-align:left}}
  td{{padding:7px;border-bottom:1px solid #e2e8f0}}
  .total{{font-size:22px;color:{ModernTheme.PRIMARY};font-weight:bold}}
  .status{{text-align:center;font-size:16px;font-weight:bold;color:{sc_color};
    margin:20px 0;padding:10px;border:2px solid {sc_color};border-radius:4px}}
  .sigs{{display:flex;justify-content:space-between;margin-top:60px}}
  .sig{{text-align:center;width:42%}}
  .sig-line{{border-top:1px solid #333;margin-top:50px;padding-top:4px;color:#64748b}}
  .footer{{text-align:center;color:#94a3b8;margin-top:36px;font-size:11px}}
  @media print{{body{{margin:20px}}}}
</style></head><body>
<div class="header">
  <h1>{fmt(LOJA_CONFIG.get('nome'))}</h1>
  <p>{fmt(LOJA_CONFIG.get('endereco'))}</p>
  <p>Tel: {fmt(LOJA_CONFIG.get('telefone'))} | CNPJ: {fmt(LOJA_CONFIG.get('cnpj'))}</p>
</div>
<div class="title">ORÇAMENTO</div>
<p><strong>Número:</strong> {fmt(orcamento.get('numero_orcamento'))} |
   <strong>Emissão:</strong> {datetime.now().strftime('%d/%m/%Y %H:%M')} |
   <strong>Validade:</strong> {fmt(orcamento.get('data_validade','7 dias'))}</p>
<h3>DADOS DO CLIENTE</h3>
<p><strong>Nome:</strong> {fmt(orcamento.get('cliente_nome','Avulso'))}</p>
<p><strong>CPF/CNPJ:</strong> {fmt(orcamento.get('cliente_cpf_cnpj',''))}</p>
<p><strong>Telefone:</strong> {fmt(orcamento.get('cliente_telefone',''))}</p>
<p><strong>Endereço:</strong> {fmt(orcamento.get('cliente_endereco',''))}</p>
<h3>ITENS DO ORÇAMENTO</h3>
<table><tr><th>#</th><th>Código</th><th>Descrição</th>
<th>Qtd</th><th>Un.</th><th>Preço Unit.</th><th>Total</th></tr>
{itens_html}</table>
<div style="text-align:right;margin:16px 0">
  <p>Subtotal: {fmtm(subtotal)}</p>
  {'<p style="color:#dc2626">Desconto: −' + fmtm(desconto) + '</p>' if desconto > 0 else ''}
  <p class="total">TOTAL: {fmtm(total)}</p>
</div>
<h3>CONDIÇÕES</h3>
<p>• Validade: {fmt(orcamento.get('data_validade','7 dias'))}</p>
<p>• Preços sujeitos a alteração sem aviso prévio</p>
<p>• Orçamento não tem valor fiscal</p>
<p>• Pagamento conforme condições combinadas</p>
<div class="status">STATUS: {status}</div>
<div class="sigs">
  <div class="sig"><div class="sig-line">Assinatura do Cliente</div></div>
  <div class="sig"><div class="sig-line">Assinatura do Vendedor</div></div>
</div>
<div class="footer">
  <p>Obrigado pela preferência!</p>
  <p>{fmt(LOJA_CONFIG.get('nome'))} — {datetime.now().year}</p>
</div>
</body></html>"""

        with open(filename, "w", encoding="utf-8") as f:
            f.write(html)

        if os.name == "nt":
            os.startfile(filename)
        messagebox.showinfo("Salvo", f"Orçamento salvo em: {filename}")