#include <zephyr/kernel.h>
#include <zephyr/irq_offload.h>
#include <zephyr/ztest.h>

struct queue_item {
	void *fifo_reserved; /* Reserved for the kernel's queue linkage. */
	int value;
};

K_QUEUE_DEFINE(test_queue);

static struct queue_item item_a;
static struct queue_item item_b;
static atomic_t isr_append_ran;

static void append_items_from_isr(const void *unused)
{
	ARG_UNUSED(unused);
	k_queue_append(&test_queue, &item_a);
	k_queue_append(&test_queue, &item_b);
	atomic_set(&isr_append_ran, 1);
}

ZTEST(queue_isr_transfer, test_isr_items_are_received_in_order)
{
	item_a.value = 1;
	item_b.value = 2;
	atomic_set(&isr_append_ran, 0);

	irq_offload(append_items_from_isr, NULL);

	zassert_equal(atomic_get(&isr_append_ran), 1,
		      "ISR append callback did not execute");
	zassert_true(k_queue_get(&test_queue, K_NO_WAIT) == &item_a,
		     "First retrieved pointer was not item_a");
	zassert_true(k_queue_get(&test_queue, K_NO_WAIT) == &item_b,
		     "Second retrieved pointer was not item_b");
	zassert_is_null(k_queue_get(&test_queue, K_NO_WAIT),
			"Queue was not empty after retrieving both items");
}

ZTEST_SUITE(queue_isr_transfer, NULL, NULL, NULL, NULL, NULL);
