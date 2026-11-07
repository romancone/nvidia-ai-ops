#!/usr/bin/env python3
"""Plot common-window decode and TTFT from saved llama-benchy events."""

import argparse
import hashlib
import json
from pathlib import Path
from statistics import mean

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator


def common_decode(events, concurrency):
    requests = {}
    for event in events:
        kind, request_id = event["type"], event.get("request_id")
        if kind == "request_start":
            requests[request_id] = {"run": event["run_index"], "tokens": [],
                                    "ttft": None, "output": None, "error": ""}
        elif request_id in requests:
            request = requests[request_id]
            if kind == "tokens" and event["count"] > 0:
                if event.get("estimated"):
                    raise ValueError("Common decode requires observed SSE token counts")
                request["tokens"].append((event["ts"], event["count"]))
            elif kind == "request_first_token":
                request["ttft"] = event["ttft_s"]
            elif kind == "request_end":
                request.update(output=event["total_tokens"], error=event.get("error", ""))

    batches = {}
    for request in requests.values():
        batches.setdefault(request["run"], []).append(request)
    measured = []
    for run, batch in sorted(batches.items()):
        if len(batch) != concurrency or any(
                not r["tokens"] or r["ttft"] is None or r["error"]
                or sum(n for _, n in r["tokens"]) != r["output"] for r in batch):
            raise ValueError("Common decode requires complete request events for every client")
        start = max(r["tokens"][0][0] for r in batch)
        end = min(r["tokens"][-1][0] for r in batch)
        if end <= start:
            raise ValueError("Requests have no common decode window")
        counts = [sum(n for t, n in r["tokens"] if start < t <= end) for r in batch]
        aggregate = sum(counts) / (end - start)
        measured.append({"run_index": run, "start": start, "end": end,
                         "seconds": end - start, "tokens_per_request": counts,
                         "aggregate_tps": aggregate, "per_request_tps": aggregate / concurrency,
                         "ttft_seconds": [r["ttft"] for r in batch]})
    if not measured:
        raise ValueError("No measured request events")
    return {"aggregate_tps": mean(b["aggregate_tps"] for b in measured),
            "per_request_tps": mean(b["per_request_tps"] for b in measured),
            "ttft_seconds": mean(t for b in measured for t in b["ttft_seconds"]),
            "batches": measured}


