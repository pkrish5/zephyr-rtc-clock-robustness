#include <stdbool.h>
#include <zephyr/kernel.h>
#include <zephyr/irq_offload.h>
#include <zephyr/ztest.h>

struct queue_item {
	void *link; /* Reserved for k_queue linkage. */
	int value;
};

static struct k_queue test_queue;
static struct queue_item items[2];
static volatile bool isr_append_executed;

static void append_from_isr(const void *unused)
{
	(void)unused;
	k_queue_append(&test_queue, &items[0]);
	k_queue_append(&test_queue, &items[1]);
	isr_append_executed = true;
}

ZTEST(queue_isr_transfer, test_append_order_and_empty)
{
	k_queue_init(&test_queue);
	isr_append_executed = false;

	irq_offload(append_from_isr, NULL);

	zassert_true(isr_append_executed, "ISR append path did not execute");
	zassert_true(k_queue_get(&test_queue, K_NO_WAIT) == &items[0],
		     "first item was out of order");
	zassert_true(k_queue_get(&test_queue, K_NO_WAIT) == &items[1],
		     "second item was out of order");
	zassert_is_null(k_queue_get(&test_queue, K_NO_WAIT),
			"queue was not empty");
}

ZTEST_SUITE(queue_isr_transfer, NULL, NULL, NULL, NULL, NULL);