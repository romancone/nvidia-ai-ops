# Strata on NVIDIA

Source installation paired with [strata.yml](strata.yml) and the
[strata role](roles/strata/). Requires Ubuntu x86_64, a working NVIDIA driver,
CUDA Toolkit and enough free GPU memory. See [nvidia.md](nvidia.md).
Minimal NVCC installations also need cuBLAS development files matching that
toolkit; select their package names with `strata_cuda_packages` in host variables.

The role prepares one selected model and installs a service unit; it does not
start or enable the service by default. Preparation downloads weights and can
run upstream's model smoke check. Stop other GPU workloads before preparation.

For Ansible, select `inference_profile: strata-qwen38-iq3s-64g` in ignored
`host_vars/<host>.yml`. Complete settings are in the
[IQ3_S profile](profiles/strata-qwen38-iq3s-64g.yml); other variants and override
precedence are in the [profile catalog](README.md#inference-profiles).
Run from the repository root:

```bash { name=strata-ansible }
ansible-playbook strata.yml --limit gpu1.example.com --diff
```

The IQ3_S profile uses four 262144-token slots, PLE in RAM, a shared
8960 MiB conversation cache, a 52 GiB cgroup limit and a 10 GiB OS reserve. Use a fresh source
directory for the upstream build. Existing model downloads stay in
`/opt/strata-data`. See the [Max C=4 measurements](reports/qwen38-flash-next.html#cache-8960): two parked
RAM histories were retained and restored; four cache slots do not guarantee
space for four full-context histories.

Upstream setup pins weight revisions, verifies sizes and SHA-256, and resumes
downloads. Qwen is built from the pinned source; DeepSeek uses its separate
upstream engine package. Record that package's version and hash independently.

## 1. Strata

### 1.1 Configure installation settings

Run the manual blocks in the same Bash shell on the target host, starting in
a checkout of this operations repository. Inventory files are unnecessary.

```bash { name=strata-settings }
export STRATA_VERSION=146df3c468739147f520ac3816de806f71232571
export STRATA_SOURCE=/opt/strata-upstream
export STRATA_DATA=/opt/strata-data
export STRATA_HOME=/var/lib/strata
export STRATA_CUDA_HOME=/usr/local/cuda # Selected toolkit, before other nvcc paths
export STRATA_FAMILY=qwen
export STRATA_MODEL=IQ3_S # Qwen3.8-Flash-Next GGUF
export STRATA_TAG=iq3_s # Upstream config filename suffix
export STRATA_CONTEXT=262144 # Per conversation, input plus output; no YaRN
export STRATA_PARALLEL=4 # Concurrent conversations
export STRATA_VISION=gpu
export STRATA_PORT=8080 # Loopback API
export STRATA_MEMORY_MAX=53248M # 52 GiB; keep at least 10 GiB for the OS
SETUP_OPTIONS=(
  --kv int8 --kv-streaming off # Keep context on the GPU
  --mtp on --vram-reserve-mib 1024
)
```

### 1.2 Install prerequisites and clone source

<!-- ops-step
id: strata.packages
ansible_task: strata.packages | Install build prerequisites
kind: package
-->
<!-- ops-step
id: strata.user
ansible_task: strata.user | Create the service account
kind: command
-->
<!-- ops-step
id: strata.directories
ansible_task: strata.directories | Create source and data directories
kind: command
-->
<!-- ops-step
id: strata.source
ansible_task: strata.source | Check out the selected source
kind: command
-->

```bash { name=strata-source }
set -e
sudo apt-get update
sudo apt-get install -y acl build-essential git ca-certificates curl cmake \
  ninja-build python3 python3-venv python3-dev util-linux iproute2
sudo useradd --system --create-home --home-dir "$STRATA_HOME" \
  --shell /usr/sbin/nologin --user-group strata
sudo usermod -aG video strata
sudo install -d -o strata -g strata "$STRATA_SOURCE" "$STRATA_DATA"
sudo -u strata git clone https://github.com/Niko1221/Strata.git "$STRATA_SOURCE"
sudo -u strata git -C "$STRATA_SOURCE" checkout --detach "$STRATA_VERSION"
sudo -u strata git -C "$STRATA_SOURCE" submodule update --init --recursive
```

### 1.3 Build and prepare the model

<!-- ops-step
id: strata.model.setup
ansible_task: strata.model.setup | Run upstream source setup
kind: command
-->
<!-- ops-step
id: strata.model.integrity
ansible_task: strata.model.setup | Run upstream source setup
kind: command
-->
<!-- ops-step
id: strata.model.profile
ansible_task: strata.model.profile | Set engine options in the upstream model config
kind: command
-->

```bash { name=strata-prepare }
sudo systemd-run --wait --pipe --collect --unit=strata-prepare \
  --uid=strata --gid=strata --working-directory="$STRATA_SOURCE" \
  --setenv="HOME=$STRATA_HOME" --setenv=PYTHONUNBUFFERED=1 \
  --setenv="PATH=$STRATA_CUDA_HOME/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin" \
  --property="MemoryMax=$STRATA_MEMORY_MAX" --property=MemorySwapMax=0 \
  --property=LimitMEMLOCK=infinity --property=RuntimeMaxSec=86400 \
  --property=SupplementaryGroups=video \
  "$STRATA_SOURCE/setup.sh" --setup --build --yes --no-start --no-browser \
  --source huggingface --backend cuda --family "$STRATA_FAMILY" \
  --model "$STRATA_MODEL" --data-dir "$STRATA_DATA" \
  --context "$STRATA_CONTEXT" --parallel "$STRATA_PARALLEL" \
  --vision "$STRATA_VISION" --host 127.0.0.1 --port "$STRATA_PORT" \
  "${SETUP_OPTIONS[@]}"
```

In `/opt/strata-upstream/strata-iq3_s.json`, update the following options in both `args` and `user_args`.
Keep the other options and their values. Leave `args_written` to upstream setup:

```json
[
  "--ram-keep-gib", "10", "--conversation-cache-min-free-mib", "10240",
  "--ple-io", "ram", "--no-ple-prefetch", "--no-prefill-borrow",
  "--prefill", "2048", "--conversation-cache-mib", "8960",
  "--conversation-cache-slots", "4"
]
```

```bash { name=strata-serving-settings }
sudo -u strata sensible-editor "$STRATA_SOURCE/strata-$STRATA_TAG.json"
```

### 1.4 Create the service unit

Edit `/etc/systemd/system/strata.service`:

```ini
[Unit]
Description=Strata inference service
After=network-online.target
Wants=network-online.target

[Service]
User=strata
Group=strata
SupplementaryGroups=video
Environment=HOME=/var/lib/strata
WorkingDirectory=/opt/strata-upstream
Environment=STRATA_BATCH_MTP=1
Environment=STRATA_BATCH_DECODE_SHARE=0
Environment=STRATA_SLOT_COPY_DIRECT=1
Environment=STRATA_EMBED_VRAM=1
Environment=MALLOC_MMAP_THRESHOLD_=1048576
ExecStart=/opt/strata-upstream/.venv/bin/python /opt/strata-upstream/serve/server.py --engine strata --config /opt/strata-upstream/strata-iq3_s.json --host 127.0.0.1 --port 8080 --max-queue 0
Restart=no
KillMode=control-group
TimeoutStopSec=60
MemoryMax=53248M
MemorySwapMax=0
OOMPolicy=stop
LimitMEMLOCK=infinity
NoNewPrivileges=true
ProtectSystem=full
ProtectHome=true
PrivateTmp=true

[Install]
WantedBy=multi-user.target
```

<!-- ops-step
id: strata.service
ansible_task: strata.service | Install the bounded systemd unit
kind: service
-->
<!-- ops-step
id: strata.service.reload
ansible_task: strata.service.reload | Reload systemd units
kind: service
-->

```bash { name=strata-service-files }
sudoedit /etc/systemd/system/strata.service
sudo systemctl daemon-reload
```

### 1.5 Start and verify after deployment approval

If a manual server is listening on the configured port, stop it before switching to the service.
For an approved start with the configured memory limit, set
`strata_start_service: true` for Ansible or run the commented command below.

<!-- ops-step
id: strata.service.start
ansible_task: strata.service.start | Enable the selected local daemon when requested
kind: service
-->
<!-- ops-step
id: strata.verify
ansible_task: strata.verify | Verify local API identity and context
kind: command
-->
<!-- ops-step
id: strata.verify.generation
ansible_task: strata.verify.generation | Require a real generated response
kind: command
-->
<!-- ops-step
id: strata.verify.slots
ansible_task: strata.verify.slots | Verify the effective runtime slot count
kind: command
-->

```bash { name=strata-verify }
# Optional persistent service
# sudo systemctl enable --now strata
curl -fsS "http://127.0.0.1:$STRATA_PORT/v1/models"
curl -fsS "http://127.0.0.1:$STRATA_PORT/metrics"
curl -fsS "http://127.0.0.1:$STRATA_PORT/v1/chat/completions" \
  -H 'Content-Type: application/json' \
  -d '{"model":"qwen3.8-flash-next-iq3_s","messages":[{"role":"user","content":"Name the capital of France."}],"max_tokens":64}'
```

Check the model ID, `meta.n_ctx=262144`, effective `live.parallel=4`, enabled
conversation cache with four cache slots and an 8960 MiB budget, and a nonempty
completion with positive token usage. These checks do not establish queue-free
parallel throughput; see the [IQ3_S report](reports/qwen38-flash-next.html#cache-8960) for measured results.

References: [upstream installation](https://github.com/Niko1221/Strata/blob/146df3c468739147f520ac3816de806f71232571/docs/SOURCE_INSTALL.md),
[models](https://github.com/Niko1221/Strata/blob/146df3c468739147f520ac3816de806f71232571/docs/MODELS.md).
