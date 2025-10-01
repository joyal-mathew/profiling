import subprocess
import numpy as np

try:
    from tqdm import tqdm, trange
except ImportError:
    print("[WARN]\ttdqm not found, progress will not be displayed")

    def tqdm(x):
        return x

    def trange(n, **kwargs):
        return range(n)


def command(args, **kwargs):
    kwargs.setdefault("check", True)
    return subprocess.run(args, **kwargs)


class Benchmark(object):
    def __init__(self, metrics):
        self.metrics = metrics

    def benchmark(self, cmd_args, num_runs=10):
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


class Runner(object):
    def __init__(self, names, scope):
        self.benchmarks = { name: scope[name] for name in names }

    def run(self, name):
        if name is None:
            for name, bench_func in tqdm(self.benchmarks.items()):
                print("Running", name)
                bench_func()
        else:
            self.benchmarks[name]()


def confidence_interval_95(data):
    return 1.96 * data.std() / np.sqrt(len(data))
