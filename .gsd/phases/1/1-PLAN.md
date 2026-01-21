---
phase: 1
plan: 1
wave: 1
---

# Plan 1.1: Create Provider Base Class and Registry

## Objective

Create the abstract base class that defines the provider interface and a registry system for dynamically loading providers. This establishes the contract that all carousel providers (Canva, Gamma, Pillow) must implement.

## Context

- .gsd/SPEC.md — Provider architecture requirements
- generate_carousel.py — Existing implementation to extract interface from
- data/curated/*.json — Input format providers must consume

## Tasks

<task type="auto">
  <name>Create providers package structure</name>
  <files>
    providers/__init__.py
    providers/base.py
  </files>
  <action>
    Create new `providers/` directory with:
    
    1. `providers/base.py`:
       - Abstract base class `CarouselProvider` with:
         - `name: str` — Provider identifier (e.g., "canva", "pillow_openai")
         - `async def generate_carousel(self, item: Dict) -> List[Image.Image]` — Core method
         - `def save_as_pdf(self, slides: List[Image.Image], output_path: str)` — PDF output
         - `async def process_day(self, date_str: str)` — Process a day's curated items
       - Common utilities: `_hex_to_rgb()`, `get_recent_curated_files()`
       - Shared config: slide dimensions, themes, data paths
    
    2. `providers/__init__.py`:
       - Provider registry dict: `PROVIDERS = {}`
       - `register_provider(name: str, cls: Type[CarouselProvider])` decorator
       - `get_provider(name: str) -> CarouselProvider` factory function
       - `list_providers() -> List[str]` utility
    
    DO NOT duplicate the slide rendering logic here — that stays in specific providers.
    DO NOT import specific providers yet — they'll self-register.
  </action>
  <verify>python -c "from providers.base import CarouselProvider; print('Base class imported')"</verify>
  <done>
    - `CarouselProvider` abstract class exists with required methods
    - Registry functions work without errors
    - No circular import issues
  </done>
</task>

<task type="auto">
  <name>Create shared configuration module</name>
  <files>
    providers/config.py
  </files>
  <action>
    Extract shared configuration from `generate_carousel.py` into `providers/config.py`:
    
    ```python
    import os
    
    class CarouselConfig:
        DATA_DIR = "data"
        SLIDING_WINDOW_HOURS = 48
        
        # Carousel dimensions (portrait 4:5 ratio for LinkedIn)
        SLIDE_WIDTH = 1080
        SLIDE_HEIGHT = 1350
        
        # Color Themes
        THEMES = {
            'dark': {...},
            'light': {...}
        }
        
        # Typography
        PADDING = 80
        HEADLINE_SIZE = 56
        BODY_SIZE = 36
        SMALL_SIZE = 24
    ```
    
    This config is shared by ALL providers.
  </action>
  <verify>python -c "from providers.config import CarouselConfig; print(f'Width: {CarouselConfig.SLIDE_WIDTH}')"</verify>
  <done>
    - Config module imports without errors
    - All constants from original Config class are present
  </done>
</task>

## Success Criteria

- [ ] `providers/` package structure created
- [ ] `CarouselProvider` abstract base class defined
- [ ] Provider registry system works
- [ ] Shared config module created
- [ ] All imports work without circular dependencies
