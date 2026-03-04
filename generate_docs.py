#!/usr/bin/env python3
"""Generate MkDocs documentation for InfraNinja actions, inventories, and facts.

This script performs a two-step process:
1. Extract metadata from all actions, inventories, and facts
2. Generate Markdown files following MkDocs structure
"""
# ruff: noqa: T201

import inspect
import json
import shutil
from pathlib import Path
from typing import Any

import infraninja.actions as actions_module
import infraninja.facts as facts_module
import infraninja.inventories as inventories_module
from infraninja.actions import Action, Composite
from infraninja.facts import CompositeFact, Fact
from infraninja.inventories import Inventory


def get_action_classes() -> list[type]:
    """Get all standard action classes (excluding Composite actions) from __all__."""
    return [
        getattr(actions_module, name)
        for name in actions_module.__all__
        if isinstance(getattr(actions_module, name), type)
        and issubclass(getattr(actions_module, name), Action)
        and not issubclass(getattr(actions_module, name), Composite)
        and getattr(actions_module, name) is not Action
    ]


def get_composite_classes() -> list[type]:
    """Get all composite action classes from __all__."""
    return [
        getattr(actions_module, name)
        for name in actions_module.__all__
        if isinstance(getattr(actions_module, name), type)
        and issubclass(getattr(actions_module, name), Composite)
        and getattr(actions_module, name) is not Composite
    ]


def get_inventory_classes() -> list[type]:
    """Get all inventory classes from __all__."""
    return [
        getattr(inventories_module, name)
        for name in inventories_module.__all__
        if isinstance(getattr(inventories_module, name), type)
        and issubclass(getattr(inventories_module, name), Inventory)
        and getattr(inventories_module, name) is not Inventory
    ]


def get_fact_classes() -> list[type]:
    """Get all standard fact classes (excluding CompositeFact) from __all__."""
    return [
        getattr(facts_module, name)
        for name in facts_module.__all__
        if isinstance(getattr(facts_module, name), type)
        and issubclass(getattr(facts_module, name), Fact)
        and not issubclass(getattr(facts_module, name), CompositeFact)
        and getattr(facts_module, name) is not Fact
    ]


