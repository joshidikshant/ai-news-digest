# AI News Digest 🤖📰

A powerful, automated pipeline that turns raw Discord conversations into curated, high-quality news digests in Notion and ready-to-post content drafts.

## 🚀 Overview

This engine monitors multiple Discord servers for AI news, uses OpenAI (GPT-4) to curate and summarize the most important updates, syncs them to a structured Notion database, and automatically generates Twitter/LinkedIn content drafts.

**Workflow:**
`Discord (Raw Sources)` → `Python Fetcher` → `OpenAI Curation (Relevance Filter)` → `Notion Database` + `Content Drafts`

## ✨ Features

- **Multi-Server Monitoring**: Configurable via `config/servers.yaml` to track specific channels across different Discord servers (e.g., OpenAI, Anthropic, Google).
- **🧠 AI Curation Engine**:
  - Filters noise: Only curated items with high relevance scores (>70) make the cut.
  - Summarizes: Generates punchy headlines, key bullet points, and a "Hot Take".
  - **Cost Optimized**: Maintains a local state to ensure **messages are never processed twice**, saving OpenAI API costs.
- **📝 Notion Integration**:
  - Syncs curated items to a Notion Database.
  - **Duplicate Prevention**: Tracks synced items to ensure your database stays clean.
  - **Adaptive Sync**: Handles missing columns gracefully (though full schema is recommended).
- **✍️ Auto-Content Generation**:
  - Creates Markdown drafts for Twitter threads and LinkedIn posts.
  - Saved to `data/content/YYYY-MM-DD/` and downloadable as GitHub Artifacts.
- **Automated Pipeline**: Runs on a schedule via GitHub Actions.

## 🛠️ Setup

### 1. Prerequisites
- **Discord User Token**: To read messages (Self-bot mode).
- **OpenAI API Key**: For curation and content generation.
- **Notion Integration Token**: To write to your database.
- **Notion Database ID**: The target database.

### 2. Configuration
The project is driven by `config/servers.yaml`. Add your target channels here:

```yaml
servers:
  - name: "Anthropic"
    channels:
      - id: 123456789012345678 # "Announcements"
        type: announcement
  - name: "OpenAI"
    channels:
      - id: 987654321098765432
        type: discussion
```

### 3. Notion Database Schema
Create a Notion Database with the following properties for full functionality:

| Property Name | Type | Description |
|---------------|------|-------------|
| **Title** | Title | The headline of the news item |
| **Category** | Select | Announcement, Insight, Tutorial, Discussion |
| **Source** | Select | Server name (e.g., OpenAI, Google) |
| **Relevance** | Number | AI-assigned score (0-100) |
| **Status** | Status | New, Reviewed, Published |
| **Hot Take** | Text | An engagement hook |
| **Date** | Date | When the message was sent |
| **Original Link** | URL | Direct link to the Discord message |

### 4. GitHub Secrets
Add the following secrets to your repository:
- `DISCORD_TOKEN`
- `OPENAI_API_KEY`
- `NOTION_API_KEY`
- `NOTION_DATABASE_ID`

## 🏃‍♂️ Usage

### Automated (GitHub Actions)
The pipeline runs automatically based on the schedule in `.github/workflows/discord-fetch.yml`.
You can also trigger it manually:
1. Go to **Actions** tab.
2. Select **AI News Digest Pipeline**.
3. Click **Run workflow**.

### Local Run
```bash
# Install dependencies
pip install -r requirements.txt

# Run the full pipeline
python discord_fetch.py
python curate.py
python notion_sync.py
python generate_content.py
```

## 📂 Project Structure

- `discord_fetch.py`: Connects to Discord and saves raw messages to `data/raw/`.
- `curate.py`: Sends raw data to OpenAI for processing. Checks `data/state/processed_messages.json` to avoid duplication. Saves to `data/curated/`.
- `notion_sync.py`: Pushes curated data to Notion. Checks `data/state/synced_items.json` to prevent duplicates.
- `generate_content.py`: Creates social media drafts from high-relevance items.
- `config/`: Configuration files for prompts and server lists.

## 🤝 Contributing
Feel free to fork and submit PRs!

## ⚠️ Disclaimer
This tool uses a user token to read Discord messages. Automating user accounts is technically against Discord TOS. Use responsibly and at your own risk.

## 👏 Credits
- **Original Inspiration**: [KingBootoshi](https://x.com/KingBootoshi), creator of SILK.
- **Base Logic**: Adapted from the original `daily-silk` fetcher.
- Built with assistance from Google DeepMind's Antigravity Agent.
