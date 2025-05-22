from items import get_items
import time

def download_images():
    """
    Download images for all items in the items dictionary.
    The images are saved in a folder named 'images' with the item shortname as the filename.
    """
    import os
    import requests

    # Create the images directory if it doesn't exist
    if not os.path.exists("images"):
        os.makedirs("images")

    # Get the items data
    items = get_items()
    if isinstance(items, str):  # If an error message was returned
        print(items)
        return

    for item in items.values():
        image_url = item["icon"]
        shortname = item["shortname"]
        filename = f"images/{shortname}.png"

        # Download the image
        try:
            response = requests.get(image_url)
            response.raise_for_status()  # Raise an exception for bad status codes
            with open(filename, "wb") as f:
                f.write(response.content)
            print(f"Downloaded {filename}")
        except requests.exceptions.RequestException as e:
            print(f"Error downloading {filename}: {e}")
        
        time.sleep(0.5)  # Sleep for 1 second to avoid overwhelming the server

if __name__ == "__main__":
    download_images()
# This script downloads images for all items in the items dictionary.