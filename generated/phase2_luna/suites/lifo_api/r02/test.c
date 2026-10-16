#include <zephyr/kernel.h>
#include <zephyr/irq_offload.h>
#include <zephyr/ztest.h>

struct lifo_item {
    void *link;
    int value;
};

K_LIFO_DEFINE(test_lifo);

static struct lifo_item item_first = { .value = 1 };
static struct lifo_item item_second = { .value = 2 };
static volatile bool isr_ran;

static void lifo_isr(void *unused)
{
    ARG_UNUSED(unused);

    isr_ran = true;
    k_lifo_put(&test_lifo, &item_first);
    k_lifo_put(&test_lifo, &item_second);
}

ZTEST(lifo_isr_to_thread, test_lifo_transfer_from_isr)
{
    isr_ran = false;
    irq_offload(lifo_isr, NULL);

    zassert_true(isr_ran, "irq_offload handler did not run");
    zassert_equal(k_lifo_get(&test_lifo, K_NO_WAIT), &item_second,
                  "first get should return the most recently inserted item");
    zassert_equal(k_lifo_get(&test_lifo, K_NO_WAIT), &item_first,
                  "second get should return the first inserted item");
    zassert_is_null(k_lifo_get(&test_lifo, K_NO_WAIT),
                    "LIFO should be empty after both gets");
}

ZTEST_SUITE(lifo_isr_to_thread, NULL, NULL, NULL, NULL, NULL);
