# vLLM Native Service

Native systemd service paired with [vllm.yml](vllm.yml) and the
[vllm role](roles/vllm/). Install a working NVIDIA driver and CUDA Toolkit first with
[nvidia.md](nvidia.md). Container Toolkit is needed only for Docker workloads.

For Ansible, shared values are in `group_vars/nvidia_hosts.yml`. Put local
credentials and overrides in ignored `host_vars/<host>.yml`, for example:

```yaml
# vllm_hf_token_file: /path/to/hf-token.txt
# vllm_model_revision: commit-or-tag
# vllm_environment:
#   CUDA_HOME: /path/to/cuda
```

Run the separate playbook from the repository root:

```bash { name=vllm-ansible }
ansible-playbook vllm.yml --limit gpu1.example.com --diff
```

## 1. vLLM Native Service

### 1.1 Configure service settings

<!-- ops-step
id: vllm.settings
kind: variables
-->

```bash { name=vllm-settings }
# Python environment and service paths
export VLLM_VERSION="0.33.0"
export VLLM_ENV_DIR="/opt/vllm-env"
export VLLM_SERVICE_USER="vllm"
export VLLM_STATE_DIR="/var/lib/vllm"
export VLLM_CONFIG_DIR="/etc/vllm"
export VLLM_SERVICE_FILE="/etc/systemd/system/vllm.service"

# Model and download cache
export VLLM_MODEL_ID="nvidia/Qwen3.8-27B-NVFP4"
export VLLM_MODEL_NAME="Qwen3.8-27B-NVFP4"
export VLLM_MODEL_DIR="/opt/models/nvidia--Qwen3.8-27B-NVFP4"
export VLLM_HF_CACHE="/opt/models/hf-cache"
# export HF_TOKEN_PATH="$HOME/hf-token.txt" # Optional file containing only the token
export VLLM_MODEL_REVISION="482ca0f3832238542f8f5295dde86b5f22711d80"

export VLLM_HOST="127.0.0.1"
export VLLM_PORT="8000"
```

### 1.2 Install Python, vLLM and Hugging Face CLI

<!-- ops-step
id: vllm.python.install
ansible_task: vllm.python.install | Install Python and build prerequisites
-->
<!-- ops-step
id: vllm.service_user.create
ansible_task: vllm.user.create | Create the service user
-->
<!-- ops-step
id: vllm.user.group
ansible_task: vllm.user.group | Create the service group
-->
<!-- ops-step
id: vllm.models.prepare
ansible_task: vllm.directories.prepare | Prepare model, state and configuration directories
-->
<!-- ops-step
id: vllm.venv.create
ansible_task: vllm.packages.install | Install vLLM and Hugging Face CLI in a virtual environment
-->
<!-- ops-step
id: vllm.packages.install
ansible_task: vllm.packages.install | Install vLLM and Hugging Face CLI in a virtual environment
-->
<!-- ops-step
id: vllm.kernels.cubin
ansible_task: vllm.kernels.download | Install precompiled kernels with vLLM
-->
<!-- ops-step
id: vllm.kernels.cache
ansible_task: vllm.kernels.download | Install precompiled kernels with vLLM
-->

```bash { name=vllm-bootstrap }
# Install prerequisites and create the service account
sudo apt-get update
sudo apt-get install -y ca-certificates python3-venv python3-dev build-essential ninja-build
sudo adduser --system --group --home "$VLLM_STATE_DIR" \
  --shell /usr/sbin/nologin "$VLLM_SERVICE_USER"
sudo install -d -o "$VLLM_SERVICE_USER" -g "$VLLM_SERVICE_USER" "$VLLM_STATE_DIR"
sudo install -d -g "$VLLM_SERVICE_USER" "$VLLM_CONFIG_DIR"
sudo install -d -o "$(id -un)" -g "$VLLM_SERVICE_USER" "$VLLM_MODEL_DIR" "$VLLM_HF_CACHE"

# Install into an isolated environment and expose both commands
sudo python3 -m venv "$VLLM_ENV_DIR"
sudo "$VLLM_ENV_DIR/bin/pip" install "vllm==$VLLM_VERSION" huggingface_hub
sudo "$VLLM_ENV_DIR/bin/vllm" download-kernels
sudo ln -sfn "$VLLM_ENV_DIR/bin/vllm" /usr/local/bin/vllm
sudo ln -sfn "$VLLM_ENV_DIR/bin/hf" /usr/local/bin/hf
```

