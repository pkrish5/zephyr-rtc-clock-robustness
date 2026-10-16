#include <zephyr/kernel.h>
#include <zephyr/irq_offload.h>
#include <zephyr/ztest.h>

struct queue_item {
	void *link; /* k_queue reserves the first word for linkage. */
	int value;
};

static struct k_queue test_queue;
static struct queue_item item1 = { .value = 1 };
static struct queue_item item2 = { .value = 2 };
static volatile bool isr_append_ran;

static void queue_append_isr(const void *unused)
{
	ARG_UNUSED(unused);
	k_queue_append(&test_queue, &item1);
	k_queue_append(&test_queue, &item2);
	isr_append_ran = true;
}

ZTEST(queue_isr_transfer, test_isr_append_order_and_empty)
{
	void *first;
	void *second;

	k_queue_init(&test_queue);
	isr_append_ran = false;

	irq_offload(queue_append_isr, NULL);

	zassert_true(isr_append_ran, "ISR append path did not execute");
	first = k_queue_get(&test_queue, K_NO_WAIT);
	second = k_queue_get(&test_queue, K_NO_WAIT);

	zassert_true(first == &item1, "first retrieved pointer was not item1");
	zassert_true(second == &item2, "second retrieved pointer was not item2");
	zassert_is_null(k_queue_get(&test_queue, K_NO_WAIT), "queue should be empty");
}

ZTEST_SUITE(queue_isr_transfer, NULL, NULL, NULL, NULL, NULL);
