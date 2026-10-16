#include <zephyr/kernel.h>
#include <zephyr/irq_offload.h>
#include <zephyr/ztest.h>
#include <zephyr/sys/util.h>

struct queue_item {
	void *link;
	int value;
};

static struct k_queue queue;
static struct queue_item item_a;
static struct queue_item item_b;
static volatile bool isr_append_ran;

static void queue_append_isr(const void *unused)
{
	ARG_UNUSED(unused);
	k_queue_append(&queue, &item_a);
	k_queue_append(&queue, &item_b);
	isr_append_ran = true;
}

ZTEST(queue_isr_transfer, test_isr_appends_in_order)
{
	k_queue_init(&queue);
	item_a.link = NULL;
	item_a.value = 1;
	item_b.link = NULL;
	item_b.value = 2;
	isr_append_ran = false;

	irq_offload(queue_append_isr, NULL);

	zassert_true(isr_append_ran, "ISR append path did not execute");
	zassert_equal(k_queue_get(&queue, K_NO_WAIT), &item_a,
		      "first item was not retrieved in insertion order");
	zassert_equal(k_queue_get(&queue, K_NO_WAIT), &item_b,
		      "second item was not retrieved in insertion order");
	zassert_is_null(k_queue_get(&queue, K_NO_WAIT), "queue should be empty");
}

ZTEST_SUITE(queue_isr_transfer, NULL, NULL, NULL, NULL, NULL);
