"""
Carousel Provider Base Class

Abstract base class that defines the interface all carousel providers must implement.
Providers handle carousel generation using different backends (Canva, Gamma, Pillow+AI).
"""

import os
import json
import glob
from abc import ABC, abstractmethod
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Optional, Tuple
from io import BytesIO

try:
    from PIL import Image
except ImportError:
    Image = None  # Pillow optional for non-Pillow providers

from providers.config import CarouselConfig


class CarouselProvider(ABC):
    """
    Abstract base class for carousel generation providers.
    
    Each provider implements its own way of generating carousel slides:
    - Canva MCP: Uses Canva's design API
    - Gamma API: Uses Gamma.app's presentation API
    - Pillow: Local generation with various image sources (DALL-E, Gemini, Unsplash)
    """
    
    # Provider identifier - subclasses must override
    name: str = "base"
    
    def __init__(self, theme: str = "dark", **kwargs):
        """
        Initialize the provider.
        
        Args:
            theme: Color theme ('dark' or 'light')
            **kwargs: Provider-specific configuration
        """
        self.theme = theme
        self.colors = CarouselConfig.THEMES.get(theme, CarouselConfig.THEMES['dark'])
        self.width = CarouselConfig.SLIDE_WIDTH
        self.height = CarouselConfig.SLIDE_HEIGHT
    
    @abstractmethod
    async def generate_carousel(self, item: Dict) -> List["Image.Image"]:
        """
        Generate carousel slides for a curated item.
        
        Args:
            item: Curated news item with keys:
                - headline: str
                - bullets: List[str]
                - hot_take: str
                - relevance: int
                
        Returns:
            List of PIL Image objects (5 slides: Hook → 3 Content → CTA)
        """
        pass
    
    def save_as_pdf(self, slides: List["Image.Image"], output_path: str) -> None:
        """
        Combine slides into a single PDF file.
        
        Args:
            slides: List of PIL Image objects
            output_path: Path to save the PDF
        """
        if not slides or Image is None:
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
    
    async def process_day(self, date_str: str) -> None:
        """
        Generate carousels for all curated items on a given day.
        
        Args:
            date_str: Date in YYYY-MM-DD format
        """
        curated_path = os.path.join(CarouselConfig.DATA_DIR, "curated", f"{date_str}.json")
        
        if not os.path.exists(curated_path):
            print(f"No curated data for {date_str}")
            return
        
        with open(curated_path, 'r', encoding='utf-8') as f:
            items = json.load(f)
        
        # Filter to high-relevance items only
        items = [i for i in items if i.get('relevance', 0) >= 70]
        
        if not items:
            print(f"No high-relevance items for {date_str}")
            return
        
        # Create output directory with theme suffix
        output_dir = os.path.join(
            CarouselConfig.DATA_DIR, 
            "carousels", 
            date_str, 
            self.theme
        )
        os.makedirs(output_dir, exist_ok=True)
        
        print(f"Generating {len(items)} carousels [{self.name}:{self.theme}] for {date_str}...")
        
        for item in items:
            headline = item.get('headline', 'untitled')
            safe_name = "".join([c for c in headline if c.isalnum() or c in (' ', '-', '_')]).strip()
            safe_name = safe_name.replace(" ", "_").lower()[:50]
            output_path = os.path.join(output_dir, f"{safe_name}.pdf")
            
            if os.path.exists(output_path):
                print(f"  Skipping existing: {safe_name}")
                continue
            
            print(f"  Processing: {headline[:40]}...")
            slides = await self.generate_carousel(item)
            self.save_as_pdf(slides, output_path)
    
    # ==================== Utility Methods ====================
    
    @staticmethod
    def hex_to_rgb(hex_color: str) -> Tuple[int, int, int]:
        """Convert hex color to RGB tuple."""
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    
    @staticmethod
    def get_recent_curated_files(hours: int = None) -> List[str]:
        """
        Get curated files from the last N hours.
        
        Args:
            hours: Number of hours to look back (default: config value)
            
        Returns:
            List of file paths for recent curated data
        """
        if hours is None:
            hours = CarouselConfig.SLIDING_WINDOW_HOURS
            
        curated_files = glob.glob(
            os.path.join(CarouselConfig.DATA_DIR, "curated", "*.json")
        )
        
        if not curated_files:
            return []
        
        now = datetime.now(timezone.utc)
        cutoff = now - timedelta(hours=hours)
        cutoff_date_str = cutoff.strftime("%Y-%m-%d")
        
        return [
            f for f in sorted(curated_files) 
            if os.path.splitext(os.path.basename(f))[0] >= cutoff_date_str
        ]
