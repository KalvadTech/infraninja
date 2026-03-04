# InfraNinja Actions

Actions are the main entry point for InfraNinja infrastructure automation. Each action represents a deployable unit with rich metadata for UI/CLI presentation.

## Action Structure

Every action inherits from the base `Action` class and defines:

- **slug**: Unique identifier (e.g., `ssh-hardening`)
- **name**: Multilingual name dictionary
- **tags**: List of searchable tags
- **category**: Action category
- **color**: Hex color code for UI
- **logo**: Font Awesome icon name
- **description**: Multilingual description

## Available Actions

### Security

#### SSHHardening
- **Slug**: `ssh-hardening`
- **Category**: security
- **Tags**: security, ssh, hardening
- **Description**: Comprehensive SSH server hardening with security best practices

#### SSHKeys
- **Slug**: `deploy-ssh-keys`
- **Category**: security
- **Tags**: security, ssh, authentication, access-control
- **Description**: Deploy and manage SSH keys from GitHub and manual sources

### Maintenance

#### UpdateAndUpgrade
- **Slug**: `update-and-upgrade`
- **Category**: maintenance
- **Tags**: system, updates, packages, maintenance
- **Description**: Update repositories and upgrade system packages

## Usage Examples

### Basic Usage

```python
from infraninja import SSHHardening, SSHKeys, UpdateAndUpgrade

# Harden SSH configuration
ssh = SSHHardening()
ssh.execute()

# Deploy SSH keys
ssh_keys = SSHKeys()
ssh_keys.execute(timeout=10, max_retries=3)

# Update and upgrade system
update = UpdateAndUpgrade()
update.execute()
```

### Using with PyInfra Inventory

```python
from pyinfra import inventory
from infraninja import SSHHardening

# Define your inventory
inventory.add_host(name="server1", ssh_user="root")

# Execute action
action = SSHHardening()
action.execute()
```

### Getting Action Metadata

```python
from infraninja import SSHHardening

action = SSHHardening()

# Get full metadata
metadata = action.get_metadata()
print(metadata)
# {
#     'slug': 'ssh-hardening',
#     'name': {'en': 'SSH Hardening', 'ar': '...', 'fr': '...'},
#     'tags': ['security', 'ssh', 'hardening'],
#     'category': 'security',
#     'color': '#E74C3C',
#     'logo': 'fa-shield',
#     'description': {...}
# }

# Get localized name
print(action.get_name('en'))  # "SSH Hardening"
print(action.get_name('ar'))  # Arabic translation

# Get localized description
print(action.get_description('fr'))  # French description
```

### Listing All Actions

```python
from infraninja.actions import (
    SSHHardening,
    SSHKeys,
    UpdateAndUpgrade,
)

actions = [
    SSHHardening(),
    SSHKeys(),
    UpdateAndUpgrade(),
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
        def custom_deploy():
            server.shell(
                name="Run custom command",
                commands=["echo 'Hello from custom action'"],
            )

        return custom_deploy()
```

## Action Categories

Common categories include:

- **security**: Security hardening and access control
- **maintenance**: System updates and maintenance
- **deployment**: Application and service deployment
- **network**: Network configuration and management
- **storage**: Storage and backup solutions
- **database**: Database deployment and management

## Multilingual Support

Actions support multiple languages for `name` and `description` fields. Currently configured languages:

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
from infraninja.actions import SSHHardening, SSHKeys, UpdateAndUpgrade

actions_registry = {
    "ssh-hardening": SSHHardening,
    "ssh-keys": SSHKeys,
    "update": UpdateAndUpgrade,
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
from infraninja.actions.ssh_hardening import SSHHardening

def test_ssh_hardening_metadata():
    action = SSHHardening()

    assert action.slug == "ssh-hardening"
    assert action.category == "security"
    assert "security" in action.tags
    assert action.get_name('en') == "SSH Hardening"

    metadata = action.get_metadata()
    assert 'slug' in metadata
    assert 'name' in metadata
    assert 'en' in metadata['name']

def test_ssh_hardening_validation():
    # Action should validate metadata on initialization
    action = SSHHardening()
    # Should not raise any errors
    action._validate_metadata()
```
