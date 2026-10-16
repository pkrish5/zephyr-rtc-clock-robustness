#include <zephyr/ztest.h>
#include <zephyr/kernel.h>
#include <zephyr/irq_offload.h>

struct queue_item {
    void *reserved;
    int value;
};

K_QUEUE_DEFINE(test_queue);

static struct queue_item item_one;
static struct queue_item item_two;
static volatile bool isr_append_ran;

static void queue_append_isr(const void *unused)
{
    ARG_UNUSED(unused);
    k_queue_append(&test_queue, &item_one);
    k_queue_append(&test_queue, &item_two);
    isr_append_ran = true;
}

ZTEST(queue_isr_transfer, test_isr_append_order_and_empty)
{
    item_one.value = 1;
    item_two.value = 2;
    isr_append_ran = false;

    irq_offload(queue_append_isr, NULL);

    zassert_true(isr_append_ran, "ISR append path did not execute");
    zassert_equal(k_queue_get(&test_queue, K_NO_WAIT), &item_one,
                  "First retrieved item must be the first appended item");
    zassert_equal(k_queue_get(&test_queue, K_NO_WAIT), &item_two,
                  "Second retrieved item must be the second appended item");
    zassert_is_null(k_queue_get(&test_queue, K_NO_WAIT),
                    "Queue should be empty after retrieving both items");
}

ZTEST_SUITE(queue_isr_transfer, NULL, NULL, NULL, NULL, NULL);
