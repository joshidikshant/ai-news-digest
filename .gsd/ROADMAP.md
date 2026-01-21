# ROADMAP.md

> **Current Phase**: Phase 2 — Pillow Providers
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
**Status**: ⬜ Not Started  
**Objective**: Implement Pillow-based providers with different image sources
**Deliverables**:
- `providers/pillow_openai.py` — Current DALL-E implementation
- `providers/pillow_gemini.py` — Gemini Imagen implementation
- `providers/pillow_unsplash.py` — Free stock photos

### Phase 3: Canva MCP Provider
**Status**: ⬜ Not Started
**Objective**: Integrate Canva MCP for carousel generation
**Deliverables**:
- `providers/canva_mcp.py` — Canva MCP integration
- Template discovery and management
- Export to PDF functionality

### Phase 4: Gamma API Provider (Optional)
**Status**: ⬜ Not Started
**Objective**: Add Gamma API as alternative provider
**Deliverables**:
- `providers/gamma.py` — Gamma API integration
- Credit tracking and monitoring

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
