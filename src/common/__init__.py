"""
Módulo común con utilidades y protocolo de comunicación.
"""

from .protocolo import Protocolo, TipoMensaje, MensajeFactory
from .utils import (
    ConfigLoader,
    ImageUtils,
    LogManager,
    PathUtils,
    ThreadSafeCounter
)

__all__ = [
    'Protocolo',
    'TipoMensaje',
    'MensajeFactory',
    'ConfigLoader',
    'ImageUtils',
    'LogManager',
    'PathUtils',
    'ThreadSafeCounter'
]
