"""
Carousel Providers Package

Modular carousel generation with pluggable backends.

Usage:
    from providers import get_provider, list_providers
    
    # List available providers
    print(list_providers())  # ['pillow_openai', 'pillow_unsplash', 'canva', ...]
    
    # Get a provider instance
    provider = get_provider('pillow_openai', theme='dark')
    
    # Generate carousels
    await provider.process_day('2026-01-21')
"""

from typing import Dict, Type, List, Optional
from providers.base import CarouselProvider
from providers.config import CarouselConfig

# Provider registry - populated by @register_provider decorator
_PROVIDERS: Dict[str, Type[CarouselProvider]] = {}


def register_provider(name: str):
    """
    Decorator to register a provider class.
    
    Usage:
        @register_provider("my_provider")
        class MyProvider(CarouselProvider):
            ...
    """
    def decorator(cls: Type[CarouselProvider]):
        cls.name = name
        _PROVIDERS[name] = cls
        return cls
    return decorator


def get_provider(name: str, **kwargs) -> CarouselProvider:
    """
    Get a provider instance by name.
    
    Args:
        name: Provider identifier (e.g., 'pillow_openai', 'canva')
        **kwargs: Arguments passed to provider constructor
        
    Returns:
        Instantiated provider
        
    Raises:
        KeyError: If provider not found
    """
    if name not in _PROVIDERS:
        available = ", ".join(_PROVIDERS.keys()) if _PROVIDERS else "(none registered)"
        raise KeyError(f"Provider '{name}' not found. Available: {available}")
    
    return _PROVIDERS[name](**kwargs)


def get_provider_with_fallback(
    preferred: str, 
    fallbacks: Optional[List[str]] = None,
    **kwargs
) -> CarouselProvider:
    """
    Get a provider with fallback chain.
    
    Args:
        preferred: Primary provider to try
        fallbacks: List of fallback providers if preferred fails
        **kwargs: Arguments passed to provider constructor
        
    Returns:
        First available provider instance
        
    Raises:
        ValueError: If no providers available
    """
    fallbacks = fallbacks or []
    
    for name in [preferred] + fallbacks:
        try:
            return get_provider(name, **kwargs)
        except KeyError:
            continue
    
    raise ValueError(
        f"No provider available. Tried: {[preferred] + fallbacks}. "
        f"Available: {list_providers()}"
    )


def list_providers() -> List[str]:
    """List all registered provider names."""
    return list(_PROVIDERS.keys())


def is_provider_available(name: str) -> bool:
    """Check if a provider is registered."""
    return name in _PROVIDERS


# Auto-import providers to trigger registration
# These imports happen at module load time
try:
    from providers import pillow_legacy  # Legacy wrapper for existing code
except ImportError as e:
    pass  # Silently skip if not available

try:
    from providers import pillow_openai  # DALL-E powered provider
except ImportError as e:
    pass  # Silently skip if not available

try:
    from providers import pillow_unsplash  # Free Unsplash images
except ImportError as e:
    pass  # Silently skip if not available

# Future providers:
# from providers import pillow_gemini  # Gemini Imagen
# from providers import canva_mcp      # Canva MCP
# from providers import gamma          # Gamma API


__all__ = [
    'CarouselProvider',
    'CarouselConfig',
    'register_provider',
    'get_provider',
    'get_provider_with_fallback',
    'list_providers',
    'is_provider_available',
]
