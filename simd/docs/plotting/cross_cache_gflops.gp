set term svg
set output "docs/plots/cross_cache_gflops.svg"

set ylabel "Performance (GFLOP/s)"
set xlabel "Size (KiB)"

set grid
set logscale x 2

plot "data/dot_cross_cache_gflops.dat" with errorlines title "dot"
