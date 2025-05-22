# This module handles the scraping of recycler data from rusthelp and returns it in a structured format.

import requests
from bs4 import BeautifulSoup
import json


def scrape_recycler_data(url):
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
    html_content = response.text
    return parse_recycler_data(html_content)

def scrape_recycler_data_all(url):
    # Send HTTP request to the webpage
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Raise an exception for bad status codes
    except requests.exceptions.RequestException as e:
        return None

    # Parse the HTML content
    html_content = response.text
    return parse_recycler_data(html_content, no_safezone=True)

def parse_recycler_data(html_content, no_safezone=False):
    soup = BeautifulSoup(html_content, "html.parser")

    # Look specifically for the recycling tab div
    recycling_tab = soup.find("div", id="recycling-tab")
    if not recycling_tab:
        return "No recycling tab found in the HTML content."

    # Find the table within the recycling tab
    table = recycling_tab.find("table")
    if not table:
        return "No recycler table found within the recycling tab."

    # Verify this is a recycling table by checking headers
    headers = [th.get_text().strip() for th in table.find_all("th")]
    if "Recycler" not in headers or "Guaranteed Output" not in headers:
        return "Table found, but it doesn't appear to be a recycler table."

    # Find all table rows (skip header row)
    rows = table.find("tbody").find_all("tr")

    result = {}

    for row in rows:
        # Extract recycler type (Safezone or Radtown)
        recycler_cell = row.find("td")
        recycler_name = recycler_cell.find("a").get_text().strip()

        if no_safezone and "Safezone" in recycler_name:
            continue

        if not no_safezone:
            # Initialize data structure for this recycler
            result[recycler_name] = {"guaranteed_output": [], "extra_chance_output": []}
        else:
            # We don't need the name of the recycler, just the items
            result = {"guaranteed_output": [], "extra_chance_output": []}

        # Extract guaranteed output items
        guaranteed_cell = recycler_cell.find_next_sibling("td")
        if guaranteed_cell:
            guaranteed_items = guaranteed_cell.find_all(
                "div", class_="relative h-fit group/popover"
            )

            for item in guaranteed_items:
                # Try to get item name from img alt attribute first
                img_tag = item.find("img")
                if img_tag and img_tag.get("alt"):
                    item_name = img_tag.get("alt")
                else:
                    # Fallback to looking for the name in the tooltip div
                    item_name_div = item.find("div", class_="absolute w-full invisible")
                    item_name = (
                        item_name_div.get_text().strip()
                        if item_name_div
                        else "Unknown Item"
                    )

                # Get quantity from the p tag
                quantity_p = item.find(
                    "p", class_="w-full font-semibold text-nowrap text-center"
                )
                quantity = "0"
                if quantity_p:
                    quantity_text = quantity_p.get_text().strip()
                    # Extract the number after the × symbol
                    if "×" in quantity_text:
                        quantity = quantity_text.split("×", 1)[1].strip()

                if not no_safezone:
                    result[recycler_name]["guaranteed_output"].append(
                        {"item": item_name, "quantity": quantity}
                    )
                else:
                    result["guaranteed_output"].append(
                        {"item": item_name, "quantity": quantity}
                    )

        # Extract extra chance output items (if they exist)
        extra_cell = (
            guaranteed_cell.find_next_sibling("td") if guaranteed_cell else None
        )
        if extra_cell:  # This column might not exist
            extra_items = extra_cell.find_all(
                "div", class_="relative h-fit group/popover"
            )

            for item in extra_items:
                # Try to get item name from img alt attribute first
                img_tag = item.find("img")
                if img_tag and img_tag.get("alt"):
                    item_name = img_tag.get("alt")
                else:
                    # Fallback to looking for the name in the tooltip div
                    item_name_div = item.find("div", class_="absolute w-full invisible")
                    item_name = (
                        item_name_div.get_text().strip()
                        if item_name_div
                        else "Unknown Item"
                    )

                # Get chance text from the p tag
                chance_p = item.find(
                    "p", class_="w-full font-semibold text-nowrap text-center"
                )
                chance_text = (
                    chance_p.get_text().strip() if chance_p else "Unknown chance"
                )

                if not no_safezone:
                    result[recycler_name]["extra_chance_output"].append(
                        {"item": item_name, "chance": chance_text}
                    )
                else:
                    result["extra_chance_output"].append(
                        {"item": item_name, "chance": chance_text}
                    )

    # If no data was found, the table might exist but not contain recycling data
    if not result:
        return "The recycling table was found but no recycling data could be extracted."

    return result


# Usage example
if __name__ == "__main__":
    url = "https://rusthelp.com/items/tactical-gloves#recycling"  # Replace with the actual URL
    recycler_data = scrape_recycler_data(url)

    # Pretty print the results
    if isinstance(recycler_data, dict):
        print(json.dumps(recycler_data, indent=2))
    else:
        print(recycler_data)  # Print error message
