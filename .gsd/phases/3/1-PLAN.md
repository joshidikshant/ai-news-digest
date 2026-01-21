---
phase: 3
plan: 1
wave: 1
---

# Plan 3.1: Gamma API Provider

## Objective

Create a Gamma API provider for professional carousel generation with built-in AI images. This is the recommended provider for daily automation at $15/month.

## Context

- providers/base.py — Base class to inherit from
- providers/pillow_openai.py — Reference for provider structure
- Gamma API: https://gamma.app (Pro plan required for API)

## Research Notes

Gamma API features:
- Direct content → carousel generation
- Multiple AI image quality tiers (Unsplash free → Premium AI)
- PNG export for LinkedIn
- Credit-based pricing (~20-120 credits per carousel)
- Pro plan: ~4,000 credits/month = 133-200 carousels

## Tasks

<task type="auto">
  <name>Create gamma provider</name>
  <files>
    providers/gamma.py
  </files>
  <action>
    Create `GammaProvider` with API-based carousel generation:
    
    1. Provider class structure:
       ```python
       @register_provider("gamma")
       class GammaProvider(CarouselProvider):
           name = "gamma"
           
           # AI image quality tiers
           IMAGE_QUALITY = {
               'none': 0,      # Unsplash only (free)
               'basic': 10,    # Basic AI
               'advanced': 20, # Advanced AI
               'premium': 40   # Premium AI (best)
           }
           
           def __init__(self, theme="dark", image_quality="basic", **kwargs):
               super().__init__(theme=theme, **kwargs)
               self.api_key = os.getenv("GAMMA_API_KEY")
               self.image_quality = image_quality
       ```
    
    2. Key methods:
       - `async def _create_presentation(self, item: Dict) -> str` — Create via API
       - `async def _export_slides(self, presentation_id: str) -> List[Image.Image]` — Export PNGs
       - `async def generate_carousel(self, item: Dict)` — Main entry point
    
    3. API flow:
       a. POST /presentations with content
       b. Poll for completion
       c. GET /presentations/{id}/export?format=png
       d. Convert to PIL Images
    
    4. Graceful degradation:
       - If GAMMA_API_KEY not set, raise clear error
       - Log API responses for debugging
    
    NOTE: Gamma API v0.3+ required (v0.2 deprecated Jan 2026)
  </action>
  <verify>python3 -c "from providers import get_provider; p = get_provider('gamma'); print(f'✅ {p.name}')"</verify>
  <done>
    - Provider registered as 'gamma'
    - API integration structure ready
    - Image quality tiers configurable
  </done>
</task>

<task type="auto">
  <name>Register provider in __init__.py</name>
  <files>
    providers/__init__.py
  </files>
  <action>
    Add import for gamma provider:
    
    ```python
    try:
        from providers import gamma
    except ImportError as e:
        pass  # Silently skip if not available
    ```
  </action>
  <verify>python3 -c "from providers import list_providers; print('gamma' in list_providers())"</verify>
  <done>
    - 'gamma' appears in list_providers()
  </done>
</task>

## Success Criteria

- [ ] `gamma` provider registered
- [ ] Provider configurable with image quality tiers
- [ ] Clear error when GAMMA_API_KEY missing
- [ ] Ready for API integration when user has Pro subscription

## Cost Analysis

| Quality | Credits/Carousel | Monthly Capacity (4000 credits) |
|---------|-----------------|--------------------------------|
| none (Unsplash) | ~20 | ~200 carousels |
| basic | ~30 | ~133 carousels |
| advanced | ~60 | ~66 carousels |
| premium | ~120 | ~33 carousels |
