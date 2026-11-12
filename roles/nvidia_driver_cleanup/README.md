# nvidia_driver_cleanup

Remove installed NVIDIA driver packages separately from installation. Requires an Ubuntu APT host.

## Configuration

Role defaults are listed below; deployment profiles and inventory can select different values.
Internal variables beginning with `_` are not operator settings.

| Variable | Role default | Purpose |
|---|---|---|
| `nvidia_driver_cleanup_package_patterns` | See [defaults](defaults/main.yml) | Patterns selecting installed driver packages for removal; see defaults for full list |

## Usage

From the repository root, put these values in `host_vars/<host>.yml`:

```yaml
# No overrides needed for the default package selection
```

```bash
ansible-playbook cleanup.yml --limit gpu1.example.com --diff
```

## Behavior and verification

Discovers installed packages, previews APT removal and rejects unrelated package changes. Missing packages are skipped. Preserves CUDA, Container Toolkit and repository files; no autoremove.

Manual recipe: [cleanup.md](../../cleanup.md)
