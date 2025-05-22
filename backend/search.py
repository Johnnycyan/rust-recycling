# This module handles the search functionality for items in the game.
from items import get_items

def search_items(query):
    items = get_items()
    results = []

    # Search for items matching the query
    for item in items.values():
        if query.lower() in item["name"].lower() or query.lower() in item["shortname"].lower():
            results.append(item)

    return results