#include <stdbool.h>
#include <zephyr/kernel.h>
#include <zephyr/irq_offload.h>
#include <zephyr/ztest.h>

struct queue_item {
	void *queue_link;
	int value;
};

static struct k_queue test_queue;
static struct queue_item first_item = { .value = 1 };
static struct queue_item second_item = { .value = 2 };
static volatile bool isr_append_executed;
static volatile bool append_was_in_isr;

static void append_from_isr(const void *arg)
{
	struct k_queue *queue = (struct k_queue *)arg;

	append_was_in_isr = k_is_in_isr();
	k_queue_append(queue, &first_item);
	k_queue_append(queue, &second_item);
	isr_append_executed = true;
}

ZTEST(queue_isr_transfer, test_fifo_order)
{
	void *item;

	k_queue_init(&test_queue);
	isr_append_executed = false;
	append_was_in_isr = false;

	irq_offload(append_from_isr, &test_queue);

	zassert_true(isr_append_executed, "ISR append path did not execute");
	zassert_true(append_was_in_isr, "append did not run in ISR context");

	item = k_queue_get(&test_queue, K_NO_WAIT);
	zassert_true(item == &first_item, "first item was out of order");
	item = k_queue_get(&test_queue, K_NO_WAIT);
	zassert_true(item == &second_item, "second item was out of order");
	zassert_true(k_queue_get(&test_queue, K_NO_WAIT) == NULL,
		     "queue was not empty");
}

ZTEST_SUITE(queue_isr_transfer, NULL, NULL, NULL, NULL, NULL);
