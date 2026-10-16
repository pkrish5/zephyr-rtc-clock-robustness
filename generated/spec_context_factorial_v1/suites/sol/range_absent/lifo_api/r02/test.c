#include <stdbool.h>
#include <zephyr/irq_offload.h>
#include <zephyr/kernel.h>
#include <zephyr/ztest.h>

struct lifo_item {
    void *link; /* Reserved for kernel linkage. */
    int id;
};

K_LIFO_DEFINE(test_lifo);

static struct lifo_item items[2] = {
    { .id = 1 },
    { .id = 2 },
};
static volatile bool isr_seen;

static void put_from_isr(const void *arg)
{
    ARG_UNUSED(arg);
    isr_seen = k_is_in_isr();
    k_lifo_put(&test_lifo, &items[0]);
    k_lifo_put(&test_lifo, &items[1]);
}

ZTEST(lifo_irq_transfer, test_isr_to_thread)
{
    k_lifo_init(&test_lifo);
    isr_seen = false;

    irq_offload(put_from_isr, NULL);

    zassert_true(isr_seen, "callback did not run in ISR context");
    zassert_equal(k_lifo_get(&test_lifo, K_NO_WAIT), &items[1],
                  "last item was not retrieved first");
    zassert_equal(k_lifo_get(&test_lifo, K_NO_WAIT), &items[0],
                  "first item was not retrieved second");
    zassert_is_null(k_lifo_get(&test_lifo, K_NO_WAIT),
                    "LIFO was not empty after two gets");
}

ZTEST_SUITE(lifo_irq_transfer, NULL, NULL, NULL, NULL, NULL);
