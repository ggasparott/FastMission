from typing import List, Optional
from sqlalchemy.orm import Session, joinedload
from app.repositories.base import BaseRepository
from app.models import Lote


class LoteRepository(BaseRepository[Lote]):
    """
    Repositório específico para operações relacionadas a Lote.
    
    Herda do BaseRepository para reutilizar métodos CRUD genéricos.
    """

    def __init__(self, db: Session):
        super().__init__(db, Lote)


    def buscar_por_status(self, status: str) -> List[Lote]:
        """
        Busca lotes por status.
        
        Args:
            status: Status do lote a ser buscado
            
        Returns:
            Lista de lotes com o status especificado
        """
        return self.db.query(self.model).filter(self.model.status == status).all()

    def buscar_recentes(self, limit: int = 10) -> List[Lote]:
        return self.db.query(Lote).order_by(Lote.created_at.desc()).limit(limit).all()
        
    def contar_por_status(self, status: str) -> int:
        return self.db.query(Lote).filter(Lote.status == status).count()

    def buscar_com_itens(self, lote_id: str) -> Optional[Lote]:
        return self.db.query(Lote).options(joinedload(Lote.itens)).filter(Lote.id == lote_id).first()