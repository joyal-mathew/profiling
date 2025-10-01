#include <assert.h>
#include <stdint.h>
#include <stdlib.h>
#include <time.h>

#define NS_PER_SEC 1000000000ULL

#ifndef number
#define number float
#endif

typedef struct {
    struct timespec start;
} Timer;

static inline void timer_start(Timer *t) {
    clock_gettime(CLOCK_MONOTONIC_RAW, &t->start);
}

static inline uint64_t timer_elapsed(Timer *t) {
    struct timespec end;
    clock_gettime(CLOCK_MONOTONIC_RAW, &end);
    uint64_t dsec = end.tv_sec - t->start.tv_sec;
    uint64_t dnsec = end.tv_nsec - t->start.tv_nsec;
    return dsec * NS_PER_SEC + dnsec;
}

static inline void blackbox(void *p) {
    asm volatile("" : : "g"(p) : "memory");
}

void populate_random(size_t n, number *x) {
    for (size_t i = 0; i < n; ++i) {
        number u = (number)rand() / (number)RAND_MAX;
        x[i] = 2 * u - 1;
    }
}

size_t parse_human_writable(char *string) {
    char *end_ptr;
    size_t n = strtoull(string, &end_ptr, 10);
    assert(end_ptr != string);

    switch (*end_ptr | ' ') {
    case 'k':
        n *= 1024;
        break;
    case 'm':
        n *= 1024 * 1024;
        break;
    }

    return n;
}
