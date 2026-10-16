#include <zephyr/ztest.h>
#include <zephyr/irq_offload.h>
#include <zephyr/kernel.h>
#include <zephyr/sys/atomic.h>

struct lifo_item {
    void *link; /* k_lifo uses the first word for linkage. */
    int value;
};

K_LIFO_DEFINE(test_lifo);
static struct lifo_item item_a;
static struct lifo_item item_b;
static atomic_t isr_called;

static void lifo_put_from_isr(const void *unused)
{
    ARG_UNUSED(unused);
    atomic_set(&isr_called, 1);
    k_lifo_put(&test_lifo, &item_a);
    k_lifo_put(&test_lifo, &item_b);
}

ZTEST(lifo_isr_to_thread, test_isr_lifo_transfer)
{
    atomic_clear(&isr_called);
    irq_offload(lifo_put_from_isr, NULL);

    zassert_equal(atomic_get(&isr_called), 1, "ISR handler was not invoked");
    zassert_equal(k_lifo_get(&test_lifo, K_NO_WAIT), &item_b,
                  "expected most recently inserted item first");
    zassert_equal(k_lifo_get(&test_lifo, K_NO_WAIT), &item_a,
                  "expected first inserted item second");
    zassert_is_null(k_lifo_get(&test_lifo, K_NO_WAIT), "LIFO should be empty");
}

ZTEST_SUITE(lifo_isr_to_thread, NULL, NULL, NULL, NULL, NULL);
