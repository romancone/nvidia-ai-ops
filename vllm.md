# vLLM Native Service

This is a Runme-friendly recipe for a native, systemd-managed vLLM service on a
single GPU host. It is based on a working Qwen3.6 NVFP4 single-GPU setup.

This recipe does not use Docker. Install and verify the NVIDIA driver and CUDA
toolkit first with [`nvidia.md`](nvidia.md). The NVIDIA container toolkit is only
needed for Docker workloads.

Requires `uv`, `hf`, and `jq` on the target host.

## 1. vLLM Native Service

- systemd-managed, no Docker
- full 262,144 native context, single GPU
- NVFP4 / SM120 kernel path via FlashInfer and CUTLASS DSL
- fp8 KV cache
- MTP speculative decoding with `num_speculative_tokens: 2`
- Qwen reasoning parser
- Qwen structured tool-call parser

### 1.1 Configure service settings

<!-- ops-step
id: vllm.settings
kind: variables
-->

```bash
# Variables
export VLLM_PYTHON_VERSION="3.13"
export VLLM_UV_PYTHON_DIR="/opt/uv-python"
export VLLM_ENV_DIR="/opt/vllm-env"
export VLLM_SERVICE_USER="vllm"
export VLLM_STATE_DIR="/var/lib/vllm"
export VLLM_CONFIG_DIR="/etc/vllm"
export VLLM_ENV_FILE="/etc/vllm/vllm.env"
export VLLM_SERVICE_FILE="/etc/systemd/system/vllm.service"

export VLLM_MODEL_ID="unsloth/Qwen3.6-27B-NVFP4"
export VLLM_MODEL_NAME="Qwen3.6-27B-NVFP4"
export VLLM_MODEL_DIR="/opt/models/Qwen3.6-27B-NVFP4"
export VLLM_HF_CACHE="/opt/models/hf-cache"
export VLLM_WORKDIR="/opt/models"

export VLLM_CUDA_HOME="/usr/local/cuda-13.4"
export VLLM_HOST="127.0.0.1"
export VLLM_PORT="8000"
export VLLM_API_KEY_VALUE="changeme"
```

### 1.2 Install Python and vLLM

The NVFP4 check should print the GPU capability and `True True`.

<!-- ops-step
id: vllm.python.install_dir
kind: file
-->

<!-- ops-step
id: vllm.python.install
kind: command
-->

<!-- ops-step
id: vllm.venv.create
kind: command
-->

<!-- ops-step
id: vllm.packages.install
kind: package
-->

<!-- ops-step
id: vllm.nvfp4.verify
kind: verify
-->

```bash
# Create Python Install Directory
sudo mkdir -p "$VLLM_UV_PYTHON_DIR"
sudo chown "$USER":"$USER" "$VLLM_UV_PYTHON_DIR"

# Install Python with uv
export UV_PYTHON_INSTALL_DIR="$VLLM_UV_PYTHON_DIR"
uv python install "$VLLM_PYTHON_VERSION"

# Create vLLM Virtual Environment
sudo mkdir -p "$VLLM_ENV_DIR"
sudo chown "$USER":"$USER" "$VLLM_ENV_DIR"
uv venv "$VLLM_ENV_DIR" --python "$VLLM_PYTHON_VERSION"

# Install vLLM Packages
source "$VLLM_ENV_DIR/bin/activate"
uv pip install "vllm>=0.25.0" "flashinfer-python>=0.6.13" "nvidia-cutlass-dsl>=4.5.2" --torch-backend=auto
deactivate
sudo chmod -R o+rX "$VLLM_UV_PYTHON_DIR"

# Verify NVFP4 / SM120 Kernel Path
"$VLLM_ENV_DIR/bin/python" -c "import torch; from vllm.utils.flashinfer import has_flashinfer_b12x_gemm as g, has_flashinfer_b12x_moe as m; print(torch.cuda.get_device_capability(), g(), m())"
```

### 1.3 Download the model

<!-- ops-step
id: vllm.models.prepare
kind: file
-->

<!-- ops-step
id: vllm.models.download
kind: command
-->

```bash
# Prepare Model Directories
sudo mkdir -p "$VLLM_MODEL_DIR" "$VLLM_HF_CACHE"
sudo chown -R "$USER":"$USER" "$VLLM_WORKDIR"

# Download Model Weights
hf download "$VLLM_MODEL_ID" --local-dir "$VLLM_MODEL_DIR"
```

### 1.4 Create the service user and environment

<!-- ops-step
id: vllm.service_user.create
kind: user
-->

<!-- ops-step
id: vllm.environment.write
kind: file
-->

