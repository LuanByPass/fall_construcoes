"""Model de Fornecedores - FALL Construções
CORRIGIDO: Remove CURRENT_DATE (não suportado no MySQL para DATE DEFAULT)
"""
from models.base_model import BaseModel

class FornecedorModel(BaseModel):
    TABLE_NAME = 'fornecedores'

    def create_table(self):
        query = f"""
        CREATE TABLE IF NOT EXISTS {self.TABLE_NAME} (
            id INT AUTO_INCREMENT PRIMARY KEY,
            nome VARCHAR(200) NOT NULL,
            cnpj VARCHAR(20) UNIQUE,
            telefone VARCHAR(20),
            email VARCHAR(100),
            endereco VARCHAR(255),
            cidade VARCHAR(100),
            estado VARCHAR(2),
            cep VARCHAR(10),
            contato_nome VARCHAR(100),
            contato_telefone VARCHAR(20),
            prazo_pagamento INT DEFAULT 30,
            limite_credito DECIMAL(10,2) DEFAULT 0.00,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
        super().create_table(query)

    def create(self, nome, cnpj, telefone, email, endereco, cidade, estado, cep,
               contato_nome, contato_telefone, prazo_pagamento, limite_credito):
        query = f"""
            INSERT INTO {self.TABLE_NAME} 
            (nome, cnpj, telefone, email, endereco, cidade, estado, cep,
             contato_nome, contato_telefone, prazo_pagamento, limite_credito)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        return self.db.execute(query, (nome, cnpj, telefone, email, endereco, cidade, estado, cep,
                                         contato_nome, contato_telefone, prazo_pagamento, limite_credito))

    def read_all(self, search=''):
        if search:
            query = f"SELECT * FROM {self.TABLE_NAME} WHERE nome LIKE %s OR cnpj LIKE %s ORDER BY nome"
            params = (f'%{search}%', f'%{search}%')
        else:
            query = f"SELECT * FROM {self.TABLE_NAME} ORDER BY nome"
            params = ()
        return self.db.execute(query, params, fetch=True) or []

    def read_by_id(self, fornecedor_id):
        query = f"SELECT * FROM {self.TABLE_NAME} WHERE id = %s"
        result = self.db.execute(query, (fornecedor_id,), fetch=True)
        return result[0] if result else None

    def update(self, fornecedor_id, **kwargs):
        allowed = ['nome', 'cnpj', 'telefone', 'email', 'endereco', 'cidade', 'estado', 'cep',
                   'contato_nome', 'contato_telefone', 'prazo_pagamento', 'limite_credito']
        fields = []
        values = []
        for key, value in kwargs.items():
            if key in allowed:
                fields.append(f"{key} = %s")
                values.append(value)
        if not fields:
            return None
        values.append(fornecedor_id)
        query = f"UPDATE {self.TABLE_NAME} SET {', '.join(fields)} WHERE id = %s"
        return self.db.execute(query, tuple(values))

    def delete(self, fornecedor_id):
        query = f"DELETE FROM {self.TABLE_NAME} WHERE id = %s"
        return self.db.execute(query, (fornecedor_id,))


class ContaPagarModel(BaseModel):
    TABLE_NAME = 'contas_pagar'

    def create_table(self):
        query = f"""
        CREATE TABLE IF NOT EXISTS {self.TABLE_NAME} (
            id INT AUTO_INCREMENT PRIMARY KEY,
            fornecedor_id INT NOT NULL,
            descricao VARCHAR(255) NOT NULL,
            numero_documento VARCHAR(50),
            valor DECIMAL(10,2) NOT NULL,
            data_emissao DATE,
            data_vencimento DATE NOT NULL,
            data_pagamento DATE,
            valor_pago DECIMAL(10,2) DEFAULT 0.00,
            juros_multa DECIMAL(10,2) DEFAULT 0.00,
            status ENUM('pendente', 'pago', 'atrasado', 'cancelado') DEFAULT 'pendente',
            forma_pagamento VARCHAR(50),
            observacoes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (fornecedor_id) REFERENCES fornecedores(id)
        )
        """
        super().create_table(query)

    def create(self, fornecedor_id, descricao, numero_documento, valor, data_vencimento, observacoes=''):
        query = f"""
            INSERT INTO {self.TABLE_NAME} (fornecedor_id, descricao, numero_documento, valor, data_vencimento, observacoes)
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        return self.db.execute(query, (fornecedor_id, descricao, numero_documento, valor, data_vencimento, observacoes))

    def read_all(self, status=None):
        if status:
            query = f"""
                SELECT cp.*, f.nome as fornecedor_nome, f.cnpj
                FROM {self.TABLE_NAME} cp
                JOIN fornecedores f ON cp.fornecedor_id = f.id
                WHERE cp.status = %s
                ORDER BY cp.data_vencimento
            """
            params = (status,)
        else:
            query = f"""
                SELECT cp.*, f.nome as fornecedor_nome, f.cnpj
                FROM {self.TABLE_NAME} cp
                JOIN fornecedores f ON cp.fornecedor_id = f.id
                ORDER BY cp.data_vencimento
            """
            params = ()
        return self.db.execute(query, params, fetch=True) or []

    def read_pendentes(self):
        query = f"""
            SELECT cp.*, f.nome as fornecedor_nome
            FROM {self.TABLE_NAME} cp
            JOIN fornecedores f ON cp.fornecedor_id = f.id
            WHERE cp.status IN ('pendente', 'atrasado')
            ORDER BY cp.data_vencimento
        """
        return self.db.execute(query, fetch=True) or []

    def pagar(self, conta_id, valor_pago, data_pagamento, forma_pagamento, juros_multa=0):
        query = f"""
            UPDATE {self.TABLE_NAME} 
            SET status = 'pago', valor_pago = %s, data_pagamento = %s, 
                forma_pagamento = %s, juros_multa = %s
            WHERE id = %s
        """
        return self.db.execute(query, (valor_pago, data_pagamento, forma_pagamento, juros_multa, conta_id))

    def delete(self, conta_id):
        query = f"DELETE FROM {self.TABLE_NAME} WHERE id = %s"
        return self.db.execute(query, (conta_id,))