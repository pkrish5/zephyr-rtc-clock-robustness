#include <zephyr/kernel.h>
#include <zephyr/irq_offload.h>
#include <zephyr/ztest.h>

struct fifo_item {
    void *fifo_reserved;
    int value;
};

K_FIFO_DEFINE(test_fifo);

static struct fifo_item item_one;
static struct fifo_item item_two;
static volatile bool isr_ran;

static void fifo_isr(void *unused)
{
    ARG_UNUSED(unused);
    isr_ran = true;
    k_fifo_put(&test_fifo, &item_one);
    k_fifo_put(&test_fifo, &item_two);
}

ZTEST(fifo_isr_to_thread, test_fifo_transfer_from_isr)
{
    item_one.value = 1;
    item_two.value = 2;
    isr_ran = false;

    irq_offload(fifo_isr, NULL);

    zassert_true(isr_ran, "irq_offload handler did not run");
    zassert_true(k_fifo_get(&test_fifo, K_NO_WAIT) == &item_one,
                 "first retrieved item was not item_one");
    zassert_true(k_fifo_get(&test_fifo, K_NO_WAIT) == &item_two,
                 "second retrieved item was not item_two");
    zassert_is_null(k_fifo_get(&test_fifo, K_NO_WAIT),
                    "FIFO should be empty after both items are retrieved");
}

ZTEST_SUITE(fifo_isr_to_thread, NULL, NULL, NULL, NULL, NULL);
