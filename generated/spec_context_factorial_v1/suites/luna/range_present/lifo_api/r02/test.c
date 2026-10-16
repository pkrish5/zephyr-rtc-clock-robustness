#include <zephyr/kernel.h>
#include <zephyr/irq_offload.h>
#include <zephyr/ztest.h>

struct lifo_item {
	void *link; /* Reserved for the kernel's LIFO linkage. */
	int value;
};

static struct k_lifo test_lifo;
static struct lifo_item first_item;
static struct lifo_item second_item;
static volatile bool isr_ran;

static void lifo_put_from_isr(const void *unused)
{
	ARG_UNUSED(unused);
	isr_ran = true;
	k_lifo_put(&test_lifo, &first_item);
	k_lifo_put(&test_lifo, &second_item);
}

ZTEST(lifo_isr_transfer, test_isr_items_are_received_in_reverse_order)
{
	k_lifo_init(&test_lifo);
	isr_ran = false;

	irq_offload(lifo_put_from_isr, NULL);

	zassert_true(isr_ran, "irq_offload handler did not run");
	zassert_equal(k_lifo_get(&test_lifo, K_NO_WAIT), &second_item,
		      "second inserted item should be retrieved first");
	zassert_equal(k_lifo_get(&test_lifo, K_NO_WAIT), &first_item,
		      "first inserted item should be retrieved second");
	zassert_is_null(k_lifo_get(&test_lifo, K_NO_WAIT),
			"LIFO should be empty after both items are retrieved");
}

ZTEST_SUITE(lifo_isr_transfer, NULL, NULL, NULL, NULL, NULL);
