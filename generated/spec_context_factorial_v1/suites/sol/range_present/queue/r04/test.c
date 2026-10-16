#include <stdbool.h>
#include <zephyr/kernel.h>
#include <zephyr/irq_offload.h>
#include <zephyr/ztest.h>

struct queue_item {
    void *kernel_link;
    int value;
};

static struct k_queue test_queue;
static struct queue_item items[2] = {
    { .value = 1 },
    { .value = 2 },
};
static volatile bool appended_in_isr;

static void append_from_isr(const void *unused)
{
    (void)unused;
    bool in_isr = k_is_in_isr();

    k_queue_append(&test_queue, &items[0]);
    k_queue_append(&test_queue, &items[1]);
    appended_in_isr = in_isr;
}

ZTEST(queue_isr_transfer, test_append_order_and_empty)
{
    void *first;
    void *second;
    void *remaining;

    k_queue_init(&test_queue);
    appended_in_isr = false;
    irq_offload(append_from_isr, NULL);

    zassert_true(appended_in_isr, "ISR append path did not execute");

    first = k_queue_get(&test_queue, K_NO_WAIT);
    second = k_queue_get(&test_queue, K_NO_WAIT);
    remaining = k_queue_get(&test_queue, K_NO_WAIT);

    zassert_true(first == &items[0], "first item was out of order");
    zassert_true(second == &items[1], "second item was out of order");
    zassert_is_null(remaining, "queue was not empty");
}

ZTEST_SUITE(queue_isr_transfer, NULL, NULL, NULL, NULL, NULL);
