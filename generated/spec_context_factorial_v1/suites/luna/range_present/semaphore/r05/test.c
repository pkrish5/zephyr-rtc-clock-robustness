#include <zephyr/kernel.h>
#include <zephyr/irq_offload.h>
#include <zephyr/ztest.h>

K_SEM_DEFINE(test_sem, 0, 3);

static void give_sem_from_isr(const void *arg)
{
	struct k_sem *sem = (struct k_sem *)arg;

	k_sem_give(sem);
}

ZTEST(semaphore_irq, test_isr_gives_increment_count)
{
	k_sem_reset(&test_sem);
	zassert_equal(k_sem_count_get(&test_sem), 0U,
		      "semaphore must start empty");

	for (unsigned int expected = 1U; expected <= 3U; ++expected) {
		irq_offload(give_sem_from_isr, &test_sem);
		zassert_equal(k_sem_count_get(&test_sem), expected,
			      "ISR give %u should make count %u", expected,
			      expected);
	}
}

ZTEST_SUITE(semaphore_irq, NULL, NULL, NULL, NULL, NULL);
