#include <zephyr/kernel.h>
#include <zephyr/irq_offload.h>
#include <zephyr/ztest.h>

K_SEM_DEFINE(test_sem, 0, 3);

static void give_from_isr(const void *unused)
{
    (void)unused;
    k_sem_give(&test_sem);
}

ZTEST(sem_irq_offload, test_multiple_isr_gives)
{
    zassert_equal(k_sem_count_get(&test_sem), 0);

    for (unsigned int expected = 1; expected <= 3; ++expected) {
        irq_offload(give_from_isr, NULL);
        zassert_equal(k_sem_count_get(&test_sem), expected);
    }
}

ZTEST_SUITE(sem_irq_offload, NULL, NULL, NULL, NULL, NULL);
