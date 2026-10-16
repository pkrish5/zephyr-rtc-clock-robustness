#include <zephyr/kernel.h>
#include <zephyr/irq_offload.h>
#include <zephyr/ztest.h>

struct fifo_item {
    void *fifo_reserved;
    uint32_t value;
};

K_FIFO_DEFINE(test_fifo);

static struct fifo_item item_a;
static struct fifo_item item_b;
static volatile bool isr_ran;

static void fifo_isr(void *unused)
{
    ARG_UNUSED(unused);
    isr_ran = true;
    k_fifo_put(&test_fifo, &item_a);
    k_fifo_put(&test_fifo, &item_b);
}

ZTEST(fifo_isr_to_thread, test_fifo_order_and_empty)
{
    item_a.value = 1U;
    item_b.value = 2U;
    isr_ran = false;

    irq_offload(fifo_isr, NULL);

    zassert_true(isr_ran, "FIFO ISR handler did not run");
    zassert_equal(k_fifo_get(&test_fifo, K_NO_WAIT), &item_a,
                  "First FIFO item was not item_a");
    zassert_equal(k_fifo_get(&test_fifo, K_NO_WAIT), &item_b,
                  "Second FIFO item was not item_b");
    zassert_is_null(k_fifo_get(&test_fifo, K_NO_WAIT),
                    "FIFO should be empty after retrieving both items");
}

ZTEST_SUITE(fifo_isr_to_thread, NULL, NULL, NULL, NULL, NULL);
