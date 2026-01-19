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
        
        # Load state of synced items to prevent duplication
        synced_state_file = os.path.join(Config.DATA_DIR, "state", "synced_items.json")
        os.makedirs(os.path.dirname(synced_state_file), exist_ok=True)
        
        synced_ids = set()
        if os.path.exists(synced_state_file):
            try:
                with open(synced_state_file, "r") as f:
                    synced_ids = set(json.load(f))
            except: pass
        
        new_synced_count = 0
        for item in items:
            # Create a unique signature for deduplication
            # Using headline + first few chars of bullet or just headline if unique enough
            # Ideally use a hash, but headline is readable
            item_sig = f"{item.get('headline', '')}_{item.get('source', {}).get('timestamp', '')}"
            if item_sig in synced_ids:
                print(f"Skipping duplicate: {item.get('headline')}")
                continue
                
            try:
                if self._create_page(item):
                    synced_ids.add(item_sig)
                    new_synced_count += 1
            except Exception as e:
                print(f"Error syncing item {item.get('headline', 'Unknown')}: {e}")

        # Save synced state
        if new_synced_count > 0:
            with open(synced_state_file, "w") as f:
                json.dump(list(synced_ids), f)
                print(f"Successfully synced {new_synced_count} new items.")
        else:
            print("No new items to sync.")

    def _create_page(self, item: Dict):
        # Construct summary text block
        summary_bullets = item.get('bullets', [])
        summary_text = "\n".join([f"• {b}" for b in summary_bullets])
        
        # Helper for GitHub URLs
        def get_github_url(path):
            if not path: return None
            clean_path = path.replace("\\", "/") # Windows fix
            if clean_path.startswith("./"): clean_path = clean_path[2:]
            return f"https://raw.githubusercontent.com/joshidikshant/ai-news-digest/main/{clean_path}"

        media_url = get_github_url(item.get('media_path'))
        video_url = get_github_url(item.get('video_path'))

        # Prepare all possible properties
        all_properties = {
            "Title": {"title": [{"text": {"content": item.get('headline', 'Untitled')}}]},
            "Category": {"select": {"name": item.get('category', 'Discussion').title()}},
            "Source": {"select": {"name": item.get('source', {}).get('server', 'Unknown')}},
            "Channel": {"rich_text": [{"text": {"content": item.get('source', {}).get('channel', 'Unknown')}}]},
            "Relevance": {"number": item.get('relevance', 0)},
            "Status": {"select": {"name": "New"}},
            "Hot Take": {"rich_text": [{"text": {"content": item.get('hot_take', '')}}]},
            "Date": {"date": {"start": item.get('source', {}).get('timestamp', datetime.now().isoformat())}}
        }
        
        # Add V2 Media Properties
        if media_url:
            all_properties["Visual"] = {"files": [{"name": "Cover Image", "type": "external", "external": {"url": media_url}}]}
        if video_url:
            all_properties["Video"] = {"files": [{"name": "Video Short", "type": "external", "external": {"url": video_url}}]}
        if item.get('video_script'):
             all_properties["Video Script"] = {"rich_text": [{"text": {"content": item.get('video_script')}}]}

        # Add link if exists
        link = item.get('source', {}).get('message_link')
        if link:
            all_properties["Original Link"] = {"url": link}

        # Page Children (Content)
        children = []
        
        # V2: Video Player at top
        if video_url:
            children.append({
                "object": "block",
                "type": "video",
                "video": {"type": "external", "external": {"url": video_url}}
            })
            
        # V2: Cover Image
        if media_url:
            children.append({
                "object": "block",
                "type": "image",
                "image": {"type": "external", "external": {"url": media_url}}
            })

        children.extend([
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
        ])
        
        # Add Script as toggle if exists
        if item.get('video_script'):
            children.append({
                "object": "block",
                "type": "toggle",
                "toggle": {
                    "rich_text": [{"text": {"content": "📜 Video Script"}}],
                    "children": [{
                        "object": "block", 
                        "type": "paragraph", 
                        "paragraph": {"rich_text": [{"text": {"content": item['video_script']}}]}
                    }]
                }
            })

        # Try to sync, removing invalid properties on failure
        # We'll make a copy of properties to modify
        current_properties = all_properties.copy()
        max_retries = 5
        
        for attempt in range(max_retries):
            try:
                self.client.pages.create(
                    parent={"database_id": self.db_id},
                    properties=current_properties,
                    children=children
                )
                print(f"Synced: {item.get('headline')}")
                return True # Success!
                
            except Exception as e:
                error_msg = str(e)
                # Check for "Property does not exist" type errors
                # Example error: "Date is not a property that exists."
                if "is not a property that exists" in error_msg:
                    # Extract property name
                    prop_name = error_msg.split(" is not a property")[0].strip()
                    # It might be part of a larger string, e.g. "Error syncing...: Date is not..."
                    if ": " in prop_name:
                         prop_name = prop_name.split(": ")[-1]
                         
                    if prop_name in current_properties:
                        print(f"  Warning: Property '{prop_name}' missing in Notion. Removing and retrying...")
                        del current_properties[prop_name]
                        continue
                
                # If error is about Status type mismatch, try to fix it
                if "Status is expected to be" in error_msg:
                    print(f"  Warning: Status type mismatch. Removing Status property...")
                    if "Status" in current_properties:
                        del current_properties["Status"]
                        continue

                # If we get here, it's an unhandled error or we failed to extract property name
                print(f"Error syncing item {item.get('headline', 'Unknown')}: {e}")
                break
        
        return False

if __name__ == "__main__":
    import glob
    
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", help="Date to sync (YYYY-MM-DD)")
    args = parser.parse_args()
    
    syncer = NotionSync()
    
    if args.date:
        # Specific date
        syncer.sync_day(args.date)
    else:
        # Auto-mode: Process all curated files (Smart Catch-up)
        curated_files = glob.glob(os.path.join(Config.DATA_DIR, "curated", "*.json"))
        curated_files.sort()
        
        if not curated_files:
            print("No curated data found.")
        else:
            print(f"Starting Notion Sync (Smart Catch-up)...")
            print(f"Found {len(curated_files)} curated days to process.\n")
            
            for f in curated_files:
                date_str = os.path.splitext(os.path.basename(f))[0]
                print(f"=== Syncing {date_str} ===")
                syncer.sync_day(date_str)
                print()  # blank line for readability

