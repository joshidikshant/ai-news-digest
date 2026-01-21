---
phase: 5
plan: 2
wave: 2
---

# Plan 5.2: Update GitHub Actions Workflow

## Objective

Uncomment and update the carousel generation step in the GitHub Actions workflow to use the new provider system.

## Context

- .github/workflows/discord-fetch.yml — Main pipeline
- Currently carousel generation is PAUSED (commented out)
- Need to add CAROUSEL_PROVIDER and GAMMA_API_KEY support

## Tasks

<task type="auto">
  <name>Update GitHub Actions workflow</name>
  <files>
    .github/workflows/discord-fetch.yml
  </files>
  <action>
    Update the workflow to use the new provider system:
    
    1. Uncomment the carousel generation step
    2. Add CAROUSEL_PROVIDER environment variable
    3. Add GAMMA_API_KEY secret for Gamma provider
    4. Add fallback to pillow_unsplash for free operation
    
    New step:
    ```yaml
    - name: Generate LinkedIn carousels
      env:
        CAROUSEL_PROVIDER: ${{ secrets.CAROUSEL_PROVIDER || 'pillow_unsplash' }}
        GAMMA_API_KEY: ${{ secrets.GAMMA_API_KEY }}
        OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
      run: |
        python generate_carousel.py \
          --provider $CAROUSEL_PROVIDER \
          --fallback pillow_unsplash
    ```
    
    This allows:
    - Default: FREE (pillow_unsplash) if no secrets set
    - Optional: gamma if GAMMA_API_KEY and CAROUSEL_PROVIDER=gamma
    - Fallback: Always falls back to free if provider fails
  </action>
  <verify>cat .github/workflows/discord-fetch.yml | grep -A5 "Generate LinkedIn"</verify>
  <done>
    - Carousel generation step uncommented
    - Provider selection via environment variable
    - Fallback to free pillow_unsplash
  </done>
</task>

<task type="auto">
  <name>Update requirements.txt</name>
  <files>
    requirements.txt
  </files>
  <action>
    Add aiohttp for Gamma provider:
    
    ```
    aiohttp>=3.8.0
    ```
    
    This is needed for the Gamma API calls.
  </action>
  <verify>grep aiohttp requirements.txt</verify>
  <done>
    - aiohttp added to requirements.txt
  </done>
</task>

## Success Criteria

- [ ] Carousel generation step uncommented
- [ ] CAROUSEL_PROVIDER environment variable support
- [ ] GAMMA_API_KEY secret support
- [ ] Default fallback to free provider
- [ ] aiohttp in requirements.txt
