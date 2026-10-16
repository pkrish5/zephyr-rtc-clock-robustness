#include <zephyr/kernel.h>
#include <zephyr/irq_offload.h>
#include <zephyr/ztest.h>

struct queue_item {
    void *reserved;
    int value;
};

K_QUEUE_DEFINE(test_queue);

static struct queue_item first_item;
static struct queue_item second_item;
static volatile bool isr_append_executed;

static void append_items_from_isr(const void *unused)
{
    ARG_UNUSED(unused);

    k_queue_append(&test_queue, &first_item);
    k_queue_append(&test_queue, &second_item);
    isr_append_executed = true;
}

ZTEST(queue_isr_transfer, test_isr_append_order_and_empty)
{
    first_item.reserved = NULL;
    first_item.value = 1;
    second_item.reserved = NULL;
    second_item.value = 2;
    isr_append_executed = false;

    irq_offload(append_items_from_isr, NULL);

    zassert_true(isr_append_executed, "ISR append path did not execute");
    zassert_true(k_queue_get(&test_queue, K_NO_WAIT) == &first_item,
                 "First retrieved item was not the first appended item");
    zassert_true(k_queue_get(&test_queue, K_NO_WAIT) == &second_item,
                 "Second retrieved item was not the second appended item");
    zassert_is_null(k_queue_get(&test_queue, K_NO_WAIT),
                    "Queue should be empty after retrieving both items");
}

ZTEST_SUITE(queue_isr_transfer, NULL, NULL, NULL, NULL, NULL);