def get_composite_fact_classes() -> list[type]:
    """Get all composite fact classes from __all__."""
    return [
        getattr(facts_module, name)
        for name in facts_module.__all__
        if isinstance(getattr(facts_module, name), type)
        and issubclass(getattr(facts_module, name), CompositeFact)
        and getattr(facts_module, name) is not CompositeFact
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


def extract_fact_info(fact_class: type) -> dict[str, Any]:
    """Extract complete information from a fact class."""
    instance = fact_class()
    metadata = instance.get_metadata()

    execute_method = extract_function_signature(fact_class.execute)
    init_method = extract_init_signature(fact_class)
    is_composite = issubclass(fact_class, CompositeFact)

    info = {
        "type": "composite_fact" if is_composite else "fact",
        "class_name": fact_class.__name__,
        "metadata": metadata,
        "init": init_method,
        "execute": execute_method,
        "docstring": inspect.getdoc(fact_class) or "",
    }

    if is_composite:
        info["sub_facts"] = [f.__name__ for f in fact_class.facts]
        info["stop_on_failure"] = fact_class.stop_on_failure

    return info


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

    print("\n=== Extracting standard facts ===")
    facts_data = []
    for fact_class in get_fact_classes():
        try:
            fact_info = extract_fact_info(fact_class)
            facts_data.append(fact_info)
            print(f"  ✓ {fact_class.__name__}")
        except Exception as e:
            print(f"  ✗ {fact_class.__name__}: {e}")

    print("\n=== Extracting composite facts ===")
    composite_facts_data = []
    for fact_class in get_composite_fact_classes():
        try:
            fact_info = extract_fact_info(fact_class)
            composite_facts_data.append(fact_info)
            print(f"  ✓ {fact_class.__name__}")
        except Exception as e:
            print(f"  ✗ {fact_class.__name__}: {e}")

    return {
        "actions": actions_data,
        "composites": composites_data,
        "inventories": inventories_data,
        "facts": facts_data,
        "composite_facts": composite_facts_data,
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
        md += "result = setup.execute(\n"
        for sub in sub_actions[:2]:  # Show first 2 sub-actions as examples
            md += f"    {sub}={{\n"
            md += '        "param": "value",\n'
            md += "    },\n"
        md += ")\n"
        md += "```\n\n"

    # Checking results
    md += "### Checking Results\n\n```python\n"
    md += "print(f\"Success: {result.success}\")\n"
    md += "print(f\"Changed: {result.changed}\")\n\n"
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
    logo = metadata["logo"]
    logo_class = logo if logo.startswith("fas ") or logo.startswith("fab ") or logo.startswith("far ") else f"fas {logo}"
    md = f'# <i class="{logo_class}" style="color: {metadata["color"]}"></i> {title}\n\n'

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

    md += "---\n\n"

    # Description
    md += "## Description\n\n"
    md += f"{description}\n\n"

    # Sub-actions for composite
    if is_composite and "sub_actions" in action:
        md += "---\n\n"
        md += "## Sub-Actions\n\n"
        md += "This composite action executes the following actions in order:\n\n"
        md += "| Order | Action | Description |\n"
        md += "|-------|--------|-------------|\n"
        for i, sub in enumerate(action["sub_actions"], 1):
            md += f"| {i} | `{sub}` | - |\n"
        md += "\n"

    # Tags
    if metadata["tags"]:
        md += "---\n\n"
        md += "## Tags\n\n"
        md += '<div class="tags-container">\n'
        for tag in metadata["tags"]:
            md += f'  <span class="tag"><i class="fas fa-hashtag"></i> {tag}</span>\n'
        md += "</div>\n\n"

    # OS Support with icons
    if metadata["os_available"]:
        md += "---\n\n"
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

    md += "---\n\n"

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

    md += "---\n\n"

    # Description
    md += "## Description\n\n"
    md += f"{description}\n\n"

    # Class docstring
    if inventory["docstring"]:
        md += f"_{inventory['docstring']}_\n\n"

    md += "---\n\n"

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

    md += "---\n\n"

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

    md += "---\n\n"

    # get_servers method
    get_servers = inventory["get_servers"]
    md += "## Get Servers\n\n"
    md += "```python\nget_servers()\n```\n\n"

    if get_servers["docstring"]:
        md += f"```\n{get_servers['docstring']}\n```\n\n"

    return md


def generate_fact_usage_example(fact: dict[str, Any]) -> str:
    """Generate a usage example for a fact."""
    class_name = fact["class_name"]
    is_composite = fact["type"] == "composite_fact"

    md = "## Usage\n\n```python\n"
    md += f"from infraninja.facts import {class_name}\n\n"
    md += f"fact = {class_name}()\n"
    md += "result = fact.execute()\n\n"

    if is_composite:
        md += "# Access merged data from all sub-facts\n"
        md += "print(result.data)\n"
    else:
        md += "if result.success:\n"
        md += "    print(result.data)\n"

    md += "```\n\n"
    return md


def generate_fact_markdown(fact: dict[str, Any], lang: str = "en") -> str:
    """Generate markdown content for a single fact in specified language."""
    metadata = fact["metadata"]
    is_composite = fact["type"] == "composite_fact"

    title = metadata["name"].get(lang, metadata["name"].get("en", "Unknown"))
    description = metadata["description"].get(
        lang, metadata["description"].get("en", "")
    )

    logo = metadata["logo"]
    logo_class = logo if logo.startswith("fas ") or logo.startswith("fab ") or logo.startswith("far ") else f"fas {logo}"
    md = f'# <i class="{logo_class}" style="color: {metadata["color"]}"></i> {title}\n\n'

    md += '<div class="meta-badges">\n'
    md += f'  <span class="badge badge-category" style="background-color: {metadata["color"]}">'
    md += f'<i class="fas fa-folder"></i> {metadata["category"]}</span>\n'
    md += f'  <span class="badge badge-slug"><i class="fas fa-tag"></i> {metadata["slug"]}</span>\n'
    md += '  <span class="badge badge-fact" style="background-color: #3498DB">'
    md += '<i class="fas fa-search"></i> fact</span>\n'
    if is_composite:
        md += '  <span class="badge badge-composite" style="background-color: #9B59B6">'
        md += '<i class="fas fa-layer-group"></i> composite</span>\n'
    md += "</div>\n\n"

    md += generate_fact_usage_example(fact)

    md += "---\n\n"

    md += "## Description\n\n"
    md += f"{description}\n\n"

    if is_composite and "sub_facts" in fact:
        md += "---\n\n"
        md += "## Sub-Facts\n\n"
        md += "This composite fact gathers the following facts in order:\n\n"
        md += "| Order | Fact | Description |\n"
        md += "|-------|------|-------------|\n"
        for i, sub in enumerate(fact["sub_facts"], 1):
            md += f"| {i} | `{sub}` | - |\n"
        md += "\n"

    if metadata["tags"]:
        md += "---\n\n"
        md += "## Tags\n\n"
        md += '<div class="tags-container">\n'
        for tag in metadata["tags"]:
            md += f'  <span class="tag"><i class="fas fa-hashtag"></i> {tag}</span>\n'
        md += "</div>\n\n"

    if metadata["os_available"]:
        md += "---\n\n"
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

    md += "---\n\n"

    execute = fact["execute"]
    md += "## Execute Method\n\n"
    return_type = "CompositeFactResult" if is_composite else "FactResult"
    md += f"```python\nexecute() -> {return_type}\n```\n\n"

    if execute["docstring"]:
        md += "### Documentation\n\n"
        md += f"```\n{execute['docstring']}\n```\n\n"

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
    facts_dir = docs_dir / "facts"

    if actions_dir.exists():
        shutil.rmtree(actions_dir)
    if inventories_dir.exists():
        shutil.rmtree(inventories_dir)
    if facts_dir.exists():
        shutil.rmtree(facts_dir)

    actions_dir.mkdir(exist_ok=True)
    inventories_dir.mkdir(exist_ok=True)
    facts_dir.mkdir(exist_ok=True)

    # Generate main index.md
    print("\n=== Generating main index ===")

    n_actions = len(data["actions"])
    n_composites = len(data["composites"])
    n_inventories = len(data["inventories"])
    n_facts = len(data["facts"]) + len(data["composite_facts"])

    index_content = f"""<div class="hero-section" markdown>

# InfraNinja

Ninja-level deployments for infrastructure automation

<div class="hero-buttons">
  <a href="actions/" class="md-button md-button--primary">Browse Actions</a>
  <a href="https://github.com/KalvadTech/infraninja" class="md-button">GitHub</a>
</div>

</div>

<div class="stats-bar">
  <div class="stat-item">
    <span class="stat-number">{n_actions}</span>
    <span class="stat-label">Actions</span>
  </div>
  <div class="stat-item">
    <span class="stat-number">{n_composites}</span>
    <span class="stat-label">Composites</span>
  </div>
  <div class="stat-item">
    <span class="stat-number">{n_inventories}</span>
    <span class="stat-label">Inventories</span>
  </div>
  <div class="stat-item">
    <span class="stat-number">{n_facts}</span>
    <span class="stat-label">Facts</span>
  </div>
</div>

<div class="feature-grid" markdown>

<a class="feature-card" href="actions/">
  <i class="fas fa-bolt"></i>
  <h3>Actions</h3>
  <p>Pre-built deployment tasks for common infrastructure components</p>
</a>

<a class="feature-card" href="actions/#composite-actions">
  <i class="fas fa-layer-group"></i>
  <h3>Composites</h3>
  <p>Meta-actions that combine multiple actions into workflows</p>
</a>

<a class="feature-card" href="inventories/">
  <i class="fas fa-server"></i>
  <h3>Inventories</h3>
  <p>Dynamic server inventory management from various sources</p>
</a>

<a class="feature-card" href="facts/">
  <i class="fas fa-search"></i>
  <h3>Facts</h3>
  <p>Read-only modules to gather system and hardware information</p>
</a>

</div>

## Getting Started

=== "Simple Action"

    ```python
    from infraninja import UpdateAndUpgrade

    # Update system packages
    action = UpdateAndUpgrade()
    action.execute()
    ```

=== "With Inventory"

    ```python
    from infraninja import UpdateAndUpgrade
    from infraninja.inventories import Jinn

    inventory = Jinn(
        api_key="your-api-key",
        groups=["production"]
    )

    action = UpdateAndUpgrade()
    action.execute()
    ```

=== "Composite"

    ```python
    from infraninja import FullSetup

    setup = FullSetup()
    result = setup.execute(
        SSHHardening={{"permit_root_login": "no"}},
    )

    for r in result.results:
        print(f"{{r.action}}: {{'OK' if r.success else 'FAILED'}}")
    ```

=== "Gathering Facts"

    ```python
    from infraninja.facts import HardwareFact

    fact = HardwareFact()
    result = fact.execute()
    print(result.data)
    ```

!!! info "Project Structure"

    ```
    infraninja/
    ├── actions/          # Action implementations
    │   ├── base.py       # Action & Composite base classes
    │   └── ...           # Individual action modules
    ├── facts/            # Fact-gathering modules
    ├── inventories/      # Inventory implementations
    ├── security/         # Security hardening modules
    └── templates/        # Configuration templates
    ```
"""

    (docs_dir / "index.md").write_text(index_content)
    print("  ✓ index.md")

    # Generate actions index
    print("\n=== Generating actions ===")

    actions_index = "# Actions\n\n"
    actions_index += "InfraNinja provides the following pre-built actions:\n\n"

    # Standard actions as card grid
    actions_index += "## Standard Actions\n\n"
    actions_index += '<div class="item-card-grid">\n'

    for action in data["actions"]:
        metadata = action["metadata"]
        name = metadata["name"].get("en", "Unknown")
        class_name = action["class_name"]
        slug = metadata["slug"]
        category = metadata["category"]
        os_count = len(metadata["os_available"])
        desc = metadata["description"].get("en", "")
        # Truncate description
        short_desc = (desc[:100] + "...") if len(desc) > 100 else desc
        tags = metadata.get("tags", [])

        logo = metadata["logo"]
        logo_class = logo if logo.startswith("fas ") or logo.startswith("fab ") or logo.startswith("far ") else f"fas {logo}"
        actions_index += f'<a class="item-card" href="{slug}/">\n'
        actions_index += f'  <div class="item-card-header"><i class="{logo_class}"></i> <strong>{name}</strong></div>\n'
        actions_index += f'  <div class="item-card-class">{class_name}</div>\n'
        actions_index += f'  <div class="item-card-desc">{short_desc}</div>\n'
        actions_index += '  <div class="item-card-footer">\n'
        actions_index += f'    <span class="mini-badge"><i class="fas fa-folder"></i> {category}</span>\n'
        actions_index += f'    <span class="mini-badge"><i class="fab fa-linux"></i> {os_count} OS</span>\n'
        for tag in tags[:3]:
            actions_index += f'    <span class="mini-badge"><i class="fas fa-hashtag"></i> {tag}</span>\n'
        actions_index += '  </div>\n'
        actions_index += '</a>\n'

        # Generate individual action page
        action_md = generate_action_markdown(action, "en")
        (actions_dir / f"{slug}.md").write_text(action_md)
        print(f"  ✓ actions/{slug}.md")

    actions_index += '</div>\n\n'

    # Composite actions as card grid
    if data["composites"]:
        actions_index += "## Composite Actions\n\n"
        actions_index += "Composite actions execute multiple actions in sequence.\n\n"
        actions_index += '<div class="item-card-grid">\n'

        for action in data["composites"]:
            metadata = action["metadata"]
            name = metadata["name"].get("en", "Unknown")
            class_name = action["class_name"]
            slug = metadata["slug"]
            category = metadata["category"]
            sub_actions = action.get("sub_actions", [])
            desc = metadata["description"].get("en", "")
            short_desc = (desc[:100] + "...") if len(desc) > 100 else desc

            actions_index += f'<a class="item-card" href="{slug}/">\n'
            actions_index += f'  <div class="item-card-header"><i class="fas fa-layer-group"></i> <strong>{name}</strong></div>\n'
            actions_index += f'  <div class="item-card-class">{class_name}</div>\n'
            actions_index += f'  <div class="item-card-desc">{short_desc}</div>\n'
            actions_index += '  <div class="item-card-footer">\n'
            actions_index += f'    <span class="mini-badge"><i class="fas fa-folder"></i> {category}</span>\n'
            actions_index += f'    <span class="mini-badge"><i class="fas fa-layer-group"></i> {len(sub_actions)} sub-actions</span>\n'
            actions_index += '  </div>\n'
            actions_index += '</a>\n'

            # Generate individual composite action page
            action_md = generate_action_markdown(action, "en")
            (actions_dir / f"{slug}.md").write_text(action_md)
            print(f"  ✓ actions/{slug}.md (composite)")

        actions_index += '</div>\n'

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
from infraninja.actions import Composite, SSHHardening, SSHKeys

class MySetup(Composite):
    slug = "my-setup"
    name = {"en": "My Setup"}
    description = {"en": "Custom server setup"}
    category = "setup"

    actions = [
        SSHHardening,
        SSHKeys,
    ]
```
"""

    (actions_dir / "index.md").write_text(actions_index)
    print("  ✓ actions/index.md")

    # Generate inventories index
    print("\n=== Generating inventories ===")
    inventories_index = "# Inventories\n\n"
    inventories_index += "InfraNinja supports the following inventory sources:\n\n"
    inventories_index += '<div class="item-card-grid">\n'

    for inventory in data["inventories"]:
        metadata = inventory["metadata"]
        name = metadata["name"].get("en", "Unknown")
        class_name = inventory["class_name"]
        slug = metadata["slug"]
        desc = metadata["description"].get("en", "N/A")
        short_desc = (desc[:100] + "...") if len(desc) > 100 else desc

        inventories_index += f'<a class="item-card" href="{slug}/">\n'
        inventories_index += f'  <div class="item-card-header"><i class="fas fa-server"></i> <strong>{name}</strong></div>\n'
        inventories_index += f'  <div class="item-card-class">{class_name}</div>\n'
        inventories_index += f'  <div class="item-card-desc">{short_desc}</div>\n'
        inventories_index += '  <div class="item-card-footer">\n'
        inventories_index += '    <span class="mini-badge"><i class="fas fa-database"></i> inventory</span>\n'
        inventories_index += f'    <span class="mini-badge"><i class="fas fa-tag"></i> {slug}</span>\n'
        inventories_index += '  </div>\n'
        inventories_index += '</a>\n'

        # Generate individual inventory page
        inventory_md = generate_inventory_markdown(inventory, "en")
        (inventories_dir / f"{slug}.md").write_text(inventory_md)
        print(f"  ✓ inventories/{slug}.md")

    inventories_index += '</div>\n'

    (inventories_dir / "index.md").write_text(inventories_index)
    print("  ✓ inventories/index.md")

    # Generate facts index
    print("\n=== Generating facts ===")
    facts_index = "# Facts\n\n"
    facts_index += "InfraNinja provides the following read-only fact-gathering modules:\n\n"

    facts_index += "## Standard Facts\n\n"
    facts_index += '<div class="item-card-grid">\n'

    for fact in data["facts"]:
        metadata = fact["metadata"]
        name = metadata["name"].get("en", "Unknown")
        class_name = fact["class_name"]
        slug = metadata["slug"]
        category = metadata["category"]
        os_count = len(metadata["os_available"])
        desc = metadata["description"].get("en", "")
        short_desc = (desc[:100] + "...") if len(desc) > 100 else desc
        tags = metadata.get("tags", [])

        logo = metadata["logo"]
        logo_class = logo if logo.startswith("fas ") or logo.startswith("fab ") or logo.startswith("far ") else f"fas {logo}"
        facts_index += f'<a class="item-card" href="{slug}/">\n'
        facts_index += f'  <div class="item-card-header"><i class="{logo_class}"></i> <strong>{name}</strong></div>\n'
        facts_index += f'  <div class="item-card-class">{class_name}</div>\n'
        facts_index += f'  <div class="item-card-desc">{short_desc}</div>\n'
        facts_index += '  <div class="item-card-footer">\n'
        facts_index += f'    <span class="mini-badge"><i class="fas fa-folder"></i> {category}</span>\n'
        facts_index += f'    <span class="mini-badge"><i class="fab fa-linux"></i> {os_count} OS</span>\n'
        for tag in tags[:3]:
            facts_index += f'    <span class="mini-badge"><i class="fas fa-hashtag"></i> {tag}</span>\n'
        facts_index += '  </div>\n'
        facts_index += '</a>\n'

        fact_md = generate_fact_markdown(fact, "en")
        (facts_dir / f"{slug}.md").write_text(fact_md)
        print(f"  ✓ facts/{slug}.md")

    facts_index += '</div>\n\n'

    if data["composite_facts"]:
        facts_index += "## Composite Facts\n\n"
        facts_index += "Composite facts gather multiple facts in sequence and merge results.\n\n"
        facts_index += '<div class="item-card-grid">\n'

        for fact in data["composite_facts"]:
            metadata = fact["metadata"]
            name = metadata["name"].get("en", "Unknown")
            class_name = fact["class_name"]
            slug = metadata["slug"]
            category = metadata["category"]
            sub_facts = fact.get("sub_facts", [])
            desc = metadata["description"].get("en", "")
            short_desc = (desc[:100] + "...") if len(desc) > 100 else desc

            facts_index += f'<a class="item-card" href="{slug}/">\n'
            facts_index += f'  <div class="item-card-header"><i class="fas fa-layer-group"></i> <strong>{name}</strong></div>\n'
            facts_index += f'  <div class="item-card-class">{class_name}</div>\n'
            facts_index += f'  <div class="item-card-desc">{short_desc}</div>\n'
            facts_index += '  <div class="item-card-footer">\n'
            facts_index += f'    <span class="mini-badge"><i class="fas fa-folder"></i> {category}</span>\n'
            facts_index += f'    <span class="mini-badge"><i class="fas fa-layer-group"></i> {len(sub_facts)} sub-facts</span>\n'
            facts_index += '  </div>\n'
            facts_index += '</a>\n'

            fact_md = generate_fact_markdown(fact, "en")
            (facts_dir / f"{slug}.md").write_text(fact_md)
            print(f"  ✓ facts/{slug}.md (composite)")

        facts_index += '</div>\n'

    (facts_dir / "index.md").write_text(facts_index)
    print("  ✓ facts/index.md")

    # Save JSON data for reference
    json_file = docs_dir.parent / "data.json"
    json_file.write_text(json.dumps(data, indent=2, default=str))
    print("\n  ✓ data.json (reference)")

    # Generate custom CSS for styling
    css_content = """/* ── InfraNinja – Design Tokens ─────────────────────────── */
:root {
  --nin-primary: #7c3aed;
  --nin-primary-light: #a78bfa;
  --nin-primary-dark: #5b21b6;
  --nin-accent: #c084fc;
  --nin-surface: #ffffff;
  --nin-surface-alt: #f5f3ff;
  --nin-surface-raised: #ffffff;
  --nin-text: #1e1b4b;
  --nin-text-muted: #6b7280;
  --nin-border: #e5e7eb;
  --nin-shadow-sm: 0 1px 3px rgba(0,0,0,.08);
  --nin-shadow-md: 0 4px 12px rgba(0,0,0,.1);
  --nin-shadow-lg: 0 8px 24px rgba(0,0,0,.12);
  --nin-radius: 12px;
  --nin-radius-sm: 8px;
}

[data-md-color-scheme="slate"] {
  --nin-primary: #a78bfa;
  --nin-primary-light: #c4b5fd;
  --nin-primary-dark: #7c3aed;
  --nin-accent: #c084fc;
  --nin-surface: #1e1e2e;
  --nin-surface-alt: #27273a;
  --nin-surface-raised: #2a2a3d;
  --nin-text: #e2e0f0;
  --nin-text-muted: #9ca3af;
  --nin-border: #3f3f5a;
  --nin-shadow-sm: 0 1px 3px rgba(0,0,0,.3);
  --nin-shadow-md: 0 4px 12px rgba(0,0,0,.35);
  --nin-shadow-lg: 0 8px 24px rgba(0,0,0,.4);
}

/* ── Content fade-in ───────────────────────────────────── */
@keyframes fadeInUp {
  from { opacity: 0; transform: translateY(16px); }
  to   { opacity: 1; transform: translateY(0); }
}
.md-content__inner { animation: fadeInUp .4s ease-out; }

/* ── Typography ────────────────────────────────────────── */
.md-content h1 {
  font-weight: 800 !important;
  letter-spacing: -0.02em;
}
.md-content h2 {
  font-weight: 700 !important;
  padding-bottom: .35em;
  border-bottom: 2px solid var(--nin-border);
  margin-top: 2em;
}
.md-content h3 {
  font-weight: 600 !important;
  color: var(--nin-text-muted);
}

/* ── Hero Section ──────────────────────────────────────── */
.hero-section {
  background: linear-gradient(135deg, var(--nin-primary-dark) 0%, var(--nin-primary) 50%, var(--nin-accent) 100%);
  color: #fff;
  padding: 4rem 2rem;
  border-radius: var(--nin-radius);
  text-align: center;
  margin-bottom: 2rem;
}
.hero-section h1 {
  font-size: 2.8rem;
  font-weight: 800 !important;
  margin: 0 0 .5rem;
  color: #fff !important;
  border: none !important;
}
.hero-section p {
  font-size: 1.2rem;
  opacity: .9;
  max-width: 600px;
  margin: 0 auto 1.5rem;
}
.hero-buttons { display: flex; gap: 1rem; justify-content: center; flex-wrap: wrap; }
.hero-buttons .md-button {
  border-radius: var(--nin-radius-sm);
  font-weight: 600;
  padding: .65rem 1.6rem;
}

/* ── Stats Bar ─────────────────────────────────────────── */
.stats-bar {
  display: flex;
  justify-content: center;
  gap: 2rem;
  padding: 1.5rem 1rem;
  flex-wrap: wrap;
  margin-bottom: 2rem;
}
.stat-item { text-align: center; }
.stat-number {
  display: block;
  font-size: 2.2rem;
  font-weight: 800;
  color: var(--nin-primary);
  line-height: 1.1;
}
.stat-label {
  font-size: .85rem;
  color: var(--nin-text-muted);
  text-transform: uppercase;
  letter-spacing: .06em;
  font-weight: 600;
}

/* ── Feature Cards Grid ────────────────────────────────── */
.feature-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 1.25rem;
  margin: 2rem 0;
}
.feature-card {
  background: var(--nin-surface-raised);
  border: 1px solid var(--nin-border);
  border-radius: var(--nin-radius);
  padding: 1.5rem;
  text-align: center;
  box-shadow: var(--nin-shadow-sm);
  transition: transform .2s ease, box-shadow .2s ease;
  text-decoration: none !important;
  color: var(--nin-text) !important;
  display: block;
}
.feature-card:hover {
  transform: translateY(-4px);
  box-shadow: var(--nin-shadow-lg);
}
.feature-card i {
  font-size: 2rem;
  color: var(--nin-primary);
  margin-bottom: .75rem;
  display: block;
}
.feature-card h3 {
  margin: 0 0 .4rem;
  font-size: 1.05rem;
  color: var(--nin-text) !important;
  border: none !important;
  padding: 0 !important;
}
.feature-card p {
  margin: 0;
  font-size: .88rem;
  color: var(--nin-text-muted);
}

/* ── Item Cards (index pages) ──────────────────────────── */
.item-card-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 1.25rem;
  margin: 1.5rem 0;
}
.item-card {
  background: var(--nin-surface-raised);
  border: 1px solid var(--nin-border);
  border-left: 4px solid var(--nin-primary);
  border-radius: var(--nin-radius-sm);
  padding: 1.25rem 1.25rem 1rem;
  text-decoration: none !important;
  color: var(--nin-text) !important;
  display: block;
  box-shadow: var(--nin-shadow-sm);
  transition: transform .2s ease, box-shadow .2s ease;
}
.item-card:hover {
  transform: translateY(-3px);
  box-shadow: var(--nin-shadow-md);
}
.item-card-header {
  display: flex;
  align-items: center;
  gap: .6rem;
  margin-bottom: .5rem;
}
.item-card-header i {
  font-size: 1.3rem;
  color: var(--nin-primary);
}
.item-card-header strong {
  font-size: 1rem;
}
.item-card-class {
  font-size: .78rem;
  color: var(--nin-text-muted);
  font-family: 'JetBrains Mono', monospace;
}
.item-card-desc {
  font-size: .88rem;
  color: var(--nin-text-muted);
  margin: .4rem 0 .75rem;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
.item-card-footer {
  display: flex;
  gap: .4rem;
  flex-wrap: wrap;
}
.mini-badge {
  display: inline-flex;
  align-items: center;
  gap: .3rem;
  font-size: .72rem;
  padding: .2rem .55rem;
  border-radius: 10px;
  font-weight: 600;
  background: var(--nin-surface-alt);
  color: var(--nin-text-muted);
  border: 1px solid var(--nin-border);
}

/* ── Badges (detail pages) ─────────────────────────────── */
.meta-badges {
  display: flex;
  gap: .5rem;
  margin: 1rem 0;
  flex-wrap: wrap;
}
.badge {
  display: inline-flex;
  align-items: center;
  gap: .45rem;
  padding: .45rem .9rem;
  border-radius: 20px;
  font-weight: 600;
  color: #fff;
  font-size: .82rem;
  letter-spacing: .02em;
  box-shadow: var(--nin-shadow-sm);
}
.badge i { font-size: .8rem; }
.badge-slug { background-color: #64748b; }
.badge-inventory { background-color: #10b981; }
.badge-composite { background-color: #9333ea; }
.badge-fact { background-color: #3b82f6; }

/* ── Tags ──────────────────────────────────────────────── */
.tags-container {
  display: flex;
  flex-wrap: wrap;
  gap: .5rem;
  margin: 1rem 0;
}
.tag {
  display: inline-flex;
  align-items: center;
  gap: .4rem;
  background: var(--nin-surface-alt);
  color: var(--nin-text);
  padding: .35rem .75rem;
  border-radius: 15px;
  font-size: .82rem;
  font-weight: 500;
  border: 1px solid transparent;
  transition: border-color .2s;
}
.tag:hover { border-color: var(--nin-primary-light); }
.tag i { font-size: .7rem; color: var(--nin-primary); }

/* ── OS Grid ───────────────────────────────────────────── */
.os-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
  gap: .75rem;
  margin: 1rem 0;
}
.os-badge {
  display: flex;
  align-items: center;
  gap: .65rem;
  background: var(--nin-surface-raised);
  border: 1px solid var(--nin-border);
  color: var(--nin-text);
  padding: .65rem 1rem;
  border-radius: var(--nin-radius-sm);
  font-weight: 600;
  transition: transform .2s, box-shadow .2s;
  box-shadow: var(--nin-shadow-sm);
}
.os-badge:hover {
  transform: translateY(-2px);
  box-shadow: var(--nin-shadow-md);
}
.os-badge i {
  font-size: 1.4rem;
  color: var(--nin-primary);
}

/* ── Tables ────────────────────────────────────────────── */
.md-typeset table:not([class]) {
  border-collapse: collapse;
  width: 100%;
  margin: 1rem 0;
  border-radius: var(--nin-radius-sm);
  overflow: hidden;
  box-shadow: var(--nin-shadow-sm);
}
.md-typeset table:not([class]) th {
  background: var(--nin-surface-alt);
  color: var(--nin-text);
  padding: .75rem 1rem;
  text-align: left;
  font-weight: 700;
  border-bottom: 2px solid var(--nin-primary);
}
.md-typeset table:not([class]) td {
  padding: .65rem 1rem;
  border-bottom: 1px solid var(--nin-border);
}
.md-typeset table:not([class]) tr:hover td {
  background: var(--nin-surface-alt);
}

/* ── Code Blocks ───────────────────────────────────────── */
.md-typeset pre {
  border: 1px solid var(--nin-border);
  border-radius: var(--nin-radius-sm);
}

/* ── Responsive ────────────────────────────────────────── */
@media (max-width: 768px) {
  .hero-section { padding: 2.5rem 1.25rem; }
  .hero-section h1 { font-size: 1.8rem; }
  .stats-bar { gap: 1rem; }
  .stat-number { font-size: 1.6rem; }
  .feature-grid { grid-template-columns: 1fr; }
  .item-card-grid { grid-template-columns: 1fr; }
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

    nav_section += "  - Facts:\n"
    nav_section += "      - Overview: facts/index.md\n"
    if data.get("facts"):
        nav_section += "      - Standard Facts:\n"
        for fact in data["facts"]:
            name = fact["metadata"]["name"].get("en", "Unknown")
            slug = fact["metadata"]["slug"]
            nav_section += f"          - {name}: facts/{slug}.md\n"
    if data.get("composite_facts"):
        nav_section += "      - Composite Facts:\n"
        for fact in data["composite_facts"]:
            name = fact["metadata"]["name"].get("en", "Unknown")
            slug = fact["metadata"]["slug"]
            nav_section += f"          - {name}: facts/{slug}.md\n"

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
    print(f"  - {len(data['facts'])} standard facts")
    print(f"  - {len(data['composite_facts'])} composite facts")
    print("\nNext steps:")
    print("  1. Install MkDocs: pip install mkdocs mkdocs-material")
    print("  2. Serve locally: mkdocs serve")
    print("  3. Build site: mkdocs build")


if __name__ == "__main__":
    main()
