"""Utility to list all available actions and their metadata"""

import inspect
from pathlib import Path
from typing import Dict, List, Type

from infraninja.actions.base import Action


def list_actions() -> Dict[str, Dict]:
    """
    List all available actions from the actions module.

    Returns:
        Dict[str, Dict]: Dictionary with action slugs as keys and metadata as values

    Example:
        .. code:: python

            from infraninja.utils.list_actions import list_actions

            actions = list_actions()
            for slug, metadata in actions.items():
                print(f"{slug}: {metadata['name']['en']}")
    """
    from infraninja import actions as actions_module

    actions_dict = {}

    # Get all members of the actions module
    for name, obj in inspect.getmembers(actions_module):
        # Check if it's a class and a subclass of Action (but not Action itself)
        if (
            inspect.isclass(obj)
            and issubclass(obj, Action)
            and obj is not Action
        ):
            # Instantiate the action to get metadata
            try:
                action_instance = obj()
                metadata = action_instance.get_metadata()
                actions_dict[metadata['slug']] = metadata
            except Exception:
                # Skip actions that can't be instantiated without parameters
                continue

    return actions_dict


def list_actions_by_category() -> Dict[str, List[Dict]]:
    """
    List all available actions grouped by category.

    Returns:
        Dict[str, List[Dict]]: Dictionary with categories as keys and lists of action metadata as values

    Example:
        .. code:: python

            from infraninja.utils.list_actions import list_actions_by_category

            by_category = list_actions_by_category()
            for category, actions in by_category.items():
                print(f"{category}: {len(actions)} actions")
    """
    actions = list_actions()
    by_category = {}

    for slug, metadata in actions.items():
        category = metadata.get('category', 'uncategorized')
        if category not in by_category:
            by_category[category] = []
        by_category[category].append(metadata)

    return by_category


def list_actions_by_tag(tag: str) -> List[Dict]:
    """
    List all actions that have a specific tag.

    Args:
        tag: Tag to filter by

    Returns:
        List[Dict]: List of action metadata dictionaries that contain the specified tag

    Example:
        .. code:: python

            from infraninja.utils.list_actions import list_actions_by_tag

            monitoring_actions = list_actions_by_tag('monitoring')
            for action in monitoring_actions:
                print(action['name']['en'])
    """
    actions = list_actions()
    filtered = []

    for slug, metadata in actions.items():
        if tag in metadata.get('tags', []):
            filtered.append(metadata)

    return filtered


def list_actions_by_os(os_name: str) -> List[Dict]:
    """
    List all actions that support a specific operating system.

    Args:
        os_name: Operating system name (e.g., 'ubuntu', 'debian', 'freebsd')

    Returns:
        List[Dict]: List of action metadata dictionaries that support the specified OS

    Example:
        .. code:: python

            from infraninja.utils.list_actions import list_actions_by_os

            freebsd_actions = list_actions_by_os('freebsd')
            for action in freebsd_actions:
                print(action['name']['en'])
    """
    actions = list_actions()
    filtered = []

    for slug, metadata in actions.items():
        if os_name in metadata.get('os_available', []):
            filtered.append(metadata)

    return filtered
