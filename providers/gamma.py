"""
Gamma API Provider

LinkedIn carousel generation using Gamma.app's API.
Based on best practices from "Carousels. - How to AI" guide.

Workflow:
1. Gamma Studio mode → Portrait (4:5 / 1080x1350)
2. 10 slides structure (Hook → Stakes → Insight → Content → CTA)
3. "Just vibes" text quantity (minimal text, high impact)
4. Nano Banana Pro for AI images

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
    LinkedIn carousel provider using Gamma.app API.
    
    Based on the "Carousels. - How to AI" best practices:
    - Studio mode with Portrait 4:5 format
    - 10 slides structure
    - "Just vibes" (minimal text)
    - Nano Banana Pro for AI images
    
    Requires: GAMMA_API_KEY environment variable (Pro plan)
    """
    
    name = "gamma"
    
    # Gamma API endpoints
    API_BASE = "https://api.gamma.app/v1"
    
    # Optimal slide count from best practices
    OPTIMAL_SLIDES = 10
    
    # AI image quality tiers (credits per slide)
    IMAGE_QUALITY = {
        'none': 0,       # Unsplash only
        'basic': 2,      # Basic AI (Nano Banana)
        'advanced': 4,   # Advanced AI
        'premium': 8     # Premium AI (Nano Banana Pro - recommended)
    }
    
    def __init__(
        self, 
        theme: str = "dark", 
        image_quality: str = "premium",  # Default to premium per best practices
        **kwargs
    ):
        super().__init__(theme=theme, **kwargs)
        self.api_key = os.getenv("GAMMA_API_KEY")
        self.image_quality = image_quality
        
        if not self.api_key:
            print("Warning: GAMMA_API_KEY not set. Gamma provider will not work.")
        
        if not AIOHTTP_AVAILABLE:
            print("Warning: aiohttp not installed. Install with: pip install aiohttp")
    
    def _estimate_credits(self, slides: int = 10) -> int:
        """Estimate credits for a carousel."""
        base_credits = 10
        image_credits = self.IMAGE_QUALITY.get(self.image_quality, 2) * slides
        return base_credits + image_credits
    
    def _build_carousel_outline(self, item: Dict) -> str:
        """
        Build the 10-slide carousel outline following best practices.
        
        Structure from "Carousels. - How to AI":
        1. Hook (polarizing/curiosity-gap headline)
        2. Stakes (why this matters now)
        3. Core Insight/Thesis
        4-9. Content slides with specific insights
        10. CTA
        """
        headline = item.get('headline', 'AI News Update')
        summary = item.get('summary', '')
        bullets = item.get('bullets', [])
        hot_take = item.get('hot_take', '')
        category = item.get('category', 'AI News')
        
        # Ensure we have enough content for 10 slides
        while len(bullets) < 6:
            bullets.append(f"Key insight about {headline}")
        
        outline = f"""# Slide 1: The Hook
{headline}

# Slide 2: The Stakes  
Why This Matters Right Now
{summary if summary else 'This changes everything for AI.'}

# Slide 3: The Core Insight
🔥 {hot_take if hot_take else bullets[0]}

# Slide 4: Key Point 1
{bullets[0]}

# Slide 5: Key Point 2
{bullets[1]}

# Slide 6: Key Point 3
{bullets[2]}

# Slide 7: What This Means
The implications are massive.
{bullets[3] if len(bullets) > 3 else 'This will reshape the industry.'}

# Slide 8: What's Next
{bullets[4] if len(bullets) > 4 else 'The future is being written now.'}

# Slide 9: The Takeaway
{bullets[5] if len(bullets) > 5 else hot_take}

# Slide 10: CTA
Follow for Daily AI Insights
Never miss another breakthrough.
"""
        return outline
    
    async def _create_presentation(self, item: Dict) -> Optional[str]:
        """
        Create a presentation via Gamma API using Studio mode.
        
        Settings based on best practices:
        - Mode: Studio BETA
        - Format: Portrait (4:5)
        - Cards: 10
        - Text: "Just vibes" (minimal)
        - Images: Nano Banana Pro
        """
        if not self.api_key:
            raise ValueError(
                "GAMMA_API_KEY not set. Get your API key from gamma.app with a Pro subscription."
            )
        
        headline = item.get('headline', 'AI News Update')
        outline = self._build_carousel_outline(item)
        
        # Gamma API payload based on best practices
        payload = {
            "title": headline,
            "content": outline,
            "mode": "studio",           # Studio mode for best results
            "format": "social",          # Social media format
            "card_size": "portrait",     # Portrait 4:5 (1080x1350)
            "cards": self.OPTIMAL_SLIDES,
            "text_quantity": "vibes",    # "Just vibes" - minimal text
            "theme": self.theme,
            "image_source": "nano_banana_pro" if self.image_quality == "premium" else "ai",
            "image_quality": self.image_quality,
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
        """Export presentation slides as images (1080x1350)."""
        if not self.api_key or not PIL_AVAILABLE:
            return []
            
        headers = {"Authorization": f"Bearer {self.api_key}"}
        slides = []
        
        async with aiohttp.ClientSession() as session:
            # Get export URLs
            async with session.get(
                f"{self.API_BASE}/presentations/{presentation_id}/export",
                params={"format": "png", "size": "1080x1350"},
                headers=headers
            ) as response:
                if response.status != 200:
                    return []
                    
                data = await response.json()
                slide_urls = data.get("slides", [])
            
            # Download each slide
            for url in slide_urls[:self.OPTIMAL_SLIDES]:
                async with session.get(url) as response:
                    if response.status == 200:
                        image_data = await response.read()
                        img = Image.open(BytesIO(image_data))
                        # Ensure LinkedIn carousel dimensions (4:5)
                        if img.size != (self.width, self.height):
                            img = img.resize(
                                (self.width, self.height), 
                                Image.Resampling.LANCZOS
                            )
                        slides.append(img)
        
        return slides
    
    async def generate_carousel(self, item: Dict) -> List["Image.Image"]:
        """
        Generate carousel slides using Gamma API.
        
        Following best practices:
        - 10 slides (Hook → Stakes → Insight → Content × 6 → CTA)
        - Portrait 4:5 format (1080x1350)
        - Nano Banana Pro AI images
        - Minimal text ("Just vibes")
        """
        if not self.api_key:
            raise ValueError(
                "GAMMA_API_KEY not set. "
                "Get your API key from gamma.app with a Pro subscription ($15/mo). "
            )
        
        if not PIL_AVAILABLE:
            raise RuntimeError("PIL not available - install with: pip install pillow")
        
        est_credits = self._estimate_credits()
        print(f"    🚀 Creating Gamma presentation ({self.OPTIMAL_SLIDES} slides, ~{est_credits} credits)...")
        
        # Create presentation
        presentation_id = await self._create_presentation(item)
        if not presentation_id:
            raise RuntimeError("Failed to create Gamma presentation")
        
        print(f"    ⏳ Generating with Nano Banana Pro...")
        
        # Wait for completion
        if not await self._wait_for_completion(presentation_id):
            raise RuntimeError("Gamma presentation generation failed or timed out")
        
        print(f"    📥 Exporting {self.OPTIMAL_SLIDES} slides (1080x1350)...")
        
        # Export slides
        slides = await self._export_slides(presentation_id)
        
        if not slides:
            raise RuntimeError("Failed to export Gamma slides")
        
        print(f"    ✅ Generated {len(slides)} slides")
        
        return slides
