#include <zephyr/kernel.h>
#include <zephyr/irq_offload.h>
#include <zephyr/ztest.h>

struct lifo_item {
    void *reserved;
    int value;
};

K_LIFO_DEFINE(test_lifo);

static struct lifo_item item_a;
static struct lifo_item item_b;
static volatile bool isr_ran;

static void lifo_isr(const void *arg)
{
    ARG_UNUSED(arg);
    isr_ran = true;
    k_lifo_put(&test_lifo, &item_a);
    k_lifo_put(&test_lifo, &item_b);
}

ZTEST(lifo_irq, test_isr_to_thread_lifo)
{
    isr_ran = false;
    irq_offload(lifo_isr, NULL);

    zassert_true(isr_ran, "irq_offload handler did not run");
    zassert_true(k_lifo_get(&test_lifo, K_NO_WAIT) == &item_b,
                 "first item was not the most recently inserted");
    zassert_true(k_lifo_get(&test_lifo, K_NO_WAIT) == &item_a,
                 "second item was not the earliest inserted");
    zassert_is_null(k_lifo_get(&test_lifo, K_NO_WAIT), "LIFO should be empty");
}

ZTEST_SUITE(lifo_irq, NULL, NULL, NULL, NULL, NULL);
