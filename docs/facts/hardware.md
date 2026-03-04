# <i class="fas fa-microchip" style="color: #E67E22"></i> Hardware Information

<div class="meta-badges">
  <span class="badge badge-category" style="background-color: #E67E22"><i class="fas fa-folder"></i> hardware</span>
  <span class="badge badge-slug"><i class="fas fa-tag"></i> hardware</span>
  <span class="badge badge-fact" style="background-color: #3498DB"><i class="fas fa-search"></i> fact</span>
</div>

## Usage

```python
from infraninja.facts import Hardware

fact = Hardware()
result = fact.execute()

if result.success:
    print(result.data)
```

---

## Description

Gather hardware information including CPUs, memory, block devices, and network devices

---

## Tags

<div class="tags-container">
  <span class="tag"><i class="fas fa-hashtag"></i> hardware</span>
  <span class="tag"><i class="fas fa-hashtag"></i> cpu</span>
  <span class="tag"><i class="fas fa-hashtag"></i> memory</span>
  <span class="tag"><i class="fas fa-hashtag"></i> network</span>
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
Gather hardware information.

Returns:
    FactResult with hardware info data
```

