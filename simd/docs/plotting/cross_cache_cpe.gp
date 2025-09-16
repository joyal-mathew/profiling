set term svg
set output "docs/plots/cross_cache_cpe.svg"

set ylabel "Throughput Cost (CPE)"
set xlabel "Size (KiB)"

set grid
set logscale x 2

plot "data/dot_cross_cache_cpe.dat" with errorlines title "dot"
