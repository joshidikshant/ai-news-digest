import os
import json
import glob
import time
from typing import Optional, Dict, List
from PIL import Image
import google.generativeai as genai

class Config:
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
    DATA_DIR = "data"
    # Placeholder for the Nano-Banana Pro model (Gemini/Imagen)
    MODEL_NAME = "gemini-1.5-pro-latest" 
    
class VisualsEngine:
    def __init__(self):
        self.api_ready = False
        if Config.GOOGLE_API_KEY:
            try:
                genai.configure(api_key=Config.GOOGLE_API_KEY)
                self.api_ready = True
            except Exception as e:
                print(f"Failed to configure Google AI: {e}")
        else:
            print("Warning: GOOGLE_API_KEY not set. Image generation will be skipped.")

    def generate_image(self, prompt: str, output_path: str) -> bool:
        """
        Generates an image using Nano-Banana Pro (Google GenAI)
        """
        if not self.api_ready:
            return False
            
        print(f"  🎨 Generating image for: {prompt[:50]}...")
        try:
            # Note: This is a placeholder for the actual Image Generation API call.
            # As of early 2026, the specific syntax for "Nano-Banana Pro" via Client might vary.
            # We assume a standard text-to-image interface.
            
            # Simulated call for safety if library doesn't match exactly
            # model = genai.ImageGenerationModel("imagen-3.0-generate-001")
            # response = model.generate_images(prompt=prompt, number_of_images=1)
            # response[0].save(output_path)
            
            # For now, we will fail gracefully if strictly not supported, 
            # allowing the user to provide the exact implementation details.
            print("  [Mock] Generated image would be saved to", output_path)
            return False # Returning False to not fake it until we have real API
            
        except Exception as e:
            print(f"  ❌ Generation failed: {e}")
            return False

    def optimize_source_image(self, source_path: str, output_path: str) -> bool:
        """
        Resizes and optimizes the source Discord image.
        """
        try:
            with Image.open(source_path) as img:
                # Convert to RGB (handle PNG alpha)
                if img.mode in ('RGBA', 'P'):
                    img = img.convert('RGB')
                
                # Resize if too huge (Notion limit)
                max_size = (1920, 1080)
                img.thumbnail(max_size, Image.Resampling.LANCZOS)
                
                img.save(output_path, "JPEG", quality=85)
                return True
        except Exception as e:
            print(f"  ❌ Failed to optimize source image {source_path}: {e}")
            return False

    def process_item(self, item: Dict, date_str: str) -> Dict:
        """
        Ensures item has a 'media_path' (visual).
        """
        if 'media_path' in item and os.path.exists(item['media_path']):
            # Already has media
            return item

        item_id = item.get('source', {}).get('message_id', str(int(time.time())))
        # Sanitize filename
        safe_id = "".join([c for c in item_id if c.isalnum() or c in ('-','_')])
        
        output_dir = os.path.join(Config.DATA_DIR, "media", "processed", date_str)
        os.makedirs(output_dir, exist_ok=True)
        
        media_path = os.path.join(output_dir, f"{safe_id}.jpg")
        
        # Strategy 1: Use Source Image
        source_images = item.get('source_images', [])
        if source_images:
            # Find first valid local path
            for raw_path in source_images:
                if os.path.exists(raw_path):
                    print(f"  📸 using source image for {item.get('headline', 'Untitled')}")
                    if self.optimize_source_image(raw_path, media_path):
                        item['media_path'] = media_path
                        item['media_type'] = 'source_image'
                        return item
        
        # Strategy 2: Generate Image
        # Only generate if relevance is high enough? Let's do all for now or >70
        if item.get('relevance', 0) >= 70:
            prompt = f"Editorial tech illustration for news headline: {item.get('headline')}. Context: {item.get('bullets', [''])[0]}. minimalist, high fidelity, 8k"
            if self.generate_image(prompt, media_path):
                item['media_path'] = media_path
                item['media_type'] = 'generated_image'
                return item
        
        return item

    def run(self):
        print("Starting Visuals Engine...")
        curated_files = glob.glob(os.path.join(Config.DATA_DIR, "curated", "**", "*.json"), recursive=True)
        curated_files.sort()
        
        for file_path in curated_files:
            date_str = os.path.splitext(os.path.basename(file_path))[0]
            print(f"Processing visuals for {date_str}...")
            
            with open(file_path, "r", encoding="utf-8") as f:
                items = json.load(f)
            
            modified = False
            processed_items = []
            for item in items:
                # Check if we need to process
                if 'media_path' not in item:
                    updated_item = self.process_item(item, date_str)
                    processed_items.append(updated_item)
                    if 'media_path' in updated_item:
                        modified = True
                else:
                    processed_items.append(item)
            
            if modified:
                with open(file_path, "w", encoding="utf-8") as f:
                    json.dump(processed_items, f, indent=2, ensure_ascii=False)
                print(f"  Updated visuals for {date_str}")

if __name__ == "__main__":
    engine = VisualsEngine()
    engine.run()
