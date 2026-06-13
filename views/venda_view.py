"""Tela de Vendas / PDV - FALL Construções (PDF + Status)"""
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from datetime import datetime
from views.base_view import BaseView
from config import ModernTheme, LOJA_CONFIG
import subprocess
import os
import platform

# ═══════════════════════════════════════════════════════════════════
# GERADOR DE PDF - Recibo/Comprovante com Status Badge
# ═══════════════════════════════════════════════════════════════════
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas


class ReciboPDFGenerator:
    """Gera PDF de Recibo/Comprovante de Venda/Orçamento com Status"""

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

    def gerar(self, venda, output_path="recibo.pdf", tipo_documento="VENDA"):
        """Gera o PDF do recibo/comprovante"""
        try:
            if isinstance(venda, dict):
                venda = dict(venda)
                if 'tipo_documento' not in venda:
                    venda['tipo_documento'] = tipo_documento

            c = canvas.Canvas(output_path, pagesize=A4)
            numero_doc = self._safe_str(self._get_val(venda, 'numero', 'numero_venda'), '000')
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
        numero_doc = self._safe_str(self._get_val(venda, 'numero', 'numero_venda'), '000')
        self._text_center(c, cx, cy, f"Nº {numero_doc}", size=12, bold=True)
        cy -= 4 * mm
        self._text_center(c, cx, cy, "DOCUMENTO NÃO FISCAL", size=8)

        # STATUS BADGE
        status = self._safe_str(self._get_val(venda, 'status'), 'PAGO').upper()
        tipo_doc = self._safe_str(self._get_val(venda, 'tipo_documento'), 'VENDA').upper()

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
        numero = self._safe_str(self._get_val(venda, 'numero', 'numero_venda'), '---')
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

