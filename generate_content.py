import os
import json
import yaml
import glob
import argparse
import asyncio
from datetime import datetime, timedelta, timezone as python_timezone
from openai import AsyncOpenAI
from typing import List, Dict

class Config:
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    DATA_DIR = "data"
    # Sliding window: only process curated files from the last N hours
    SLIDING_WINDOW_HOURS = 48
    
    @staticmethod
    def load_prompts():
        with open("config/prompts.yaml", "r") as f:
            return yaml.safe_load(f)

class ContentGenerator:
    def __init__(self):
        if not Config.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY environment variable not set")
        
        # Use AsyncOpenAI for non-blocking API calls
        self.client = AsyncOpenAI(api_key=Config.OPENAI_API_KEY)
        self.config = Config.load_prompts()
        self.model = self.config['llm']['model']
        # Semaphore to limit concurrent API calls (avoid rate limits)
        self.sem = asyncio.Semaphore(5)
        
    async def generate_day_async(self, date_str: str):
        """Generate content drafts for a single day (async)."""
        filepath = os.path.join(Config.DATA_DIR, "curated", f"{date_str}.json")
        if not os.path.exists(filepath):
            print(f"No curated data found for {date_str}")
            return
            
        with open(filepath, "r", encoding="utf-8") as f:
            items = json.load(f)
        
        # Filter to high-relevance items first
        items_to_process = [item for item in items if item.get('relevance', 0) >= 70]
        
        if not items_to_process:
            print(f"No high-relevance items for {date_str}")
            return
            
        print(f"Generating content for {len(items_to_process)} items (parallel)...")
        
        output_dir = os.path.join(Config.DATA_DIR, "content", date_str)
        os.makedirs(output_dir, exist_ok=True)
        
        # Create async tasks for all items
        tasks = [self._process_item(item, output_dir) for item in items_to_process]
        await asyncio.gather(*tasks)
        
        print(f"✅ Completed content generation for {date_str}")

    async def _process_item(self, item: Dict, output_dir: str):
        """Process a single item: generate drafts and save to file."""
        safe_title = "".join([c for c in item['headline'] if c.isalnum() or c in (' ', '-', '_')]).strip().replace(" ", "_").lower()
        filename = f"{safe_title}.md"
        filepath_out = os.path.join(output_dir, filename)
        
        # Skip if draft already exists
        if os.path.exists(filepath_out):
            print(f"  Skipping existing: {filename[:40]}...")
            return
        
        # Acquire semaphore before making API calls
        async with self.sem:
            print(f"  Generating: {item['headline'][:40]}...")
            drafts = await self._generate_drafts(item)
        
        # Write to file
        with open(filepath_out, "w", encoding="utf-8") as f:
            f.write(f"# Content Drafts: {item['headline']}\n\n")
            f.write(f"**Source:** {item.get('source', {}).get('server')} | **Relevance:** {item.get('relevance')}\n")
            f.write(f"**Hot Take:** {item.get('hot_take')}\n\n")
            f.write("---\n\n")
            
            if 'twitter' in drafts:
                f.write("## 🐦 Twitter / X\n\n")
                f.write(drafts['twitter'])
                f.write("\n\n---\n\n")
                
            if 'linkedin' in drafts:
                f.write("## 💼 LinkedIn\n\n")
                f.write(drafts['linkedin'])
                f.write("\n\n---\n\n")
        
        print(f"  ✨ Saved: {filename[:40]}...")

    async def _generate_drafts(self, item: Dict) -> Dict[str, str]:
        """Generate Twitter and LinkedIn drafts in parallel."""
        prompt_config = self.config['prompts']['content_generation']
        formats = ['twitter', 'linkedin']
        
        async def fetch_draft(fmt: str):
            system_prompt = prompt_config[fmt]['system']
            user_prompt = f"""
Headline: {item['headline']}
Key Points:
{json.dumps(item['bullets'], indent=2)}
Hot Take: {item.get('hot_take', 'N/A')}

Draft the content now.
"""
            try:
                response = await self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    temperature=0.8
                )
                return fmt, response.choices[0].message.content
            except Exception as e:
                print(f"    ❌ Error generating {fmt}: {e}")
                return fmt, None
        
        # Generate both formats in parallel
        results = await asyncio.gather(*(fetch_draft(fmt) for fmt in formats))
        
        drafts = {}
        for fmt, content in results:
            if content:
                drafts[fmt] = content
                
        return drafts


def get_recent_curated_files(hours: int = 48) -> List[str]:
    """Get curated files from the last N hours only (sliding window)."""
    curated_files = glob.glob(os.path.join(Config.DATA_DIR, "curated", "*.json"))
    
    if not curated_files:
        return []
    
    # Calculate cutoff date
    now = datetime.now(python_timezone.utc)
    cutoff = now - timedelta(hours=hours)
    cutoff_date_str = cutoff.strftime("%Y-%m-%d")
    
    # Filter to only recent files
    recent_files = []
    for f in sorted(curated_files):
        date_str = os.path.splitext(os.path.basename(f))[0]
        if date_str >= cutoff_date_str:
            recent_files.append(f)
    
    return recent_files


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", help="Date to generate for (YYYY-MM-DD)")
    parser.add_argument("--all", action="store_true", help="Process ALL curated files (ignore sliding window)")
    args = parser.parse_args()
    
    generator = ContentGenerator()
    
    if args.date:
        # Specific date requested
        await generator.generate_day_async(args.date)
    elif args.all:
        # Process all curated files (for manual catch-up)
        curated_files = glob.glob(os.path.join(Config.DATA_DIR, "curated", "*.json"))
        curated_files.sort()
        print(f"Processing ALL {len(curated_files)} curated days...")
        for f in curated_files:
            date_str = os.path.splitext(os.path.basename(f))[0]
            print(f"\n=== Generating Content for {date_str} ===")
            await generator.generate_day_async(date_str)
    else:
        # Default: sliding window (last 48 hours)
        recent_files = get_recent_curated_files(Config.SLIDING_WINDOW_HOURS)
        
        if not recent_files:
            print("No curated data found in the last 48 hours.")
        else:
            print(f"Found {len(recent_files)} curated days in last {Config.SLIDING_WINDOW_HOURS} hours.")
            for f in recent_files:
                date_str = os.path.splitext(os.path.basename(f))[0]
                print(f"\n=== Generating Content for {date_str} ===")
                await generator.generate_day_async(date_str)


if __name__ == "__main__":
    asyncio.run(main())
