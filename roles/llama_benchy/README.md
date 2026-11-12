# llama_benchy

Install the API benchmark client and existing runner/plotter. Requires Ubuntu APT and Python venv support.

## Configuration

Role defaults are listed below; deployment profiles and inventory can select different values.
Internal variables beginning with `_` are not operator settings.

| Variable | Role default | Purpose |
|---|---|---|
| `llama_benchy_version` | `"0.4.0"` | Pinned upstream client version |
| `llama_benchy_venv` | `/opt/llama-benchy-env` | Python environment directory |

## Usage

From the repository root, put these values in `host_vars/<host>.yml`:

```yaml
llama_benchy_version: "0.4.0"
```

```bash
ansible-playbook benchmark.yml --limit gpu1.example.com --diff
```

## Behavior and verification

Installs upstream llama-benchy, matplotlib and command links. Installation does not execute benchmarks. Workload and result verification follow the benchmark protocol.

Manual recipe: [benchmark.md](../../benchmark.md)
