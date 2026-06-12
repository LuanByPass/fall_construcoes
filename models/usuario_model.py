"""Model de Usuários"""
import hashlib
from models.base_model import BaseModel

class UsuarioModel(BaseModel):
    TABLE_NAME = 'usuarios'

    def create_table(self):
        query = f"""
        CREATE TABLE IF NOT EXISTS {self.TABLE_NAME} (
            id INT AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(50) NOT NULL UNIQUE,
            password_hash VARCHAR(255) NOT NULL,
            nome VARCHAR(100),
            email VARCHAR(100),
            is_admin BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
        super().create_table(query)

    def _hash_password(self, password):
        return hashlib.sha256(password.encode()).hexdigest()

    def create(self, username, password, nome='', email='', is_admin=False):
        query = f"""
            INSERT INTO {self.TABLE_NAME} (username, password_hash, nome, email, is_admin)
            VALUES (%s, %s, %s, %s, %s)
        """
        return self.db.execute(query, (username, self._hash_password(password), 
                                       nome, email, is_admin))

    def authenticate(self, username, password):
        query = f"SELECT * FROM {self.TABLE_NAME} WHERE username = %s AND password_hash = %s"
        result = self.db.execute(query, (username, self._hash_password(password)), fetch=True)
        return result[0] if result else None
