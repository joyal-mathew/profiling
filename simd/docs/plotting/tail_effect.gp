set term svg
set output "docs/plots/tail_effect.svg"

set ylabel "Performance (GFLOP/s)"
set grid

set style data histograms
set style histogram clustered gap 2
set style histogram errorbars gap 2 lw 2
set style fill solid 1.0 border -1

plot "data/tail_effect.dat" using 2:3:4:xtic(1) title "tail-less", \
     '' using 5:6:7:xtic(1) title "tailed" \
