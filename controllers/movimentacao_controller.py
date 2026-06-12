"""Controller de Movimentações"""
from models.movimentacao_model import MovimentacaoModel

class MovimentacaoController:
    def __init__(self):
        self.model = MovimentacaoModel()
        self.model.create_table()

    def listar(self, produto_id=None, limit=100):
        return self.model.read_all(produto_id, limit)
