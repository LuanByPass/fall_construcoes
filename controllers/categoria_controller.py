"""Controller de Categorias"""
from models.categoria_model import CategoriaModel

class CategoriaController:
    def __init__(self):
        self.model = CategoriaModel()
        self.model.create_table()

    def listar(self):
        return self.model.read_all()

    def criar(self, nome, descricao):
        if not nome.strip():
            return False, "Nome da categoria é obrigatório"
        result = self.model.create(nome.strip(), descricao.strip())
        return (True, "Categoria criada") if result else (False, "Erro ao criar")

    def atualizar(self, categoria_id, nome, descricao):
        if not nome.strip():
            return False, "Nome é obrigatório"
        result = self.model.update(categoria_id, nome.strip(), descricao.strip())
        return (True, "Categoria atualizada") if result else (False, "Erro")

    def deletar(self, categoria_id):
        result = self.model.delete(categoria_id)
        if result is False:
            return False, "Existem produtos vinculados"
        return (True, "Categoria excluída") if result else (False, "Erro")
