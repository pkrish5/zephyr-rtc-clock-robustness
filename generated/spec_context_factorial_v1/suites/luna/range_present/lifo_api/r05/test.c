#include <zephyr/ztest.h>
#include <zephyr/irq_offload.h>
#include <zephyr/kernel.h>

struct lifo_item {
    void *link; /* k_lifo uses the first pointer-sized word for linkage. */
    uint32_t value;
};

K_LIFO_DEFINE(test_lifo);

static struct lifo_item item_a;
static struct lifo_item item_b;
static volatile bool isr_ran;

static void lifo_put_isr(const void *unused)
{
    ARG_UNUSED(unused);
    isr_ran = true;
    k_lifo_put(&test_lifo, &item_a);
    k_lifo_put(&test_lifo, &item_b);
}

ZTEST(lifo_isr_to_thread, test_reverse_order_and_empty)
{
    isr_ran = false;

    irq_offload(lifo_put_isr, NULL);

    zassert_true(isr_ran, "ISR handler was not run");

    void *first = k_lifo_get(&test_lifo, K_NO_WAIT);
    void *second = k_lifo_get(&test_lifo, K_NO_WAIT);

    zassert_true(first == &item_b, "first item should be the last inserted");
    zassert_true(second == &item_a, "second item should be the first inserted");
    zassert_is_null(k_lifo_get(&test_lifo, K_NO_WAIT), "LIFO should be empty");
}

ZTEST_SUITE(lifo_isr_to_thread, NULL, NULL, NULL, NULL, NULL);
