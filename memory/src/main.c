#include <stdlib.h>
#include <stdio.h>
#include <stdbool.h>
#include <assert.h>
#include <string.h>

#include "../../common.c"

#define PAGE_SIZE 4096

void elementwise_multiply(const number * restrict x, const number * restrict y,
                          number * restrict z, size_t n, size_t *idx) {
    for (size_t i = 0; i < n; ++i) {
        size_t j = idx[i];
        z[i] += x[j] * y[j];
    }
}

void populate_idx_pages(size_t *idx, size_t n, size_t random_sparsity) {
    assert(n <= RAND_MAX);

    for (size_t i = 0; i < n; ++i) {
        if (random_sparsity != 0 && (i + 1) % random_sparsity == 0)
            idx[i] = rand() % n;
        else
            idx[i] = i;
    }
}

void populate_idx(size_t *idx, size_t n, size_t random_sparsity) {
    for (size_t i = 0; i < n; ++i) {
        if (random_sparsity != 0 && (i + 1) % random_sparsity == 0) {
            size_t delta = rand() % PAGE_SIZE;
            delta -= PAGE_SIZE / 2;
            size_t j = i + delta;
            if (j >= n) {
                if (delta > PAGE_SIZE) j = 0;
                else j = n - 1;
            }
            idx[i] = j;
        }
        else {
            idx[i] = i;
        }
    }
}

int main(int argc, char **argv) {
    assert(argc == 4);

    srand(0);

    size_t n = parse_human_writable(argv[1]);
    size_t random_sparsity = parse_human_writable(argv[2]);
    char *miss_type = argv[3];

    number *x = malloc(3 * n * sizeof (number));
    number *y = x + n;
    number *z = y + n;

    size_t *idx = malloc(n * sizeof (size_t));

    populate_random(n, x);
    populate_random(n, y);
    if (strcmp(miss_type, "cache") == 0)
        populate_idx(idx, n, random_sparsity);
    else if (strcmp(miss_type, "tlb") == 0)
        populate_idx_pages(idx, n, random_sparsity);
    else
        assert(false);

    Timer timer;
    timer_start(&timer);
    elementwise_multiply(x, y, z, n, idx);
    uint64_t elapsed = timer_elapsed(&timer);

    blackbox(z);

    printf("%ld\n", elapsed);
}
