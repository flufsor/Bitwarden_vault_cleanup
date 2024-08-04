"""Checking and cleaning a Bitwarden vault."""

from __future__ import annotations

import json
from pathlib import Path

from rich import print
from rich.prompt import Confirm

merged_items = set()


def remove_userless_item(data: dict) -> dict:
    """Remove items from the data that do not have a username."""
    for item in data["items"]:
        if "login" in item and (item["login"]["username"] is None or "username" not in item["login"]):
            print(f"Removing item with no username: \"{item['name']}\"")
            data["items"].remove(item)
    return data


def remove_passwordless_item(data: dict) -> dict:
    """Remove items from the data that do not have a password."""
    for item in data["items"]:
        if "login" in item and item["login"]["password"] is None or "password" not in item["login"]:
            print(f"Removing item with no password: \"{item["name"]}\"")
            data["items"].remove(item)
    return data


def remove_uriless_item(data: dict) -> dict:
    """Remove items from the data that do not have a URI."""
    items_to_remove = []
    for item in data["items"]:
        if "login" in item and "uris" in item["login"] and item["login"]["uris"]:
            uris = [uri for uri in item["login"]["uris"] if uri.get("uri")]
            item["login"]["uris"] = uris
            if not uris:
                items_to_remove.append(item)
        else:
            items_to_remove.append(item)

    for item in items_to_remove:
        print(f"Removing item with no valid URI: \"{item['name']}\"")
        data["items"].remove(item)

    return data


def find_items_with_duplicates(data: dict) -> list[tuple[dict, dict]]:
    """Remove duplicate items from the data."""
    return [
        (item, other_item)
        for item in data["items"]
        for other_item in data["items"]
        if item != other_item
        and item["login"]["uris"][0]["uri"] == other_item["login"]["uris"][0]["uri"]
        and item["login"]["username"] == other_item["login"]["username"]
        and item["login"]["password"] == other_item["login"]["password"]
    ]


def merge_uris_of_items(item_a: dict, item_b: dict) -> None:
    """Merge URIs of items that have the same URI."""
    if item_a["id"] not in merged_items and item_b["id"] not in merged_items:
        print(f"Found possible duplicate items: \"{item_a['name']}\" and \"{item_b["name"]}\"")
        uris_a = [uri["uri"] for uri in item_a["login"]["uris"]]
        uris_b = [uri["uri"] for uri in item_b["login"]["uris"]]
        print(f"\"{item_a['name']}\" has the following URIs: {uris_a}")
        print(f"\"{item_b['name']}\" has the following URIs: {uris_b}")

        merge_answer = Confirm.ask("Do you want to merge these items? [y/N]", default=False)
        if merge_answer:
            uris = item_a["login"]["uris"] + item_b["login"]["uris"]
            uris = list({uri["uri"]: uri for uri in uris}.values())
            item_a["login"]["uris"] = uris

            merged_items.add(item_b["id"])

            print(f"Merged item \"{item_b['name']}\" into \"{item_a['name']}\" successfully.")


if __name__ == "__main__":
    with Path("fake.json").open() as file:
        data = json.load(file)

    start_item_count = len(data["items"])
    print(f"Found {start_item_count} items. \n")

    data = remove_userless_item(data)
    print(f"Removed {start_item_count - len(data['items'])} items without a username. \n")

    cur_count = len(data["items"])
    data = remove_passwordless_item(data)
    print(f"Removed {cur_count - len(data['items'])} items without a password. \n")

    cur_count = len(data["items"])
    data = remove_uriless_item(data)
    print(f"Removed {cur_count - len(data["items"])} items without a URI. \n")

    cur_count = len(data["items"])
    items_with_duplicates = find_items_with_duplicates(data)
    for duplicate in items_with_duplicates:
        merge_uris_of_items(*duplicate)

    print(f"Ending with {len(data['items'])} of {start_item_count} items remaining.")
