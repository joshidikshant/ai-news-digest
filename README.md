# AI News Digest 🤖📰

A powerful, automated pipeline for tech-savvy curators. It turns raw Discord conversations into curated, high-quality news digests in Notion and ready-to-post content drafts for Twitter/LinkedIn.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Code Style: Black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

## 🚀 Overview

This engine monitors multiple Discord servers for AI news, uses OpenAI (GPT-4o) to curate and summarize the most important updates, syncs them to a structured Notion database, and automatically generates social media drafts.

**Workflow:**
`Discord (Raw Sources)` → `Python Fetcher` → `OpenAI Curation` → `Notion Database` + `Content Drafts`

## ✨ Features

- **Multi-Server Monitoring**: Configurable via `config/servers.yaml` to track specific channels across different Discord servers (e.g., OpenAI, Anthropic, Google).
- **🧠 AI Curation Engine**:
  - Filters noise: Only curated items with high relevance scores (>70) make the cut.
  - Summarizes: Generates punchy headlines, key bullet points, and a "Hot Take".
  - **Cost Optimized**: Maintains a local state to ensure **messages are never processed twice**, saving OpenAI API costs.
- **📝 Notion Integration**:
  - Syncs curated items to a Notion Database.
  - **Duplicate Prevention**: Tracks synced items to ensure your database stays clean.
  - **Adaptive Schema**: Automatically handles missing columns to prevent crashes.
- **✍️ Auto-Content Generation**:
  - Creates Markdown drafts for Twitter threads and LinkedIn posts.
  - Saved to `data/content/YYYY-MM-DD/` and downloadable as GitHub Artifacts.
- **Automated Pipeline**: Runs on a schedule via GitHub Actions.

---

## 🛠️ Detailed Setup

### 1. Prerequisites
- **Python 3.11+**
- **Notion Account**
- **Discord Account**
- **OpenAI API Key**

### 2. Discord Configuration
You need a Discord User Token to read messages (Self-bot mode).
1. Open Discord in Browser.
2. Open DevTools (`Ctrl+Shift+I` / `Cmd+Opt+I`) -> Network Tab.
3. Filter by `messages`.
4. Click a channel. Copy the `authorization` header from the request.
   > **⚠️ Warning**: Keep this token secret. Do not share it.

### 3. Notion Configuration
1. Create a new Integration at [Notion Developers](https://www.notion.so/my-integrations).
2. Create a new Database in Notion.
3. Share the Database with your Integration (meatball menu -> Connections).
4. **Crucial**: Ensure your Database has these properties:

| Property Name | Type | Description |
|---------------|------|-------------|
| **Title** | Title | Headline |
| **Category** | Select | Announcement, Insight, Tutorial, Discussion |
| **Source** | Select | Server name (e.g., OpenAI) |
| **Relevance** | Number | Score (0-100) |
| **Status** | Status | New, Reviewed, Published |
| **Hot Take** | Text | Engagement hook |
| **Date** | Date | Message timestamp |
| **Original Link** | URL | Link to Discord message |

*Tip: You can use the included `setup_notion_db.py` script to inspect your database schema if needed.*

### 4. GitHub Configuration
Fork this repo and add these Secrets (`Settings` -> `Secrets and variables` -> `Actions`):
- `DISCORD_TOKEN`
- `OPENAI_API_KEY`
- `NOTION_API_KEY`
- `NOTION_DATABASE_ID`

---

## 🏃‍♂️ Usage

### Automated (GitHub Actions)
The pipeline runs automatically daily at 7:10 AM PST.
You can also trigger it manually via the **Actions** tab -> **AI News Digest Pipeline**.

### Local Run
1. Clone the repo.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Set Environment Variables:
   ```bash
   export DISCORD_TOKEN="your_token"
   export OPENAI_API_KEY="sk-..."
   export NOTION_API_KEY="secret_..."
   export NOTION_DATABASE_ID="your_db_id"
   ```
4. Run the full pipeline:
   ```bash
   # 1. Fetch
   python discord_fetch.py
   
   # 2. Curate (Cost optimized: skips existing)
   python curate.py
   
   # 3. Sync (Cost optimized: skips existing)
   python notion_sync.py
   
   # 4. Generate Content
   python generate_content.py
   
   # 5. Generate LinkedIn Carousels
   python generate_carousel.py --provider pillow_unsplash
   ```

---

## 🎠 LinkedIn Carousel Generation

Generate professional LinkedIn carousel PDFs from your curated news.

### Available Providers

| Provider | Cost | Quality | Best For |
|----------|------|---------|----------|
| `pillow_unsplash` | **FREE** | Good | Daily automation |
| `gamma` | $15/mo | Excellent | Professional content |
| `pillow_openai` | ~$0.20/carousel | Premium | Special features |

### Quick Start

```bash
# Free mode (default)
python generate_carousel.py --provider pillow_unsplash

# List providers
python generate_carousel.py --list-providers

# With Gamma API
export GAMMA_API_KEY="your_key"
python generate_carousel.py --provider gamma
```

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `CAROUSEL_PROVIDER` | Default provider | `pillow_unsplash` |
| `GAMMA_API_KEY` | Gamma.app API key | - |

---

## 🔧 Customization

### Modifying Prompts
Edit `config/prompts.yaml` to change the AI's persona or output format.
- `curation.system`: Controls how the AI filters and summarizes news.
- `content_generation.twitter`: Controls the style of generated Tweets.

### Adding Servers
Edit `config/servers.yaml` to add more sources.
```yaml
servers:
  - name: "Stability AI"
    channels:
      - id: 123456789
        type: announcement
```

---

## ❓ Troubleshooting

**"No curated data found"**
- Check `data/raw/` to see if Discord fetch worked.
- Check `curate.py` logs. If messages were fetched but not curated, they might have been filtered out by the "Cost Optimization" check (delete `data/state/processed_messages.json` to force re-run).

**Notion Sync Errors**
- Ensure your property names match EXACTLY (case-sensitive).
- Use `setup_notion_db.py` to debug schema issues.

---

## ⚠️ Disclaimer
This tool uses a user token to read Discord messages. Automating user accounts is technically against Discord TOS. Use responsibly and at your own risk.

## 👏 Credits
- **Original Inspiration**: [KingBootoshi](https://x.com/KingBootoshi), creator of SILK.
- **Base Logic**: Adapted from the original `daily-silk` fetcher.
- Built with assistance from Google DeepMind's Antigravity Agent.
