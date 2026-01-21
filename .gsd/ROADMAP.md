# ROADMAP.md

> **Current Phase**: Phase 3 — Canva MCP Provider
> **Milestone**: v1.0 — Modular Carousel Generator

## Must-Haves (from SPEC)

- [ ] Provider abstraction layer
- [ ] Canva MCP provider
- [ ] Pillow+AI provider (OpenAI/Gemini)
- [ ] Pillow+Unsplash provider (free fallback)
- [ ] CLI provider selection
- [ ] Fallback chain support

## Phases

### Phase 1: Provider Abstraction Layer
**Status**: ✅ Complete
**Objective**: Create base provider interface and refactor existing code
**Deliverables**:
- `providers/base.py` — Abstract base class ✓
- `providers/__init__.py` — Provider registry ✓
- Refactor `generate_carousel.py` to use provider pattern ✓

### Phase 2: Pillow Providers
**Status**: ✅ Complete
**Objective**: Implement Pillow-based providers with different image sources
**Deliverables**:
- `providers/pillow_openai.py` — DALL-E images ✓
- `providers/pillow_unsplash.py` — Free Unsplash images ✓
- `providers/pillow_gemini.py` — Gemini Imagen (optional) ✓ementation
- `providers/pillow_unsplash.py` — Free stock photos

### Phase 3: Gamma API Provider
**Status**: 🔄 In Progress
**Objective**: Implement Gamma API for professional carousel generation
**Deliverables**:
- `providers/gamma.py` — Gamma API integration
- Image quality tiers (Unsplash → Premium AI)
- Credit tracking for cost management

### Phase 5: CLI & Workflow Integration
**Status**: ⬜ Not Started
**Objective**: Complete CLI integration and GitHub Actions workflow
**Deliverables**:
- Updated CLI with `--provider` flag
- `config/providers.yaml` for fallback configuration
- Update `.github/workflows/discord-fetch.yml` to uncomment carousel step
- Provider selection via `CAROUSEL_PROVIDER` environment variable
- Fallback chain: `canva → pillow_unsplash` (zero-cost default)

### Phase 6: Testing & Documentation
**Status**: ⬜ Not Started
**Objective**: Comprehensive testing and docs
**Deliverables**:
- Provider unit tests
- Integration tests
- Updated README
