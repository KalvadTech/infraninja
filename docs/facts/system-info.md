# <i class="fas fa-info-circle" style="color: #3498DB"></i> System Information

<div class="meta-badges">
  <span class="badge badge-category" style="background-color: #3498DB"><i class="fas fa-folder"></i> system</span>
  <span class="badge badge-slug"><i class="fas fa-tag"></i> system-info</span>
  <span class="badge badge-fact" style="background-color: #3498DB"><i class="fas fa-search"></i> fact</span>
</div>

## Usage

```python
from infraninja.facts import SystemInfo

fact = SystemInfo()
result = fact.execute()

if result.success:
    print(result.data)
```

---

## Description

Gather system information including OS, hostname, kernel, and architecture

---

## Tags

<div class="tags-container">
  <span class="tag"><i class="fas fa-hashtag"></i> system</span>
  <span class="tag"><i class="fas fa-hashtag"></i> os</span>
  <span class="tag"><i class="fas fa-hashtag"></i> info</span>
</div>

---

## Supported Operating Systems

<div class="os-grid">
  <div class="os-badge"><i class="fab fa-ubuntu"></i> Ubuntu</div>
  <div class="os-badge"><i class="fab fa-debian"></i> Debian</div>
  <div class="os-badge"><i class="fab fa-linux"></i> Alpine</div>
  <div class="os-badge"><i class="fab fa-freebsd"></i> Freebsd</div>
  <div class="os-badge"><i class="fab fa-redhat"></i> Rhel</div>
  <div class="os-badge"><i class="fab fa-centos"></i> Centos</div>
  <div class="os-badge"><i class="fab fa-fedora"></i> Fedora</div>
  <div class="os-badge"><i class="fab fa-linux"></i> Arch</div>
</div>

---

## Execute Method

```python
execute() -> FactResult
```

### Documentation

```
Gather system information.

Returns:
    FactResult with system info data
```

