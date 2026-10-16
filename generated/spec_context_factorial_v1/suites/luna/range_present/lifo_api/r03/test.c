#include <zephyr/kernel.h>
#include <zephyr/irq_offload.h>
#include <zephyr/ztest.h>

struct lifo_item {
	void *kernel_link;
	int value;
};

K_LIFO_DEFINE(test_lifo);
static struct lifo_item item_a;
static struct lifo_item item_b;
static volatile bool isr_ran;

static void lifo_isr(const void *arg)
{
	ARG_UNUSED(arg);
	isr_ran = true;
	k_lifo_put(&test_lifo, &item_a);
	k_lifo_put(&test_lifo, &item_b);
}

ZTEST(lifo_isr_to_thread, test_lifo_transfer_from_isr)
{
	isr_ran = false;
	irq_offload(lifo_isr, NULL);

	zassert_true(isr_ran, "ISR handler did not run");
	zassert_true(k_lifo_get(&test_lifo, K_NO_WAIT) == &item_b,
		     "First get did not return most recently inserted item");
	zassert_true(k_lifo_get(&test_lifo, K_NO_WAIT) == &item_a,
		     "Second get did not return first inserted item");
	zassert_is_null(k_lifo_get(&test_lifo, K_NO_WAIT),
			"LIFO should be empty after both gets");
}

ZTEST_SUITE(lifo_isr_to_thread, NULL, NULL, NULL, NULL, NULL);
