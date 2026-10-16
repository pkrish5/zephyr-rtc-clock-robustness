#include <zephyr/kernel.h>
#include <zephyr/irq_offload.h>
#include <zephyr/ztest.h>

struct queue_item {
	void *link; /* First word reserved for kernel linkage. */
	int value;
};

K_QUEUE_DEFINE(test_queue);

static struct queue_item items[2] = {
	{ .value = 1 },
	{ .value = 2 },
};
static volatile unsigned int appended;
static volatile bool ran_in_isr;

static void append_from_isr(const void *arg)
{
	ARG_UNUSED(arg);

	ran_in_isr = k_is_in_isr();
	k_queue_append(&test_queue, &items[0]);
	appended++;
	k_queue_append(&test_queue, &items[1]);
	appended++;
}

ZTEST(queue_isr_transfer, test_fifo_transfer)
{
	appended = 0;
	ran_in_isr = false;

	/* irq_offload returns after the ISR callback completes. */
	irq_offload(append_from_isr, NULL);

	zassert_true(ran_in_isr, "Append callback did not run in ISR context");
	zassert_equal(appended, 2U, "ISR did not complete both appends");
	zassert_equal_ptr(k_queue_get(&test_queue, K_NO_WAIT), &items[0],
			  "First item out of order");
	zassert_equal_ptr(k_queue_get(&test_queue, K_NO_WAIT), &items[1],
			  "Second item out of order");
	zassert_is_null(k_queue_get(&test_queue, K_NO_WAIT),
			"Queue still contains an item");

	/* Functional test: HSI accuracy alone supplies no delivery-latency bound. */
}

ZTEST_SUITE(queue_isr_transfer, NULL, NULL, NULL, NULL, NULL);
