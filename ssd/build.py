import sys
import os

sys.path.append(os.path.dirname(os.getcwd()))
from common import Runner, Benchmark, command, tqdm, trange, confidence_interval_95


def block_sweep():
    sizes = [4, 16, 32, 64, 128, 256]

    with open("data/rand_block_sweep.txt", "w") as f:
        for bs in tqdm(sizes):
            lines = command(["fio", "--rw=randread", f"--blocksize={bs}Ki", "scripts/block_size_sweep.fio"], capture_output=True).stdout.decode("utf-8").splitlines()
            for line in lines:
                if any(x in line for x in [" bs=", "read:", " lat (usec):"]):
                    print(line.strip(), file=f)

    with open("data/seq_block_sweep.txt", "w") as f:
        for bs in tqdm(sizes):
            lines = command(["fio", "--rw=read", f"--blocksize={bs}Ki", "scripts/block_size_sweep.fio"], capture_output=True).stdout.decode("utf-8").splitlines()
            for line in lines:
                if any(x in line for x in [" bs=", "read:", " lat (usec):"]):
                    print(line.strip(), file=f)


def rw_ratio_sweep():
    ratios = [100, 70, 50, 0]

    with open("data/rw_ratio_sweep.txt", "w") as f:
        for r in tqdm(ratios):
            lines = command(["fio", f"--rwmixread={r}", "scripts/rw_ratio_sweep.fio"], capture_output=True).stdout.decode("utf-8").splitlines()
            for line in lines:
                if any(x in line for x in [" bs=", "read:", "write:", " lat (usec):"]):
                    print(line.strip(), file=f)


def qd_sweep():
    qds = list(range(1, 6))

    with open("data/qd_sweep.txt", "w") as f:
        for qd in tqdm(qds):
            lines = command(["fio", f"--iodepth={qd}", "scripts/qd_sweep.fio"], capture_output=True).stdout.decode("utf-8").splitlines()
            for line in lines:
                if any(x in line for x in [" bs=", "read:", " lat (usec):"]):
                    print(line.strip(), file=f)


if __name__ == "__main__":
    benchmark_names = [
        "block_sweep",
        "rw_ratio_sweep",
        "qd_sweep",
    ]

    runner = Runner(benchmark_names, globals())
    runner.run(None if len(sys.argv) < 2 else sys.argv[1])
