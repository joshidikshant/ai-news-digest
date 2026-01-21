# SPEC.md — Project Specification

> **Status**: `FINALIZED`

## Vision

Build a **modular LinkedIn Carousel Generator** that allows users to choose between multiple backend providers (Canva MCP, Gamma API, or custom Pillow+AI) for generating professional carousel PDFs from curated AI news content. The system integrates with the existing `ai-news-digest` pipeline and outputs LinkedIn-ready carousels.

## Goals

1. **Modular Provider Architecture** — Pluggable backend system supporting Canva, Gamma, and Pillow+AI
2. **Configuration-Driven Selection** — User chooses provider via config/env without code changes
3. **Consistent Output Format** — All providers produce same carousel structure (5-slide PDF)
4. **Cost Optimization** — Enable fallback chains (e.g., try Canva → fallback to Pillow)

## Non-Goals (Out of Scope)

- LinkedIn posting automation (manual upload only)
- Real-time carousel preview UI
- Multi-language support (English only for v1)
- Video carousels (PDF/PNG only)

## Users

- **Primary**: The project owner running automated daily workflows
- **Use Case**: Generate carousels from curated AI news for LinkedIn posting

## Constraints

- **Technical**: Must integrate with existing `curate.py` output format
- **Budget**: Minimize API costs; prefer free/included options
- **Existing Assets**: User has Canva paid plan, OpenAI API access
- **Output**: LinkedIn carousel format (1080x1350 portrait, PDF)

## Providers

| Provider | API Access | Cost | AI Images |
|----------|------------|------|-----------|
| Canva MCP | User's paid plan | $0 additional | ✅ |
| Gamma API | Pro $15/mo | ~20-120 credits/carousel | ✅ |
| Pillow + OpenAI | DALL-E API | ~$0.20/carousel | ✅ |
| Pillow + Gemini | Imagen API | TBD | ✅ |
| Pillow + Unsplash | Free API | $0 | Stock only |

## Success Criteria

- [ ] Provider abstraction layer with common interface
- [ ] At least 3 working providers (Canva, Pillow+OpenAI, Pillow+Unsplash)
- [ ] CLI flag to select provider: `--provider canva|gamma|pillow`
- [ ] Fallback chain configuration
- [ ] Existing carousel tests pass
- [ ] Generated carousels match 5-slide structure
