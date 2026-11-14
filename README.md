# NVIDIA AI Ops

NVIDIA GPU infrastructure recipes for Ubuntu AI hosts.

This repository keeps two forms of the same operational knowledge:

- Ansible roles for repeatable, idempotent deployment
- Markdown recipes for humans who want to read, review, and run the same steps manually

The Markdown files are written to work well in tools such as Runme, but plain
terminal copy/paste remains valid.

## Current Recipes

| Recipe | Human doc | Automation |
|---|---|---|
| NVIDIA driver cleanup (optional) | [`cleanup.md`](cleanup.md) | [`cleanup.yml`](cleanup.yml) |
| NVIDIA driver, CUDA toolkit, NVIDIA container toolkit | [`nvidia.md`](nvidia.md) | [`site.yml`](site.yml) |
| vLLM native service | [`vllm.md`](vllm.md) | [`vllm.yml`](vllm.yml) |
| Strata CUDA installation and profile ([benchmarks](reports/qwen38-flash-next.html)) | [`strata.md`](strata.md) / [`strata-plan.md`](strata-plan.md) | [`strata.yml`](strata.yml) |
| Strata removal | [Role settings](roles/strata_cleanup/README.md) | [`strata-cleanup.yaml`](strata-cleanup.yaml) |
| vLLM removal | [Role settings](roles/vllm_cleanup/README.md) | [`vllm-cleanup.yaml`](vllm-cleanup.yaml) |
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

- `nvidia` (default): NVIDIA repository, `nvidia-open`, and branch pinning
- `ubuntu`: Ubuntu repositories

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

## Benchmark Reports

[Model overview](reports/index.html) · [Qwen3.8 Flash-Next](reports/qwen38-flash-next.html) · [Qwen3.8 27B](reports/qwen38-27b.html)

Open the report HTML files directly in a browser. The canonical dataset is
`evaluation/benchmark-data.json`; `reports/benchmark-data.js` is a generated
copy used both on GitHub Pages and from disk. Never edit it independently.
Clean source files are in [evaluation/](evaluation/README.md). After changing the JSON:

```bash
python3 - <<'PYDATA'
import json
from pathlib import Path

data = json.loads(Path("evaluation/benchmark-data.json").read_text())
Path("reports/benchmark-data.js").write_text(
    "// Generated from evaluation/benchmark-data.json; do not edit.\n"
    "window.benchmarkDataset = "
    + json.dumps(data, ensure_ascii=False, separators=(",", ":")) + ";\n"
)
PYDATA
```

Pages regenerates the viewing copy from the canonical JSON during build.

## Inference Profiles

Choose one complete profile in `host_vars/<host>.yml` or set the shared selection
in `group_vars/nvidia_hosts.yml`:

```yaml
inference_profile: strata-qwen38-iq3s-64g
```

Run from the repository root after stopping other GPU workloads:

```bash
ansible-playbook inference.yml --limit gpu1.example.com --diff
```

| Profile | Model / engine | Host RAM | Context and cache | Status |
|---|---|---|---|---|
| [strata-qwen38-iq3s-64g](profiles/strata-qwen38-iq3s-64g.yml) | Flash-Next IQ3_S / Strata | 64 GiB | 4×256K; 8960 MiB cache; PLE RAM; 52 GiB cgroup | Measured; default selection |
| [strata-qwen38-nvfp4-64g](profiles/strata-qwen38-nvfp4-64g.yml) | Flash-Next NVFP4/GPTQ / Strata | 64 GiB | 4×256K; 5120 MiB cache; PLE SSD direct | Previous measured configuration |
| [strata-qwen38-nvfp4-128g](profiles/strata-qwen38-nvfp4-128g.yml) | Flash-Next NVFP4/GPTQ / Strata | 128 GiB | 4×256K; 24576 MiB cache; PLE RAM; 114521 MiB cgroup | Four near-Max histories restored on node3 |
| [vllm-qwen38-27b-nvfp4](profiles/vllm-qwen38-27b-nvfp4.yml) | Qwen3.8-27B NVFP4 / vLLM 0.33.0 | Existing 96 GB GPU host configuration | 256K; FP8 KV; MTP 2; max-num-seqs 64 | Preserved vLLM settings; not Flash-Next |

Strata profiles retain a 10 GiB OS reserve and prohibit process swap. Four request
slots do not guarantee four parked Max histories: the IQ3_S repeat retained and
restored two RAM histories. See the [measurements](reports/qwen38-flash-next.html#cache-8960).
The vLLM sequence limit is admission capacity, not verified Max concurrency.

Each deployable YAML is an independent model configuration, including native engine options
and environment. Switching profiles does not merge the previous model's options.
The profile values override inventory values of the same name; extra variables
(`-e`) override the profile. Keep connection details, credentials and unrelated
host settings in ignored host variables. For a persistent alternative tuning,
copy a profile to a new YAML and select its filename without `.yml`.

`inference.yml` defaults to IQ3_S when no selection is set. Existing `strata.yml`
and `vllm.yml` use the same loader, default to their own engine's profile and
reject a selection for the other engine. Strata prepares files without starting
its service; vLLM retains its existing install-and-start behavior. The selector
does not stop another engine or a manually started server. Downloads remain on disk.

The 128 GiB NVFP4 profile parks histories of at least 1024 tokens. The
[report](reports/qwen38-flash-next.html#strata-nvfp4-128g) records the hardware
and cache settings used for each measurement.

Completed tests are stored in [benchmark-data.json](evaluation/benchmark-data.json).
Clean inputs, outputs and measurement snapshots live in `evaluation/raw/`.
The [manifest](evaluation/raw-manifest.json) records original paths and SHA-256
checksums. Failed attempts, diagnostics and experiment history remain on node3.

## Role Settings

Each role documents its public variables, defaults, prerequisites and service behavior:

| Role | Settings |
|---|---|
| NVIDIA driver | [README](roles/nvidia_driver/README.md) |
| NVIDIA driver cleanup | [README](roles/nvidia_driver_cleanup/README.md) |
| CUDA Toolkit | [README](roles/cuda_toolkit/README.md) |
| NVIDIA Container Toolkit | [README](roles/nvidia_container_toolkit/README.md) |
| vLLM | [README](roles/vllm/README.md) |
| Strata | [README](roles/strata/README.md) |
| llama-benchy | [README](roles/llama_benchy/README.md) |

## Human Recipe Quick Start

vLLM has a separate playbook, `vllm.yml`. It installs vLLM and Hugging Face CLI,
downloads the configured model and starts a local systemd service. Its model settings
are in `profiles/vllm-qwen38-27b-nvfp4.yml`; optional authentication uses a token file
specified in ignored host variables. See [`vllm.md`](vllm.md) for configuration
and manual steps.

For Strata, follow [`strata.md`](strata.md): configure the model, install and
build upstream Strata, prepare weights, then create the service unit. The manual
recipe describes IQ3_S with PLE in RAM, four 256K slots and an 8960 MiB shared
cache. Service activation is optional and explicit. The paired `strata.yml`
playbook prepares the selected [profile](#inference-profiles) without starting
or enabling the service by default.

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
