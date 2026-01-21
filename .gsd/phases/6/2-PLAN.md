---
phase: 6
plan: 2
wave: 1
---

# Plan 6.2: Update README Documentation

## Objective

Update the README to document the new carousel provider system.

## Tasks

<task type="auto">
  <name>Update README with carousel documentation</name>
  <files>
    README.md
  </files>
  <action>
    Add a "LinkedIn Carousel Generation" section:
    
    1. Available providers table:
       | Provider | Cost | Quality | Best For |
       |----------|------|---------|----------|
       | pillow_unsplash | FREE | Good | Daily automation |
       | gamma | $15/mo | Excellent | Professional |
       | pillow_openai | ~$0.20/carousel | Premium | Special content |
    
    2. Usage examples:
       ```bash
       # Free mode (default)
       python generate_carousel.py --provider pillow_unsplash
       
       # With Gamma
       export GAMMA_API_KEY=your_key
       python generate_carousel.py --provider gamma
       ```
    
    3. Environment variables:
       - CAROUSEL_PROVIDER
       - CAROUSEL_FALLBACK
       - GAMMA_API_KEY
       - GAMMA_IMAGE_QUALITY
    
    4. GitHub Actions configuration:
       - How to set secrets
       - How to change provider
  </action>
  <verify>grep -A5 "Carousel" README.md</verify>
  <done>
    - Provider table in README
    - Usage examples documented
    - Environment variables documented
  </done>
</task>

## Success Criteria

- [ ] Provider comparison table
- [ ] Usage examples
- [ ] Environment variable documentation
- [ ] GitHub Actions setup instructions
