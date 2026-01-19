"""
LinkedIn Carousel Generator
Generates PDF carousels from curated AI news items.

Structure: 5 slides
- Slide 1: Hook (headline)
- Slides 2-4: Content (1 bullet per slide)
- Slide 5: Hot Take + CTA
"""

import os
import json
import glob
import argparse
import textwrap
from datetime import datetime, timedelta, timezone as python_timezone
from typing import List, Dict, Tuple
from io import BytesIO

try:
    from PIL import Image, ImageDraw, ImageFont
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.utils import ImageReader
except ImportError:
    print("Required packages not installed. Run: pip install pillow reportlab")
    raise


class Config:
    DATA_DIR = "data"
    SLIDING_WINDOW_HOURS = 48
    
    # Carousel dimensions (portrait 4:5 ratio for LinkedIn)
    SLIDE_WIDTH = 1080
    SLIDE_HEIGHT = 1350
    
    # Colors (Dark Mode)
    BG_COLOR = "#0A0A0A"
    TEXT_COLOR = "#FFFFFF"
    ACCENT_COLOR = "#6366F1"  # Indigo
    SECONDARY_COLOR = "#10B981"  # Emerald
    MUTED_COLOR = "#9CA3AF"  # Gray
    
    # Typography
    PADDING = 80
    HEADLINE_SIZE = 56
    BODY_SIZE = 36
    SMALL_SIZE = 24


