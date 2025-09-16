#!/usr/bin/env sh

set -xe

gcc "$@" -Ofast -march=native -o docs/disassembly/vectorized.s -S src/main.c
gcc "$@" -Ofast -march=native -o build/vectorized src/main.c

gcc "$@" -Ofast -fno-tree-vectorize -o docs/disassembly/scalar.s -S src/main.c
gcc "$@" -Ofast -fno-tree-vectorize -o build/scalar src/main.c
