# strata

Prepare stock Strata on Ubuntu x86_64 with a working NVIDIA driver and CUDA compiler. Select a model profile with sufficient RAM, VRAM and disk.

## Configuration

Role defaults are listed below; deployment profiles and inventory can select different values.
Internal variables beginning with `_` are not operator settings.

| Variable | Role default | Purpose |
|---|---|---|
| `strata_repo` | `https://github.com/Niko1221/Strata.git` | Upstream Git repository |
| `strata_version` | `146df3c468739147f520ac3816de806f71232571` | Pinned source commit |
| `strata_user` | `strata` | Service account |
| `strata_home` | `/var/lib/strata` | Service account home |
| `strata_source` | `/opt/strata-upstream` | Unmodified upstream checkout |
| `strata_data` | `/opt/strata-data` | Model and pack storage |
| `strata_family` | `''` | Required upstream model family |
| `strata_model` | `''` | Required upstream model/quantization selector |
| `strata_config_tag` | `''` | Required upstream JSON filename suffix |
| `strata_context` | `131072` | Tokens per slot, input plus output |
| `strata_parallel` | `4` | Request slots; also sets cache slot count |
| `strata_vision` | `'yes'` | Vision placement: yes, no, gpu or cpu |
| `strata_port` | `8080` | Loopback API port |
| `strata_cuda_home` | `'{{ cuda_toolkit_home &#124; default("/usr/local/cuda") }}'` | CUDA compiler directory |
| `strata_cuda_packages` | `[]` | Additional CUDA development packages |
| `strata_setup_options` | `[]` | Native setup arguments |
| `strata_managed_flags` | `[--ram-keep-gib, --conversation-cache-min-free-mib, --ple-io, --no-ple-prefetch, --no-prefill-borrow, --prefill]` | Engine flags owned by the role; omitted overrides are removed from args and user_args |
| `strata_user_args` | `[]` | Native engine overrides restricted to managed flags |
| `strata_conversation_cache_mib` | `5120` | Shared RAM history cache budget, not per-slot allocation |
| `strata_environment` | `{}` | Service environment variables |
| `strata_memory_reserve_gib` | `10` | OS reserve used in memory validation |
| `strata_memory_max` | `"{{ (ansible_facts.memtotal_mb &#124; int) - (strata_memory_reserve_gib &#124; int) * 1024 }}M"` | Cgroup cap in M units; must leave the OS reserve |
| `strata_min_available_mb` | `46000` | Minimum available RAM before setup |
| `strata_min_disk_gb` | `160` | Minimum free storage before setup |
| `strata_setup_timeout` | `86400` | Setup timeout in seconds |
| `strata_start_service` | `false` | Enable/start the service and verify generation; false prepares only |

## Usage

From the repository root, put these values in `host_vars/<host>.yml`:

```yaml
inference_profile: strata-qwen38-iq3s-64g
```

```bash
ansible-playbook strata.yml --limit gpu1.example.com --diff
```

See the [profile catalog](../../README.md#inference-profiles) for complete model settings and override precedence.

## Behavior and verification

Validates settings, driver/compiler and storage, builds unmodified upstream source and prepares weights. Installs a bounded unit; activation is opt-in. An enabled deployment verifies API identity, context, cache slots and real generation.

Manual recipe: [strata.md](../../strata.md)
