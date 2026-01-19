"""
LinkedIn Carousel Generator
Generates PDF carousels from curated AI news items.

Features:
- 5-slide structure: Hook → 3 Content → CTA
- Dual themes: Dark mode + Light mode (for A/B testing)
- AI-generated illustrations via DALL-E
- 48-hour sliding window
"""

import os
import json
import glob
import argparse
import textwrap
import asyncio
from datetime import datetime, timedelta, timezone as python_timezone
from typing import List, Dict, Tuple, Optional
from io import BytesIO
import hashlib

try:
    from PIL import Image, ImageDraw, ImageFont
    from openai import AsyncOpenAI
except ImportError:
    print("Required packages not installed. Run: pip install pillow openai")
    raise


class Config:
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    DATA_DIR = "data"
    SLIDING_WINDOW_HOURS = 48
    
    # Carousel dimensions (portrait 4:5 ratio for LinkedIn)
    SLIDE_WIDTH = 1080
    SLIDE_HEIGHT = 1350
    
    # Color Themes
    THEMES = {
        'dark': {
            'bg': "#0A0A0A",
            'text': "#FFFFFF",
            'accent': "#6366F1",
            'secondary': "#10B981",
            'muted': "#9CA3AF"
        },
        'light': {
            'bg': "#FAFAFA",
            'text': "#1F2937",
            'accent': "#4F46E5",
            'secondary': "#059669",
            'muted': "#6B7280"
        }
    }
    
    # Typography
    PADDING = 80
    HEADLINE_SIZE = 56
    BODY_SIZE = 36
    SMALL_SIZE = 24
    
    # AI Image settings
    DALLE_MODEL = "dall-e-3"
    IMAGE_SIZE = "1024x1024"


