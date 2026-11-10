# Dependency Data Model

## Locked Package

One resolved package in the lock.

| Field | Meaning |
| - | - |
| Name | Canonical package name. |
| Version | Resolved release version. |
| Source | Registry or direct source. |
| Markers | Conditions that select a package for a platform or Python version. |
| Dependencies | Other packages required by this package. |

## Export Entry

One package requirement in a generated installation export.

| Field | Meaning |
| - | - |
| Name | Package name required by the installation. |
| Version | Version selected by the lock. |
| Marker | Condition that applies the entry to a supported environment. |
| Source note | Direct or transitive dependency annotation. |
| Export | Runtime export or development export. |

## Relationships and Validation

- A lock can contain multiple package variants when markers select different versions or sources.
- Each export entry must match its locked package and preserve its applicable marker.
- The development export includes the runtime set and the development dependencies.
- The runtime export must retain all 11 existing platform markers.
