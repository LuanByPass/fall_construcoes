"""Model de Produtos - FALL Construções"""
from models.base_model import BaseModel

class ProdutoModel(BaseModel):
    TABLE_NAME = 'produtos'

    def create_table(self):
        query = f"""
        CREATE TABLE IF NOT EXISTS {self.TABLE_NAME} (
            id INT AUTO_INCREMENT PRIMARY KEY,
            codigo VARCHAR(50) NOT NULL UNIQUE,
            codigo_barras VARCHAR(50) UNIQUE,
            nome VARCHAR(200) NOT NULL,
            descricao TEXT,
            categoria_id INT,
            quantidade INT DEFAULT 0,
            quantidade_minima INT DEFAULT 10,
            preco_custo DECIMAL(10,2) DEFAULT 0.00,
            preco_venda DECIMAL(10,2) DEFAULT 0.00,
            preco_atacado DECIMAL(10,2) DEFAULT 0.00,
            unidade VARCHAR(20) DEFAULT 'UN',
            localizacao VARCHAR(100),
            fornecedor VARCHAR(200),
            peso_kg DECIMAL(8,2),
            dimensoes VARCHAR(50),
            marca VARCHAR(100),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            FOREIGN KEY (categoria_id) REFERENCES categorias(id) ON DELETE SET NULL
        )
        """
        super().create_table(query)

    def create(self, codigo, nome, descricao, categoria_id, quantidade, 
               quantidade_minima, preco_custo, preco_venda, preco_atacado,
               unidade, localizacao, fornecedor, codigo_barras=None, 
               peso_kg=None, dimensoes=None, marca=None):
        query = f"""
            INSERT INTO {self.TABLE_NAME} 
            (codigo, codigo_barras, nome, descricao, categoria_id, quantidade, 
             quantidade_minima, preco_custo, preco_venda, preco_atacado, 
             unidade, localizacao, fornecedor, peso_kg, dimensoes, marca)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        return self.db.execute(query, (codigo, codigo_barras, nome, descricao, 
                                       categoria_id, quantidade, quantidade_minima,
                                       preco_custo, preco_venda, preco_atacado,
                                       unidade, localizacao, fornecedor, 
                                       peso_kg, dimensoes, marca))

    def read_all(self, search=''):
        if search:
            query = f"""
                SELECT p.*, c.nome as categoria_nome 
                FROM {self.TABLE_NAME} p
                LEFT JOIN categorias c ON p.categoria_id = c.id
                WHERE p.nome LIKE %s OR p.codigo LIKE %s OR p.codigo_barras LIKE %s OR p.descricao LIKE %s
                ORDER BY p.nome
            """
            params = (f'%{search}%', f'%{search}%', f'%{search}%', f'%{search}%')
        else:
            query = f"""
                SELECT p.*, c.nome as categoria_nome 
                FROM {self.TABLE_NAME} p
                LEFT JOIN categorias c ON p.categoria_id = c.id
                ORDER BY p.nome
            """
            params = ()
        return self.db.execute(query, params, fetch=True) or []

    def read_by_id(self, produto_id):
        query = f"""
            SELECT p.*, c.nome as categoria_nome 
            FROM {self.TABLE_NAME} p
            LEFT JOIN categorias c ON p.categoria_id = c.id
            WHERE p.id = %s
        """
        result = self.db.execute(query, (produto_id,), fetch=True)
        return result[0] if result else None

    def read_by_codigo(self, codigo):
        query = f"SELECT * FROM {self.TABLE_NAME} WHERE codigo = %s"
        result = self.db.execute(query, (codigo,), fetch=True)
        return result[0] if result else None

    def read_by_codigo_barras(self, codigo_barras):
        query = f"""
            SELECT p.*, c.nome as categoria_nome 
            FROM {self.TABLE_NAME} p
            LEFT JOIN categorias c ON p.categoria_id = c.id
            WHERE p.codigo_barras = %s
        """
        result = self.db.execute(query, (codigo_barras,), fetch=True)
        return result[0] if result else None

    def update(self, produto_id, **kwargs):
        allowed = ['codigo', 'codigo_barras', 'nome', 'descricao', 'categoria_id', 
                   'quantidade', 'quantidade_minima', 'preco_custo', 'preco_venda', 
                   'preco_atacado', 'unidade', 'localizacao', 'fornecedor',
                   'peso_kg', 'dimensoes', 'marca']
        fields = []
        values = []
        for key, value in kwargs.items():
            if key in allowed:
                fields.append(f"{key} = %s")
                values.append(value)
        if not fields:
            return None
        values.append(produto_id)
        query = f"UPDATE {self.TABLE_NAME} SET {', '.join(fields)} WHERE id = %s"
        return self.db.execute(query, tuple(values))

    def update_quantidade(self, produto_id, quantidade):
        query = f"UPDATE {self.TABLE_NAME} SET quantidade = quantidade + %s WHERE id = %s"
        return self.db.execute(query, (quantidade, produto_id))

    def delete(self, produto_id):
        query = f"DELETE FROM {self.TABLE_NAME} WHERE id = %s"
        return self.db.execute(query, (produto_id,))

    def get_baixo_estoque(self):
        query = f"""
            SELECT p.*, c.nome as categoria_nome 
            FROM {self.TABLE_NAME} p
            LEFT JOIN categorias c ON p.categoria_id = c.id
            WHERE p.quantidade <= p.quantidade_minima
            ORDER BY p.quantidade ASC
        """
        return self.db.execute(query, fetch=True) or []

    def get_valor_total(self):
        query = f"SELECT SUM(quantidade * preco_custo) as total FROM {self.TABLE_NAME}"
        result = self.db.execute(query, fetch=True)
        return result[0]['total'] if result else 0
