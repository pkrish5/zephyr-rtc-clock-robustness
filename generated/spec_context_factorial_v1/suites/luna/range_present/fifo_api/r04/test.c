#include <zephyr/kernel.h>
#include <zephyr/irq_offload.h>
#include <zephyr/ztest.h>

K_FIFO_DEFINE(test_fifo);

struct fifo_item {
    void *fifo_reserved;
    int value;
};

static struct fifo_item item_a;
static struct fifo_item item_b;
static atomic_t isr_ran;

static void fifo_isr(const void *unused)
{
    ARG_UNUSED(unused);

    atomic_set(&isr_ran, 1);
    k_fifo_put(&test_fifo, &item_a);
    k_fifo_put(&test_fifo, &item_b);
}

ZTEST(fifo_irq, test_isr_to_thread_fifo_order)
{
    atomic_set(&isr_ran, 0);

    irq_offload(fifo_isr, NULL);

    zassert_equal(atomic_get(&isr_ran), 1, "irq_offload handler did not run");
    zassert_true(k_is_in_isr() == false, "test should be running in thread context");

    void *first = k_fifo_get(&test_fifo, K_NO_WAIT);
    void *second = k_fifo_get(&test_fifo, K_NO_WAIT);

    zassert_true(first == &item_a, "first FIFO item pointer mismatch");
    zassert_true(second == &item_b, "second FIFO item pointer mismatch");
    zassert_is_null(k_fifo_get(&test_fifo, K_NO_WAIT), "FIFO should be empty");
}

ZTEST_SUITE(fifo_irq, NULL, NULL, NULL, NULL, NULL);