### 1.3 Download the model

<!-- ops-step
id: vllm.models.download
ansible_task: vllm.model.download | Download the model as the SSH login user
-->

```bash { name=vllm-model }
# Download as the login user; HF_TOKEN_PATH is read directly when configured
HF_HOME="$VLLM_HF_CACHE" hf download "$VLLM_MODEL_ID" \
  --local-dir "$VLLM_MODEL_DIR" --revision "$VLLM_MODEL_REVISION"
```

### 1.4 Configure the server

Create `/etc/vllm/config.yaml` with these values. Paths and the served name must
match section 1.1. This profile targets one 96 GB Blackwell GPU with NVFP4
weights, an FP8 KV cache and the native 262144-token context, without YaRN.

```yaml
model: /opt/models/nvidia--Qwen3.8-27B-NVFP4
served-model-name: [Qwen3.8-27B-NVFP4]
host: 127.0.0.1
port: 8000
max-model-len: 262144 # Input and output together; native context
gpu-memory-utilization: 0.9 # Fraction of GPU memory
kv-cache-dtype: fp8
max-num-seqs: 64 # Admission limit; parallel capacity depends on context
max-num-batched-tokens: 8192
long-prefill-token-threshold: 1024 # Base chunk cap with competing requests
long-prefill-token-threshold-adaptive: true # Share the token budget across requests
mm-processor-cache-gb: 0
reasoning-parser: qwen3
enable-auto-tool-choice: true
tool-call-parser: qwen3_coder
disable-prefix-caching: true
disable-flashinfer-autotune: true
speculative-config:
  method: mtp
  num_speculative_tokens: 2 # MTP draft tokens
override-generation-config:
  temperature: 1.0 # Official thinking profile
  top_p: 0.95
  top_k: 20
  min_p: 0
  repetition_penalty: 1.0
  presence_penalty: 0
  frequency_penalty: 0
  max_new_tokens: 131072 # 128K generated tokens, within the total context
default-chat-template-kwargs:
  enable_thinking: true
  reasoning_effort: xhigh
```

<!-- ops-step
id: vllm.config.write
ansible_task: vllm.config.write | Write vLLM server options
-->

```bash { name=vllm-config }
# Create or edit the server options, then allow the service to read them
sudoedit "$VLLM_CONFIG_DIR/config.yaml"
sudo chown root:"$VLLM_SERVICE_USER" "$VLLM_CONFIG_DIR/config.yaml"
sudo chmod 640 "$VLLM_CONFIG_DIR/config.yaml"
```

Ansible writes this file from `vllm_options`, adding the model, listener and
optional `vllm_api_key`. A non-loopback listener requires an API key.

