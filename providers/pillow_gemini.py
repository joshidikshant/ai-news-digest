"""
Pillow Gemini Provider

Carousel generation using Pillow for rendering and Google Gemini for AI-generated
background illustrations. Alternative to DALL-E with potentially different pricing.

Cost: Varies by Gemini API tier
Note: Gemini Imagen availability may vary by region/account
"""

import os
import textwrap
import hashlib
from typing import List, Dict, Optional, Tuple
from io import BytesIO

try:
    from PIL import Image, ImageDraw, ImageFont
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    Image = None

try:
    import google.generativeai as genai
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False
    genai = None

from providers.base import CarouselProvider
from providers.config import CarouselConfig
from providers import register_provider


@register_provider("pillow_gemini")
class PillowGeminiProvider(CarouselProvider):
    """
    Carousel provider using Google Gemini for AI-generated illustrations.
    
    Uses Gemini's image generation capabilities as an alternative to DALL-E.
    Falls back to solid color backgrounds if API unavailable.
    
    Requires: GEMINI_API_KEY environment variable
    """
    
    name = "pillow_gemini"
    
    def __init__(self, theme: str = "dark", generate_images: bool = True, **kwargs):
        super().__init__(theme=theme, **kwargs)
        self.generate_images = generate_images
        
        # Initialize Gemini client
        api_key = CarouselConfig.GEMINI_API_KEY
        self.gemini_available = False
        
        if api_key and generate_images and GENAI_AVAILABLE:
            try:
                genai.configure(api_key=api_key)
                self.gemini_available = True
            except Exception as e:
                print(f"Warning: Gemini setup failed: {e}")
        elif generate_images and not api_key:
            print("Warning: GEMINI_API_KEY not set, skipping AI illustrations")
        elif generate_images and not GENAI_AVAILABLE:
            print("Warning: google-generativeai not installed, skipping AI illustrations")
        
        # Load fonts
        self.fonts = self._load_fonts()
        
        # Image cache directory
        self.image_cache_dir = os.path.join(CarouselConfig.DATA_DIR, "image_cache", "gemini")
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
    
    def _get_image_cache_path(self, prompt: str) -> str:
        """Get cache path for an image based on prompt hash."""
        prompt_hash = hashlib.md5(prompt.encode()).hexdigest()[:12]
        return os.path.join(self.image_cache_dir, f"{prompt_hash}.png")
    
    async def _generate_illustration(self, headline: str, bullet: str = "") -> Optional["Image.Image"]:
        """Generate an AI illustration using Gemini."""
        if not self.gemini_available or not PIL_AVAILABLE:
            return None
        
        context = bullet if bullet else headline
        prompt = f"Abstract, minimal tech illustration representing: {context[:100]}. Style: modern, geometric, gradient colors, no text, suitable for LinkedIn carousel background. Clean and professional."
        
        # Check cache first
        cache_path = self._get_image_cache_path(prompt)
        if os.path.exists(cache_path):
            try:
                return Image.open(cache_path)
            except:
                pass
        
        try:
            # Use Gemini's image generation
            # Note: API may vary based on Gemini version and availability
            model = genai.GenerativeModel('gemini-pro-vision')
            
            # Gemini Imagen API (if available)
            # This is a placeholder - actual implementation depends on Gemini Imagen availability
            response = await model.generate_images_async(
                prompt=prompt,
                number_of_images=1,
            )
            
            if response.images:
                img_data = response.images[0].data
                img = Image.open(BytesIO(img_data))
                img.save(cache_path, 'PNG')
                return img
            
            return None
            
        except Exception as e:
            print(f"    ⚠️ Gemini error: {e}")
            return None
    
    def _create_slide(self, slide_type: str, content: Dict, bg_image: Optional["Image.Image"] = None) -> "Image.Image":
        """Create a single slide image."""
        if not PIL_AVAILABLE:
            raise RuntimeError("PIL not available")
            
        bg_rgb = self.hex_to_rgb(self.colors['bg'])
        img = Image.new('RGB', (self.width, self.height), bg_rgb)
        
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
        """Generate all slides for a carousel with Gemini illustrations."""
        if not PIL_AVAILABLE:
            raise RuntimeError("PIL not available - install with: pip install pillow")
            
        slides = []
        headline = item.get('headline', 'AI News')
        bullets = item.get('bullets', [])
        
        bg_images = [None] * 5
        if self.generate_images and self.gemini_available:
            print(f"    🎨 Generating Gemini illustrations...")
            
            bg_images[0] = await self._generate_illustration(headline)
            for i, bullet in enumerate(bullets[:3]):
                bg_images[i + 1] = await self._generate_illustration(headline, bullet)
            bg_images[4] = await self._generate_illustration(headline, item.get('hot_take', ''))
        
        slides.append(self._create_slide("hook", {'headline': headline}, bg_images[0]))
        
        for i, bullet in enumerate(bullets[:3]):
            slides.append(self._create_slide("content", {
                'slide_num': i + 2,
                'bullet': bullet
            }, bg_images[i + 1] if i + 1 < len(bg_images) else None))
        
        while len(slides) < 4:
            slides.append(self._create_slide("content", {
                'slide_num': len(slides) + 1,
                'bullet': 'Stay tuned for more updates...'
            }))
        
        slides.append(self._create_slide("cta", {
            'hot_take': item.get('hot_take', 'The AI landscape is evolving fast.')
        }, bg_images[4] if len(bg_images) > 4 else None))
        
        return slides
