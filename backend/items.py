# This module handles the scraping of item data from rusthelp and stores it in a JSON file.
import json
import os
import time
import requests


def scrape_item_list():
    url = "https://rusthelp.com/downloads/admin-item-list-public.json"

    # Send HTTP request to the webpage
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Raise an exception for bad status codes
    except requests.exceptions.RequestException as e:
        return f"Error fetching the URL: {e}"

    # Parse the HTML content
    body = response.json()

    items = {}
    for item in body:
        print(item)
        if item["shortName"] not in items:
            items[item["shortName"]] = {
                "name": item["displayName"],
                "description": item["description"],
                "id": item["id"],
                "shortname": item["shortName"],
                "icon": item["iconUrl"],
                "url": f"https://rusthelp.com/items/{item['displayName'].lower().replace(' ', '-')}#recycling",
            }

    return items


def get_items():
    # Check if items.json exists and is not empty and is not older than 1 day
    try:
        with open("items.json", "r") as f:
            items = json.load(f)
            if items and (time.time() - os.path.getmtime("items.json")) < 86400:
                return items
    except (FileNotFoundError, json.JSONDecodeError):
        pass

    # If items.json does not exist or is empty, scrape the data
    items = scrape_item_list()
    if isinstance(items, str):  # If an error message was returned
        return items

    # Save the items to items.json
    with open("items.json", "w") as f:
        json.dump(items, f, indent=4)

    return items
