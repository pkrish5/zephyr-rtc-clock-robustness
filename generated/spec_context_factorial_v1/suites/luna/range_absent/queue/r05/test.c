#include <zephyr/kernel.h>
#include <zephyr/irq_offload.h>
#include <zephyr/ztest.h>

struct queue_item {
	void *reserved;
	int value;
};

K_QUEUE_DEFINE(test_queue);

static struct queue_item item_one = { .reserved = NULL, .value = 1 };
static struct queue_item item_two = { .reserved = NULL, .value = 2 };
static volatile bool isr_append_executed;

static void append_items_from_isr(const void *unused)
{
	ARG_UNUSED(unused);
	k_queue_append(&test_queue, &item_one);
	k_queue_append(&test_queue, &item_two);
	isr_append_executed = true;
}

ZTEST(queue_isr_transfer, test_isr_append_and_thread_get)
{
	void *first;
	void *second;

	isr_append_executed = false;
	irq_offload(append_items_from_isr, NULL);

	zassert_true(isr_append_executed, "ISR append path did not execute");

	first = k_queue_get(&test_queue, K_NO_WAIT);
	second = k_queue_get(&test_queue, K_NO_WAIT);
	zassert_equal_ptr(first, &item_one, "first item must preserve insertion order");
	zassert_equal_ptr(second, &item_two, "second item must preserve insertion order");
	zassert_is_null(k_queue_get(&test_queue, K_NO_WAIT), "queue must be empty");
}

ZTEST_SUITE(queue_isr_transfer, NULL, NULL, NULL, NULL, NULL);
