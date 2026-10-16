#include <zephyr/kernel.h>
#include <zephyr/irq_offload.h>
#include <zephyr/ztest.h>

struct queue_item {
    void *reserved;
    int value;
};

K_QUEUE_DEFINE(test_queue);

static struct queue_item item_a;
static struct queue_item item_b;
static volatile bool isr_ran;

static void queue_isr(const void *unused)
{
    ARG_UNUSED(unused);
    k_queue_append(&test_queue, &item_a);
    k_queue_append(&test_queue, &item_b);
    isr_ran = true;
}

ZTEST(queue_isr_transfer, test_isr_items_retrieved_in_order)
{
    item_a.value = 1;
    item_b.value = 2;
    isr_ran = false;

    irq_offload(queue_isr, NULL);

    zassert_true(isr_ran, "ISR append path did not execute");
    zassert_equal(k_queue_get(&test_queue, K_NO_WAIT), &item_a,
                  "first item was not retrieved in insertion order");
    zassert_equal(k_queue_get(&test_queue, K_NO_WAIT), &item_b,
                  "second item was not retrieved in insertion order");
    zassert_is_null(k_queue_get(&test_queue, K_NO_WAIT),
                    "queue should be empty after retrieving both items");
}

ZTEST_SUITE(queue_isr_transfer, NULL, NULL, NULL, NULL, NULL);
