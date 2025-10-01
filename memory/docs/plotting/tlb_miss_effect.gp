set term svg
set output "docs/plots/tlb_miss_effect.svg"

set ylabel "Time (ns)"
set xlabel "TLB Miss Count (#)"

set grid
set key off

plot "data/tlb_miss_effect.dat" with errorlines
