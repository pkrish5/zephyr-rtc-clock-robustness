#include <zephyr/ztest.h>
#include <zephyr/irq_offload.h>
#include <zephyr/kernel.h>
#include <zephyr/sys/atomic.h>

struct lifo_item {
    void *link;
    uint32_t value;
};

K_LIFO_DEFINE(test_lifo);

static struct lifo_item item_a;
static struct lifo_item item_b;
static atomic_t isr_ran;

static void lifo_put_isr(const void *arg)
{
    ARG_UNUSED(arg);

    k_lifo_put(&test_lifo, &item_a);
    k_lifo_put(&test_lifo, &item_b);
    atomic_set(&isr_ran, 1);
}

ZTEST(lifo_irq_transfer, test_isr_to_thread_lifo)
{
    item_a.value = 1U;
    item_b.value = 2U;
    atomic_clear(&isr_ran);

    irq_offload(lifo_put_isr, NULL);

    zassert_equal(atomic_get(&isr_ran), 1, "ISR handler did not run");
    zassert_true(k_lifo_get(&test_lifo, K_NO_WAIT) == &item_b,
                 "first get should return the last inserted item");
    zassert_true(k_lifo_get(&test_lifo, K_NO_WAIT) == &item_a,
                 "second get should return the first inserted item");
    zassert_is_null(k_lifo_get(&test_lifo, K_NO_WAIT),
                    "LIFO should be empty after both items are retrieved");
}

ZTEST_SUITE(lifo_irq_transfer, NULL, NULL, NULL, NULL, NULL);
