#include <zephyr/kernel.h>
#include <zephyr/irq_offload.h>
#include <zephyr/ztest.h>

struct queue_item {
	void *link;
	int value;
};

K_QUEUE_DEFINE(test_queue);

static struct queue_item first = { .value = 1 };
static struct queue_item second = { .value = 2 };
static volatile bool append_path_executed;
static volatile bool append_ran_in_isr;

static void append_from_isr(const void *arg)
{
	ARG_UNUSED(arg);
	append_ran_in_isr = k_is_in_isr();
	k_queue_append(&test_queue, &first);
	k_queue_append(&test_queue, &second);
	append_path_executed = true;
}

ZTEST(queue_isr, test_isr_to_thread_order)
{
	irq_offload(append_from_isr, NULL);

	zassert_true(append_path_executed, "ISR append path did not execute");
	zassert_true(append_ran_in_isr, "append callback did not run in ISR context");
	zassert_true(k_queue_get(&test_queue, K_NO_WAIT) == &first,
		     "first item was out of order");
	zassert_true(k_queue_get(&test_queue, K_NO_WAIT) == &second,
		     "second item was out of order");
	zassert_is_null(k_queue_get(&test_queue, K_NO_WAIT),
			"queue was not empty");
}

ZTEST_SUITE(queue_isr, NULL, NULL, NULL, NULL, NULL);
