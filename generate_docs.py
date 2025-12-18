#!/usr/bin/env python3
"""Generate MkDocs documentation for InfraNinja actions and inventories.

This script performs a two-step process:
1. Extract metadata from all actions and inventories
2. Generate Markdown files following MkDocs structure
"""
# ruff: noqa: T201

import inspect
import json
import shutil
from pathlib import Path
from typing import Any

# Import all actions and inventories
from infraninja.actions import (
    Composite,
    FullSetup,
    Netdata,
    SSHHardening,
    SSHKeys,
    UpdateAndUpgrade,
)
from infraninja.inventories import Coolify, Jinn


def get_action_classes() -> list[type]:
    """Get all standard action classes (excluding Composite actions)."""
    return [
        Netdata,
        SSHHardening,
        SSHKeys,
        UpdateAndUpgrade,
    ]


def get_composite_classes() -> list[type]:
    """Get all composite action classes."""
    return [
        FullSetup,
    ]


def get_inventory_classes() -> list[type]:
    """Get all inventory classes (excluding base Inventory class)."""
    return [
        Jinn,
        Coolify,
    ]


def extract_function_signature(func) -> dict[str, Any]:
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


def extract_init_signature(cls) -> dict[str, Any]:
    """Extract __init__ signature for classes with custom constructors."""
    if cls.__init__ is object.__init__:
        return {"name": "__init__", "params": [], "docstring": "", "return_type": "None"}
    return extract_function_signature(cls.__init__)


def extract_action_info(action_class: type) -> dict[str, Any]:
    """Extract complete information from an action class."""
    instance = action_class()
    metadata = instance.get_metadata()

    # Get execute method signature
    execute_method = extract_function_signature(action_class.execute)

    # Get __init__ signature for constructor params
    init_method = extract_init_signature(action_class)

    # Check if it's a composite action
    is_composite = issubclass(action_class, Composite)

    info = {
        "type": "composite" if is_composite else "action",
        "class_name": action_class.__name__,
        "metadata": metadata,
        "init": init_method,
        "execute": execute_method,
        "docstring": inspect.getdoc(action_class) or "",
    }

    # Add sub-actions for composite
    if is_composite:
        info["sub_actions"] = [a.__name__ for a in action_class.actions]
        info["stop_on_failure"] = action_class.stop_on_failure

    return info


def extract_inventory_info(inventory_class: type) -> dict[str, Any]:
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


def extract_all_data() -> dict[str, list[dict]]:
    """Step 1: Extract all metadata from actions and inventories."""
    print("Step 1: Extracting metadata...")

    print("\n=== Extracting standard actions ===")
    actions_data = []
    for action_class in get_action_classes():
        try:
            action_info = extract_action_info(action_class)
            actions_data.append(action_info)
            print(f"  ✓ {action_class.__name__}")
        except Exception as e:
            print(f"  ✗ {action_class.__name__}: {e}")

    print("\n=== Extracting composite actions ===")
    composites_data = []
    for action_class in get_composite_classes():
        try:
            action_info = extract_action_info(action_class)
            composites_data.append(action_info)
            print(f"  ✓ {action_class.__name__}")
        except Exception as e:
            print(f"  ✗ {action_class.__name__}: {e}")

    print("\n=== Extracting inventories ===")
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
        "composites": composites_data,
        "inventories": inventories_data,
    }


def generate_usage_example(action: dict[str, Any]) -> str:
    """Generate a usage example for an action."""
    class_name = action["class_name"]
    init_params = action.get("init", {}).get("params", [])
    exec_params = action["execute"].get("params", [])

    md = "## Usage\n\n```python\n"
    md += f"from infraninja import {class_name}\n\n"

    # Constructor with params if any
    if init_params:
        param_examples = []
        for p in init_params:
            if p["default"]:
                param_examples.append(f'{p["name"]}={p["default"]}')
            else:
                param_examples.append(f'{p["name"]}="value"')
        md += f"action = {class_name}(\n"
        for param in param_examples:
            md += f"    {param},\n"
        md += ")\n"
    else:
        md += f"action = {class_name}()\n"

    # Execute with params if any
    if exec_params:
        md += "action.execute(\n"
        for p in exec_params:
            if p["default"]:
                example_val = p["default"]
            elif "str" in p["type"].lower():
                example_val = f'"your-{p["name"]}"'
            elif "list" in p["type"].lower():
                example_val = "[]"
            elif "bool" in p["type"].lower():
                example_val = "True"
            else:
                example_val = "..."
            md += f"    {p['name']}={example_val},\n"
        md += ")\n"
    else:
        md += "action.execute()\n"

    md += "```\n\n"
    return md


