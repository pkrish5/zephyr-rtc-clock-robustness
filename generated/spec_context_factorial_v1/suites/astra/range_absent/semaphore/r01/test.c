#include <zephyr/kernel.h>
#include <zephyr/irq_offload.h>
#include <zephyr/ztest.h>

#define GIVE_COUNT 3U

K_SEM_DEFINE(test_sem, 0, GIVE_COUNT);

static void give_from_isr(const void *arg)
{
	(void)arg;
	k_sem_give(&test_sem);
}

ZTEST(sem_isr, test_count_increments)
{
	k_sem_reset(&test_sem);
	zassert_equal(k_sem_count_get(&test_sem), 0U,
		      "Initial semaphore count must be zero");

	for (unsigned int expected = 1U; expected <= GIVE_COUNT; ++expected) {
		irq_offload(give_from_isr, NULL);
		zassert_equal(k_sem_count_get(&test_sem), expected,
			      "Each ISR give must increment the count by one");
	}
}

ZTEST_SUITE(sem_isr, NULL, NULL, NULL, NULL, NULL);
