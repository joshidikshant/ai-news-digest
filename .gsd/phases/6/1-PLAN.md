---
phase: 6
plan: 1
wave: 1
---

# Plan 6.1: Provider Tests

## Objective

Create basic tests for the provider system to ensure reliability.

## Tasks

<task type="auto">
  <name>Create provider unit tests</name>
  <files>
    tests/test_providers.py
  </files>
  <action>
    Create unit tests for the provider system:
    
    1. Test registry functions:
       - `list_providers()` returns expected providers
       - `get_provider()` returns correct provider type
       - `get_provider()` raises error for unknown provider
    
    2. Test each provider:
       - Can be instantiated
       - Has required methods (generate_carousel, save_as_pdf)
       - Handles missing API keys gracefully
    
    3. Test configuration:
       - CarouselConfig has expected defaults
       - Themes are valid
    
    Use pytest for testing.
  </action>
  <verify>python -m pytest tests/test_providers.py -v</verify>
  <done>
    - Provider tests passing
    - Registry tests passing
    - Config tests passing
  </done>
</task>

## Success Criteria

- [ ] Tests for provider registry
- [ ] Tests for each provider instantiation
- [ ] Tests pass without API keys (graceful degradation)
