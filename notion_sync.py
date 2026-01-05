import os
import json
import argparse
from datetime import datetime
from notion_client import Client as NotionClient
from typing import List, Dict

class Config:
    NOTION_API_KEY = os.getenv("NOTION_API_KEY")
    NOTION_DATABASE_ID = os.getenv("NOTION_DATABASE_ID")
    DATA_DIR = "data"

class NotionSync:
    def __init__(self):
        if not Config.NOTION_API_KEY:
            raise ValueError("NOTION_API_KEY environment variable not set")
        if not Config.NOTION_DATABASE_ID:
            raise ValueError("NOTION_DATABASE_ID environment variable not set")
            
        self.client = NotionClient(auth=Config.NOTION_API_KEY)
        self.db_id = Config.NOTION_DATABASE_ID
        
    def sync_day(self, date_str: str):
        filepath = os.path.join(Config.DATA_DIR, "curated", f"{date_str}.json")
        if not os.path.exists(filepath):
            print(f"No curated data found for {date_str}")
            return
            
        with open(filepath, "r", encoding="utf-8") as f:
            items = json.load(f)
            
        print(f"Syncing {len(items)} items to Notion...")
        
        for item in items:
            try:
                self._create_page(item)
            except Exception as e:
                print(f"Error syncing item {item.get('headline', 'Unknown')}: {e}")

    def _create_page(self, item: Dict):
        # Construct summary text block
        summary_bullets = item.get('bullets', [])
        summary_text = "\n".join([f"• {b}" for b in summary_bullets])
        
        # Prepare properties
        properties = {
            "Title": {"title": [{"text": {"content": item.get('headline', 'Untitled')}}]},
            "Category": {"select": {"name": item.get('category', 'Discussion').title()}},
            "Source": {"select": {"name": item.get('source', {}).get('server', 'Unknown')}},
            "Channel": {"rich_text": [{"text": {"content": item.get('source', {}).get('channel', 'Unknown')}}]},
            "Relevance": {"number": item.get('relevance', 0)},
            "Status": {"select": {"name": "New"}},
            "Hot Take": {"rich_text": [{"text": {"content": item.get('hot_take', '')}}]},
            "Date": {"date": {"start": item.get('source', {}).get('timestamp', datetime.now().isoformat())}}
        }
        
        # Add link if exists
        link = item.get('source', {}).get('message_link')
        if link:
            properties["Original Link"] = {"url": link}

        # Page Children (Content)
        children = [
            {
                "object": "block",
                "type": "heading_2",
                "heading_2": {"rich_text": [{"text": {"content": "Summary"}}]}
            },
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {"rich_text": [{"text": {"content": summary_text}}]}
            },
            {
                "object": "block",
                "type": "callout",
                "callout": {
                    "rich_text": [{"text": {"content": f"🔥 {item.get('hot_take', 'No hot take')}"}}],
                    "icon": {"emoji": "🔥"}
                }
            }
        ]

        self.client.pages.create(
            parent={"database_id": self.db_id},
            properties=properties,
            children=children
        )
        print(f"Synced: {item.get('headline')}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", help="Date to sync (YYYY-MM-DD)")
    args = parser.parse_args()
    
    date_str = args.date if args.date else datetime.now().strftime("%Y-%m-%d")
    syncer = NotionSync()
    syncer.sync_day(date_str)
