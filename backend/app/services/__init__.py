"""
Services Layer - Camada de Negócio

Este módulo exporta todos os services da aplicação para facilitar imports.

Uso:
    from app.services import LoteService, ItemService, NCMService
    
    # Ao invés de:
    # from app.services.lote_service import LoteService
    # from app.services.item_service import ItemService
    # from app.services.ncm_service import NCMService
"""

from .lote_service import (
    LoteService,
    LoteNotFoundException,
    LoteValidationError
)

from .item_service import (
    ItemService,
    ItemNotFoundException,
    ItemValidationError
)

from .ncm_service import (
    NCMService,
    NCMNotFoundException,
    NCMValidationError
)


__all__ = [
    # Services
    "LoteService",
    "ItemService",
    "NCMService",
    
    # Exceções - Lote
    "LoteNotFoundException",
    "LoteValidationError",
    
    # Exceções - Item
    "ItemNotFoundException",
    "ItemValidationError",
    
    # Exceções - NCM
    "NCMNotFoundException",
    "NCMValidationError",
]
