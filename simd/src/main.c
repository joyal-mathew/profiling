#include <assert.h>
#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

#include "../../common.c"

#define VECTOR_WIDTH 32 // AVX2 (256 bit)
#define L3_SIZE (16 * 1024 * 1024)

#define STRIDE 4

#ifdef UNALIGNED

#define ALIGN_PTR(p) p
const size_t PTR_OFFSET = VECTOR_WIDTH / 2;

#else

#define ALIGN_PTR(p) __builtin_assume_aligned(p, VECTOR_WIDTH)
const size_t PTR_OFFSET = 0;

#endif

typedef enum {
    am_Undef,
    am_Unit,
    am_Strided,
    am_Gather,
} AccessMode;

void fma_kernel(size_t n, number a, number * restrict in_x,
                number * restrict in_y) {
    number * restrict x = ALIGN_PTR(in_x);
    number * restrict y = ALIGN_PTR(in_y);

    for (size_t i = 0; i < n; ++i)
        y[i] = a * x[i] + y[i];
}

void fma_strided(size_t n, number a, number * restrict in_x,
                number * restrict in_y) {
    number * restrict x = ALIGN_PTR(in_x);
    number * restrict y = ALIGN_PTR(in_y);

    size_t l = 0;
    for (int j = 0; j < STRIDE; ++j) {
        for (size_t i = 0; i < n / STRIDE; ++i, ++l) {
            size_t k = i * STRIDE + j;
            y[l] = a * x[k] + y[l];
        }
    }
}

void fma_gather(size_t n, number a, number * restrict in_x,
                number * restrict in_y, size_t * restrict idx) {
    number * restrict x = ALIGN_PTR(in_x);
    number * restrict y = ALIGN_PTR(in_y);

    for (size_t i = 0; i < n; ++i) {
        size_t j = idx[i];
        y[i] = a * x[j] + y[i];
    }
}

number dot_kernel(size_t n, number *restrict in_x, number *restrict in_y) {
    number * restrict x = ALIGN_PTR(in_x);
    number * restrict y = ALIGN_PTR(in_y);

    number total = 0;
    for (size_t i = 0; i < n; ++i)
        total += x[i] * y[i];

    return total;
}

number dot_strided(size_t n, number *restrict in_x, number *restrict in_y) {
    number * restrict x = ALIGN_PTR(in_x);
    number * restrict y = ALIGN_PTR(in_y);

    number total = 0;
    size_t l = 0;
    for (int j = 0; j < STRIDE; ++j) {
        for (size_t i = 0; i < n / STRIDE; ++i, ++l) {
            size_t k = i * STRIDE + j;
            total += x[k] * y[l];
        }
    }

    return total;
}

number dot_gather(size_t n, number *restrict in_x, number *restrict in_y,
                  size_t *restrict idx) {
    number *restrict x = ALIGN_PTR(in_x);
    number * restrict y = ALIGN_PTR(in_y);

    number total = 0;
    for (size_t i = 0; i < n; ++i) {
        size_t j = idx[i];
        total += x[j] * y[i];
    }

    return total;
}

void conv1d_kernel(size_t n, number a, number b, number c,
                   number * restrict in_x, number * restrict in_y) {
    number * restrict x = ALIGN_PTR(in_x);
    number * restrict y = ALIGN_PTR(in_y);

    for (size_t i = 0; i < n; ++i) {
        if (i == 0)
            y[i] = b * x[i] + c * x[i + 1];
        else if (i == n - 1)
            y[i] = a * x[i - 1] + b * x[i];
        else
            y[i] = a * x[i - 1] + b * x[i] + c * x[i + 1];
    }
}

void conv1d_strided(size_t n, number a, number b, number c,
                    number *restrict in_x, number *restrict in_y) {
    number * restrict x = ALIGN_PTR(in_x);
    number * restrict y = ALIGN_PTR(in_y);

    size_t l = 0;
    for (int j = 0; j < STRIDE; ++j) {
        for (size_t i = 0; i < n / STRIDE; ++i, ++l) {
            size_t k = i * STRIDE + j;


        if (k == 0)
            y[l] = b * x[k] + c * x[k + 1];
        else if (k == n - 1)
            y[l] = a * x[k - 1] + b * x[k];
        else
            y[l] = a * x[k - 1] + b * x[k] + c * x[k + 1];
        }
    }
}

void conv1d_gather(size_t n, number a, number b, number c,
                   number *restrict in_x, number *restrict in_y, size_t *idx) {
    number *restrict x = ALIGN_PTR(in_x);
    number *restrict y = ALIGN_PTR(in_y);

    number total = 0;
    for (size_t i = 0; i < n; ++i) {
        size_t j = idx[i];

        if (j == 0)
        y[i] = b * x[j] + c * x[j + 1];
        else if (j == n - 1)
        y[i] = a * x[j - 1] + b * x[j];
        else
        y[i] = a * x[j - 1] + b * x[j] + c * x[j + 1];
    }
}


