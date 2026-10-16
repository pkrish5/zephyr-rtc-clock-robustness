#include <zephyr/ztest.h>
#include <zephyr/irq_offload.h>
#include <zephyr/kernel.h>

struct lifo_item {
    void *reserved;
    int value;
};

K_LIFO_DEFINE(test_lifo);
static struct lifo_item first_item;
static struct lifo_item second_item;
static volatile bool isr_ran;

static void lifo_isr(void *unused)
{
    ARG_UNUSED(unused);
    isr_ran = true;
    k_lifo_put(&test_lifo, &first_item);
    k_lifo_put(&test_lifo, &second_item);
}

ZTEST(lifo_irq, test_isr_to_thread_lifo)
{
    isr_ran = false;
    irq_offload(lifo_isr, NULL);

    zassert_true(isr_ran, "ISR handler did not run");
    zassert_is_null(k_lifo_get(&test_lifo, K_NO_WAIT), "LIFO should start empty");

    zassert_equal(k_lifo_get(&test_lifo, K_NO_WAIT), &second_item,
                  "First get should return the last item inserted by ISR");
    zassert_equal(k_lifo_get(&test_lifo, K_NO_WAIT), &first_item,
                  "Second get should return the first item inserted by ISR");
    zassert_is_null(k_lifo_get(&test_lifo, K_NO_WAIT), "LIFO should be empty after both gets");
}

ZTEST_SUITE(lifo_irq, NULL, NULL, NULL, NULL, NULL);
