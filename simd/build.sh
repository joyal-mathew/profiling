#!/usr/bin/env sh

gcc -Ofast -march=native -o docs/disassembly/vectorized.s -S src/main.c &
gcc -Ofast -march=native -o build/vectorized src/main.c &

gcc -Ofast -fno-tree-vectorize -o docs/disassembly/scalar.s -S src/main.c &
gcc -Ofast -fno-tree-vectorize -o build/scalar src/main.c &

gcc -Ofast -march=native -DUNALIGNED -o docs/disassembly/unaligned.s -S src/main.c &
gcc -Ofast -march=native -DUNALIGNED -o build/unaligned src/main.c &

gcc -Ofast -march=native -Dnumber=double -o docs/disassembly/double.s -S src/main.c &
gcc -Ofast -march=native -Dnumber=double -o build/double src/main.c &

wait
