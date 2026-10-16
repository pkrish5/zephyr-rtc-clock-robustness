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
static bool isr_ran;
static bool isr_context_seen;

static void put_items_from_isr(const void *unused)
{
	ARG_UNUSED(unused);
	isr_ran = true;
	isr_context_seen = k_is_in_isr();
	k_fifo_put(&test_fifo, &item_a);
	k_fifo_put(&test_fifo, &item_b);
}

ZTEST(k_fifo_irq_offload, test_isr_to_thread_fifo_order)
{
	item_a.value = 1;
	item_b.value = 2;
	isr_ran = false;
	isr_context_seen = false;

	irq_offload(put_items_from_isr, NULL);

	zassert_true(isr_ran, "ISR callback did not run");
	zassert_true(isr_context_seen, "callback did not run in interrupt context");
	zassert_equal(k_fifo_get(&test_fifo, K_NO_WAIT), &item_a,
		      "first FIFO item was not item_a");
	zassert_equal(k_fifo_get(&test_fifo, K_NO_WAIT), &item_b,
		      "second FIFO item was not item_b");
	zassert_is_null(k_fifo_get(&test_fifo, K_NO_WAIT),
			"FIFO should be empty after both gets");
}

ZTEST_SUITE(k_fifo_irq_offload, NULL, NULL, NULL, NULL, NULL);
