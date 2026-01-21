"""
Pillow Unsplash Provider

Carousel generation using Pillow for rendering and Unsplash for free stock images.
This is the zero-cost fallback provider that works without any API keys.

Cost: FREE (uses Unsplash Source API)
"""

import os
import textwrap
import hashlib
import urllib.request
import urllib.parse
from typing import List, Dict, Optional, Tuple
from io import BytesIO

try:
    from PIL import Image, ImageDraw, ImageFont
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    Image = None

from providers.base import CarouselProvider
from providers.config import CarouselConfig
from providers import register_provider


@register_provider("pillow_unsplash")
class PillowUnsplashProvider(CarouselProvider):
    """
    Free carousel provider using Unsplash for stock images.
    
    Uses the Unsplash Source API which requires no authentication.
    Images are selected based on keywords extracted from the content.
    
    Requires: Nothing! Works out of the box.
    """
    
    name = "pillow_unsplash"
    
    # Keywords to use for tech-related image searches
    TECH_KEYWORDS = ["technology", "ai", "data", "network", "digital", "abstract"]
    
    def __init__(self, theme: str = "dark", generate_images: bool = True, **kwargs):
        super().__init__(theme=theme, **kwargs)
        self.generate_images = generate_images
        
        # Load fonts
        self.fonts = self._load_fonts()
        
        # Image cache directory
        self.image_cache_dir = os.path.join(CarouselConfig.DATA_DIR, "image_cache", "unsplash")
        os.makedirs(self.image_cache_dir, exist_ok=True)
    
    def _load_fonts(self) -> Dict[str, "ImageFont.FreeTypeFont"]:
        """Load fonts with fallback to default."""
        if not PIL_AVAILABLE:
            return {}
            
        fonts = {}
        
        font_paths = [
            "/System/Library/Fonts/Helvetica.ttc",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "C:\\Windows\\Fonts\\arial.ttf",
        ]
        
        default_font = None
        for path in font_paths:
            if os.path.exists(path):
                default_font = path
                break
        
        try:
            if default_font:
                fonts['headline'] = ImageFont.truetype(default_font, CarouselConfig.HEADLINE_SIZE)
                fonts['body'] = ImageFont.truetype(default_font, CarouselConfig.BODY_SIZE)
                fonts['small'] = ImageFont.truetype(default_font, CarouselConfig.SMALL_SIZE)
            else:
                fonts['headline'] = ImageFont.load_default()
                fonts['body'] = ImageFont.load_default()
                fonts['small'] = ImageFont.load_default()
        except Exception as e:
            print(f"Font loading warning: {e}")
            fonts['headline'] = ImageFont.load_default()
            fonts['body'] = ImageFont.load_default()
            fonts['small'] = ImageFont.load_default()
            
        return fonts
    
    def _extract_keywords(self, text: str) -> str:
        """Extract relevant keywords from text for image search."""
        # Simple keyword extraction - could be enhanced with NLP
        text_lower = text.lower()
        
        # Common AI/tech terms to search for
        tech_terms = [
            "ai", "artificial intelligence", "machine learning", "neural", 
            "robot", "automation", "data", "cloud", "network", "cyber",
            "algorithm", "code", "software", "hardware", "chip", "computer"
        ]
        
        found_terms = [term for term in tech_terms if term in text_lower]
        
        if found_terms:
            return ",".join(found_terms[:2] + ["technology"])
        
        # Default to general tech keywords
        return "technology,abstract,digital"
    
    def _get_image_cache_path(self, query: str) -> str:
        """Get cache path for an image based on query hash."""
        query_hash = hashlib.md5(query.encode()).hexdigest()[:12]
        return os.path.join(self.image_cache_dir, f"{query_hash}.png")
    
    async def _fetch_unsplash_image(self, headline: str, bullet: str = "") -> Optional["Image.Image"]:
        """Fetch a stock image from Unsplash Source API."""
        if not PIL_AVAILABLE:
            return None
        
        context = bullet if bullet else headline
        keywords = self._extract_keywords(context)
        
        # Check cache first
        cache_path = self._get_image_cache_path(keywords)
        if os.path.exists(cache_path):
            try:
                return Image.open(cache_path)
            except:
                pass
        
        try:
            # Unsplash Source API - no auth required
            url = f"https://source.unsplash.com/1024x1024/?{urllib.parse.quote(keywords)}"
            
            request = urllib.request.Request(url)
            request.add_header('User-Agent', 'AI-News-Digest/1.0')
            
            with urllib.request.urlopen(request, timeout=10) as response:
                image_data = response.read()
            
            img = Image.open(BytesIO(image_data))
            
            # Cache the image
            img.save(cache_path, 'PNG')
            
            return img
            
        except Exception as e:
            print(f"    ⚠️ Unsplash error: {e}")
            return None
    
    def _create_slide(self, slide_type: str, content: Dict, bg_image: Optional["Image.Image"] = None) -> "Image.Image":
        """Create a single slide image."""
        if not PIL_AVAILABLE:
            raise RuntimeError("PIL not available")
            
        bg_rgb = self.hex_to_rgb(self.colors['bg'])
        img = Image.new('RGB', (self.width, self.height), bg_rgb)
        
        # Add background image if available
        if bg_image:
            bg_resized = bg_image.resize((self.width, self.height), Image.Resampling.LANCZOS)
            overlay = Image.new('RGBA', (self.width, self.height), (*bg_rgb, 180))
            img.paste(bg_resized, (0, 0))
            img = Image.alpha_composite(img.convert('RGBA'), overlay).convert('RGB')
        
        draw = ImageDraw.Draw(img)
        
        text_rgb = self.hex_to_rgb(self.colors['text'])
        accent_rgb = self.hex_to_rgb(self.colors['accent'])
        muted_rgb = self.hex_to_rgb(self.colors['muted'])
        secondary_rgb = self.hex_to_rgb(self.colors['secondary'])
        
        padding = CarouselConfig.PADDING
        
        if slide_type == "hook":
            draw.rectangle([0, 0, self.width, 8], fill=accent_rgb)
            draw.text((padding, padding + 20), "01", font=self.fonts['small'], fill=muted_rgb)
            
            headline = content.get('headline', 'AI News Update')
            wrapped = textwrap.wrap(headline, width=20)
            
            y_start = (self.height - len(wrapped) * 70) // 2
            for i, line in enumerate(wrapped[:4]):
                draw.text((padding, y_start + i * 70), line, font=self.fonts['headline'], fill=text_rgb)
            
            draw.text((self.width // 2 - 50, self.height - padding - 30), "Swipe →", font=self.fonts['small'], fill=muted_rgb)
            
        elif slide_type == "content":
            slide_num = content.get('slide_num', 2)
            bullet = content.get('bullet', '')
            
            draw.text((padding, padding + 20), f"0{slide_num}", font=self.fonts['small'], fill=accent_rgb)
            
            wrapped = textwrap.wrap(bullet, width=25)
            y_start = (self.height - len(wrapped) * 50) // 2
            
            for i, line in enumerate(wrapped[:5]):
                draw.text((padding, y_start + i * 50), line, font=self.fonts['body'], fill=text_rgb)
            
            draw.text((self.width // 2 - 50, self.height - padding - 30), "Swipe →", font=self.fonts['small'], fill=muted_rgb)
            
        elif slide_type == "cta":
            hot_take = content.get('hot_take', '')
            
            draw.rectangle([0, 0, self.width, 8], fill=secondary_rgb)
            draw.text((padding, padding + 20), "05", font=self.fonts['small'], fill=muted_rgb)
            draw.text((padding, self.height // 3), "🔥 Hot Take", font=self.fonts['small'], fill=accent_rgb)
            
            wrapped = textwrap.wrap(hot_take, width=28)
            y_start = self.height // 3 + 50
            for i, line in enumerate(wrapped[:4]):
                draw.text((padding, y_start + i * 45), line, font=self.fonts['body'], fill=text_rgb)
            
            cta_y = self.height - padding - 100
            draw.text((padding, cta_y), "What do you think? 👇", font=self.fonts['body'], fill=accent_rgb)
            draw.text((padding, cta_y + 50), "Follow for more AI insights", font=self.fonts['small'], fill=muted_rgb)
        
        return img
    
    async def generate_carousel(self, item: Dict) -> List["Image.Image"]:
        """Generate all slides for a carousel with Unsplash images."""
        if not PIL_AVAILABLE:
            raise RuntimeError("PIL not available - install with: pip install pillow")
            
        slides = []
        headline = item.get('headline', 'AI News')
        bullets = item.get('bullets', [])
        
        # Fetch images for each slide
        bg_images = [None] * 5
        if self.generate_images:
            print(f"    🖼️ Fetching Unsplash images...")
            
            # Fetch images sequentially to avoid rate limiting
            bg_images[0] = await self._fetch_unsplash_image(headline)
            for i, bullet in enumerate(bullets[:3]):
                bg_images[i + 1] = await self._fetch_unsplash_image(headline, bullet)
            bg_images[4] = await self._fetch_unsplash_image(headline, item.get('hot_take', ''))
        
        # Slide 1: Hook
        slides.append(self._create_slide("hook", {'headline': headline}, bg_images[0]))
        
        # Slides 2-4: Content
        for i, bullet in enumerate(bullets[:3]):
            slides.append(self._create_slide("content", {
                'slide_num': i + 2,
                'bullet': bullet
            }, bg_images[i + 1] if i + 1 < len(bg_images) else None))
        
        # Pad with empty slides if needed
        while len(slides) < 4:
            slides.append(self._create_slide("content", {
                'slide_num': len(slides) + 1,
                'bullet': 'Stay tuned for more updates...'
            }))
        
        # Slide 5: CTA
        slides.append(self._create_slide("cta", {
            'hot_take': item.get('hot_take', 'The AI landscape is evolving fast.')
        }, bg_images[4] if len(bg_images) > 4 else None))
        
        return slides
