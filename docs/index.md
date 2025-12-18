# InfraNinja Documentation

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
