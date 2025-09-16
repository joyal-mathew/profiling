#include <assert.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

#define NS_PER_SEC 1000000000ULL
#define VECTOR_WIDTH 32 // AVX2 (256 bit)

#ifndef number
#define number float
#endif

#define ALIGN_PTR(p) __builtin_assume_aligned((p), VECTOR_WIDTH)
/* #define ALIGN_PTR(p) p */

typedef struct {
    struct timespec start;
} Timer;

void timer_start(Timer *t) {
    clock_gettime(CLOCK_MONOTONIC_RAW, &t->start);
}

uint64_t timer_elapsed(Timer *t) {
    struct timespec end;
    clock_gettime(CLOCK_MONOTONIC_RAW, &end);
    uint64_t dsec = end.tv_sec - t->start.tv_sec;
    uint64_t dnsec = end.tv_nsec - t->start.tv_nsec;
    return dsec * NS_PER_SEC + dnsec;
}

static inline void blackbox(void *p) {
    asm volatile("" : : "g"(p) : "memory");
}

void fma_kernel(size_t n, number a, number * restrict in_x, number * restrict in_y) {
    number * restrict x = ALIGN_PTR(in_x);
    number * restrict y = ALIGN_PTR(in_y);

    for (size_t i = 0; i < n; ++i)
        y[i] = a * x[i] + y[i];
}

number dot_kernel(size_t n, number * restrict in_x, number * restrict in_y) {
    number * restrict x = ALIGN_PTR(in_x);
    number * restrict y = ALIGN_PTR(in_y);

    number total = 0;
    for (size_t i = 0; i < n; ++i)
        total += x[i] * y[i];

    return total;
}

void conv1d_kernel(size_t n, number a, number b, number c, number * restrict in_x, number * restrict in_y) {
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

void populate_random(size_t n, number *x) {
    for (size_t i = 0; i < n; ++i) {
        number u = (number) rand() / (number) RAND_MAX;
        x[i] = 2 * u - 1;
    }
}

void warmup(size_t n, number *data) {
    for (size_t i = 0; i < n; ++i) {
        number x = data[i];
        blackbox(&x);
    }
}

int main(int argc, char **argv) {
    assert(argc == 3);

    char *end_ptr;
    size_t n = strtoull(argv[1], &end_ptr, 10);
    assert(end_ptr != argv[1]);

    switch (*end_ptr | ' ') {
        case 'k': n *= 1024; break;
        case 'm': n *= 1024 * 1024; break;
    }

    char *kernel = argv[2];

    srand(0);

    number params[3];
    number *x = aligned_alloc(VECTOR_WIDTH, 2 * n * sizeof (number));
    number *y = x + n;

    assert((uintptr_t) x % VECTOR_WIDTH == 0);
    assert((uintptr_t) y % VECTOR_WIDTH == 0);

    populate_random(3, params);
    populate_random(n, x);

    Timer t;
    uint64_t elapsed;
    number s;

    for (size_t i = 0; i < n; ++i) {
        blackbox(x + i);
        blackbox(y + i);
    }

    if (strcmp(kernel, "fma") == 0) {
        warmup(2 * n, x);
        timer_start(&t);
        fma_kernel(n, params[0], x, y);
        elapsed = timer_elapsed(&t);
    }
    else if (strcmp(kernel, "dot") == 0) {
        warmup(2 * n, x);
        timer_start(&t);
        s = dot_kernel(n, x, y);
        elapsed = timer_elapsed(&t);
    }
    else if (strcmp(kernel, "conv1d") == 0) {
        warmup(2 * n, x);
        timer_start(&t);
        conv1d_kernel(n, params[0], params[1], params[2], x, y);
        elapsed = timer_elapsed(&t);
    }
    else {
        assert(false);
    }

    blackbox(&s);
    blackbox(y);

    printf("%ld\n", elapsed);
}
