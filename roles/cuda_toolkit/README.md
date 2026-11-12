# cuda_toolkit

Install CUDA Toolkit and expose nvcc. Requires Ubuntu and configured package names, version and repository keyring.

## Configuration

Role defaults are listed below; deployment profiles and inventory can select different values.
Internal variables beginning with `_` are not operator settings.

| Variable | Role default | Purpose |
|---|---|---|
| `cuda_toolkit_home` | `""` | Installed CUDA directory |
| `cuda_toolkit_display_version` | `""` | Expected nvcc release |
| `cuda_toolkit_profile` | `/etc/profile.d/cuda.sh` | Shell environment file |
| `cuda_toolkit_keyring_url` | `""` | NVIDIA repository keyring DEB URL |
| `cuda_toolkit_packages` | `[]` | CUDA packages to install |

## Usage

From the repository root, put these values in `host_vars/<host>.yml`:

```yaml
cuda_toolkit_home: /usr/local/cuda-13.4
cuda_toolkit_display_version: "13.4"
cuda_toolkit_packages: [cuda-toolkit-13-4]
cuda_toolkit_keyring_url: "{{ nvidia_driver_keyring_url }}"
```

```bash
ansible-playbook site.yml --limit gpu1.example.com --diff
```

`site.yml` runs driver, CUDA and Container Toolkit roles in that order, using the repository package settings.

## Behavior and verification

Installs the keyring and packages, writes the shell environment and nvcc symlink, then checks compiler output. Does not start a service.

Manual recipe: [nvidia.md](../../nvidia.md)
