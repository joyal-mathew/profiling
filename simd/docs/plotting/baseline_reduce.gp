set term svg
set output "docs/plots/baseline_reduce.svg"

set ylabel "Speedup (T_{scalar} / T_{vectorized})"
set xlabel "Size (KiB)"

set grid
set logscale x 2

plot "data/dot_speedup.dat" with errorlines title "dot"
