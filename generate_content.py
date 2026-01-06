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

class ContentGenerator:
    def __init__(self):
        if not Config.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY environment variable not set")
        
        self.client = OpenAI(api_key=Config.OPENAI_API_KEY)
        self.config = Config.load_prompts()
        self.model = self.config['llm']['model']
        
    def generate_day(self, date_str: str):
        filepath = os.path.join(Config.DATA_DIR, "curated", f"{date_str}.json")
        if not os.path.exists(filepath):
            print(f"No curated data found for {date_str}")
            return
            
        with open(filepath, "r", encoding="utf-8") as f:
            items = json.load(f)
            
        print(f"Generating content for {len(items)} items...")
        
        output_dir = os.path.join(Config.DATA_DIR, "content", date_str)
        os.makedirs(output_dir, exist_ok=True)
        
        generated_count = 0
        for item in items:
            # Only generate for high relevance or specific flag
            if item.get('relevance', 0) < 70:
                continue
                
            drafts = self._generate_drafts(item)
            
            # Save individual drafts
            safe_title = "".join([c for c in item['headline'] if c.isalnum() or c in (' ', '-', '_')]).strip().replace(" ", "_").lower()
            filename = f"{safe_title}.md"
            filepath_out = os.path.join(output_dir, filename)
            
            if os.path.exists(filepath_out):
                print(f"Skipping existing draft: {filename}")
                continue
            
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
            
            generated_count += 1
            print(f"Generated drafts for: {item['headline']}")

    def _generate_drafts(self, item: Dict) -> Dict[str, str]:
        prompt_config = self.config['prompts']['content_generation']
        drafts = {}
        
        formats = ['twitter', 'linkedin']
        
        for fmt in formats:
            system_prompt = prompt_config[fmt]['system']
            user_prompt = f"""
Headline: {item['headline']}
Key Points:
{json.dumps(item['bullets'], indent=2)}
Hot Take: {item.get('hot_take', 'N/A')}

Draft the content now.
"""
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    temperature=0.8
                )
                drafts[fmt] = response.choices[0].message.content
            except Exception as e:
                print(f"Error generating {fmt} for {item['headline']}: {e}")
                
        return drafts

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", help="Date to generate for (YYYY-MM-DD)")
    args = parser.parse_args()
    
    generator = ContentGenerator()
    
    if args.date:
        generator.generate_day(args.date)
    else:
        # Auto-mode: Process all curated files
        curated_files = glob.glob(os.path.join(Config.DATA_DIR, "curated", "*.json"))
        curated_files.sort()
        
        if not curated_files:
            print("No curated data found.")
        else:
            print(f"Found {len(curated_files)} curated days to process.")
            for f in curated_files:
                date_str = os.path.splitext(os.path.basename(f))[0]
                print(f"\n=== Generating Content for {date_str} ===")
                generator.generate_day(date_str)
