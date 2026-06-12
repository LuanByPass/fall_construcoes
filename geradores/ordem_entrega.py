"""
Gerador de Ordem de Entrega (PDF) — VIA DUPLA COM PAGINAÇÃO
Tabela preenche todo o espaço. Comprovante rente à borda inferior.
"""
import os
import subprocess
import platform
from datetime import datetime, date, timedelta
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas


class OrdemEntregaGenerator:
    """Gera PDF de Ordem de Entrega estilo DANFE com via dupla e paginação"""

    def __init__(self, loja_config):
        self.loja_config = loja_config
        self.page_width, self.page_height = A4
        self.margin = 10 * mm

    # ── HELPERS DE CONVERSÃO SEGURA ──
    @staticmethod
    def _to_str(valor, default="---"):
        if valor is None or valor == "":
            return default
        if isinstance(valor, str):
            return valor if valor.strip() else default
        if isinstance(valor, (datetime, date)):
            return valor.strftime("%d/%m/%Y")
        if isinstance(valor, timedelta):
            total_seconds = int(valor.total_seconds())
            hours = total_seconds // 3600
            minutes = (total_seconds % 3600) // 60
            return f"{hours:02d}:{minutes:02d}"
        return str(valor)

    @staticmethod
    def _to_float(valor, default=0.0):
        if valor is None or valor == "":
            return default
        if isinstance(valor, (int, float)):
            return float(valor)
        try:
            return float(str(valor).replace("R$", "").replace(" ", "").replace(",", "."))
        except (ValueError, TypeError):
            return default

    # ── PAGINAÇÃO ──
    def _dedup_itens(self, itens_raw):
        """Remove itens duplicados por código+nome+qtd."""
        seen = set()
        itens = []
        for item in itens_raw:
            cod = str(item.get("codigo") or item.get("produto_codigo") or "")
            nome = str(item.get("produto_nome") or item.get("nome") or "")
            qtd = str(item.get("quantidade", 1))
            key = (cod, nome, qtd)
            if key not in seen:
                seen.add(key)
                itens.append(item)
        return itens

    def _calcular_layout_pagina1(self, tem_observacao):
        """Calcula layout bottom-up. Retorna (max_linhas, y_tabela_top, y_tabela_bottom)."""
        margem_inf = 10 * mm
        espaco = 3 * mm

        # De baixo para cima
        h_comprovante = 24 * mm
        y_comprovante_bottom = margem_inf
        y_comprovante_top = y_comprovante_bottom + h_comprovante

        y_empresa_dest_bottom = y_comprovante_top + espaco
        h_empresa_dest = 18 * mm
        y_empresa_dest_top = y_empresa_dest_bottom + h_empresa_dest

        y_empresa_header_bottom = y_empresa_dest_top + espaco
        h_empresa_header = 22 * mm
        y_empresa_header_top = y_empresa_header_bottom + h_empresa_header

        espaco_corte = 5 * mm
        y_corte = y_empresa_header_top + espaco_corte

        h_rodape_cliente = 8 * mm
        y_rodape_bottom = y_corte + espaco_corte
        y_rodape_top = y_rodape_bottom + h_rodape_cliente

        espaco_tabela_rodape = 3 * mm
        y_tabela_bottom = y_rodape_top + espaco_tabela_rodape

        if tem_observacao:
            h_obs = 16 * mm
            y_tabela_bottom = y_rodape_top + espaco_tabela_rodape + h_obs + espaco

        # De cima para baixo
        y_topo = self.page_height - self.margin
        y_after_header = y_topo - 30 * mm - espaco
        y_after_dest = y_after_header - 28 * mm - espaco
        y_after_detalhes = y_after_dest - 14 * mm - espaco
        y_tabela_top = y_after_detalhes

        altura_tabela = y_tabela_top - y_tabela_bottom
        max_linhas = int((altura_tabela - 10 * mm) / (6 * mm))
        return max(0, max_linhas), y_tabela_top, y_tabela_bottom

    def _calcular_layout_continuacao(self):
        """Calcula layout para páginas de continuação com resumo + tabela + rodapé."""
        margem_inf = 10 * mm
        espaco = 5 * mm
        h_header = 18 * mm
        h_resumo = 14 * mm  # resumo do destinatário
        h_rodape = 12 * mm

        y_topo = self.page_height - self.margin
        y_after_header = y_topo - h_header - espaco
        y_after_resumo = y_after_header - h_resumo - espaco

        altura_disponivel = y_after_resumo - margem_inf - h_rodape
        max_linhas = int((altura_disponivel - 10 * mm) / (6 * mm))
        # Limita a 20 linhas para não ficar muito vazio
        return min(max(0, max_linhas), 20)

    def gerar(self, entrega, venda=None, output_path=None):
        if output_path is None:
            temp_dir = os.path.join(os.environ.get("TEMP", "/tmp"), "fall_ordens")
            os.makedirs(temp_dir, exist_ok=True)
            numero = str(entrega.get('id', '000')).zfill(6)
            output_path = os.path.join(temp_dir, f"ordem_entrega_{numero}.pdf")

        try:
            c = canvas.Canvas(output_path, pagesize=A4)
            c.setTitle(f"Ordem de Entrega - {self._to_str(entrega.get('id', '000'))}")

            itens = []
            if venda and venda.get("itens"):
                itens = self._dedup_itens(venda.get("itens", []))

            tem_obs = bool(entrega.get("observacoes"))
            max_p1, y_tabela_top, y_tabela_bottom = self._calcular_layout_pagina1(tem_obs)
            max_pn = self._calcular_layout_continuacao()

            total_itens = len(itens)
            itens_p1 = itens[:max_p1]
            itens_restantes = itens[max_p1:]

            # Preenche linhas vazias na página 1
            while len(itens_p1) < max_p1:
                itens_p1.append({
                    "codigo": "", "produto_codigo": "", "produto_nome": "", "nome": "",
                    "quantidade": "", "preco_unitario": "", "preco": "", "subtotal": "",
                })

            # ═══════════════════════════════════════════════════════════════
            # PÁGINA 1
            # ═══════════════════════════════════════════════════════════════
            y = self.page_height - self.margin

            y = self._draw_header(c, entrega, y, via="VIA DO CLIENTE")
            y -= 3 * mm

            y = self._draw_destinatario(c, entrega, y)
            y -= 3 * mm

            y = self._draw_detalhes_entrega(c, entrega, y)
            y -= 3 * mm

            y = self._draw_itens(c, itens_p1, y, y_final=y_tabela_bottom,
                                 mostrar_continua=(total_itens > max_p1))

            if tem_obs:
                y -= 3 * mm
                y = self._draw_observacoes(c, entrega, y)

            y -= 3 * mm
            y = self._draw_rodape_via(c, y, "VIA DO CLIENTE — Guarde este documento")
            y -= 5 * mm

            y = self._draw_linha_corte(c, y)
            y -= 5 * mm

            y = self._draw_header(c, entrega, y, via="VIA DA EMPRESA", compacto=True)
            y -= 3 * mm

            y = self._draw_destinatario_compacto(c, entrega, y)
            y -= 3 * mm

            y = self._draw_comprovante_recebimento(c, entrega, y)

            # ═══════════════════════════════════════════════════════════════
            # PÁGINAS 2+: Continuação com resumo do destinatário
            # ═══════════════════════════════════════════════════════════════
            pagina_atual = 2
            while itens_restantes:
                c.showPage()
                y = self.page_height - self.margin

                y = self._draw_header_continuacao(c, entrega, pagina_atual, y)
                y -= 5 * mm

                y = self._draw_resumo_continuacao(c, entrega, y)
                y -= 5 * mm

                chunk = itens_restantes[:max_pn]
                itens_restantes = itens_restantes[max_pn:]

                # Preenche apenas até 5 linhas em branco (não a página inteira)
                min_linhas = min(len(chunk) + 5, max_pn)
                while len(chunk) < min_linhas:
                    chunk.append({
                        "codigo": "", "produto_codigo": "", "produto_nome": "", "nome": "",
                        "quantidade": "", "preco_unitario": "", "preco": "", "subtotal": "",
                    })

                y = self._draw_itens(c, chunk, y, y_final=22*mm,
                                     mostrar_continua=bool(itens_restantes))
                y -= 5 * mm

                y = self._draw_rodape_continuacao(c, y, pagina_atual)
                pagina_atual += 1

            c.save()
            return output_path

        except Exception as e:
            print(f"[ORDEM ENTREGA] ERRO ao gerar PDF: {e}")
            import traceback
            traceback.print_exc()
            raise

    def abrir_pdf(self, path):
        try:
            if platform.system() == "Windows":
                os.startfile(path)
            elif platform.system() == "Darwin":
                subprocess.run(["open", path], check=False)
            else:
                subprocess.run(["xdg-open", path], check=False)
        except Exception as e:
            print(f"[ORDEM ENTREGA] Erro ao abrir PDF: {e}")

    # ── HELPERS DE DESENHO ──
    def _rect(self, c, x, y, w, h, stroke=1, fill=0):
        c.rect(x, y - h, w, h, stroke=stroke, fill=fill)

    def _text(self, c, x, y, text, font="Helvetica", size=8, bold=False):
        if bold:
            font = font + "-Bold"
        c.setFont(font, size)
        c.drawString(x, y, self._to_str(text))

    def _text_center(self, c, x, y, text, font="Helvetica", size=8, bold=False):
        if bold:
            font = font + "-Bold"
        c.setFont(font, size)
        tw = c.stringWidth(self._to_str(text), font, size)
        c.drawString(x - tw / 2, y, self._to_str(text))

    def _label(self, c, x, y, text, size=6):
        c.setFillColorRGB(0.3, 0.3, 0.3)
        c.setFont("Helvetica-Bold", size)
        c.drawString(x, y, self._to_str(text))
        c.setFillColorRGB(0, 0, 0)

    def _label_value(self, c, x, y, label, value, label_size=6, value_size=8, value_bold=False):
        self._label(c, x, y, label, label_size)
        font = "Helvetica-Bold" if value_bold else "Helvetica"
        c.setFont(font, value_size)
        c.drawString(x, y - value_size - 1, self._to_str(value))

    # ── CABEÇALHO ──
    def _draw_header(self, c, entrega, y_start, via="", compacto=False):
        x = self.margin
        y = y_start
        w_total = self.page_width - 2 * self.margin
        h = 22 * mm if compacto else 30 * mm
        w_left = 55 * mm if compacto else 65 * mm

        c.setFillColorRGB(0.95, 0.95, 0.95)
        c.rect(x, y - h, w_total, h, stroke=0, fill=1)
        c.setFillColorRGB(0, 0, 0)

        c.setLineWidth(1)
        c.rect(x, y - h, w_total, h, stroke=1, fill=0)
        c.setLineWidth(0.5)
        c.line(x + w_left, y, x + w_left, y - h)

        cx = x + w_left / 2
        cy = y - 5 * mm
        self._text_center(c, cx, cy, "ORDEM DE ENTREGA", size=12 if compacto else 14, bold=True)
        cy -= 4 * mm
        self._text_center(c, cx, cy, "Documento de Transporte e Entrega", size=6)
        cy -= 5 * mm
        numero = str(entrega.get('id', '000')).zfill(6)
        self._text_center(c, cx, cy, f"Nº ENT-{numero}", size=9, bold=True)
        cy -= 4 * mm
        data_emissao = datetime.now().strftime('%d/%m/%Y %H:%M')
        self._text_center(c, cx, cy, f"Emissao: {data_emissao}", size=7)

        rx = x + w_left + 2 * mm
        ry = y - 4 * mm
        self._text(c, rx, ry, self.loja_config.get('nome', 'FALL CONSTRUCOES'), size=9, bold=True)
        ry -= 3.5 * mm
        self._text(c, rx, ry, f"CNPJ: {self.loja_config.get('cnpj', '')}", size=6)
        ry -= 3 * mm
        endereco = self._to_str(self.loja_config.get('endereco', ''))
        if len(endereco) > 60:
            endereco = endereco[:57] + "..."
        self._text(c, rx, ry, endereco, size=6)
        ry -= 3 * mm
        self._text(c, rx, ry, f"Tel: {self._to_str(self.loja_config.get('telefone', ''))}", size=6)

        if via:
            c.setFillColorRGB(0.9, 0.1, 0.1)
            c.setFont("Helvetica-Bold", 7)
            c.drawString(x + w_total - 40 * mm, y - 4 * mm, f"[{via}]")
            c.setFillColorRGB(0, 0, 0)

        return y - h

    # ── CABEÇALHO DE CONTINUAÇÃO ──
    def _draw_header_continuacao(self, c, entrega, pagina, y_start):
        x = self.margin
        y = y_start
        w_total = self.page_width - 2 * self.margin
        h = 18 * mm

        c.setFillColorRGB(0.95, 0.95, 0.95)
        c.rect(x, y - h, w_total, h, stroke=0, fill=1)
        c.setFillColorRGB(0, 0, 0)

        c.setLineWidth(1)
        c.rect(x, y - h, w_total, h, stroke=1, fill=0)

        numero = str(entrega.get('id', '000')).zfill(6)
        c.setFont("Helvetica-Bold", 12)
        c.drawCentredString(x + w_total / 2, y - 7 * mm, f"ORDEM DE ENTREGA — CONTINUAÇÃO")
        c.setFont("Helvetica", 8)
        c.drawCentredString(x + w_total / 2, y - 12 * mm,
                            f"Nº ENT-{numero}  |  Página {pagina}  |  {self.loja_config.get('nome', 'FALL CONSTRUCOES')}")

        return y - h

    # ── RESUMO DO DESTINATÁRIO (página 2+) ──
    def _draw_resumo_continuacao(self, c, entrega, y_start):
        """Mini resumo do destinatário para páginas de continuação."""
        x = self.margin
        y = y_start
        w = self.page_width - 2 * self.margin
        h = 14 * mm

        c.setLineWidth(1)
        c.rect(x, y - h, w, h, stroke=1, fill=0)
        c.setLineWidth(0.5)
        c.line(x + w * 0.55, y, x + w * 0.55, y - h)

        c.setFillColorRGB(0.95, 0.95, 0.95)
        c.rect(x, y - 5 * mm, w, 5 * mm, stroke=0, fill=1)
        c.setFillColorRGB(0, 0, 0)

        c.setFont("Helvetica-Bold", 6)
        c.drawString(x + 2 * mm, y - 3.5 * mm, "DESTINATARIO")
        c.drawString(x + w * 0.55 + 2 * mm, y - 3.5 * mm, "ENDERECO DE ENTREGA")

        cliente = self._to_str(entrega.get('cliente_nome', 'Consumidor Final'))
        if len(cliente) > 40:
            cliente = cliente[:37] + "..."
        c.setFont("Helvetica", 7)
        c.drawString(x + 2 * mm, y - 9 * mm, cliente)

        endereco = self._to_str(entrega.get('endereco_entrega', 'Nao informado'))
        if len(endereco) > 50:
            endereco = endereco[:47] + "..."
        c.drawString(x + w * 0.55 + 2 * mm, y - 9 * mm, endereco)

        return y - h

    # ── DESTINATÁRIO (via completa) ──
    def _draw_destinatario(self, c, entrega, y_start):
        x = self.margin
        y = y_start
        w = self.page_width - 2 * self.margin
        h = 28 * mm

        c.setLineWidth(1)
        c.rect(x, y - h, w, h, stroke=1, fill=0)
        c.setLineWidth(0.5)
        c.line(x, y - h / 2, x + w, y - h / 2)

        col1 = x + w * 0.50
        col2 = x + w * 0.75
        c.line(col1, y, col1, y - h / 2)
        c.line(col2, y, col2, y - h / 2)

        col3 = x + w * 0.35
        col4 = x + w * 0.60
        col5 = x + w * 0.80
        c.line(col3, y - h / 2, col3, y - h)
        c.line(col4, y - h / 2, col4, y - h)
        c.line(col5, y - h / 2, col5, y - h)

        ly = y - 4 * mm
        cliente_nome = self._to_str(entrega.get('cliente_nome', 'Consumidor Final'))
        if len(cliente_nome) > 35:
            cliente_nome = cliente_nome[:32] + "..."
        telefone = self._to_str(entrega.get('telefone_contato') or entrega.get('telefone'))
        cpf_cnpj = self._to_str(entrega.get('cpf_cnpj') or entrega.get('cpf') or entrega.get('cnpj'))

        self._label_value(c, x + 2 * mm, ly, "NOME / RAZAO SOCIAL", cliente_nome)
        self._label_value(c, col1 + 2 * mm, ly, "TELEFONE", telefone)
        self._label_value(c, col2 + 2 * mm, ly, "CNPJ / CPF", cpf_cnpj)

        ly2 = y - h / 2 - 4 * mm
        endereco = self._to_str(entrega.get('endereco_entrega', 'Nao informado'))
        if len(endereco) > 45:
            endereco = endereco[:42] + "..."
        cidade = self._to_str(entrega.get('cidade', 'Nao informado'))
        uf = self._to_str(entrega.get('estado') or entrega.get('uf', 'PI'))
        cep = self._to_str(entrega.get('cep'))

        self._label_value(c, x + 2 * mm, ly2, "ENDERECO DE ENTREGA", endereco)
        self._label_value(c, col3 + 2 * mm, ly2, "MUNICIPIO", cidade)
        self._label_value(c, col4 + 2 * mm, ly2, "UF", uf)
        self._label_value(c, col5 + 2 * mm, ly2, "CEP", cep)

        return y - h

    # ── DESTINATÁRIO COMPACTO (via empresa) ──
    def _draw_destinatario_compacto(self, c, entrega, y_start):
        x = self.margin
        y = y_start
        w = self.page_width - 2 * self.margin
        h = 18 * mm

        c.setLineWidth(1)
        c.rect(x, y - h, w, h, stroke=1, fill=0)
        c.setLineWidth(0.5)
        c.line(x, y - h / 2, x + w, y - h / 2)
        c.line(x + w * 0.60, y, x + w * 0.60, y - h / 2)

        ly = y - 4 * mm
        cliente_nome = self._to_str(entrega.get('cliente_nome', 'Consumidor Final'))
        cpf_cnpj = self._to_str(entrega.get('cpf_cnpj') or entrega.get('cpf') or entrega.get('cnpj'))
        endereco = self._to_str(entrega.get('endereco_entrega', 'Nao informado'))
        cidade = self._to_str(entrega.get('cidade', 'Nao informado'))
        uf = self._to_str(entrega.get('estado') or entrega.get('uf', 'PI'))

        self._label_value(c, x + 2 * mm, ly, "DESTINATARIO", cliente_nome)
        self._label_value(c, x + w * 0.60 + 2 * mm, ly, "CNPJ / CPF", cpf_cnpj)

        ly2 = y - h / 2 - 4 * mm
        self._label_value(c, x + 2 * mm, ly2, "ENDERECO", endereco)
        self._label_value(c, x + w * 0.60 + 2 * mm, ly2, "CIDADE/UF", f"{cidade} — {uf}")

        return y - h

    # ── DETALHES DA ENTREGA (sem status) ──
    def _draw_detalhes_entrega(self, c, entrega, y_start):
        x = self.margin
        y = y_start
        w = self.page_width - 2 * self.margin
        h = 14 * mm

        c.setLineWidth(1)
        c.rect(x, y - h, w, h, stroke=1, fill=0)

        cols = [x + w * i / 6 for i in range(1, 6)]
        for cx in cols:
            c.line(cx, y, cx, y - h)

        ly = y - 4 * mm
        data_agendada = entrega.get('data_agendada', '')
        data_str = self._to_str(data_agendada)
        if data_str == "---":
            data_str = ""
        hora = self._to_str(entrega.get('hora_agendada'))
        veiculo = self._to_str(entrega.get('tipo_veiculo')).upper()
        motorista = self._to_str(entrega.get('motorista'))
        placa = self._to_str(entrega.get('placa_veiculo'))
        frete = self._to_float(entrega.get('valor_frete'))

        labels = ["DATA AGENDADA", "HORA", "VEICULO", "MOTORISTA", "PLACA", "VALOR FRETE"]
        valores = [data_str, hora, veiculo, motorista, placa, f"R$ {frete:.2f}"]

        col_w = w / 6
        for i, (lab, val) in enumerate(zip(labels, valores)):
            cx = x + i * col_w + 2 * mm
            self._label(c, cx, ly, lab, 5)
            c.setFont("Helvetica-Bold" if i == 5 else "Helvetica", 7)
            c.drawString(cx, ly - 8, self._to_str(val))

        return y - h

    # ── ITENS DA VENDA ──
    def _draw_itens(self, c, itens, y_start, y_final=10*mm, mostrar_continua=False):
        x = self.margin
        y = y_start
        w = self.page_width - 2 * self.margin

        if not itens:
            return y_start

        row_height = 6 * mm
        header_height = 10 * mm
        h = header_height + len(itens) * row_height + 2 * mm

        altura_maxima = y - y_final
        if h > altura_maxima:
            linhas_cabem = max(0, int((altura_maxima - header_height - 2 * mm) / row_height))
            itens = itens[:linhas_cabem]
            h = header_height + len(itens) * row_height + 2 * mm

        c.setLineWidth(1)
        c.rect(x, y - h, w, h, stroke=1, fill=0)

        c.setFillColorRGB(0.9, 0.9, 0.9)
        c.rect(x, y - header_height, w, header_height, stroke=0, fill=1)
        c.setFillColorRGB(0, 0, 0)

        cols_x = [x, x + 20*mm, x + 110*mm, x + 130*mm, x + 150*mm, x + 170*mm, x + w]
        c.setLineWidth(0.5)
        for cx in cols_x[1:-1]:
            c.line(cx, y, cx, y - h)
        c.line(x, y - header_height, x + w, y - header_height)

        headers = ["CODIGO", "DESCRICAO", "QTD", "V.UNIT", "V.TOTAL", "UN"]
        ly = y - 4 * mm
        for i, h_text in enumerate(headers):
            cx = cols_x[i] + 2 * mm
            c.setFont("Helvetica-Bold", 6)
            c.drawString(cx, ly, h_text)

        c.setFont("Helvetica", 6)
        for idx, item in enumerate(itens):
            iy = y - header_height - (idx + 1) * row_height + 2 * mm
            nome = self._to_str(item.get("produto_nome") or item.get("nome") or "", default="")
            if nome:
                nome = nome[:35]
            codigo = self._to_str(item.get("codigo") or item.get("produto_codigo"), default="")
            qtd = item.get("quantidade", "")
            if not isinstance(qtd, (int, float)):
                try:
                    qtd = int(qtd) if qtd else ""
                except (ValueError, TypeError):
                    qtd = ""
            preco = self._to_float(item.get("preco_unitario") or item.get("preco"))
            total_item = self._to_float(item.get("subtotal"), default=preco * qtd if qtd else 0)

            vals = [
                self._to_str(codigo)[:10] if codigo else "",
                nome[:35] if nome else "",
                self._to_str(qtd) if qtd else "",
                f"{preco:.2f}" if preco and item.get("preco_unitario") else "",
                f"{total_item:.2f}" if total_item and item.get("subtotal") else "",
                "UN" if item.get("codigo") or item.get("produto_codigo") else ""
            ]
            for i, val in enumerate(vals):
                cx = cols_x[i] + 2 * mm
                val_str = self._to_str(val, default="")
                if i >= 2 and val_str:
                    tw = c.stringWidth(val_str, "Helvetica", 6)
                    col_w = cols_x[i + 1] - cols_x[i]
                    c.drawString(cx + col_w - tw - 3 * mm, iy, val_str)
                else:
                    c.drawString(cx, iy, val_str)

            c.setLineWidth(0.3)
            c.line(x, y - header_height - (idx + 1) * row_height, x + w, y - header_height - (idx + 1) * row_height)

        if mostrar_continua:
            c.setFont("Helvetica-Bold", 7)
            c.setFillColorRGB(0.8, 0.1, 0.1)
            c.drawString(x + 2 * mm, y - h + 3 * mm, "(continua na próxima página)")
            c.setFillColorRGB(0, 0, 0)

        return y - h

    # ── OBSERVAÇÕES ──
    def _draw_observacoes(self, c, entrega, y_start):
        x = self.margin
        y = y_start
        w = self.page_width - 2 * self.margin
        h = 16 * mm

        c.setLineWidth(1)
        c.rect(x, y - h, w, h, stroke=1, fill=0)
        c.setLineWidth(0.5)
        c.line(x + w * 0.65, y, x + w * 0.65, y - h)

        c.setFillColorRGB(0.9, 0.9, 0.9)
        c.rect(x, y - 5 * mm, w * 0.65, 5 * mm, stroke=0, fill=1)
        c.rect(x + w * 0.65, y - 5 * mm, w * 0.35, 5 * mm, stroke=0, fill=1)
        c.setFillColorRGB(0, 0, 0)

        c.setFont("Helvetica-Bold", 6)
        c.drawString(x + 2 * mm, y - 3.5 * mm, "INFORMACOES COMPLEMENTARES / OBSERVACOES")
        c.drawString(x + w * 0.65 + 2 * mm, y - 3.5 * mm, "RESERVADO")

        obs = self._to_str(entrega.get("observacoes", ""))
        if obs and obs != "---":
            if len(obs) > 120:
                obs = obs[:117] + "..."
            c.setFont("Helvetica", 6)
            c.drawString(x + 2 * mm, y - 10 * mm, obs)

        return y - h

    # ── RODAPÉS ──
    def _draw_rodape_via(self, c, y_start, texto):
        x = self.margin
        y = y_start
        w = self.page_width - 2 * self.margin
        h = 8 * mm

        c.setFillColorRGB(0.95, 0.95, 0.95)
        c.rect(x, y - h, w, h, stroke=0, fill=1)
        c.setFillColorRGB(0.5, 0.5, 0.5)
        c.setFont("Helvetica-Bold", 7)
        c.drawCentredString(x + w / 2, y - 5 * mm, texto)
        c.setFillColorRGB(0, 0, 0)
        return y - h

    def _draw_rodape_continuacao(self, c, y_start, pagina):
        x = self.margin
        y = y_start
        w = self.page_width - 2 * self.margin

        c.setLineWidth(0.5)
        c.line(x, y, x + w, y)

        c.setFont("Helvetica", 6)
        c.setFillColorRGB(0.4, 0.4, 0.4)
        c.drawCentredString(x + w / 2, y - 4 * mm,
            f"Documento sem valor fiscal — FALL Construções  |  Página {pagina}")
        c.setFillColorRGB(0, 0, 0)
        return y

    # ── LINHA DE CORTE ──
    def _draw_linha_corte(self, c, y_start):
        x = self.margin
        y = y_start
        w = self.page_width - 2 * self.margin

        c.setDash(3, 3)
        c.setLineWidth(0.8)
        c.setStrokeColorRGB(0.6, 0.1, 0.1)
        c.line(x, y, x + w, y)
        c.setStrokeColorRGB(0, 0, 0)
        c.setDash()

        c.setFont("Helvetica-Bold", 7)
        c.setFillColorRGB(0.6, 0.1, 0.1)
        c.drawCentredString(x + w / 2, y + 2 * mm, "✂  CORTE AQUI  ✂")
        c.setFillColorRGB(0, 0, 0)
        return y

    # ── COMPROVANTE MÍNIMO — RENTE À BORDA INFERIOR ──
    def _draw_comprovante_recebimento(self, c, entrega, y_start):
        x = self.margin
        y_bottom = 10 * mm
        w = self.page_width - 2 * self.margin
        h = 24 * mm
        y = y_bottom + h

        c.setLineWidth(1)
        c.rect(x, y_bottom, w, h, stroke=1, fill=0)

        c.setFillColorRGB(0.9, 0.9, 0.9)
        c.rect(x, y - 8 * mm, w, 8 * mm, stroke=0, fill=1)
        c.setFillColorRGB(0, 0, 0)
        c.setFont("Helvetica-Bold", 10)
        c.drawString(x + 2 * mm, y - 5 * mm, "COMPROVANTE DE RECEBIMENTO")
        c.setFont("Helvetica", 7)
        c.drawString(x + w - 55 * mm, y - 5 * mm,
                     f"Entrega Nº ENT-{str(entrega.get('id','000')).zfill(6)}")

        c.setFont("Helvetica", 7)
        c.drawString(x + 2 * mm, y - 12 * mm,
                     "Declaro que recebi os produtos acima descritos em perfeito estado.")

        c.setLineWidth(0.5)
        c.line(x + 2 * mm, y - 14 * mm, x + w - 2 * mm, y - 14 * mm)

        ly = y - 20 * mm
        col_mid = x + w * 0.55

        self._label(c, x + 2 * mm, ly, "ASSINATURA DO RECEBEDOR", 5)
        c.line(x + 2 * mm, ly - 8, col_mid - 4 * mm, ly - 8)

        self._label(c, col_mid + 2 * mm, ly, "DATA DO RECEBIMENTO", 5)
        c.line(col_mid + 2 * mm, ly - 8, x + w - 4 * mm, ly - 8)

        return y_bottom