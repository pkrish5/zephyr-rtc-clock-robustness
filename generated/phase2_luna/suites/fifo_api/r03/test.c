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

static void fifo_isr(const void *arg)
{
    ARG_UNUSED(arg);
    isr_ran = true;
    k_fifo_put(&test_fifo, &item_a);
    k_fifo_put(&test_fifo, &item_b);
}

ZTEST(fifo_isr_to_thread, test_fifo_transfer_from_isr)
{
    item_a.value = 1;
    item_b.value = 2;
    isr_ran = false;

    irq_offload(fifo_isr, NULL);

    zassert_true(isr_ran, "ISR handler did not run");
    zassert_true(k_fifo_get(&test_fifo, K_NO_WAIT) == &item_a,
                 "first FIFO item was not item_a");
    zassert_true(k_fifo_get(&test_fifo, K_NO_WAIT) == &item_b,
                 "second FIFO item was not item_b");
    zassert_is_null(k_fifo_get(&test_fifo, K_NO_WAIT),
                    "FIFO should be empty after both gets");
}

ZTEST_SUITE(fifo_isr_to_thread, NULL, NULL, NULL, NULL, NULL);
