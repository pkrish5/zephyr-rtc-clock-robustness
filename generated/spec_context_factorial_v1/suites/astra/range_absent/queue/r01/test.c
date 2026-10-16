#include <zephyr/kernel.h>
#include <zephyr/irq_offload.h>
#include <zephyr/ztest.h>
#include <stdbool.h>
#include <stddef.h>

struct queue_item {
	void *link; /* First word reserved for kernel linkage. */
	int value;
};

static struct k_queue queue;
static struct queue_item first = { .value = 1 };
static struct queue_item second = { .value = 2 };
static volatile bool isr_append_executed;

static void append_from_isr(const void *unused)
{
	ARG_UNUSED(unused);

	k_queue_append(&queue, &first);
	k_queue_append(&queue, &second);
	isr_append_executed = k_is_in_isr();
}

ZTEST(queue_isr_transfer, test_fifo_transfer)
{
	k_queue_init(&queue);
	isr_append_executed = false;

	irq_offload(append_from_isr, NULL);

	zassert_true(isr_append_executed, "ISR append path did not execute");
	zassert_equal_ptr(k_queue_get(&queue, K_NO_WAIT), &first,
			  "First item was not retrieved first");
	zassert_equal_ptr(k_queue_get(&queue, K_NO_WAIT), &second,
			  "Second item was not retrieved second");
	zassert_is_null(k_queue_get(&queue, K_NO_WAIT),
			"An item remains in the queue");
	zassert_true(k_queue_is_empty(&queue), "Queue is not empty");
}

ZTEST_SUITE(queue_isr_transfer, NULL, NULL, NULL, NULL, NULL);
