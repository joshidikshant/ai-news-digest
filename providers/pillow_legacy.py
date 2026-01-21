"""
Pillow Legacy Provider

Wraps the existing CarouselGenerator class as a provider.
This allows testing the provider pattern without rewriting the Pillow code.

After Phase 2, this will be replaced by dedicated providers:
- pillow_openai.py (DALL-E images)
- pillow_gemini.py (Gemini Imagen)
- pillow_unsplash.py (free stock images)
"""

import sys
import os

# Add parent directory to path to import generate_carousel
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from typing import List, Dict, TYPE_CHECKING

# Optional PIL import - only needed at runtime
if TYPE_CHECKING:
    from PIL import Image

from providers.base import CarouselProvider
from providers import register_provider


@register_provider("pillow_legacy")
class PillowLegacyProvider(CarouselProvider):
    """
    Legacy provider that wraps the existing CarouselGenerator.
    
    This is a transitional provider that delegates to the original
    implementation in generate_carousel.py.
    """
    
    name = "pillow_legacy"
    
    def __init__(self, theme: str = "dark", generate_images: bool = True, **kwargs):
        super().__init__(theme=theme, **kwargs)
        self.generate_images = generate_images
        self._generator = None
    
    def _get_generator(self):
        """Lazy-load the generator to avoid circular imports."""
        if self._generator is None:
            # Import here to avoid circular dependency
            from generate_carousel import CarouselGenerator
            self._generator = CarouselGenerator(
                theme=self.theme, 
                generate_images=self.generate_images
            )
        return self._generator
    
    async def generate_carousel(self, item: Dict) -> List:
        """Generate carousel using existing CarouselGenerator."""
        generator = self._get_generator()
        return await generator.generate_carousel_async(item)
    
    async def process_day(self, date_str: str) -> None:
        """Process a day using existing CarouselGenerator."""
        generator = self._get_generator()
        await generator.process_day_async(date_str)
