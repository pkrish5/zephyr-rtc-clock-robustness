#include <zephyr/kernel.h>
#include <zephyr/irq_offload.h>
#include <zephyr/ztest.h>

struct lifo_item {
    void *reserved; /* First word is reserved for kernel linkage. */
    int value;
};

K_LIFO_DEFINE(test_lifo);

static struct lifo_item item_a;
static struct lifo_item item_b;
static volatile bool isr_ran;

static void lifo_put_from_isr(const void *unused)
{
    ARG_UNUSED(unused);
    isr_ran = true;
    k_lifo_put(&test_lifo, &item_a);
    k_lifo_put(&test_lifo, &item_b);
}

ZTEST(lifo_isr_transfer, test_isr_items_are_received_in_reverse_order)
{
    isr_ran = false;

    irq_offload(lifo_put_from_isr, NULL);

    zassert_true(isr_ran, "irq_offload handler did not run");
    zassert_equal(k_lifo_get(&test_lifo, K_NO_WAIT), &item_b,
                  "first get should return the last item inserted");
    zassert_equal(k_lifo_get(&test_lifo, K_NO_WAIT), &item_a,
                  "second get should return the first item inserted");
    zassert_is_null(k_lifo_get(&test_lifo, K_NO_WAIT),
                    "LIFO should be empty after both items are retrieved");
}

ZTEST_SUITE(lifo_isr_transfer, NULL, NULL, NULL, NULL, NULL);
