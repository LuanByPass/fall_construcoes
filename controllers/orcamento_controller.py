"""Controller de Orçamentos - FALL Construções"""
import random
import string
from datetime import datetime, timedelta
from models.orcamento_model import OrcamentoModel, OrcamentoItemModel
from models.produto_model import ProdutoModel
from models.cliente_model import ClienteModel

try:
    from utils.logger import Logger
except:
    class Logger:
        @classmethod
        def log(cls, msg, level='INFO'):
            print(f"[{level}] {msg}")

class OrcamentoController:
    def __init__(self):
        self.orcamento_model = OrcamentoModel()
        self.orcamento_model.create_table()
        self.item_model = OrcamentoItemModel()
        self.item_model.create_table()
        self.produto_model = ProdutoModel()
        self.produto_model.create_table()
        self.cliente_model = ClienteModel()
        self.cliente_model.create_table()

    def _gerar_numero(self):
        data = datetime.now().strftime('%Y%m%d')
        random_num = ''.join(random.choices(string.digits, k=4))
        return f"ORC-{data}-{random_num}"

    def criar_orcamento(self, cliente_id, vendedor_id, dias_validade=7, observacoes=''):
        numero = self._gerar_numero()
        data_validade = (datetime.now() + timedelta(days=dias_validade)).strftime('%Y-%m-%d')

        orcamento_id = self.orcamento_model.create(numero, cliente_id, vendedor_id, data_validade, observacoes)
        if orcamento_id:
            Logger.log(f"Orçamento criado: {numero}", 'SUCCESS')
            return True, {"id": orcamento_id, "numero": numero}
        return False, "Erro ao criar orçamento"

    def adicionar_item(self, orcamento_id, produto_id, quantidade):
        produto = self.produto_model.read_by_id(produto_id)
        if not produto:
            return False, "Produto não encontrado"

        preco = float(produto['preco_venda'])
        subtotal = preco * quantidade

        self.item_model.create(orcamento_id, produto_id, quantidade, preco, subtotal)
        Logger.log(f"Item adicionado ao orçamento: {produto['nome']} x{quantidade}", 'SUCCESS')
        return True, "Item adicionado"

    def finalizar_orcamento(self, orcamento_id, desconto=0):
        itens = self.item_model.read_by_orcamento(orcamento_id)
        if not itens:
            return False, "Orçamento sem itens"

        subtotal = sum(float(item['subtotal']) for item in itens)
        total = subtotal - float(desconto)
        if total < 0:
            total = 0

        self.orcamento_model.update_total(orcamento_id, subtotal, desconto, total)
        Logger.log(f"Orçamento {orcamento_id} finalizado. Total: R$ {total:.2f}", 'SUCCESS')
        return True, {"subtotal": subtotal, "desconto": desconto, "total": total}

    def converter_em_venda(self, orcamento_id, venda_controller):
        """Converte orçamento aprovado em venda"""
        orcamento = self.orcamento_model.read_by_id(orcamento_id)
        if not orcamento:
            return False, "Orçamento não encontrado"

        if orcamento['status'] != 'aprovado':
            return False, "Orçamento deve estar aprovado para converter"

        itens = self.item_model.read_by_orcamento(orcamento_id)

        # Cria venda
        success, venda = venda_controller.criar_venda(
            orcamento['cliente_id'], 
            forma_pagamento='dinheiro',
            observacoes=f"Convertido do orçamento {orcamento['numero_orcamento']}"
        )

        if not success:
            return False, venda

        # Adiciona itens
        for item in itens:
            venda_controller.adicionar_item(venda['id'], item['produto_id'], item['quantidade'])

        # Finaliza venda
        venda_controller.finalizar_venda(venda['id'], orcamento['desconto'])

        # Atualiza status do orçamento
        self.orcamento_model.update_status(orcamento_id, 'convertido')

        Logger.log(f"Orçamento {orcamento_id} convertido em venda {venda['numero']}", 'SUCCESS')
        return True, venda

    def listar(self, status=None):
        return self.orcamento_model.read_all(status)

    def obter(self, orcamento_id):
        orcamento = self.orcamento_model.read_by_id(orcamento_id)
        if orcamento:
            orcamento['itens'] = self.item_model.read_by_orcamento(orcamento_id)
        return orcamento

    def aprovar(self, orcamento_id):
        self.orcamento_model.update_status(orcamento_id, 'aprovado')
        Logger.log(f"Orçamento {orcamento_id} aprovado", 'SUCCESS')
        return True, "Orçamento aprovado"

    def rejeitar(self, orcamento_id):
        self.orcamento_model.update_status(orcamento_id, 'rejeitado')
        Logger.log(f"Orçamento {orcamento_id} rejeitado", 'WARNING')
        return True, "Orçamento rejeitado"

    def listar_clientes(self, busca=''):
        return self.cliente_model.read_all(busca)
