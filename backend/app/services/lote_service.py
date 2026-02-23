"""
Service Layer - Lote

Responsabilidades:
- Validação de regras de negócio
- Orquestração entre LoteRepository e ItemRepository
- Cálculo de estatísticas e progresso
- Tratamento de exceções de negócio
"""

from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime
from sqlalchemy.orm import Session

from app.models import Lote, ItemCadastral, StatusLote, StatusValidacao
from app.repositories.lote_repository import LoteRepository
from app.repositories.item_repository import ItemRepository


class LoteNotFoundException(Exception):
    """Exceção lançada quando um lote não é encontrado"""
    pass


class LoteValidationError(Exception):
    """Exceção lançada quando há erro de validação de negócio"""
    pass


class LoteService:
    """
    Service para operações de negócio relacionadas a Lotes.
    
    Orquestra operações entre LoteRepository e ItemRepository,
    aplicando regras de negócio e validações.
    """
    
    def __init__(self, db: Session):
        """
        Inicializa o service com as dependências necessárias.
        
        Args:
            db: Sessão do SQLAlchemy
        """
        self.db = db
        self.lote_repo = LoteRepository(db)
        self.item_repo = ItemRepository(db)
    
    
    def criar_lote_com_itens(
        self, 
        arquivo_nome: str, 
        itens_data: List[Dict[str, Any]]
    ) -> Lote:
        """
        Cria um novo lote e seus itens associados em uma transação.
        
        Args:
            arquivo_nome: Nome do arquivo CSV enviado
            itens_data: Lista de dicionários com dados dos itens
        
        Returns:
            Lote criado com itens
        
        Raises:
            LoteValidationError: Se houver erro de validação
        
        Exemplo:
            lote = service.criar_lote_com_itens(
                arquivo_nome="produtos_2024.csv",
                itens_data=[
                    {
                        "descricao": "ARROZ INTEGRAL 1KG",
                        "ncm_original": "10063021",
                        "cest_original": "1700400"
                    },
                    # ... mais itens
                ]
            )
        """
        # Validação de negócio
        if not arquivo_nome:
            raise LoteValidationError("Nome do arquivo é obrigatório")
        
        if not itens_data or len(itens_data) == 0:
            raise LoteValidationError("Lote deve conter pelo menos 1 item")
        
        # Criar lote
        lote = Lote(
            arquivo_nome=arquivo_nome,
            status=StatusLote.PENDENTE,
            total_itens=len(itens_data)
        )
        
        lote_criado = self.lote_repo.criar(lote)
        
        # Criar itens associados
        itens = []
        for item_data in itens_data:
            item = ItemCadastral(
                lote_id=lote_criado.id,
                descricao=item_data.get("descricao", ""),
                ncm_original=item_data.get("ncm_original", ""),
                cest_original=item_data.get("cest_original"),
                status_validacao=StatusValidacao.PENDENTE
            )
            itens.append(item)
        
        # Bulk insert dos itens
        self.item_repo.criar_lote_itens(itens)
        
        # Retornar lote criado
        return self.buscar_lote_completo(str(lote_criado.id))
    
    
    def buscar_lote_completo(self, lote_id: str) -> Lote:
        """
        Busca um lote com todos os seus itens (eager loading).
        
        Args:
            lote_id: UUID do lote
        
        Returns:
            Lote com itens carregados
        
        Raises:
            LoteNotFoundException: Se o lote não existir
        
        Exemplo:
            lote = service.buscar_lote_completo("uuid-123")
            print(f"Lote: {lote.arquivo_nome}")
            print(f"Total de itens: {len(lote.itens)}")
        """
        lote = self.lote_repo.buscar_com_itens(lote_id)
        
        if not lote:
            raise LoteNotFoundException(f"Lote {lote_id} não encontrado")
        
        return lote
    
    
    def buscar_lote_por_id(self, lote_id: str) -> Lote:
        """
        Busca um lote por ID (sem carregar itens).
        
        Args:
            lote_id: UUID do lote
        
        Returns:
            Lote encontrado
        
        Raises:
            LoteNotFoundException: Se o lote não existir
        """
        lote = self.lote_repo.buscar_por_id(lote_id)
        
        if not lote:
            raise LoteNotFoundException(f"Lote {lote_id} não encontrado")
        
        return lote
    
    
    def calcular_progresso(self, lote_id: str) -> Dict[str, Any]:
        """
        Calcula o progresso de processamento de um lote.
        
        Args:
            lote_id: UUID do lote
        
        Returns:
            Dicionário com estatísticas de progresso:
                - status: status atual do lote
                - progresso: percentual processado (0-100)
                - total_itens: total de itens no lote
                - itens_processados: total processado (válidos + divergentes)
                - itens_validos: total com status VALIDO
                - itens_divergentes: total com status DIVERGENTE
                - itens_pendentes: total com status PENDENTE
        
        Raises:
            LoteNotFoundException: Se o lote não existir
        
        Exemplo:
            progresso = service.calcular_progresso("uuid-123")
            print(f"Progresso: {progresso['progresso']}%")
            print(f"Válidos: {progresso['itens_validos']}")
            print(f"Divergências: {progresso['itens_divergentes']}")
        """
        # Validar existência do lote
        lote = self.buscar_lote_por_id(lote_id)
        
        # Buscar estatísticas dos itens
        stats = self.item_repo.obter_estatisticas_lote(lote_id)
        
        # Calcular progresso
        total = stats['total']
        validos = stats.get('aprovados', 0)  # Usando 'aprovados' como 'validos'
        divergentes = stats.get('erros', 0)  # Usando 'erros' como 'divergentes'
        pendentes = stats.get('pendentes', 0)
        
        processados = validos + divergentes
        progresso_percentual = stats.get('progresso', 0.0)
        
        return {
            "status": lote.status,
            "progresso": progresso_percentual,
            "total_itens": total,
            "itens_processados": processados,
            "itens_validos": validos,
            "itens_divergentes": divergentes,
            "itens_pendentes": pendentes
        }
    
    
    def obter_estatisticas(self, lote_id: str) -> Dict[str, Any]:
        """
        Obtém estatísticas detalhadas de um lote.
        
        Similar a calcular_progresso, mas com informações adicionais
        como tempo médio de processamento, tipos de erro mais comuns, etc.
        
        Args:
            lote_id: UUID do lote
        
        Returns:
            Dicionário com estatísticas completas
        
        Raises:
            LoteNotFoundException: Se o lote não existir
        """
        lote = self.buscar_lote_por_id(lote_id)
        progresso = self.calcular_progresso(lote_id)
        
        # Estatísticas adicionais podem ser adicionadas aqui
        # como tempo médio, taxa de sucesso, etc.
        
        return {
            **progresso,
            "arquivo_nome": lote.arquivo_nome,
            "data_upload": lote.data_upload,
            "taxa_sucesso": (progresso['itens_validos'] / progresso['total_itens'] * 100) 
                if progresso['total_itens'] > 0 else 0.0
        }
    
    
    def listar_lotes_recentes(self, limit: int = 10) -> List[Lote]:
        """
        Lista os lotes mais recentes.
        
        Args:
            limit: Quantidade máxima de lotes a retornar
        
        Returns:
            Lista de lotes ordenados por data de upload (desc)
        
        Exemplo:
            recentes = service.listar_lotes_recentes(limit=5)
            for lote in recentes:
                print(f"{lote.arquivo_nome} - {lote.status}")
        """
        return self.lote_repo.buscar_recentes(limit=limit)
    
    
    def listar_por_status(self, status: str) -> List[Lote]:
        """
        Lista lotes por status.
        
        Args:
            status: Status a filtrar (PENDENTE, PROCESSANDO, CONCLUIDO, ERRO)
        
        Returns:
            Lista de lotes com o status especificado
        
        Exemplo:
            pendentes = service.listar_por_status(StatusLote.PENDENTE)
            print(f"Há {len(pendentes)} lotes pendentes")
        """
        # Validar status
        try:
            StatusLote(status)
        except ValueError:
            raise LoteValidationError(f"Status inválido: {status}")
        
        return self.lote_repo.buscar_por_status(status)
    
    
    def atualizar_status_lote(self, lote_id: str, novo_status: str) -> Lote:
        """
        Atualiza o status de um lote.
        
        Args:
            lote_id: UUID do lote
            novo_status: Novo status (PENDENTE, PROCESSANDO, CONCLUIDO, ERRO)
        
        Returns:
            Lote atualizado
        
        Raises:
            LoteNotFoundException: Se o lote não existir
            LoteValidationError: Se o status for inválido
        
        Exemplo:
            # Marcar lote como processando
            lote = service.atualizar_status_lote(
                "uuid-123", 
                StatusLote.PROCESSANDO
            )
        """
        # Validar status
        try:
            StatusLote(novo_status)
        except ValueError:
            raise LoteValidationError(f"Status inválido: {novo_status}")
        
        # Validar existência do lote
        if not self.lote_repo.existe(lote_id):
            raise LoteNotFoundException(f"Lote {lote_id} não encontrado")
        
        # Atualizar
        lote_atualizado = self.lote_repo.atualizar(lote_id, {"status": novo_status})
        
        if not lote_atualizado:
            raise LoteNotFoundException(f"Erro ao atualizar lote {lote_id}")
        
        return lote_atualizado
    
    
    def deletar_lote(self, lote_id: str) -> bool:
        """
        Deleta um lote e todos os seus itens (cascade).
        
        Args:
            lote_id: UUID do lote
        
        Returns:
            True se deletado com sucesso
        
        Raises:
            LoteNotFoundException: Se o lote não existir
        
        Exemplo:
            sucesso = service.deletar_lote("uuid-123")
            if sucesso:
                print("Lote deletado com sucesso")
        """
        # Validar existência
        if not self.lote_repo.existe(lote_id):
            raise LoteNotFoundException(f"Lote {lote_id} não encontrado")
        
        # Deletar (cascade vai remover os itens automaticamente)
        return self.lote_repo.deletar(lote_id)
    
    
    def validar_lote_existe(self, lote_id: str) -> bool:
        """
        Verifica se um lote existe.
        
        Args:
            lote_id: UUID do lote
        
        Returns:
            True se o lote existir, False caso contrário
        
        Exemplo:
            if service.validar_lote_existe("uuid-123"):
                print("Lote existe")
            else:
                print("Lote não encontrado")
        """
        return self.lote_repo.existe(lote_id)
