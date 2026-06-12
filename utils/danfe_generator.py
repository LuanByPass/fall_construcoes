"""
Gerador de DANFE (Documento Auxiliar da Nota Fiscal Eletrônica)
Para PDV / Sistema de Vendas - Layout profissional estilo SEFAZ
Usa ReportLab canvas direto para máximo controle do layout
VERSÃO CORRIGIDA V2 - Resolve "list index out of range" e barcode
"""
import os
import tempfile
import traceback
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from reportlab.graphics.barcode import code128
from reportlab.graphics.barcode import createBarcodeDrawing
from reportlab.graphics.shapes import Drawing
from reportlab.graphics import renderPDF
from reportlab.lib.utils import ImageReader


class DanfeGenerator:
    """Gera PDF de Nota Fiscal estilo DANFE para PDV usando canvas direto"""

    def __init__(self, loja_config):
        self.loja_config = loja_config
        self.page_width, self.page_height = A4
        self.margin = 10 * mm

    def gerar(self, venda, output_path="danfe.pdf"):
        """Gera o PDF DANFE da venda com tratamento de erro completo"""
        try:
            c = canvas.Canvas(output_path, pagesize=A4)
            c.setTitle(f"DANFE - Venda {venda.get('numero', '000')}")

            y = self.page_height - self.margin

            # === CABEÇALHO DANFE ===
            y = self._draw_header(c, venda, y)
            y -= 4 * mm

            # === DADOS DO EMITENTE ===
            y = self._draw_emitente(c, y)
            y -= 4 * mm

            # === DADOS DO DESTINATÁRIO ===
            y = self._draw_destinatario(c, venda, y)
            y -= 4 * mm

            # === CÁLCULO DO IMPOSTO ===
            y = self._draw_impostos(c, venda, y)
            y -= 4 * mm

            # === TRANSPORTADOR ===
            y = self._draw_transporte(c, y)
            y -= 4 * mm

            # === PRODUTOS / SERVIÇOS ===
            y = self._draw_produtos(c, venda, y)
            y -= 4 * mm

            # === DADOS ADICIONAIS ===
            self._draw_dados_adicionais(c, venda, y)

            c.save()
            return output_path
        except Exception as e:
            # Log detalhado para debug
            print(f"[DANFE] ERRO ao gerar PDF: {e}")
            traceback.print_exc()
            raise

    # ─────────────────────────────────────────────────────────────
    # HELPERS DE DESENHO
    # ─────────────────────────────────────────────────────────────

    def _rect(self, c, x, y, w, h, stroke=1, fill=0):
        """Desenha retângulo"""
        c.rect(x, y - h, w, h, stroke=stroke, fill=fill)

    def _line(self, c, x1, y1, x2, y2):
        """Desenha linha"""
        c.line(x1, y1, x2, y2)

    def _text(self, c, x, y, text, font="Helvetica", size=8, bold=False):
        """Desenha texto"""
        if bold:
            font = font + "-Bold"
        c.setFont(font, size)
        c.drawString(x, y, str(text))

    def _text_right(self, c, x, y, text, font="Helvetica", size=8, bold=False):
        """Desenha texto alinhado à direita"""
        if bold:
            font = font + "-Bold"
        c.setFont(font, size)
        tw = c.stringWidth(str(text), font, size)
        c.drawString(x - tw, y, str(text))

    def _text_center(self, c, x, y, text, font="Helvetica", size=8, bold=False):
        """Desenha texto centralizado"""
        if bold:
            font = font + "-Bold"
        c.setFont(font, size)
        tw = c.stringWidth(str(text), font, size)
        c.drawString(x - tw / 2, y, str(text))

    def _label(self, c, x, y, text, size=6):
        """Label pequeno em cinza"""
        c.setFillColorRGB(0.3, 0.3, 0.3)
        c.setFont("Helvetica-Bold", size)
        c.drawString(x, y, str(text))
        c.setFillColorRGB(0, 0, 0)

    def _label_value(self, c, x, y, label, value, label_size=6, value_size=8, value_bold=False):
        """Label + valor empilhados"""
        self._label(c, x, y, label, label_size)
        font = "Helvetica-Bold" if value_bold else "Helvetica"
        c.setFont(font, value_size)
        c.drawString(x, y - value_size - 1, str(value))

    def _hline(self, c, x, y, w):
        """Linha horizontal"""
        c.setStrokeColorRGB(0, 0, 0)
        c.setLineWidth(0.5)
        c.line(x, y, x + w, y)

    def _vline(self, c, x, y, h):
        """Linha vertical"""
        c.setStrokeColorRGB(0, 0, 0)
        c.setLineWidth(0.5)
        c.line(x, y, x, y - h)

    # ─────────────────────────────────────────────────────────────
    # BARCODE 100% SEGURO (CORREÇÃO PRINCIPAL)
    # ─────────────────────────────────────────────────────────────

    def _draw_barcode_safe(self, c, x, y, chave, max_width=100*mm, height=12*mm):
        """
        Desenha barcode Code128 de forma 100% segura.
        Evita COMPLETAMENTE o erro:
        "Can only add Shape or UserNode objects to a Group"
        """
        # Normaliza chave: Code128 aceita alfanumérico
        chave_clean = ''.join(ch for ch in str(chave) if ch.isalnum())
        if not chave_clean:
            chave_clean = "000000000000"

        # ─── Método 1: createBarcodeDrawing (retorna Drawing válido) ───
        try:
            d = createBarcodeDrawing(
                'Code128',
                value=chave_clean,
                barHeight=height * 0.75,
                barWidth=0.5,          # em pontos (~0.176 mm)
                humanReadable=False
            )
            # Ajusta escala se o drawing for maior que o espaço disponível
            scale_x = 1.0
            if hasattr(d, 'width') and d.width > max_width:
                scale_x = max_width / float(d.width)
            if scale_x < 1.0:
                d.scale(scale_x, scale_x)
            renderPDF.draw(d, c, x, y - height + 2*mm)
            return True
        except Exception as e:
            print(f"[DANFE] createBarcodeDrawing falhou: {e}")

        # ─── Método 2: Flowable drawOn direto (sem Drawing) ───
        try:
            barcode = code128.Code128(
                chave_clean,
                barHeight=height * 0.75,
                barWidth=0.5,
                humanReadable=False
            )
            barcode.drawOn(c, x, y - height + 2*mm)
            return True
        except Exception as e:
            print(f"[DANFE] Barcode drawOn falhou: {e}")

        # ─── Fallback 3: texto monoespaçado (nunca quebra) ───
        try:
            c.setFont("Courier-Bold", 7)
            c.drawString(x, y - height/2, f"CHAVE ACESSO: {chave_clean}")
            return False
        except Exception:
            return False

    # ─────────────────────────────────────────────────────────────
    # SEÇÕES DO DANFE
    # ─────────────────────────────────────────────────────────────

    def _draw_header(self, c, venda, y_start):
        """Cabeçalho DANFE + código de barras + chave de acesso"""
        x = self.margin
        y = y_start
        w_total = self.page_width - 2 * self.margin
        h = 42 * mm
        w_left = 65 * mm
        w_right = w_total - w_left - 1 * mm

        # Fundo cinza claro
        c.setFillColorRGB(0.95, 0.95, 0.95)
        c.rect(x, y - h, w_total, h, stroke=0, fill=1)
        c.setFillColorRGB(0, 0, 0)

        # Borda externa
        c.setLineWidth(1)
        c.rect(x, y - h, w_total, h, stroke=1, fill=0)

        # Divisão esquerda/direita
        c.setLineWidth(0.5)
        c.line(x + w_left, y, x + w_left, y - h)

        # === COLUNA ESQUERDA: DANFE ===
        cx = x + w_left / 2
        cy = y - 6 * mm
        self._text_center(c, cx, cy, "DANFE", size=14, bold=True)
        cy -= 5 * mm
        self._text_center(c, cx, cy, "Documento Auxiliar da", size=7)
        cy -= 3.5 * mm
        self._text_center(c, cx, cy, "Nota Fiscal Eletrônica", size=7)
        cy -= 6 * mm
        self._text_center(c, cx, cy, "0 - ENTRADA    1 - SAÍDA", size=7, bold=True)
        cy -= 6 * mm
        numero_venda = str(venda.get('numero', '000'))[:8]
        self._text_center(c, cx, cy, f"Nº {numero_venda}", size=10, bold=True)
        cy -= 5 * mm
        self._text_center(c, cx, cy, f"Série {venda.get('serie', '001')}", size=9, bold=True)
        cy -= 4 * mm
        self._text_center(c, cx, cy, "Folha 1/1", size=7)

        # === COLUNA DIREITA: CONTROLE DO FISCO ===
        rx = x + w_left + 2 * mm
        ry = y - 5 * mm
        self._text(c, rx, ry, "CONTROLE DO FISCO", size=7, bold=True)

        # Código de barras (VERSÃO CORRIGIDA - sem Drawing.add())
        ry -= 4 * mm
        chave = venda.get('chave_acesso', self._gerar_chave_mock(venda))
        self._draw_barcode_safe(c, rx, ry, chave, max_width=w_right - 4*mm, height=12*mm)

        ry -= 14 * mm
        self._text(c, rx, ry, "CHAVE DE ACESSO", size=6, bold=True)
        ry -= 4 * mm
        chave_formatada = self._format_chave(chave)
        if len(chave_formatada) > 60:
            chave_formatada = chave_formatada[:57] + "..."
        self._text(c, rx, ry, chave_formatada, size=6, bold=True)
        ry -= 5 * mm
        self._text(c, rx, ry, "Consulta de autenticidade no portal nacional da NF-e", size=6)
        ry -= 3.5 * mm
        self._text(c, rx, ry, "www.nfe.fazenda.gov.br/portal", size=6)

        return y - h

    def _draw_emitente(self, c, y_start):
        """Dados do emitente (empresa)"""
        x = self.margin
        y = y_start
        w = self.page_width - 2 * self.margin
        h = 22 * mm

        c.setLineWidth(1)
        c.rect(x, y - h, w, h, stroke=1, fill=0)

        # Linha divisória horizontal
        c.setLineWidth(0.5)
        c.line(x, y - h / 2, x + w, y - h / 2)

        # Linhas verticais
        col1 = x + w * 0.50
        col2 = x + w * 0.75
        c.line(col1, y, col1, y - h / 2)
        c.line(col2, y, col2, y - h / 2)

        # Linha inferior vertical
        col3 = x + w * 0.50
        col4 = x + w * 0.75
        c.line(col3, y - h / 2, col3, y - h)
        c.line(col4, y - h / 2, col4, y - h)

        # Labels e valores - linha 1
        ly = y - 4 * mm
        self._label_value(c, x + 2 * mm, ly, "NOME / RAZÃO SOCIAL",
                          self.loja_config.get('nome', 'FALL CONSTRUÇÕES'))
        self._label_value(c, col1 + 2 * mm, ly, "CNPJ",
                          self.loja_config.get('cnpj', '57.839.618/0001-67'))
        self._label_value(c, col2 + 2 * mm, ly, "INSCRIÇÃO ESTADUAL",
                          self.loja_config.get('ie', 'ISENTO'))

        # Labels e valores - linha 2
        ly2 = y - h / 2 - 4 * mm
        self._label_value(c, x + 2 * mm, ly2, "ENDEREÇO",
                          self.loja_config.get('endereco', 'Av. Dom Helder Câmara, 3691 - Vale Quem Tem'))
        self._label_value(c, col3 + 2 * mm, ly2, "MUNICÍPIO",
                          self.loja_config.get('cidade', 'Teresina'))
        self._label_value(c, col4 + 2 * mm, ly2, "UF",
                          self.loja_config.get('uf', 'PI'))

        return y - h

    def _draw_destinatario(self, c, venda, y_start):
        """Dados do destinatário (cliente)"""
        x = self.margin
        y = y_start
        w = self.page_width - 2 * self.margin
        h = 28 * mm

        c.setLineWidth(1)
        c.rect(x, y - h, w, h, stroke=1, fill=0)

        # Divisões
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

        # Linha 1
        ly = y - 4 * mm
        cliente_nome = venda.get('cliente_nome', 'Consumidor Final')
        if len(cliente_nome) > 35:
            cliente_nome = cliente_nome[:32] + "..."
        cpf_cnpj = venda.get('cpf_cnpj', '')
        data_venda = venda.get('data_venda', datetime.now())
        if isinstance(data_venda, datetime):
            data_str = data_venda.strftime('%d/%m/%Y')
        else:
            data_str = str(data_venda)[:10]

        self._label_value(c, x + 2 * mm, ly, "NOME / RAZÃO SOCIAL", cliente_nome)
        self._label_value(c, col1 + 2 * mm, ly, "CNPJ / CPF", cpf_cnpj if cpf_cnpj else "---")
        self._label_value(c, col2 + 2 * mm, ly, "DATA DA EMISSÃO", data_str)

        # Linha 2
        ly2 = y - h / 3 - 4 * mm
        endereco = venda.get('cliente_endereco', 'Não informado')
        if len(endereco) > 45:
            endereco = endereco[:42] + "..."
        cidade = venda.get('cliente_cidade', 'Não informado')
        uf = venda.get('cliente_uf', self.loja_config.get('uf', 'PI'))

        self._label_value(c, x + 2 * mm, ly2, "ENDEREÇO", endereco)
        self._label_value(c, col3 + 2 * mm, ly2, "MUNICÍPIO", cidade)
        self._label_value(c, col4 + 2 * mm, ly2, "UF", uf)
        self._label_value(c, col5 + 2 * mm, ly2, "INSCRIÇÃO ESTADUAL", "---")

        # Linha 3
        ly3 = y - 2 * h / 3 - 4 * mm
        if isinstance(data_venda, datetime):
            hora_str = data_venda.strftime('%H:%M:%S')
        else:
            hora_str = ""
        self._label_value(c, x + 2 * mm, ly3, "DATA DA SAÍDA", data_str)
        self._label_value(c, col3 + 2 * mm, ly3, "HORA DA SAÍDA", hora_str)
        self._label_value(c, col4 + 2 * mm, ly3, "INSCRIÇÃO ESTADUAL DO SUBST. TRIB.", "---")
        self._label_value(c, col5 + 2 * mm, ly3, "CNPJ", "---")

        return y - h

    def _draw_impostos(self, c, venda, y_start):
        """Cálculo do imposto"""
        x = self.margin
        y = y_start
        w = self.page_width - 2 * self.margin
        h = 24 * mm

        c.setLineWidth(1)
        c.rect(x, y - h, w, h, stroke=1, fill=0)

        c.setLineWidth(0.5)
        c.line(x, y - h / 2, x + w, y - h / 2)

        # 7 colunas na linha superior, 7 na inferior
        cols = [x + w * i / 7 for i in range(1, 7)]
        for cx in cols:
            c.line(cx, y, cx, y - h / 2)
            c.line(cx, y - h / 2, cx, y - h)

        total = float(venda.get('total', 0))
        subtotal = float(venda.get('subtotal', 0))
        desconto = float(venda.get('desconto', 0))
        icms = total * 0.18
        ipi = total * 0.05

        labels_linha1 = [
            "BASE DE CÁLCULO ICMS", "VALOR ICMS", "BASE DE CÁLC. ICMS ST",
            "VALOR ICMS SUBST.", "VALOR IMP. IMPORTAÇÃO", "VALOR IPI",
            "VALOR TOTAL PRODUTOS"
        ]
        valores_linha1 = [
            f"R$ {subtotal:.2f}", f"R$ {icms:.2f}", "0,00", "0,00",
            "0,00", f"R$ {ipi:.2f}", f"R$ {subtotal:.2f}"
        ]

        labels_linha2 = [
            "VALOR DO FRETE", "VALOR DO SEGURO", "DESCONTO",
            "OUTRAS DESPESAS", "VALOR TOTAL IPI", "VALOR APROX. TRIBUTOS",
            "VALOR TOTAL DA NOTA"
        ]
        valores_linha2 = [
            "0,00", "0,00", f"R$ {desconto:.2f}", "0,00",
            f"R$ {ipi:.2f}", f"R$ {(icms + ipi):.2f}", f"R$ {total:.2f}"
        ]

        # Desenha linha 1
        ly = y - 4 * mm
        col_w = w / 7
        for i, (lab, val) in enumerate(zip(labels_linha1, valores_linha1)):
            cx = x + i * col_w + 2 * mm
            self._label(c, cx, ly, lab, 5)
            c.setFont("Helvetica-Bold" if i == 6 else "Helvetica", 7)
            c.drawString(cx, ly - 8, val)

        # Desenha linha 2
        ly2 = y - h / 2 - 4 * mm
        for i, (lab, val) in enumerate(zip(labels_linha2, valores_linha2)):
            cx = x + i * col_w + 2 * mm
            self._label(c, cx, ly2, lab, 5)
            c.setFont("Helvetica-Bold" if i == 6 else "Helvetica", 7)
            c.drawString(cx, ly2 - 8, val)

        # Destaque amarelo no total
        c.setFillColorRGB(1, 1, 0.8)
        c.rect(x + 6 * col_w, y - h / 2, col_w, h / 2, stroke=0, fill=1)
        c.setFillColorRGB(0, 0, 0)
        c.setFont("Helvetica-Bold", 7)
        c.drawString(x + 6 * col_w + 2 * mm, ly2 - 8, valores_linha2[6])

        return y - h

    def _draw_transporte(self, c, y_start):
        """Transportador / Volumes Transportados"""
        x = self.margin
        y = y_start
        w = self.page_width - 2 * self.margin
        h = 22 * mm

        c.setLineWidth(1)
        c.rect(x, y - h, w, h, stroke=1, fill=0)

        c.setLineWidth(0.5)
        c.line(x, y - h / 2, x + w, y - h / 2)

        col1 = x + w * 0.35
        col2 = x + w * 0.50
        col3 = x + w * 0.65
        col4 = x + w * 0.80
        col5 = x + w * 0.90
        c.line(col1, y, col1, y - h / 2)
        c.line(col2, y, col2, y - h / 2)
        c.line(col3, y, col3, y - h / 2)
        c.line(col4, y, col4, y - h / 2)
        c.line(col5, y, col5, y - h / 2)

        c.line(col1, y - h / 2, col1, y - h)
        c.line(col2, y - h / 2, col2, y - h)
        c.line(col3, y - h / 2, col3, y - h)
        c.line(col4, y - h / 2, col4, y - h)
        c.line(col5, y - h / 2, col5, y - h)

        # Linha 1
        ly = y - 4 * mm
        labels1 = ["NOME / RAZÃO SOCIAL", "FRETE POR CONTA", "CÓDIGO ANTT",
                   "PLACA DO VEÍCULO", "UF", "CNPJ / CPF"]
        for i, lab in enumerate(labels1):
            cx = x + i * (w / 6) + 2 * mm
            self._label(c, cx, ly, lab, 5)
            c.setFont("Helvetica", 7)
            c.drawString(cx, ly - 8, "---")

        # Linha 2
        ly2 = y - h / 2 - 4 * mm
        labels2 = ["ENDEREÇO", "MUNICÍPIO", "UF", "INSCRIÇÃO ESTADUAL",
                   "QUANTIDADE", "ESPÉCIE"]
        for i, lab in enumerate(labels2):
            cx = x + i * (w / 6) + 2 * mm
            self._label(c, cx, ly2, lab, 5)
            c.setFont("Helvetica", 7)
            c.drawString(cx, ly2 - 8, "---")

        return y - h

    def _draw_produtos(self, c, venda, y_start):
        """Tabela de produtos / serviços - VERSÃO FINAL COM COLUNAS AJUSTADAS"""
        x = self.margin
        y = y_start
        w = self.page_width - 2 * self.margin

        itens = venda.get("itens", [])
        if not itens:
            itens = []

        row_height = 6 * mm
        header_height = 10 * mm  # Aumentado para caber headers de 2 linhas
        h = header_height + len(itens) * row_height + 2 * mm
        if h < 30 * mm:
            h = 30 * mm

        c.setLineWidth(1)
        c.rect(x, y - h, w, h, stroke=1, fill=0)

        # Fundo cinza do header
        c.setFillColorRGB(0.9, 0.9, 0.9)
        c.rect(x, y - header_height, w, header_height, stroke=0, fill=1)
        c.setFillColorRGB(0, 0, 0)

        # ════════════════════════════════════════════════════════════
        # CORREÇÃO 1: Definir 14 colunas com 15 posições X (início + fim de cada)
        # ════════════════════════════════════════════════════════════
        # Colunas: CÓD(18), DESC(57), NCM(15), CST(10), CFOP(12), UN(10), 
        #          QTD(12), V.UNIT(14), V.TOTAL(14), BC.ICMS(12), V.ICMS(12), 
        #          IPI(10), ALQ.ICMS(10), ALQ.IPI(10+)
        # ════════════════════════════════════════════════════════════
        # COLUNAS REDIMENSIONADAS - Total = 190mm (largura útil A4)
        # ════════════════════════════════════════════════════════════
        cols_x = [
            x,                    # 0 - início
            x + 15 * mm,          # 1 - CÓD (15mm)
            x + 65 * mm,          # 2 - DESC (50mm)
            x + 77 * mm,          # 3 - NCM (12mm)
            x + 87 * mm,          # 4 - CST (10mm)
            x + 97 * mm,          # 5 - CFOP (10mm)
            x + 105 * mm,         # 6 - UN (8mm)
            x + 115 * mm,         # 7 - QTD (10mm)
            x + 127 * mm,         # 8 - V.UNIT (12mm)
            x + 139 * mm,         # 9 - V.TOTAL (12mm)
            x + 150 * mm,         # 10 - BC.ICMS (11mm)
            x + 161 * mm,         # 11 - V.ICMS (11mm)
            x + 170 * mm,         # 12 - IPI (9mm)
            x + 180 * mm,         # 13 - ALQ.ICMS (10mm)
            x + w                 # 14 - ALQ.IPI / fim (10mm)
        ]
        # Agora cols_x tem 15 posições (0 a 14), suficiente para 14 colunas

        c.setLineWidth(0.5)
        # Desenha linhas verticais entre colunas (do 1 ao 13, o 14 é a borda)
        for cx in cols_x[1:-1]:
            c.line(cx, y, cx, y - h)

        c.line(x, y - header_height, x + w, y - header_height)

        # ════════════════════════════════════════════════════════════
        # CORREÇÃO 2: Headers com exatamente 14 elementos
        # ════════════════════════════════════════════════════════════
        headers = [
            ("CÓDIGO\nPRODUTO", 2),
            ("DESCRIÇÃO DO PRODUTO / SERVIÇO", 1),
            ("NCM/SH", 1),
            ("CST", 1),
            ("CFOP", 1),
            ("UN", 1),
            ("QUANT.", 1),
            ("VALOR\nUNIT.", 2),
            ("VALOR\nTOTAL", 2),
            ("BC\nICMS", 2),
            ("VALOR\nICMS", 2),
            ("IPI", 1),
            ("ALÍQ.\nICMS", 2),
            ("ALÍQ.\nIPI", 2)
        ]
        # 14 headers para 14 colunas ✓

        # Desenha headers - CORREÇÃO 3: verifica limites antes de acessar
        for i, (h_text, n_lines) in enumerate(headers):
            # Garante que i está dentro de cols_x
            if i >= len(cols_x) - 1:
                break  # Evita index out of range

            cx = cols_x[i] + 1 * mm
            lines = h_text.split("\n")
            # Centraliza verticalmente no header
            start_y = y - 2.5 * mm
            for j, line in enumerate(lines):
                c.setFont("Helvetica-Bold", 5)
                c.drawString(cx, start_y - j * 3.5 * mm, line)

        # Itens
        c.setFont("Helvetica", 5.5)
        for idx, item in enumerate(itens):
            iy = y - header_height - (idx + 1) * row_height + 2 * mm
            nome = (item.get("produto_nome") or item.get("nome") or "Item")[:35]
            codigo = item.get("codigo", "---")
            qtd = item.get("quantidade", 1)
            preco = float(item.get("preco_unitario", item.get("preco", 0)))
            total_item = float(item.get("subtotal", preco * qtd))
            icms_item = total_item * 0.18

            vals = [
                str(codigo)[:8], nome[:30],  # Código + Descrição (reduzido para caber)
                "---", "102", "5102", "UN",  # NCM, CST, CFOP, UN
                str(qtd), f"{preco:.2f}", f"{total_item:.2f}",  # QTD, V.Unit, V.Total
                f"{total_item:.2f}", f"{icms_item:.2f}", "0.00", "18.00", "0.00"  # BC ICMS, V.ICMS, IPI, ALQ.ICMS, ALQ.IPI
            ]
            # 14 valores para 14 colunas ✓

            for i, val in enumerate(vals):
                # ════════════════════════════════════════════════════
                # CORREÇÃO 4: Verificação segura de índices
                # ════════════════════════════════════════════════════
                if i >= len(cols_x) - 1:
                    break  # Evita index out of range

                cx = cols_x[i] + 1 * mm

                # CORREÇÃO 5: Cálculo seguro da largura da coluna
                if i + 1 < len(cols_x):
                    col_w = cols_x[i + 1] - cols_x[i]
                else:
                    col_w = w - (cols_x[i] - x)

                # Alinha números à direita (colunas 6 em diante)
                if i >= 6:
                    tw = c.stringWidth(val, "Helvetica", 6)
                    # CORREÇÃO 6: Garante que não ultrapassa a coluna
                    draw_x = min(cx + col_w - tw - 2 * mm, cx + col_w - 2 * mm)
                    c.drawString(draw_x, iy, val)
                else:
                    c.drawString(cx, iy, val)

            # Linha horizontal entre itens
            c.setLineWidth(0.3)
            c.line(x, y - header_height - (idx + 1) * row_height, 
                   x + w, y - header_height - (idx + 1) * row_height)

        return y - h

    def _draw_dados_adicionais(self, c, venda, y_start):
        """Dados adicionais e informações complementares"""
        x = self.margin
        y = y_start
        w = self.page_width - 2 * self.margin
        h = 20 * mm

        c.setLineWidth(1)
        c.rect(x, y - h, w, h, stroke=1, fill=0)

        c.setLineWidth(0.5)
        c.line(x + w * 0.65, y, x + w * 0.65, y - h)

        # Fundo cinza dos títulos
        c.setFillColorRGB(0.9, 0.9, 0.9)
        c.rect(x, y - 5 * mm, w * 0.65, 5 * mm, stroke=0, fill=1)
        c.rect(x + w * 0.65, y - 5 * mm, w * 0.35, 5 * mm, stroke=0, fill=1)
        c.setFillColorRGB(0, 0, 0)

        c.setFont("Helvetica-Bold", 6)
        c.drawString(x + 2 * mm, y - 3.5 * mm, "INFORMAÇÕES COMPLEMENTARES")
        c.drawString(x + w * 0.65 + 2 * mm, y - 3.5 * mm, "RESERVADO AO FISCO")

        # Conteúdo
        forma = venda.get('forma_pagamento', 'dinheiro').upper()
        numero = venda.get('numero', '---')
        info = f"FORMA: {forma} | Nº: {numero} | PDV FALL CONSTRUÇÕES"
        if len(info) > 100:
            info = info[:97] + "..."

        c.setFont("Helvetica", 5.5)
        c.drawString(x + 2 * mm, y - 10 * mm, info)
        c.drawString(x + w * 0.65 + 2 * mm, y - 10 * mm, "---")

    # ─────────────────────────────────────────────────────────────
    # UTILS
    # ─────────────────────────────────────────────────────────────

    def _gerar_chave_mock(self, venda):
        """Gera uma chave de acesso mock (44 dígitos) para demonstração"""
        import hashlib
        seed = str(venda.get('id', 1)) + str(venda.get('numero', '000'))
        hash_val = hashlib.md5(seed.encode()).hexdigest()
        chave = "35" + hash_val[:42]
        return chave.upper()[:44]

    def _format_chave(self, chave):
        """Formata chave de acesso em grupos de 4"""
        return ' '.join([chave[i:i + 4] for i in range(0, len(chave), 4)])