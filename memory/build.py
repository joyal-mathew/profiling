import sys
import os

sys.path.append(os.path.dirname(os.getcwd()))
from common import Runner, Benchmark, command, tqdm, trange, confidence_interval_95

from random import shuffle

PERF_NEEDLE = "frequency clocks"
CACHE_MISS_EVENT = "cache-misses"
TLB_MISS_EVENT = "dTLB-load-misses"

PERF_ARGS = ["taskset", "-c", "0", "chrt", "-f", "99", "perf", "stat", "-e"]
CACHE_MISS_ARGS = PERF_ARGS + [CACHE_MISS_EVENT]
TLB_MISS_ARGS = PERF_ARGS + [TLB_MISS_EVENT]

def test_idle_latency(size):
    bench = Benchmark({
        "ns": lambda p: float(next(l for l in p.stdout.decode("utf-8").splitlines() if PERF_NEEDLE in l).split()[-2]),
        "cycles": lambda p: float(next(l for l in p.stdout.decode("utf-8").splitlines() if PERF_NEEDLE in l).split()[3]),
    })

    b = bench.benchmark(["mlc", "--idle_latency", "-b" + str(size)], num_runs=1)

    return b["ns"][0], b["cycles"][0]


def sweep(op, pattern, stride):
    bench = Benchmark({
        "metric": lambda p: float(p.stdout.decode("utf-8").splitlines()[-1].split()[1]),
    })

    cmd = ["mlc", "-e"]
    if pattern == "rand":
        cmd.append("-r" if op == "latency_matrix" else "-U")

    cmd.append("-l" + str(stride))
    cmd.append("--" + op)

    return bench.benchmark(cmd, num_runs=1)["metric"][0]


def sweep_ratio(opt):
    bench = Benchmark({
        "bw": lambda p: float(p.stdout.decode("utf-8").splitlines()[-1].split()[1]),
    })

    return bench.benchmark(["mlc", "-" + opt, "--bandwidth_matrix"], num_runs=1)["bw"][0]


def zero_queue_baselines():
    sizes = [
        192,
        3 * 1024,
        16 * 1024,
        32 * 1024,
    ]

    run_info = { s: None for s in sizes }
    runs = list(run_info)
    shuffle(runs)

    for r in tqdm(runs):
        run_info[r] = test_idle_latency(r)

    with open("data/zero_queue_baselines.dat", "w") as f:
        for s in sizes:
            print(s, *run_info[s], file=f)


def pattern_and_granularity():
    ops = ["latency_matrix", "bandwidth_matrix"]
    patterns = ["rand", "seq"]
    strides = [64, 256, 1024]

    run_info = {}

    for op in ops:
        for p in patterns:
            for s in strides:
                run_info[(op, p, s)] = None
    
    runs = list(run_info)
    shuffle(runs)

    for op, p, s in tqdm(runs):
        run_info[(op, p, s)] = sweep(op, p, s)

    for op in ops:
        with open(f"data/{op}", "w") as f:
            print("[", file=f)
            for p in patterns:
                out = [run_info[(op, p, s)] for s in strides]
                print(out, "", sep=",", file=f)
            print("]", file=f)


def mix_sweep():
    opts = [
        ("R",  "1:0"),
        ("W7", "2:1"),
        ("W8", "1:1"),
        ("W6", "0:1"),
    ]

    run_info = { o: None for o, _ in opts }
    runs = list(run_info)
    shuffle(runs)

    for r in tqdm(runs):
        run_info[r] = sweep_ratio(r)

    with open("data/rw_ratio_sweep.dat", "w") as f:
        for o, label in opts:
            print(label, run_info[o], file=f)


def intensity_sweep():
    print("Sweeping intensity...", flush=True)
    output = command(["mlc", "--loaded_latency"], capture_output=True).stdout
    lines = output.decode("utf-8").splitlines()
    index = next(i for i, l in enumerate(lines) if set(l.strip()) == {"="})

    data = [tuple(map(float, l.split()[1:])) for l in lines[index + 1:]]
    # data.sort()

    with open("data/intensity_sweep.dat", "w") as f:
        for d in data:
            print(*d, file=f)


def cache_miss():
    bench = Benchmark({
        "time": lambda p: int(p.stdout),
        "misses": lambda p: int(next(l for l in p.stderr.decode("utf-8").splitlines() if CACHE_MISS_EVENT in l).split()[0].replace(",", ""))
    })

    limit = 1024
    spacing = 32

    n = "1m"
    sparses = list(range(spacing, limit + spacing, spacing)) + [0]

    run_info = { s: None for s in sparses }
    runs = list(run_info)
    shuffle(runs)

    for r in tqdm(runs):
        run_info[r] = bench.benchmark(CACHE_MISS_ARGS + ["build/main", n, str(r), "cache"], num_runs=20)

    data = []
    for info in run_info.values():
        time = info["time"]
        misses = info["misses"]

        ci = confidence_interval_95(time).item()
        mr = misses.mean().item()
        t = time.mean().item()

        data.append((mr, t, t - ci, t + ci))

    data.sort()

    with open("data/cache_miss_effect.dat", "w") as f:
        for t in data:
            print(*t, file=f)


def tlb_miss():
    bench = Benchmark({
        "time": lambda p: int(p.stdout),
        "misses": lambda p: int(next(l for l in p.stderr.decode("utf-8").splitlines() if TLB_MISS_EVENT in l).split()[0].replace(",", ""))
    })

    limit = 1024
    spacing = 32

    n = "1m"
    sparses = list(range(spacing, limit + spacing, spacing)) + [0]

    run_info = { s: None for s in sparses }
    runs = list(run_info)
    shuffle(runs)

    for r in tqdm(runs):
        run_info[r] = bench.benchmark(TLB_MISS_ARGS + ["build/main", n, str(r), "tlb"], num_runs=10)

    data = []
    for info in run_info.values():
        time = info["time"]
        misses = info["misses"]

        ci = confidence_interval_95(time).item()
        mr = misses.mean().item()
        t = time.mean().item()

        data.append((mr, t, t - ci, t + ci))

    data.sort()

    with open("data/tlb_miss_effect.dat", "w") as f:
        for t in data:
            print(*t, file=f)


if __name__ == "__main__":
    command(["./build.sh"])

    benchmark_names = [
        "zero_queue_baselines",
        "pattern_and_granularity",
        "mix_sweep",
        "intensity_sweep",
        "cache_miss",
        "tlb_miss",
    ]

    runner = Runner(benchmark_names, globals())
    runner.run(None if len(sys.argv) < 2 else sys.argv[1])
