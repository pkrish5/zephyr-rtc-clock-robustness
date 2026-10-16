#include <zephyr/ztest.h>
#include <zephyr/kernel.h>
#include <zephyr/irq_offload.h>

struct queue_item {
	void *link;
	int value;
};

static struct k_queue test_queue;
static struct queue_item item_a;
static struct queue_item item_b;
static volatile bool isr_append_ran;

static void queue_append_isr(const void *arg)
{
	ARG_UNUSED(arg);
	isr_append_ran = true;
	k_queue_append(&test_queue, &item_a);
	k_queue_append(&test_queue, &item_b);
}

ZTEST(queue_isr_transfer, test_isr_append_order_and_empty)
{
	void *first;
	void *second;

	k_queue_init(&test_queue);
	item_a.value = 1;
	item_b.value = 2;
	isr_append_ran = false;

	irq_offload(queue_append_isr, NULL);

	zassert_true(isr_append_ran, "ISR append path did not execute");
	first = k_queue_get(&test_queue, K_NO_WAIT);
	second = k_queue_get(&test_queue, K_NO_WAIT);
	zassert_equal(first, &item_a, "first retrieved pointer was not item_a");
	zassert_equal(second, &item_b, "second retrieved pointer was not item_b");
	zassert_is_null(k_queue_get(&test_queue, K_NO_WAIT), "queue was not empty");
}

ZTEST_SUITE(queue_isr_transfer, NULL, NULL, NULL, NULL, NULL);
