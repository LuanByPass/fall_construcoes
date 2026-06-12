"""Controller de Vendas - FALL Construções
CORRIGIDO FINAL: usuario_id (coluna real), status ENUM('pendente','pago','cancelado')
"""
from models.venda_model import VendaModel, VendaItemModel
from models.cliente_model import ClienteModel
from models.produto_model import ProdutoModel
from models.movimentacao_model import MovimentacaoModel
from datetime import datetime

try:
    from utils.logger import Logger
except:
    class Logger:
        @classmethod
        def log(cls, msg, level='INFO'):
            print(f"[{level}] {msg}")


class VendaController:
    def __init__(self):
        self.venda_model = VendaModel()
        self.venda_model.create_table()
        self.venda_item_model = VendaItemModel()
        self.venda_item_model.create_table()
        self.cliente_model = ClienteModel()
        self.cliente_model.create_table()
        self.produto_model = ProdutoModel()
        self.produto_model.create_table()
        self.movimentacao_model = MovimentacaoModel()
        self.movimentacao_model.create_table()

    # ========== CLIENTES ==========
    def criar_cliente(self, dados):
        """Cria novo cliente (usado pelo PDV e relatório)"""
        try:
            cliente_id = self.cliente_model.create(**dados)
            return True, "✅ Cliente criado com sucesso!"
        except Exception as e:
            return False, f"❌ Erro: {e}"

    def listar_clientes(self, busca=''):
        """Lista clientes para seleção no PDV"""
        return self.cliente_model.read_all(busca)

    def obter_cliente(self, cliente_id):
        """Obtém cliente por ID"""
        return self.cliente_model.read_by_id(cliente_id)

    # ========== VENDAS - FLUXO 3 PASSOS ==========
    def criar_venda(self, cliente_id=None, forma_pagamento='dinheiro'):
        """PASSO 1: Cria venda vazia (sem itens ainda)"""
        try:
            venda_id = self.venda_model.create(
                cliente_id=cliente_id,
                usuario_id=1,  # ✅ CORRIGIDO: usuario_id (coluna real)
                subtotal=0,
                desconto=0,
                total=0,
                forma_pagamento=forma_pagamento,
                status='pendente'
            )

            # Busca a venda criada para retornar dados
            venda = self.venda_model.read_by_id(venda_id)

            Logger.log(f"Venda {venda_id} criada (pendente)", 'INFO')
            return True, {
                'id': venda_id,
                'numero': venda.get('numero_venda', venda_id)
            }

        except Exception as e:
            Logger.log(f"Erro ao criar venda: {e}", 'ERROR')
            return False, f"❌ Erro ao criar venda: {e}"

    def adicionar_item(self, venda_id, produto_id, quantidade):
        """PASSO 2: Adiciona item à venda"""
        try:
            # Busca produto
            produto = self.produto_model.read_by_id(produto_id)
            if not produto:
                return False, "Produto não encontrado"

            # Verifica estoque
            estoque_atual = produto.get('quantidade', 0)
            if estoque_atual < quantidade:
                return False, f"Estoque insuficiente. Disponível: {estoque_atual}"

            preco = float(produto.get('preco_venda', 0))
            subtotal_item = preco * quantidade

            # Cria item da venda (com subtotal)
            self.venda_item_model.create(
                venda_id=venda_id,
                produto_id=produto_id,
                quantidade=quantidade,
                preco_unitario=preco,
                subtotal=subtotal_item
            )

            # Atualiza estoque
            self.produto_model.update_quantidade(produto_id, -quantidade)

            # Movimentação
            quantidade_nova = estoque_atual - quantidade
            self.movimentacao_model.create(
                produto_id=produto_id,
                tipo=MovimentacaoModel.TIPO_VENDA,
                quantidade=-quantidade,
                quantidade_anterior=estoque_atual,
                quantidade_nova=quantidade_nova,
                motivo=f'Venda {venda_id}',
                venda_id=venda_id,
                usuario='Sistema'
            )

            Logger.log(f"Item {produto_id} x{quantidade} adicionado à venda {venda_id}", 'INFO')
            return True, "Item adicionado"

        except Exception as e:
            Logger.log(f"Erro ao adicionar item: {e}", 'ERROR')
            return False, f"❌ Erro ao adicionar item: {e}"

    def finalizar_venda(self, venda_id, desconto=0):
        """PASSO 3: Finaliza venda com desconto

        ✅ CORRIGIDO: Usa 'pago' (válido no ENUM)
        """
        try:
            # Busca todos os itens da venda
            itens = self.venda_item_model.read_by_venda(venda_id)

            # Calcula totais
            subtotal = sum(float(item.get('subtotal', 0)) for item in itens)
            total = subtotal - float(desconto)

            # ✅ Venda criada como 'pendente' — aguarda confirmação de pagamento
            self.venda_model.update(venda_id, 
                subtotal=subtotal,
                desconto=desconto,
                total=total,
                status='pendente'
            )

            Logger.log(f"Venda {venda_id} finalizada - Total: R$ {total:.2f}", 'SUCCESS')
            return True, {'total': total}

        except Exception as e:
            Logger.log(f"Erro ao finalizar: {e}", 'ERROR')
            return False, f"❌ Erro ao finalizar: {e}"

    # ========== CONSULTAS ==========
    def listar_vendas(self, data_inicio=None, data_fim=None, status=None):
        """Lista vendas com filtros"""
        return self.venda_model.read_all(status=status, data_inicio=data_inicio, data_fim=data_fim)

    def obter_venda(self, venda_id):
        """Obtém venda com itens e dados do cliente"""
        venda = self.venda_model.read_by_id(venda_id)
        if not venda:
            return None

        # Busca itens
        venda['itens'] = self.venda_item_model.read_by_venda(venda_id)

        # Busca cliente
        if venda.get('cliente_id'):
            cliente = self.cliente_model.read_by_id(venda['cliente_id'])
            if cliente:
                venda['cliente_nome'] = cliente.get('nome')
                venda['cpf_cnpj'] = cliente.get('cpf_cnpj')

        return venda

    def listar_finalizadas_sem_entrega(self):
        """Lista vendas finalizadas sem entrega (para tela de entregas)"""
        try:
            vendas = self.venda_model.read_all(status='pago')
            return vendas
        except:
            return []

    def reimprimir(self, venda_id):
        """Reimprime cupom da venda"""
        return self.obter_venda(venda_id)

    def mudar_status(self, venda_id, novo_status):
        """
        Altera o status de uma venda com validação de transição.
        Reutiliza cancelar() quando o novo status é 'cancelado'.

        Args:
            venda_id: ID da venda
            novo_status: 'pendente', 'pago' ou 'cancelado'

        Returns:
            (bool, str) -> (sucesso, mensagem)
        """
        try:
            venda = self.venda_model.read_by_id(venda_id)
            if not venda:
                return False, "Venda não encontrada"

            status_atual = venda.get('status', 'pendente')

            # Valida transições permitidas
            transicoes = {
                'pendente': ['pago', 'cancelado'],
                'pago': ['cancelado'],
                'cancelado': []  # Não pode sair de cancelado
            }

            if novo_status not in transicoes.get(status_atual, []):
                return False, f"Não é possível alterar de '{status_atual}' para '{novo_status}'"

            # Se for cancelar, reutiliza o método cancelar existente
            if novo_status == 'cancelado':
                return self.cancelar(venda_id)

            # Para outras transições (pendente -> pago), atualiza direto
            self.venda_model.update(venda_id, status=novo_status)
            Logger.log(f"Venda {venda_id}: {status_atual} -> {novo_status}", 'INFO')
            return True, f"Venda alterada para '{novo_status}' com sucesso"

        except Exception as e:
            Logger.log(f"Erro ao mudar status da venda {venda_id}: {e}", 'ERROR')
            return False, f"Erro ao alterar status: {str(e)}"

    def cancelar(self, venda_id):
        """Cancela uma venda e devolve estoque"""
        try:
            venda = self.venda_model.read_by_id(venda_id)
            if not venda:
                return False, "Venda não encontrada"

            # Devolve estoque
            itens = self.venda_item_model.read_by_venda(venda_id)
            for item in itens:
                produto = self.produto_model.read_by_id(item['produto_id'])
                estoque_atual = produto.get('quantidade', 0) if produto else 0
                quantidade_devolvida = item['quantidade']
                quantidade_nova = estoque_atual + quantidade_devolvida

                self.produto_model.update_quantidade(item['produto_id'], quantidade_devolvida)

                self.movimentacao_model.create(
                    produto_id=item['produto_id'],
                    tipo=MovimentacaoModel.TIPO_ENTRADA,
                    quantidade=quantidade_devolvida,
                    quantidade_anterior=estoque_atual,
                    quantidade_nova=quantidade_nova,
                    motivo=f'Cancelamento venda {venda_id}',
                    venda_id=venda_id,
                    usuario='Sistema'
                )

            # ✅ CORREÇÃO: 'cancelado' é válido no ENUM
            self.venda_model.update(venda_id, status='cancelado')
            Logger.log(f"Venda {venda_id} cancelada", 'WARNING')
            return True, "✅ Venda cancelada"
        except Exception as e:
            return False, f"❌ Erro: {e}"