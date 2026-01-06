import os
import json
import yaml
import glob
import argparse
from datetime import datetime, timezone as python_timezone
from openai import OpenAI
from typing import List, Dict

class Config:
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    DATA_DIR = "data"
    
    @staticmethod
    def load_prompts():
        with open("config/prompts.yaml", "r") as f:
            return yaml.safe_load(f)

class CurationEngine:
    def __init__(self):
        if not Config.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY environment variable not set")
        
        self.client = OpenAI(api_key=Config.OPENAI_API_KEY)
        self.config = Config.load_prompts()
        self.model = self.config['llm']['model']
        
    def curate_server_day(self, server_name: str, date_str: str, messages: List[Dict]) -> List[Dict]:
        if not messages:
            return []
            
        print(f"Curating {len(messages)} messages for {server_name} on {date_str}...")
        
        # Prepare context for LLM
        prompt_config = self.config['prompts']['curation']
        system_prompt = prompt_config['system']
        format_instructions = prompt_config['output_format']
        
        # Batching strategies could be implemented here, but for MVP we send all (or truncate)
        # We'll just take the top 50 most recent to avoid context limits for now, or batch
        messages_text = ""
        for msg in messages:
            messages_text += f"""
---
ID: {msg['id']}
Author: {msg['author']}
Channel: {msg.get('channel_name', 'unknown')}
Timestamp: {msg['timestamp']}
Link: {msg.get('link', 'N/A')}
Content:
{msg['content']}
---
"""
        
        user_prompt = f"""
Here are the raw Discord messages from {server_name} for {date_str}.
Please curate them according to your instructions.

{messages_text}

{format_instructions}
"""

        try:
            import sys
            print(f"  Calling OpenAI API with model {self.model}...", flush=True)
            sys.stdout.flush()
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.7
            )
            
            print(f"  OpenAI response received!", flush=True)
            
            content = response.choices[0].message.content
            print(f"  Raw content length: {len(content)} chars", flush=True)
            print(f"  Content preview: {content[:500]}...", flush=True)
            
            result = json.loads(content)
            print(f"  Parsed JSON type: {type(result)}", flush=True)
            
            # Handle multiple response formats
            if isinstance(result, list):
                # Direct array of items
                items = result
            elif isinstance(result, dict):
                if 'items' in result:
                    # Wrapped in items array (expected format)
                    items = result['items']
                elif 'headline' in result:
                    # Single item without wrapper
                    items = [result]
                else:
                    # Unknown format, try to find array values
                    items = []
                    for val in result.values():
                        if isinstance(val, list):
                            items = val
                            break
            else:
                items = []
                
            print(f"  Extracted items count: {len(items)}", flush=True)
                 
            # Add metadata
            for item in items:
                item['curated_at'] = datetime.now(python_timezone.utc).isoformat()
                item['original_server'] = server_name
            
            print(f"  Curated {len(items)} items", flush=True)
            return items
            
        except Exception as e:
            import traceback
            print(f"Error curating {server_name}: {e}", flush=True)
            traceback.print_exc()
            sys.stdout.flush()
            sys.stderr.flush()
            return []

    def run(self, date_str: str = None):
        print(f"Starting Curation Run...")
        
        target_files = []
        if date_str:
            # Specific date
            target_files = glob.glob(os.path.join(Config.DATA_DIR, "raw", "**", f"{date_str}.json"), recursive=True)
        else:
            # Auto-mode: Find ALL raw files
            # This allows the pipeline to catch up on any missed days
            target_files = glob.glob(os.path.join(Config.DATA_DIR, "raw", "**", "*.json"), recursive=True)
            
        if not target_files:
            print("No raw data files found to process.")
            return

        # Sort files to process chronologically
        target_files.sort()
        
        print(f"Found {len(target_files)} raw data files to process.")
        
        files_by_date = {}
        for f in target_files:
            # filename is YYYY-MM-DD.json
            d = os.path.splitext(os.path.basename(f))[0]
            if d not in files_by_date: files_by_date[d] = []
            files_by_date[d].append(f)
            
        sorted_dates = sorted(files_by_date.keys())
        for d in sorted_dates:
            self._process_date(d, files_by_date[d])

    def _process_date(self, date_str: str, raw_files: List[str]):
        print(f"\n=== Processing Date: {date_str} ===")
        all_curated_items = []
        
        for file_path in raw_files:
            server_name = os.path.basename(os.path.dirname(file_path)) 
            
            with open(file_path, "r", encoding="utf-8") as f:
                messages = json.load(f)
            
            # Load state of processed message IDs
            processed_state_file = os.path.join(Config.DATA_DIR, "state", "processed_messages.json")
            os.makedirs(os.path.dirname(processed_state_file), exist_ok=True)
            
            processed_ids = set()
            if os.path.exists(processed_state_file):
                try:
                    with open(processed_state_file, "r") as f:
                        processed_ids = set(json.load(f))
                except: pass
                
            # Filter messages check for str(id)
            new_messages = [m for m in messages if str(m['id']) not in processed_ids]
            
            if not new_messages:
                print(f"  No new messages to curate for {server_name} on {date_str}")
                continue
                
            print(f"  Found {len(new_messages)} new messages (skipped {len(messages) - len(new_messages)} processed)")
                
            curated = self.curate_server_day(server_name.replace("_", " ").title(), date_str, new_messages)
            
            if curated:
                all_curated_items.extend(curated)
                processed_ids.update(str(m['id']) for m in new_messages)
                
                with open(processed_state_file, "w") as f:
                    # Convert set to list for JSON serialization
                    json.dump(list(processed_ids), f)
            
        # Merge with existing curated file for the day
        output_dir = os.path.join(Config.DATA_DIR, "curated")
        json_path = os.path.join(output_dir, f"{date_str}.json")
        
        if os.path.exists(json_path):
            try:
                with open(json_path, "r", encoding="utf-8") as f:
                    existing_day_items = json.load(f)
                    existing_titles = {i.get('headline') for i in existing_day_items}
                    for item in all_curated_items:
                        if item.get('headline') not in existing_titles:
                            existing_day_items.append(item)
                    all_curated_items = existing_day_items
            except:
                pass 
            
        if all_curated_items:
            self._save_results(date_str, all_curated_items)

            
    def _save_results(self, date_str: str, items: List[Dict]):
        output_dir = os.path.join(Config.DATA_DIR, "curated")
        os.makedirs(output_dir, exist_ok=True)
        
        # Save JSON
        json_path = os.path.join(output_dir, f"{date_str}.json")
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(items, f, indent=2, ensure_ascii=False)
            
        # Save Markdown Summary
        md_path = os.path.join(output_dir, f"{date_str}.md")
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(f"# AI News Digest - {date_str}\n\n")
            
            # Group by category
            by_cat = {}
            for item in items:
                cat = item.get('category', 'other').title()
                if cat not in by_cat: by_cat[cat] = []
                by_cat[cat].append(item)
                
            for cat, cat_items in by_cat.items():
                f.write(f"## {cat}\n")
                for item in cat_items:
                    f.write(f"### {item.get('headline', 'Untitled')}\n")
                    f.write(f"**Score:** {item.get('relevance', 0)} | **Source:** {item.get('source', {}).get('server', 'Unknown')}\n\n")
                    for bullet in item.get('bullets', []):
                        f.write(f"- {bullet}\n")
                    f.write(f"\n> 🔥 **Hot Take:** {item.get('hot_take', 'N/A')}\n\n")
                    f.write("---\n")
                    
        print(f"Saved {len(items)} curated items to {json_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", help="Date to curate (YYYY-MM-DD)")
    args = parser.parse_args()
    
    engine = CurationEngine()
    engine.run(args.date)
