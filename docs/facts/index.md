# Facts

InfraNinja provides the following read-only fact-gathering modules:

## Standard Facts

| Name | Class | Slug | Category | Supported OS |
|------|-------|------|----------|-------------|
| [Hardware Information](hardware.md) | `Hardware` | `hardware` | hardware | 8 OS |
| [System Information](system-info.md) | `SystemInfo` | `system-info` | system | 8 OS |

## Composite Facts

Composite facts gather multiple facts in sequence and merge results.

| Name | Class | Slug | Category | Sub-Facts |
|------|-------|------|----------|----------|
| [Full System Facts](full-facts.md) | `FullFacts` | `full-facts` | system | SystemInfo, Hardware |
