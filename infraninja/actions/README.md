# InfraNinja Actions

Actions are the main entry point for InfraNinja infrastructure automation. Each action represents a deployable unit with rich metadata for UI/CLI presentation.

## Action Structure

Every action inherits from the base `Action` class and defines:

- **slug**: Unique identifier (e.g., `deploy-netdata`)
- **name**: Multilingual name dictionary
- **tags**: List of searchable tags
- **category**: Action category
- **color**: Hex color code for UI
- **logo**: Font Awesome icon name
- **description**: Multilingual description

## Available Actions

### Monitoring

#### NetdataAction
- **Slug**: `deploy-netdata`
- **Category**: monitoring
- **Tags**: monitoring, observability, metrics, alerting
- **Description**: Deploy Netdata real-time monitoring platform

### Security

#### SSHKeysAction
- **Slug**: `deploy-ssh-keys`
- **Category**: security
- **Tags**: security, ssh, authentication, access-control
- **Description**: Deploy and manage SSH keys from GitHub and manual sources

### Maintenance

#### UpdateAndUpgradeAction
- **Slug**: `update-and-upgrade`
- **Category**: maintenance
- **Tags**: system, updates, packages, maintenance
- **Description**: Update repositories and upgrade system packages

## Usage Examples

### Basic Usage

```python
from infraninja import NetdataAction, SSHKeysAction, UpdateAndUpgradeAction

# Deploy Netdata monitoring
netdata = NetdataAction()
netdata.execute()

# Deploy SSH keys
ssh_keys = SSHKeysAction()
ssh_keys.execute(timeout=10, max_retries=3)

# Update and upgrade system
update = UpdateAndUpgradeAction()
update.execute()
```

### Using with PyInfra Inventory

```python
from pyinfra import inventory
from infraninja import NetdataAction

# Define your inventory
inventory.add_host(name="server1", ssh_user="root")

# Execute action
action = NetdataAction()
action.execute()
```

### Getting Action Metadata

```python
from infraninja import NetdataAction

action = NetdataAction()

# Get full metadata
metadata = action.get_metadata()
print(metadata)
# {
#     'slug': 'deploy-netdata',
#     'name': {'en': 'Deploy Netdata Monitoring', 'ar': '...', 'fr': '...'},
#     'tags': ['monitoring', 'observability', 'metrics', 'alerting'],
#     'category': 'monitoring',
#     'color': '#00AB44',
#     'logo': 'fa-chart-line',
#     'description': {...}
# }

# Get localized name
print(action.get_name('en'))  # "Deploy Netdata Monitoring"
print(action.get_name('ar'))  # Arabic translation

# Get localized description
print(action.get_description('fr'))  # French description
```

### Listing All Actions

```python
from infraninja.actions import (
    NetdataAction,
    SSHKeysAction,
    UpdateAndUpgradeAction,
)

actions = [
    NetdataAction(),
    SSHKeysAction(),
    UpdateAndUpgradeAction(),
]

# Display action catalog
for action in actions:
    print(f"{action.slug}: {action.get_name('en')}")
    print(f"  Category: {action.category}")
    print(f"  Tags: {', '.join(action.tags)}")
    print(f"  Color: {action.color}")
    print(f"  Icon: {action.logo}")
    print()
```

## Creating Custom Actions

To create a new action, inherit from the `Action` base class:

```python
from infraninja.actions.base import Action
from pyinfra.api import deploy
from pyinfra.operations import server

class CustomAction(Action):
    slug = "custom-action"
    name = {
        "en": "My Custom Action",
        "ar": "إجراء مخصص",
        "fr": "Mon action personnalisée",
    }
    tags = ["custom", "example"]
    category = "utilities"
    color = "#FF5733"
    logo = "fa-magic"
    description = {
        "en": "A custom action example",
        "ar": "مثال على إجراء مخصص",
        "fr": "Un exemple d'action personnalisée",
    }

    def execute(self, **kwargs):
        @deploy("My Custom Deployment")
        def custom_deploy():
            server.shell(
                name="Run custom command",
                commands=["echo 'Hello from custom action'"],
            )

        return custom_deploy()
```

## Action Categories

Common categories include:

- **monitoring**: Observability and monitoring tools
- **security**: Security hardening and access control
- **maintenance**: System updates and maintenance
- **deployment**: Application and service deployment
- **network**: Network configuration and management
- **storage**: Storage and backup solutions
- **database**: Database deployment and management

## Multilingual Support

Actions support multiple languages for `name` and `description` fields. Currently supported languages:

- **en**: English (required)
- **ar**: Arabic
- **fr**: French

Additional languages can be added as needed. The English translation is required and used as a fallback.

## Integration with UI/CLI

The action metadata structure is designed for easy integration with:

- **Web UIs**: Display actions with colors, icons, and localized text
- **CLI tools**: Generate interactive menus and help text
- **API endpoints**: Expose action catalogs via REST APIs
- **Documentation**: Auto-generate documentation from metadata

Example CLI integration:

```python
import sys
from infraninja.actions import NetdataAction, SSHKeysAction, UpdateAndUpgradeAction

actions_registry = {
    "netdata": NetdataAction,
    "ssh-keys": SSHKeysAction,
    "update": UpdateAndUpgradeAction,
}

if __name__ == "__main__":
    action_name = sys.argv[1] if len(sys.argv) > 1 else None

    if action_name in actions_registry:
        action = actions_registry[action_name]()
        print(f"Executing: {action.get_name('en')}")
        action.execute()
    else:
        print("Available actions:")
        for name, ActionClass in actions_registry.items():
            action = ActionClass()
            print(f"  {name}: {action.get_name('en')}")
```

## Testing Actions

```python
import pytest
from infraninja.actions.netdata import NetdataAction

def test_netdata_action_metadata():
    action = NetdataAction()

    assert action.slug == "deploy-netdata"
    assert action.category == "monitoring"
    assert "monitoring" in action.tags
    assert action.get_name('en') == "Deploy Netdata Monitoring"

    metadata = action.get_metadata()
    assert 'slug' in metadata
    assert 'name' in metadata
    assert 'en' in metadata['name']

def test_netdata_action_validation():
    # Action should validate metadata on initialization
    action = NetdataAction()
    # Should not raise any errors
    action._validate_metadata()
```
