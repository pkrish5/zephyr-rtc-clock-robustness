#include <zephyr/kernel.h>
#include <zephyr/irq_offload.h>
#include <zephyr/ztest.h>

K_SEM_DEFINE(test_sem, 0, 2);

static void give_from_isr(const void *arg)
{
	(void)arg;
	k_sem_give(&test_sem);
}

ZTEST(sem_isr, test_count_after_each_isr_give)
{
	k_sem_reset(&test_sem);
	zassert_equal(k_sem_count_get(&test_sem), 0U,
		      "Initial count must be zero");

	for (unsigned int expected = 1U; expected <= 2U; ++expected) {
		irq_offload(give_from_isr, NULL);
		zassert_equal(k_sem_count_get(&test_sem), expected,
			      "Each ISR give must increase the count by one");
	}
}

ZTEST_SUITE(sem_isr, NULL, NULL, NULL, NULL, NULL);
