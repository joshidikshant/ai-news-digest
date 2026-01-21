---
phase: 1
plan: 2
wave: 2
---

# Plan 1.2: Refactor generate_carousel.py to Use Provider Pattern

## Objective

Refactor the existing `generate_carousel.py` to use the provider abstraction layer. The main script becomes a thin CLI wrapper that delegates to the selected provider.

## Context

- .gsd/SPEC.md — CLI requirements (`--provider` flag)
- generate_carousel.py — Current implementation (418 lines)
- providers/base.py — Base class from Plan 1.1
- providers/config.py — Shared config from Plan 1.1

## Tasks

<task type="auto">
  <name>Refactor main script to provider pattern</name>
  <files>
    generate_carousel.py
  </files>
  <action>
    Modify `generate_carousel.py` to:
    
    1. Import the provider registry:
       ```python
       from providers import get_provider, list_providers
       ```
    
    2. Add `--provider` CLI argument:
       ```python
       parser.add_argument(
           "--provider",
           choices=list_providers(),
           default=os.getenv("CAROUSEL_PROVIDER", "pillow_openai"),
           help="Carousel generation provider"
       )
       ```
    
    3. Replace direct `CarouselGenerator` usage with:
       ```python
       provider = get_provider(args.provider)
       provider.theme = theme
       await provider.process_day_async(date_str)
       ```
    
    4. Keep the existing `CarouselGenerator` class for now — it will be moved to `providers/pillow_openai.py` in Phase 2.
    
    5. Add fallback logic in main():
       ```python
       def get_provider_with_fallback(preferred: str, fallbacks: List[str]):
           for name in [preferred] + fallbacks:
               try:
                   return get_provider(name)
               except KeyError:
                   continue
           raise ValueError(f"No provider available")
       ```
    
    DO NOT remove the CarouselGenerator class yet.
    DO NOT change the output format or directory structure.
  </action>
  <verify>python generate_carousel.py --help | grep -q "provider"</verify>
  <done>
    - `--provider` flag appears in help output
    - Script runs without import errors
    - Existing functionality preserved
  </done>
</task>

<task type="auto">
  <name>Create legacy provider wrapper</name>
  <files>
    providers/pillow_legacy.py
  </files>
  <action>
    Create a temporary wrapper that imports the existing CarouselGenerator as a provider:
    
    ```python
    from providers.base import CarouselProvider, register_provider
    from generate_carousel import CarouselGenerator
    
    @register_provider("pillow_legacy")
    class PillowLegacyProvider(CarouselProvider):
        name = "pillow_legacy"
        
        def __init__(self, theme="dark", generate_images=True):
            self._generator = CarouselGenerator(theme, generate_images)
        
        async def generate_carousel(self, item):
            return await self._generator.generate_carousel_async(item)
        
        # ... delegate other methods
    ```
    
    This allows testing the provider pattern without rewriting all the Pillow code.
    
    Register in `providers/__init__.py`:
    ```python
    from providers.pillow_legacy import PillowLegacyProvider
    ```
  </action>
  <verify>python -c "from providers import get_provider; p = get_provider('pillow_legacy'); print(f'Got: {p.name}')"</verify>
  <done>
    - Legacy provider can be instantiated
    - Provider appears in registry
    - Generates same output as direct usage
  </done>
</task>

## Success Criteria

- [ ] `--provider` CLI flag works
- [ ] `CAROUSEL_PROVIDER` env var is respected
- [ ] Legacy provider passes smoke test
- [ ] Output format unchanged (data/carousels/{date}/{theme}/*.pdf)
