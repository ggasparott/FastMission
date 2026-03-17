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

from ..models import ItemCadastral, StatusValidacao
from ..repositories.item_repository import ItemRepository
from ..repositories.lote_repository import LoteRepository


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
    
    # =================================================================
    # CRUD MANUAL - Cadastro de Item no Varejo
    # TODO: Implemente os métodos abaixo
    # =================================================================
    
    def criar_item(self, dados: dict) -> ItemCadastral:
        """
        Cria um novo item cadastral manualmente.
        
        Lógica:
        1. Verificar duplicidade de SKU (se informado):
           - sku = dados.get("sku")
           - if sku and self.item_repo.buscar_por_sku(sku):
           -     raise ItemValidationError(f"SKU '{sku}' já cadastrado")
            
        2. Verificar duplicidade de EAN (se informado):
           - ean = dados.get("ean_gtin")
           - if ean and self.item_repo.buscar_por_ean(ean):
           -     raise ItemValidationError(f"EAN '{ean}' já cadastrado")
        
        3. Mapear campos do schema para o model:
           - item_dados = {
           -     "descricao": dados["descricao"],
           -     "ncm_original": dados["ncm"],        ← note: schema usa "ncm", model usa "ncm_original"
           -     "cest_original": dados.get("cest"),   ← schema usa "cest", model usa "cest_original"
           -     "sku": dados.get("sku"),
           -     "ean_gtin": dados.get("ean_gtin"),
           -     "descricao_longa": dados.get("descricao_longa"),
           -     "cfop": dados.get("cfop"),
           -     "origem_produto": dados.get("origem_produto"),
           -     "cst_csosn": dados.get("cst_csosn"),
           -     "aliquota_icms": dados.get("aliquota_icms"),
           -     "aliquota_pis": dados.get("aliquota_pis"),
           -     "aliquota_cofins": dados.get("aliquota_cofins"),
           -     "possui_st": dados.get("possui_st"),
           -     "status_validacao": StatusValidacao.PENDENTE,
           - }
        
        4. return self.item_repo.criar_item_manual(item_dados)
        """
        sku = dados.get("sku")
        if sku and  self.item_repo.buscar_por_sku(sku):
            raise ItemValidationError(f"SKU '{sku}' já cadastrado")
        
        ean = dados.get("ean_gtin")
        if ean and self.item_repo.buscar_por_ean(ean):
            raise ItemValidationError(f"EAN '{ean}' já cadastrado")

        item_dados = {
            "descricao": dados["descricao"],
            "ncm_original": dados["ncm"],        
            "cest_original": dados.get("cest"),   
            "sku": dados.get("sku"),
            "ean_gtin": dados.get("ean_gtin"),
            "descricao_longa": dados.get("descricao_longa"),
            "cfop": dados.get("cfop"),
            "origem_produto": dados.get("origem_produto"),
            "cst_csosn": dados.get("cst_csosn"),
            "aliquota_icms": dados.get("aliquota_icms"),
            "aliquota_pis": dados.get("aliquota_pis"),
            "aliquota_cofins": dados.get("aliquota_cofins"),
            "possui_st": dados.get("possui_st"),
            "quantidade": dados.get("quantidade"),
            "valor_unitario": dados.get("valor_unitario"),
            "status_validacao": StatusValidacao.PENDENTE,
        }
        return self.item_repo.criar_item_manual(item_dados)

    def atualizar_item(self, item_id: str, dados: dict) -> ItemCadastral:
        """
        Atualiza um item existente.
        
        Lógica:
        1. Verificar se o item existe:
           - item = self.item_repo.buscar_por_id(item_id)
           - if not item: raise ItemNotFoundException(...)
        
        2. Se SKU está sendo alterado, verificar duplicidade:
           - novo_sku = dados.get("sku")
           - if novo_sku and novo_sku != item.sku:
           -     existente = self.item_repo.buscar_por_sku(novo_sku)
           -     if existente: raise ItemValidationError(...)
        
        3. Se EAN está sendo alterado, verificar duplicidade:
           - (mesmo padrão do SKU)
        
        4. Mapear campos (atenção: "ncm" → "ncm_original", "cest" → "cest_original")
           - updates = {}
           - if "descricao" in dados and dados["descricao"] is not None:
           -     updates["descricao"] = dados["descricao"]
           - if "ncm" in dados and dados["ncm"] is not None:
           -     updates["ncm_original"] = dados["ncm"]
           - ... (repetir para todos os campos) ...
        
        5. return self.item_repo.atualizar_item(item_id, updates)
        """
        item = self.item_repo.buscar_por_id(item_id)
        if not item: raise ItemNotFoundException("O item não foi encontrado")

        novo_sku = dados.get("sku")
        if novo_sku and novo_sku != item.sku:
            if self.item_repo.buscar_por_sku(novo_sku):
                raise ItemValidationError(f"SKU '{novo_sku}' já cadastrado")
            

        novo_ean = dados.get("ean_gtin")
        if novo_ean and novo_ean != item.ean_gtin:
            if self.item_repo.buscar_por_ean(novo_ean):
                raise ItemValidationError(f"EAN '{novo_ean}' já cadastrado")

        updates = {}
        if "descricao" in dados and dados["descricao"] is not None:
            updates["descricao"] = dados["descricao"]
        if "ncm" in dados and dados["ncm"] is not None:
            updates["ncm_original"] = dados["ncm"]
        if "cest" in dados and dados["cest"] is not None:
            updates["cest_original"] = dados["cest"]
        if "sku" in dados and dados["sku"] is not None:
            updates["sku"] = dados["sku"]
        if "ean_gtin" in dados and dados["ean_gtin"] is not None:
            updates["ean_gtin"] = dados["ean_gtin"]
        if "descricao_longa" in dados and dados["descricao_longa"] is not None:
            updates["descricao_longa"] = dados["descricao_longa"]
        if "cfop" in dados and dados["cfop"] is not None:
            updates["cfop"] = dados["cfop"]
        if "origem_produto" in dados and dados["origem_produto"] is not None:
            updates["origem_produto"] = dados["origem_produto"]
        if "cst_csosn" in dados and dados["cst_csosn"] is not None:
            updates["cst_csosn"] = dados["cst_csosn"]
        if "aliquota_icms" in dados and dados["aliquota_icms"] is not None:
            updates["aliquota_icms"] = dados["aliquota_icms"]
        if "aliquota_pis" in dados and dados["aliquota_pis"] is not None:
            updates["aliquota_pis"] = dados["aliquota_pis"]
        if "aliquota_cofins" in dados and dados["aliquota_cofins"] is not None:
            updates["aliquota_cofins"] = dados["aliquota_cofins"]
        if "possui_st" in dados and dados["possui_st"] is not None:
            updates["possui_st"] = dados["possui_st"]
        if "quantidade" in dados and dados["quantidade"] is not None:
            updates["quantidade"] = dados["quantidade"]
        if "valor_unitario" in dados and dados["valor_unitario"] is not None:
            updates["valor_unitario"] = dados["valor_unitario"]

        return self.item_repo.atualizar_item(item_id, updates)
    
    def deletar_item(self, item_id: str) -> bool:
        """
        Deleta um item.
        
        Lógica:
        1. Verificar se existe:
           - if not self.item_repo.existe(item_id):
           -     raise ItemNotFoundException(...)
        2. return self.item_repo.deletar_item(item_id)
        """
        if not self.item_repo.existe(item_id):
            raise ItemNotFoundException("O item não foi encontrado")
        return self.item_repo.deletar_item(item_id)
    
    def listar_itens(
        self, 
        skip: int = 0, 
        limit: int = 50,
        sku: Optional[str] = None,
        ncm: Optional[str] = None,
        cfop: Optional[str] = None,
        possui_st: Optional[str] = None
    ) -> List[ItemCadastral]:
        """
        Lista itens com filtros opcionais.
        
        Lógica:
        1. Simplesmente delegar para o repository:
           return self.item_repo.listar_com_filtros(
               skip=skip, limit=limit,
               sku=sku, ncm=ncm, cfop=cfop, possui_st=possui_st
           )
        """
        return self.item_repo.listar_com_filtros(
            skip=skip, limit=limit,
            sku=sku, ncm=ncm, cfop=cfop, possui_st=possui_st
        )
