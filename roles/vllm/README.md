# vllm

Install native vLLM on Ubuntu x86_64 with a working NVIDIA driver and CUDA compiler. Select a model profile that fits the host.

## Configuration

Role defaults are listed below; deployment profiles and inventory can select different values.
Internal variables beginning with `_` are not operator settings.

| Variable | Role default | Purpose |
|---|---|---|
| `vllm_version` | `""` | Required vLLM version |
| `vllm_python` | `python3` | Python executable |
| `vllm_venv` | `/opt/vllm-env` | Python environment directory |
| `vllm_service_name` | `vllm` | Systemd unit name |
| `vllm_service_user` | `vllm` | Service account |
| `vllm_state_dir` | `/var/lib/vllm` | Service state directory |
| `vllm_config_dir` | `/etc/vllm` | Server configuration directory |
| `vllm_model_id` | `""` | Required Hugging Face repository |
| `vllm_model_revision` | `""` | Pinned model revision |
| `vllm_model_name` | `"{{ vllm_model_id.split('/')[-1] }}"` | Served API model name |
| `vllm_model_dir` | `"/opt/models/{{ vllm_model_id &#124; replace('/', '--') }}"` | Downloaded model directory |
| `vllm_hf_cache` | `/opt/models/hf-cache` | Hugging Face cache directory |
| `vllm_hf_token_file` | `""` | Optional local token file on the target, readable by download user |
| `vllm_download_user` | `"{{ ansible_user &#124; default(ansible_facts.user_id) }}"` | Account used to download weights |
| `vllm_host` | `127.0.0.1` | API bind address; non-loopback requires a key |
| `vllm_port` | `8000` | API port |
| `vllm_api_key` | `""` | API authentication key; keep in private inventory |
| `vllm_options` | `{}` | Native vLLM options, including sampling, context, MTP and tool calling |
| `vllm_environment` | `CUDA_HOME: /usr/local/cuda` | Service environment variables |
| `vllm_ready_timeout` | `1800` | API readiness timeout in seconds |
| `vllm_prereq_packages` | `ca-certificates, python3-venv, python3-dev, python3-packaging, build-essential, ninja-build` | System build and Python prerequisites |

## Usage

From the repository root, put these values in `host_vars/<host>.yml`:

```yaml
inference_profile: vllm-qwen38-27b-nvfp4
```

```bash
ansible-playbook vllm.yml --limit gpu1.example.com --diff
```

See the [profile catalog](../../README.md#inference-profiles) for complete model settings and override precedence.

## Behavior and verification

Downloads pinned weights, installs vLLM and configures, enables and starts its service. Managed changes can restart it. Checks API identity, effective context and real generation; this is not a concurrency benchmark.

Manual recipe: [vllm.md](../../vllm.md)
