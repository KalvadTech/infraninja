#!/usr/bin/env python3
"""Generate MkDocs documentation for InfraNinja actions and inventories.

This script performs a two-step process:
1. Extract metadata from all actions and inventories
2. Generate Markdown files following MkDocs structure
"""

import inspect
import json
import shutil
from pathlib import Path
from typing import Any, Dict, List

# Import all actions and inventories
from infraninja.actions import (
    NetdataAction,
    SSHKeysAction,
    UpdateAndUpgradeAction,
)
from infraninja.inventories import Coolify, Jinn


def get_action_classes() -> List[type]:
    """Get all action classes (excluding base Action class)."""
    return [
        NetdataAction,
        SSHKeysAction,
        UpdateAndUpgradeAction,
    ]


def get_inventory_classes() -> List[type]:
    """Get all inventory classes (excluding base Inventory class)."""
    return [
        Jinn,
        Coolify,
    ]


def extract_function_signature(func) -> Dict[str, Any]:
    """Extract function signature details including parameters and their types."""
    sig = inspect.signature(func)
    params = []

    for param_name, param in sig.parameters.items():
        if param_name in ["self", "cls", "kwargs"]:
            continue

        param_info = {
            "name": param_name,
            "type": str(param.annotation)
            if param.annotation != inspect.Parameter.empty
            else "Any",
            "default": str(param.default)
            if param.default != inspect.Parameter.empty
            else None,
            "required": param.default == inspect.Parameter.empty,
        }
        params.append(param_info)

    return {
        "name": func.__name__,
        "params": params,
        "docstring": inspect.getdoc(func) or "",
        "return_type": str(sig.return_annotation)
        if sig.return_annotation != inspect.Signature.empty
        else "Any",
    }


def extract_action_info(action_class: type) -> Dict[str, Any]:
    """Extract complete information from an action class."""
    instance = action_class()
    metadata = instance.get_metadata()

    # Get execute method signature
    execute_method = extract_function_signature(action_class.execute)

    return {
        "type": "action",
        "class_name": action_class.__name__,
        "metadata": metadata,
        "execute": execute_method,
        "docstring": inspect.getdoc(action_class) or "",
    }


def extract_inventory_info(inventory_class: type) -> Dict[str, Any]:
    """Extract complete information from an inventory class."""
    # Get class-level metadata
    metadata = {
        "slug": inventory_class.slug,
        "name": inventory_class.name,
        "description": inventory_class.description,
    }

    # Get __init__ signature
    init_method = extract_function_signature(inventory_class.__init__)

    # Get load_servers signature
    load_servers_method = extract_function_signature(inventory_class.load_servers)

    # Get get_servers signature
    get_servers_method = extract_function_signature(inventory_class.get_servers)

    return {
        "type": "inventory",
        "class_name": inventory_class.__name__,
        "metadata": metadata,
        "init": init_method,
        "load_servers": load_servers_method,
        "get_servers": get_servers_method,
        "docstring": inspect.getdoc(inventory_class) or "",
    }


def extract_all_data() -> Dict[str, List[Dict]]:
    """Step 1: Extract all metadata from actions and inventories."""
    print("Step 1: Extracting metadata...")
    print("\n=== Extracting action information ===")
    actions_data = []
    for action_class in get_action_classes():
        try:
            action_info = extract_action_info(action_class)
            actions_data.append(action_info)
            print(f"  ✓ {action_class.__name__}")
        except Exception as e:
            print(f"  ✗ {action_class.__name__}: {e}")

    print("\n=== Extracting inventory information ===")
    inventories_data = []
    for inventory_class in get_inventory_classes():
        try:
            inventory_info = extract_inventory_info(inventory_class)
            inventories_data.append(inventory_info)
            print(f"  ✓ {inventory_class.__name__}")
        except Exception as e:
            print(f"  ✗ {inventory_class.__name__}: {e}")

    return {
        "actions": actions_data,
        "inventories": inventories_data,
    }


def format_multilang(data: Dict[str, str], key: str = "Description") -> str:
    """Format multilingual data for markdown."""
    if len(data) == 1:
        return list(data.values())[0]

    result = []
    for lang, text in data.items():
        result.append(f"**{lang.upper()}**: {text}")
    return "\n\n".join(result)


