#!/usr/bin/env python3
"""Run llama-benchy at increasing concurrency, stopping on vLLM queuing."""

import argparse
import json
import os
from pathlib import Path
import signal
import shutil
import subprocess
import time
import urllib.request


def snapshot(url):
    names = {
        "vllm:num_requests_running": "running",
        "vllm:num_requests_waiting": "waiting",
        "vllm:num_preemptions_total": "preemptions",
    }
    values = {key: 0.0 for key in names.values()}
    seen = set()
    with urllib.request.urlopen(url, timeout=5) as response:
        for line in response.read().decode().splitlines():
            name = line.split("{", 1)[0].split(" ", 1)[0]
            if name in names:
                values[names[name]] += float(line.rsplit(" ", 1)[1])
                seen.add(name)
    if seen != names.keys():
        raise RuntimeError("Running, waiting and preemption metrics are required")
    return {"time": time.time(), **values}


def stop(process):
    if process.poll() is None:
        try:
            os.killpg(process.pid, signal.SIGINT)
        except ProcessLookupError:
            process.wait()
            return
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGKILL)
            process.wait()


def requests(path):
    states = {}
    if not path.exists():
        return states
    with path.open() as stream:
        for line in stream:
            if not line.endswith("\n"):
                break
            event = json.loads(line)
            kind, request_id = event["type"], event.get("request_id")
            if kind == "request_start":
                states[request_id] = {"run": event["run_index"], "first": None,
                                      "last": None, "done": False, "error": ""}
            elif request_id in states:
                state = states[request_id]
                if kind == "tokens":
                    state["first"] = state["first"] or event["ts"]
                    state["last"] = event["ts"]
                elif kind == "request_end":
                    state.update(done=True, error=event.get("error", ""))
    return states


def decode_batches(directory, concurrency):
    batches = {}
    for state in requests(directory / "progress.jsonl").values():
        batches.setdefault(state["run"], []).append(state)
    evidence = []
    for run, batch in sorted(batches.items()):
        complete = len(batch) == concurrency and all(
            r["done"] and not r["error"] and r["first"] and r["last"] for r in batch)
        start = max(r["first"] for r in batch) if complete else None
        end = min(r["last"] for r in batch) if complete else None
        evidence.append({"run_index": run, "requests": len(batch),
                         "start": start, "end": end,
                         "overlap_seconds": max(0, end - start) if complete else 0,
                         "max_running": 0})
    with (directory / "metrics.jsonl").open() as trace:
        for line in trace:
            sample = json.loads(line)
            for batch in evidence:
                if batch["start"] is not None and batch["start"] <= sample["time"] <= batch["end"]:
                    batch["max_running"] = max(batch["max_running"], sample["running"])
    return evidence


