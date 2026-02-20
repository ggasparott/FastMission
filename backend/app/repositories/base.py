from typing import TypeVar, Generic, Type, List, Optional
from unittest import skip
from sqlalchemy.orm import Session
from app.models.base import Base

ModelType = TypeVar("ModelType", bound=Base)

class BaseRepository(Generic[ModelType]):
    """
    Repositório base genérico que implementa operações CRUD padrão.
    
    Todos os repositórios específicos devem herdar desta classe para
    reaproveitar a lógica comum de acesso a dados.
    
    Args:
        ModelType: Tipo genérico que representa o modelo SQLAlchemy
    """

    def __init__(self, db: Session, model: Type[ModelType]):
        """
        Inicializa o repositório com uma sessão de banco e o modelo.
        
        Args:
            db: Sessão do SQLAlchemy para operações no banco
            model: Classe do modelo SQLAlchemy (ex: Lote, Item, NCM)
        """
        self.db = db
        self.model = model
        

    def buscar_por_id(self, id: str) -> Optional[ModelType]:
        """
        Busca um registro pelo ID.
        
        Args:
            id: Identificador único do registro
            
        Returns:
            Objeto do modelo encontrado ou None se não existir
        """
        return self.db.query(self.model).filter(self.model.id == id).first()
    
    def  listar_todos(self, skip: int = 0, limit: int = None) -> List[ModelType]:
        """
        Lista todos os registros com paginação opcional.
        
        Args:
            skip: Número de registros a pular (para paginação)
            limit: Número máximo de registros a retornar
            
        Returns:
            Lista de objetos do modelo
        """
        query = self.db.query(self.model)
        if skip > 0:
            query = query.offset(skip)
        if limit is not None:
            query = query.limit(limit)
        return query.all()
    
    def criar(self, obj: ModelType) -> ModelType:
        """
        Cria um novo registro no banco de dados.
        
        Args:
            obj: Instância do modelo já populada com dados
            
        Returns:
            Objeto criado com ID e campos gerados pelo banco
            
        Raises:
            Exception: Se houver erro na criação (após rollback)
        """
        try:
            self.db.add(obj)
            self.db.commit()
            self.db.refresh(obj)
            return obj
        except Exception as e:
            self.db.rollback()
            raise e
        
    def atualizar(self, obj: ModelType, updates: dict) -> Optional[ModelType]:
            """
            Atualiza um registro existente com novos valores.
            
            Args:
                obj: Objeto do modelo a ser atualizado
                updates: Dicionário com campos e valores para atualizar
                
            Returns:
                Objeto atualizado ou None se não encontrado
                
            Raises:
                Exception: Se houver erro na atualização (após rollback)
            """
            result = self.buscar_por_id(obj.id)
            if not result:
                return None
            try:
                for key, value in updates.items():
                    if hasattr(result, key):
                        setattr(result, key, value)
                self.db.commit()
                self.db.refresh(result)
                return result
            except Exception as e:
                self.db.rollback()
                raise e

    def deletar(self, id: str) -> bool:
        """
        Deleta um registro pelo ID.
        
        Args:
            id: Identificador do registro a deletar
            
        Returns:
            True se deletado com sucesso, False se não encontrado
            
        Raises:
            Exception: Se houver erro na deleção (após rollback)
        """
        obj = self.buscar_por_id(id)
        if not obj:
            return False
        try:
            self.db.delete(obj)
            self.db.commit()
            return True
        except Exception as e:
            self.db.rollback()
            raise e
        
    def contar(self) -> int:
        """
        Conta o total de registros na tabela.
        
        Returns:
            Número total de registros
        """
        return self.db.query(self.model).count()
    
    def existe(self, id) -> bool:
        """
        Verifica se um registro existe pelo ID.
        
        Args:
            id: Identificador a verificar
            
        Returns:
            True se existe, False caso contrário
        """
        return self.buscar_por_id(id) is not None