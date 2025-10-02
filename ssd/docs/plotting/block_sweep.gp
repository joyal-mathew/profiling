set term svg
set output "docs/plots/block_sweep.svg"

set xlabel "Size (KiB)"
set grid

set yrange [0:400]
set y2range [0:1400]
set ytics 50 nomirror tc lt 1
set ylabel "Latency (ns)"
set y2tics 200 nomirror tc lt 2
set y2label "Bandwidth (MB/s)"

plot "data/rand_block_sweep.dat" using 1:3 with linespoints title "rand latency", \
     "" using 1:2 with linespoints axes x1y2 title "rand bandwidth", \
     "data/seq_block_sweep.dat" using 1:3 with linespoints title "seq latency", \
     "" using 1:2 with linespoints axes x1y2 title "seq bandwidth"
