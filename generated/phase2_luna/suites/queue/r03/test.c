#include <zephyr/ztest.h>
#include <zephyr/kernel.h>
#include <zephyr/irq_offload.h>

struct queue_item {
    void *reserved;
    int value;
};

static struct k_queue test_queue;
static struct queue_item first_item;
static struct queue_item second_item;
static volatile bool isr_append_ran;

static void append_items_from_isr(const void *unused)
{
    ARG_UNUSED(unused);
    k_queue_append(&test_queue, &first_item);
    k_queue_append(&test_queue, &second_item);
    isr_append_ran = true;
}

ZTEST(queue_isr_transfer, test_isr_append_order_and_empty)
{
    k_queue_init(&test_queue);
    first_item = (struct queue_item){ .reserved = NULL, .value = 1 };
    second_item = (struct queue_item){ .reserved = NULL, .value = 2 };
    isr_append_ran = false;

    irq_offload(append_items_from_isr, NULL);

    zassert_true(isr_append_ran, "ISR append path did not execute");
    zassert_equal(k_queue_get(&test_queue, K_NO_WAIT), &first_item,
                  "first retrieved item was not the first appended item");
    zassert_equal(k_queue_get(&test_queue, K_NO_WAIT), &second_item,
                  "second retrieved item was not the second appended item");
    zassert_is_null(k_queue_get(&test_queue, K_NO_WAIT),
                    "queue should be empty after retrieving both items");
}

ZTEST_SUITE(queue_isr_transfer, NULL, NULL, NULL, NULL, NULL);
