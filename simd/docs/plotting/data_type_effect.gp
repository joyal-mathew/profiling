set term svg
set output "docs/plots/data_type_effect.svg"

set ylabel "Performance (GFLOP/s)"
set grid

set style data histograms
set style histogram clustered gap 2
set style histogram errorbars gap 2 lw 2
set style fill solid 1.0 border -1

plot "data/data_type_effect.dat" using 2:3:4:xtic(1) title "float32", \
     '' using 5:6:7:xtic(1) title "float64", \
