<div class="hero-section" markdown>

# InfraNinja

Ninja-level deployments for infrastructure automation

<div class="hero-buttons">
  <a href="actions/" class="md-button md-button--primary">Browse Actions</a>
  <a href="https://github.com/KalvadTech/infraninja" class="md-button">GitHub</a>
</div>

</div>

<div class="stats-bar">
  <div class="stat-item">
    <span class="stat-number">26</span>
    <span class="stat-label">Actions</span>
  </div>
  <div class="stat-item">
    <span class="stat-number">6</span>
    <span class="stat-label">Composites</span>
  </div>
  <div class="stat-item">
    <span class="stat-number">2</span>
    <span class="stat-label">Inventories</span>
  </div>
  <div class="stat-item">
    <span class="stat-number">3</span>
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
        SSHHardening={"permit_root_login": "no"},
    )

    for r in result.results:
        print(f"{r.action}: {'OK' if r.success else 'FAILED'}")
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
