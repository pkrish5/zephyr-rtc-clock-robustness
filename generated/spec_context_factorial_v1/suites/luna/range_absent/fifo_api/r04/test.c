#include <zephyr/kernel.h>
#include <zephyr/irq_offload.h>
#include <zephyr/ztest.h>

struct fifo_item {
	void *reserved;
	int value;
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

ZTEST(irq_fifo, test_isr_to_thread_fifo_order)
{
	item_a.value = 1;
	item_b.value = 2;
	isr_ran = false;
	irq_offload(fifo_isr, NULL);

	zassert_true(isr_ran, "irq_offload handler did not run");
	zassert_equal(k_fifo_get(&test_fifo, K_NO_WAIT), &item_a,
		      "first FIFO item should be item_a");
	zassert_equal(k_fifo_get(&test_fifo, K_NO_WAIT), &item_b,
		      "second FIFO item should be item_b");
	zassert_is_null(k_fifo_get(&test_fifo, K_NO_WAIT),
			"FIFO should be empty after both gets");
}

ZTEST_SUITE(irq_fifo, NULL, NULL, NULL, NULL, NULL);
