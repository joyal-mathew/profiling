set term svg
set output "docs/plots/cross_cache_cpe.svg"

set ylabel "Throughput Cost (CPE)"
set xlabel "Size (KiB)"

set label "L1" at graph 0.1, 0.8 font "Arial,28" textcolor 'red'
set label "L2" at graph 0.4, 0.8 font "Arial,28" textcolor 'red'
set label "L3" at graph 0.75, 0.8 font "Arial,28" textcolor 'red'

set arrow from 192, graph 0 to 192, graph 1 nohead lc rgb 'red'
set arrow from 3072, graph 0 to 3072, graph 1 nohead lc rgb 'red'
set arrow from 16384, graph 0 to 16384, graph 1 nohead lc rgb 'red'

set grid
set logscale x 2

plot "data/dot_cross_cache_cpe.dat" with errorlines title "dot"
