# Maintainer Notes

## Contributors

Read [AGENTS.md](AGENTS.md) for contribution rules, writing style and command
formatting. This file owns the repository layout, role behavior and recipe mappings.

## Layout and Ownership

| File | Purpose |
|---|---|
| [AGENTS.md](AGENTS.md) | Contribution rules and review guidance |
| [README.md](README.md) | Recipe index, Ansible quick start and shared configuration guidance |
| [nvidia.md](nvidia.md) / [site.yml](site.yml) | Manual and Ansible paths for NVIDIA Driver, CUDA Toolkit and Container Toolkit |
| [cleanup.md](cleanup.md) / [cleanup.yml](cleanup.yml) | Optional NVIDIA driver package cleanup |
| [vllm.md](vllm.md) / [vllm.yml](vllm.yml) | Manual and Ansible paths for native vLLM serving and Hugging Face CLI |
| [strata.md](strata.md) / [strata.yml](strata.yml) | Manual and Ansible paths for CUDA Strata preparation and opt-in serving |
| [strata-plan.md](strata-plan.md) | Final Strata profile and verification status |
| [TODO.md](TODO.md) | Temporary work notes in Russian; empty after completion |
| [benchmark.md](benchmark.md) / [benchmark.yml](benchmark.yml) | API benchmark protocol and isolated llama-benchy installation |
| [inference.yml](inference.yml) / [profiles/](profiles/) | Complete serving profiles and engine selection; planned profiles cannot deploy |
| [evaluation/benchmark-data.json](evaluation/benchmark-data.json) | Completed test records, derived timing metrics, saved functional answers and source checksums; raw evidence stays on node3 at the archive path recorded in the JSON |
| [reports/](reports/) | `index.html` compares model configurations; each model has its own page. `report.js` renders only `evaluation/benchmark-data.json`; CSS and HTML contain no measurement values. `strata.html` redirects old links |
| [roles/](roles/) | Source of truth for task order, supported settings and verification |
| [ansible.cfg](ansible.cfg) / [hosts.example.ini](hosts.example.ini) | Select ignored `./hosts` inventory / provide its public template |
| [group_vars/all.yml](group_vars/all.yml) | Default SSH user |
| [group_vars/nvidia_hosts.yml](group_vars/nvidia_hosts.yml) | GPU package settings and optional inference profile selection |
| `hosts` / `host_vars/` | Ignored inventory and per-host connection or package overrides |
| [.agents/skills/benchmark-report-review/](.agents/skills/benchmark-report-review/SKILL.md) | Review workflow for benchmark imports, coverage and report migrations |

`roles/*/README.md` lists public role defaults and behavior. Profile YAML files own
model settings; role defaults remain reusable. `inference.yml` loads one complete
profile before including its role. The engine-specific playbooks share this loader
and reject a profile for the wrong engine. Profile values take precedence over
inventory; extra variables take precedence over profiles.

All playbooks target `nvidia_hosts`. `site.yml` applies `nvidia_driver`,
`cuda_toolkit` and `nvidia_container_toolkit` in that order. Container Toolkit is
optional in the manual but included in `site.yml` by default. Cleanup runs only
through the separate `cleanup.yml` playbook. `vllm.yml` runs only the `vllm` role
and requires an already working NVIDIA driver and CUDA compiler.
`benchmark.yml` installs the API client and runner; benchmarks require an explicit run.
`strata.yml` runs only `strata`, requires a working NVIDIA driver and CUDA compiler,
and prepares one model without enabling its service by default.

## Role Behavior

- `nvidia_driver` validates settings, the target OS and conflicting driver sources.
  It installs the selected source's packages, pins the branch for NVIDIA's
  repository and verifies package state. After a manual reboot, an unchanged
  rerun checks GPU visibility and the running driver branch
- `cuda_toolkit` installs the configured toolkit, sets the shell environment,
  exposes `nvcc` and checks compiler visibility
- `nvidia_container_toolkit` installs the toolkit and optionally configures the
  Docker runtime, restarts Docker on configuration changes and verifies the runtime
- `nvidia_driver_cleanup` discovers driver packages and leftover package
  configuration, previews APT and rejects unrelated changes. It preserves CUDA,
  container tooling, repository keyrings and source lists; autoremove is disabled.
  Missing packages do not block discovery or cleanup of the remaining packages
- `vllm` installs an isolated Python environment and Hugging Face CLI, downloads
  the selected model as the login user, and manages a local systemd service.
  Server options stay in configuration. The HF token file is used for downloads
  and is not copied into the service. Verification checks CUDA access, model
  identity, configured context and a real generation request
- `llama_benchy` installs a pinned API client and the reusable
  [runner](roles/llama_benchy/files/llama-benchy-run.py). The runner saves native
  results, excludes cases with observed waiting or preemption, and requires
  a common decode interval in every measured batch. The
  [plotter](roles/llama_benchy/files/llama-benchy-plot.py) reads those results and
  counts observed SSE tokens in that common window and plots aggregate decode,
  decode per request and TTFT separately after each run
- `strata` adapts the sibling AMD role's account, source setup, preparation stamp
  and bounded service to CUDA. Upstream setup verifies pinned weights. The unit reads its model JSON directly;
  the selected profile supplies the native user_args overrides.
  Model and slot choices stay in profiles selected by inventory. Service activation is opt-in;
  enabled deployments check model identity, context and effective slots, then
  require enabled conversation cache with matching slots before real generation.
  Build the pinned upstream checkout with unmodified tracked source files.
  The AMD evaluation harness, Go dependency and NVMe tuning are not included

## Recipe Mappings

Manual recipes and roles share settings, installation order and the final result.
Each included manual operation maps to its task through stable `ops-step` IDs and
`ansible_task` names; grouped cells may map to several tasks. Validation and
check-mode helpers may remain Ansible-only.

The model-download completion marker is Ansible-only; a failed download is
resumed before the marker is written. Manual service commands restart directly;
the role restarts on managed changes and verifies the running service on reruns.

## Verification

Manual recipes retain essential safeguards and final verification; roles also
handle prerequisite validation, idempotence and check mode. A check-mode preview
does not establish a working installation. Report a deployment as validated only
after the relevant runtime checks and an unchanged rerun.
