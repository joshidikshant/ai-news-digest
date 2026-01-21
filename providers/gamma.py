"""
Gamma API Provider

LinkedIn carousel generation using Gamma.app's official API.
Docs: https://developers.gamma.app/reference/generate-a-gamma

API Workflow:
1. POST /v1.0/generations → Creates generation, returns generationId
2. Poll GET /v1.0/generations/{id} → Wait for status=completed
3. Download exportUrl (PDF) from response

Cost: $15/mo Pro plan
"""

import os
import asyncio
import time
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
    LinkedIn carousel provider using Gamma.app official API.
    
    API Reference: https://developers.gamma.app/reference/generate-a-gamma
    
    Requires: GAMMA_API_KEY environment variable
    """
    
    name = "gamma"
    
    # Correct Gamma API base URL
    API_BASE = "https://public-api.gamma.app/v1.0"
    
    # Optimal settings for LinkedIn carousels
    NUM_CARDS = 10
    
    def __init__(
        self, 
        theme: str = "dark", 
        image_quality: str = "premium",
        **kwargs
    ):
        super().__init__(theme=theme, **kwargs)
        self.api_key = os.getenv("GAMMA_API_KEY")
        self.image_quality = image_quality
        
        if not self.api_key:
            print("Warning: GAMMA_API_KEY not set. Gamma provider will not work.")
        
        if not AIOHTTP_AVAILABLE:
            print("Warning: aiohttp not installed. Install with: pip install aiohttp")
    
    def _build_input_text(self, item: Dict) -> str:
        """
        Build input text for Gamma generation.
        
        Structure: 10 slides for LinkedIn carousel
        - Slide 1: Hook
        - Slide 2: Stakes  
        - Slide 3: Core Insight
        - Slides 4-9: Content
        - Slide 10: CTA
        """
        headline = item.get('headline', 'AI News Update')
        summary = item.get('summary', '')
        bullets = item.get('bullets', [])
        hot_take = item.get('hot_take', '')
        
        # Ensure enough bullets
        while len(bullets) < 6:
            bullets.append(f"Key insight about {headline}")
        
        input_text = f"""Create a 10-slide LinkedIn carousel about: {headline}

---
SLIDE 1: THE HOOK
{headline}

---
SLIDE 2: THE STAKES
Why This Matters Right Now
{summary if summary else 'This changes everything.'}

---
SLIDE 3: THE CORE INSIGHT
🔥 {hot_take if hot_take else bullets[0]}

---
SLIDE 4: KEY POINT 1
{bullets[0]}

---
SLIDE 5: KEY POINT 2
{bullets[1]}

---
SLIDE 6: KEY POINT 3
{bullets[2]}

---
SLIDE 7: IMPLICATIONS
{bullets[3] if len(bullets) > 3 else 'This will reshape the industry.'}

---
SLIDE 8: WHAT'S NEXT
{bullets[4] if len(bullets) > 4 else 'The future is being written now.'}

---
SLIDE 9: THE TAKEAWAY
{bullets[5] if len(bullets) > 5 else hot_take}

