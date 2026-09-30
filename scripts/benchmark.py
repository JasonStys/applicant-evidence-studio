"""Reproducible synthetic ranking benchmark: time, throughput and traced Python allocations."""

# Index: argparse@4, json@5, platform@6, statistics@7, time@8, tracemalloc@9, Path@10, samples@12, rank@13, main@16, main.parser@18, main.args@20, main.jobs@21, main.samples_data@21, main.results@22, main.size@23, main.applicants@24, main.index@26, main.timings@28, main._@29, main.start@30, main.ranked@31, main.row@33, main._@36, main.peak@36, main.median@38, main.report@48
import argparse
import json
import platform
import statistics
import time
import tracemalloc
from pathlib import Path

from app.demo import samples
from app.review import rank


def main():
    """Measure bounded 100/1,000/10,000-record ranking; numbers are observations, not production SLAs."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path("artifacts/benchmark.json"))
    args = parser.parse_args()
    jobs, samples_data = samples()
    results = []
    for size in [100, 1000, 10000]:
        applicants = [
            samples_data[index % len(samples_data)].model_copy(update={"id": f"A{index:05}"})
            for index in range(size)
        ]
        timings = []
        for _ in range(3):
            start = time.perf_counter()
            ranked = rank(applicants, jobs[0])
            timings.append(time.perf_counter() - start)
            assert len(ranked) == size and all(0 <= row["score"] <= 100 for row in ranked)
        tracemalloc.start()
        rank(applicants, jobs[0])
        _, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        median = statistics.median(timings)
        results.append(
            {
                "applicants": size,
                "seconds": timings,
                "median_seconds": median,
                "records_per_second": size / median,
                "peak_traced_bytes": peak,
            }
        )
    report = {
        "python": platform.python_version(),
        "platform": platform.platform(),
        "repeats": 3,
        "scope": "in-process scoring/sorting; excludes DB loading, parsing, network, concurrent users and AI",
        "results": results,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    if results[-1]["median_seconds"] > 30:
        raise SystemExit("Generous 30-second regression ceiling exceeded")


if __name__ == "__main__":
    main()
