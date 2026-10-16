#include <zephyr/kernel.h>
#include <zephyr/irq_offload.h>
#include <zephyr/ztest.h>
#include <stdbool.h>

struct fifo_item {
	void *reserved;
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

ZTEST(fifo_isr, test_transfer_to_thread)
{
	k_fifo_init(&fifo);
	ran_in_isr = false;

	irq_offload(enqueue_from_isr, NULL);

	zassert_true(ran_in_isr, "Producer did not run in interrupt context");
	zassert_false(k_is_in_isr(), "Consumer must run in thread context");
	zassert_equal_ptr(k_fifo_get(&fifo, K_NO_WAIT), &first,
			  "First item was not received first");
	zassert_equal_ptr(k_fifo_get(&fifo, K_NO_WAIT), &second,
			  "Second item was not received second");
	zassert_is_null(k_fifo_get(&fifo, K_NO_WAIT),
			"FIFO must be empty after both items are retrieved");
}

ZTEST_SUITE(fifo_isr, NULL, NULL, NULL, NULL, NULL);
