set term svg
set output "docs/plots/scalar_gflops.svg"

set ylabel "Performance (GFLOP/s)"
set xlabel "Size (KiB)"

set grid
set logscale x 2

plot "data/fma_scalar_gflops.dat" with errorlines title "fma", \
     "data/conv1d_scalar_gflops.dat" with errorlines title "conv1d", \
     "data/dot_scalar_gflops.dat" with errorlines title "dot"
