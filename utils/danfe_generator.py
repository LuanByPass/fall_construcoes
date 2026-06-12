"""
Gerador de Recibo/Comprovante de Venda - FALL CONSTRUÇÕES
Layout profissional estilo SEFAZ (simplificado - sem chave de acesso e sem impostos detalhados)
Usa ReportLab canvas direto para máximo controle do layout
VERSÃO FINAL V5 - Correções visuais, campos flexíveis, sem frete, sem fundo amarelo
"""
import os
import traceback
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas


class DanfeGenerator:
    """Gera PDF de Recibo/Comprovante de Venda para PDV usando canvas direto"""

    def __init__(self, loja_config):
        self.loja_config = loja_config
        self.page_width, self.page_height = A4
        self.margin = 10 * mm

    # ════════════════════════════════════════════════════════════
    # HELPERS DE SEGURANÇA
    # ════════════════════════════════════════════════════════════
    def _safe_str(self, value, default=""):
        """Converte qualquer valor para string segura, tratando None."""
        if value is None:
            return default
        if hasattr(value, 'nome') and value.nome is not None:
            value = value.nome
        elif hasattr(value, '__str__'):
            value = str(value)
        result = str(value).strip()
        return result if result else default

    def _safe_float(self, value, default=0.0):
        """Converte valor para float seguro."""
        if value is None:
            return default
        try:
            return float(value)
        except (ValueError, TypeError):
            return default

    def _safe_date(self, value):
        """Converte valor para datetime ou retorna datetime.now()."""
        if value is None:
            return datetime.now()
        if isinstance(value, datetime):
            return value
        try:
            if isinstance(value, str):
                return datetime.fromisoformat(value.replace('Z', '+00:00'))
            return datetime.now()
        except Exception:
            return datetime.now()

    def _get_val(self, venda, *keys, default=""):
        """Tenta várias chaves no dicionário/objeto até encontrar um valor válido."""
        for key in keys:
            val = venda.get(key) if isinstance(venda, dict) else getattr(venda, key, None)
            if val is not None and str(val).strip():
                return val
        return default

    def gerar(self, venda, output_path="danfe.pdf"):
        """Gera o PDF do recibo/comprovante de venda"""
        try:
            c = canvas.Canvas(output_path, pagesize=A4)
            numero_doc = self._safe_str(self._get_val(venda, 'numero', 'numero_venda', 'id', 'codigo'), '000')
            c.setTitle(f"Recibo - Venda {numero_doc}")

            y = self.page_height - self.margin

            # === CABEÇALHO ===
            y = self._draw_header(c, venda, y)
            y -= 3 * mm

            # === DADOS DO EMITENTE ===
            y = self._draw_emitente(c, y)
            y -= 3 * mm

            # === DADOS DO DESTINATÁRIO ===
            y = self._draw_destinatario(c, venda, y)
            y -= 3 * mm

            # === RESUMO DA VENDA ===
            y = self._draw_resumo_venda(c, venda, y)
            y -= 3 * mm

            # === PRODUTOS / SERVIÇOS ===
            y = self._draw_produtos(c, venda, y)
            y -= 3 * mm

            # === DADOS ADICIONAIS ===
            self._draw_dados_adicionais(c, venda, y)

            c.save()
            return output_path
        except Exception as e:
            print(f"[RECIBO] ERRO ao gerar PDF: {e}")
            traceback.print_exc()
            raise

    # ─────────────────────────────────────────────────────────────
    # HELPERS DE DESENHO
    # ─────────────────────────────────────────────────────────────

    def _rect(self, c, x, y, w, h, stroke=1, fill=0):
        c.rect(x, y - h, w, h, stroke=stroke, fill=fill)

    def _text(self, c, x, y, text, font="Helvetica", size=8, bold=False):
        if bold:
            font = font + "-Bold"
        c.setFont(font, size)
        c.drawString(x, y, str(text))

    def _text_center(self, c, x, y, text, font="Helvetica", size=8, bold=False):
        if bold:
            font = font + "-Bold"
        c.setFont(font, size)
        tw = c.stringWidth(str(text), font, size)
        c.drawString(x - tw / 2, y, str(text))

    def _label(self, c, x, y, text, size=6):
        c.setFillColorRGB(0.3, 0.3, 0.3)
        c.setFont("Helvetica-Bold", size)
        c.drawString(x, y, str(text))
        c.setFillColorRGB(0, 0, 0)

    def _label_value(self, c, x, y, label, value, label_size=6, value_size=8, value_bold=False):
        """Label + valor empilhados com espaçamento adequado"""
        self._label(c, x, y, label, label_size)
        font = "Helvetica-Bold" if value_bold else "Helvetica"
        c.setFont(font, value_size)
        c.drawString(x, y - value_size - 1, str(value))

    # ─────────────────────────────────────────────────────────────
    # SEÇÕES DO RECIBO
    # ─────────────────────────────────────────────────────────────

    def _draw_header(self, c, venda, y_start):
        """Cabeçalho simplificado - SEM chave de acesso e SEM barcode"""
        x = self.margin
        y = y_start
        w_total = self.page_width - 2 * self.margin
        h = 20 * mm

        c.setFillColorRGB(0.95, 0.95, 0.95)
        c.rect(x, y - h, w_total, h, stroke=0, fill=1)
        c.setFillColorRGB(0, 0, 0)

        c.setLineWidth(1)
        c.rect(x, y - h, w_total, h, stroke=1, fill=0)

        cx = x + w_total / 2
        cy = y - 6 * mm
        self._text_center(c, cx, cy, "RECIBO / COMPROVANTE DE VENDA", size=14, bold=True)
        cy -= 5 * mm
        numero_doc = self._safe_str(self._get_val(venda, 'numero', 'numero_venda', 'id', 'codigo'), '000')
        self._text_center(c, cx, cy, f"Nº {numero_doc}", size=12, bold=True)
        cy -= 4 * mm
        self._text_center(c, cx, cy, "DOCUMENTO NÃO FISCAL", size=8)

        return y - h

    def _draw_emitente(self, c, y_start):
        """Dados do emitente (empresa) - ALTURA AUMENTADA para evitar sobreposição"""
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
                          self._safe_str(self.loja_config.get('endereco'), 'Av. Dom Helder Câmara, 3691 - Vale Quem Tem'))
        self._label_value(c, col1 + 2 * mm, ly2, "MUNICÍPIO",
                          self._safe_str(self.loja_config.get('cidade'), 'Teresina'))
        self._label_value(c, col2 + 2 * mm, ly2, "UF",
                          self._safe_str(self.loja_config.get('uf'), 'PI'))

        return y - h

    def _draw_destinatario(self, c, venda, y_start):
        """Dados do destinatário (cliente) - ALTURA AUMENTADA, CHAVES FLEXÍVEIS"""
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

        # ════════════════════════════════════════════════════════════
        # CHAVES FLEXÍVEIS: tenta vários nomes de campo comuns no MVC
        # ════════════════════════════════════════════════════════════
        cliente_nome = self._safe_str(
            self._get_val(venda, 'cliente_nome', 'nome_cliente', 'cliente', 'nome'), "CONSUMIDOR"
        )
        if len(cliente_nome) > 35:
            cliente_nome = cliente_nome[:32] + "..."

        cpf_cnpj = self._safe_str(self._get_val(venda, 'cpf_cnpj', 'cpf', 'cnpj', 'cliente_cpf'), '---')
        data_venda = self._safe_date(self._get_val(venda, 'data_venda', 'data', 'data_emissao', 'created_at'))
        data_str = data_venda.strftime('%d/%m/%Y')

        endereco = self._safe_str(self._get_val(venda, 'cliente_endereco', 'endereco', 'endereco_cliente'), 'Não informado')
        if len(endereco) > 45:
            endereco = endereco[:42] + "..."

        cidade = self._safe_str(self._get_val(venda, 'cliente_cidade', 'cidade', 'cidade_cliente'), 'Não informado')
        uf = self._safe_str(
            self._get_val(venda, 'cliente_uf', 'uf', 'uf_cliente'),
            self._safe_str(self.loja_config.get('uf'), 'PI')
        )
        telefone = self._safe_str(self._get_val(venda, 'cliente_telefone', 'telefone', 'fone', 'celular'), '---')
        forma_pgto = self._safe_str(self._get_val(venda, 'forma_pagamento', 'pagamento', 'forma_pgto', 'meio_pagamento'), '---').upper()
        vendedor = self._safe_str(self._get_val(venda, 'vendedor', 'nome_vendedor', 'usuario', 'operador', 'atendente'), '---')

        # Linha 1
        ly = y - 5 * mm
        self._label_value(c, x + 2 * mm, ly, "NOME / RAZÃO SOCIAL", cliente_nome)
        self._label_value(c, col1 + 2 * mm, ly, "CNPJ / CPF", cpf_cnpj)
        self._label_value(c, col2 + 2 * mm, ly, "DATA DA EMISSÃO", data_str)

        # Linha 2
        ly2 = y - h / 3 - 5 * mm
        self._label_value(c, x + 2 * mm, ly2, "ENDEREÇO", endereco)
        self._label_value(c, col3 + 2 * mm, ly2, "MUNICÍPIO", cidade)
        self._label_value(c, col4 + 2 * mm, ly2, "UF", uf)
        self._label_value(c, col5 + 2 * mm, ly2, "TELEFONE", telefone)

        # Linha 3
        ly3 = y - 2 * h / 3 - 5 * mm
        hora_str = data_venda.strftime('%H:%M:%S')
        self._label_value(c, x + 2 * mm, ly3, "DATA DA SAÍDA", data_str)
        self._label_value(c, col3 + 2 * mm, ly3, "HORA DA SAÍDA", hora_str)
        self._label_value(c, col4 + 2 * mm, ly3, "FORMA PAGAMENTO", forma_pgto)
        self._label_value(c, col5 + 2 * mm, ly3, "VENDEDOR", vendedor)

        return y - h

    def _draw_resumo_venda(self, c, venda, y_start):
        """Resumo financeiro da venda - SEM FRETE, SEM FUNDO AMARELO"""
        x = self.margin
        y = y_start
        w = self.page_width - 2 * self.margin
        h = 20 * mm

        c.setLineWidth(1)
        c.rect(x, y - h, w, h, stroke=1, fill=0)

        c.setLineWidth(0.5)
        # 3 colunas: Subtotal | Desconto | Total
        col1 = x + w * 0.35
        col2 = x + w * 0.70
        c.line(col1, y, col1, y - h)
        c.line(col2, y, col2, y - h)

        subtotal = self._safe_float(self._get_val(venda, 'subtotal', 'valor_bruto'), 0)
        desconto = self._safe_float(self._get_val(venda, 'desconto', 'valor_desconto'), 0)
        total = self._safe_float(self._get_val(venda, 'total', 'valor_total', 'valor_liquido'), 0)

        ly = y - 5 * mm

        # Labels
        self._label(c, x + 2 * mm, ly, "SUBTOTAL", 5)
        self._label(c, col1 + 2 * mm, ly, "DESCONTO", 5)
        self._label(c, col2 + 2 * mm, ly, "TOTAL GERAL", 5)

        # Valores (SEM FUNDO AMARELO - igual aos outros campos)
        c.setFont("Helvetica-Bold", 9)
        c.drawString(x + 2 * mm, ly - 10, f"R$ {subtotal:.2f}")
        c.drawString(col1 + 2 * mm, ly - 10, f"R$ {desconto:.2f}")
        c.drawString(col2 + 2 * mm, ly - 10, f"R$ {total:.2f}")

        return y - h

    def _draw_produtos(self, c, venda, y_start):
        """Tabela de produtos - SIMPLIFICADA"""
        x = self.margin
        y = y_start
        w = self.page_width - 2 * self.margin

        itens = venda.get("itens") if isinstance(venda, dict) else getattr(venda, 'itens', None)
        if itens is None:
            itens = []

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

        cols_x = [
            x,
            x + 20 * mm,
            x + 95 * mm,
            x + 110 * mm,
            x + 125 * mm,
            x + 150 * mm,
            x + w
        ]

        c.setLineWidth(0.5)
        for cx in cols_x[1:-1]:
            c.line(cx, y, cx, y - h)

        c.line(x, y - header_height, x + w, y - header_height)

        headers = ["CÓDIGO", "DESCRIÇÃO DO PRODUTO / SERVIÇO", "UN", "QTD", "V. UNIT.", "V. TOTAL"]

        for i, h_text in enumerate(headers):
            if i >= len(cols_x) - 1:
                break
            cx = cols_x[i] + 1 * mm
            c.setFont("Helvetica-Bold", 6)
            c.drawString(cx, y - 5 * mm, h_text)

        c.setFont("Helvetica", 6)
        for idx, item in enumerate(itens):
            iy = y - header_height - (idx + 1) * row_height + 2 * mm

            nome = self._safe_str(
                self._get_val(item, 'produto_nome', 'nome', 'descricao', 'produto'), "Item"
            )[:40]
            codigo = self._safe_str(self._get_val(item, 'codigo', 'id_produto', 'sku', 'referencia'), "---")
            qtd = self._safe_float(self._get_val(item, 'quantidade', 'qtd', 'qtde'), 1)
            preco = self._safe_float(
                self._get_val(item, 'preco_unitario', 'preco', 'valor_unitario', 'unitario'), 0
            )
            total_item = self._safe_float(self._get_val(item, 'subtotal', 'total_item', 'valor_total'), preco * qtd)

            vals = [
                str(codigo)[:12],
                nome[:38],
                self._safe_str(self._get_val(item, 'unidade', 'un', 'un_medida'), "UN"),
                str(int(qtd)),
                f"R$ {preco:.2f}",
                f"R$ {total_item:.2f}"
            ]

            for i, val in enumerate(vals):
                if i >= len(cols_x) - 1:
                    break
                cx = cols_x[i] + 1 * mm

                if i + 1 < len(cols_x):
                    col_w = cols_x[i + 1] - cols_x[i]
                else:
                    col_w = w - (cols_x[i] - x)

                if i >= 4:
                    tw = c.stringWidth(val, "Helvetica", 6)
                    draw_x = min(cx + col_w - tw - 2 * mm, cx + col_w - 2 * mm)
                    c.drawString(draw_x, iy, val)
                else:
                    c.drawString(cx, iy, val)

            c.setLineWidth(0.3)
            c.line(x, y - header_height - (idx + 1) * row_height,
                   x + w, y - header_height - (idx + 1) * row_height)

        return y - h

    def _draw_dados_adicionais(self, c, venda, y_start):
        """Dados adicionais - observações e informações complementares"""
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

        forma = self._safe_str(self._get_val(venda, 'forma_pagamento', 'pagamento', 'forma_pgto'), 'dinheiro').upper()
        numero = self._safe_str(self._get_val(venda, 'numero', 'numero_venda', 'id', 'codigo'), '---')
        obs = self._safe_str(self._get_val(venda, 'observacao', 'obs', 'observacoes'), '')
        vendedor = self._safe_str(self._get_val(venda, 'vendedor', 'nome_vendedor', 'usuario'), '---')

        info = f"FORMA: {forma} | Nº: {numero} | VENDEDOR: {vendedor}"
        if obs:
            info += f" | OBS: {obs}"
        if len(info) > 120:
            info = info[:117] + "..."

        c.setFont("Helvetica", 5.5)
        c.drawString(x + 2 * mm, y - 10 * mm, info)
        c.drawString(x + 2 * mm, y - 14 * mm, "PDV FALL CONSTRUÇÕES - Documento não fiscal para controle interno")
        c.drawString(x + 2 * mm, y - 18 * mm, "Não possui valor fiscal. Conserve este comprovante para eventuais trocas.")
        c.drawString(x + 2 * mm, y - 22 * mm, "Trocas em até 7 dias com este documento e produto sem uso.")

        # Linha para assinatura
        c.line(x + w * 0.65 + 5 * mm, y - 15 * mm, x + w - 5 * mm, y - 15 * mm)
        c.setFont("Helvetica", 5)
        c.drawString(x + w * 0.65 + 5 * mm, y - 18 * mm, "Assinatura do Cliente / Recebedor")

    # ─────────────────────────────────────────────────────────────
    # UTILS
    # ─────────────────────────────────────────────────────────────

    def _gerar_chave_mock(self, venda):
        """Gera uma chave de acesso mock (44 dígitos) para demonstração"""
        import hashlib
        seed = str(self._get_val(venda, 'id', 'numero', 'codigo', default=1)) + "000"
        hash_val = hashlib.md5(seed.encode()).hexdigest()
        chave = "35" + hash_val[:42]
        return chave.upper()[:44]

    def _format_chave(self, chave):
        """Formata chave de acesso em grupos de 4"""
        return ' '.join([chave[i:i + 4] for i in range(0, len(chave), 4)])