class CarouselGenerator:
    def __init__(self):
        self.width = Config.SLIDE_WIDTH
        self.height = Config.SLIDE_HEIGHT
        
        # Try to load fonts (fallback to default if not available)
        self.fonts = self._load_fonts()
    
    def _load_fonts(self) -> Dict[str, ImageFont.FreeTypeFont]:
        """Load fonts with fallback to default."""
        fonts = {}
        
        # Try common font paths
        font_paths = [
            "/System/Library/Fonts/Helvetica.ttc",  # macOS
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",  # Linux
            "C:\\Windows\\Fonts\\arial.ttf",  # Windows
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
                # Use PIL default font (basic but works)
                fonts['headline'] = ImageFont.load_default()
                fonts['body'] = ImageFont.load_default()
                fonts['small'] = ImageFont.load_default()
        except Exception as e:
            print(f"Font loading warning: {e}, using default")
            fonts['headline'] = ImageFont.load_default()
            fonts['body'] = ImageFont.load_default()
            fonts['small'] = ImageFont.load_default()
            
        return fonts
    
    def _hex_to_rgb(self, hex_color: str) -> Tuple[int, int, int]:
        """Convert hex color to RGB tuple."""
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    
    def _create_slide(self, slide_type: str, content: Dict) -> Image.Image:
        """Create a single slide image."""
        # Create base image
        bg_rgb = self._hex_to_rgb(Config.BG_COLOR)
        img = Image.new('RGB', (self.width, self.height), bg_rgb)
        draw = ImageDraw.Draw(img)
        
        text_rgb = self._hex_to_rgb(Config.TEXT_COLOR)
        accent_rgb = self._hex_to_rgb(Config.ACCENT_COLOR)
        muted_rgb = self._hex_to_rgb(Config.MUTED_COLOR)
        
        padding = Config.PADDING
        max_width = self.width - (2 * padding)
        
        if slide_type == "hook":
            # SLIDE 1: HOOK
            # Draw accent bar at top
            draw.rectangle([0, 0, self.width, 8], fill=accent_rgb)
            
            # Slide number
            draw.text((padding, padding + 20), "01", font=self.fonts['small'], fill=muted_rgb)
            
            # Main headline (centered vertically)
            headline = content.get('headline', 'AI News Update')
            wrapped = textwrap.wrap(headline, width=20)
            
            y_start = (self.height - len(wrapped) * 70) // 2
            for i, line in enumerate(wrapped[:4]):  # Max 4 lines
                draw.text((padding, y_start + i * 70), line, font=self.fonts['headline'], fill=text_rgb)
            
            # Swipe indicator at bottom
            draw.text((self.width // 2 - 50, self.height - padding - 30), "Swipe →", font=self.fonts['small'], fill=muted_rgb)
            
        elif slide_type == "content":
            # SLIDES 2-4: CONTENT
            slide_num = content.get('slide_num', 2)
            bullet = content.get('bullet', '')
            
            # Slide number
            draw.text((padding, padding + 20), f"0{slide_num}", font=self.fonts['small'], fill=accent_rgb)
            
            # Bullet point (centered)
            wrapped = textwrap.wrap(bullet, width=25)
            y_start = (self.height - len(wrapped) * 50) // 2
            
            for i, line in enumerate(wrapped[:5]):  # Max 5 lines
                draw.text((padding, y_start + i * 50), line, font=self.fonts['body'], fill=text_rgb)
            
            # Swipe indicator
            draw.text((self.width // 2 - 50, self.height - padding - 30), "Swipe →", font=self.fonts['small'], fill=muted_rgb)
            
        elif slide_type == "cta":
            # SLIDE 5: HOT TAKE + CTA
            hot_take = content.get('hot_take', '')
            
            # Draw accent bar at top
            draw.rectangle([0, 0, self.width, 8], fill=self._hex_to_rgb(Config.SECONDARY_COLOR))
            
            # Slide number
            draw.text((padding, padding + 20), "05", font=self.fonts['small'], fill=muted_rgb)
            
            # Hot Take label
            draw.text((padding, self.height // 3), "🔥 Hot Take", font=self.fonts['small'], fill=accent_rgb)
            
            # Hot take content
            wrapped = textwrap.wrap(hot_take, width=28)
            y_start = self.height // 3 + 50
            for i, line in enumerate(wrapped[:4]):
                draw.text((padding, y_start + i * 45), line, font=self.fonts['body'], fill=text_rgb)
            
            # CTA
            cta_y = self.height - padding - 100
            draw.text((padding, cta_y), "What do you think? 👇", font=self.fonts['body'], fill=accent_rgb)
            draw.text((padding, cta_y + 50), "Follow for more AI insights", font=self.fonts['small'], fill=muted_rgb)
        
        return img
    
    def generate_carousel(self, item: Dict) -> List[Image.Image]:
        """Generate all slides for a carousel from a curated item."""
        slides = []
        
        # Slide 1: Hook
        slides.append(self._create_slide("hook", {'headline': item.get('headline', 'AI News')}))
        
        # Slides 2-4: Content (bullets)
        bullets = item.get('bullets', [])
        for i, bullet in enumerate(bullets[:3]):  # Max 3 content slides
            slides.append(self._create_slide("content", {
                'slide_num': i + 2,
                'bullet': bullet
            }))
        
        # Pad with empty content slides if less than 3 bullets
        while len(slides) < 4:
            slides.append(self._create_slide("content", {
                'slide_num': len(slides) + 1,
                'bullet': 'Stay tuned for more updates...'
            }))
        
        # Slide 5: Hot Take + CTA
        slides.append(self._create_slide("cta", {
            'hot_take': item.get('hot_take', 'The AI landscape is evolving fast.')
        }))
        
        return slides
    
    def save_as_pdf(self, slides: List[Image.Image], output_path: str):
        """Combine slides into a single PDF."""
        if not slides:
            return
        
        # Convert slides to PDF
        first_slide = slides[0]
        pdf_buffer = BytesIO()
        
        # Save all slides as PDF
        first_slide.save(
            pdf_buffer,
            format='PDF',
            save_all=True,
            append_images=slides[1:],
            resolution=72.0
        )
        
        # Write to file
        with open(output_path, 'wb') as f:
            f.write(pdf_buffer.getvalue())
        
        print(f"  ✅ Saved: {output_path}")
    
    def process_day(self, date_str: str):
        """Generate carousels for all curated items on a given day."""
        curated_path = os.path.join(Config.DATA_DIR, "curated", f"{date_str}.json")
        
        if not os.path.exists(curated_path):
            print(f"No curated data for {date_str}")
            return
        
        with open(curated_path, 'r', encoding='utf-8') as f:
            items = json.load(f)
        
        # Filter to high-relevance items
        items = [i for i in items if i.get('relevance', 0) >= 70]
        
        if not items:
            print(f"No high-relevance items for {date_str}")
            return
        
        # Create output directory
        output_dir = os.path.join(Config.DATA_DIR, "carousels", date_str)
        os.makedirs(output_dir, exist_ok=True)
        
        print(f"Generating {len(items)} carousels for {date_str}...")
        
        for item in items:
            # Create safe filename
            headline = item.get('headline', 'untitled')
            safe_name = "".join([c for c in headline if c.isalnum() or c in (' ', '-', '_')]).strip()
            safe_name = safe_name.replace(" ", "_").lower()[:50]
            output_path = os.path.join(output_dir, f"{safe_name}.pdf")
            
            # Skip if already exists
            if os.path.exists(output_path):
                print(f"  Skipping existing: {safe_name}")
                continue
            
            # Generate slides
            slides = self.generate_carousel(item)
            
            # Save as PDF
            self.save_as_pdf(slides, output_path)


def get_recent_curated_files(hours: int = 48) -> List[str]:
    """Get curated files from the last N hours only."""
    curated_files = glob.glob(os.path.join(Config.DATA_DIR, "curated", "*.json"))
    
    if not curated_files:
        return []
    
    now = datetime.now(python_timezone.utc)
    cutoff = now - timedelta(hours=hours)
    cutoff_date_str = cutoff.strftime("%Y-%m-%d")
    
    recent_files = []
    for f in sorted(curated_files):
        date_str = os.path.splitext(os.path.basename(f))[0]
        if date_str >= cutoff_date_str:
            recent_files.append(f)
    
    return recent_files


def main():
    parser = argparse.ArgumentParser(description="Generate LinkedIn carousel PDFs from curated items")
    parser.add_argument("--date", help="Date to process (YYYY-MM-DD)")
    parser.add_argument("--all", action="store_true", help="Process all curated files")
    args = parser.parse_args()
    
    generator = CarouselGenerator()
    
    if args.date:
        generator.process_day(args.date)
    elif args.all:
        curated_files = glob.glob(os.path.join(Config.DATA_DIR, "curated", "*.json"))
        curated_files.sort()
        print(f"Processing ALL {len(curated_files)} curated days...")
        for f in curated_files:
            date_str = os.path.splitext(os.path.basename(f))[0]
            print(f"\n=== {date_str} ===")
            generator.process_day(date_str)
    else:
        # Default: sliding window
        recent_files = get_recent_curated_files(Config.SLIDING_WINDOW_HOURS)
        
        if not recent_files:
            print(f"No curated data in the last {Config.SLIDING_WINDOW_HOURS} hours.")
            return
        
        print(f"Processing {len(recent_files)} days (last {Config.SLIDING_WINDOW_HOURS} hours)...")
        for f in recent_files:
            date_str = os.path.splitext(os.path.basename(f))[0]
            print(f"\n=== {date_str} ===")
            generator.process_day(date_str)


if __name__ == "__main__":
    main()
