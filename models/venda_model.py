"""Modelo de Vendas - FALL Construções
CORRIGIDO FINAL: usuario_id (coluna real), status ENUM correto
"""
from utils.database import DatabaseConnection
from datetime import datetime

class VendaModel:
    def __init__(self):
        self.db = DatabaseConnection()
        self.table = 'vendas'

    def create_table(self):
        sql = """
        CREATE TABLE IF NOT EXISTS vendas (
            id INT AUTO_INCREMENT PRIMARY KEY,
            numero_venda VARCHAR(20) UNIQUE,
            cliente_id INT,
            usuario_id INT,
            data_venda TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            subtotal DECIMAL(10,2) DEFAULT 0,
            desconto DECIMAL(10,2) DEFAULT 0,
            total DECIMAL(10,2) DEFAULT 0,
            forma_pagamento ENUM('dinheiro', 'cartao', 'pix', 'boleto', 'crediario') DEFAULT 'dinheiro',
            status ENUM('pendente', 'pago', 'cancelado') DEFAULT 'pendente',
            observacoes TEXT
        )
        """
        self.db.execute(sql)

    def create(self, **kwargs):
        numero = self._gerar_numero()
        kwargs['numero_venda'] = numero

        columns = ', '.join(kwargs.keys())
        placeholders = ', '.join(['%s'] * len(kwargs))
        sql = f"INSERT INTO {self.table} ({columns}) VALUES ({placeholders})"

        last_id = self.db.execute(sql, tuple(kwargs.values()))
        return last_id

    def _gerar_numero(self):
        try:
            result = self.db.execute(
                "SELECT MAX(CAST(SUBSTRING(numero_venda, 6) AS UNSIGNED)) as max_num "
                "FROM vendas WHERE numero_venda LIKE 'VEND-%'",
                fetch=True
            )
            if result and len(result) > 0:
                max_num = result[0].get('max_num') or 0
            else:
                max_num = 0
            return f"VEND-{max_num + 1:06d}"
        except:
            return f"VEND-{datetime.now().strftime('%Y%m%d%H%M%S')}"

    def read_all(self, limit=100, status=None, data_inicio=None, data_fim=None):
        sql = """
            SELECT v.*, c.nome as cliente_nome, c.cpf_cnpj
            FROM vendas v
            LEFT JOIN clientes c ON v.cliente_id = c.id
            WHERE 1=1
        """
        params = []

        if status:
            sql += " AND v.status = %s"
            params.append(status)

        if data_inicio:
            sql += " AND DATE(v.data_venda) >= %s"
            params.append(data_inicio)

        if data_fim:
            sql += " AND DATE(v.data_venda) <= %s"
            params.append(data_fim)

        sql += " ORDER BY v.data_venda DESC LIMIT %s"
        params.append(limit)

        return self.db.execute(sql, tuple(params), fetch=True) or []

    def read_by_id(self, venda_id):
        sql = """
            SELECT v.*, c.nome as cliente_nome, c.cpf_cnpj, c.telefone, c.endereco
            FROM vendas v
            LEFT JOIN clientes c ON v.cliente_id = c.id
            WHERE v.id = %s
        """
        result = self.db.execute(sql, (venda_id,), fetch=True)
        return result[0] if result else None

    def update(self, venda_id, **kwargs):
        if not kwargs:
            return
        columns = ', '.join([f"{k} = %s" for k in kwargs.keys()])
        sql = f"UPDATE {self.table} SET {columns} WHERE id = %s"
        values = list(kwargs.values()) + [venda_id]
        self.db.execute(sql, tuple(values))

    def update_status(self, venda_id, status):
        self.update(venda_id, status=status)


class VendaItemModel:
    def __init__(self):
        self.db = DatabaseConnection()
        self.table = 'venda_itens'

    def create_table(self):
        sql = """
        CREATE TABLE IF NOT EXISTS venda_itens (
            id INT AUTO_INCREMENT PRIMARY KEY,
            venda_id INT NOT NULL,
            produto_id INT NOT NULL,
            quantidade INT NOT NULL,
            preco_unitario DECIMAL(10,2) DEFAULT 0,
            subtotal DECIMAL(10,2) DEFAULT 0,
            FOREIGN KEY (venda_id) REFERENCES vendas(id),
            FOREIGN KEY (produto_id) REFERENCES produtos(id)
        )
        """
        self.db.execute(sql)

    def create(self, **kwargs):
        # Calcula subtotal se não fornecido
        if 'subtotal' not in kwargs and 'quantidade' in kwargs and 'preco_unitario' in kwargs:
            kwargs['subtotal'] = float(kwargs['quantidade']) * float(kwargs['preco_unitario'])

        columns = ', '.join(kwargs.keys())
        placeholders = ', '.join(['%s'] * len(kwargs))
        sql = f"INSERT INTO {self.table} ({columns}) VALUES ({placeholders})"
        return self.db.execute(sql, tuple(kwargs.values()))

    def read_by_venda(self, venda_id):
        sql = """
            SELECT vi.*, p.nome as produto_nome, p.codigo as produto_codigo
            FROM venda_itens vi
            JOIN produtos p ON vi.produto_id = p.id
            WHERE vi.venda_id = %s
        """
        return self.db.execute(sql, (venda_id,), fetch=True) or []