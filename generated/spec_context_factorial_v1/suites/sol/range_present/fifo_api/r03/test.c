#include <zephyr/kernel.h>
#include <zephyr/irq_offload.h>
#include <zephyr/ztest.h>

struct fifo_item {
    void *fifo_reserved;
    int value;
};

K_FIFO_DEFINE(test_fifo);

static struct fifo_item items[2] = {
    { .value = 1 },
    { .value = 2 },
};
static volatile bool ran_in_isr;

static void enqueue_from_isr(const void *unused)
{
    ARG_UNUSED(unused);

    ran_in_isr = k_is_in_isr();
    k_fifo_put(&test_fifo, &items[0]);
    k_fifo_put(&test_fifo, &items[1]);
}

ZTEST(fifo_irq_transfer, test_isr_to_thread_order)
{
    void *first;
    void *second;

    k_fifo_init(&test_fifo);
    ran_in_isr = false;

    irq_offload(enqueue_from_isr, NULL);

    first = k_fifo_get(&test_fifo, K_NO_WAIT);
    second = k_fifo_get(&test_fifo, K_NO_WAIT);

    zassert_true(ran_in_isr, "enqueue callback did not run in ISR context");
    zassert_true(first == &items[0], "first FIFO item is out of order");
    zassert_true(second == &items[1], "second FIFO item is out of order");
    zassert_is_null(k_fifo_get(&test_fifo, K_NO_WAIT), "FIFO is not empty");
}

ZTEST_SUITE(fifo_irq_transfer, NULL, NULL, NULL, NULL, NULL);
