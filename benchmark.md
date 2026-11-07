# API Benchmark Protocol

[llama-benchy](https://github.com/eugr/llama-benchy) measures an existing
OpenAI-compatible server. `llama-benchy-run` controls concurrency using vLLM's
live queue and preemption metrics. Installation does not start benchmarks.

Run Ansible from the repository root:

```bash
ansible-playbook benchmark.yml --limit gpu1.example.com --diff
```

Optional overrides in ignored `host_vars/<host>.yml`:

```yaml
# llama_benchy_version: "0.4.0" # Benchmark release
# llama_benchy_venv: /opt/llama-benchy-env # Separate client environment
```

## 1. llama-benchy

### 1.1 Configure the client

For manual installation, use a checkout on the benchmark host. Execute the
following cells in the same Bash shell; inventory files are unnecessary.

```bash {name=bench-settings}
export BENCHY_VERSION="0.4.0" # Benchmark release
export BENCHY_VENV="/opt/llama-benchy-env" # Client environment
export BASE_URL="http://127.0.0.1:8000/v1" # API endpoint
export MODEL_ID="org/model" # Model publisher and artifact
export SERVED_MODEL="your-model" # Exact /v1/models ID
export TOKENIZER="/opt/models/your-model" # Model tokenizer directory
export MAX_CLIENTS=1 # Concurrency ceiling for the selected context profile
export RESULTS="$(mktemp -d /var/tmp/llama-benchy.XXXXXX)" # New attempt directory
BENCH_ARGS=(
  --base-url "$BASE_URL" --model "$MODEL_ID"
  --served-model-name "$SERVED_MODEL" --tokenizer "$TOKENIZER"
  --tg 256 --depth 0 --exact-tg --latency-mode generation --skip-coherence
)
```

### 1.2 Install the client and runner

<!-- ops-step
id: llama_benchy.prerequisites
ansible_task: llama_benchy.prerequisites | Install Python environment support
kind: package
-->
<!-- ops-step
id: llama_benchy.install
ansible_task: llama_benchy.install | Install llama-benchy in an isolated environment
kind: package
-->
<!-- ops-step
id: llama_benchy.command
ansible_task: llama_benchy.command | Expose the benchmark command
kind: command
-->
<!-- ops-step
id: llama_benchy.runner
ansible_task: llama_benchy.runner | Install the queue-monitored benchmark runner
kind: command
-->

```bash {name=bench-install}
sudo apt-get update
sudo apt-get install -y python3-venv ca-certificates
sudo python3 -m venv "$BENCHY_VENV"
sudo "$BENCHY_VENV/bin/pip" install "llama-benchy==$BENCHY_VERSION" matplotlib
sudo ln -sfn "$BENCHY_VENV/bin/llama-benchy" /usr/local/bin/llama-benchy
sudo install -m 755 roles/llama_benchy/files/llama-benchy-run.py \
  /usr/local/bin/llama-benchy-run
sudo install -m 755 roles/llama_benchy/files/llama-benchy-plot.py \
  /usr/local/bin/llama-benchy-plot.py
```

### 1.3 Run a quick short test

Use an idle server. The
[512-input/256-output profile](https://github.com/Ramshreyas/EXD/blob/main/episodes/Ep04/ep4-inference-benchmarking-continued.md)
uses the default Sherlock Holmes corpus. One measured batch after warmup is a
quick throughput check, not a quality evaluation.

```bash {name=bench-short}
llama-benchy-run --metrics-url "${BASE_URL%/v1}/metrics" \
  --output "$RESULTS/short" --max-concurrency "$MAX_CLIENTS" -- \
  "${BENCH_ARGS[@]}" --pp 512 --runs 1
```

### 1.4 Run the standard protocol

| Profile | Requested input tokens | Output tokens | Measured batches |
|---|---:|---:|---:|
| Short | 512 | 256 | 3 |
| Long | 32768 | 256 | 3 |

Run each profile separately. Set `MAX_CLIENTS` for its available capacity;
Short parallelism does not establish Long capacity. Requests inherit the
server's production sampling and thinking settings; do not force temperature 0
or disable thinking for a speed comparison. Record actual API token usage:
chat-template adaptation can change the requested input count.

Max is a separate, explicitly agreed context-capacity run, outside the default
Short/Long sequence. Agree its input and output budgets within the configured
native context first; do not enable YaRN or use the advertised extended window
automatically.

```bash {name=bench-standard}
PP=32768 # Long; Short uses 512
llama-benchy-run --metrics-url "${BASE_URL%/v1}/metrics" \
  --output "$RESULTS/pp-$PP" --max-concurrency "$MAX_CLIENTS" \
  --label "Input target: $PP tokens" -- \
  "${BENCH_ARGS[@]}" --pp "$PP" --runs 3
```

The runner uses 1, 2, 4, 8, ... clients, then the supplied ceiling M when it lies
between powers N and 2N. It samples live metrics every 50 ms and aborts a case on
observed queuing or preemption, including warmup and prefill. That case is
excluded; higher counts are not attempted. Between the last successful and first
excluded counts, it bisects the remaining interval without repeating counts to
find the largest verified queue-free count for this profile.
`max-num-seqs` is a server admission limit; clients are actual simultaneous API
requests. The runner does not change server settings or reduce context.

To extend completed cases, add `--resume`, reuse the same `--output` directory
and raise `--max-concurrency`. Keep the native arguments in the same order and
the server configuration unchanged. Existing measurements are retained; the
next power of two is measured without repeating completed counts. A run with
excluded or failed cases cannot be resumed as a higher-capacity configuration.

Every measured batch must have a common decode interval: the latest first token
must precede the earliest last token across all C requests. A running-request
sample must also show C active requests within that interval; a peak elsewhere
does not prove decode parallelism. Missing overlap is reported as
`parallelism unverified`; the runner does not lengthen responses automatically.
When request events show a request awaiting its first token, a queue is labelled
`prefill queue`. Warmup has no native request events, so its queue phase remains
unobserved. Both queues invalidate the case; neither establishes a GPU memory
limit. Zero queue means none observed at the recorded metrics interval.

The source measurements are `c*/result.json`, `c*/progress.jsonl` and
`c*/metrics.jsonl`. `index.json` records commands and case status; logs and
streamed answers stay alongside them. Success requires `complete` status and
observed parallelism at the requested count in every measured batch, with zero
observed waiting and no increase in preemptions throughout the case. Missing
metrics or interrupted runs are not successes.

For each measured batch, set `start = latest first token` and
`end = earliest last token` across all C requests. Count the observed SSE tokens
received in `(start, end]`, without interpolation. Aggregate decode is that count
divided by `end - start`; decode per request is the aggregate divided by C.
Average the batch rates. All requests have passed prefill before this window.
TTFT is measured separately from each HTTP request's start to its first token,
using `request_first_token.ttft_s`, and averaged across requests.

Each run writes `throughput.json` with batch windows, token counts, TTFT and
source hashes, plus `throughput.png` and `throughput.svg` with three panels:
aggregate decode, decode per request in the same window, and TTFT. The native
`tg_throughput` window can include other requests' prefill and is not used as
pure decode. Missing observed token counts or overlap prevent recalculation;
there is no fallback to the native rate. Failed or queued cases are excluded,
never plotted as zero. Server settings stay fixed; use `--label` for their chart
caption. Hollow markers preserve output-count discrepancies from the client.

Keep the server launch configuration, model revision/quantization, GPU and builds
with each attempt. Compare matched workloads; report aggregate and per-request
decode, TTFT and prefill separately. Retain original counts, including any
llama-benchy token-count discrepancy; never silently correct measurements.

Keep earlier Long measurements under their original configuration identity.
Preserve source measurements; a changed serving profile requires a separate attempt.

### 1.5 Recalculate saved results

Regenerate the derived summary and graphs without contacting the server or
starting a benchmark. Use the updated plotter and one existing profile directory:

```bash {name=bench-replot}
"$BENCHY_VENV/bin/python" /usr/local/bin/llama-benchy-plot.py \
  "$RESULTS/pp-$PP"
```