def run_case(args, native_args, concurrency):
    directory = args.output / f"c{concurrency}"
    directory.mkdir()
    deadline = time.monotonic() + 10
    while True:
        before = snapshot(args.metrics_url)
        if not before["running"] and not before["waiting"]:
            break
        if time.monotonic() >= deadline:
            raise RuntimeError("Server has active requests; run on an idle server")
        time.sleep(0.05)
    command = ["llama-benchy", *native_args, "--concurrency", str(concurrency),
               "--save-result", str(directory / "result.json"), "--format", "json",
               "--emit-progress", str(directory / "progress.jsonl"),
               "--save-total-throughput-timeseries", "--exit-on-first-fail"]
    record = {"concurrency": concurrency, "command": command, "status": "complete",
              "result": f"c{concurrency}/result.json", "max_running": 0,
              "max_waiting": 0, "preemptions": 0, "samples": 0}
    (directory / "command.json").write_text(json.dumps(command, indent=2) + "\n")
    with (directory / "bench.log").open("w") as log, (directory / "metrics.jsonl").open("w") as trace:
        process = subprocess.Popen(command, stdout=log, stderr=subprocess.STDOUT,
                                   start_new_session=True)
        try:
            while True:
                sample = snapshot(args.metrics_url)
                trace.write(json.dumps(sample) + "\n")
                trace.flush()
                record["samples"] += 1
                record["max_running"] = max(record["max_running"], sample["running"])
                record["max_waiting"] = max(record["max_waiting"], sample["waiting"])
                record["preemptions"] = sample["preemptions"] - before["preemptions"]
                if record["preemptions"]:
                    record["status"] = "excluded: preemption"
                    break
                if sample["waiting"]:
                    active = [r for r in requests(directory / "progress.jsonl").values()
                              if not r["done"]]
                    phase = "prefill queue" if any(not r["first"] for r in active) else "queue"
                    record["status"] = f"excluded: {phase}"
                    record["queue_phase"] = "prefill" if phase == "prefill queue" else "unobserved"
                    break
                if process.poll() is not None:
                    break
                time.sleep(0.05)
        except KeyboardInterrupt:
            record["status"] = "interrupted"
        except Exception as error:
            record["status"] = f"monitor failed: {error}"
        finally:
            stop(process)
        record["returncode"] = process.returncode
    if record["status"] == "complete":
        if process.returncode:
            record["status"] = "benchmark failed"
        else:
            record["decode_batches"] = decode_batches(directory, concurrency)
            native = json.loads((directory / "result.json").read_text())
            request_counts = [len((row.get("e2e_ttft") or {}).get("values", []))
                for row in native["benchmarks"] if not row["is_context_prefill_phase"]]
            record["expected_batches"] = sum(n // concurrency for n in request_counts)
            if (not record["expected_batches"] or any(not n or n % concurrency for n in request_counts)
                    or len(record["decode_batches"]) != record["expected_batches"]
                    or any(b["overlap_seconds"] <= 0 or b["max_running"] < concurrency
                           for b in record["decode_batches"])):
                record["status"] = "parallelism unverified"
    return record


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--metrics-url", required=True, help="vLLM Prometheus endpoint")
    parser.add_argument("--output", type=Path, required=True, help="New result directory")
    parser.add_argument("--resume", action="store_true", help="Extend completed cases in the existing output")
    parser.add_argument("--max-concurrency", type=int, required=True, help="Client ceiling")
    parser.add_argument("--label", default="", help="Chart caption for the server configuration")
    parser.add_argument("benchy_args", nargs=argparse.REMAINDER, help="llama-benchy arguments after --")
    args = parser.parse_args()
    if args.max_concurrency < 1:
        parser.error("--max-concurrency must be positive")
    args.output = args.output.resolve()
    native_args = args.benchy_args
    if native_args[:1] == ["--"]:
        native_args = native_args[1:]
    if args.resume:
        index = json.loads((args.output / "index.json").read_text())
        records = index["cases"]
        prefix = ["llama-benchy", *native_args]
        if (index["metrics_url"] != args.metrics_url or not records
                or any(c["status"] != "complete" or c["command"][:len(prefix)] != prefix
                       or c["command"][len(prefix):len(prefix) + 1] != ["--concurrency"]
                       for c in records)):
            parser.error("Resume requires completed cases and identical native arguments in the same order")
        verified = max(c["concurrency"] for c in records)
        if args.max_concurrency <= verified:
            parser.error("Set a concurrency ceiling above the completed cases")
        args.label = args.label or index.get("label", "")
        concurrency = min(1 << verified.bit_length(), args.max_concurrency)
    else:
        args.output.mkdir(parents=True, exist_ok=False)
        records, concurrency, verified = [], 1, 0
    excluded = None
    while True:
        print(json.dumps({"concurrency": concurrency, "status": "running"}), flush=True)
        try:
            record = run_case(args, native_args, concurrency)
        except (OSError, RuntimeError, ValueError) as error:
            record = {"concurrency": concurrency, "status": f"failed: {error}"}
        records.append(record)
        (args.output / "index.json").write_text(json.dumps({
            "label": args.label, "metrics_url": args.metrics_url,
            "poll_seconds": 0.05, "rule": "no queue throughout; common decode in every measured batch",
            "cases": records,
        }, indent=2) + "\n")
        print(json.dumps(record), flush=True)
        if record["status"] == "complete":
            verified = concurrency
        elif record["status"].startswith("excluded:"):
            excluded = concurrency
        else:
            break
        if excluded is not None:
            if excluded - verified <= 1:
                break
            concurrency = (verified + excluded) // 2
        elif concurrency == args.max_concurrency:
            break
        else:
            concurrency = min(concurrency * 2, args.max_concurrency)
    python = Path(shutil.which("llama-benchy")).resolve().with_name("python")
    plot = Path(__file__).resolve().with_name("llama-benchy-plot.py")
    chart = subprocess.run([str(python), str(plot), str(args.output)])
    return int(not verified or chart.returncode != 0 or
               record["status"] not in ("complete", "excluded: queue", "excluded: prefill queue", "excluded: preemption"))


if __name__ == "__main__":
    raise SystemExit(main())
