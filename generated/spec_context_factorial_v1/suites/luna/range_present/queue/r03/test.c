#include <zephyr/ztest.h>
#include <zephyr/kernel.h>
#include <zephyr/irq_offload.h>

struct queue_item {
	void *kernel_link;
	int value;
};

static struct k_queue transfer_queue;
static struct queue_item item_first = { .value = 1 };
static struct queue_item item_second = { .value = 2 };
static volatile bool isr_append_ran;

static void append_items_from_isr(const void *unused)
{
	ARG_UNUSED(unused);
	k_queue_append(&transfer_queue, &item_first);
	k_queue_append(&transfer_queue, &item_second);
	isr_append_ran = true;
}

ZTEST(queue_isr_transfer, test_isr_append_order_and_empty)
{
	k_queue_init(&transfer_queue);
	isr_append_ran = false;

	irq_offload(append_items_from_isr, NULL);
	zassert_true(isr_append_ran, "ISR append path did not execute");

	void *first = k_queue_get(&transfer_queue, K_NO_WAIT);
	void *second = k_queue_get(&transfer_queue, K_NO_WAIT);
	zassert_equal_ptr(first, &item_first, "first item was not retrieved in insertion order");
	zassert_equal_ptr(second, &item_second, "second item was not retrieved in insertion order");
	zassert_is_null(k_queue_get(&transfer_queue, K_NO_WAIT), "queue should be empty");
}

ZTEST_SUITE(queue_isr_transfer, NULL, NULL, NULL, NULL, NULL);
