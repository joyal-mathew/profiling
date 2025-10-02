set term svg
set output "docs/plots/rw_sweep.svg"

set xlabel "Read Ratio"
set grid

set yrange [0:100]
set y2range [0:400]
set ytics 25 nomirror tc lt 1
set ylabel "Latency (ns)"
set y2tics 100 nomirror tc lt 2
set y2label "Bandwidth (MB/s)"

plot "data/rw_ratio_sweep.dat" using 1:(($2+$4)/2) with linespoints axes x1y2 title "bandwidth", \
     "" using 1:(($3+$5)/2) with linespoints title "latency"
