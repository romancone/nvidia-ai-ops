# Maintainer Notes

This repository is the public home for reusable NVIDIA AI host operations.

Future work should keep two operator paths with the same installation result:

- Ansible roles for repeatable deployment.
- Runme-friendly Markdown recipes for human review and manual execution.

Manual recipes keep essential safeguards and final verification. Ansible roles
also include complete validation, runtime checks, and check-mode handling.

Keep roles generic and host-agnostic. Put hostnames, users, ports, local paths,
and lab-specific choices in ignored inventory files or example variables, not in
role logic.

The Ansible project lives at the repository root:

- `ansible.cfg` selects `./hosts`; run Ansible commands from the repository root.
- `hosts.example.ini` is the public inventory template; `hosts` is the ignored
  single-file inventory for real hosts.
- `group_vars/all.yml` sets the default connection user to `ubuntu`.
- `group_vars/nvidia_hosts.yml` defines the shared NVIDIA/CUDA settings.
- `host_vars/` holds ignored per-host overrides, including non-default SSH users.
- `site.yml` targets `nvidia_hosts` and applies the reusable roles from `roles/`.

The current recipe set is intentionally small:

- `cleanup.md` pairs with `cleanup.yml` and the `nvidia_driver_cleanup` role for
  optional driver package cleanup before changing sources. It previews APT,
  rejects unrelated changes and preserves CUDA and container tooling.
- `nvidia.md` is the human-readable pair for `site.yml` and covers NVIDIA driver,
  CUDA toolkit, and NVIDIA container toolkit.
- `vllm.md` covers a native systemd vLLM service example without Docker.

Before adding automation for vLLM, preserve the existing Markdown recipe as the
operator contract and create the Ansible role against the same step structure.
