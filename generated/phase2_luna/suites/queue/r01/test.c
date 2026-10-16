#include <zephyr/ztest.h>
#include <zephyr/kernel.h>
#include <zephyr/irq_offload.h>
#include <zephyr/sys/atomic.h>

struct queue_item {
    void *link; /* k_queue uses the first word for linkage. */
    int value;
};

K_QUEUE_DEFINE(test_queue);
static struct queue_item item_a = { .value = 1 };
static struct queue_item item_b = { .value = 2 };
static atomic_t isr_append_ran;

static void queue_isr(void *unused)
{
    ARG_UNUSED(unused);
    k_queue_append(&test_queue, &item_a);
    k_queue_append(&test_queue, &item_b);
    atomic_set(&isr_append_ran, 1);
}

ZTEST(queue_isr_transfer, test_isr_appends_in_order)
{
    k_queue_init(&test_queue);
    atomic_clear(&isr_append_ran);

    irq_offload(queue_isr, NULL);

    zassert_true(atomic_get(&isr_append_ran) != 0, "ISR append path did not execute");
    zassert_equal(k_queue_get(&test_queue, K_NO_WAIT), &item_a, "first item out of order");
    zassert_equal(k_queue_get(&test_queue, K_NO_WAIT), &item_b, "second item out of order");
    zassert_is_null(k_queue_get(&test_queue, K_NO_WAIT), "queue should be empty");
}

ZTEST_SUITE(queue_isr_transfer, NULL, NULL, NULL, NULL, NULL);
