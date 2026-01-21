---
phase: 2
plan: 2
wave: 1
---

# Plan 2.2: Pillow Unsplash Provider (Free Fallback)

## Objective

Create a zero-cost provider that uses Unsplash API for background images. This is the default fallback when paid APIs aren't configured.

## Context

- providers/pillow_openai.py — Reference implementation from Plan 2.1
- providers/base.py — Base class
- providers/config.py — Shared configuration

## Tasks

<task type="auto">
  <name>Create pillow_unsplash provider</name>
  <files>
    providers/pillow_unsplash.py
  </files>
  <action>
    Create `PillowUnsplashProvider` based on pillow_openai but with Unsplash:
    
    1. Copy slide rendering logic from pillow_openai
    2. Replace `_generate_illustration()` with Unsplash API call:
       ```python
       async def _fetch_unsplash_image(self, query: str) -> Optional[Image.Image]:
           # Use Unsplash Source API (no key required for basic usage)
           # https://source.unsplash.com/1024x1024/?{query}
           url = f"https://source.unsplash.com/1024x1024/?{urllib.parse.quote(query)}"
           # Download and cache
       ```
    
    3. Register as 'pillow_unsplash'
    
    4. Key features:
       - No API key required for basic usage
       - Falls back to solid color if image fetch fails
       - Same caching mechanism as OpenAI provider
    
    DO NOT require UNSPLASH_ACCESS_KEY for basic functionality
    Use the simple Source API which requires no authentication
  </action>
  <verify>python3 -c "from providers import get_provider; p = get_provider('pillow_unsplash'); print(f'✅ {p.name}')"</verify>
  <done>
    - Provider registered as 'pillow_unsplash'
    - Works without any API keys
    - Uses Unsplash Source API for images
  </done>
</task>

## Success Criteria

- [ ] `pillow_unsplash` provider registered
- [ ] Works without API keys
- [ ] Fetches images from Unsplash Source API
