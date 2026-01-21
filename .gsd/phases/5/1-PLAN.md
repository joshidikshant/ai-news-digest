---
phase: 5
plan: 1
wave: 1
---

# Plan 5.1: Finalize CLI Provider Selection

## Objective

Finalize the `--provider` CLI argument and add fallback chain support for robust carousel generation.

## Context

- generate_carousel.py — Main script with basic `--provider` flag
- providers/__init__.py — Has `get_provider_with_fallback()` stub
- Current providers: pillow_legacy, pillow_openai, pillow_unsplash, pillow_gemini, gamma

## Tasks

<task type="auto">
  <name>Enhance CLI with fallback support</name>
  <files>
    generate_carousel.py
  </files>
  <action>
    Update CLI to support fallback chains and better provider selection:
    
    1. Add `--fallback` argument for fallback provider
    2. Add `--list-providers` flag to show available providers
    3. Add `--image-quality` flag for Gamma tier (none/basic/advanced/premium)
    4. Improve error messages with setup instructions
    
    CLI examples:
    ```bash
    # Use gamma with pillow_unsplash fallback
    python generate_carousel.py --provider gamma --fallback pillow_unsplash
    
    # List available providers
    python generate_carousel.py --list-providers
    
    # Free mode (auto-selects pillow_unsplash)
    python generate_carousel.py --provider pillow_unsplash
    
    # Gamma with specific quality
    python generate_carousel.py --provider gamma --image-quality premium
    ```
  </action>
  <verify>python3 generate_carousel.py --list-providers</verify>
  <done>
    - --provider flag working
    - --fallback flag for fallback chains
    - --list-providers shows all registered providers
    - --image-quality for Gamma tiers
  </done>
</task>

<task type="auto">
  <name>Implement get_provider_with_fallback</name>
  <files>
    providers/__init__.py
  </files>
  <action>
    Complete the fallback chain implementation:
    
    ```python
    def get_provider_with_fallback(*provider_names: str, **kwargs) -> CarouselProvider:
        """Get first available provider from the chain."""
        errors = []
        for name in provider_names:
            try:
                provider = get_provider(name, **kwargs)
                # Verify provider is usable (has API key, etc.)
                if provider.is_available():  # New method
                    return provider
            except Exception as e:
                errors.append(f"{name}: {e}")
        
        raise RuntimeError(f"No providers available. Tried: {errors}")
    ```
    
    Also add `is_available()` method to base class.
  </action>
  <verify>python3 -c "from providers import get_provider_with_fallback"</verify>
  <done>
    - get_provider_with_fallback() working
    - Graceful chain iteration
  </done>
</task>

## Success Criteria

- [ ] `--provider` selects specific provider
- [ ] `--fallback` adds fallback on error
- [ ] `--list-providers` shows available providers
- [ ] `--image-quality` configures Gamma tier