def generate_action_markdown(action: Dict[str, Any]) -> str:
    """Generate markdown content for a single action."""
    metadata = action["metadata"]
    md = f"# {metadata['name'].get('en', 'Unknown')}\n\n"

    # Add multilingual names
    if len(metadata["name"]) > 1:
        md += "## Names\n\n"
        for lang, name in metadata["name"].items():
            md += f"- **{lang.upper()}**: {name}\n"
        md += "\n"

    # Slug and category
    md += f"**Slug**: `{metadata['slug']}`\n\n"
    md += f"**Category**: {metadata['category']}\n\n"

    # Description
    md += "## Description\n\n"
    md += format_multilang(metadata["description"]) + "\n\n"

    # Tags
    if metadata["tags"]:
        md += "## Tags\n\n"
        md += ", ".join([f"`{tag}`" for tag in metadata["tags"]]) + "\n\n"

    # OS Support
    if metadata["os_available"]:
        md += "## Supported Operating Systems\n\n"
        for os in metadata["os_available"]:
            md += f"- {os}\n"
        md += "\n"

    # Execute method
    execute = action["execute"]
    md += "## Execute Method\n\n"

    param_list = (
        ", ".join([p["name"] for p in execute["params"]]) if execute["params"] else ""
    )
    md += f"```python\n{execute['name']}({param_list})\n```\n\n"

    if execute["params"]:
        md += "### Parameters\n\n"
        md += "| Parameter | Type | Default | Required |\n"
        md += "|-----------|------|---------|----------|\n"
        for param in execute["params"]:
            required = "✓" if param["required"] else "✗"
            default = f"`{param['default']}`" if param["default"] else "N/A"
            md += (
                f"| `{param['name']}` | `{param['type']}` | {default} | {required} |\n"
            )
        md += "\n"

    if execute["docstring"]:
        md += "### Documentation\n\n"
        md += f"```\n{execute['docstring']}\n```\n\n"

    return md


def generate_inventory_markdown(inventory: Dict[str, Any]) -> str:
    """Generate markdown content for a single inventory."""
    metadata = inventory["metadata"]
    md = f"# {metadata['name'].get('en', 'Unknown')}\n\n"

    # Add multilingual names
    if len(metadata["name"]) > 1:
        md += "## Names\n\n"
        for lang, name in metadata["name"].items():
            md += f"- **{lang.upper()}**: {name}\n"
        md += "\n"

    # Slug
    md += f"**Slug**: `{metadata['slug']}`\n\n"

    # Description
    md += "## Description\n\n"
    md += format_multilang(metadata["description"]) + "\n\n"

    # Class docstring
    if inventory["docstring"]:
        md += f"{inventory['docstring']}\n\n"

    # __init__ method
    init = inventory["init"]
    md += "## Initialization\n\n"

    param_list = (
        ", ".join([p["name"] for p in init["params"]]) if init["params"] else ""
    )
    md += f"```python\n{inventory['class_name']}({param_list})\n```\n\n"

    if init["params"]:
        md += "### Parameters\n\n"
        md += "| Parameter | Type | Default | Required |\n"
        md += "|-----------|------|---------|----------|\n"
        for param in init["params"]:
            required = "✓" if param["required"] else "✗"
            default = f"`{param['default']}`" if param["default"] else "N/A"
            md += (
                f"| `{param['name']}` | `{param['type']}` | {default} | {required} |\n"
            )
        md += "\n"

    if init["docstring"]:
        md += "### Documentation\n\n"
        md += f"```\n{init['docstring']}\n```\n\n"

    # load_servers method
    load_servers = inventory["load_servers"]
    md += "## Load Servers\n\n"

    param_list = (
        ", ".join([p["name"] for p in load_servers["params"]])
        if load_servers["params"]
        else ""
    )
    md += f"```python\nload_servers({param_list})\n```\n\n"

    if load_servers["params"]:
        md += "### Parameters\n\n"
        md += "| Parameter | Type | Default | Required |\n"
        md += "|-----------|------|---------|----------|\n"
        for param in load_servers["params"]:
            required = "✓" if param["required"] else "✗"
            default = f"`{param['default']}`" if param["default"] else "N/A"
            md += (
                f"| `{param['name']}` | `{param['type']}` | {default} | {required} |\n"
            )
        md += "\n"

    if load_servers["docstring"]:
        md += f"```\n{load_servers['docstring']}\n```\n\n"

    # get_servers method
    get_servers = inventory["get_servers"]
    md += "## Get Servers\n\n"
    md += "```python\nget_servers()\n```\n\n"

    if get_servers["docstring"]:
        md += f"```\n{get_servers['docstring']}\n```\n\n"

    return md


