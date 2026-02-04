"""
Properties module - Gestão de propriedades
"""

from .controller import property_controller
from .models import Property
from .router import router
from .schemas import PropertyCreate, PropertyResponse, PropertyUpdate

__all__ = [
    "Property",
    "PropertyCreate",
    "PropertyUpdate",
    "PropertyResponse",
    "property_repository",
    "property_controller",
    "router",
]