void populate_idx(size_t n, size_t *idx) {
    assert(n <= RAND_MAX);

    for (size_t i = 0; i < n; ++i)
        idx[i] = i;

    for (size_t i = n - 1; i >= 1; --i) {
        size_t j = rand() % i;
        size_t t = idx[i];
        idx[i] = idx[j];
        idx[j] = t;
    }
}

void warmup(size_t n, number *data) {
    for (size_t i = 0; i < n; ++i) {
        number x = data[i];
        blackbox(&x);
    }
}

int popcnt(unsigned x) {
    int count = 0;
    while (x) {
        x &= x - 1;
        count++;
    }
    return count;
}

void *align_ptr(void *ptr, unsigned alignment) {
    assert(popcnt(alignment) == 1);

    uintptr_t addr = (uintptr_t)ptr;
    uintptr_t inv_mask = alignment - 1;
    uintptr_t offset = (addr & inv_mask) ? alignment : 0;
    return (void *)((addr & ~inv_mask) + offset);
}

int main(int argc, char **argv) {
    assert(3 <= argc);

    size_t n = parse_human_writable(argv[1]);
    char *kernel = argv[2];

    bool cold = false;
    AccessMode mode = am_Undef;
    size_t rounds = 1;
    for (int i = 3; i < argc; ++i) {
        if (strcmp(argv[i], "-c") == 0) {
            cold = true;
        }
        else if (strcmp(argv[i], "-u") == 0) {
            assert(mode == am_Undef);
            mode = am_Unit;
        }
        else if (strcmp(argv[i], "-s") == 0) {
            assert(mode == am_Undef);
            mode = am_Strided;
        }
        else if (strcmp(argv[i], "-g") == 0) {
            assert(mode == am_Undef);
            mode = am_Gather;
        }
        else if (strcmp(argv[i], "-r") == 0) {
            assert(++i < argc);
            rounds = parse_human_writable(argv[i]);
        }
    }

    if (mode == am_Strided)
        assert(n % STRIDE == 0);
    else if (mode == am_Undef)
        mode = am_Unit;

    srand(0);

    assert(L3_SIZE % sizeof (number) == 0);
    size_t cold_size = L3_SIZE / sizeof (number);
    number *cold_data = malloc(L3_SIZE);

    size_t *idx = malloc(n * sizeof (size_t));
    populate_idx(n, idx);

    number params[3];

    size_t alloc_size = 2 * (n * sizeof (number) + PTR_OFFSET) + VECTOR_WIDTH;
    number *x = aligned_alloc(VECTOR_WIDTH, alloc_size) + PTR_OFFSET;
    number *y = align_ptr(x + n, VECTOR_WIDTH) + PTR_OFFSET;

    assert((uintptr_t) x % VECTOR_WIDTH == PTR_OFFSET);
    assert((uintptr_t) y % VECTOR_WIDTH == PTR_OFFSET);

    populate_random(cold_size, cold_data);
    populate_random(3, params);
    populate_random(n, x);

    Timer t;
    uint64_t elapsed;
    number s;

    number *cache_preload;
    size_t cache_preload_len;

    if (cold) {
        cache_preload = cold_data;
        cache_preload_len = cold_size;
    }
    else {
        cache_preload = x;
        cache_preload_len = 2 * n;
    }

#define BENCHMARK(code)                             \
    do {                                            \
        warmup(cache_preload_len, cache_preload);   \
        timer_start(&t);                            \
        for (size_t r = 0; r < rounds; ++r)         \
            code;                                   \
        elapsed = timer_elapsed(&t);                \
    } while (false)

    if (strcmp(kernel, "fma") == 0) {
        switch (mode) {
        case am_Undef: assert(false); break;
        case am_Unit: BENCHMARK(fma_kernel(n, params[0], x, y)); break;
        case am_Strided: BENCHMARK(fma_strided(n, params[0], x, y)); break;
        case am_Gather: BENCHMARK(fma_gather(n, params[0], x, y, idx)); break;
        }
    }
    else if (strcmp(kernel, "dot") == 0) {
        switch (mode) {
        case am_Undef: assert(false); break;
        case am_Unit: BENCHMARK(s = dot_kernel(n, x, y)); break;
        case am_Strided: BENCHMARK(s = dot_strided(n, x, y)); break;
        case am_Gather: BENCHMARK(s = dot_gather(n, x, y, idx)); break;
        }
    }
    else if (strcmp(kernel, "conv1d") == 0) {
        switch (mode) {
        case am_Undef: assert(false); break;
        case am_Unit:
            BENCHMARK(conv1d_kernel(n, params[0], params[1], params[2], x, y));
            break;
        case am_Strided:
            BENCHMARK(conv1d_strided(n, params[0], params[1], params[2], x, y));
            break;
        case am_Gather:
            BENCHMARK(
                conv1d_gather(n, params[0], params[1], params[2], x, y, idx));
            break;
        }

    }
    else {
        assert(false);
    }

    blackbox(&s);
    blackbox(y);

    printf("%ld\n", elapsed);
}
