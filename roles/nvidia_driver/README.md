# nvidia_driver

Install an NVIDIA open driver from NVIDIA or Ubuntu packages. Requires Ubuntu x86_64 and matching release settings.

## Configuration

Role defaults are listed below; deployment profiles and inventory can select different values.
Internal variables beginning with `_` are not operator settings.

| Variable | Role default | Purpose |
|---|---|---|
| `nvidia_driver_ubuntu_version` | `""` | Repository release: 2204, 2404 or 2604; must match host |
| `nvidia_driver_source` | `nvidia` | Package source: nvidia or ubuntu |
| `nvidia_driver_package` | `"{{ 'nvidia-open' if nvidia_driver_source == 'nvidia' else 'nvidia-driver-' ~ nvidia_driver_branch ~ '-open' }}"` | Driver metapackage derived from source and branch |
| `nvidia_driver_module_package` | `""` | Optional Ubuntu prebuilt kernel module package; empty uses DKMS |
| `nvidia_driver_branch` | `""` | Required driver branch |
| `nvidia_driver_keyring_url` | `""` | NVIDIA repository keyring DEB URL |
| `nvidia_driver_prereq_packages` | `ca-certificates, curl, linux-headers-generic, build-essential, dkms, ubuntu-drivers-common` | Build and driver detection prerequisites |

## Usage

From the repository root, put these values in `host_vars/<host>.yml`:

```yaml
nvidia_driver_ubuntu_version: "2404"
nvidia_driver_source: nvidia
nvidia_driver_branch: "615"
```

```bash
ansible-playbook site.yml --limit gpu1.example.com --diff
```

`site.yml` runs driver, CUDA and Container Toolkit roles in that order, using the repository package settings.

## Behavior and verification

Validates OS, package source and conflicting packages, installs the driver and branch pinning, and checks the loaded driver on an unchanged rerun. Reports reboot requirements; never reboots the host.

Manual recipe: [nvidia.md](../../nvidia.md)
