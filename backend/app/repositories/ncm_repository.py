from typing import List, Optional
from sqlalchemy.orm import Session
from app.repositories.base import BaseRepository
from app.models import NCMOficial

class NCMRepository(BaseRepository[NCMOficial]):
    """
    Repositório específico para operações relacionadas a NCMOficial.
    
    Herda do BaseRepository para reutilizar métodos CRUD genéricos.
    """
    def __init__(self, db: Session):
        super().__init__(db, NCMOficial)


    def buscar_por_codigo(self, codigo: str) -> Optional[NCMOficial]:
        busca = self.db.query(NCMOficial).filter(NCMOficial.codigo == codigo).first()
        if not busca:
            return None
        return busca

    def buscar_por_prefixo(self, prefixo: str, limit: int = 10) -> List[NCMOficial]:
        return self.db.query(NCMOficial).filter(NCMOficial.codigo.like(f"{prefixo}%")).limit(limit).all()

    def validar_codigo(self, codigo: str) -> bool:
        ncm = self.buscar_por_codigo(codigo)
        return ncm is not None

    def criar_lote(self, ncms: List[dict]) -> int:
        self.db.bulk_insert_mappings(NCMOficial, ncms)
        self.db.commit()
        return len(ncms)

    def buscar_por_descricao(self, termo: str, limit: int = 10) -> List[NCMOficial]:
        return self.db.query(NCMOficial).filter(NCMOficial.descricao.ilike(f"%{termo}%")).limit(limit).all()

    def limpar_tabela(self) -> None:
        self.db.query(NCMOficial).delete()
        self.db.commit()