---
SLIDE 10: CALL TO ACTION
Follow for Daily AI Insights
Never miss another breakthrough.
"""
        return input_text
    
    async def _create_generation(self, item: Dict) -> Optional[str]:
        """
        Create a Gamma generation via API.
        
        POST https://public-api.gamma.app/v1.0/generations
        Returns: generationId
        """
        if not self.api_key:
            raise ValueError("GAMMA_API_KEY not set.")
        
        if not AIOHTTP_AVAILABLE:
            raise RuntimeError("aiohttp not installed. Run: pip install aiohttp")
        
        headline = item.get('headline', 'AI News Update')
        input_text = self._build_input_text(item)
        
        # Map image quality to Gamma image model
        # Valid models: dall-e-3, imagen-3-flash, imagen-3-pro, imagen-4-pro, 
        # imagen-4-ultra, flux-1-pro, flux-1-quick, flux-1-ultra, etc.
        image_model_map = {
            'none': None,
            'basic': 'imagen-3-flash',      # Fast, good quality
            'advanced': 'flux-1-pro',       # Higher quality
            'premium': 'imagen-4-ultra'     # Best quality
        }
        
        # Get folder ID from env or use default
        folder_id = os.getenv("GAMMA_FOLDER_ID", "74df73cje79wzca")
        
        payload = {
            "inputText": input_text,
            "textMode": "preserve",  # Use our structured text as-is
            "format": "social",       # Social media format for carousels
            "numCards": self.NUM_CARDS,
            "exportAs": "pdf",        # Export as PDF for LinkedIn
            "folderIds": [folder_id], # Array of folder IDs per API docs
            "textOptions": {
                "tone": "Professional",
                "audience": "LinkedIn Tech Professionals",
                "amount": "brief"     # Minimal text for carousels
            },
            "imageOptions": {
                "source": "aiGenerated" if self.image_quality != 'none' else "unsplash",
                "model": image_model_map.get(self.image_quality, 'imagen-3-flash')
            },
            "cardOptions": {
                "dimensions": "4x5"   # Portrait for LinkedIn (1080x1350)
            }
        }
        
        # Remove None values
        if payload["imageOptions"]["model"] is None:
            del payload["imageOptions"]["model"]
        
        headers = {
            "X-API-KEY": self.api_key,
            "Content-Type": "application/json",
            "accept": "application/json"
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.API_BASE}/generations",
                    json=payload,
                    headers=headers
                ) as response:
                    response_text = await response.text()
                    
                    if response.status == 200 or response.status == 201:
                        data = await response.json()
                        gen_id = data.get("generationId") or data.get("id")
                        print(f"    ✅ Generation started: {gen_id}")
                        return gen_id
                    elif response.status == 401:
                        raise ValueError("Invalid GAMMA_API_KEY")
                    elif response.status == 402:
                        raise ValueError("Gamma credits exhausted")
                    else:
                        print(f"    ⚠️ Gamma API error: {response.status} - {response_text}")
                        return None
        except aiohttp.ClientError as e:
            print(f"    ⚠️ Network error: {e}")
            return None
    
    async def _poll_generation(
        self, 
        generation_id: str, 
        timeout: int = 180,
        poll_interval: int = 5
    ) -> Optional[Dict]:
        """
        Poll generation status until completed.
        
        GET https://public-api.gamma.app/v1.0/generations/{generationId}
        Returns: Full response with exportUrl when completed
        """
        if not self.api_key:
            return None
        
        headers = {
            "X-API-KEY": self.api_key,
            "accept": "application/json"
        }
        
        start_time = time.time()
        
        async with aiohttp.ClientSession() as session:
            while (time.time() - start_time) < timeout:
                async with session.get(
                    f"{self.API_BASE}/generations/{generation_id}",
                    headers=headers
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        status = data.get("status", "").lower()
                        
                        if status == "completed":
                            print(f"    ✅ Generation completed!")
                            return data
                        elif status == "failed":
                            error = data.get("error", "Unknown error")
                            print(f"    ❌ Generation failed: {error}")
                            return None
                        else:
                            elapsed = int(time.time() - start_time)
                            print(f"    ⏳ Status: {status} ({elapsed}s)")
                    else:
                        response_text = await response.text()
                        print(f"    ⚠️ Poll error: {response.status} - {response_text}")
                
                await asyncio.sleep(poll_interval)
        
        print(f"    ⚠️ Timeout after {timeout}s")
        return None
    
    async def _download_pdf(self, export_url: str, output_path: str) -> bool:
        """Download the generated PDF."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(export_url) as response:
                    if response.status == 200:
                        content = await response.read()
                        with open(output_path, 'wb') as f:
                            f.write(content)
                        return True
                    else:
                        print(f"    ⚠️ Download error: {response.status}")
                        return False
        except Exception as e:
            print(f"    ⚠️ Download failed: {e}")
            return False
    
    async def generate_carousel(self, item: Dict) -> List["Image.Image"]:
        """
        Generate carousel using Gamma API.
        
        Note: Gamma generates PDF directly, so we return empty list
        and handle PDF separately in process_day.
        """
        if not self.api_key:
            raise ValueError(
                "GAMMA_API_KEY not set. "
                "Get your API key from gamma.app with a Pro subscription."
            )
        
        print(f"    🚀 Creating Gamma generation ({self.NUM_CARDS} slides)...")
        
        # Create generation
        generation_id = await self._create_generation(item)
        if not generation_id:
            raise RuntimeError("Failed to create Gamma generation")
        
        # Poll for completion
        result = await self._poll_generation(generation_id)
        if not result:
            raise RuntimeError("Gamma generation failed or timed out")
        
        # Store export URL for PDF download
        self._last_export_url = result.get("exportUrl")
        self._last_gamma_url = result.get("gammaUrl")
        
        if self._last_gamma_url:
            print(f"    🔗 View: {self._last_gamma_url}")
        
        # Return empty list since we'll handle PDF separately
        return []
    
    async def process_item(self, item: Dict, output_dir: str) -> Optional[str]:
        """
        Process a single item and download PDF.
        
        Overrides base class to handle Gamma's direct PDF export.
        """
        import re
        
        headline = item.get('headline', 'untitled')
        safe_name = re.sub(r'[^\w\s-]', '', headline.lower())
        safe_name = re.sub(r'[-\s]+', '_', safe_name).strip('_')[:50]
        
        try:
            # Generate via Gamma API
            await self.generate_carousel(item)
            
            # Download PDF if available
            if hasattr(self, '_last_export_url') and self._last_export_url:
                os.makedirs(output_dir, exist_ok=True)
                output_path = os.path.join(output_dir, f"{safe_name}.pdf")
                
                print(f"    📥 Downloading PDF...")
                if await self._download_pdf(self._last_export_url, output_path):
                    print(f"    ✅ Saved: {output_path}")
                    return output_path
                else:
                    print(f"    ⚠️ PDF download failed")
                    return None
            else:
                print(f"    ⚠️ No export URL available")
                return None
                
        except Exception as e:
            print(f"    ❌ Error: {e}")
            return None
    
    async def process_day(self, date_str: str):
        """Process all items for a given date."""
        import json
        
        curated_path = os.path.join(
            CarouselConfig.DATA_DIR, 
            "curated", 
            f"{date_str}.json"
        )
        
        if not os.path.exists(curated_path):
            print(f"No curated data for {date_str}")
            return
        
        with open(curated_path, 'r') as f:
            items = json.load(f)
        
        if not items:
            print(f"No items in {date_str}")
            return
        
        output_dir = os.path.join(
            CarouselConfig.DATA_DIR,
            "carousels",
            date_str,
            self.theme
        )
        
        print(f"Generating {len(items)} carousels [gamma:{self.theme}] for {date_str}...")
        
        for item in items:
            headline = item.get('headline', 'Unknown')
            print(f"\n  Processing: {headline[:50]}...")
            await self.process_item(item, output_dir)
