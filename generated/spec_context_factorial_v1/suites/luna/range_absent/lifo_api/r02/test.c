#include <zephyr/ztest.h>
#include <zephyr/kernel.h>
#include <zephyr/irq_offload.h>

struct lifo_item {
	void *link;
	int value;
};

K_LIFO_DEFINE(test_lifo);

static struct lifo_item item1;
static struct lifo_item item2;
static volatile bool isr_ran;

static void lifo_isr(void *unused)
{
	ARG_UNUSED(unused);
	isr_ran = true;
	k_lifo_put(&test_lifo, &item1);
	k_lifo_put(&test_lifo, &item2);
}

ZTEST(lifo_isr_to_thread, test_isr_put_order_and_empty)
{
	isr_ran = false;
	irq_offload(lifo_isr, NULL);

	zassert_true(isr_ran, "LIFO ISR handler did not run");
	zassert_equal(k_lifo_get(&test_lifo, K_NO_WAIT), &item2,
		      "First get should return most recently inserted item");
	zassert_equal(k_lifo_get(&test_lifo, K_NO_WAIT), &item1,
		      "Second get should return first inserted item");
	zassert_is_null(k_lifo_get(&test_lifo, K_NO_WAIT),
			"LIFO should be empty after retrieving both items");
}

ZTEST_SUITE(lifo_isr_to_thread, NULL, NULL, NULL, NULL, NULL);
