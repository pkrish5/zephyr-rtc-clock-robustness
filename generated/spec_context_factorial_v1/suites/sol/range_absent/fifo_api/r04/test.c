#include <stdbool.h>
#include <zephyr/kernel.h>
#include <zephyr/irq_offload.h>
#include <zephyr/ztest.h>

struct fifo_item {
	void *fifo_reserved;
	int value;
};

static struct k_fifo test_fifo;
static struct fifo_item items[2] = {
	{ .value = 1 },
	{ .value = 2 },
};
static volatile bool isr_ran;
static volatile bool ran_in_isr;

static void enqueue_from_isr(const void *arg)
{
	ARG_UNUSED(arg);
	isr_ran = true;
	ran_in_isr = k_is_in_isr();
	k_fifo_put(&test_fifo, &items[0]);
	k_fifo_put(&test_fifo, &items[1]);
}

ZTEST(fifo_irq_offload, test_isr_to_thread_order)
{
	void *first;
	void *second;

	k_fifo_init(&test_fifo);
	isr_ran = false;
	ran_in_isr = false;

	irq_offload(enqueue_from_isr, NULL);

	zassert_true(isr_ran, "offloaded handler did not run");
	zassert_true(ran_in_isr, "handler did not run in ISR context");

	first = k_fifo_get(&test_fifo, K_NO_WAIT);
	second = k_fifo_get(&test_fifo, K_NO_WAIT);
	zassert_true(first == &items[0], "first item is out of order");
	zassert_true(second == &items[1], "second item is out of order");
	zassert_is_null(k_fifo_get(&test_fifo, K_NO_WAIT), "FIFO is not empty");
}

ZTEST_SUITE(fifo_irq_offload, NULL, NULL, NULL, NULL, NULL);
