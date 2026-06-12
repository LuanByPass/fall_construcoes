"""Model de Categorias"""
from models.base_model import BaseModel

class CategoriaModel(BaseModel):
    TABLE_NAME = 'categorias'

    def create_table(self):
        query = f"""
        CREATE TABLE IF NOT EXISTS {self.TABLE_NAME} (
            id INT AUTO_INCREMENT PRIMARY KEY,
            nome VARCHAR(100) NOT NULL UNIQUE,
            descricao TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
        super().create_table(query)

    def create(self, nome, descricao=''):
        query = f"INSERT INTO {self.TABLE_NAME} (nome, descricao) VALUES (%s, %s)"
        return self.db.execute(query, (nome, descricao))

    def read_all(self):
        query = f"SELECT * FROM {self.TABLE_NAME} ORDER BY nome"
        return self.db.execute(query, fetch=True) or []

    def read_by_id(self, categoria_id):
        query = f"SELECT * FROM {self.TABLE_NAME} WHERE id = %s"
        result = self.db.execute(query, (categoria_id,), fetch=True)
        return result[0] if result else None

    def update(self, categoria_id, nome, descricao):
        query = f"UPDATE {self.TABLE_NAME} SET nome = %s, descricao = %s WHERE id = %s"
        return self.db.execute(query, (nome, descricao, categoria_id))

    def delete(self, categoria_id):
        check = "SELECT COUNT(*) as total FROM produtos WHERE categoria_id = %s"
        result = self.db.execute(check, (categoria_id,), fetch=True)
        if result and result[0]['total'] > 0:
            return False
        query = f"DELETE FROM {self.TABLE_NAME} WHERE id = %s"
        return self.db.execute(query, (categoria_id,))
