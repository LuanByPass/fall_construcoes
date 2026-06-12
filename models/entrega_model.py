"""Model de Entregas/Frete - FALL Construções"""
from models.base_model import BaseModel

class EntregaModel(BaseModel):
    TABLE_NAME = 'entregas'

    def create_table(self):
        query = f"""
        CREATE TABLE IF NOT EXISTS {self.TABLE_NAME} (
            id INT AUTO_INCREMENT PRIMARY KEY,
            venda_id INT,
            orcamento_id INT,
            cliente_id INT NOT NULL,
            endereco_entrega VARCHAR(255) NOT NULL,
            cidade VARCHAR(100),
            estado VARCHAR(2),
            cep VARCHAR(10),
            telefone_contato VARCHAR(20),
            data_agendada DATE,
            hora_agendada TIME,
            status ENUM('agendada', 'em_transito', 'entregue', 'cancelada') DEFAULT 'agendada',
            valor_frete DECIMAL(10,2) DEFAULT 0.00,
            tipo_veiculo ENUM('moto', 'carro', 'caminhonete', 'caminhao', 'carreta') DEFAULT 'caminhonete',
            motorista VARCHAR(100),
            placa_veiculo VARCHAR(10),
            observacoes TEXT,
            data_entrega TIMESTAMP NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (venda_id) REFERENCES vendas(id) ON DELETE SET NULL,
            FOREIGN KEY (orcamento_id) REFERENCES orcamentos(id) ON DELETE SET NULL,
            FOREIGN KEY (cliente_id) REFERENCES clientes(id)
        )
        """
        super().create_table(query)

    def create(self, venda_id, orcamento_id, cliente_id, endereco, cidade, estado, cep,
               telefone, data_agendada, hora_agendada, valor_frete, tipo_veiculo,
               motorista, placa, observacoes=''):
        query = f"""
            INSERT INTO {self.TABLE_NAME} 
            (venda_id, orcamento_id, cliente_id, endereco_entrega, cidade, estado, cep,
             telefone_contato, data_agendada, hora_agendada, valor_frete, tipo_veiculo,
             motorista, placa_veiculo, observacoes)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        return self.db.execute(query, (venda_id, orcamento_id, cliente_id, endereco, cidade,
                                       estado, cep, telefone, data_agendada, hora_agendada,
                                       valor_frete, tipo_veiculo, motorista, placa, observacoes))

    def read_all(self, status=None, limit=100):
        if status:
            query = f"""
                SELECT e.*, c.nome as cliente_nome, v.numero_venda
                FROM {self.TABLE_NAME} e
                LEFT JOIN clientes c ON e.cliente_id = c.id
                LEFT JOIN vendas v ON e.venda_id = v.id
                WHERE e.status = %s
                ORDER BY e.data_agendada DESC
                LIMIT %s
            """
            params = (status, limit)
        else:
            query = f"""
                SELECT e.*, c.nome as cliente_nome, v.numero_venda
                FROM {self.TABLE_NAME} e
                LEFT JOIN clientes c ON e.cliente_id = c.id
                LEFT JOIN vendas v ON e.venda_id = v.id
                ORDER BY e.data_agendada DESC
                LIMIT %s
            """
            params = (limit,)
        return self.db.execute(query, params, fetch=True) or []

    def read_by_id(self, entrega_id):
        query = f"""
            SELECT e.*, c.nome as cliente_nome, c.telefone, v.numero_venda
            FROM {self.TABLE_NAME} e
            LEFT JOIN clientes c ON e.cliente_id = c.id
            LEFT JOIN vendas v ON e.venda_id = v.id
            WHERE e.id = %s
        """
        result = self.db.execute(query, (entrega_id,), fetch=True)
        return result[0] if result else None

    def update_status(self, entrega_id, status):
        if status == 'entregue':
            query = f"UPDATE {self.TABLE_NAME} SET status = %s, data_entrega = NOW() WHERE id = %s"
        else:
            query = f"UPDATE {self.TABLE_NAME} SET status = %s WHERE id = %s"
        return self.db.execute(query, (status, entrega_id))

    def delete(self, entrega_id):
        query = f"DELETE FROM {self.TABLE_NAME} WHERE id = %s"
        return self.db.execute(query, (entrega_id,))
