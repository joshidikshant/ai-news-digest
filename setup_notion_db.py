import os
import argparse
from notion_client import Client as NotionClient

def setup_database(api_key, db_id):
    client = NotionClient(auth=api_key)
    
    print(f"Updating database {db_id}...")
    
    properties = {
        "Date": {"date": {}},
        "Original Link": {"url": {}}
    }
    
    try:
        client.databases.update(
            database_id=db_id,
            properties=properties
        )
        print("Successfully added 'Date' and 'Original Link' properties!")
    except Exception as e:
        print(f"Error updating database: {e}")

if __name__ == "__main__":
    if not os.getenv("NOTION_API_KEY") or not os.getenv("NOTION_DATABASE_ID"):
        print("Error: NOTION_API_KEY and NOTION_DATABASE_ID must be set")
        exit(1)
        
    setup_database(os.getenv("NOTION_API_KEY"), os.getenv("NOTION_DATABASE_ID"))
