# NVIDIA AI Ops

NVIDIA GPU infrastructure recipes for Ubuntu AI hosts.

This repository keeps two forms of the same operational knowledge:

- Ansible roles for repeatable, idempotent deployment.
- Markdown recipes for humans who want to read, review, and run the same steps manually.

The Markdown files are written to work well in tools such as Runme, but plain
terminal copy/paste remains valid.

## Current Recipes

| Recipe | Human doc | Automation |
|---|---|---|
| NVIDIA driver, CUDA toolkit, NVIDIA container toolkit | [`nvidia.md`](nvidia.md) | [`site.yml`](site.yml) |
| vLLM native service | [`vllm.md`](vllm.md) | not automated yet |

## Ansible Quick Start

Run Ansible from the repository root. `ansible.cfg` selects `./hosts` as the
single default inventory:

```ini
[defaults]
inventory = ./hosts
```

Create a local inventory from the example on a new checkout:

```bash
cp hosts.example.ini hosts
vim hosts
```

`hosts` and local files under `host_vars/` are gitignored. Keep real hostnames and
connection details there. `group_vars/all.yml` sets `ansible_user: ubuntu` for
every host; override it in `host_vars/<inventory_hostname>.yml` when needed:

```yaml
ansible_user: your_ssh_user
```

NVIDIA/CUDA settings live in `group_vars/nvidia_hosts.yml`. The `site.yml` playbook
targets the `nvidia_hosts` group and composes the reusable roles in `roles/`.

Set `nvidia_driver_ubuntu_version` to `2204`, `2404` (default), or `2604` for
Ubuntu 22.04, 24.04, or 26.04. Ansible checks that it matches the target host's
Ubuntu version and requires x86_64. Verified links are in [`nvidia.md`](nvidia.md).

The example targets Ubuntu 24.04 x86_64 with driver branch **615** and CUDA
Toolkit **13.4**. The driver uses `nvidia-open` plus
`nvidia-driver-pinning-615`; CUDA uses `cuda-toolkit-13-4`. Updates within these
branches remain available, while a new branch requires an explicit configuration
change. The NVIDIA repository is configured before the driver branch pin.

Run the NVIDIA deployment:

```bash
ansible-playbook site.yml --diff
```

After a driver installation or update, reboot manually and rerun the playbook to
verify the loaded driver. The playbook reports this requirement without rebooting.

## Human Recipe Quick Start

Open [`nvidia.md`](nvidia.md), review the variables, then run each shell block on
the target host. With Runme, each fenced shell block can be executed as a cell.

## Recipe Alignment

Markdown recipes and Ansible tasks use stable step IDs:

```text
nvidia.driver.prerequisites
nvidia.driver.keyring
nvidia.driver.branch_pin
nvidia.driver.install
nvidia.cuda.toolkit
nvidia.container.toolkit
```

The two paths share settings, installation order, and the expected result:

- manual recipes keep installation commands and final verification concise
- Ansible roles include full validation, runtime checks, and check-mode handling
- included manual operations map to Ansible tasks; validation-only tasks may
  remain Ansible-only

This repository intentionally does not rely on a fragile Markdown-to-Ansible
translator. Stable step IDs link the manual operations to their Ansible tasks.

## Project Rules

See [`AGENTS.md`](AGENTS.md).
