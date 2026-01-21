"""
Carousel Provider System

Gamma API provider for generating LinkedIn carousels.
"""

from providers.base import CarouselProvider
from providers.config import CarouselConfig

# Provider registry
_providers = {}


def register_provider(name: str):
    """Decorator to register a provider class."""
    def decorator(cls):
        _providers[name] = cls
        return cls
    return decorator


def get_provider(name: str, **kwargs) -> CarouselProvider:
    """Get a provider instance by name."""
    if name not in _providers:
        available = list(_providers.keys())
        raise ValueError(f"Unknown provider: {name}. Available: {available}")
    
    return _providers[name](**kwargs)


def list_providers() -> list:
    """List all registered providers."""
    return list(_providers.keys())


# Import gamma provider
try:
    from providers import gamma
except ImportError as e:
    print(f"Warning: Could not import gamma provider: {e}")


__all__ = [
    "CarouselProvider",
    "CarouselConfig",
    "register_provider",
    "get_provider",
    "list_providers",
]
