#include <zephyr/kernel.h>
#include <zephyr/irq_offload.h>
#include <zephyr/ztest.h>
#include <stdbool.h>

struct queue_item {
	void *link;
	int value;
};

static struct k_queue queue;
static struct queue_item items[2] = {
	{ .value = 1 },
	{ .value = 2 },
};
static volatile bool isr_append_completed;

static void append_from_isr(const void *arg)
{
	(void)arg;

	k_queue_append(&queue, &items[0]);
	k_queue_append(&queue, &items[1]);
	isr_append_completed = k_is_in_isr();
}

ZTEST(queue_isr_transfer, test_fifo_transfer)
{
	k_queue_init(&queue);
	isr_append_completed = false;

	irq_offload(append_from_isr, NULL);

	zassert_true(isr_append_completed, "ISR append path did not complete");
	zassert_equal_ptr(k_queue_get(&queue, K_NO_WAIT), &items[0],
			 "First item out of order");
	zassert_equal_ptr(k_queue_get(&queue, K_NO_WAIT), &items[1],
			 "Second item out of order");
	zassert_true(k_queue_is_empty(&queue), "Queue is not empty");
	zassert_is_null(k_queue_get(&queue, K_NO_WAIT),
			"Unexpected remaining item");
}

ZTEST_SUITE(queue_isr_transfer, NULL, NULL, NULL, NULL, NULL);
