"""Histórico de Vendas - FALL Construcoes (PDF + Status)"""
import tkinter as tk
from tkinter import ttk, messagebox
import subprocess, os, platform
from datetime import datetime
from views.base_view import BaseView
from config import ModernTheme, LOJA_CONFIG

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
        status = self._safe_str(self._get_val(venda, 'status'), 'PENDENTE').upper()
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

class HistoricoVendasView(BaseView):
    def __init__(self, parent, controllers):
        super().__init__(parent, None)
        self.controllers = controllers
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
        """Gera PDF profissional da venda e abre automaticamente"""
        try:
            venda = self.controllers["venda"].obter_venda(venda_id)
            if not venda:
                messagebox.showwarning("Aviso", "Venda não encontrada.")
                return

            # Garante que tem itens
            if not venda.get("itens"):
                vd = self.controllers["venda"].obter_venda(venda_id)
                if vd and vd.get("itens"):
                    venda["itens"] = vd["itens"]

            # Diretório seguro
            import tempfile
            temp_dir = tempfile.gettempdir()
            pdf_path = os.path.join(temp_dir, f"venda_{venda.get('numero_venda', '000')}.pdf")
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

        if False:  # DANFE removido, usar ReciboPDFGenerator
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

        if False:  # DANFE removido, usar ReciboPDFGenerator
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
        """Fallback: gera PDF ao invés de comprovante texto"""
        self._escolher_tipo_comprovante(venda.get("id"))
