#include <zephyr/kernel.h>
#include <zephyr/irq_offload.h>
#include <zephyr/ztest.h>
#include <stdbool.h>

struct queue_item {
	void *link; /* First word reserved for kernel linkage. */
};

static struct k_queue queue;
static struct queue_item items[2];
static volatile bool append_path_executed;
static volatile bool callback_in_isr;

static void append_from_isr(const void *unused)
{
	(void)unused;
	callback_in_isr = k_is_in_isr();
	k_queue_append(&queue, &items[0]);
	k_queue_append(&queue, &items[1]);
	append_path_executed = true;
}

ZTEST(queue_isr_transfer, test_fifo_transfer)
{
	k_queue_init(&queue);
	append_path_executed = false;
	callback_in_isr = false;

	/* irq_offload completes the callback before returning. */
	irq_offload(append_from_isr, NULL);

	zassert_true(callback_in_isr, "Callback must run in ISR context");
	zassert_true(append_path_executed, "ISR append path did not complete");
	zassert_equal_ptr(k_queue_get(&queue, K_NO_WAIT), &items[0],
			  "First item out of order");
	zassert_equal_ptr(k_queue_get(&queue, K_NO_WAIT), &items[1],
			  "Second item out of order");
	zassert_true(k_queue_is_empty(&queue), "Queue must be empty");
	zassert_is_null(k_queue_get(&queue, K_NO_WAIT),
			"Unexpected remaining item");
}

ZTEST_SUITE(queue_isr_transfer, NULL, NULL, NULL, NULL, NULL);
