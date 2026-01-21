"""
Carousel Provider Configuration

Shared configuration for all carousel providers.
Extracted from generate_carousel.py to enable modular provider architecture.
"""

import os


class CarouselConfig:
    """Shared configuration for carousel generation."""
    
    # Environment
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    UNSPLASH_ACCESS_KEY = os.getenv("UNSPLASH_ACCESS_KEY")
    
    # Data paths
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
    
    # AI Image settings (for Pillow providers)
    DALLE_MODEL = "dall-e-3"
    IMAGE_SIZE = "1024x1024"
