# Project Rules

## Git

- Always open a feature branch for new work and propose the branch name for human confirmation before creating it.
- Never push without explicit human confirmation.
- Keep commits reviewable and scoped to one feature or cleanup.

## Writing Style

- Do not bloat comments.
- Do not write reasoning or history facts into code comments.
- Do not use ASCII decoration.
- Public docs are for humans first: concise, practical, and current.

## Recipes

- Keep Ansible roles reusable and host-agnostic.
- Align manual recipes with their Ansible roles in settings, installation order,
  and final result.
- Keep manual recipes simple. Skip redundant variable, OS, and preflight checks,
  change tracking, and check-mode reports. Retain essential safeguards and final
  verification.
- Ansible roles must include complete prerequisite and settings validation,
  runtime checks, idempotence, and check-mode handling.
- Use two-level numbering in Markdown recipes: `## 1. Role name`, then
  `### 1.1 Logical part`, `### 1.2 Logical part`, and so on.
- Match top-level numbers to the roles in playbook order. For manual-only
  recipes, use one top-level service section. Number logical parts at the
  second level.
- Combine related commands for each numbered part into one `bash` block. Use
  concise `# comments` inside the block to distinguish its operations.
- Mark optional major sections with `(Optional)` in the heading and state when
  they are needed. The optional label applies to all parts within that section;
  describe separately whether the playbook includes the role by default.
- Preserve stable `ops-step` IDs and `ansible_task` mappings for included manual
  operations, including grouped tasks. Validation-only tasks may remain
  Ansible-only.

## Ansible Layout

- Keep `ansible.cfg`, `site.yml`, `hosts.example.ini`, `group_vars/`, `host_vars/`,
  and `roles/` at the repository root.
- Use `inventory = ./hosts` in `ansible.cfg`; keep the real `hosts` file and local
  host overrides under `host_vars/` ignored by Git.
- Set the default SSH user to `ubuntu` in `group_vars/all.yml`; put host-specific
  overrides in local inventory or host variables.
- Keep NVIDIA settings in `group_vars/nvidia_hosts.yml` and target `nvidia_hosts`.
- Run Ansible from the repository root and include `--diff` in every
  `ansible-playbook` example or instruction.

## Maintainer Context

Read [`MAINTAINERS.md`](MAINTAINERS.md) before changing recipe structure.
