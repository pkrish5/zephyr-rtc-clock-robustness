#include <zephyr/kernel.h>
#include <zephyr/irq_offload.h>
#include <zephyr/ztest.h>

struct queue_item {
	void *link;
	int value;
};

K_QUEUE_DEFINE(test_queue);

static struct queue_item first_item = { .value = 1 };
static struct queue_item second_item = { .value = 2 };
static volatile bool append_ran_in_isr;

static void append_from_isr(const void *arg)
{
	ARG_UNUSED(arg);
	append_ran_in_isr = k_is_in_isr();
	k_queue_append(&test_queue, &first_item);
	k_queue_append(&test_queue, &second_item);
}

ZTEST(queue_isr, test_append_order_and_empty)
{
	append_ran_in_isr = false;
	irq_offload(append_from_isr, NULL);

	zassert_true(append_ran_in_isr, "append path did not run in an ISR");
	zassert_true(k_queue_get(&test_queue, K_NO_WAIT) == &first_item,
		     "first item was not retrieved first");
	zassert_true(k_queue_get(&test_queue, K_NO_WAIT) == &second_item,
		     "second item was not retrieved second");
	zassert_true(k_queue_get(&test_queue, K_NO_WAIT) == NULL,
		     "queue is not empty");
}

ZTEST_SUITE(queue_isr, NULL, NULL, NULL, NULL, NULL);
