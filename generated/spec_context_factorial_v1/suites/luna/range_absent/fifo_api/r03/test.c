#include <zephyr/kernel.h>
#include <zephyr/irq_offload.h>
#include <zephyr/ztest.h>

struct fifo_item {
    void *fifo_reserved;
    int value;
};

K_FIFO_DEFINE(test_fifo);

static struct fifo_item item_a;
static struct fifo_item item_b;
static volatile bool isr_ran;

static void fifo_isr(const void *unused)
{
    ARG_UNUSED(unused);

    isr_ran = true;
    k_fifo_put(&test_fifo, &item_a);
    k_fifo_put(&test_fifo, &item_b);
}

ZTEST(irq_fifo, test_isr_to_thread_fifo_order)
{
    item_a.value = 1;
    item_b.value = 2;
    isr_ran = false;

    irq_offload(fifo_isr, NULL);

    zassert_true(isr_ran, "IRQ-offloaded handler did not run");
    zassert_equal(k_fifo_get(&test_fifo, K_NO_WAIT), &item_a,
                  "First FIFO item was not item_a");
    zassert_equal(k_fifo_get(&test_fifo, K_NO_WAIT), &item_b,
                  "Second FIFO item was not item_b");
    zassert_is_null(k_fifo_get(&test_fifo, K_NO_WAIT),
                    "FIFO should be empty after both items are retrieved");
}

ZTEST_SUITE(irq_fifo, NULL, NULL, NULL, NULL, NULL);
