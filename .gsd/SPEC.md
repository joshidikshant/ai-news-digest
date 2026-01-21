# SPEC.md — Project Specification

> **Status**: `FINALIZED`

## Vision

Build a **modular LinkedIn Carousel Generator** that allows users to choose between multiple backend providers (Canva MCP, Gamma API, or custom Pillow+AI) for generating professional carousel PDFs from curated AI news content. The system integrates seamlessly with the existing `ai-news-digest` pipeline and outputs LinkedIn-ready carousels.

## Existing Pipeline Integration

The carousel generator is the **final step** in the existing workflow:

```
┌─────────────────────────────────────────────────────────────────────┐
│                     AI NEWS DIGEST PIPELINE                         │
├─────────────────────────────────────────────────────────────────────┤
│  discord_fetch.py  →  curate.py  →  notion_sync.py                 │
│         ↓                ↓               ↓                          │
│   data/raw/       data/curated/    Notion DB                        │
│                          ↓                                          │
│               generate_content.py                                   │
│                          ↓                                          │
│               data/content/ (Twitter/LinkedIn text)                 │
│                          ↓                                          │
│               generate_carousel.py  ← THIS PROJECT                  │
│                          ↓                                          │
│               data/carousels/ (PDF/PNG)                             │
└─────────────────────────────────────────────────────────────────────┘
```

**Input**: `data/curated/{date}.json` — Curated AI news items
**Output**: `data/carousels/{date}/{theme}/{name}.pdf` — LinkedIn carousel PDFs

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

- **Technical**: Must consume `data/curated/{date}.json` format unchanged
- **Workflow**: Must run after `generate_content.py` in GitHub Actions
- **Budget**: Minimize API costs; original DALL-E approach ($0.20/carousel) too expensive
- **Existing Assets**: User has Canva paid plan, OpenAI API access, Gemini access
- **Output**: LinkedIn carousel format (1080x1350 portrait, PDF)
- **48-hour Window**: Already implemented in existing carousel code

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
