import discord
import json
import os
import argparse
import yaml
from datetime import datetime, timedelta, timezone as python_timezone
from typing import List, Dict, Optional

class Config:
    """Centralized configuration"""
    TOKEN = os.getenv("DISCORD_TOKEN")
    DATA_DIR = "data"
    
    @staticmethod
    def load_servers():
        with open("config/servers.yaml", "r") as f:
            return yaml.safe_load(f)

class MessageParser:
    """Handles message parsing and formatting"""
    
    @staticmethod
    def normalize_timestamp(dt: datetime) -> str:
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    
    @staticmethod
    def parse_message(message: discord.Message) -> Dict:
        # Handle regular content
        content = message.content or ""
        
        # Handle embeds if present
        if message.embeds:
            for embed in message.embeds:
                if embed.title:
                    content += f"\n# {embed.title}"
                if embed.description:
                    content += f"\n{embed.description}"
                # Add fields if needed
                for field in embed.fields:
                    content += f"\n**{field.name}**: {field.value}"

        return {
            "id": str(message.id),
            "timestamp": MessageParser.normalize_timestamp(message.created_at),
            "content": content,
            "author": str(message.author),
            "link": message.jump_url,
            "attachments": [a.url for a in message.attachments]
        }

class DataManager:
    """Manages data storage"""
    
    def __init__(self, data_dir: str):
        self.data_dir = data_dir
    
    def save_data(self, server_name: str, date_str: str, data: List[Dict]) -> None:
        # Create directory structure: data/raw/{server_name}/
        server_dir = os.path.join(self.data_dir, "raw", server_name.lower().replace(" ", "_"))
        os.makedirs(server_dir, exist_ok=True)
        
        filename = f"{date_str}.json"
        filepath = os.path.join(server_dir, filename)
        
        # Load existing if exists to merge/dedupe
        existing_data = []
        if os.path.exists(filepath):
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    existing_data = json.load(f)
            except:
                pass
        
        # Merge and dedupe by ID
        seen_ids = {item["id"] for item in existing_data}
        merged = existing_data.copy()
        
        new_count = 0
        for item in data:
            if item["id"] not in seen_ids:
                merged.append(item)
                seen_ids.add(item["id"])
                new_count += 1
        
        # Sort by timestamp
        merged.sort(key=lambda x: x["timestamp"])
        
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(merged, f, indent=2, ensure_ascii=False)
            
        if new_count > 0:
            print(f"[{server_name}] Saved {new_count} new messages to {filepath}")

class DiscordFetcher:
    """Handles Discord interactions and message fetching"""
    
    def __init__(self, config: Config, data_manager: DataManager):
        self.config = config
        self.data_manager = data_manager
        # discord.py-self doesn't use Intents for user accounts
        self.client = discord.Client()
        self._register_events()
    
    def _register_events(self):
        @self.client.event
        async def on_ready():
            print(f'Logged in as {self.client.user}')
            await self._fetch_all()
            await self.client.close()
    
    async def _fetch_all(self):
        servers_config = self.config.load_servers()
        args = self._parse_args()
        
        end_date = datetime.now(python_timezone.utc)
        start_date = end_date - timedelta(days=args.days)
        
        print(f"Fetching messages since {start_date.strftime('%Y-%m-%d')}")

        for server in servers_config['servers']:
            server_name = server['name']
            print(f"\nScanning server: {server_name}")
            
            all_messages = []
            
            for channel_config in server.get('channels', []):
                channel_id = int(channel_config['id'])
                channel_name = channel_config['name']
                
                try:
                    channel = self.client.get_channel(channel_id)
                    if not channel:
                        # Attempt to fetch if not in cache
                        try:
                            channel = await self.client.fetch_channel(channel_id)
                        except:
                            print(f"  Cannot access channel {channel_name} ({channel_id})")
                            continue
                            
                    print(f"  Fetching {channel_name}...")
                    
                    async for msg in channel.history(limit=None, after=start_date):
                        parsed = MessageParser.parse_message(msg)
                        parsed['channel_name'] = channel_name
                        all_messages.append(parsed)
                        
                except Exception as e:
                    print(f"  Error fetching {channel_name}: {e}")
            
            if all_messages:
                # Group by date for saving
                by_date = {}
                for msg in all_messages:
                    date_str = msg['timestamp'].split(' ')[0]
                    if date_str not in by_date:
                        by_date[date_str] = []
                    by_date[date_str].append(msg)
                
                for date_str, msgs in by_date.items():
                    self.data_manager.save_data(server_name, date_str, msgs)

    def _parse_args(self) -> argparse.Namespace:
        parser = argparse.ArgumentParser(description='Fetch Discord messages')
        parser.add_argument('--days', type=int, default=1, 
                          help='Number of days to fetch history for (default: 1)')
        return parser.parse_args()
    
    def run(self):
        if not self.config.TOKEN:
            print("Error: DISCORD_TOKEN environment variable not set")
            return
        self.client.run(self.config.TOKEN)

def main():
    config = Config()
    data_manager = DataManager(config.DATA_DIR)
    fetcher = DiscordFetcher(config, data_manager)
    fetcher.run()

if __name__ == "__main__":
    main()
