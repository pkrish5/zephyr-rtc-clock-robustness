#include <zephyr/kernel.h>
#include <zephyr/irq_offload.h>
#include <zephyr/ztest.h>

K_SEM_DEFINE(isr_sem, 0, 3);

static void give_from_isr(const void *arg)
{
    (void)arg;
    k_sem_give(&isr_sem);
}

ZTEST(sem_irq_offload, test_multiple_isr_gives)
{
    zassert_equal(k_sem_count_get(&isr_sem), 0U, "initial count is not zero");

    for (unsigned int expected = 1U; expected <= 3U; ++expected) {
        irq_offload(give_from_isr, NULL);
        zassert_equal(k_sem_count_get(&isr_sem), expected,
                      "ISR give did not increment count by one");
    }
}

ZTEST_SUITE(sem_irq_offload, NULL, NULL, NULL, NULL, NULL);
