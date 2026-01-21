---
phase: 3
plan: 1
wave: 1
---

# Plan 3.1: Canva MCP Provider

## Objective

Create a Canva MCP provider that leverages the user's existing Canva paid plan for professional carousel generation. This provider uses Canva's AI capabilities and template system.

## Context

- providers/base.py — Base class to inherit from
- providers/pillow_openai.py — Reference for provider structure
- Canva MCP Server: `npx @canva/cli@latest mcp`

## Research Notes

Canva MCP capabilities:
- `create-design` — Generate designs from prompts/templates
- `export-design` — Export to PDF/PNG for LinkedIn
- `search-designs` — Find existing templates
- `autofill` — Populate templates with external data

## Tasks

<task type="auto">
  <name>Create canva_mcp provider</name>
  <files>
    providers/canva_mcp.py
  </files>
  <action>
    Create `CanvaMCPProvider` with MCP-based carousel generation:
    
    1. Provider class structure:
       ```python
       @register_provider("canva_mcp")
       class CanvaMCPProvider(CarouselProvider):
           name = "canva_mcp"
           
           def __init__(self, theme="dark", template_id=None, **kwargs):
               super().__init__(theme=theme, **kwargs)
               self.template_id = template_id or os.getenv("CANVA_TEMPLATE_ID")
               # MCP client setup (placeholder until MCP integration clear)
       ```
    
    2. Key methods:
       - `async def _create_design(self, item: Dict) -> str` — Create design via MCP
       - `async def _export_design(self, design_id: str) -> List[Image.Image]` — Export to images
       - `async def generate_carousel(self, item: Dict)` — Main entry point
    
    3. Fallback behavior:
       - If Canva MCP unavailable, raise clear error with setup instructions
       - Log MCP commands for debugging
    
    4. Template mode vs AI mode:
       - Template mode: Use predefined carousel template
       - AI mode: Let Canva AI generate design from prompt
    
    NOTE: This is a STUB provider that defines the interface.
    Full MCP integration requires the Canva CLI to be installed.
  </action>
  <verify>python3 -c "from providers import get_provider; p = get_provider('canva_mcp'); print(f'✅ {p.name}')"</verify>
  <done>
    - Provider registered as 'canva_mcp'
    - Clear interface for MCP-based generation
    - Graceful error when MCP not configured
  </done>
</task>

<task type="auto">
  <name>Register provider in __init__.py</name>
  <files>
    providers/__init__.py
  </files>
  <action>
    Add import for canva_mcp provider:
    
    ```python
    try:
        from providers import canva_mcp
    except ImportError as e:
        pass  # Silently skip if not available
    ```
  </action>
  <verify>python3 -c "from providers import list_providers; print('canva_mcp' in list_providers())"</verify>
  <done>
    - 'canva_mcp' appears in list_providers()
  </done>
</task>

## Success Criteria

- [ ] `canva_mcp` provider registered
- [ ] Provider can be instantiated
- [ ] Clear documentation on MCP setup requirements
- [ ] Interface ready for full MCP integration

## Notes

This is a **stub implementation**. Full Canva MCP integration requires:
1. Canva paid plan (user has ✓)
2. Canva CLI: `npx @canva/cli@latest mcp`
3. MCP server running
4. Antigravity MCP client integration

The stub allows:
- Testing the fallback chain: canva_mcp → pillow_unsplash
- Documenting the expected interface
- Future MCP integration without changing other code
