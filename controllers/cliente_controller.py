"""Controller de Clientes - FALL Construções
CORRIGIDO: Usa read_all() + filtro em Python (sem read_by_cliente)
"""
from models.cliente_model import ClienteModel
from models.venda_model import VendaModel, VendaItemModel

try:
    from utils.logger import Logger
except:
    class Logger:
        @classmethod
        def log(cls, msg, level='INFO'):
            print(f"[{level}] {msg}")


class ClienteController:
    def __init__(self):
        self.cliente_model = ClienteModel()
        self.cliente_model.create_table()
        self.venda_model = VendaModel()
        self.venda_item_model = VendaItemModel()

    def criar(self, dados):
        """Cria novo cliente"""
        try:
            cliente_id = self.cliente_model.create(**dados)
            Logger.log(f"Cliente criado: {dados.get('nome')}", 'SUCCESS')
            return True, "✅ Cliente criado com sucesso!"
        except Exception as e:
            return False, f"❌ Erro ao criar cliente: {e}"

    def listar_todos(self):
        """Lista todos os clientes"""
        return self.cliente_model.read_all()

    def buscar(self, termo):
        """Busca clientes por nome, cpf ou telefone"""
        return self.cliente_model.search(termo)

    def obter(self, cliente_id):
        """Obtém cliente por ID"""
        return self.cliente_model.read_by_id(cliente_id)

    def atualizar(self, cliente_id, dados):
        """Atualiza dados do cliente"""
        try:
            self.cliente_model.update(cliente_id, **dados)
            Logger.log(f"Cliente {cliente_id} atualizado", 'SUCCESS')
            return True, "✅ Cliente atualizado com sucesso!"
        except Exception as e:
            return False, f"❌ Erro ao atualizar: {e}"

    def deletar(self, cliente_id):
        """Deleta cliente com verificação de vínculos"""
        # ✅ CORREÇÃO: Usa read_all() + filtro em Python
        todas_vendas = self.venda_model.read_all(limit=10000)
        vendas_cliente = [v for v in todas_vendas if v.get('cliente_id') == cliente_id]

        if vendas_cliente:
            return False, f"❌ Cliente possui {len(vendas_cliente)} venda(s). Não pode ser excluído."

        try:
            self.cliente_model.delete(cliente_id)
            Logger.log(f"Cliente {cliente_id} excluído", 'WARNING')
            return True, "✅ Cliente excluído com sucesso!"
        except Exception as e:
            return False, f"❌ Erro ao excluir: {e}"

    def get_estatisticas(self, cliente_id):
        """Retorna estatísticas do cliente"""
        # ✅ CORREÇÃO: Usa read_all() + filtro em Python
        todas_vendas = self.venda_model.read_all(limit=10000)
        vendas_cliente = [v for v in todas_vendas if v.get('cliente_id') == cliente_id and v.get('status') == 'finalizada']

        total_compras = len(vendas_cliente)
        total_gasto = sum(float(v.get('total', 0)) for v in vendas_cliente)

        # Conta produtos diferentes
        produtos_ids = set()
        for v in vendas_cliente:
            itens = self.venda_item_model.read_by_venda(v['id'])
            for item in itens:
                produtos_ids.add(item.get('produto_id'))

        ultima = vendas_cliente[-1] if vendas_cliente else None
        ultima_data = ''
        if ultima and ultima.get('data_hora'):
            if isinstance(ultima['data_hora'], str):
                ultima_data = ultima['data_hora'][:10]
            else:
                ultima_data = ultima['data_hora'].strftime('%d/%m/%Y')

        return {
            'total_compras': total_compras,
            'total_gasto': total_gasto,
            'produtos_diferentes': len(produtos_ids),
            'ultima_compra': ultima_data if ultima_data else 'Nunca'
        }

    def get_compras(self, cliente_id):
        """Retorna histórico de compras do cliente"""
        # ✅ CORREÇÃO: Usa read_all() + filtro em Python
        todas_vendas = self.venda_model.read_all(limit=10000)
        vendas_cliente = [v for v in todas_vendas if v.get('cliente_id') == cliente_id]

        resultado = []
        for v in vendas_cliente:
            itens = self.venda_item_model.read_by_venda(v['id'])
            resultado.append({
                'id': v['id'],
                'numero': v.get('numero', 'N/A'),
                'data_hora': v.get('data_hora'),
                'total_itens': len(itens),
                'total': v.get('total', 0),
                'forma_pagamento': v.get('forma_pagamento', 'N/A'),
                'status': v.get('status', 'N/A')
            })

        return resultado