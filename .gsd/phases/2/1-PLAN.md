---
phase: 2
plan: 1
wave: 1
---

# Plan 2.1: Pillow OpenAI Provider (Extract from Legacy)

## Objective

Extract the DALL-E image generation logic from `generate_carousel.py` into a proper provider class. This becomes the reference implementation for other Pillow providers.

## Context

- providers/base.py — Base class to inherit from
- providers/pillow_legacy.py — Wrapper we're replacing
- generate_carousel.py — Source code to extract (CarouselGenerator class)
- providers/config.py — Shared configuration

## Tasks

<task type="auto">
  <name>Create pillow_openai provider</name>
  <files>
    providers/pillow_openai.py
  </files>
  <action>
    Extract and refactor the CarouselGenerator class into `providers/pillow_openai.py`:
    
    1. Create `PillowOpenAIProvider` class extending `CarouselProvider`
    2. Move these methods from CarouselGenerator:
       - `_load_fonts()` → Keep as instance method
       - `_generate_illustration()` → DALL-E specific
       - `_create_slide()` → Slide rendering
       - `generate_carousel_async()` → Renamed to `generate_carousel()`
       - `_get_image_cache_path()` → Image caching
    
    3. Use `CarouselConfig` from `providers/config.py` instead of local `Config` class
    
    4. Register with decorator:
       ```python
       @register_provider("pillow_openai")
       class PillowOpenAIProvider(CarouselProvider):
           name = "pillow_openai"
       ```
    
    5. Key differences from legacy:
       - Inherits from `CarouselProvider` (not standalone)
       - Uses shared config
       - Implements required abstract methods
    
    DO NOT modify generate_carousel.py - it stays as fallback
    DO NOT remove CarouselGenerator from generate_carousel.py
  </action>
  <verify>python3 -c "from providers import get_provider; p = get_provider('pillow_openai'); print(f'✅ {p.name}')"</verify>
  <done>
    - Provider registered as 'pillow_openai'
    - Has generate_carousel() method
    - DALL-E integration preserved
  </done>
</task>

<task type="auto">
  <name>Register provider in __init__.py</name>
  <files>
    providers/__init__.py
  </files>
  <action>
    Add import for pillow_openai provider:
    
    ```python
    try:
        from providers import pillow_openai
    except ImportError as e:
        print(f"Warning: pillow_openai not available: {e}")
    ```
  </action>
  <verify>python3 -c "from providers import list_providers; print(list_providers())"</verify>
  <done>
    - 'pillow_openai' appears in list_providers()
  </done>
</task>

## Success Criteria

- [ ] `pillow_openai` provider registered
- [ ] Provider can be instantiated with theme parameter
- [ ] DALL-E image generation preserved (requires API key to fully test)
