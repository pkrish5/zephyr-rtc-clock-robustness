#include <zephyr/kernel.h>
#include <zephyr/irq_offload.h>
#include <zephyr/ztest.h>

struct queue_item {
    void *link; /* First word reserved for k_queue linkage. */
    int id;
};

static struct k_queue test_queue;
static struct queue_item items[2] = {
    { .id = 1 },
    { .id = 2 },
};
static volatile int isr_appends;

static void append_from_isr(const void *unused)
{
    ARG_UNUSED(unused);

    k_queue_append(&test_queue, &items[0]);
    isr_appends++;
    k_queue_append(&test_queue, &items[1]);
    isr_appends++;
}

ZTEST(queue_isr_transfer, test_append_order_and_empty)
{
    k_queue_init(&test_queue);
    isr_appends = 0;

    irq_offload(append_from_isr, NULL);

    zassert_equal(isr_appends, 2, "ISR append path did not complete");
    zassert_true(k_queue_get(&test_queue, K_NO_WAIT) == &items[0],
                 "first item was out of order");
    zassert_true(k_queue_get(&test_queue, K_NO_WAIT) == &items[1],
                 "second item was out of order");
    zassert_is_null(k_queue_get(&test_queue, K_NO_WAIT),
                    "queue was not empty");
}

ZTEST_SUITE(queue_isr_transfer, NULL, NULL, NULL, NULL, NULL);
