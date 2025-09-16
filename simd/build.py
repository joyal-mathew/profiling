from tqdm import tqdm, trange
from random import shuffle
import numpy as np
import scipy.stats as st
import subprocess
import sys


FLOP_EVENT = "fp_ret_sse_avx_ops.all"
PERF_ARGS = ["taskset", "-c", "0", "chrt", "-f", "99", "perf", "stat", "-e", FLOP_EVENT]


def align(addr, n):
    return (addr + n - 1) // n * n


def command(args, **kwargs):
    kwargs.setdefault("check", True)
    return subprocess.run(args, **kwargs)


def expand(n):
    try:
        return int(n)
    except ValueError:
        posfixes = ["k", "m"]
        return int(n[:-1]) * 1024 ** (posfixes.index(n[-1].lower()) + 1)


class Benchmark(object):
    def __init__(self, metrics):
        self.metrics = metrics

    def benchmark(self, cmd_args, num_runs):
        results = { k: np.zeros(num_runs) for k in self.metrics }

        for i in trange(num_runs, leave=False):
            process = command(cmd_args, capture_output=True)
            for metric, extract in self.metrics.items():
                try:
                    results[metric][i] = extract(process)
                except:
                    print("\n===CMD===")
                    print(cmd_args)
                    print("\n===STDOUT===")
                    print(process.stdout.decode("utf-8"))
                    print("\n===STDERR===")
                    print(process.stderr.decode("utf-8"))
                    raise

        return results


def compute(f, a, b):
     x = f(a, b)
     ci = tuple(map(float, st.bootstrap((a, b), f, vectorized=True).confidence_interval))
     return x, ci


def confidence_interval_95(data):
    return 1.96 * data.std() / np.sqrt(len(data))


N_RUNS = 20

L1 = 192 * 1024
L2 = 3 * 1024 ** 2
L3 = 16 * 1024 ** 2

CPU_FREQ = 4.3e9

flops_per_elem = {
    "dot": 4,
    "fma": 4,
    "conv1d": 7,
}

bench = Benchmark({
    "time": lambda p: int(p.stdout),
    "flop_count": lambda p: int(next(l for l in p.stderr.decode("utf-8").splitlines() if FLOP_EVENT in l).split()[0].replace(",", ""))
})

def vector_speedup():
    ns = ["20k", "200k", "1m", "4m"]
    ops = ["fma", "dot", "conv1d"]
    exes = ["scalar", "vectorized"]

    run_info = {}

    for n in ns:
        for op in ops:
            for exe in exes:
                run_info[(n, op, exe)] = None

    runs = list(run_info)
    shuffle(runs)

    for n, op, exe in tqdm(runs):
        run_info[(n, op, exe)] = bench.benchmark(PERF_ARGS + ["build/" + exe, n, op], N_RUNS)

    for op in ops:
        speedup_file = f"data/{op}_speedup.dat"
        scalar_file = f"data/{op}_scalar_gflops.dat"
        vector_file = f"data/{op}_vector_gflops.dat"
        with open(speedup_file, "w") as f_spd, open(scalar_file, "w") as f_scl, open(vector_file, "w") as f_vct:
            for n in ns:
                m = expand(n)
                scalar = run_info[(n, op, "scalar")]
                vector = run_info[(n, op, "vectorized")]

                speedup, speedup_ci = compute(lambda a, b, axis=0: a.mean(axis=axis) / b.mean(axis=axis), scalar["time"], vector["time"])
                scalar_gflops, scalar_gflops_ci = compute(lambda a, b, axis=0: a.mean(axis=axis) / b.mean(axis=axis), scalar["flop_count"], scalar["time"])
                vector_gflops, vector_gflops_ci = compute(lambda a, b, axis=0: a.mean(axis=axis) / b.mean(axis=axis), vector["flop_count"], vector["time"])

                print(m / 1024, speedup, *speedup_ci, file=f_spd)
                print(m / 1024, scalar_gflops, *scalar_gflops_ci, file=f_scl)
                print(m / 1024, vector_gflops, *vector_gflops_ci, file=f_vct)


def cross_cache():
    op = "dot"
    n_per_level = 5

    L0 = 4 * 1024 # minimum test n
    L4 = L3 * 2 # maximum test n

    l1_ns = [align(L0 + (L1 - L0) * i // n_per_level, 32) for i in range(1, n_per_level)]
    l2_ns = [align(L1 + (L2 - L1) * i // n_per_level, 32) for i in range(1, n_per_level)]
    l3_ns = [align(L2 + (L3 - L2) * i // n_per_level, 32) for i in range(1, n_per_level)]
    l4_ns = [align(L3 + (L4 - L3) * i // n_per_level, 32) for i in range(1, n_per_level)]

    ns = l1_ns + l2_ns + l3_ns + l4_ns

    run_info = { n: None for n in ns }

    runs = list(run_info)
    shuffle(runs)

    for n in tqdm(runs):
        run_info[n] = bench.benchmark(PERF_ARGS + ["build/vectorized", str(n), op], N_RUNS)

    with open("data/dot_cross_cache_gflops.dat", "w") as g_f, open("data/dot_cross_cache_cpe.dat", "w") as cpe_f:
        for n, info in run_info.items():
            gflops, gflops_ci = compute(lambda a, b, axis=0: a.mean(axis=axis) / b.mean(axis=axis), info["flop_count"], info["time"])
            c = CPU_FREQ * flops_per_elem[op]
            cpe = c / gflops
            cpe_ci = tuple(c / x for x in gflops_ci)

            print(n / 1024, gflops, *gflops_ci, file=g_f)
            print(n / 1024, cpe, *cpe_ci, file=cpe_f)


if __name__ == "__main__":
    command(["./build.sh"])

    benchmark_names = [
        "vector_speedup",
        "cross_cache",
    ]

    g = globals()
    benchmarks = { name: g[name] for name in benchmark_names }

    to_run = sys.argv[1]
    if to_run == "!all":
        for name, bench_func in benchmarks.items():
            print("Running", name)
            bench_func()
    else:
        benchmarks[to_run]()
