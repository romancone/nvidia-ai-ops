# vLLM cleanup

[vllm-cleanup.yaml](../../vllm-cleanup.yaml) removes Python environment, configuration, state, download cache, completed model downloads, service unit and overrides.
The role reads installation defaults from `vllm` and respects inventory path
overrides. It does not load a model profile.

| Setting | Default | Purpose |
|---|---|---|
| `vllm_cleanup_extra_paths` | `[]` | Additional installation or incomplete download directories |
| `vllm_cleanup_model_root` | `/opt/models` | Search for completed model downloads |

Incomplete downloads without a completion marker need an explicit
`vllm_model_dir` or `vllm_cleanup_extra_paths` entry. Command links are removed
only when they point into the configured vLLM environment.

Preview with `ansible-playbook vllm-cleanup.yaml --limit HOST --check --diff`.
Check mode reports planned changes without stopping services or deleting files.
An actual run stops the managed service and refuses deletion if a remaining
process references a selected path; stop manually launched servers separately.
Missing files and services are harmless on repeated runs.

Service accounts, drivers, CUDA, shared system packages, external credentials,
benchmark tools and measurement archives are preserved. User home directories
and shared model roots cannot be deletion targets. Directory content diffs are
suppressed to avoid dumping model and cache file listings.
