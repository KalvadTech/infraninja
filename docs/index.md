# InfraNinja Documentation

Welcome to InfraNinja - Ninja-level deployments for infrastructure automation.

## What is InfraNinja?

InfraNinja is a powerful infrastructure automation framework built on top of PyInfra. It provides:

- **Actions**: Pre-built deployment tasks for common infrastructure components
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
```

## Contributing

InfraNinja is open source and welcomes contributions! Visit our repository to learn more.