class VendaView(BaseView):
    def __init__(self, parent, controllers):
        super().__init__(parent, None)
        self.controllers = controllers
        self.venda_atual = None
        self.itens_venda = []
        self.desconto_percentual = 0.0
        self.desconto_valor = 0.0
        self.build()

    def build(self):
        self.frame = tk.Frame(self.parent, bg=ModernTheme.BG)

        # ── Layout principal (esq / dir) ──────────────────────────────────────
        main = tk.Frame(self.frame, bg=ModernTheme.BG)
        main.pack(fill=tk.BOTH, expand=True, padx=16, pady=(0, 16))

        # ── COLUNA ESQUERDA – SEM SCROLL (ORIGINAL) ───────────────────────────
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

        # ── COLUNA DIREITA – RESUMO COM BOTÃO FIXO NO BOTTOM ──────────────────
        right = tk.Frame(main, bg=ModernTheme.CARD_BG,
                         highlightbackground=ModernTheme.BORDER,
                         highlightthickness=1, width=320)
        right.pack(side=tk.RIGHT, fill=tk.Y, padx=(12, 0))
        right.pack_propagate(False)

        tk.Frame(right, bg=ModernTheme.PRIMARY, height=4).pack(fill=tk.X)

        # Container principal da direita com grid para botão fixo no bottom
        right_container = tk.Frame(right, bg=ModernTheme.CARD_BG)
        right_container.pack(fill=tk.BOTH, expand=True)
        right_container.grid_rowconfigure(0, weight=1)  # conteúdo expande
        right_container.grid_rowconfigure(1, weight=0)  # botão fixo
        right_container.grid_columnconfigure(0, weight=1)

        # ── Área scrollable (conteúdo do resumo) ─────────────────────────────
        scroll_area = tk.Frame(right_container, bg=ModernTheme.CARD_BG)
        scroll_area.grid(row=0, column=0, sticky="nsew")

        # Canvas para scroll do conteúdo
        content_canvas = tk.Canvas(scroll_area, bg=ModernTheme.CARD_BG, highlightthickness=0)
        content_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        content_scroll = ttk.Scrollbar(scroll_area, orient=tk.VERTICAL, command=content_canvas.yview)
        content_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        content_canvas.configure(yscrollcommand=content_scroll.set)

        resumo_content = tk.Frame(content_canvas, bg=ModernTheme.CARD_BG)
        content_window = content_canvas.create_window((0, 0), window=resumo_content, anchor=tk.NW)

        def _on_resumo_configure(event=None):
            content_canvas.configure(scrollregion=content_canvas.bbox("all"))
        resumo_content.bind("<Configure>", _on_resumo_configure)

        def _on_content_canvas_configure(event):
            content_canvas.itemconfig(content_window, width=event.width)
        content_canvas.bind("<Configure>", _on_content_canvas_configure)

        # Mouse wheel para o conteúdo scrollable
        def _on_content_mousewheel(event):
            content_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        def _bind_content_wheel(widget):
            widget.bind("<MouseWheel>", _on_content_mousewheel)
            widget.bind("<Button-4>", lambda e: content_canvas.yview_scroll(-1, "units"))
            widget.bind("<Button-5>", lambda e: content_canvas.yview_scroll(1, "units"))
            for child in widget.winfo_children():
                _bind_content_wheel(child)
        _bind_content_wheel(resumo_content)

        # Padding interno do conteúdo
        inner_pad = tk.Frame(resumo_content, bg=ModernTheme.CARD_BG)
        inner_pad.pack(fill=tk.BOTH, expand=True, padx=20, pady=16)

        tk.Label(inner_pad, text="🧾  RESUMO DA VENDA",
                 font=("Segoe UI", 12, "bold"),
                 bg=ModernTheme.CARD_BG, fg=ModernTheme.PRIMARY).pack(anchor=tk.W, pady=(0, 12))

        # Número da venda
        self.numero_label = tk.Label(inner_pad, text="Nº: —",
                                     font=("Segoe UI", 11),
                                     bg=ModernTheme.CARD_BG, fg=ModernTheme.TEXT_MUTED)
        self.numero_label.pack(anchor=tk.W)

        # Cliente
        self.cliente_nota_label = tk.Label(inner_pad, text="Cliente: Consumidor Final",
                                           font=("Segoe UI", 10),
                                           bg=ModernTheme.CARD_BG, fg=ModernTheme.TEXT_MUTED)
        self.cliente_nota_label.pack(anchor=tk.W, pady=(0, 16))

        # Subtotal
        tk.Label(inner_pad, text="SUBTOTAL",
                 font=("Segoe UI", 9, "bold"),
                 bg=ModernTheme.CARD_BG, fg=ModernTheme.TEXT_MUTED).pack(anchor=tk.W)
        self.subtotal_label = tk.Label(inner_pad, text="R$ 0,00",
                                       font=("Segoe UI", 20, "bold"),
                                       bg=ModernTheme.CARD_BG, fg=ModernTheme.TEXT)
        self.subtotal_label.pack(anchor=tk.W, pady=(0, 10))

        # Desconto
        tk.Label(inner_pad, text="DESCONTO",
                 font=("Segoe UI", 9, "bold"),
                 bg=ModernTheme.CARD_BG, fg=ModernTheme.TEXT_MUTED).pack(anchor=tk.W)
        self.desconto_label = tk.Label(inner_pad, text="R$ 0,00 (0%)",
                                       font=("Segoe UI", 16, "bold"),
                                       bg=ModernTheme.CARD_BG, fg=ModernTheme.DANGER)
        self.desconto_label.pack(anchor=tk.W, pady=(0, 10))

        # Separador
        tk.Frame(inner_pad, bg=ModernTheme.BORDER, height=2).pack(
            fill=tk.X, pady=12)

        # TOTAL
        tk.Label(inner_pad, text="TOTAL A PAGAR",
                 font=("Segoe UI", 10, "bold"),
                 bg=ModernTheme.CARD_BG, fg=ModernTheme.PRIMARY).pack(anchor=tk.W)
        self.total_label = tk.Label(inner_pad, text="R$ 0,00",
                                    font=("Segoe UI", 36, "bold"),
                                    bg=ModernTheme.CARD_BG, fg=ModernTheme.SUCCESS)
        self.total_label.pack(anchor=tk.W, pady=(0, 16))

        # Forma de pagamento
        tk.Label(inner_pad, text="FORMA DE PAGAMENTO",
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
            tk.Radiobutton(inner_pad, text=text,
                           variable=self.pagamento_var, value=val,
                           bg=ModernTheme.CARD_BG, fg=ModernTheme.TEXT,
                           font=("Segoe UI", 10),
                           selectcolor=ModernTheme.CARD_BG,
                           activebackground=ModernTheme.CARD_BG).pack(
                anchor=tk.W, pady=2)

        # Separador
        tk.Frame(inner_pad, bg=ModernTheme.BORDER, height=2).pack(
            fill=tk.X, pady=14)

        # ── Botão Finalizar – FIXO no bottom, NUNCA some ──────────────────────
        btn_frame = tk.Frame(right_container, bg=ModernTheme.CARD_BG)
        btn_frame.grid(row=1, column=0, sticky="sew", padx=20, pady=(0, 16))

        btn_fin = tk.Button(btn_frame, text="✔  FINALIZAR VENDA",
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
        """Gera PDF profissional da venda e abre automaticamente"""
        try:
            venda = self.controllers["venda"].obter_venda(venda_id)
            if not venda:
                messagebox.showwarning("Aviso", "Venda não encontrada.")
                return

            # Garante que tem itens
            if not venda.get("itens") and self.itens_venda:
                venda["itens"] = self.itens_venda

            # Adiciona dados do cliente se disponível
            if not venda.get("cliente_nome") and cliente_id:
                cliente = self.controllers["venda"].obter_cliente(cliente_id)
                if cliente:
                    venda["cliente_nome"] = cliente.get("nome")
                    venda["cpf_cnpj"] = cliente.get("cpf_cnpj")

            # Diretório seguro
            import tempfile
            temp_dir = tempfile.gettempdir()
            pdf_path = os.path.join(temp_dir, f"venda_{venda.get('numero', '000')}.pdf")
            pdf_path = os.path.normpath(pdf_path)

            Logger.log(f"Gerando PDF em: {pdf_path}", "INFO")

            # Gera PDF com status
            gerador = ReciboPDFGenerator(LOJA_CONFIG)
            gerador.gerar(venda, output_path=pdf_path, tipo_documento="VENDA")

            if os.path.exists(pdf_path) and os.path.getsize(pdf_path) > 0:
                Logger.log(f"PDF criado: {pdf_path}", "SUCCESS")

                # Abre PDF
                try:
                    if os.name == "nt":
                        os.startfile(pdf_path)
                except Exception as e2:
                    Logger.log(f"Não abriu: {e2}", "WARNING")

                messagebox.showinfo(
                    "PDF Gerado",
                    f"Venda salva em PDF!\n\nArquivo: {os.path.basename(pdf_path)}\nLocal: {temp_dir}"
                )
            else:
                raise Exception("PDF não foi criado")

        except Exception as e:
            Logger.log(f"Erro PDF: {e}", "ERROR")
            import traceback
            traceback.print_exc()
            messagebox.showerror(
                "Erro",
                f"Não foi possível gerar PDF.\n\n{e}\n\nVerifique: pip install reportlab"
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