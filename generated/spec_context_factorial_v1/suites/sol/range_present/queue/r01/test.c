#include <stdbool.h>
#include <zephyr/kernel.h>
#include <zephyr/irq_offload.h>
#include <zephyr/ztest.h>

struct queue_item {
	void *link; /* First word reserved for k_queue linkage. */
	int value;
};

static struct k_queue queue;
static struct queue_item first = { .value = 1 };
static struct queue_item second = { .value = 2 };
static volatile bool append_ran;
static volatile bool append_was_in_isr;

static void append_from_isr(const void *arg)
{
	ARG_UNUSED(arg);
	append_was_in_isr = k_is_in_isr();
	k_queue_append(&queue, &first);
	k_queue_append(&queue, &second);
	append_ran = true;
}

ZTEST(queue_isr_transfer, test_append_order_and_empty)
{
	void *first_out;
	void *second_out;

	k_queue_init(&queue);
	first.link = NULL;
	second.link = NULL;
	append_ran = false;
	append_was_in_isr = false;

	irq_offload(append_from_isr, NULL);

	zassert_true(append_ran, "ISR append path did not execute");
	zassert_true(append_was_in_isr, "append did not run in ISR context");
	first_out = k_queue_get(&queue, K_NO_WAIT);
	second_out = k_queue_get(&queue, K_NO_WAIT);
	zassert_true(first_out == &first, "first item was out of order");
	zassert_true(second_out == &second, "second item was out of order");
	zassert_true(k_queue_get(&queue, K_NO_WAIT) == NULL,
		     "queue was not empty");
}

ZTEST_SUITE(queue_isr_transfer, NULL, NULL, NULL, NULL, NULL);
