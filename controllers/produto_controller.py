"""Controller de Produtos - FALL Construções"""
from models.produto_model import ProdutoModel
from models.movimentacao_model import MovimentacaoModel

try:
    from utils.logger import Logger
except:
    class Logger:
        @classmethod
        def log(cls, msg, level='INFO'):
            print(f"[{level}] {msg}")

class ProdutoController:
    def __init__(self):
        self.model = ProdutoModel()
        self.model.create_table()
        self.movimentacao_model = MovimentacaoModel()
        self.movimentacao_model.create_table()

    def listar(self, busca=''):
        return self.model.read_all(busca)

    def obter(self, produto_id):
        return self.model.read_by_id(produto_id)

    def obter_por_codigo_barras(self, codigo_barras):
        return self.model.read_by_codigo_barras(codigo_barras)

    def criar(self, dados):
        required = ['codigo', 'nome', 'quantidade', 'preco_custo', 'preco_venda']
        for field in required:
            if not str(dados.get(field, '')).strip():
                return False, f"Campo {field} é obrigatório"

        if self.model.read_by_codigo(dados['codigo']):
            return False, "Código já existe"

        result = self.model.create(
            dados['codigo'], dados['nome'], dados.get('descricao', ''),
            dados.get('categoria_id') or None,
            int(dados['quantidade']), int(dados.get('quantidade_minima', 10)),
            float(dados['preco_custo']), float(dados['preco_venda']),
            float(dados.get('preco_atacado', 0)),
            dados.get('unidade', 'UN'), dados.get('localizacao', ''),
            dados.get('fornecedor', ''), dados.get('codigo_barras'),
            dados.get('peso_kg'), dados.get('dimensoes'), dados.get('marca')
        )

        if result:
            self.movimentacao_model.create(
                result, MovimentacaoModel.TIPO_ENTRADA,
                int(dados['quantidade']), 0, int(dados['quantidade']),
                'Cadastro inicial do produto'
            )
            Logger.log(f"Produto criado: {dados['codigo']}", 'SUCCESS')
            return True, "Produto criado com sucesso"
        return False, "Erro ao criar produto"

    def atualizar(self, produto_id, dados):
        produto = self.model.read_by_id(produto_id)
        if not produto:
            return False, "Produto não encontrado"

        if dados.get('codigo') != produto['codigo']:
            existing = self.model.read_by_codigo(dados['codigo'])
            if existing and existing['id'] != produto_id:
                return False, "Código já existe em outro produto"

        result = self.model.update(produto_id, **dados)
        if result is not None:
            Logger.log(f"Produto {produto_id} atualizado", 'SUCCESS')
            return True, "Produto atualizado"
        return False, "Erro ao atualizar"

    def movimentar(self, produto_id, tipo, quantidade, motivo=''):
        if quantidade <= 0:
            return False, "Quantidade deve ser maior que zero"

        produto = self.model.read_by_id(produto_id)
        if not produto:
            return False, "Produto não encontrado"

        qtd_anterior = produto['quantidade']

        if tipo == MovimentacaoModel.TIPO_SAIDA:
            if qtd_anterior < quantidade:
                return False, "Quantidade insuficiente em estoque"
            qtd_nova = qtd_anterior - quantidade
        elif tipo == MovimentacaoModel.TIPO_ENTRADA:
            qtd_nova = qtd_anterior + quantidade
        else:
            qtd_nova = quantidade

        self.model.update(produto_id, quantidade=qtd_nova)
        self.movimentacao_model.create(
            produto_id, tipo, quantidade, qtd_anterior, qtd_nova, motivo
        )

        Logger.log(f"Movimentação {tipo}: produto {produto_id}", 'SUCCESS')
        return True, f"Movimentação de {tipo} registrada. Nova quantidade: {qtd_nova}"

    def deletar(self, produto_id):
        Logger.log(f"Tentando excluir produto ID: {produto_id}", 'INFO')

        produto = self.model.read_by_id(produto_id)
        if not produto:
            return False, "Produto não encontrado"

        try:
            self.model.delete(produto_id)
            verificacao = self.model.read_by_id(produto_id)

            if verificacao is None:
                Logger.log(f"Produto {produto_id} excluído", 'SUCCESS')
                return True, "Produto excluído com sucesso"
            else:
                return False, "Erro ao excluir produto"
        except Exception as e:
            Logger.log(f"Erro ao excluir: {e}", 'ERROR')
            return False, f"Erro ao excluir: {str(e)}"

    def baixo_estoque(self):
        return self.model.get_baixo_estoque()

    def valor_total(self):
        return self.model.get_valor_total()
