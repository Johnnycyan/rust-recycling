# This is the main entry point for the backend application.
# It imports the necessary modules and starts the FastAPI application.

# Import necessary modules
import sys
import time
from fastapi import FastAPI
from search import search_items
from items import get_items
from recycler import scrape_recycler_data_all as get_recycler_data
from fastapi import APIRouter
import json
import os
from pathlib import Path

def create_app():
    # Create a FastAPI instance
    app = FastAPI()

    # Create a router for the API
    router = APIRouter()

    # Define the API endpoints
    @router.get("/items")
    async def items_endpoint():
        """
        Get the list of items.
        This endpoint returns a JSON object containing all items.
        """
        return get_items()

    @router.get("/search")
    async def search_endpoint(name: str):
        """
        Search for items based on the name string.
        This endpoint returns a list of items that match the query.
        Example: /search?name=wood
        """
        return search_items(name)

    @router.get("/recycler")
    async def recycler_endpoint(url: str = None, name: str = None):
        """
        Get recycling data for a specific item.
        This endpoint takes a URL as a query parameter and returns the recycling data for that item.
        Example: /recycler?url=https://rusthelp.com/items/tactical-gloves#recycling
        """
        if not url and not name:
            return {"error": "Either 'url' or 'name' must be provided."}
        if name:
            # If a name is provided, construct the URL using the name
            url = f"https://rusthelp.com/items/{name.lower().replace(' ', '-')}#recycling"
        if not url.startswith("https://rusthelp.com/items/"):
            return {"error": "Invalid URL. Must start with 'https://rusthelp.com/items/'."}
        return get_recycler_data(url)

    @router.get("/generate-recycling-data")
    async def generate_recycling_data_endpoint():
        """
        Generate recycling data for all items and save to a JSON file.
        This endpoint fetches all items, gets recycling data for each one,
        and saves the compiled data to a single JSON file.
        """
        items = get_items()
        recycling_data = {}
        start_time = time.time()
        failed = 0
        print(f"Start time: {start_time}")
        
        # Create data directory if it doesn't exist
        data_dir = Path("c:/Users/john/Documents/Coding/rust-recycling/data")
        data_dir.mkdir(exist_ok=True)
        
        # Output file path
        output_file = data_dir / "all_recycling_data.json"
        
        # Process each item to get recycling data
        for item in items.values():
            if failed > 200:
                print("Too many failures, stopping the process.")
                break
            item_name = item.get("name", "")
            if item_name:
                try:
                    # Construct URL and get recycling data
                    url = f"https://rusthelp.com/items/{item_name.lower().replace(' ', '-')}#recycling"
                    item_data = get_recycler_data(url)
                    if item_data is None:
                        failed += 1
                        continue
                    recycling_data[item_name] = item_data
                    print(f"Processed: {item_name}")
                except Exception as e:
                    failed += 1
                    print(f"Error processing {item_name}: {str(e)}")
        
        # Save data to JSON file
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(recycling_data, indent=2, fp=f)

        end_time = time.time()
        print(f"End time: {end_time}")
        
        return {
            "status": "success", 
            "message": f"Recycling data generated for {len(recycling_data)} items in {end_time - start_time:.2f} seconds.",
            "file_path": str(output_file)
        }

    # Include the router in the FastAPI app
    app.include_router(router)

    return app

def generate_recycling_data():
    """
    Generate recycling data for all items and save to a JSON file.
    This endpoint fetches all items, gets recycling data for each one,
    and saves the compiled data to a single JSON file.
    """
    items = get_items()
    recycling_data = {}
    start_time = time.time()
    failed = 0
    print(f"Start time: {start_time}")
    
    # Create data directory if it doesn't exist
    script_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(script_dir, "..", "data")
    os.makedirs(data_dir, exist_ok=True)
    
    # Output file path
    output_file = os.path.join(data_dir, "all_recycling_data.json")
    
    # Process each item to get recycling data
    for item in items.values():
        if failed > 400:
            print("Too many failures, stopping the process.")
            break
        item_name = item.get("name", "")
        if item_name:
            try:
                # Construct URL and get recycling data
                url = f"https://rusthelp.com/items/{item_name.lower().replace(' ', '-')}#recycling"
                item_data = get_recycler_data(url)
                if item_data is None:
                    failed += 1
                    continue
                recycling_data[item_name] = item_data
                print(f"Processed: {item_name}")
            except Exception as e:
                failed += 1
                print(f"Error processing {item_name}: {str(e)}")
    
    # Save data to JSON file
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(recycling_data, indent=2, fp=f)

    end_time = time.time()
    print(f"End time: {end_time}")
    
    print(f"Recycling data generated for {len(recycling_data)} items in {end_time - start_time:.2f} seconds.")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "generate-recycling-data":
        # If the script is run with the argument "generate-recycling-data", call the function directly
        generate_recycling_data()
        input("Press Enter to exit...")
        os._exit(0)
    # If the script is run without arguments, start the FastAPI app
    # Run the FastAPI app using uvicorn
    import uvicorn
    app = create_app()
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")