class CarouselGenerator:
    def __init__(self, theme: str = "dark", generate_images: bool = True):
        self.width = Config.SLIDE_WIDTH
        self.height = Config.SLIDE_HEIGHT
        self.theme = theme
        self.colors = Config.THEMES.get(theme, Config.THEMES['dark'])
        self.generate_images = generate_images
        
        # Initialize OpenAI client for DALL-E
        if Config.OPENAI_API_KEY and generate_images:
            self.openai_client = AsyncOpenAI(api_key=Config.OPENAI_API_KEY)
        else:
            self.openai_client = None
            if generate_images:
                print("Warning: OPENAI_API_KEY not set, skipping AI illustrations")
        
        # Load fonts
        self.fonts = self._load_fonts()
        
        # Image cache directory
        self.image_cache_dir = os.path.join(Config.DATA_DIR, "image_cache")
        os.makedirs(self.image_cache_dir, exist_ok=True)
    
    def _load_fonts(self) -> Dict[str, ImageFont.FreeTypeFont]:
        """Load fonts with fallback to default."""
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
                fonts['headline'] = ImageFont.truetype(default_font, Config.HEADLINE_SIZE)
                fonts['body'] = ImageFont.truetype(default_font, Config.BODY_SIZE)
                fonts['small'] = ImageFont.truetype(default_font, Config.SMALL_SIZE)
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
    
    def _hex_to_rgb(self, hex_color: str) -> Tuple[int, int, int]:
        """Convert hex color to RGB tuple."""
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    
    def _get_image_cache_path(self, prompt: str) -> str:
        """Get cache path for an image based on prompt hash."""
        prompt_hash = hashlib.md5(prompt.encode()).hexdigest()[:12]
        return os.path.join(self.image_cache_dir, f"{prompt_hash}.png")
    
    async def _generate_illustration(self, headline: str, bullet: str = "") -> Optional[Image.Image]:
        """Generate an AI illustration using DALL-E."""
        if not self.openai_client:
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
                model=Config.DALLE_MODEL,
                prompt=prompt,
                size=Config.IMAGE_SIZE,
                quality="standard",
                n=1
            )
            
            image_url = response.data[0].url
            
            # Download the image
            import urllib.request
            with urllib.request.urlopen(image_url) as response:
                image_data = response.read()
            
            img = Image.open(BytesIO(image_data))
            
            # Cache the image
            img.save(cache_path, 'PNG')
            
            return img
            
        except Exception as e:
            print(f"    ⚠️ DALL-E error: {e}")
            return None
    
    def _create_slide(self, slide_type: str, content: Dict, bg_image: Optional[Image.Image] = None) -> Image.Image:
        """Create a single slide image."""
        bg_rgb = self._hex_to_rgb(self.colors['bg'])
        img = Image.new('RGB', (self.width, self.height), bg_rgb)
        
        # Add AI-generated background if available
        if bg_image:
            # Resize and position background
            bg_resized = bg_image.resize((self.width, self.height), Image.Resampling.LANCZOS)
            
            # Apply overlay to ensure text readability
            overlay = Image.new('RGBA', (self.width, self.height), (*bg_rgb, 180))
            img.paste(bg_resized, (0, 0))
            img = Image.alpha_composite(img.convert('RGBA'), overlay).convert('RGB')
        
        draw = ImageDraw.Draw(img)
        
        text_rgb = self._hex_to_rgb(self.colors['text'])
        accent_rgb = self._hex_to_rgb(self.colors['accent'])
        muted_rgb = self._hex_to_rgb(self.colors['muted'])
        secondary_rgb = self._hex_to_rgb(self.colors['secondary'])
        
        padding = Config.PADDING
        
        if slide_type == "hook":
            # SLIDE 1: HOOK
            draw.rectangle([0, 0, self.width, 8], fill=accent_rgb)
            draw.text((padding, padding + 20), "01", font=self.fonts['small'], fill=muted_rgb)
            
            headline = content.get('headline', 'AI News Update')
            wrapped = textwrap.wrap(headline, width=20)
            
            y_start = (self.height - len(wrapped) * 70) // 2
            for i, line in enumerate(wrapped[:4]):
                draw.text((padding, y_start + i * 70), line, font=self.fonts['headline'], fill=text_rgb)
            
            draw.text((self.width // 2 - 50, self.height - padding - 30), "Swipe →", font=self.fonts['small'], fill=muted_rgb)
            
        elif slide_type == "content":
            # SLIDES 2-4: CONTENT
            slide_num = content.get('slide_num', 2)
            bullet = content.get('bullet', '')
            
            draw.text((padding, padding + 20), f"0{slide_num}", font=self.fonts['small'], fill=accent_rgb)
            
            wrapped = textwrap.wrap(bullet, width=25)
            y_start = (self.height - len(wrapped) * 50) // 2
            
            for i, line in enumerate(wrapped[:5]):
                draw.text((padding, y_start + i * 50), line, font=self.fonts['body'], fill=text_rgb)
            
            draw.text((self.width // 2 - 50, self.height - padding - 30), "Swipe →", font=self.fonts['small'], fill=muted_rgb)
            
        elif slide_type == "cta":
            # SLIDE 5: HOT TAKE + CTA
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
    
    async def generate_carousel_async(self, item: Dict) -> List[Image.Image]:
        """Generate all slides for a carousel with AI illustrations."""
        slides = []
        headline = item.get('headline', 'AI News')
        bullets = item.get('bullets', [])
        
        # Generate AI illustrations for each slide (parallel)
        bg_images = [None] * 5
        if self.generate_images and self.openai_client:
            print(f"    🎨 Generating AI illustrations...")
            
            # Create prompts for each slide
            tasks = []
            # Hook slide uses headline
            tasks.append(self._generate_illustration(headline))
            # Content slides use bullets
            for bullet in bullets[:3]:
                tasks.append(self._generate_illustration(headline, bullet))
            # CTA slide uses hot_take
            tasks.append(self._generate_illustration(headline, item.get('hot_take', '')))
            
            # Gather all results
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
    
    def save_as_pdf(self, slides: List[Image.Image], output_path: str):
        """Combine slides into a single PDF."""
        if not slides:
            return
        
        first_slide = slides[0]
        pdf_buffer = BytesIO()
        
        first_slide.save(
            pdf_buffer,
            format='PDF',
            save_all=True,
            append_images=slides[1:],
            resolution=72.0
        )
        
        with open(output_path, 'wb') as f:
            f.write(pdf_buffer.getvalue())
        
        print(f"  ✅ Saved: {os.path.basename(output_path)}")
    
    async def process_day_async(self, date_str: str):
        """Generate carousels for all curated items on a given day."""
        curated_path = os.path.join(Config.DATA_DIR, "curated", f"{date_str}.json")
        
        if not os.path.exists(curated_path):
            print(f"No curated data for {date_str}")
            return
        
        with open(curated_path, 'r', encoding='utf-8') as f:
            items = json.load(f)
        
        items = [i for i in items if i.get('relevance', 0) >= 70]
        
        if not items:
            print(f"No high-relevance items for {date_str}")
            return
        
        # Create output directory with theme suffix
        output_dir = os.path.join(Config.DATA_DIR, "carousels", date_str, self.theme)
        os.makedirs(output_dir, exist_ok=True)
        
        print(f"Generating {len(items)} carousels [{self.theme} theme] for {date_str}...")
        
        for item in items:
            headline = item.get('headline', 'untitled')
            safe_name = "".join([c for c in headline if c.isalnum() or c in (' ', '-', '_')]).strip()
            safe_name = safe_name.replace(" ", "_").lower()[:50]
            output_path = os.path.join(output_dir, f"{safe_name}.pdf")
            
            if os.path.exists(output_path):
                print(f"  Skipping existing: {safe_name}")
                continue
            
            print(f"  Processing: {headline[:40]}...")
            slides = await self.generate_carousel_async(item)
            self.save_as_pdf(slides, output_path)


def get_recent_curated_files(hours: int = 48) -> List[str]:
    """Get curated files from the last N hours only."""
    curated_files = glob.glob(os.path.join(Config.DATA_DIR, "curated", "*.json"))
    
    if not curated_files:
        return []
    
    now = datetime.now(python_timezone.utc)
    cutoff = now - timedelta(hours=hours)
    cutoff_date_str = cutoff.strftime("%Y-%m-%d")
    
    return [f for f in sorted(curated_files) if os.path.splitext(os.path.basename(f))[0] >= cutoff_date_str]


async def main():
    parser = argparse.ArgumentParser(description="Generate LinkedIn carousel PDFs")
    parser.add_argument("--date", help="Date to process (YYYY-MM-DD)")
    parser.add_argument("--all", action="store_true", help="Process all curated files")
    parser.add_argument("--theme", choices=["dark", "light", "both"], default="both", help="Color theme")
    parser.add_argument("--no-images", action="store_true", help="Skip AI illustration generation")
    args = parser.parse_args()
    
    themes = ["dark", "light"] if args.theme == "both" else [args.theme]
    generate_images = not args.no_images
    
    for theme in themes:
        print(f"\n{'='*50}")
        print(f"Theme: {theme.upper()}")
        print(f"{'='*50}")
        
        generator = CarouselGenerator(theme=theme, generate_images=generate_images)
        
        if args.date:
            await generator.process_day_async(args.date)
        elif args.all:
            curated_files = glob.glob(os.path.join(Config.DATA_DIR, "curated", "*.json"))
            curated_files.sort()
            print(f"Processing ALL {len(curated_files)} curated days...")
            for f in curated_files:
                date_str = os.path.splitext(os.path.basename(f))[0]
                print(f"\n=== {date_str} ===")
                await generator.process_day_async(date_str)
        else:
            recent_files = get_recent_curated_files(Config.SLIDING_WINDOW_HOURS)
            
            if not recent_files:
                print(f"No curated data in the last {Config.SLIDING_WINDOW_HOURS} hours.")
                continue
            
            print(f"Processing {len(recent_files)} days...")
            for f in recent_files:
                date_str = os.path.splitext(os.path.basename(f))[0]
                print(f"\n=== {date_str} ===")
                await generator.process_day_async(date_str)


if __name__ == "__main__":
    asyncio.run(main())
