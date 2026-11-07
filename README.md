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
| NVIDIA driver cleanup (optional) | [`cleanup.md`](cleanup.md) | [`cleanup.yml`](cleanup.yml) |
| NVIDIA driver, CUDA toolkit, NVIDIA container toolkit | [`nvidia.md`](nvidia.md) | [`site.yml`](site.yml) |
| vLLM native service | [`vllm.md`](vllm.md) | [`vllm.yml`](vllm.yml) |
| API benchmark client and protocol | [`benchmark.md`](benchmark.md) | [`benchmark.yml`](benchmark.yml) |

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

Select `nvidia_driver_source` in local host variables:

- `nvidia` (default): NVIDIA repository, `nvidia-open`, and branch pinning.
- `ubuntu`: Ubuntu repositories.

Package names follow `nvidia_driver_branch`. Set `nvidia_driver_module_package`
for prebuilt modules matching the host kernel, or leave it empty for DKMS.
CUDA Toolkit uses NVIDIA's repository with either driver source.

Before switching driver sources or repairing leftover driver packages, stop GPU
workloads and run the separate [`nvidia_driver_cleanup`](roles/nvidia_driver_cleanup/)
role. Select an inventory host with `--limit` and preview the plan first:

```bash
ansible-playbook cleanup.yml --limit gpu1.example.com --check --diff
ansible-playbook cleanup.yml --limit gpu1.example.com --diff
```

It purges driver packages from both sources, libraries, kernel modules, branch
pins and their package configuration. APT changes outside the selected driver
packages are rejected. CUDA Toolkit, Container Toolkit, repository keyrings and
source lists are preserved; `autoremove` is disabled. See [`cleanup.md`](cleanup.md)
for manual steps. Cleanup is optional and is not included in `site.yml`.

Run the NVIDIA deployment:

```bash
ansible-playbook site.yml --diff
```

After a driver installation or update, reboot manually and rerun the playbook to
verify the loaded driver. The playbook reports this requirement without rebooting.

## Human Recipe Quick Start

vLLM has a separate playbook, `vllm.yml`. It installs vLLM and Hugging Face CLI,
downloads the configured model and starts a local systemd service. Its settings
are in `group_vars/nvidia_hosts.yml`; optional authentication uses a token file
specified in ignored host variables. See [`vllm.md`](vllm.md) for configuration
and manual steps.

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
