"""Utility to list all available inventories and their metadata"""

import inspect
from typing import Dict, List

from infraninja.inventories.base import Inventory


def list_inventories() -> Dict[str, Dict]:
    """
    List all available inventories from the inventories module.

    Returns:
        Dict[str, Dict]: Dictionary with inventory slugs as keys and metadata as values

    Example:
        .. code:: python

            from infraninja.utils.list_inventories import list_inventories

            inventories = list_inventories()
            for slug, metadata in inventories.items():
                print(f"{slug}: {metadata['name']['en']}")
    """
    from infraninja import inventories as inventories_module

    inventories_dict = {}

    # Get all members of the inventories module
    for name, obj in inspect.getmembers(inventories_module):
        # Check if it's a class and a subclass of Inventory (but not Inventory itself)
        if (
            inspect.isclass(obj)
            and issubclass(obj, Inventory)
            and obj is not Inventory
        ):
            # Get metadata from class attributes without instantiating
            try:
                metadata = {
                    'slug': obj.slug,
                    'name': obj.name,
                    'description': obj.description,
                }
                if metadata['slug']:  # Only add if slug is defined
                    inventories_dict[metadata['slug']] = metadata
            except Exception:
                # Skip inventories that don't have required attributes
                continue

    return inventories_dict


def get_inventory_by_slug(slug: str) -> Dict:
    """
    Get metadata for a specific inventory by its slug.

    Args:
        slug: Inventory slug identifier

    Returns:
        Dict: Inventory metadata dictionary

    Raises:
        KeyError: If inventory with the given slug is not found

    Example:
        .. code:: python

            from infraninja.utils.list_inventories import get_inventory_by_slug

            jinn_metadata = get_inventory_by_slug('jinn')
            print(jinn_metadata['name']['en'])
    """
    inventories = list_inventories()
    if slug not in inventories:
        raise KeyError(f"Inventory with slug '{slug}' not found")
    return inventories[slug]


def list_inventory_names(language: str = "en") -> Dict[str, str]:
    """
    List all inventory names in a specific language.

    Args:
        language: Language code (defaults to 'en')

    Returns:
        Dict[str, str]: Dictionary with slugs as keys and localized names as values

    Example:
        .. code:: python

            from infraninja.utils.list_inventories import list_inventory_names

            names_en = list_inventory_names('en')
            names_ar = list_inventory_names('ar')
    """
    inventories = list_inventories()
    names = {}

    for slug, metadata in inventories.items():
        name_dict = metadata.get('name', {})
        names[slug] = name_dict.get(language, name_dict.get('en', ''))

    return names
