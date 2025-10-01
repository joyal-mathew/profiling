set term svg
set output "docs/plots/intensity_sweep.svg"

set ylabel "Bandwidth (MB/s)"
set xlabel "Latency (ns)"
set grid

set key off

plot "data/intensity_sweep.dat" with points
