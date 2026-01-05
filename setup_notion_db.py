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
        db = client.databases.retrieve(database_id=db_id)
        print(f"DB keys: {db.keys()}")
        print(f"Raw properties keys: {db.get('properties', {}).keys()}")
        
        client.databases.update(
            database_id=db_id,
            properties=properties
        )
        print("Successfully added 'Date' and 'Original Link' properties!")
        
        # Verify
        db = client.databases.retrieve(database_id=db_id)
        print(f"Raw properties keys after update: {db.get('properties', {}).keys()}")
            
    except Exception as e:
        print(f"Error updating database: {e}")

if __name__ == "__main__":
    if not os.getenv("NOTION_API_KEY") or not os.getenv("NOTION_DATABASE_ID"):
        print("Error: NOTION_API_KEY and NOTION_DATABASE_ID must be set")
        exit(1)
        
    setup_database(os.getenv("NOTION_API_KEY"), os.getenv("NOTION_DATABASE_ID"))
