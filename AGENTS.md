# Project Rules

## Scope and Review

- Stay within the requested change. Do not add models, frameworks, benchmarks,
  helper scripts or extra test repetitions without a request
- Treat review, tests, host changes, commits, pushes and merges as separate actions.
  Respect explicit prohibitions across turns until the user changes them.
  "No tests" includes syntax checks and benchmark reruns; use static inspection
- Keep review changes unstaged when requested. Inspect the current working diff;
  do not mix it with previously committed or parked work
- Keep scratch scripts, build outputs and transient debug files outside the repository
- Keep only clean, completed tests in the repository. Store their structured
  results in one dataset under `evaluation/`; keep web pages in `reports/`.
  Keep complete clean source inputs, outputs and measurements for published
  completed tests under `evaluation/`, with source paths and checksums.
  `reports/` contains generated viewing data, never a second editable source.
  Keep failed attempts, diagnostics, scratch files, experimental builds and
  experiment history on the benchmark host; never bulk-copy temporary directories

## Third-party products

Never modify third-party products. Do not patch, fork to change behavior,
rewrite installed files, or monkey-patch dependencies at runtime. Use
documented upstream configuration and public interfaces. If upstream lacks a
required capability, report the limitation and stop before changing the product.

## Git

- Use `codex/<topic>` feature branches for new work. Propose the name for human
  confirmation before creating it unless that name is already authorized
- Never commit or push without explicit human authorization
- Continue on the current branch when instructed; preserve unrelated pending work
- Keep commits reviewable and scoped to one feature or cleanup

## Writing Style

- Do not end bullet items with a period, in Markdown or HTML
- Write in clean, simple language. Public docs must be concise, practical and current
- Manual recipes must work on their own with runnable commands and short comments.
  Do not require Ansible inventory files to follow manual steps; keep Ansible
  configuration in a separate, clearly labelled example
- Show the editable configuration and its file path before dependent commands
- Explain parameters beside their values with concise YAML or Bash `#` comments.
  Show optional parameters commented out; do not repeat the explanation in prose
- Remove repeated reminders, vague "review/update as needed" instructions and
  internal implementation details from operator steps
- State what to run and what output confirms success
- Do not use ASCII decoration, verbose comments, or reasoning and history in comments

## Command Formatting

- Use standard Ubuntu commands. Omit redundant flags and checks
- Put separate commands on separate lines; do not chain them with `&&`
- Keep the command and short flags together: `curl -fL \`, not a bare `curl`
  followed by a separate line containing only `-fL`
- Wrap long commands with `\` at logical boundaries. Keep each long option with
  its value; do not split every short argument mechanically
- When a recipe requires a reboot, show `sudo reboot` without a shell check to
  decide whether to print it. Never reboot a host without authorization

## Recipes

- Keep Ansible roles reusable and host-agnostic
- Roles define installation and service behavior; inventory supplies host and
  package choices. Paired recipes and configuration examples derive from them
- Align manual recipes with their Ansible roles in settings, installation order,
  paths, service arguments and final result. Prose-only edits should leave commands
  unchanged unless a correction requires changing them
- Keep manual recipes simple. Skip redundant variable, OS, and preflight checks,
  change tracking, and check-mode reports. Retain essential safeguards and final
  verification
- Ansible roles must include complete prerequisite and settings validation,
  runtime checks, idempotence, and check-mode handling
- Use two-level numbering in Markdown recipes: `## 1. Role name`, then
  `### 1.1 Logical part`, `### 1.2 Logical part`, and so on
- Match top-level numbers to the roles in playbook order. For manual-only
  recipes, use one top-level service section. Number logical parts at the
  second level
- Combine related commands for each numbered part into one `bash` block. Use
  named Runme cells and concise `# comments` to distinguish operations
- Mark optional major sections with `(Optional)` in the heading and state when
  they are needed. The label applies to the entire section; describe separately
  whether the playbook includes the role by default
- Preserve stable `ops-step` IDs and `ansible_task` mappings for included manual
  operations, including grouped tasks. Validation-only tasks may remain
  Ansible-only
