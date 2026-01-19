import os
import json
import glob
import time
from typing import Optional, Dict
from openai import OpenAI
import google.generativeai as genai

class Config:
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
    DATA_DIR = "data"
    
class VideoEngine:
    def __init__(self):
        if not Config.OPENAI_API_KEY:
             raise ValueError("OPENAI_API_KEY not set")
        
        self.openai_client = OpenAI(api_key=Config.OPENAI_API_KEY)
        self.api_ready = False
        
        if Config.GOOGLE_API_KEY:
            try:
                genai.configure(api_key=Config.GOOGLE_API_KEY)
                self.api_ready = True
            except: pass
        else:
            print("Warning: GOOGLE_API_KEY not set. Video generation will be skipped.")

    def generate_script(self, item: Dict) -> str:
        """
        Generates a 30s Video Sales Letter (VSL) style script.
        """
        system_prompt = """
        You are a video script writer for 'AI News Shorts'.
        Write a 30-second script (approx 60-80 words) for a vertical video.
        Style: Fast-paced, high energy, attention-grabbing hook.
        Structure:
        1. Hook (0-3s)
        2. The News (3-20s) - What happened?
        3. The Impact (20-30s) - Why it matters? with a CTA.
        Output: Just the spoken word text. No scene directions.
        """
        
        user_prompt = f"""
        Headline: {item.get('headline')}
        Bullets: {item.get('bullets')}
        Hot Take: {item.get('hot_take')}
        """
        
        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7
            )
            return response.choices[0].message.content.strip()
        except:
            return ""

    def generate_video(self, item: Dict, script: str, output_path: str) -> bool:
        if not self.api_ready: return False
        
        print(f"  🎬 Generating Veo 3 video for: {item.get('headline')[:30]}...")
        
        # Construct Veo 3 Prompt
        # Note: Veo 3 API details are hypothetical/assumed based on PRD V2 research
        visual_prompt = f"Cinematic tech news summary, vertical 9:16. {item.get('headline')}"
        full_prompt = f"{visual_prompt}. Audio Script: '{script}'"
        
        try:
            # Placeholder for Veo 3 call
            # model = genai.GenerativeModel('veo-3')
            # video = model.generate_content(full_prompt)
            # video.save(output_path)
            
            # Since we don't have the real API, we just print what we WOULd do
            print(f"  [Mock] Generated video saved to {output_path}")
            return False 
            
        except Exception as e:
            print(f"  ❌ Video gen failed: {e}")
            return False

    def run(self):
        print("Starting Video Engine...")
        curated_files = glob.glob(os.path.join(Config.DATA_DIR, "curated", "**", "*.json"), recursive=True)
        curated_files.sort()
        
        for file_path in curated_files:
            date_str = os.path.splitext(os.path.basename(file_path))[0]
            
            with open(file_path, "r", encoding="utf-8") as f:
                items = json.load(f)
            
            modified = False
            processed_items = []
            for item in items:
                # Logic: Only generate video if high relevance and not already exists
                if (item.get('relevance', 0) >= 85 and 
                    'video_path' not in item):
                    
                    # Ensure we have a script
                    script = self.generate_script(item)
                    if script:
                        item['video_script'] = script
                        
                        item_id = item.get('source', {}).get('message_id', str(int(time.time())))
                        safe_id = "".join([c for c in item_id if c.isalnum() or c in ('-','_')])
                        
                        output_dir = os.path.join(Config.DATA_DIR, "media", "video", date_str)
                        os.makedirs(output_dir, exist_ok=True)
                        video_path = os.path.join(output_dir, f"{safe_id}.mp4")
                        
                        success = self.generate_video(item, script, video_path)
                        if success:
                            item['video_path'] = video_path
                            modified = True
                        else:
                            # Mock success for testing flow? No, keep strictly false if not generated.
                            # But implemented mock prints.
                            pass
                            
                processed_items.append(item)
            
            if modified:
                with open(file_path, "w", encoding="utf-8") as f:
                    json.dump(processed_items, f, indent=2, ensure_ascii=False)
                print(f"  Updated videos for {date_str}")

if __name__ == "__main__":
    engine = VideoEngine()
    engine.run()
