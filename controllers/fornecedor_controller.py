"""Controller de Fornecedores e Contas a Pagar - FALL Construções"""
from models.fornecedor_model import FornecedorModel, ContaPagarModel

try:
    from utils.logger import Logger
except:
    class Logger:
        @classmethod
        def log(cls, msg, level='INFO'):
            print(f"[{level}] {msg}")

class FornecedorController:
    def __init__(self):
        self.fornecedor_model = FornecedorModel()
        self.fornecedor_model.create_table()
        self.conta_model = ContaPagarModel()
        self.conta_model.create_table()

    def criar_fornecedor(self, dados):
        required = ['nome']
        for field in required:
            if not str(dados.get(field, '')).strip():
                return False, f"Campo {field} é obrigatório"

        result = self.fornecedor_model.create(
            dados['nome'], dados.get('cnpj', ''), dados.get('telefone', ''),
            dados.get('email', ''), dados.get('endereco', ''), dados.get('cidade', ''),
            dados.get('estado', ''), dados.get('cep', ''), dados.get('contato_nome', ''),
            dados.get('contato_telefone', ''), int(dados.get('prazo_pagamento', 30)),
            float(dados.get('limite_credito', 0))
        )
        return (True, "Fornecedor criado") if result else (False, "Erro")

    def listar_fornecedores(self, busca=''):
        return self.fornecedor_model.read_all(busca)

    def obter_fornecedor(self, fornecedor_id):
        return self.fornecedor_model.read_by_id(fornecedor_id)

    def criar_conta(self, dados):
        required = ['fornecedor_id', 'descricao', 'valor', 'data_vencimento']
        for field in required:
            if not str(dados.get(field, '')).strip():
                return False, f"Campo {field} é obrigatório"

        result = self.conta_model.create(
            dados['fornecedor_id'], dados['descricao'], dados.get('numero_documento', ''),
            float(dados['valor']), dados['data_vencimento'], dados.get('observacoes', '')
        )
        return (True, "Conta criada") if result else (False, "Erro")

    def listar_contas(self, status=None):
        return self.conta_model.read_all(status)

    def listar_contas_pendentes(self):
        return self.conta_model.read_pendentes()

    def pagar_conta(self, conta_id, valor_pago, data_pagamento, forma_pagamento, juros_multa=0):
        self.conta_model.pagar(conta_id, float(valor_pago), data_pagamento, forma_pagamento, float(juros_multa))
        Logger.log(f"Conta {conta_id} paga", 'SUCCESS')
        return True, "Conta paga com sucesso"
