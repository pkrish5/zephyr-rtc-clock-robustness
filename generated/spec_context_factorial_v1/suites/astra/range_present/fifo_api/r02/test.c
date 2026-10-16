#include <zephyr/kernel.h>
#include <zephyr/irq_offload.h>
#include <zephyr/ztest.h>
#include <stdbool.h>

struct fifo_item {
	void *fifo_reserved;
	int value;
};

static struct k_fifo fifo;
static struct fifo_item first = { .value = 1 };
static struct fifo_item second = { .value = 2 };
static bool ran_in_isr;

static void enqueue_from_isr(const void *arg)
{
	ARG_UNUSED(arg);
	ran_in_isr = k_is_in_isr();
	k_fifo_put(&fifo, &first);
	k_fifo_put(&fifo, &second);
}

ZTEST(fifo_isr_transfer, test_isr_to_thread_fifo_order)
{
	k_fifo_init(&fifo);
	ran_in_isr = false;

	irq_offload(enqueue_from_isr, NULL);

	zassert_true(ran_in_isr, "Producer did not execute in ISR context");
	zassert_false(k_is_in_isr(), "Consumer must execute in thread context");

	void *received_first = k_fifo_get(&fifo, K_NO_WAIT);
	void *received_second = k_fifo_get(&fifo, K_NO_WAIT);

	zassert_true(received_first == &first, "First item pointer mismatch");
	zassert_true(received_second == &second, "Second item pointer mismatch");
	zassert_true(k_fifo_is_empty(&fifo), "FIFO is not empty after both gets");
	zassert_is_null(k_fifo_get(&fifo, K_NO_WAIT), "Unexpected extra item");
}

ZTEST_SUITE(fifo_isr_transfer, NULL, NULL, NULL, NULL, NULL);