The [official model card](https://huggingface.co/Qwen/Qwen3.8-27B#best-practices)
defines the native context and thinking sampling profile.
[Alibaba Model Studio](https://modelstudio.console.alibabacloud.com/ap-southeast-1/model/market/detail/qwen3.8-27b)
lists a 128K output limit. Here `max_new_tokens` caps all generated tokens,
including reasoning; input plus generation must fit the configured context.

### 1.5 Create or edit the systemd service file

Create `/etc/systemd/system/vllm.service` with this content:

```ini
[Unit]
Description=vLLM inference service
After=network-online.target
Wants=network-online.target

[Service]
User=vllm
Group=vllm
WorkingDirectory=/var/lib/vllm
Environment="HF_HOME=/var/lib/vllm/huggingface"
Environment=HF_HUB_OFFLINE=1
Environment="CUDA_HOME=/usr/local/cuda"
ExecStart=/opt/vllm-env/bin/vllm serve --config /etc/vllm/config.yaml
Restart=on-failure
RestartSec=5
TimeoutStartSec=1800
LimitNOFILE=1048576
LimitMEMLOCK=infinity
NoNewPrivileges=true

[Install]
WantedBy=multi-user.target
```

<!-- ops-step
id: vllm.systemd.write
ansible_task: vllm.systemd.write | Write the vLLM systemd unit
-->
<!-- ops-step
id: vllm.environment.write
ansible_task: vllm.systemd.write | Write the vLLM systemd unit
-->

```bash { name=vllm-systemd-write }
# Create or edit the unit separately from starting it
sudoedit "$VLLM_SERVICE_FILE"
```

### 1.6 Reload systemd and start the service

<!-- ops-step
id: vllm.systemd.reload
ansible_task: vllm.systemd.reload | Apply pending service changes
-->
<!-- ops-step
id: vllm.systemd.start
ansible_task: vllm.systemd.start | Enable and start vLLM
-->

```bash { name=vllm-systemd-start }
# Apply the unit and start or restart the service
sudo systemctl daemon-reload
sudo systemctl enable vllm
sudo systemctl restart vllm
```

### 1.7 Verify GPU access and the API

<!-- ops-step
id: vllm.torch.cuda_check
ansible_task: vllm.torch.cuda_check | Verify CUDA access and installed package versions
-->
<!-- ops-step
id: vllm.api.health
ansible_task: vllm.api.health | Wait for the API to become healthy
-->
<!-- ops-step
id: vllm.health.models
ansible_task: vllm.api.models | Read the served model identity
-->
<!-- ops-step
id: vllm.api.chat
ansible_task: vllm.api.chat | Verify a real generation request
-->
<!-- ops-step
id: vllm.nvfp4.verify
ansible_task: vllm.api.generate | Require a completed nonempty model answer
-->
<!-- ops-step
id: vllm.health.tool_call
ansible_task: vllm.api.tools | Verify structured tool calling when enabled
-->

```bash { name=vllm-verify }
# Verify CUDA from the service account
sudo runuser -u "$VLLM_SERVICE_USER" -- "$VLLM_ENV_DIR/bin/python" -c \
  'import torch; assert torch.cuda.is_available(); print(torch.cuda.get_device_name(0))'

# Wait for the API, then verify the model and generate an answer
curl -fsS --retry-connrefused --retry 180 --retry-delay 10 --max-time 10 \
  "http://$VLLM_HOST:$VLLM_PORT/health"
curl -fsS "http://$VLLM_HOST:$VLLM_PORT/v1/models"
curl -fsS "http://$VLLM_HOST:$VLLM_PORT/v1/chat/completions" \
  -H 'Content-Type: application/json' --data-binary @- <<JSON
{"model":"$VLLM_MODEL_NAME","messages":[{"role":"user","content":"Reply with OK."}],"temperature":0,"max_tokens":32,"chat_template_kwargs":{"enable_thinking":false}}
JSON

# Verify the configured tool-call parser
curl -fsS "http://$VLLM_HOST:$VLLM_PORT/v1/chat/completions" \
  -H 'Content-Type: application/json' --data-binary @- <<JSON
{"model":"$VLLM_MODEL_NAME","messages":[{"role":"user","content":"What is the weather in Brussels?"}],"tools":[{"type":"function","function":{"name":"get_weather","description":"Get current weather for a location","parameters":{"type":"object","properties":{"location":{"type":"string"}},"required":["location"]}}}],"tool_choice":"auto","temperature":0,"max_tokens":128,"chat_template_kwargs":{"enable_thinking":false}}
JSON
```

The GPU name should match the host. The API should report the selected model,
its local root path and context, then return a nonempty answer with `finish_reason: stop`.
The tool request should return a `get_weather` call with valid location arguments.

### 1.8 Follow logs (Optional)

<!-- ops-step
id: vllm.logs.follow
kind: observe
-->

```bash { name=vllm-logs interactive=true }
# Follow startup and request logs
sudo journalctl -u vllm -f
```
