set term svg
set output "docs/plots/rw_ratio_sweep.svg"

set ylabel "Bandwidth (GB/s)"
set xlabel "R/W ratio"
set grid

set yrange [20:32]

set style data histograms
set style fill solid 1.0 border -1

set key off

plot "data/rw_ratio_sweep.dat" using ($2/1000):xtic(1)
