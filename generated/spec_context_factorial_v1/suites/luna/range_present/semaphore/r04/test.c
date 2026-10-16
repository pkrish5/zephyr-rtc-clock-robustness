#include <zephyr/kernel.h>
#include <zephyr/irq_offload.h>
#include <zephyr/ztest.h>

K_SEM_DEFINE(isr_sem, 0, 3);

static void give_from_isr(const void *unused)
{
    ARG_UNUSED(unused);
    k_sem_give(&isr_sem);
}

ZTEST(isr_semaphore, test_irq_offload_gives_increment_count)
{
    k_sem_reset(&isr_sem);
    zassert_equal(k_sem_count_get(&isr_sem), 0U, "initial count must be zero");

    irq_offload(give_from_isr, NULL);
    zassert_equal(k_sem_count_get(&isr_sem), 1U, "count after first ISR give");

    irq_offload(give_from_isr, NULL);
    zassert_equal(k_sem_count_get(&isr_sem), 2U, "count after second ISR give");
}

ZTEST_SUITE(isr_semaphore, NULL, NULL, NULL, NULL, NULL);
