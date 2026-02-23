"""
Service Layer - ItemCadastral

Responsabilidades:
- Validação de regras de negócio para itens cadastrais
- Atualização de resultados de validação
- Busca e filtragem de itens
- Lógica de validação específica da Reforma Tributária
"""

from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime
from sqlalchemy.orm import Session

from app.models import ItemCadastral, StatusValidacao
from app.repositories.item_repository import ItemRepository
from app.repositories.lote_repository import LoteRepository


class ItemNotFoundException(Exception):
    """Exceção lançada quando um item não é encontrado"""
    pass


class ItemValidationError(Exception):
    """Exceção lançada quando há erro de validação de negócio"""
    pass


class ItemService:
    """
    Service para operações de negócio relacionadas a ItemCadastral.
    
    Gerencia validações, atualizações e consultas de itens cadastrais,
    aplicando regras específicas da Reforma Tributária.
    """
    
    def __init__(self, db: Session):
        """
        Inicializa o service com as dependências necessárias.
        
        Args:
            db: Sessão do SQLAlchemy
        """
        self.db = db
        self.item_repo = ItemRepository(db)
        self.lote_repo = LoteRepository(db)
    
    
    def buscar_item_por_id(self, item_id: str) -> ItemCadastral:
        """
        Busca um item por ID.
        
        Args:
            item_id: UUID do item
        
        Returns:
            Item encontrado
        
        Raises:
            ItemNotFoundException: Se o item não existir
        
        Exemplo:
            item = service.buscar_item_por_id("uuid-123")
            print(f"Descrição: {item.descricao}")
        """
        item = self.item_repo.buscar_por_id(item_id)
        
        if not item:
            raise ItemNotFoundException(f"Item {item_id} não encontrado")
        
        return item
    
    
    def buscar_itens_lote(
        self, 
        lote_id: str, 
        skip: int = 0, 
        limit: int = 100
    ) -> List[ItemCadastral]:
        """
        Busca itens de um lote com paginação.
        
        Args:
            lote_id: UUID do lote
            skip: Quantidade de registros a pular
            limit: Quantidade máxima de registros
        
        Returns:
            Lista de itens do lote
        
        Exemplo:
            # Primeira página (50 itens)
            itens = service.buscar_itens_lote("uuid-lote", skip=0, limit=50)
            
            # Segunda página
            itens = service.buscar_itens_lote("uuid-lote", skip=50, limit=50)
        """
        # Validar que o lote existe
        if not self.lote_repo.existe(lote_id):
            raise ItemValidationError(f"Lote {lote_id} não encontrado")
        
        return self.item_repo.buscar_por_lote(lote_id, skip=skip, limit=limit)
    
    
    def atualizar_validacao_ncm(
        self,
        item_id: str,
        ncm_sugerido: Optional[str] = None,
        status_validacao: str = StatusValidacao.VALIDO,
        motivo_divergencia: Optional[str] = None,
        confianca_ai: Optional[float] = None
    ) -> ItemCadastral:
        """
        Atualiza o resultado da validação de NCM de um item.
        
        Args:
            item_id: UUID do item
            ncm_sugerido: NCM sugerido pela IA (se diferente do original)
            status_validacao: VALIDO, DIVERGENTE ou PENDENTE
            motivo_divergencia: Motivo da divergência (se houver)
            confianca_ai: Score de confiança da IA (0-100)
        
        Returns:
            Item atualizado
        
        Raises:
            ItemNotFoundException: Se o item não existir
            ItemValidationError: Se houver erro de validação
        
        Exemplo:
            # NCM validado com sucesso
            item = service.atualizar_validacao_ncm(
                item_id="uuid-123",
                status_validacao=StatusValidacao.VALIDO,
                confianca_ai=98.5
            )
            
            # NCM com divergência
            item = service.atualizar_validacao_ncm(
                item_id="uuid-456",
                ncm_sugerido="10063021",
                status_validacao=StatusValidacao.DIVERGENTE,
                motivo_divergencia="NCM original 10063022 não existe. Sugestão: 10063021 (Arroz)",
                confianca_ai=95.2
            )
        """
        # Validar existência do item
        if not self.item_repo.existe(item_id):
            raise ItemNotFoundException(f"Item {item_id} não encontrado")
        
        # Validar status
        try:
            StatusValidacao(status_validacao)
        except ValueError:
            raise ItemValidationError(f"Status de validação inválido: {status_validacao}")
        
        # Validar confiança (0-100)
        if confianca_ai is not None and (confianca_ai < 0 or confianca_ai > 100):
            raise ItemValidationError("Confiança da IA deve estar entre 0 e 100")
        
        # Preparar dados de atualização
        updates = {
            "status_validacao": status_validacao,
            "data_processamento": datetime.utcnow()
        }
        
        if ncm_sugerido:
            updates["ncm_sugerido"] = ncm_sugerido
        
        if motivo_divergencia:
            updates["motivo_divergencia"] = motivo_divergencia
        
        if confianca_ai is not None:
            updates["confianca_ai"] = confianca_ai
        
        # Atualizar item
        item_atualizado = self.item_repo.atualizar(item_id, updates)
        
        if not item_atualizado:
            raise ItemNotFoundException(f"Erro ao atualizar item {item_id}")
        
        return item_atualizado
    
    
    def atualizar_validacao_cest(
        self,
        item_id: str,
        cest_sugerido: Optional[str] = None,
        cest_obrigatorio: Optional[str] = None
    ) -> ItemCadastral:
        """
        Atualiza o resultado da validação de CEST de um item.
        
        Args:
            item_id: UUID do item
            cest_sugerido: CEST sugerido pela IA
            cest_obrigatorio: "SIM", "NAO" ou "VERIFICAR"
        
        Returns:
            Item atualizado
        
        Raises:
            ItemNotFoundException: Se o item não existir
        
        Exemplo:
            item = service.atualizar_validacao_cest(
                item_id="uuid-123",
                cest_sugerido="1700400",
                cest_obrigatorio="SIM"
            )
        """
        # Validar existência
        if not self.item_repo.existe(item_id):
            raise ItemNotFoundException(f"Item {item_id} não encontrado")
        
        # Preparar updates
        updates = {}
        
        if cest_sugerido:
            updates["cest_sugerido"] = cest_sugerido
        
        if cest_obrigatorio:
            if cest_obrigatorio not in ["SIM", "NAO", "VERIFICAR"]:
                raise ItemValidationError(
                    "CEST obrigatório deve ser 'SIM', 'NAO' ou 'VERIFICAR'"
                )
            updates["cest_obrigatorio"] = cest_obrigatorio
        
        # Atualizar
        item_atualizado = self.item_repo.atualizar(item_id, updates)
        
        if not item_atualizado:
            raise ItemNotFoundException(f"Erro ao atualizar item {item_id}")
        
        return item_atualizado
    
    
    def atualizar_reforma_tributaria(
        self,
        item_id: str,
        regime_tributario: Optional[str] = None,
        aliquota_ibs: Optional[float] = None,
        aliquota_cbs: Optional[float] = None,
        possui_beneficio_fiscal: Optional[str] = None,
        tipo_beneficio: Optional[str] = None,
        artigo_legal: Optional[str] = None
    ) -> ItemCadastral:
        """
        Atualiza informações da Reforma Tributária (IBS/CBS).
        
        Args:
            item_id: UUID do item
            regime_tributario: NORMAL, ALIQUOTA_REDUZIDA, CASHBACK, IMUNE
            aliquota_ibs: Alíquota do IBS (%)
            aliquota_cbs: Alíquota do CBS (%)
            possui_beneficio_fiscal: "SIM", "NAO" ou "POSSIVEL"
            tipo_beneficio: Descrição do benefício (ex: "Cesta básica")
            artigo_legal: Artigo da lei (ex: "Art. 18, §1º")
        
        Returns:
            Item atualizado
        
        Raises:
            ItemNotFoundException: Se o item não existir
            ItemValidationError: Se houver erro de validação
        
        Exemplo:
            # Produto da cesta básica com alíquota reduzida
            item = service.atualizar_reforma_tributaria(
                item_id="uuid-123",
                regime_tributario="ALIQUOTA_REDUZIDA",
                aliquota_ibs=0.0,
                aliquota_cbs=0.0,
                possui_beneficio_fiscal="SIM",
                tipo_beneficio="Cesta básica nacional",
                artigo_legal="Art. 18, §1º da LC 214/2025"
            )
        """
        # Validar existência
        if not self.item_repo.existe(item_id):
            raise ItemNotFoundException(f"Item {item_id} não encontrado")
        
        # Validar regime tributário
        regimes_validos = ["NORMAL", "ALIQUOTA_REDUZIDA", "CASHBACK", "IMUNE"]
        if regime_tributario and regime_tributario not in regimes_validos:
            raise ItemValidationError(
                f"Regime tributário inválido. Opções: {', '.join(regimes_validos)}"
            )
        
        # Validar alíquotas (0-100)
        if aliquota_ibs is not None and (aliquota_ibs < 0 or aliquota_ibs > 100):
            raise ItemValidationError("Alíquota IBS deve estar entre 0 e 100")
        
        if aliquota_cbs is not None and (aliquota_cbs < 0 or aliquota_cbs > 100):
            raise ItemValidationError("Alíquota CBS deve estar entre 0 e 100")
        
        # Validar benefício fiscal
        if possui_beneficio_fiscal and possui_beneficio_fiscal not in ["SIM", "NAO", "POSSIVEL"]:
            raise ItemValidationError(
                "Benefício fiscal deve ser 'SIM', 'NAO' ou 'POSSIVEL'"
            )
        
        # Preparar updates
        updates = {}
        
        if regime_tributario:
            updates["regime_tributario"] = regime_tributario
        
        if aliquota_ibs is not None:
            updates["aliquota_ibs"] = aliquota_ibs
        
        if aliquota_cbs is not None:
            updates["aliquota_cbs"] = aliquota_cbs
        
        if possui_beneficio_fiscal:
            updates["possui_beneficio_fiscal"] = possui_beneficio_fiscal
        
        if tipo_beneficio:
            updates["tipo_beneficio"] = tipo_beneficio
        
        if artigo_legal:
            updates["artigo_legal"] = artigo_legal
        
        # Atualizar
        item_atualizado = self.item_repo.atualizar(item_id, updates)
        
        if not item_atualizado:
            raise ItemNotFoundException(f"Erro ao atualizar item {item_id}")
        
        return item_atualizado
    
    
    def buscar_itens_pendentes(self, lote_id: str, limit: int = 10) -> List[ItemCadastral]:
        """
        Busca itens pendentes de validação de um lote.
        
        Args:
            lote_id: UUID do lote
            limit: Quantidade máxima de itens
        
        Returns:
            Lista de itens com status PENDENTE
        
        Exemplo:
            # Para processar em lotes pequenos (Celery task)
            while True:
                pendentes = service.buscar_itens_pendentes("uuid-lote", limit=10)
                if not pendentes:
                    break
                
                for item in pendentes:
                    processar_item(item)
        """
        return self.item_repo.buscar_itens_pendentes(lote_id, limit=limit)
    
    
    def buscar_itens_com_divergencia(self, lote_id: str) -> List[ItemCadastral]:
        """
        Busca todos os itens com divergências de um lote.
        
        Args:
            lote_id: UUID do lote
        
        Returns:
            Lista de itens com status DIVERGENTE
        
        Exemplo:
            divergencias = service.buscar_itens_com_divergencia("uuid-lote")
            print(f"Encontradas {len(divergencias)} divergências")
            
            for item in divergencias:
                print(f"- {item.descricao}: {item.motivo_divergencia}")
        """
        return self.item_repo.buscar_itens_com_erro(lote_id)
    
    
    def buscar_itens_por_ncm(self, ncm: str) -> List[ItemCadastral]:
        """
        Busca todos os itens com um NCM específico.
        
        Args:
            ncm: Código NCM (8 dígitos)
        
        Returns:
            Lista de itens com o NCM
        
        Exemplo:
            # Buscar todos os produtos de arroz
            arrozes = service.buscar_itens_por_ncm("10063021")
            print(f"Total de produtos de arroz: {len(arrozes)}")
        """
        return self.item_repo.buscar_por_ncm(ncm)
    
    
    def obter_estatisticas_validacao(self, lote_id: str) -> Dict[str, Any]:
        """
        Obtém estatísticas de validação de um lote.
        
        Args:
            lote_id: UUID do lote
        
        Returns:
            Dicionário com estatísticas completas
        
        Exemplo:
            stats = service.obter_estatisticas_validacao("uuid-lote")
            print(f"Total: {stats['total']}")
            print(f"Aprovados: {stats['aprovados']}")
            print(f"Divergências: {stats['erros']}")
            print(f"Progresso: {stats['progresso']}%")
        """
        return self.item_repo.obter_estatisticas_lote(lote_id)
    
    
    def validar_item_completo(
        self,
        item_id: str,
        resultados_validacao: Dict[str, Any]
    ) -> ItemCadastral:
        """
        Atualiza todas as validações de um item de uma vez.
        
        Método helper para atualizar NCM, CEST e Reforma Tributária
        em uma única chamada.
        
        Args:
            item_id: UUID do item
            resultados_validacao: Dicionário com todos os resultados
        
        Returns:
            Item completamente atualizado
        
        Exemplo:
            item = service.validar_item_completo(
                item_id="uuid-123",
                resultados_validacao={
                    # NCM
                    "ncm_sugerido": "10063021",
                    "status_validacao": "VALIDO",
                    "confianca_ai": 98.5,
                    
                    # CEST
                    "cest_sugerido": "1700400",
                    "cest_obrigatorio": "SIM",
                    
                    # Reforma Tributária
                    "regime_tributario": "ALIQUOTA_REDUZIDA",
                    "aliquota_ibs": 0.0,
                    "aliquota_cbs": 0.0,
                    "possui_beneficio_fiscal": "SIM",
                    "tipo_beneficio": "Cesta básica nacional"
                }
            )
        """
        # Validar existência
        if not self.item_repo.existe(item_id):
            raise ItemNotFoundException(f"Item {item_id} não encontrado")
        
        # Adicionar timestamp
        resultados_validacao["data_processamento"] = datetime.utcnow()
        
        # Atualizar tudo de uma vez
        item_atualizado = self.item_repo.atualizar(item_id, resultados_validacao)
        
        if not item_atualizado:
            raise ItemNotFoundException(f"Erro ao atualizar item {item_id}")
        
        return item_atualizado