def generate_mkdocs_structure(data: Dict[str, List[Dict]]) -> None:
    """Step 2: Generate MkDocs markdown files."""
    print("\nStep 2: Generating MkDocs structure...")

    # Create base docs directory
    docs_dir = Path("docs")
    docs_dir.mkdir(parents=True, exist_ok=True)

    # Clean up old generated content
    actions_dir = docs_dir / "actions"
    inventories_dir = docs_dir / "inventories"

    if actions_dir.exists():
        shutil.rmtree(actions_dir)
    if inventories_dir.exists():
        shutil.rmtree(inventories_dir)

    actions_dir.mkdir(exist_ok=True)
    inventories_dir.mkdir(exist_ok=True)

    # Generate main index.md
    print("\n=== Generating main index ===")
    index_content = """# InfraNinja Documentation

Welcome to InfraNinja - Ninja-level deployments for infrastructure automation.

## What is InfraNinja?

InfraNinja is a powerful infrastructure automation framework built on top of PyInfra. It provides:

- **Actions**: Pre-built deployment tasks for common infrastructure components
- **Inventories**: Dynamic server inventory management from various sources
- **Multilingual Support**: Full support for multiple languages (English, Arabic, French, etc.)
- **Extensible**: Easy to create custom actions and inventories

## Key Concepts

### Actions

Actions are reusable deployment tasks that can be executed across your infrastructure. Each action encapsulates:

- Installation and configuration logic
- OS-specific implementations
- Templating and customization options
- Metadata (name, description, tags, supported OS)

Browse available actions: [Actions](actions/index.md)

### Inventories

Inventories provide dynamic server management from various sources like APIs and cloud providers. Features include:

- Automatic SSH configuration generation
- Server filtering by tags/groups
- Multi-source support (Jinn, Coolify, etc.)
- Metadata extraction

Browse available inventories: [Inventories](inventories/index.md)

## Getting Started

```python
from infraninja.actions import NetdataAction
from infraninja.inventories import Jinn

# Initialize inventory
inventory = Jinn(
    api_key="your-api-key",
    groups=["production"]
)

# Deploy action
action = NetdataAction()
action.execute()
```

## Project Structure

```
infraninja/
├── actions/          # Action implementations
├── inventories/      # Inventory implementations
├── templates/        # Configuration templates
└── docs/            # Documentation (you are here!)
```

## Contributing

InfraNinja is open source and welcomes contributions! Visit our repository to learn more.
"""

    (docs_dir / "index.md").write_text(index_content)
    print("  ✓ index.md")

    # Generate actions index
    print("\n=== Generating actions ===")
    actions_index = "# Actions\n\n"
    actions_index += "InfraNinja provides the following pre-built actions:\n\n"
    actions_index += "| Name | Slug | Category | Supported OS |\n"
    actions_index += "|------|------|----------|-------------|\n"

    for action in data["actions"]:
        metadata = action["metadata"]
        name = metadata["name"].get("en", "Unknown")
        slug = metadata["slug"]
        category = metadata["category"]
        os_count = len(metadata["os_available"])

        actions_index += (
            f"| [{name}]({slug}.md) | `{slug}` | {category} | {os_count} OS |\n"
        )

        # Generate individual action page
        action_md = generate_action_markdown(action)
        (actions_dir / f"{slug}.md").write_text(action_md)
        print(f"  ✓ actions/{slug}.md")

    (actions_dir / "index.md").write_text(actions_index)
    print("  ✓ actions/index.md")

    # Generate inventories index
    print("\n=== Generating inventories ===")
    inventories_index = "# Inventories\n\n"
    inventories_index += "InfraNinja supports the following inventory sources:\n\n"
    inventories_index += "| Name | Slug | Description |\n"
    inventories_index += "|------|------|-------------|\n"

    for inventory in data["inventories"]:
        metadata = inventory["metadata"]
        name = metadata["name"].get("en", "Unknown")
        slug = metadata["slug"]
        desc = metadata["description"].get("en", "N/A")

        inventories_index += f"| [{name}]({slug}.md) | `{slug}` | {desc} |\n"

        # Generate individual inventory page
        inventory_md = generate_inventory_markdown(inventory)
        (inventories_dir / f"{slug}.md").write_text(inventory_md)
        print(f"  ✓ inventories/{slug}.md")

    (inventories_dir / "index.md").write_text(inventories_index)
    print("  ✓ inventories/index.md")

    # Save JSON data for reference
    json_file = docs_dir / "data.json"
    json_file.write_text(json.dumps(data, indent=2, default=str))
    print("\n  ✓ data.json (reference)")


def main():
    """Main function to generate documentation."""
    # Step 1: Extract data
    data = extract_all_data()

    # Step 2: Generate MkDocs structure
    generate_mkdocs_structure(data)

    print("\n✅ Documentation generation complete!")
    print("\nNext steps:")
    print("  1. Install MkDocs: pip install mkdocs mkdocs-material")
    print("  2. Serve locally: mkdocs serve")
    print("  3. Build site: mkdocs build")


if __name__ == "__main__":
    main()