def generate_composite_usage(action: dict[str, Any]) -> str:
    """Generate usage example for composite actions."""
    class_name = action["class_name"]
    sub_actions = action.get("sub_actions", [])

    md = "## Usage\n\n### Basic Usage\n\n```python\n"
    md += f"from infraninja import {class_name}\n\n"
    md += f"setup = {class_name}()\n"
    md += "result = setup.execute()\n\n"
    md += "if result.success:\n"
    md += '    print("Setup completed successfully")\n'
    md += "```\n\n"

    # With custom params
    if sub_actions:
        md += "### With Custom Parameters\n\n"
        md += "Pass parameters to specific sub-actions using their class name:\n\n"
        md += "```python\n"
        md += f"result = setup.execute(\n"
        for sub in sub_actions[:2]:  # Show first 2 sub-actions as examples
            md += f"    {sub}={{\n"
            md += f'        "param": "value",\n'
            md += f"    }},\n"
        md += ")\n"
        md += "```\n\n"

    # Checking results
    md += "### Checking Results\n\n```python\n"
    md += f"print(f\"Success: {{result.success}}\")\n"
    md += f"print(f\"Changed: {{result.changed}}\")\n\n"
    md += "for r in result.results:\n"
    md += '    status = "OK" if r.success else "FAILED"\n'
    md += '    print(f"  {r.action}: {status}")\n'
    md += "```\n\n"

    return md


def generate_action_markdown(action: dict[str, Any], lang: str = "en") -> str:
    """Generate markdown content for a single action in specified language."""
    metadata = action["metadata"]
    is_composite = action["type"] == "composite"

    # Get translated text
    title = metadata["name"].get(lang, metadata["name"].get("en", "Unknown"))
    description = metadata["description"].get(
        lang, metadata["description"].get("en", "")
    )

    # Header with icon and color styling
    md = f'# <i class="{metadata["logo"]}" style="color: {metadata["color"]}"></i> {title}\n\n'

    # Metadata badges
    md += '<div class="meta-badges">\n'
    md += f'  <span class="badge badge-category" style="background-color: {metadata["color"]}">'
    md += f'<i class="fas fa-folder"></i> {metadata["category"]}</span>\n'
    md += f'  <span class="badge badge-slug"><i class="fas fa-tag"></i> {metadata["slug"]}</span>\n'
    if is_composite:
        md += '  <span class="badge badge-composite" style="background-color: #9B59B6">'
        md += '<i class="fas fa-layer-group"></i> composite</span>\n'
    md += "</div>\n\n"

    # Usage example (before description)
    if is_composite:
        md += generate_composite_usage(action)
    else:
        md += generate_usage_example(action)

    # Description
    md += "## Description\n\n"
    md += f"{description}\n\n"

    # Sub-actions for composite
    if is_composite and "sub_actions" in action:
        md += "## Sub-Actions\n\n"
        md += "This composite action executes the following actions in order:\n\n"
        md += "| Order | Action | Description |\n"
        md += "|-------|--------|-------------|\n"
        for i, sub in enumerate(action["sub_actions"], 1):
            md += f"| {i} | `{sub}` | - |\n"
        md += "\n"

    # Tags
    if metadata["tags"]:
        md += "## Tags\n\n"
        md += '<div class="tags-container">\n'
        for tag in metadata["tags"]:
            md += f'  <span class="tag"><i class="fas fa-hashtag"></i> {tag}</span>\n'
        md += "</div>\n\n"

    # OS Support with icons
    if metadata["os_available"]:
        md += "## Supported Operating Systems\n\n"
        md += '<div class="os-grid">\n'
        os_icons = {
            "ubuntu": "fab fa-ubuntu",
            "debian": "fab fa-debian",
            "alpine": "fab fa-linux",
            "freebsd": "fab fa-freebsd",
            "rhel": "fab fa-redhat",
            "centos": "fab fa-centos",
            "fedora": "fab fa-fedora",
            "arch": "fab fa-linux",
            "opensuse": "fab fa-suse",
        }
        for os in metadata["os_available"]:
            icon = os_icons.get(os, "fab fa-linux")
            md += f'  <div class="os-badge"><i class="{icon}"></i> {os.title()}</div>\n'
        md += "</div>\n\n"

    # Constructor parameters (if any)
    init = action.get("init", {})
    if init.get("params"):
        md += "## Constructor Parameters\n\n"
        md += "| Parameter | Type | Default | Description |\n"
        md += "|-----------|------|---------|-------------|\n"
        for param in init["params"]:
            default = f"`{param['default']}`" if param["default"] else "N/A"
            md += f"| `{param['name']}` | `{param['type']}` | {default} | - |\n"
        md += "\n"

    # Execute method
    execute = action["execute"]
    md += "## Execute Method\n\n"

    param_list = (
        ", ".join([p["name"] for p in execute["params"]]) if execute["params"] else ""
    )
    return_type = "CompositeResult" if is_composite else execute.get("return_type", "Any")
    md += f"```python\nexecute({param_list}) -> {return_type}\n```\n\n"

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


