#include <zephyr/kernel.h>
#include <zephyr/irq_offload.h>
#include <zephyr/ztest.h>
#include <stdbool.h>

struct queue_item {
	void *link; /* First word reserved for kernel linkage. */
};

static struct k_queue queue;
static struct queue_item first_item;
static struct queue_item second_item;
static volatile bool append_executed;
static volatile bool ran_in_isr;

static void append_from_isr(const void *arg)
{
	ARG_UNUSED(arg);

	ran_in_isr = k_is_in_isr();
	k_queue_append(&queue, &first_item);
	k_queue_append(&queue, &second_item);
	append_executed = true;
}

ZTEST(queue_isr_transfer, test_fifo_transfer)
{
	k_queue_init(&queue);
	append_executed = false;
	ran_in_isr = false;

	irq_offload(append_from_isr, NULL);

	zassert_true(append_executed, "ISR append path did not complete");
	zassert_true(ran_in_isr, "Append callback did not run in ISR context");
	zassert_equal_ptr(k_queue_get(&queue, K_NO_WAIT), &first_item,
			  "First item was not retrieved first");
	zassert_equal_ptr(k_queue_get(&queue, K_NO_WAIT), &second_item,
			  "Second item was not retrieved second");
	zassert_is_null(k_queue_get(&queue, K_NO_WAIT),
			"Queue still contains an item");
	zassert_true(k_queue_is_empty(&queue), "Queue is not empty");
}

ZTEST_SUITE(queue_isr_transfer, NULL, NULL, NULL, NULL, NULL);
