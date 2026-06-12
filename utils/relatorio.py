"""Funções de relatório para FALL Construções"""
from utils.database import DatabaseConnection
from datetime import datetime, timedelta

try:
    from utils.logger import Logger
except:
    class Logger:
        @classmethod
        def log(cls, msg, level='INFO'):
            print(f"[{level}] {msg}")

class RelatorioController:
    def __init__(self):
        self.db = DatabaseConnection()

    def estoque_atual(self):
        """Relatório completo do estoque"""
        query = """
            SELECT 
                c.nome AS categoria,
                COUNT(p.id) AS total_produtos,
                SUM(p.quantidade) AS total_itens,
                SUM(p.quantidade * p.preco_custo) AS valor_custo,
                SUM(p.quantidade * p.preco_venda) AS valor_venda,
                SUM(p.quantidade * (p.preco_venda - p.preco_custo)) AS lucro_potencial
            FROM categorias c
            LEFT JOIN produtos p ON c.id = p.categoria_id
            GROUP BY c.id, c.nome
            ORDER BY valor_custo DESC
        """
        return self.db.execute(query, fetch=True) or []

    def produtos_baixo_estoque(self):
        """Produtos com estoque crítico"""
        query = """
            SELECT p.*, c.nome AS categoria_nome
            FROM produtos p
            LEFT JOIN categorias c ON p.categoria_id = c.id
            WHERE p.quantidade <= p.quantidade_minima
            ORDER BY (p.quantidade / p.quantidade_minima) ASC
        """
        return self.db.execute(query, fetch=True) or []

    def vendas_periodo(self, inicio=None, fim=None):
        """Vendas por período"""
        if not inicio:
            inicio = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        if not fim:
            fim = datetime.now().strftime('%Y-%m-%d')

        query = """
            SELECT 
                DATE(data_venda) AS dia,
                COUNT(*) AS total_vendas,
                SUM(total) AS total_faturado,
                SUM(desconto) AS total_descontos,
                AVG(total) AS ticket_medio
            FROM vendas
            WHERE DATE(data_venda) BETWEEN %s AND %s
              AND status != 'cancelado'
            GROUP BY DATE(data_venda)
            ORDER BY dia DESC
        """
        return self.db.execute(query, (inicio, fim), fetch=True) or []

    def ranking_produtos(self, limite=10):
        """Produtos mais vendidos"""
        query = """
            SELECT 
                p.nome, p.codigo,
                SUM(vi.quantidade) AS total_vendido,
                SUM(vi.subtotal) AS total_faturado
            FROM produtos p
            LEFT JOIN venda_itens vi ON p.id = vi.produto_id
            GROUP BY p.id, p.nome, p.codigo
            ORDER BY total_vendido DESC
            LIMIT %s
        """
        return self.db.execute(query, (limite,), fetch=True) or []

    def resumo_financeiro(self):
        """Resumo financeiro geral"""
        query = """
            SELECT 
                COUNT(*) AS total_produtos,
                SUM(quantidade) AS total_itens,
                SUM(quantidade * preco_custo) AS valor_estoque_custo,
                SUM(quantidade * preco_venda) AS valor_estoque_venda,
                SUM(quantidade * (preco_venda - preco_custo)) AS lucro_potencial
            FROM produtos
        """
        return self.db.execute(query, fetch=True) or []

    def clientes_top(self, limite=10):
        """Clientes que mais compram - CORRIGIDO"""
        query = """
            SELECT 
                c.nome, c.cpf_cnpj,
                COUNT(v.id) AS total_compras,
                SUM(COALESCE(v.total, 0)) AS total_gasto
            FROM clientes c
            LEFT JOIN vendas v ON c.id = v.cliente_id 
                AND v.status != 'cancelado'
            GROUP BY c.id, c.nome, c.cpf_cnpj
            ORDER BY total_gasto DESC
            LIMIT %s
        """
        return self.db.execute(query, (limite,), fetch=True) or []
