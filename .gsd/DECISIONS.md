# DECISIONS.md — Architecture Decision Records

## Format

Each decision follows this structure:
- **ID**: ADR-NNN
- **Date**: YYYY-MM-DD
- **Status**: Proposed | Accepted | Deprecated | Superseded
- **Context**: Why this decision was needed
- **Decision**: What was decided
- **Consequences**: What this means going forward

---

## ADR-001: Modular Provider Architecture

**Date**: 2026-01-21
**Status**: Accepted

### Context
The existing `generate_carousel.py` uses DALL-E for AI images (~$0.20/carousel), which is too expensive for daily automation. User has access to multiple alternatives:
- Canva (paid plan)
- Gamma API
- Unsplash (free)

### Decision
Implement a pluggable provider architecture where carousel backends are interchangeable. Each provider implements a common interface for generating 5-slide carousel PDFs.

### Consequences
- **Positive**: Flexibility to switch providers based on cost/quality needs
- **Positive**: Can implement fallback chains (try Canva → Pillow if fails)
- **Negative**: More complex codebase than single implementation
- **Negative**: Need to maintain multiple provider implementations

---

## ADR-002: Canva MCP as Primary Provider

**Date**: 2026-01-21
**Status**: Proposed

### Context
User already pays for Canva, and Canva offers an MCP server for programmatic design creation.

### Decision
Prioritize Canva MCP as the primary provider since it has no additional cost.

### Consequences
- **Positive**: Zero additional cost
- **Positive**: Professional templates and AI images included
- **Negative**: Dependency on Canva's MCP availability
- **Mitigation**: Fallback to Pillow+Unsplash if Canva fails
