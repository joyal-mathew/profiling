set term svg
set output "docs/plots/vector_gflops_reduce.svg"

set ylabel "Performance (GFLOP/s)"
set xlabel "Size (KiB)"

set grid
set logscale x 2

plot "data/dot_vector_gflops.dat" with errorlines title "dot"