def generate_inventory_markdown(inventory: dict[str, Any], lang: str = "en") -> str:
    """Generate markdown content for a single inventory in specified language."""
    metadata = inventory["metadata"]

    # Get translated text
    title = metadata["name"].get(lang, metadata["name"].get("en", "Unknown"))
    description = metadata["description"].get(
        lang, metadata["description"].get("en", "")
    )

    # Header with icon
    md = f'# <i class="fas fa-server" style="color: #48bb78"></i> {title}\n\n'

    # Metadata badges
    md += '<div class="meta-badges">\n'
    md += '  <span class="badge badge-inventory" style="background-color: #48bb78">'
    md += '<i class="fas fa-database"></i> inventory</span>\n'
    md += f'  <span class="badge badge-slug"><i class="fas fa-tag"></i> {metadata["slug"]}</span>\n'
    md += "</div>\n\n"

    # Usage example
    md += "## Usage\n\n```python\n"
    md += f"from infraninja.inventories import {inventory['class_name']}\n\n"
    md += f"inventory = {inventory['class_name']}(\n"
    md += '    api_url="https://api.example.com",\n'
    md += '    api_key="your-api-key",\n'
    md += ")\n"
    md += "servers = inventory.get_servers()\n"
    md += "```\n\n"

    # Description
    md += "## Description\n\n"
    md += f"{description}\n\n"

    # Class docstring
    if inventory["docstring"]:
        md += f"_{inventory['docstring']}_\n\n"

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


def generate_mkdocs_structure(data: dict[str, list[dict]]) -> None:
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
- **Composite Actions**: Meta-actions that combine multiple actions into workflows
- **Inventories**: Dynamic server inventory management from various sources
- **Extensible**: Easy to create custom actions and inventories

## Key Concepts

### Actions

Actions are reusable deployment tasks that can be executed across your infrastructure. Each action encapsulates:

- Installation and configuration logic
- OS-specific implementations
- Templating and customization options
- Metadata (name, description, tags, supported OS)

Browse available actions: [Actions](actions/index.md)

### Composite Actions

Composite actions group multiple actions together and execute them in sequence. They:

- Inherit all metadata capabilities from regular actions
- Auto-compute supported OS as intersection of sub-actions
- Support passing parameters to specific sub-actions
- Can stop on failure or continue execution

### Inventories

Inventories provide dynamic server management from various sources like APIs and cloud providers. Features include:

- Automatic SSH configuration generation
- Server filtering by tags/groups
- Multi-source support (Jinn, Coolify, etc.)
- Metadata extraction

Browse available inventories: [Inventories](inventories/index.md)

## Getting Started

### Simple Action

```python
from infraninja import Netdata

# Deploy Netdata monitoring
action = Netdata()
action.execute()
```

### With Inventory

```python
from infraninja import UpdateAndUpgrade
from infraninja.inventories import Jinn

# Initialize inventory
inventory = Jinn(
    api_key="your-api-key",
    groups=["production"]
)

# Deploy action
action = UpdateAndUpgrade()
action.execute()
```

### Composite Action

```python
from infraninja import FullSetup

# Execute multiple actions in sequence
setup = FullSetup()
result = setup.execute(
    SSHHardening={"permit_root_login": "no"},
    Netdata={"claim_token": "xxx"},
)

# Check results
for r in result.results:
    print(f"{r.action}: {'OK' if r.success else 'FAILED'}")
```

## Project Structure

