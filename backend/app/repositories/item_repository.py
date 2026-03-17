"""
Repository para operações com ItemCadastral.

Fornece métodos para gerenciar itens cadastrais de lotes,
incluindo validação, contagem e atualização de resultados.
"""

from typing import List, Optional
from sqlalchemy.orm import Session
from .base import BaseRepository
from ..models import ItemCadastral


class ItemRepository(BaseRepository[ItemCadastral]):
    """
    Repository para operações com ItemCadastral.
    
    Herda operações CRUD básicas e adiciona métodos específicos
    para processamento e validação de itens.
    
    Métodos herdados:
        - buscar_por_id(id) -> Optional[ItemCadastral]
        - listar_todos(skip, limit) -> List[ItemCadastral]
        - criar(obj) -> ItemCadastral
        - atualizar(obj, updates) -> Optional[ItemCadastral]
        - deletar(id) -> bool
        - contar() -> int
        - existe(id) -> bool
    """
    
    def __init__(self, db: Session):
        """
        Inicializa o repository de ItemCadastral.
        
        Args:
            db: Sessão do SQLAlchemy para operações no banco
        """
        super().__init__(db, ItemCadastral)
    
    
    def buscar_por_lote(self, lote_id: str, skip: int = 0, limit: int = 100) -> List[ItemCadastral]:
        """
        Busca todos os itens de um lote específico com paginação.
        
        Args:
            lote_id: ID do lote
            skip: Quantos registros pular (paginação)
            limit: Máximo de registros a retornar
        
        Returns:
            Lista de itens do lote
        
        Exemplo:
            # Primeira página (50 itens)
            itens = repo.buscar_por_lote("uuid-lote", skip=0, limit=50)
            
            # Segunda página (próximos 50)
            itens = repo.buscar_por_lote("uuid-lote", skip=50, limit=50)
        """
        query = self.db.query(ItemCadastral).filter(ItemCadastral.lote_id == lote_id)
        
        if skip > 0:
            query = query.offset(skip)
        
        if limit is not None:
            query = query.limit(limit)
        
        return query.all()
    
    
    def buscar_por_ncm(self, ncm: str) -> List[ItemCadastral]:
        """
        Busca todos os itens com um NCM específico.
        
        Args:
            ncm: Código NCM (8 dígitos)
        
        Returns:
            Lista de itens com o NCM especificado
        
        Exemplo:
            # Buscar todos os itens de arroz
            arrozes = repo.buscar_por_ncm("10063021")
            print(f"Encontrados {len(arrozes)} itens de arroz")
        """
        return self.db.query(ItemCadastral).filter(ItemCadastral.ncm == ncm).all()
    
    
    def contar_por_lote(self, lote_id: str) -> int:
        """
        Conta total de itens em um lote.
        
        Args:
            lote_id: ID do lote
        
        Returns:
            Quantidade total de itens no lote
        
        Exemplo:
            total = repo.contar_por_lote("uuid-lote")
            print(f"Lote possui {total} itens")
        """
        return self.db.query(ItemCadastral).filter(ItemCadastral.lote_id == lote_id).count()
    
    
    def contar_por_status(self, lote_id: str, status: str) -> int:
        """
        Conta itens com um status específico dentro de um lote.
        
        Args:
            lote_id: ID do lote
            status: Status a ser contado (ex: "APROVADO", "ERRO", "PENDENTE")
        
        Returns:
            Quantidade de itens com o status
        
        Exemplo:
            total = repo.contar_por_lote("uuid-lote")
            aprovados = repo.contar_por_status("uuid-lote", "APROVADO")
            progresso = (aprovados / total) * 100
            print(f"Progresso: {progresso}%")
        """
        return (
            self.db.query(ItemCadastral)
            .filter(ItemCadastral.lote_id == lote_id)
            .filter(ItemCadastral.status == status)
            .count()
        )
    
    
    def atualizar_resultado(self, item_id: str, status: str, resultado: str) -> Optional[ItemCadastral]:
        """
        Atualiza o resultado da validação de um item.
        
        Args:
            item_id: ID do item
            status: Novo status ("APROVADO", "ERRO", "ALERTA")
            resultado: Mensagem do resultado da validação
        
        Returns:
            Item atualizado ou None se não encontrado
        
        Exemplo:
            # Item com NCM inválido
            item = repo.atualizar_resultado(
                item_id="uuid-123",
                status="ERRO",
                resultado="NCM 99999999 não existe no ComexStat"
            )
            
            # Item validado com sucesso
            item = repo.atualizar_resultado(
                item_id="uuid-456",
                status="APROVADO",
                resultado="Todos os campos validados com sucesso"
            )
        """
        return self.atualizar(item_id, {
            "status": status,
            "resultado_validacao": resultado
        })
    
    
    def buscar_itens_pendentes(self, lote_id: str, limit: int = 10) -> List[ItemCadastral]:
        """
        Busca itens que ainda não foram validados (status PENDENTE).
        
        Args:
            lote_id: ID do lote
            limit: Máximo de itens a retornar (padrão: 10)
        
        Returns:
            Lista de itens pendentes
        
        Uso em Celery Task:
            # Processar itens em lotes pequenos
            while True:
                itens = repo.buscar_itens_pendentes("uuid-lote", limit=10)
                if not itens:
                    break  # Não há mais itens pendentes
                
                for item in itens:
                    validar_item(item)
        """
        return (
            self.db.query(ItemCadastral)
            .filter(ItemCadastral.lote_id == lote_id)
            .filter(ItemCadastral.status == "PENDENTE")
            .limit(limit)
            .all()
        )
    
    
    def buscar_itens_com_erro(self, lote_id: str) -> List[ItemCadastral]:
        """
        Busca todos os itens com erro em um lote.
        
        Args:
            lote_id: ID do lote
        
        Returns:
            Lista de itens com status "ERRO"
        
        Exemplo:
            erros = repo.buscar_itens_com_erro("uuid-lote")
            for item in erros:
                print(f"Linha {item.linha_csv}: {item.resultado_validacao}")
        """
        return (
            self.db.query(ItemCadastral)
            .filter(ItemCadastral.lote_id == lote_id)
            .filter(ItemCadastral.status == "ERRO")
            .all()
        )
    
    
    def obter_estatisticas_lote(self, lote_id: str) -> dict:
        """
        Retorna estatísticas completas de validação de um lote.
        
        Args:
            lote_id: ID do lote
        
        Returns:
            Dicionário com estatísticas:
                - total: total de itens
                - aprovados: quantidade aprovada
                - erros: quantidade com erro
                - pendentes: quantidade pendente
                - progresso: percentual processado
        
        Exemplo:
            stats = repo.obter_estatisticas_lote("uuid-lote")
            print(f"Total: {stats['total']}")
            print(f"Aprovados: {stats['aprovados']}")
            print(f"Erros: {stats['erros']}")
            print(f"Progresso: {stats['progresso']}%")
        """
        total = self.contar_por_lote(lote_id)
        aprovados = self.contar_por_status(lote_id, "APROVADO")
        erros = self.contar_por_status(lote_id, "ERRO")
        pendentes = self.contar_por_status(lote_id, "PENDENTE")
        
        progresso = 0.0
        if total > 0:
            processados = aprovados + erros
            progresso = (processados / total) * 100
        
        return {
            "total": total,
            "aprovados": aprovados,
            "erros": erros,
            "pendentes": pendentes,
            "progresso": round(progresso, 2)
        }
    
    
    def criar_lote_itens(self, itens: List[ItemCadastral]) -> int:
    
        self.db.add_all(itens)
        self.db.commit()
        return len(itens)
    
    # =================================================================
    # MÉTODOS PARA CADASTRO MANUAL DE ITENS (MVP Varejo)
    # TODO: Implemente os métodos abaixo
    # =================================================================
    
    def buscar_por_sku(self, sku: str) -> Optional[ItemCadastral]:
        """
        Busca um item pelo SKU (código interno).
        Usado para verificar duplicidade antes de cadastrar.
        
        Lógica:
        1. self.db.query(ItemCadastral)
        2. .filter(ItemCadastral.sku == sku)
        3. .first()  → retorna 1 ou None
        """
        return self.db.query(ItemCadastral).filter(ItemCadastral.sku == sku).first()
    
    def buscar_por_ean(self, ean: str) -> Optional[ItemCadastral]:
        """
        Busca um item pelo EAN/GTIN (código de barras).
        
        Lógica: Mesmo padrão do buscar_por_sku, mas filtra por ean_gtin
        """
        return self.db.query(ItemCadastral).filter(ItemCadastral.ean_gtin == ean).first()   

    
    def listar_com_filtros(
        self, 
        skip: int = 0, 
        limit: int = 50,
        sku: Optional[str] = None,
        ncm: Optional[str] = None,
        cfop: Optional[str] = None,
        possui_st: Optional[str] = None
    ) -> List[ItemCadastral]:
        """
        Lista itens com filtros opcionais para busca avançada.
        
        Lógica:
        1. query = self.db.query(ItemCadastral)
        2. Para CADA filtro que não for None, adicionar .filter():
           - if sku:   query = query.filter(ItemCadastral.sku == sku)
           - if ncm:   query = query.filter(ItemCadastral.ncm_original == ncm)
           - if cfop:  query = query.filter(ItemCadastral.cfop == cfop)
           - if possui_st: query = query.filter(ItemCadastral.possui_st == possui_st)
        3. Aplicar .offset(skip).limit(limit)
        4. Retornar query.all()
        """
        query = self.db.query(ItemCadastral)
        if sku: 
            query = query.filter(ItemCadastral.sku == sku)   
            
        if ncm: 
            query = query.filter(ItemCadastral.ncm_original == ncm)    
            
        if cfop: 
            query = query.filter(ItemCadastral.cfop == cfop)
            
        if possui_st is not None: 
            query = query.filter(ItemCadastral.possui_st == possui_st)    
            
        return query.offset(skip).limit(limit).all()
    def criar_item_manual(self, dados: dict) -> ItemCadastral:
        """
        Cria um item cadastral manualmente (não via CSV).
        
        Lógica:
        1. item = ItemCadastral(**dados)  → cria o objeto com os dados do dict
        2. self.db.add(item)              → adiciona na sessão
        3. self.db.commit()               → persiste no banco
        4. self.db.refresh(item)          → recarrega com dados do banco (ex: id gerado)
        5. return item
        """
        item = ItemCadastral(**dados)
        self.db.add(item)
        self.db.commit()
        self.db.refresh(item)
        return item

    def atualizar_item(self, item_id: str, dados: dict) -> Optional[ItemCadastral]:
        """
        Atualiza campos de um item existente.
        
        Lógica:
        1. item = self.buscar_por_id(item_id)  → método herdado do BaseRepository
        2. Se item for None, return None
        3. Para cada (campo, valor) em dados.items():
           - if valor is not None:
           -     setattr(item, campo, valor)   → atualiza dinamicamente
        4. self.db.commit()
        5. self.db.refresh(item)
        6. return item
        """
        item = self.buscar_por_id(item_id)
        if item is None:
            return None

        for campo, valor in dados.items():
            if valor is not None and hasattr(item, campo):
                setattr(item, campo, valor)

        self.db.commit()
        self.db.refresh(item)
        return item
    
    def deletar_item(self, item_id: str) -> bool:
        """
        Deleta um item pelo ID.
        
        Lógica:
        1. item = self.buscar_por_id(item_id)
        2. Se item for None, return False
        3. self.db.delete(item)
        4. self.db.commit()
        5. return True
        """
        item = self.buscar_por_id(item_id)
        if item is None:
            return False
        self.db.delete(item)
        self.db.commit()
        return True