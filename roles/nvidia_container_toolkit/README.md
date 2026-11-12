# nvidia_container_toolkit

Install NVIDIA Container Toolkit. Docker must be installed when Docker runtime configuration is enabled.

## Configuration

Role defaults are listed below; deployment profiles and inventory can select different values.
Internal variables beginning with `_` are not operator settings.

| Variable | Role default | Purpose |
|---|---|---|
| `nvidia_container_toolkit_keyring` | `/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg` | Repository signing key path |
| `nvidia_container_toolkit_source` | `/etc/apt/sources.list.d/nvidia-container-toolkit.list` | APT source file |
| `nvidia_container_toolkit_packages` | `nvidia-container-toolkit` | Toolkit packages |
| `nvidia_container_toolkit_configure_docker` | `true` | Configure Docker runtime; may restart Docker |
| `nvidia_container_toolkit_docker_set_as_default` | `false` | Make NVIDIA the default Docker runtime |

## Usage

From the repository root, put these values in `host_vars/<host>.yml`:

```yaml
nvidia_container_toolkit_configure_docker: true
nvidia_container_toolkit_docker_set_as_default: false
```

```bash
ansible-playbook site.yml --limit gpu1.example.com --diff
```

`site.yml` runs driver, CUDA and Container Toolkit roles in that order, using the repository package settings.

## Behavior and verification

Installs the repository and toolkit. Docker configuration changes can restart Docker; verification checks runtime configuration. Does not run an inference workload.

Manual recipe: [nvidia.md](../../nvidia.md)