```
infraninja/
├── actions/          # Action implementations
│   ├── base.py       # Action & Composite base classes
│   ├── netdata.py    # Netdata monitoring
│   ├── ssh_hardening.py
│   ├── ssh_keys.py
│   ├── update_and_upgrade.py
│   └── full_setup.py # Composite action example
├── inventories/      # Inventory implementations
├── security/         # Security hardening modules
└── templates/        # Configuration templates
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

    # Standard actions table
    actions_index += "## Standard Actions\n\n"
    actions_index += "| Name | Class | Slug | Category | Supported OS |\n"
    actions_index += "|------|-------|------|----------|-------------|\n"

    for action in data["actions"]:
        metadata = action["metadata"]
        name = metadata["name"].get("en", "Unknown")
        class_name = action["class_name"]
        slug = metadata["slug"]
        category = metadata["category"]
        os_count = len(metadata["os_available"])

        actions_index += f"| [{name}]({slug}.md) | `{class_name}` | `{slug}` | {category} | {os_count} OS |\n"

        # Generate individual action page
        action_md = generate_action_markdown(action, "en")
        (actions_dir / f"{slug}.md").write_text(action_md)
        print(f"  ✓ actions/{slug}.md")

    # Composite actions table
    if data["composites"]:
        actions_index += "\n## Composite Actions\n\n"
        actions_index += "Composite actions execute multiple actions in sequence.\n\n"
        actions_index += "| Name | Class | Slug | Category | Sub-Actions |\n"
        actions_index += "|------|-------|------|----------|-------------|\n"

        for action in data["composites"]:
            metadata = action["metadata"]
            name = metadata["name"].get("en", "Unknown")
            class_name = action["class_name"]
            slug = metadata["slug"]
            category = metadata["category"]
            sub_actions = ", ".join(action.get("sub_actions", []))

            actions_index += f"| [{name}]({slug}.md) | `{class_name}` | `{slug}` | {category} | {sub_actions} |\n"

            # Generate individual composite action page
            action_md = generate_action_markdown(action, "en")
            (actions_dir / f"{slug}.md").write_text(action_md)
            print(f"  ✓ actions/{slug}.md (composite)")

    # Creating custom actions section
    actions_index += """
## Creating Custom Actions

### Standard Action

```python
from infraninja.actions import Action

class MyAction(Action):
    slug = "my-action"
    name = {"en": "My Action"}
    description = {"en": "Does something useful"}
    category = "custom"
    os_available = ["ubuntu", "debian"]

    def execute(self, **kwargs):
        # Your implementation here
        pass
```

### Composite Action

```python
from infraninja.actions import Composite, Netdata, SSHHardening

class MySetup(Composite):
    slug = "my-setup"
    name = {"en": "My Setup"}
    description = {"en": "Custom server setup"}
    category = "setup"

    actions = [
        SSHHardening,
        Netdata,
    ]
