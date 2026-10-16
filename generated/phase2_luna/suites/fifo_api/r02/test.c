#include <zephyr/ztest.h>
#include <zephyr/kernel.h>
#include <zephyr/irq_offload.h>

struct fifo_item {
    void *fifo_reserved;
    int value;
};

K_FIFO_DEFINE(test_fifo);

static struct fifo_item item_one = { .value = 1 };
static struct fifo_item item_two = { .value = 2 };
static volatile bool isr_ran;

static void fifo_isr(const void *arg)
{
    ARG_UNUSED(arg);
    isr_ran = true;
    k_fifo_put(&test_fifo, &item_one);
    k_fifo_put(&test_fifo, &item_two);
}

ZTEST(fifo_irq, test_isr_to_thread_fifo_order)
{
    isr_ran = false;
    irq_offload(fifo_isr, NULL);

    zassert_true(isr_ran, "IRQ offload handler did not run");
    zassert_equal(k_fifo_get(&test_fifo, K_NO_WAIT), &item_one,
                  "First FIFO item was not the first item inserted");
    zassert_equal(k_fifo_get(&test_fifo, K_NO_WAIT), &item_two,
                  "Second FIFO item was not the second item inserted");
    zassert_is_null(k_fifo_get(&test_fifo, K_NO_WAIT),
                    "FIFO should be empty after retrieving both items");
}

ZTEST_SUITE(fifo_irq, NULL, NULL, NULL, NULL, NULL);
