"""
Módulo de propriedades
"""

from .router import router
from .repository import PropertyRepository
from .schema import PropertyCreate, PropertyResponse, PropertyUpdate
from .models import Property

__all__ = ["router", "PropertyRepository", "PropertyCreate", "PropertyResponse", "PropertyUpdate", "Property"]