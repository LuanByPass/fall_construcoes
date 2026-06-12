"""Model de Movimentações"""
from models.base_model import BaseModel

class MovimentacaoModel(BaseModel):
    TABLE_NAME = 'movimentacoes'

    TIPO_ENTRADA = 'entrada'
    TIPO_SAIDA = 'saida'
    TIPO_AJUSTE = 'ajuste'
    TIPO_VENDA = 'venda'

    def create_table(self):
        query = f"""
        CREATE TABLE IF NOT EXISTS {self.TABLE_NAME} (
            id INT AUTO_INCREMENT PRIMARY KEY,
            produto_id INT NOT NULL,
            tipo ENUM('entrada', 'saida', 'ajuste', 'venda') NOT NULL,
            quantidade INT NOT NULL,
            quantidade_anterior INT NOT NULL,
            quantidade_nova INT NOT NULL,
            motivo VARCHAR(255),
            venda_id INT,
            usuario VARCHAR(100),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (produto_id) REFERENCES produtos(id) ON DELETE CASCADE,
            FOREIGN KEY (venda_id) REFERENCES vendas(id) ON DELETE SET NULL
        )
        """
        super().create_table(query)

    def create(self, produto_id, tipo, quantidade, quantidade_anterior, 
               quantidade_nova, motivo='', venda_id=None, usuario='Sistema'):
        query = f"""
            INSERT INTO {self.TABLE_NAME} 
            (produto_id, tipo, quantidade, quantidade_anterior, quantidade_nova, motivo, venda_id, usuario)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """
        return self.db.execute(query, (produto_id, tipo, quantidade, 
                                       quantidade_anterior, quantidade_nova, 
                                       motivo, venda_id, usuario))

    def read_all(self, produto_id=None, limit=100):
        if produto_id:
            query = f"""
                SELECT m.*, p.nome as produto_nome, p.codigo 
                FROM {self.TABLE_NAME} m
                JOIN produtos p ON m.produto_id = p.id
                WHERE m.produto_id = %s
                ORDER BY m.created_at DESC
                LIMIT %s
            """
            params = (produto_id, limit)
        else:
            query = f"""
                SELECT m.*, p.nome as produto_nome, p.codigo 
                FROM {self.TABLE_NAME} m
                JOIN produtos p ON m.produto_id = p.id
                ORDER BY m.created_at DESC
                LIMIT %s
            """
            params = (limit,)
        return self.db.execute(query, params, fetch=True) or []
