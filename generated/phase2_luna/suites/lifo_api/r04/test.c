#include <zephyr/ztest.h>
#include <zephyr/kernel.h>
#include <zephyr/irq_offload.h>

struct lifo_item {
	void *link;
	int value;
};

K_LIFO_DEFINE(test_lifo);
static struct lifo_item item_a;
static struct lifo_item item_b;
static volatile bool isr_ran;

static void lifo_offload_handler(const void *arg)
{
	ARG_UNUSED(arg);
	isr_ran = true;
	k_lifo_put(&test_lifo, &item_a);
	k_lifo_put(&test_lifo, &item_b);
}

ZTEST(lifo_isr_transfer, test_isr_lifo_order_and_empty)
{
	isr_ran = false;
	irq_offload(lifo_offload_handler, NULL);

	zassert_true(isr_ran, "irq_offload handler did not run");
	zassert_equal(k_lifo_get(&test_lifo, K_NO_WAIT), &item_b,
		      "first get should return the last item inserted by ISR");
	zassert_equal(k_lifo_get(&test_lifo, K_NO_WAIT), &item_a,
		      "second get should return the first item inserted by ISR");
	zassert_is_null(k_lifo_get(&test_lifo, K_NO_WAIT),
			"LIFO should be empty after retrieving both items");
}

ZTEST_SUITE(lifo_isr_transfer, NULL, NULL, NULL, NULL, NULL);