```bash
# Create Service User and State Directory
if ! id "$VLLM_SERVICE_USER" >/dev/null 2>&1; then
  sudo useradd --system --no-create-home --shell /usr/sbin/nologin "$VLLM_SERVICE_USER"
fi
sudo chown -R "$VLLM_SERVICE_USER":"$VLLM_SERVICE_USER" "$VLLM_ENV_DIR" "$VLLM_WORKDIR"
sudo mkdir -p "$VLLM_STATE_DIR"
sudo chown "$VLLM_SERVICE_USER":"$VLLM_SERVICE_USER" "$VLLM_STATE_DIR"

# Write Environment File
sudo mkdir -p "$VLLM_CONFIG_DIR"
sudo tee "$VLLM_ENV_FILE" >/dev/null <<EOF
HOME=$VLLM_STATE_DIR
TRITON_CACHE_DIR=$VLLM_STATE_DIR/.triton-cache
HF_HOME=$VLLM_HF_CACHE
VLLM_API_KEY=$VLLM_API_KEY_VALUE
FLASHINFER_CUDA_ARCH_LIST=12.0f
FLASHINFER_FORCE_SM=120f
EOF
sudo chmod 600 "$VLLM_ENV_FILE"
sudo chown "$VLLM_SERVICE_USER":"$VLLM_SERVICE_USER" "$VLLM_ENV_FILE"
```

### 1.5 Create or edit the systemd service file

Create the unit with the block below, or use `sudoedit "$VLLM_SERVICE_FILE"` and
replace the `$VLLM_*` placeholders with your values from step 1.1.
When editing directly, use a single trailing `\` on continuation lines.

<!-- ops-step
id: vllm.systemd.write
kind: file
-->

```bash
# Write systemd Service
sudo tee "$VLLM_SERVICE_FILE" >/dev/null <<EOF
[Unit]
Description=vLLM server - $VLLM_MODEL_NAME - full context
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=$VLLM_SERVICE_USER
Group=$VLLM_SERVICE_USER
EnvironmentFile=$VLLM_ENV_FILE
Environment=PATH=$VLLM_CUDA_HOME/bin:/usr/bin:/bin
Environment=LD_LIBRARY_PATH=$VLLM_CUDA_HOME/lib64
WorkingDirectory=$VLLM_WORKDIR
ExecStart=$VLLM_ENV_DIR/bin/vllm serve $VLLM_MODEL_DIR \\
  --served-model-name $VLLM_MODEL_NAME \\
  --trust-remote-code \\
  --dtype bfloat16 \\
  --max-model-len 262144 \\
  --kv-cache-dtype fp8 \\
  --gpu-memory-utilization 0.90 \\
  --enable-chunked-prefill \\
  --enable-prefix-caching \\
  --reasoning-parser qwen3 \\
  --enable-auto-tool-choice \\
  --tool-call-parser qwen3_coder \\
  --speculative-config '{"method":"mtp","num_speculative_tokens":2}' \\
  --host $VLLM_HOST \\
  --port $VLLM_PORT
Restart=on-failure
RestartSec=5
LimitNOFILE=1048576
LimitMEMLOCK=infinity

[Install]
WantedBy=multi-user.target
EOF
```

### 1.6 Reload systemd and start the service

<!-- ops-step
id: vllm.systemd.start
kind: command
-->

```bash
# Enable and Start Service
sudo systemctl daemon-reload
sudo systemctl enable --now vllm.service
sudo systemctl status vllm.service --no-pager
```

### 1.7 Verify the API

<!-- ops-step
id: vllm.health.models
kind: verify
-->

<!-- ops-step
id: vllm.health.tool_call
kind: verify
-->

```bash
# Check Model List
curl -s "http://$VLLM_HOST:$VLLM_PORT/v1/models" \
  -H "Authorization: Bearer $VLLM_API_KEY_VALUE" | jq .

# Check Tool Call Path
curl -s "http://$VLLM_HOST:$VLLM_PORT/v1/chat/completions" \
  -H "Authorization: Bearer $VLLM_API_KEY_VALUE" \
  -H "Content-Type: application/json" \
  -d "{
    \"model\":\"$VLLM_MODEL_NAME\",
    \"messages\":[{\"role\":\"user\",\"content\":\"What is the weather in Brussels?\"}],
    \"tools\":[{
      \"type\":\"function\",
      \"function\":{
        \"name\":\"get_weather\",
        \"description\":\"Get current weather for a location\",
        \"parameters\":{\"type\":\"object\",\"properties\":{\"location\":{\"type\":\"string\"}},\"required\":[\"location\"]}
      }
    }],
    \"tool_choice\":\"auto\"
  }" | jq '.choices[0].message.tool_calls'
```

### 1.8 Follow logs (Optional)

<!-- ops-step
id: vllm.logs.follow
kind: observe
-->

```bash
# Follow Logs
journalctl -u vllm.service -f
```
