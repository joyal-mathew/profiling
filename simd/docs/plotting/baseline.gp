set term svg
set output "docs/plots/baseline.svg"

set ylabel "Speedup (T_{scalar} / T_{vectorized})"
set xlabel "Size (KiB)"

set grid
set logscale x 2

plot "data/fma_speedup.dat" with errorlines title "fma", \
     "data/conv1d_speedup.dat" with errorlines title "conv1d", \
