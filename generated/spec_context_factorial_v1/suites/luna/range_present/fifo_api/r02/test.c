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
static volatile bool isr_ran;

static void fifo_put_from_isr(const void *parameter)
{
	ARG_UNUSED(parameter);

	k_fifo_put(&test_fifo, &item_a);
	k_fifo_put(&test_fifo, &item_b);
	isr_ran = true;
}

ZTEST(fifo_isr_transfer, test_fifo_items_from_isr)
{
	isr_ran = false;

	irq_offload(fifo_put_from_isr, NULL);

	zassert_true(isr_ran, "FIFO producer ISR did not run");
	zassert_true(k_fifo_get(&test_fifo, K_NO_WAIT) == &item_a,
		     "First FIFO item was not the first item inserted by the ISR");
	zassert_true(k_fifo_get(&test_fifo, K_NO_WAIT) == &item_b,
		     "Second FIFO item was not the second item inserted by the ISR");
	zassert_is_null(k_fifo_get(&test_fifo, K_NO_WAIT),
			"FIFO should be empty after retrieving both items");
}

ZTEST_SUITE(fifo_isr_transfer, NULL, NULL, NULL, NULL, NULL);
