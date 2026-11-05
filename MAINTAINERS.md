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
| [vllm.md](vllm.md) | Manual-only native systemd vLLM service recipe |
| [roles/](roles/) | Source of truth for task order, supported settings and verification |
| [ansible.cfg](ansible.cfg) / [hosts.example.ini](hosts.example.ini) | Select ignored `./hosts` inventory / provide its public template |
| [group_vars/all.yml](group_vars/all.yml) | Default SSH user |
| [group_vars/nvidia_hosts.yml](group_vars/nvidia_hosts.yml) | Shared NVIDIA/CUDA settings mirrored by the paired manual recipe |
| `hosts` / `host_vars/` | Ignored inventory and per-host connection or package overrides |
| [.agents/skills/benchmark-report-review/](.agents/skills/benchmark-report-review/SKILL.md) | Review workflow for benchmark imports, coverage and report migrations |

Both playbooks target `nvidia_hosts`. `site.yml` applies `nvidia_driver`,
`cuda_toolkit` and `nvidia_container_toolkit` in that order. Container Toolkit is
optional in the manual but included in `site.yml` by default. Cleanup runs only
through the separate `cleanup.yml` playbook.

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

## Recipe Mappings

Manual recipes and roles share settings, installation order and the final result.
Each included manual operation maps to its task through stable `ops-step` IDs and
`ansible_task` names; grouped cells may map to several tasks. Validation and
check-mode helpers may remain Ansible-only.

`vllm.md` has no paired role. Preserve it as the operator contract if automation
is requested, using the same logical steps.

## Verification

Manual recipes retain essential safeguards and final verification; roles also
handle prerequisite validation, idempotence and check mode. A check-mode preview
does not establish a working installation. Report a deployment as validated only
after the relevant runtime checks and an unchanged rerun.
