"""
Provider Unit Tests

Tests for the carousel provider system including:
- Registry functions
- Provider instantiation
- Graceful degradation without API keys
"""

import pytest
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestProviderRegistry:
    """Tests for the provider registry system."""
    
    def test_list_providers_returns_list(self):
        """list_providers should return a list."""
        from providers import list_providers
        
        result = list_providers()
        assert isinstance(result, list)
    
    def test_list_providers_contains_expected(self):
        """list_providers should contain expected providers."""
        from providers import list_providers
        
        result = list_providers()
        expected = ['pillow_legacy', 'pillow_openai', 'pillow_unsplash', 'pillow_gemini', 'gamma']
        
        for provider in expected:
            assert provider in result, f"Expected {provider} in providers list"
    
    def test_get_provider_returns_correct_type(self):
        """get_provider should return the correct provider type."""
        from providers import get_provider
        from providers.base import CarouselProvider
        
        provider = get_provider('pillow_unsplash')
        assert isinstance(provider, CarouselProvider)
        assert provider.name == 'pillow_unsplash'
    
    def test_get_provider_unknown_raises_error(self):
        """get_provider should raise error for unknown provider."""
        from providers import get_provider
        
        with pytest.raises((ValueError, KeyError)):
            get_provider('unknown_provider')
    
    def test_get_provider_accepts_theme(self):
        """get_provider should pass theme to provider."""
        from providers import get_provider
        
        provider = get_provider('pillow_unsplash', theme='light')
        assert provider.theme == 'light'


class TestProviderInstantiation:
    """Tests for individual provider instantiation."""
    
    def test_pillow_unsplash_instantiates(self):
        """pillow_unsplash should instantiate without API key."""
        from providers import get_provider
        
        provider = get_provider('pillow_unsplash')
        assert provider.name == 'pillow_unsplash'
    
    def test_gamma_instantiates_without_key(self):
        """gamma should instantiate gracefully without API key."""
        from providers import get_provider
        
        # Clear any existing key
        old_key = os.environ.pop('GAMMA_API_KEY', None)
        
        try:
            provider = get_provider('gamma')
            assert provider.name == 'gamma'
            assert provider.api_key is None
        finally:
            if old_key:
                os.environ['GAMMA_API_KEY'] = old_key
    
    def test_pillow_openai_instantiates_without_key(self):
        """pillow_openai should instantiate gracefully without API key."""
        from providers import get_provider
        
        # Clear any existing key
        old_key = os.environ.pop('OPENAI_API_KEY', None)
        
        try:
            provider = get_provider('pillow_openai')
            assert provider.name == 'pillow_openai'
        finally:
            if old_key:
                os.environ['OPENAI_API_KEY'] = old_key


class TestProviderMethods:
    """Tests for provider method signatures."""
    
    def test_provider_has_generate_carousel(self):
        """All providers should have generate_carousel method."""
        from providers import get_provider, list_providers
        
        for name in list_providers():
            provider = get_provider(name)
            assert hasattr(provider, 'generate_carousel')
            assert callable(provider.generate_carousel)
    
    def test_provider_has_save_as_pdf(self):
        """All providers should have save_as_pdf method."""
        from providers import get_provider, list_providers
        
        for name in list_providers():
            provider = get_provider(name)
            assert hasattr(provider, 'save_as_pdf')
            assert callable(provider.save_as_pdf)
    
    def test_provider_has_process_day(self):
        """All providers should have process_day method."""
        from providers import get_provider, list_providers
        
        for name in list_providers():
            provider = get_provider(name)
            assert hasattr(provider, 'process_day')
            assert callable(provider.process_day)


class TestCarouselConfig:
    """Tests for CarouselConfig."""
    
    def test_config_has_dimensions(self):
        """CarouselConfig should have slide dimensions."""
        from providers.config import CarouselConfig
        
        assert CarouselConfig.SLIDE_WIDTH == 1080
        assert CarouselConfig.SLIDE_HEIGHT == 1350
    
    def test_config_has_themes(self):
        """CarouselConfig should have theme definitions."""
        from providers.config import CarouselConfig
        
        assert 'dark' in CarouselConfig.THEMES
        assert 'light' in CarouselConfig.THEMES
    
    def test_themes_have_required_colors(self):
        """Themes should have all required color keys."""
        from providers.config import CarouselConfig
        
        required_keys = ['bg', 'text', 'accent', 'secondary', 'muted']
        
        for theme_name, theme in CarouselConfig.THEMES.items():
            for key in required_keys:
                assert key in theme, f"Theme {theme_name} missing {key}"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
