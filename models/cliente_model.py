"""Model de Clientes - FALL Construções"""
from models.base_model import BaseModel

class ClienteModel(BaseModel):
    TABLE_NAME = 'clientes'

    def create_table(self):
        query = f"""
        CREATE TABLE IF NOT EXISTS {self.TABLE_NAME} (
            id INT AUTO_INCREMENT PRIMARY KEY,
            nome VARCHAR(200) NOT NULL,
            cpf_cnpj VARCHAR(20) UNIQUE,
            telefone VARCHAR(20),
            email VARCHAR(100),
            endereco VARCHAR(255),
            cidade VARCHAR(100),
            estado VARCHAR(2),
            cep VARCHAR(10),
            tipo ENUM('fisica', 'juridica') DEFAULT 'fisica',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
        super().create_table(query)

    def create(self, nome, cpf_cnpj, telefone, email, endereco, cidade, estado, cep, tipo='fisica'):
        query = f"""
            INSERT INTO {self.TABLE_NAME} (nome, cpf_cnpj, telefone, email, endereco, cidade, estado, cep, tipo)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        return self.db.execute(query, (nome, cpf_cnpj, telefone, email, endereco, cidade, estado, cep, tipo))

    def read_all(self, search=''):
        if search:
            query = f"SELECT * FROM {self.TABLE_NAME} WHERE nome LIKE %s OR cpf_cnpj LIKE %s ORDER BY nome"
            params = (f'%{search}%', f'%{search}%')
        else:
            query = f"SELECT * FROM {self.TABLE_NAME} ORDER BY nome"
            params = ()
        return self.db.execute(query, params, fetch=True) or []

    def read_by_id(self, cliente_id):
        query = f"SELECT * FROM {self.TABLE_NAME} WHERE id = %s"
        result = self.db.execute(query, (cliente_id,), fetch=True)
        return result[0] if result else None

    def update(self, cliente_id, **kwargs):
        allowed = ['nome', 'cpf_cnpj', 'telefone', 'email', 'endereco', 'cidade', 'estado', 'cep', 'tipo']
        fields = []
        values = []
        for key, value in kwargs.items():
            if key in allowed:
                fields.append(f"{key} = %s")
                values.append(value)
        if not fields:
            return None
        values.append(cliente_id)
        query = f"UPDATE {self.TABLE_NAME} SET {', '.join(fields)} WHERE id = %s"
        return self.db.execute(query, tuple(values))

    def delete(self, cliente_id):
        query = f"DELETE FROM {self.TABLE_NAME} WHERE id = %s"
        return self.db.execute(query, (cliente_id,))
