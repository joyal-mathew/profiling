set term svg
set output "docs/plots/cache_miss_effect.svg"

set ylabel "Time (ns)"
set xlabel "Cache Miss Count (#)"

set grid
set key off

plot "data/cache_miss_effect.dat" with errorlines
