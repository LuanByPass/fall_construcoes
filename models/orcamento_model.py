"""Model de Orçamentos - FALL Construções"""
from models.base_model import BaseModel

class OrcamentoModel(BaseModel):
    TABLE_NAME = 'orcamentos'

    def create_table(self):
        query = f"""
        CREATE TABLE IF NOT EXISTS {self.TABLE_NAME} (
            id INT AUTO_INCREMENT PRIMARY KEY,
            numero_orcamento VARCHAR(20) NOT NULL UNIQUE,
            cliente_id INT,
            vendedor_id INT,
            data_orcamento TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            data_validade DATE,
            subtotal DECIMAL(10,2) DEFAULT 0.00,
            desconto DECIMAL(10,2) DEFAULT 0.00,
            total DECIMAL(10,2) DEFAULT 0.00,
            status ENUM('pendente', 'aprovado', 'rejeitado', 'convertido') DEFAULT 'pendente',
            observacoes TEXT,
            FOREIGN KEY (cliente_id) REFERENCES clientes(id)
        )
        """
        super().create_table(query)

    def create(self, numero, cliente_id, vendedor_id, data_validade, observacoes=''):
        query = f"""
            INSERT INTO {self.TABLE_NAME} (numero_orcamento, cliente_id, vendedor_id, data_validade, observacoes)
            VALUES (%s, %s, %s, %s, %s)
        """
        return self.db.execute(query, (numero, cliente_id, vendedor_id, data_validade, observacoes))

    def read_all(self, status=None, limit=100):
        if status:
            query = f"""
                SELECT o.*, c.nome as cliente_nome, c.telefone
                FROM {self.TABLE_NAME} o
                LEFT JOIN clientes c ON o.cliente_id = c.id
                WHERE o.status = %s
                ORDER BY o.data_orcamento DESC
                LIMIT %s
            """
            params = (status, limit)
        else:
            query = f"""
                SELECT o.*, c.nome as cliente_nome, c.telefone
                FROM {self.TABLE_NAME} o
                LEFT JOIN clientes c ON o.cliente_id = c.id
                ORDER BY o.data_orcamento DESC
                LIMIT %s
            """
            params = (limit,)
        return self.db.execute(query, params, fetch=True) or []

    def read_by_id(self, orcamento_id):
        query = f"""
            SELECT o.*, c.nome as cliente_nome, c.telefone, c.email, c.endereco
            FROM {self.TABLE_NAME} o
            LEFT JOIN clientes c ON o.cliente_id = c.id
            WHERE o.id = %s
        """
        result = self.db.execute(query, (orcamento_id,), fetch=True)
        return result[0] if result else None

    def update_status(self, orcamento_id, status):
        query = f"UPDATE {self.TABLE_NAME} SET status = %s WHERE id = %s"
        return self.db.execute(query, (status, orcamento_id))

    def update_total(self, orcamento_id, subtotal, desconto, total):
        query = f"UPDATE {self.TABLE_NAME} SET subtotal = %s, desconto = %s, total = %s WHERE id = %s"
        return self.db.execute(query, (subtotal, desconto, total, orcamento_id))

    def delete(self, orcamento_id):
        query = f"DELETE FROM {self.TABLE_NAME} WHERE id = %s"
        return self.db.execute(query, (orcamento_id,))

class OrcamentoItemModel(BaseModel):
    TABLE_NAME = 'orcamento_itens'

    def create_table(self):
        query = f"""
        CREATE TABLE IF NOT EXISTS {self.TABLE_NAME} (
            id INT AUTO_INCREMENT PRIMARY KEY,
            orcamento_id INT NOT NULL,
            produto_id INT NOT NULL,
            quantidade INT NOT NULL,
            preco_unitario DECIMAL(10,2) NOT NULL,
            subtotal DECIMAL(10,2) NOT NULL,
            FOREIGN KEY (orcamento_id) REFERENCES orcamentos(id) ON DELETE CASCADE,
            FOREIGN KEY (produto_id) REFERENCES produtos(id)
        )
        """
        super().create_table(query)

    def create(self, orcamento_id, produto_id, quantidade, preco_unitario, subtotal):
        query = f"""
            INSERT INTO {self.TABLE_NAME} (orcamento_id, produto_id, quantidade, preco_unitario, subtotal)
            VALUES (%s, %s, %s, %s, %s)
        """
        return self.db.execute(query, (orcamento_id, produto_id, quantidade, preco_unitario, subtotal))

    def read_by_orcamento(self, orcamento_id):
        query = f"""
            SELECT oi.*, p.nome as produto_nome, p.codigo, p.codigo_barras
            FROM {self.TABLE_NAME} oi
            JOIN produtos p ON oi.produto_id = p.id
            WHERE oi.orcamento_id = %s
        """
        return self.db.execute(query, (orcamento_id,), fetch=True) or []
