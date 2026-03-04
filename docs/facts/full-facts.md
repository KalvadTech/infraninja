# <i class="fas fa-clipboard-list" style="color: #9B59B6"></i> Full System Facts

<div class="meta-badges">
  <span class="badge badge-category" style="background-color: #9B59B6"><i class="fas fa-folder"></i> system</span>
  <span class="badge badge-slug"><i class="fas fa-tag"></i> full-facts</span>
  <span class="badge badge-fact" style="background-color: #3498DB"><i class="fas fa-search"></i> fact</span>
  <span class="badge badge-composite" style="background-color: #9B59B6"><i class="fas fa-layer-group"></i> composite</span>
</div>

## Usage

```python
from infraninja.facts import FullFacts

fact = FullFacts()
result = fact.execute()

# Access merged data from all sub-facts
print(result.data)
```

---

## Description

Gather complete system and hardware information from the server

---

## Sub-Facts

This composite fact gathers the following facts in order:

| Order | Fact | Description |
|-------|------|-------------|
| 1 | `SystemInfo` | - |
| 2 | `Hardware` | - |

---

## Tags

<div class="tags-container">
  <span class="tag"><i class="fas fa-hashtag"></i> system</span>
  <span class="tag"><i class="fas fa-hashtag"></i> hardware</span>
  <span class="tag"><i class="fas fa-hashtag"></i> info</span>
  <span class="tag"><i class="fas fa-hashtag"></i> composite</span>
</div>

---

## Supported Operating Systems

<div class="os-grid">
  <div class="os-badge"><i class="fab fa-linux"></i> Alpine</div>
  <div class="os-badge"><i class="fab fa-linux"></i> Arch</div>
  <div class="os-badge"><i class="fab fa-centos"></i> Centos</div>
  <div class="os-badge"><i class="fab fa-debian"></i> Debian</div>
  <div class="os-badge"><i class="fab fa-fedora"></i> Fedora</div>
  <div class="os-badge"><i class="fab fa-freebsd"></i> Freebsd</div>
  <div class="os-badge"><i class="fab fa-redhat"></i> Rhel</div>
  <div class="os-badge"><i class="fab fa-ubuntu"></i> Ubuntu</div>
</div>

---

## Execute Method

```python
execute() -> CompositeFactResult
```

### Documentation

```
Execute all sub-facts in sequence.

Args:
    **kwargs: Dict of {FactClassName: {param: value}} for sub-fact params

Returns:
    CompositeFactResult with results from all sub-facts
```

