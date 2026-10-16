#include <stdbool.h>
#include <stdint.h>
#include <zephyr/irq_offload.h>
#include <zephyr/kernel.h>
#include <zephyr/ztest.h>

struct lifo_item {
    void *link; /* First word reserved for k_lifo linkage. */
    uint32_t id;
};

static struct k_lifo lifo;
static struct lifo_item first_item = { .id = 1 };
static struct lifo_item second_item = { .id = 2 };
static volatile bool ran_in_isr;

static void put_from_isr(const void *unused)
{
    ARG_UNUSED(unused);
    ran_in_isr = k_is_in_isr();
    k_lifo_put(&lifo, &first_item);
    k_lifo_put(&lifo, &second_item);
}

ZTEST(lifo_irq_transfer, test_isr_to_thread_order)
{
    k_lifo_init(&lifo);
    ran_in_isr = false;

    irq_offload(put_from_isr, NULL);

    zassert_true(ran_in_isr, "put callback did not run in ISR context");
    zassert_true(k_lifo_get(&lifo, K_NO_WAIT) == &second_item,
                 "second item was not retrieved first");
    zassert_true(k_lifo_get(&lifo, K_NO_WAIT) == &first_item,
                 "first item was not retrieved second");
    zassert_true(k_lifo_get(&lifo, K_NO_WAIT) == NULL,
                 "LIFO was not empty after two gets");
}

ZTEST_SUITE(lifo_irq_transfer, NULL, NULL, NULL, NULL, NULL);
