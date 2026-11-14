# Strata cleanup

[strata-cleanup.yaml](../../strata-cleanup.yaml) removes source, builds, models, packed weights, conversation caches, service state, unit and overrides.
The role reads installation defaults from `strata` and respects inventory path
overrides. It does not load a model profile.

| Setting | Default | Purpose |
|---|---|---|
| `strata_cleanup_extra_paths` | `[]` | Additional installation or incomplete download directories |
| `strata_cleanup_legacy_paths` | `[/opt/strata]` | Previous Strata source directories |

Preview with `ansible-playbook strata-cleanup.yaml --limit HOST --check --diff`.
Check mode reports planned changes without stopping services or deleting files.
An actual run stops the managed service and refuses deletion if a remaining
process references a selected path; stop manually launched servers separately.
Missing files and services are harmless on repeated runs.

Service accounts, drivers, CUDA, shared system packages, external credentials,
benchmark tools and measurement archives are preserved. User home directories
and shared model roots cannot be deletion targets. Directory content diffs are
suppressed to avoid dumping model and cache file listings.
