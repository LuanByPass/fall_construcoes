"""Controller de Entregas - FALL Construções"""
from models.entrega_model import EntregaModel
from models.cliente_model import ClienteModel

try:
    from utils.logger import Logger
except:
    class Logger:
        @classmethod
        def log(cls, msg, level='INFO'):
            print(f"[{level}] {msg}")

class EntregaController:
    def __init__(self):
        self.entrega_model = EntregaModel()
        self.entrega_model.create_table()
        self.cliente_model = ClienteModel()
        self.cliente_model.create_table()

    def criar_entrega(self, dados):
        required = ['cliente_id', 'endereco_entrega', 'data_agendada']
        for field in required:
            if not str(dados.get(field, '')).strip():
                return False, f"Campo {field} é obrigatório"

        result = self.entrega_model.create(
            dados.get('venda_id'), dados.get('orcamento_id'),
            dados['cliente_id'], dados['endereco_entrega'],
            dados.get('cidade', ''), dados.get('estado', ''),
            dados.get('cep', ''), dados.get('telefone_contato', ''),
            dados['data_agendada'], dados.get('hora_agendada', '08:00'),
            float(dados.get('valor_frete', 0)),
            dados.get('tipo_veiculo', 'caminhonete'),
            dados.get('motorista', ''), dados.get('placa_veiculo', ''),
            dados.get('observacoes', '')
        )

        if result:
            Logger.log(f"Entrega agendada: {result}", 'SUCCESS')
            return True, "Entrega agendada com sucesso"
        return False, "Erro ao agendar entrega"

    def listar(self, status=None):
        return self.entrega_model.read_all(status)

    def obter(self, entrega_id):
        return self.entrega_model.read_by_id(entrega_id)

    def atualizar_status(self, entrega_id, status):
        self.entrega_model.update_status(entrega_id, status)
        Logger.log(f"Entrega {entrega_id} -> {status}", 'SUCCESS')
        return True, f"Status atualizado para {status}"

    def listar_clientes(self, busca=''):
        return self.cliente_model.read_all(busca)
