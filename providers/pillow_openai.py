"""
Pillow OpenAI Provider

Carousel generation using Pillow for rendering and OpenAI DALL-E for AI-generated
background illustrations. This is the premium provider with the highest quality output.

Cost: ~$0.04 per image ($0.20 per 5-slide carousel)
"""

import os
import textwrap
import hashlib
import asyncio
from typing import List, Dict, Optional, Tuple
from io import BytesIO

try:
    from PIL import Image, ImageDraw, ImageFont
    from openai import AsyncOpenAI
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    Image = None

from providers.base import CarouselProvider
from providers.config import CarouselConfig
from providers import register_provider


@register_provider("pillow_openai")
class PillowOpenAIProvider(CarouselProvider):
    """
    Premium carousel provider using DALL-E for AI-generated illustrations.
    
    Generates beautiful, unique backgrounds for each slide using OpenAI's
    DALL-E 3 model. Results are cached to avoid redundant API calls.
    
    Requires: OPENAI_API_KEY environment variable
    """
    
    name = "pillow_openai"
    
    def __init__(self, theme: str = "dark", generate_images: bool = True, **kwargs):
        super().__init__(theme=theme, **kwargs)
        self.generate_images = generate_images
        
        # Initialize OpenAI client for DALL-E
        api_key = CarouselConfig.OPENAI_API_KEY
        if api_key and generate_images:
            self.openai_client = AsyncOpenAI(api_key=api_key)
        else:
            self.openai_client = None
            if generate_images:
                print("Warning: OPENAI_API_KEY not set, skipping AI illustrations")
        
        # Load fonts
        self.fonts = self._load_fonts()
        
        # Image cache directory
        self.image_cache_dir = os.path.join(CarouselConfig.DATA_DIR, "image_cache")
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
        """Generate an AI illustration using DALL-E."""
        if not self.openai_client or not PIL_AVAILABLE:
            return None
        
        # Create a prompt for the illustration
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
            response = await self.openai_client.images.generate(
                model=CarouselConfig.DALLE_MODEL,
                prompt=prompt,
                size=CarouselConfig.IMAGE_SIZE,
                quality="standard",
                n=1
            )
            
            image_url = response.data[0].url
            
            # Download the image
            import urllib.request
            with urllib.request.urlopen(image_url) as resp:
                image_data = resp.read()
            
            img = Image.open(BytesIO(image_data))
            
            # Cache the image
            img.save(cache_path, 'PNG')
            
            return img
            
        except Exception as e:
            print(f"    ⚠️ DALL-E error: {e}")
            return None
    
    def _create_slide(self, slide_type: str, content: Dict, bg_image: Optional["Image.Image"] = None) -> "Image.Image":
        """Create a single slide image."""
        if not PIL_AVAILABLE:
            raise RuntimeError("PIL not available")
            
        bg_rgb = self.hex_to_rgb(self.colors['bg'])
        img = Image.new('RGB', (self.width, self.height), bg_rgb)
        
        # Add AI-generated background if available
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
        """Generate all slides for a carousel with AI illustrations."""
        if not PIL_AVAILABLE:
            raise RuntimeError("PIL not available - install with: pip install pillow")
            
        slides = []
        headline = item.get('headline', 'AI News')
        bullets = item.get('bullets', [])
        
        # Generate AI illustrations for each slide (parallel)
        bg_images = [None] * 5
        if self.generate_images and self.openai_client:
            print(f"    🎨 Generating AI illustrations...")
            
            tasks = []
            tasks.append(self._generate_illustration(headline))
            for bullet in bullets[:3]:
                tasks.append(self._generate_illustration(headline, bullet))
            tasks.append(self._generate_illustration(headline, item.get('hot_take', '')))
            
            bg_images = await asyncio.gather(*tasks, return_exceptions=True)
            bg_images = [img if isinstance(img, Image.Image) else None for img in bg_images]
        
        # Slide 1: Hook
        slides.append(self._create_slide("hook", {'headline': headline}, bg_images[0] if len(bg_images) > 0 else None))
        
        # Slides 2-4: Content
        for i, bullet in enumerate(bullets[:3]):
            bg_idx = i + 1
            slides.append(self._create_slide("content", {
                'slide_num': i + 2,
                'bullet': bullet
            }, bg_images[bg_idx] if len(bg_images) > bg_idx else None))
        
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
