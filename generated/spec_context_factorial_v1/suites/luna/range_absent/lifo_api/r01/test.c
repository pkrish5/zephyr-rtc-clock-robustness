#include <zephyr/ztest.h>
#include <zephyr/kernel.h>
#include <zephyr/irq_offload.h>

struct lifo_item {
    void *reserved;
    int value;
};

K_LIFO_DEFINE(test_lifo);

static struct lifo_item item_a;
static struct lifo_item item_b;
static volatile bool isr_ran;

static void lifo_isr(const void *unused)
{
    ARG_UNUSED(unused);
    isr_ran = true;
    k_lifo_put(&test_lifo, &item_a);
    k_lifo_put(&test_lifo, &item_b);
}

ZTEST(lifo_isr_transfer, test_isr_to_thread)
{
    isr_ran = false;
    irq_offload(lifo_isr, NULL);

    zassert_true(isr_ran, "irq_offload handler did not run");
    zassert_equal(k_lifo_get(&test_lifo, K_NO_WAIT), &item_b,
                  "first get should return the last inserted item");
    zassert_equal(k_lifo_get(&test_lifo, K_NO_WAIT), &item_a,
                  "second get should return the first inserted item");
    zassert_is_null(k_lifo_get(&test_lifo, K_NO_WAIT),
                    "LIFO should be empty after both items are retrieved");
}

ZTEST_SUITE(lifo_isr_transfer, NULL, NULL, NULL, NULL, NULL);
