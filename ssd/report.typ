#import "@local/basic:0.1.0": *

#show: project.with(
    title: "SSD Profiling",
    authors: ("Joyal Mathew",),
    date: today,
)

= Experiments

Experiments were done on a test partition using the Flexible I/O Tester (FIO).

== Zero-Queue Baselines

FIO was used to generate these measurements. The following options were set to measure the zero-queue latency:

```
iodepth=1
direct=1
```

These options ensured no queueing and direct I/O access (bypassing the OS cache).

#figure(table(
    columns: 3,
    [], [Read Latency (ns)], [Write Latency (ns)],
    [Random Access, 4 KiB Blocks], [62.11], [19.8],
    [Sequential Access, 128 KiB Blocks], [704.89], [106.22],
))

= Block-Size/Pattern Sweep
