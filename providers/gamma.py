"""
Gamma API Provider

Carousel generation using Gamma.app's API for professional presentations.
Best option for daily automation with built-in AI images at $15/month.

Cost: $15/mo Pro plan (~4000 credits)
- Unsplash only: ~20 credits = 200 carousels/month
- Basic AI: ~30 credits = 133 carousels/month
- Premium AI: ~120 credits = 33 carousels/month
"""

import os
import asyncio
from typing import List, Dict, Optional
from io import BytesIO

try:
    import aiohttp
    AIOHTTP_AVAILABLE = True
except ImportError:
    AIOHTTP_AVAILABLE = False
    aiohttp = None

try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    Image = None

from providers.base import CarouselProvider
from providers.config import CarouselConfig
from providers import register_provider


@register_provider("gamma")
class GammaProvider(CarouselProvider):
    """
    Premium carousel provider using Gamma.app API.
    
    Gamma generates professional presentations from content with
    built-in AI image generation at multiple quality tiers.
    
    Requires: GAMMA_API_KEY environment variable (Pro plan)
    """
    
    name = "gamma"
    
    # Gamma API endpoints
    API_BASE = "https://api.gamma.app/v1"
    
    # AI image quality tiers (credits per slide)
    IMAGE_QUALITY = {
        'none': 0,       # No AI images (Unsplash only)
        'basic': 2,      # Basic AI images
        'advanced': 4,   # Advanced AI images
        'premium': 8     # Premium AI images (best quality)
    }
    
    def __init__(
        self, 
        theme: str = "dark", 
        image_quality: str = "basic",
        **kwargs
    ):
        super().__init__(theme=theme, **kwargs)
        self.api_key = os.getenv("GAMMA_API_KEY")
        self.image_quality = image_quality
        
        if not self.api_key:
            print("Warning: GAMMA_API_KEY not set. Gamma provider will not work.")
        
        if not AIOHTTP_AVAILABLE:
            print("Warning: aiohttp not installed. Install with: pip install aiohttp")
    
    def _estimate_credits(self, slides: int = 5) -> int:
        """Estimate credits for a carousel."""
        base_credits = 10  # Base cost per presentation
        image_credits = self.IMAGE_QUALITY.get(self.image_quality, 2) * slides
        return base_credits + image_credits
    
    async def _create_presentation(self, item: Dict) -> Optional[str]:
        """
        Create a presentation via Gamma API.
        
        Returns presentation ID if successful.
        """
        if not self.api_key:
            raise ValueError(
                "GAMMA_API_KEY not set. Get your API key from gamma.app with a Pro subscription."
            )
        
        headline = item.get('headline', 'AI News Update')
        bullets = item.get('bullets', [])
        hot_take = item.get('hot_take', '')
        
        # Build the presentation content
        content = f"""# {headline}

## Key Insights

{chr(10).join(f'- {bullet}' for bullet in bullets[:3])}

## Hot Take 🔥

{hot_take}

## Follow for More

Follow for daily AI insights!
"""
        
        payload = {
            "title": headline,
            "content": content,
            "style": "modern",
            "theme": self.theme,
            "format": "carousel",  # LinkedIn carousel format
            "image_quality": self.image_quality,
            "slides": 5
        }
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.API_BASE}/presentations",
                    json=payload,
                    headers=headers
                ) as response:
                    if response.status == 201:
                        data = await response.json()
                        return data.get("id")
                    elif response.status == 401:
                        raise ValueError("Invalid GAMMA_API_KEY")
                    elif response.status == 402:
                        raise ValueError("Gamma credits exhausted. Upgrade your plan.")
                    else:
                        error = await response.text()
                        print(f"    ⚠️ Gamma API error: {response.status} - {error}")
                        return None
        except aiohttp.ClientError as e:
            print(f"    ⚠️ Network error: {e}")
            return None
    
    async def _wait_for_completion(
        self, 
        presentation_id: str, 
        timeout: int = 120
    ) -> bool:
        """Poll until presentation is ready."""
        if not self.api_key:
            return False
            
        headers = {"Authorization": f"Bearer {self.api_key}"}
        
        async with aiohttp.ClientSession() as session:
            for _ in range(timeout // 5):
                async with session.get(
                    f"{self.API_BASE}/presentations/{presentation_id}",
                    headers=headers
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get("status") == "completed":
                            return True
                        elif data.get("status") == "failed":
                            print(f"    ⚠️ Presentation generation failed")
                            return False
                
                await asyncio.sleep(5)
        
        print(f"    ⚠️ Timeout waiting for presentation")
        return False
    
    async def _export_slides(self, presentation_id: str) -> List["Image.Image"]:
        """Export presentation slides as images."""
        if not self.api_key or not PIL_AVAILABLE:
            return []
            
        headers = {"Authorization": f"Bearer {self.api_key}"}
        slides = []
        
        async with aiohttp.ClientSession() as session:
            # Get export URLs
            async with session.get(
                f"{self.API_BASE}/presentations/{presentation_id}/export",
                params={"format": "png"},
                headers=headers
            ) as response:
                if response.status != 200:
                    return []
                    
                data = await response.json()
                slide_urls = data.get("slides", [])
            
            # Download each slide
            for url in slide_urls[:5]:  # Max 5 slides for carousel
                async with session.get(url) as response:
                    if response.status == 200:
                        image_data = await response.read()
                        img = Image.open(BytesIO(image_data))
                        # Resize to LinkedIn carousel dimensions
                        img = img.resize(
                            (self.width, self.height), 
                            Image.Resampling.LANCZOS
                        )
                        slides.append(img)
        
        return slides
    
    async def generate_carousel(self, item: Dict) -> List["Image.Image"]:
        """Generate carousel slides using Gamma API."""
        if not self.api_key:
            raise ValueError(
                "GAMMA_API_KEY not set. "
                "Get your API key from gamma.app with a Pro subscription ($15/mo). "
                "Or use --provider=pillow_unsplash for free generation."
            )
        
        if not PIL_AVAILABLE:
            raise RuntimeError("PIL not available - install with: pip install pillow")
        
        print(f"    🚀 Creating Gamma presentation (est. {self._estimate_credits()} credits)...")
        
        # Create presentation
        presentation_id = await self._create_presentation(item)
        if not presentation_id:
            raise RuntimeError("Failed to create Gamma presentation")
        
        print(f"    ⏳ Waiting for generation...")
        
        # Wait for completion
        if not await self._wait_for_completion(presentation_id):
            raise RuntimeError("Gamma presentation generation failed or timed out")
        
        print(f"    📥 Exporting slides...")
        
        # Export slides
        slides = await self._export_slides(presentation_id)
        
        if not slides:
            raise RuntimeError("Failed to export Gamma slides")
        
        print(f"    ✅ Generated {len(slides)} slides")
        
        return slides
