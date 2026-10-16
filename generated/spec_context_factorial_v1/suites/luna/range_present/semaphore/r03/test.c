#include <zephyr/kernel.h>
#include <zephyr/irq_offload.h>
#include <zephyr/ztest.h>

K_SEM_DEFINE(isr_sem, 0, 3);

static void give_from_isr(const void *unused)
{
	ARG_UNUSED(unused);
	k_sem_give(&isr_sem);
}

ZTEST(sem_irq_offload, test_isr_gives_increment_count)
{
	k_sem_reset(&isr_sem);
	zassert_equal(k_sem_count_get(&isr_sem), 0U,
		      "semaphore must start at zero");

	irq_offload(give_from_isr, NULL);
	zassert_equal(k_sem_count_get(&isr_sem), 1U,
		      "first ISR give must increment count");

	irq_offload(give_from_isr, NULL);
	zassert_equal(k_sem_count_get(&isr_sem), 2U,
		      "second ISR give must increment count");

	irq_offload(give_from_isr, NULL);
	zassert_equal(k_sem_count_get(&isr_sem), 3U,
		      "third ISR give must not be lost");
}

ZTEST_SUITE(sem_irq_offload, NULL, NULL, NULL, NULL, NULL);
