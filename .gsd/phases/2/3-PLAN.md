---
phase: 2
plan: 3
wave: 2
---

# Plan 2.3: Pillow Gemini Provider (Optional)

## Objective

Create a provider using Google's Gemini Imagen API as an alternative to DALL-E. This is lower priority and depends on Gemini API availability.

## Context

- providers/pillow_openai.py — Reference implementation
- providers/base.py — Base class
- Gemini Imagen API documentation

## Tasks

<task type="auto">
  <name>Create pillow_gemini provider</name>
  <files>
    providers/pillow_gemini.py
  </files>
  <action>
    Create `PillowGeminiProvider` based on pillow_openai:
    
    1. Copy base structure from pillow_openai
    2. Replace DALL-E call with Gemini Imagen API:
       ```python
       import google.generativeai as genai
       
       async def _generate_illustration(self, headline: str, bullet: str = "") -> Optional[Image.Image]:
           # Use Gemini's image generation
           genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
           # Generate and return image
       ```
    
    3. Register as 'pillow_gemini'
    
    4. Graceful degradation:
       - Skip if GEMINI_API_KEY not set
       - Fall back to solid backgrounds
    
    NOTE: Gemini Imagen may have different availability
    Research API availability before implementing
  </action>
  <verify>python3 -c "from providers import get_provider; p = get_provider('pillow_gemini'); print(f'✅ {p.name}')"</verify>
  <done>
    - Provider registered as 'pillow_gemini'
    - Uses Gemini API for image generation
    - Graceful fallback when API unavailable
  </done>
</task>

## Success Criteria

- [ ] `pillow_gemini` provider registered
- [ ] Uses Gemini Imagen API
- [ ] Graceful degradation without API key
