"""Tela de Relatórios - FALL Construções (PDF Profissional + Gráficos) - VERSÃO FINAL"""
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime, timedelta
from views.base_view import BaseView
from config import ModernTheme, LOJA_CONFIG
import subprocess
import os

# ═══════════════════════════════════════════════════════════════════
# GERADOR DE PDF PROFISSIONAL - Relatórios com Gráficos
# ═══════════════════════════════════════════════════════════════════
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor, Color, white, black
from reportlab.pdfgen import canvas
from reportlab.graphics.shapes import Drawing, String, Rect, Line
from reportlab.graphics.charts.barcharts import HorizontalBarChart, VerticalBarChart
from reportlab.graphics.charts.piecharts import Pie
from reportlab.graphics.charts.linecharts import HorizontalLineChart
from reportlab.graphics import renderPDF
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph
from reportlab.lib.enums import TA_CENTER, TA_LEFT


class RelatorioPDFGenerator:
    """Gera PDF profissional de relatórios com gráficos - VERSÃO FINAL"""

    # Cores específicas para cada categoria/produto (paleta profissional)
    CORES_GRAFICO = [
        HexColor("#0f5132"),   # 0 - Verde escuro
        HexColor("#198754"),   # 1 - Verde médio
        HexColor("#20c997"),   # 2 - Verde claro
        HexColor("#ffc107"),   # 3 - Amarelo
        HexColor("#dc3545"),   # 4 - Vermelho
        HexColor("#6f42c1"),   # 5 - Roxo
        HexColor("#0dcaf0"),   # 6 - Ciano
        HexColor("#fd7e14"),   # 7 - Laranja
        HexColor("#d63384"),   # 8 - Rosa
        HexColor("#6610f2"),   # 9 - Índigo
    ]

    def __init__(self, loja_config):
        self.loja_config = loja_config
        self.page_width, self.page_height = A4
        self.margin = 15 * mm
        # Cores do tema FALL
        self.cor_primaria = HexColor("#0f5132")
        self.cor_secundaria = HexColor("#198754")
        self.cor_acento = HexColor("#20c997")
        self.cor_texto = HexColor("#212529")
        self.cor_cinza = HexColor("#6c757d")
        self.cor_fundo = HexColor("#f8f9fa")
        self.cor_borda = HexColor("#dee2e6")

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

    def _format_date(self, value):
        """Converte datetime/date para string formatada"""
        if value is None:
            return ""
        if isinstance(value, str):
            return value
        if hasattr(value, 'strftime'):
            return value.strftime('%d/%m/%Y')
        return str(value)

    def gerar_relatorio(self, titulo, dados, colunas, parametros=None, 
                       tipo_grafico=None, dados_grafico=None, 
                       output_path="relatorio.pdf"):
        try:
            c = canvas.Canvas(output_path, pagesize=A4)
            c.setTitle(f"Relatório - {titulo}")

            y = self.page_height - self.margin

            # === CABEÇALHO ===
            y = self._draw_header_profissional(c, titulo, y)
            y -= 3 * mm

            # === PARÂMETROS ===
            if parametros:
                y = self._draw_parametros(c, parametros, y)
                y -= 3 * mm

            # === GRÁFICO ===
            if tipo_grafico and dados_grafico:
                y = self._draw_grafico(c, tipo_grafico, dados_grafico, y)
                y -= 5 * mm

            # === RESUMO/KPIs ===
            if dados:
                y = self._draw_kpis(c, dados, colunas, y)
                y -= 3 * mm

            # === TABELA ===
            y = self._draw_tabela_profissional(c, dados, colunas, y, titulo)
            y -= 5 * mm

            # === RODAPÉ ===
            self._draw_footer_profissional(c)

            c.save()
            return output_path

        except Exception as e:
            print(f"[PDF] ERRO: {e}")
            import traceback
            traceback.print_exc()
            raise

    def _draw_header_profissional(self, c, titulo, y_start):
        x = self.margin
        w = self.page_width - 2 * self.margin
        h = 35 * mm

        c.setFillColor(self.cor_primaria)
        c.rect(x, y_start - h, w, h, stroke=0, fill=1)

        c.setFillColor(self.cor_acento)
        c.rect(x, y_start - h, w, 3*mm, stroke=0, fill=1)

        c.setFillColor(HexColor("#ffffff"))
        c.setFont("Helvetica-Bold", 18)
        nome = self._safe_str(self.loja_config.get('nome'), 'FALL CONSTRUÇÕES')
        c.drawString(x + 5*mm, y_start - 12*mm, nome)

        c.setFont("Helvetica-Bold", 14)
        c.drawString(x + 5*mm, y_start - 20*mm, titulo)

        c.setFont("Helvetica", 9)
        data_str = datetime.now().strftime('%d/%m/%Y %H:%M')
        c.drawString(x + 5*mm, y_start - 26*mm, f"Emitido em: {data_str}")

        c.setFont("Helvetica", 8)
        cnpj = self._safe_str(self.loja_config.get('cnpj'), '')
        if cnpj:
            c.drawRightString(x + w - 5*mm, y_start - 12*mm, f"CNPJ: {cnpj}")
        endereco = self._safe_str(self.loja_config.get('endereco'), '')
        if endereco:
            c.drawRightString(x + w - 5*mm, y_start - 17*mm, endereco)
        cidade = self._safe_str(self.loja_config.get('cidade'), '')
        uf = self._safe_str(self.loja_config.get('uf'), '')
        if cidade and uf:
            c.drawRightString(x + w - 5*mm, y_start - 22*mm, f"{cidade} - {uf}")

        c.setFillColor(self.cor_texto)
        return y_start - h - 5*mm

    def _draw_parametros(self, c, parametros, y_start):
        x = self.margin
        w = self.page_width - 2 * self.margin
        h = 8 * mm + (len(parametros) * 6 * mm)
        if h < 20 * mm:
            h = 20 * mm

        c.setFillColor(self.cor_fundo)
        c.rect(x, y_start - h, w, h, stroke=0, fill=1)

        c.setStrokeColor(self.cor_borda)
        c.setLineWidth(0.5)
        c.rect(x, y_start - h, w, h, stroke=1, fill=0)

        c.setFillColor(self.cor_primaria)
        c.setFont("Helvetica-Bold", 9)
        c.drawString(x + 5*mm, y_start - 6*mm, "PARÂMETROS DO RELATÓRIO")

        c.setFillColor(self.cor_texto)
        c.setFont("Helvetica", 8)
        y_pos = y_start - 12*mm
        for chave, valor in parametros.items():
            c.setFont("Helvetica-Bold", 8)
            c.drawString(x + 5*mm, y_pos, f"{chave}:")
            c.setFont("Helvetica", 8)
            c.drawString(x + 35*mm, y_pos, str(valor))
            y_pos -= 6*mm

        return y_start - h - 3*mm

    def _draw_grafico(self, c, tipo, dados_grafico, y_start):
        """Desenha gráfico no PDF com legenda de cores"""
        x = self.margin
        w = self.page_width - 2 * self.margin

        h_grafico = 85 * mm
        h_legenda = 30 * mm
        h_total = h_grafico + h_legenda

        c.setFillColor(self.cor_primaria)
        c.setFont("Helvetica-Bold", 11)
        titulo_grafico = dados_grafico.get('titulo', 'Gráfico')
        c.drawString(x, y_start - 5*mm, titulo_grafico)

        y_pos = y_start - 10*mm

        if tipo == 'barra':
            drawing = Drawing(w, h_grafico)
            chart = VerticalBarChart()
            chart.x = 40
            chart.y = 40
            chart.height = 160
            chart.width = 380
            chart.data = [dados_grafico['valores']]
            chart.categoryAxis.categoryNames = dados_grafico['labels']
            chart.categoryAxis.labels.fontSize = 8
            chart.categoryAxis.labels.angle = 35
            chart.categoryAxis.labels.dy = -5
            chart.valueAxis.labels.fontSize = 8
            chart.valueAxis.valueMin = 0

            # CORREÇÃO DEFINITIVA: API correta do ReportLab
            # chart.bars[(serie, indice)] para acessar barra individual
            # Dados: [[val1, val2, val3]] -> uma série com múltiplas barras
            for i in range(len(dados_grafico['valores'])):
                cor_idx = i % len(self.CORES_GRAFICO)
                chart.bars[(0, i)].fillColor = self.CORES_GRAFICO[cor_idx]
                chart.bars[(0, i)].strokeColor = HexColor("#333333")
                chart.bars[(0, i)].strokeWidth = 0.5

            drawing.add(chart)
            renderPDF.draw(drawing, c, x, y_pos - h_grafico + 10*mm)

            self._draw_legenda(c, x, y_pos - h_grafico - 5*mm, w, 
                               dados_grafico['labels'], dados_grafico['valores'])

        elif tipo == 'barra_horizontal':
            drawing = Drawing(w, h_grafico)
            chart = HorizontalBarChart()
            chart.x = 120
            chart.y = 30
            chart.height = 160
            chart.width = 320
            chart.data = [dados_grafico['valores']]
            chart.categoryAxis.categoryNames = dados_grafico['labels']
            chart.categoryAxis.labels.fontSize = 9
            chart.valueAxis.labels.fontSize = 8
            chart.valueAxis.valueMin = 0
            chart.barWidth = 12

            # CORREÇÃO DEFINITIVA: API correta do ReportLab
            for i in range(len(dados_grafico['valores'])):
                cor_idx = i % len(self.CORES_GRAFICO)
                chart.bars[(0, i)].fillColor = self.CORES_GRAFICO[cor_idx]
                chart.bars[(0, i)].strokeColor = HexColor("#333333")
                chart.bars[(0, i)].strokeWidth = 0.5

            drawing.add(chart)
            renderPDF.draw(drawing, c, x, y_pos - h_grafico + 10*mm)

            self._draw_legenda(c, x, y_pos - h_grafico - 5*mm, w, 
                               dados_grafico['labels'], dados_grafico['valores'])

        elif tipo == 'linha':
            drawing = Drawing(w, h_grafico)
            chart = HorizontalLineChart()
            chart.x = 40
            chart.y = 40
            chart.height = 160
            chart.width = 380
            chart.data = [dados_grafico['valores']]
            chart.categoryAxis.categoryNames = dados_grafico['labels']
            chart.categoryAxis.labels.fontSize = 8
            chart.categoryAxis.labels.angle = 35
            chart.valueAxis.labels.fontSize = 8
            chart.lines[0].strokeColor = self.cor_secundaria
            chart.lines[0].strokeWidth = 2
            drawing.add(chart)
            renderPDF.draw(drawing, c, x, y_pos - h_grafico + 10*mm)

            self._draw_legenda(c, x, y_pos - h_grafico - 5*mm, w, 
                               dados_grafico['labels'], dados_grafico['valores'])

        return y_pos - h_total - 5*mm

    def _draw_legenda(self, c, x, y, w, labels, valores):
        """Desenha legenda colorida profissional abaixo do gráfico"""
        n_items = len(labels)
        cols = 2
        rows = (n_items + cols - 1) // cols

        item_width = w / cols
        item_height = 6 * mm

        c.setFont("Helvetica", 8)

        for i, (label, valor) in enumerate(zip(labels, valores)):
            col = i % cols
            row = i // cols

            lx = x + (col * item_width) + 5*mm
            ly = y - (row * item_height)

            # Quadrado colorido com borda
            cor_idx = i % len(self.CORES_GRAFICO)
            c.setFillColor(self.CORES_GRAFICO[cor_idx])
            c.setStrokeColor(HexColor("#333333"))
            c.setLineWidth(0.5)
            c.rect(lx, ly - 2*mm, 4*mm, 4*mm, stroke=1, fill=1)

            # Texto: Nome + valor formatado
            c.setFillColor(self.cor_texto)
            total = sum(valores) if valores else 1
            pct = (valor / total * 100) if total > 0 else 0
            texto = f"{label} - R$ {valor:,.2f} ({pct:.1f}%)"
            c.drawString(lx + 6*mm, ly, texto[:45])

    def _draw_kpis(self, c, dados, colunas, y_start):
        x = self.margin
        w = self.page_width - 2 * self.margin
        h_kpi = 25 * mm

        total_registros = len(dados)
        valores_numericos = []
        for linha in dados:
            for val in linha:
                try:
                    v = str(val).replace('R$', '').replace('.', '').replace(',', '.').strip()
                    if v and v != '-':
                        valores_numericos.append(float(v))
                except:
                    pass

        total_valor = sum(valores_numericos) if valores_numericos else 0
        media_valor = total_valor / len(valores_numericos) if valores_numericos else 0

        kpis = [
            ("Registros", str(total_registros), self.cor_primaria),
            ("Total", f"R$ {total_valor:,.2f}", self.cor_secundaria),
            ("Média", f"R$ {media_valor:,.2f}", self.cor_acento),
        ]

        n_kpis = len(kpis)
        kpi_width = w / n_kpis

        for i, (label, valor, cor) in enumerate(kpis):
            kx = x + (i * kpi_width)

            c.setFillColor(self.cor_fundo)
            c.rect(kx + 2*mm, y_start - h_kpi, kpi_width - 4*mm, h_kpi, stroke=0, fill=1)

            c.setFillColor(cor)
            c.rect(kx + 2*mm, y_start - 4*mm, kpi_width - 4*mm, 4*mm, stroke=0, fill=1)

            c.setFillColor(self.cor_cinza)
            c.setFont("Helvetica", 8)
            c.drawString(kx + 5*mm, y_start - 10*mm, label)

            c.setFillColor(self.cor_texto)
            c.setFont("Helvetica-Bold", 14)
            c.drawString(kx + 5*mm, y_start - 20*mm, valor)

        c.setFillColor(self.cor_texto)
        return y_start - h_kpi - 5*mm

    def _draw_tabela_profissional(self, c, dados, colunas, y_start, titulo="Relatório"):
        x = self.margin
        w = self.page_width - 2 * self.margin

        n_cols = len(colunas)
        col_width = w / n_cols
        row_height = 7 * mm
        header_height = 9 * mm

        c.setFillColor(self.cor_primaria)
        c.setFont("Helvetica-Bold", 10)
        c.drawString(x, y_start - 5*mm, "DADOS DETALHADOS")
        y_start -= 10*mm

        c.setFillColor(self.cor_primaria)
        c.rect(x, y_start - header_height, w, header_height, stroke=0, fill=1)
        c.setFillColor(HexColor("#ffffff"))
        c.setFont("Helvetica-Bold", 8)

        for i, col in enumerate(colunas):
            cx = x + (i * col_width) + 3*mm
            c.drawString(cx, y_start - 6*mm, str(col)[:20])

        y = y_start - header_height

        c.setFont("Helvetica", 8)
        for idx, linha in enumerate(dados):
            if y < 35*mm:
                c.showPage()
                y = self.page_height - self.margin
                c.setFillColor(self.cor_primaria)
                c.rect(x, y - 12*mm, w, 12*mm, stroke=0, fill=1)
                c.setFillColor(HexColor("#ffffff"))
                c.setFont("Helvetica-Bold", 10)
                c.drawString(x + 5*mm, y - 7*mm, f"{titulo} (continuação)")
                c.setFillColor(self.cor_texto)
                y -= 20*mm

                c.setFillColor(self.cor_primaria)
                c.rect(x, y - header_height, w, header_height, stroke=0, fill=1)
                c.setFillColor(HexColor("#ffffff"))
                c.setFont("Helvetica-Bold", 8)
                for i, col in enumerate(colunas):
                    cx = x + (i * col_width) + 3*mm
                    c.drawString(cx, y - 6*mm, str(col)[:20])
                y -= header_height

            if idx % 2 == 0:
                c.setFillColor(self.cor_fundo)
                c.rect(x, y - row_height, w, row_height, stroke=0, fill=1)

            c.setStrokeColor(self.cor_borda)
            c.setLineWidth(0.3)
            c.line(x, y - row_height, x + w, y - row_height)

            c.setFillColor(self.cor_texto)
            for i, valor in enumerate(linha):
                cx = x + (i * col_width) + 3*mm
                texto = str(valor)[:22]
                c.drawString(cx, y - 5*mm, texto)

            y -= row_height

        c.setStrokeColor(self.cor_borda)
        c.setLineWidth(0.5)
        c.rect(x, y_start - header_height, w, (len(dados) * row_height) + header_height, stroke=1, fill=0)

        for i in range(1, n_cols):
            lx = x + (i * col_width)
            c.setStrokeColor(self.cor_borda)
            c.setLineWidth(0.3)
            c.line(lx, y_start - header_height, lx, y_start - header_height - (len(dados) * row_height))

        return y

    def _draw_footer_profissional(self, c):
        x = self.margin
        w = self.page_width - 2 * self.margin
        y = 15 * mm

        c.setStrokeColor(self.cor_borda)
        c.setLineWidth(0.5)
        c.line(x, y + 5*mm, x + w, y + 5*mm)

        c.setFont("Helvetica", 7)
        c.setFillColor(self.cor_cinza)
        c.drawString(x, y, 
            f"FALL CONSTRUÇÕES - Documento gerado em {datetime.now().strftime('%d/%m/%Y %H:%M')} - Página {c.getPageNumber()}")
        c.setFillColor(self.cor_texto)


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

        self.notebook.add(self.tab_estoque,  text="  Estoque")
        self.notebook.add(self.tab_vendas,   text="  Vendas")
        self.notebook.add(self.tab_ranking,  text="  Ranking")

        self._build_estoque_tab()
        self._build_vendas_tab()
        self._build_ranking_tab()

    # ── Aba Estoque ───────────────────────────────────────────────────────────
    def _build_estoque_tab(self):
        toolbar = tk.Frame(self.tab_estoque, bg=ModernTheme.BG)
        toolbar.pack(fill=tk.X, padx=16, pady=8)

        tk.Button(toolbar, text="Atualizar", command=self._load_estoque,
                 bg=ModernTheme.PRIMARY, fg='white', bd=0, padx=15, pady=8,
                 font=('Segoe UI', 10, 'bold'), cursor='hand2').pack(side=tk.LEFT)
        tk.Button(toolbar, text="Imprimir", command=self._imprimir_estoque,
                 bg=ModernTheme.INFO, fg='white', bd=0, padx=15, pady=8,
                 font=('Segoe UI', 10, 'bold'), cursor='hand2').pack(side=tk.LEFT, padx=6)

        self.estoque_kpi = tk.Frame(self.tab_estoque, bg=ModernTheme.BG)
        self.estoque_kpi.pack(fill=tk.X, padx=16, pady=(0, 8))

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
                # CORREÇÃO: 5 elementos no tuple, desempacotar em 5 variáveis
                kpis = [
                    ("Total Produtos",   str(r.get("total_produtos") or 0),    ModernTheme.PRIMARY),
                    ("Total Itens",      str(r.get("total_itens") or 0),       ModernTheme.INFO),
                    ("Valor Custo",      f"R$ {float(r.get('valor_estoque_custo') or 0):,.2f}", ModernTheme.DANGER),
                    ("Valor Venda",      f"R$ {float(r.get('valor_estoque_venda') or 0):,.2f}", ModernTheme.SUCCESS),
                    ("Lucro Potencial",  f"R$ {float(r.get('lucro_potencial') or 0):,.2f}",     ModernTheme.WARNING),
                ]
                # CORREÇÃO: Desempacotar em 5 variáveis (icon, title, val, color, _)
                # ou remover o icon se não for usar
                for title, val, color in kpis:
                    c = tk.Frame(self.estoque_kpi, bg=ModernTheme.CARD_BG,
                                 highlightbackground=ModernTheme.BORDER,
                                 highlightthickness=1)
                    c.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=4)
                    tk.Frame(c, bg=color, height=3).pack(fill=tk.X)
                    inner = tk.Frame(c, bg=ModernTheme.CARD_BG, padx=12, pady=10)
                    inner.pack()
                    tk.Label(inner, text=title,
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

        tk.Button(toolbar, text="Atualizar", command=self._load_vendas,
                 bg=ModernTheme.PRIMARY, fg='white', bd=0, padx=15, pady=8,
                 font=('Segoe UI', 10, 'bold'), cursor='hand2').pack(side=tk.LEFT)
        tk.Button(toolbar, text="Imprimir", command=self._imprimir_vendas,
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
                dia_str = self._format_date_value(d.get("dia"))
                self.vendas_tree.insert("", tk.END, values=(
                    dia_str, 
                    d["total_vendas"],
                    f"R$ {float(d['total_faturado'] or 0):,.2f}",
                    f"R$ {float(d['total_descontos'] or 0):,.2f}",
                    f"R$ {float(d['ticket_medio'] or 0):,.2f}",
                ))
        except Exception as e:
            Logger.log(f"Erro relatório vendas: {e}", "ERROR")

    def _format_date_value(self, value):
        """Converte qualquer tipo de data para string DD/MM/AAAA"""
        if value is None:
            return ""
        if isinstance(value, str):
            return value
        if hasattr(value, 'strftime'):
            return value.strftime('%d/%m/%Y')
        return str(value)

    # ── Aba Ranking ───────────────────────────────────────────────────────────
    def _build_ranking_tab(self):
        toolbar = tk.Frame(self.tab_ranking, bg=ModernTheme.BG)
        toolbar.pack(fill=tk.X, padx=16, pady=8)

        tk.Button(toolbar, text="Atualizar", command=self._load_ranking,
                 bg=ModernTheme.PRIMARY, fg='white', bd=0, padx=15, pady=8,
                 font=('Segoe UI', 10, 'bold'), cursor='hand2').pack(side=tk.LEFT)
        tk.Button(toolbar, text="Imprimir", command=self._imprimir_ranking,
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
                medal = {1: "1.", 2: "2.", 3: "3."}.get(i, f"{i:>2}.")
                self.ranking_tree.insert("", tk.END, values=(
                    f"{medal}  {d['nome']}",
                    d["codigo"],
                    d.get("total_vendido") or 0,
                    f"R$ {float(d.get('total_faturado') or 0):,.2f}",
                ))
        except Exception as e:
            Logger.log(f"Erro ranking: {e}", "ERROR")

    # ═══════════════════════════════════════════════════════════════════
    # IMPRESSÃO PDF PROFISSIONAL
    # ═══════════════════════════════════════════════════════════════════

    def _imprimir_estoque(self):
        """Gera PDF do relatório de estoque com GRÁFICO DE BARRAS HORIZONTAL"""
        try:
            from utils.relatorio import RelatorioController
            rel = RelatorioController()
            dados_raw = rel.estoque_atual()
            resumo = rel.resumo_financeiro()

            # Prepara dados da tabela
            dados = []
            for d in dados_raw:
                dados.append([
                    d["categoria"], 
                    str(d["total_produtos"]), 
                    str(d["total_itens"]),
                    f"R$ {float(d['valor_custo'] or 0):,.2f}",
                    f"R$ {float(d['valor_venda'] or 0):,.2f}",
                    f"R$ {float(d['lucro_potencial'] or 0):,.2f}",
                ])

            # Prepara dados do GRÁFICO DE BARRAS HORIZONTAL
            categorias = [d["categoria"] for d in dados_raw[:6]]
            valores = [float(d["valor_venda"] or 0) for d in dados_raw[:6]]

            dados_grafico = {
                'titulo': 'Distribuição por Categoria (Valor de Venda)',
                'labels': categorias,
                'valores': valores
            }

            parametros = {
                'Tipo': 'Relatório de Estoque',
                'Data': datetime.now().strftime('%d/%m/%Y'),
                'Total Categorias': str(len(dados_raw))
            }

            self._gerar_pdf_profissional(
                "RELATÓRIO DE ESTOQUE",
                dados,
                ["Categoria", "Produtos", "Itens", "Valor Custo", "Valor Venda", "Lucro Pot."],
                parametros=parametros,
                tipo_grafico='barra_horizontal',
                dados_grafico=dados_grafico
            )

        except Exception as e:
            Logger.log(f"Erro ao gerar PDF estoque: {e}", "ERROR")
            messagebox.showerror("Erro", f"Não foi possível gerar PDF: {e}")

    def _imprimir_vendas(self):
        """Gera PDF do relatório de vendas com gráfico de barras vertical"""
        try:
            from utils.relatorio import RelatorioController
            rel = RelatorioController()
            dados_raw = rel.vendas_periodo(self.data_inicio.get(), self.data_fim.get())

            # Prepara dados da tabela
            dados = []
            for d in dados_raw:
                dia_str = self._format_date_value(d.get("dia"))
                dados.append([
                    dia_str,
                    str(d["total_vendas"]),
                    f"R$ {float(d['total_faturado'] or 0):,.2f}",
                    f"R$ {float(d['total_descontos'] or 0):,.2f}",
                    f"R$ {float(d['ticket_medio'] or 0):,.2f}",
                ])

            # Prepara dados do gráfico
            dias = [self._format_date_value(d.get("dia"))[-5:] for d in dados_raw[-10:]]
            faturado = [float(d["total_faturado"] or 0) for d in dados_raw[-10:]]

            dados_grafico = {
                'titulo': 'Faturamento dos Últimos 10 Dias',
                'labels': dias,
                'valores': faturado
            }

            parametros = {
                'Período': f"{self.data_inicio.get()} a {self.data_fim.get()}",
                'Total de Dias': str(len(dados_raw)),
                'Tipo': 'Relatório de Vendas'
            }

            self._gerar_pdf_profissional(
                "RELATÓRIO DE VENDAS",
                dados,
                ["Dia", "Vendas", "Faturado", "Descontos", "Ticket Médio"],
                parametros=parametros,
                tipo_grafico='barra',
                dados_grafico=dados_grafico
            )

        except Exception as e:
            Logger.log(f"Erro ao gerar PDF vendas: {e}", "ERROR")
            messagebox.showerror("Erro", f"Não foi possível gerar PDF: {e}")

    def _imprimir_ranking(self):
        """Gera PDF do ranking de produtos com gráfico de barras"""
        try:
            from utils.relatorio import RelatorioController
            rel = RelatorioController()
            dados_raw = rel.ranking_produtos(10)

            dados = []
            for i, d in enumerate(dados_raw, 1):
                medal = {1: "1.", 2: "2.", 3: "3."}.get(i, f"{i}.")
                dados.append([
                    f"{medal} {d['nome']}",
                    d["codigo"],
                    str(d.get("total_vendido") or 0),
                    f"R$ {float(d.get('total_faturado') or 0):,.2f}",
                ])

            nomes = [d["nome"][:15] for d in dados_raw[:5]]
            faturado = [float(d.get("total_faturado") or 0) for d in dados_raw[:5]]

            dados_grafico = {
                'titulo': 'Top 5 Produtos - Faturamento',
                'labels': nomes,
                'valores': faturado
            }

            parametros = {
                'Tipo': 'Ranking de Produtos',
                'Top': '10 produtos',
                'Data': datetime.now().strftime('%d/%m/%Y')
            }

            self._gerar_pdf_profissional(
                "RANKING DE PRODUTOS",
                dados,
                ["Produto", "Código", "Qtd Vendida", "Faturado"],
                parametros=parametros,
                tipo_grafico='barra',
                dados_grafico=dados_grafico
            )

        except Exception as e:
            Logger.log(f"Erro ao gerar PDF ranking: {e}", "ERROR")
            messagebox.showerror("Erro", f"Não foi possível gerar PDF: {e}")

    def _gerar_pdf_profissional(self, titulo, dados, colunas, 
                                 parametros=None, tipo_grafico=None, 
                                 dados_grafico=None):
        try:
            import tempfile
            temp_dir = tempfile.gettempdir()
            pdf_path = os.path.join(temp_dir, f"relatorio_{titulo.replace(' ', '_').lower()}.pdf")
            pdf_path = os.path.normpath(pdf_path)

            Logger.log(f"Gerando PDF: {pdf_path}", "INFO")

            gerador = RelatorioPDFGenerator(LOJA_CONFIG)
            gerador.gerar_relatorio(
                titulo, dados, colunas,
                parametros=parametros,
                tipo_grafico=tipo_grafico,
                dados_grafico=dados_grafico,
                output_path=pdf_path
            )

            if os.path.exists(pdf_path) and os.path.getsize(pdf_path) > 0:
                Logger.log(f"PDF criado: {pdf_path}", "SUCCESS")

                try:
                    if os.name == "nt":
                        os.startfile(pdf_path)
                except Exception as e2:
                    Logger.log(f"Não abriu: {e2}", "WARNING")

                messagebox.showinfo(
                    "PDF Gerado",
                    f"Relatório salvo em PDF!\n\nArquivo: {os.path.basename(pdf_path)}\nLocal: {temp_dir}"
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
            ("Imprimir (Padrão)",   ModernTheme.PRIMARY, lambda: self._imprimir_texto(text)),
            ("Escolher Impressora", ModernTheme.INFO,    lambda: self._imprimir_dialogo(text)),
            ("Salvar",              ModernTheme.SUCCESS,
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