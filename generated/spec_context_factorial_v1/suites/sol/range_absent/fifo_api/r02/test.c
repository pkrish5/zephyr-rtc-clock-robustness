#include <stdbool.h>
#include <zephyr/kernel.h>
#include <zephyr/irq_offload.h>
#include <zephyr/ztest.h>

struct fifo_item {
	void *fifo_reserved;
};

K_FIFO_DEFINE(test_fifo);

static struct fifo_item first_item;
static struct fifo_item second_item;
static volatile bool ran_in_isr;

static void enqueue_from_isr(const void *unused)
{
	(void)unused;
	ran_in_isr = k_is_in_isr();
	k_fifo_put(&test_fifo, &first_item);
	k_fifo_put(&test_fifo, &second_item);
}

ZTEST(fifo_isr, test_isr_to_thread_transfer)
{
	void *first;
	void *second;

	ran_in_isr = false;
	irq_offload(enqueue_from_isr, NULL);

	first = k_fifo_get(&test_fifo, K_NO_WAIT);
	second = k_fifo_get(&test_fifo, K_NO_WAIT);

	zassert_true(ran_in_isr, "enqueue did not run in ISR context");
	zassert_true(first == &first_item, "first item out of order");
	zassert_true(second == &second_item, "second item out of order");
	zassert_is_null(k_fifo_get(&test_fifo, K_NO_WAIT), "FIFO is not empty");
}

ZTEST_SUITE(fifo_isr, NULL, NULL, NULL, NULL, NULL);
