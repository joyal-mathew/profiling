set term svg
set output "docs/plots/zero_queue_baselines.svg"

set ylabel "Latency (ns)"
set xlabel "Size (KiB)"
set grid

# set style data histograms
# set style fill solid 1.0 border -1

set key off

plot "data/zero_queue_baselines.dat" using 1:2 with linespoints