def draw(directory):
    index = json.loads((directory / "index.json").read_text())
    points, input_counts, output_counts, excluded = [], [], [], []
    summary = {"definition": "common_decode_v1", "interval": "(latest first token, earliest last token]",
               "label": index.get("label", ""), "index_sha256": hashlib.sha256(
                   (directory / "index.json").read_bytes()).hexdigest(), "cases": [], "excluded": []}
    model, profile = "llama-benchy", None
    for case in index["cases"]:
        count = case["concurrency"]
        if case["status"] != "complete":
            excluded.append(str(count))
            summary["excluded"].append({"concurrency": count, "status": case["status"]})
            continue
        native = json.loads((directory / case["result"]).read_text())
        rows = [row for row in native["benchmarks"] if not row["is_context_prefill_phase"]]
        if len(rows) != 1:
            raise ValueError("Plot one context profile per run")
        row = rows[0]
        key = (row["prompt_size"], row["context_size"], row["response_size"])
        if profile is not None and profile != key:
            raise ValueError("Cannot join different context profiles")
        model, profile = native["model"], key
        events = [json.loads(line) for line in
                  (directory / f"c{count}/progress.jsonl").read_text().splitlines()]
        ends = [event for event in events if event["type"] == "request_end"]
        input_counts.extend(event["prompt_tokens"] for event in ends)
        output_counts.extend(event["total_tokens"] for event in ends)
        mismatch = "--exact-tg" in case["command"] and any(
            event["total_tokens"] != row["response_size"] for event in ends)
        metric = common_decode(events, count)
        request_count = len((row.get("e2e_ttft") or {}).get("values", []))
        if len(metric["batches"]) * count != request_count:
            raise ValueError("Saved events do not cover every measured request")
        sources = [case["result"], f"c{count}/progress.jsonl"]
        summary["cases"].append({"concurrency": count, **metric, "source_sha256": {
            name: hashlib.sha256((directory / name).read_bytes()).hexdigest() for name in sources}})
        points.append((count, metric["aggregate_tps"], metric["per_request_tps"],
                       metric["ttft_seconds"], mismatch))

    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 12,
                         "axes.spines.top": False, "axes.spines.right": False,
                         "axes.spines.left": False, "axes.spines.bottom": False})
    fig, axes = plt.subplots(3, 1, figsize=(10, 9), dpi=160, sharex=True,
                             gridspec_kw={"height_ratios": [1.4, 1, 1]})
    fig.subplots_adjust(left=.12, right=.96, top=.8, bottom=.16, hspace=.24)
    fig.suptitle("Common-window decode and TTFT", x=.12, y=.97,
                 ha="left", fontsize=19, fontweight="bold")
    fig.text(.12, .91, model, fontsize=12, color="#344054")
    fig.text(.12, .865, index.get("label", ""), fontsize=11, color="#475467")
    for axis, metric, color, marker, label in zip(
            axes, (1, 2, 3), ("#2563eb", "#b54708", "#15803d"), ("o", "D", "s"),
            ("Aggregate decode, tok/s", "Per request, tok/s", "Mean TTFT, s")):
        axis.set_axisbelow(True)
        axis.grid(axis="y", color="#e5e7eb", linewidth=.8)
        axis.set_ylabel(label, labelpad=13, fontsize=11)
        axis.tick_params(axis="both", length=0, pad=8, labelsize=10)
        axis.yaxis.set_major_locator(MaxNLocator(nbins=4, integer=False))
        axis.set_ylim(bottom=0)
        if not points:
            axis.text(.5, .5, "No queue-free measurements", transform=axis.transAxes,
                      ha="center", color="#475467")
            continue
        x, y = [point[0] for point in points], [point[metric] for point in points]
        axis.plot(x, y, color=color, linewidth=2, zorder=2)
        axis.scatter(x, y, color=color, s=36, marker=marker, zorder=3)
        for point in points:
            if point[4]:
                axis.scatter(point[0], point[metric], facecolors="white", edgecolors=color,
                             linewidths=1.7, s=49, marker=marker, zorder=4)
        axis.axvline(x[-1], color="#667085", linestyle=(0, (3, 4)), linewidth=1)
        axis.set_xlim(.5, max(2, x[-1] + 1))
        axis.set_ylim(0, max(y) * 1.25)
        axis.annotate(f"{y[-1]:.1f}", (x[-1], y[-1]), xytext=(-4, 12),
                      textcoords="offset points", ha="center", fontsize=11, color=color)
    if points:
        axes[-1].set_xticks([point[0] for point in points])
    axes[-1].set_xlabel("Concurrent API requests", labelpad=13, fontsize=12)
    inputs = f"{min(input_counts):,}–{max(input_counts):,}" if input_counts else "unmeasured"
    outputs = f"{min(output_counts)}–{max(output_counts)}" if output_counts else "unmeasured"
    fig.text(.12, .08, f"Actual input: {inputs} tokens · reported output: {outputs} tokens",
             fontsize=9.5, color="#475467")
    note = f"Excluded concurrency: {', '.join(excluded)}" if excluded else "All requested cases completed"
    fig.text(.12, .055, note + f" · metrics interval: {index['poll_seconds']:g} s",
             fontsize=9.5, color="#475467")
    fig.text(.12, .03, "Observed SSE tokens in the common window · raw results preserved",
             fontsize=9.5, color="#475467")
    fig.text(.12, .005, "Hollow markers: output-count discrepancy", fontsize=9.5, color="#475467")
    for extension in ("png", "svg"):
        fig.savefig(directory / f"throughput.{extension}", facecolor="white")
    plt.close(fig)
    summary.update(model=model, profile=profile)
    (directory / "throughput.json").write_text(json.dumps(summary, indent=2) + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    draw(parser.parse_args().directory)