```
"""

    (actions_dir / "index.md").write_text(actions_index)
    print("  ✓ actions/index.md")

    # Generate inventories index
    print("\n=== Generating inventories ===")
    inventories_index = "# Inventories\n\n"
    inventories_index += "InfraNinja supports the following inventory sources:\n\n"
    inventories_index += "| Name | Class | Slug | Description |\n"
    inventories_index += "|------|-------|------|-------------|\n"

    for inventory in data["inventories"]:
        metadata = inventory["metadata"]
        name = metadata["name"].get("en", "Unknown")
        class_name = inventory["class_name"]
        slug = metadata["slug"]
        desc = metadata["description"].get("en", "N/A")

        inventories_index += f"| [{name}]({slug}.md) | `{class_name}` | `{slug}` | {desc} |\n"

        # Generate individual inventory page
        inventory_md = generate_inventory_markdown(inventory, "en")
        (inventories_dir / f"{slug}.md").write_text(inventory_md)
        print(f"  ✓ inventories/{slug}.md")

    (inventories_dir / "index.md").write_text(inventories_index)
    print("  ✓ inventories/index.md")

    # Save JSON data for reference
    json_file = docs_dir.parent / "data.json"
    json_file.write_text(json.dumps(data, indent=2, default=str))
    print("\n  ✓ data.json (reference)")

    # Generate custom CSS for styling
    css_content = """/* Custom styling for InfraNinja documentation */

.meta-badges {
    display: flex;
    gap: 0.5rem;
    margin: 1rem 0;
    flex-wrap: wrap;
}

.badge {
    display: inline-flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.5rem 1rem;
    border-radius: 20px;
    font-weight: 600;
    color: white;
    font-size: 0.9rem;
}

.badge i {
    font-size: 0.85rem;
}

.badge-slug {
    background-color: #718096;
}

.badge-inventory {
    background-color: #48bb78;
}

.badge-composite {
    background-color: #9B59B6;
}

.tags-container {
    display: flex;
    flex-wrap: wrap;
    gap: 0.5rem;
    margin: 1rem 0;
}

.tag {
    display: inline-flex;
    align-items: center;
    gap: 0.5rem;
    background-color: #e2e8f0;
    color: #2d3748;
    padding: 0.4rem 0.8rem;
    border-radius: 15px;
    font-size: 0.85rem;
    font-weight: 500;
}

.tag i {
    font-size: 0.75rem;
    color: #667eea;
}

.os-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
    gap: 1rem;
    margin: 1rem 0;
}

.os-badge {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    padding: 0.75rem 1rem;
    border-radius: 8px;
    font-weight: 600;
    transition: transform 0.2s;
}

.os-badge:hover {
    transform: translateY(-2px);
}

.os-badge i {
    font-size: 1.5rem;
}

/* RTL support for Arabic */
html[dir="rtl"] .meta-badges,
html[dir="rtl"] .tags-container,
html[dir="rtl"] .os-badge {
    direction: rtl;
}

/* Table styling */
table {
    border-collapse: collapse;
    width: 100%;
    margin: 1rem 0;
}

table th {
    background-color: #667eea;
    color: white;
    padding: 0.75rem;
    text-align: left;
}

table td {
    padding: 0.75rem;
    border-bottom: 1px solid #e2e8f0;
}

table tr:hover {
    background-color: #f7fafc;
}

/* Code blocks */
code {
    background-color: #f7fafc;
    padding: 0.2rem 0.4rem;
    border-radius: 4px;
    font-size: 0.9em;
}
"""

    css_file = docs_dir / "stylesheets" / "extra.css"
    css_file.parent.mkdir(exist_ok=True)
    css_file.write_text(css_content)
    print("  ✓ docs/stylesheets/extra.css")


def update_mkdocs_nav(data: dict[str, list[dict]]) -> None:
    """Update mkdocs.yml navigation with all actions."""
    print("\n=== Updating mkdocs.yml navigation ===")

    mkdocs_path = Path("mkdocs.yml")
    if not mkdocs_path.exists():
        print("  ✗ mkdocs.yml not found, skipping nav update")
        return

    # Build navigation structure
    standard_actions = []
    for action in data["actions"]:
        name = action["metadata"]["name"].get("en", "Unknown")
        slug = action["metadata"]["slug"]
        standard_actions.append(f"          - {name}: actions/{slug}.md")

    composite_actions = []
    for action in data["composites"]:
        name = action["metadata"]["name"].get("en", "Unknown")
        slug = action["metadata"]["slug"]
        composite_actions.append(f"          - {name}: actions/{slug}.md")

    nav_section = """nav:
  - Home: index.md
  - Actions:
      - Overview: actions/index.md
      - Standard Actions:
"""
    nav_section += "\n".join(standard_actions) + "\n"

    if composite_actions:
        nav_section += "      - Composite Actions:\n"
        nav_section += "\n".join(composite_actions) + "\n"

    nav_section += "  - Inventories:\n"
    nav_section += "      - Overview: inventories/index.md\n"
    for inv in data["inventories"]:
        name = inv["metadata"]["name"].get("en", "Unknown")
        slug = inv["metadata"]["slug"]
        nav_section += f"      - {name}: inventories/{slug}.md\n"

    # Read and update mkdocs.yml
    content = mkdocs_path.read_text()

    # Find and replace nav section
    import re
    nav_pattern = r"nav:.*?(?=\n[a-z]|\Z)"
    new_content = re.sub(nav_pattern, nav_section.rstrip(), content, flags=re.DOTALL)

    mkdocs_path.write_text(new_content)
    print("  ✓ mkdocs.yml navigation updated")


def main():
    """Main function to generate documentation."""
    print("=" * 60)
    print("InfraNinja Documentation Generator")
    print("=" * 60)

    # Step 1: Extract data
    data = extract_all_data()

    # Step 2: Generate MkDocs structure
    generate_mkdocs_structure(data)

    # Step 3: Update mkdocs.yml navigation
    update_mkdocs_nav(data)

    print("\n" + "=" * 60)
    print("✅ Documentation generation complete!")
    print("=" * 60)
    print("\nGenerated:")
    print(f"  - {len(data['actions'])} standard actions")
    print(f"  - {len(data['composites'])} composite actions")
    print(f"  - {len(data['inventories'])} inventories")
    print("\nNext steps:")
    print("  1. Install MkDocs: pip install mkdocs mkdocs-material")
    print("  2. Serve locally: mkdocs serve")
    print("  3. Build site: mkdocs build")


if __name__ == "__main__":
    main()
