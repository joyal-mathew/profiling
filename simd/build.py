from random import shuffle
import subprocess
import sys
import math

import numpy as np

try:
    from tqdm import tqdm, trange
except ImportError:
    print("[WARN]\ttdqm not found, progress will not be displayed")

    def tqdm(x):
        return x

    def trange(n, **kwargs):
        return range(n)


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


def confidence_interval_95(data):
    return 1.96 * data.std() / np.sqrt(len(data))


def f_mean(a, b, axis=0):
    return a.mean(axis=axis) / b.mean(axis=axis)


try:
    import scipy.stats as st

    def compute_ci(a, b):
        return tuple(map(float, st.bootstrap((a, b), f_mean, vectorized=True).confidence_interval))
except ImportError:
    print("[WARN]\tscipy not found, using delta method to approximate confidence interval")

    def compute_ci(a, b):
        mu_a, mu_b = a.mean(), b.mean()
        var_a, var_b = a.var(), b.var()
        r = f_mean(a, b)
        var = var_a * (1 / mu_b) ** 2 + var_b * (mu_a / mu_b ** 2) ** 2
        ci = 1.96 * math.sqrt(var)
        return r - ci, r + ci


def compute_ratio(a, b):
     x = f_mean(a, b)
     ci = compute_ci(a, b)
     return x, ci


N_RUNS = 10

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

                speedup, speedup_ci = compute_ratio(scalar["time"], vector["time"])
                scalar_gflops, scalar_gflops_ci = compute_ratio(scalar["flop_count"], scalar["time"])
                vector_gflops, vector_gflops_ci = compute_ratio(vector["flop_count"], vector["time"])

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
            gflops, gflops_ci = compute_ratio(info["flop_count"], info["time"])
            c = CPU_FREQ * flops_per_elem[op]
            cpe = c / gflops
            cpe_ci = tuple(c / x for x in gflops_ci)

            print(n / 1024, gflops, *gflops_ci, file=g_f)
            print(n / 1024, cpe, *cpe_ci, file=cpe_f)


def unaligned_and_tail():
    ns = ["2m"]
    ops = ["fma", "dot", "conv1d"]
    exes = ["vectorized", "unaligned"]

    tail_ns = ["32", "48"]
    tail_rounds = "1k"

    run_info = {}

    for n in ns:
        for op in ops:
            for exe in exes:
                run_info[(n, op, exe, "1")] = None

    for n in tail_ns:
        for op in ops:
            run_info[(n, op, "vectorized", tail_rounds)] = None

    runs = list(run_info)
    shuffle(runs)

    for n, op, exe, rounds in tqdm(runs):
        run_info[(n, op, exe, rounds)] = bench.benchmark(PERF_ARGS + ["build/" + exe, n, op, "-r", rounds], N_RUNS)

    with open("data/align_speedup.dat", "w") as f:
        for op in ops:
            n = ns[0]
            m = expand(n)
            vector = run_info[(n, op, "vectorized", "1")]
            unaligned = run_info[(n, op, "unaligned", "1")]

            gflops_v, gflops_v_ci = compute_ratio(vector["flop_count"], vector["time"])
            gflops_u, gflops_u_ci = compute_ratio(unaligned["flop_count"], unaligned["time"])

            print(op, gflops_v, *gflops_v_ci, gflops_u, *gflops_u_ci, file=f)

    with open(f"data/tail_effect.dat", "w") as f:
        for op in ops:
            m = expand(n)
            clean = run_info[(tail_ns[0], op, "vectorized", tail_rounds)]
            tail = run_info[(tail_ns[1], op, "vectorized", tail_rounds)]

            gflops, gflops_ci = compute_ratio(clean["flop_count"], clean["time"])
            gflops_t, gflops_t_ci = compute_ratio(tail["flop_count"], tail["time"])

            print(op, gflops, *gflops_ci, gflops_t, *gflops_t_ci, file=f)


def strided_and_gather():
    n = "2m"
    ops = ["fma", "dot", "conv1d"]
    access = ["-u", "-s", "-g"]

    run_info = {}

    for op in ops:
        for a in access:
            run_info[(op, a)] = None

    runs = list(run_info)
    shuffle(runs)

    for op, a in tqdm(runs):
        run_info[(op, a)] = bench.benchmark(PERF_ARGS + ["build/vectorized", n, op, a], N_RUNS)

    with open("data/strided_gather_effects.dat", "w") as f:
        m = expand(n)
        for op in ops:
            unit = run_info[(op, "-u")]
            strided = run_info[(op, "-s")]
            gather = run_info[(op, "-g")]

            gflops_u, gflops_u_ci = compute_ratio(unit["flop_count"], unit["time"])
            gflops_s, gflops_s_ci = compute_ratio(strided["flop_count"], strided["time"])
            gflops_g, gflops_g_ci = compute_ratio(gather["flop_count"], gather["time"])

            print(op, gflops_u, *gflops_u_ci, gflops_s, *gflops_s_ci, gflops_g, *gflops_g_ci, file=f)


def data_type():
    mbs = 2
    ops = ["fma", "dot", "conv1d"]
    fl_n = str(mbs) + "m"
    db_n = str(mbs // 2) + "m"
    infos = [
        ["vectorized", fl_n],
        ["double", db_n],
    ]

    run_info = {}

    for op in ops:
        for exe, n in infos:
            run_info[(n, op, exe)] = None

    runs = list(run_info)
    shuffle(runs)

    for n, op, exe in tqdm(runs):
        run_info[(n, op, exe)] = bench.benchmark(PERF_ARGS + ["build/" + exe, n, op], N_RUNS)

    with open("data/data_type_effect.dat", "w") as f:
        for op in ops:
            fl = run_info[(fl_n, op, "vectorized")]
            db = run_info[(db_n, op, "double")]

            gflops_f, gflops_f_ci = compute_ratio(fl["flop_count"], fl["time"])
            gflops_d, gflops_d_ci = compute_ratio(db["flop_count"], db["time"])

            print(op, gflops_f, *gflops_f_ci, gflops_d, *gflops_d_ci, file=f)


if __name__ == "__main__":
    command(["./build.sh"])

    benchmark_names = [
        "vector_speedup",
        "cross_cache",
        "unaligned_and_tail",
        "strided_and_gather",
        "data_type",
    ]

    g = globals()
    benchmarks = { name: g[name] for name in benchmark_names }

    to_run = None if len(sys.argv) < 2 else sys.argv[1]
    if to_run is None:
        for name, bench_func in tqdm(benchmarks.items()):
            print("Running", name)
            bench_func()
    else:
        benchmarks[to_run]()