- Update affected settings, operations and verification in both paths together.
  A shared ID alone does not prove equivalent behavior
- Use native Ansible modules where suitable

## Ansible Layout

- Keep `ansible.cfg`, `site.yml`, `hosts.example.ini`, `group_vars/`, `host_vars/`,
  and `roles/` at the repository root
- Use `inventory = ./hosts` in `ansible.cfg`; keep the real `hosts` file and local
  host overrides under `host_vars/` ignored by Git
- Set the default SSH user to `ubuntu` in `group_vars/all.yml`; put host-specific
  overrides in local inventory or host variables
- Keep NVIDIA settings in `group_vars/nvidia_hosts.yml` and target `nvidia_hosts`
- Roles must not contain node names or host-specific package cleanup
- Run Ansible from the repository root and include `--diff` in every
  `ansible-playbook` example or instruction
- Do not add test suites, embedded helper scripts or recipe-rewriting tools
  without a request

## Compatibility and Verification

- Keep host and release choices in configuration, not host-specific role logic.
  Discover installed versions and leftover paths rather than copying them from
  the verification host
- Check current NVIDIA and Ubuntu primary sources when selecting packages or versions
- Distinguish package availability, vendor product support, upstream testing
  and verification on the actual host
- Require evidence before adding architecture overrides, driver replacements
  or global library-path changes; document any necessary workaround
- Keep cleanup and switches between driver sources separate from installation.
  Reject unrelated package changes
- Report reboot requirements. Package installation alone is not GPU or workload validation
- Respect the requested test configurations; do not silently substitute settings
  or expand the matrix. Report the actual settings and relevant results
- Never present an untested configuration as verified

## Benchmark Data

Apply these rules when benchmark data is in scope:

- Follow [benchmark.md](benchmark.md): Short/Long at powers-of-two client counts
  up to verified parallel capacity, with no queued requests. Max requires an
  explicitly agreed context and output budget
- Identify the canonical dataset; pages and generated summaries must not maintain
  independent measurement values
- Preserve source paths, attempt identity and checksums for completed results.
  Do not import incomplete attempts or fill missing measurements with guesses
- Keep microbenchmarks, server workloads and capacity measurements distinct.
  Reuse a result only when its workload and relevant configuration match
- Preserve model artifact, quantization, backend, concurrency, context, cache,
  build and source-attempt identity, including other result-affecting settings
- Keep TTFT, prefill, decode throughput and end-to-end throughput distinct.
  Never include prefill in a value labelled decode speed
- Distinguish measured failure, timeout, missing measurement and excluded scope.
  A timeout does not establish a memory limit
- Preserve useful measurements and image answers during imports and migrations.
  Stored records and access through a viewer are separate requirements
- Remove approved obsolete records at the import boundary as well as in the
  dataset so later imports cannot restore them

## Report Changes

Apply these rules when changing reports:

- Preserve hand-maintained pages and staged edits. Presentation changes must not
  rewrite measurements or the import pipeline
- Reuse existing controls, styles and selector order. Do not add sections,
  columns, exports or explanations beyond the requested scope
- Keep model order stable and labels sufficient to distinguish configurations
- Distinguish unmeasured planned cases from excluded combinations in selectors
- Keep recommendations separate from full results. Compare matched settings and
  state whether the choice favors quality, speed or memory
- Give each explanation one visible home
- Keep switch labels and table headers unbroken; wrap complete control groups
  at narrow widths without stretching buttons
- When verification is authorized, inspect the rendered page, filters and image
  previews. Source inspection alone does not prove the UI works

## Maintainer Context

Read [MAINTAINERS.md](MAINTAINERS.md) before changing recipe structure or a report
pipeline. Keep file ownership there, not in these rules.

For new-model result collection, benchmark imports, coverage reviews and report migrations, use
[benchmark-report-review](.agents/skills/benchmark-report-review/SKILL.md).
Routine text and CSS edits do not need the full workflow.

For overview cards and model report presentation, use
[benchmark-report-layout](.agents/skills/benchmark-report-layout/SKILL.md).
