set term svg
set output "docs/plots/qd_sweep.svg"

set xlabel "Queue Depth"
set grid

set xtics 10

set yrange [0:1000]
set y2range [0:800]
set ytics 100 nomirror tc lt 1
set y2label "Latency (ns)"
set y2tics 100 nomirror tc lt 2
set ylabel "Bandwidth (MB/s)"

plot "data/qd_sweep.dat" every 10::0::100 using 1:2 with linespoints title "bandwidth", \
     "" every 10::0::100 using 1:3 with linespoints axes x1y2 title "latency"
