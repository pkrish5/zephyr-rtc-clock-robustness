#include <zephyr/kernel.h>
#include <zephyr/irq_offload.h>
#include <zephyr/ztest.h>
#include <stdbool.h>

struct queue_item {
	void *link; /* First word reserved for kernel linkage. */
	int value;
};

static struct k_queue queue;
static struct queue_item first = { .value = 1 };
static struct queue_item second = { .value = 2 };
static volatile bool append_completed;
static volatile bool ran_in_isr;

static void append_from_isr(const void *unused)
{
	ARG_UNUSED(unused);
	ran_in_isr = k_is_in_isr();
	k_queue_append(&queue, &first);
	k_queue_append(&queue, &second);
	append_completed = true;
}

ZTEST(queue_isr_transfer, test_fifo_transfer)
{
	k_queue_init(&queue);
	append_completed = false;
	ran_in_isr = false;

	/* Offload completes before the test thread resumes. */
	irq_offload(append_from_isr, NULL);

	zassert_true(append_completed, "ISR append path did not complete");
	zassert_true(ran_in_isr, "Append callback was not in ISR context");
	zassert_equal_ptr(k_queue_get(&queue, K_NO_WAIT), &first,
			  "First item out of order");
	zassert_equal_ptr(k_queue_get(&queue, K_NO_WAIT), &second,
			  "Second item out of order");
	zassert_is_null(k_queue_get(&queue, K_NO_WAIT),
			"Queue contains an unexpected item");

	/* Functional test: the HSI accuracy does not bound delivery latency. */
}

ZTEST_SUITE(queue_isr_transfer, NULL, NULL, NULL, NULL, NULL);
