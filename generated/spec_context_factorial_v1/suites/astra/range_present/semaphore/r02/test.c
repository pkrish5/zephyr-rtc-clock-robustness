#include <zephyr/kernel.h>
#include <zephyr/irq_offload.h>
#include <zephyr/ztest.h>

#define GIVE_COUNT 3U

K_SEM_DEFINE(isr_sem, 0, GIVE_COUNT);

static void give_from_isr(const void *arg)
{
	(void)arg;
	k_sem_give(&isr_sem);
}

ZTEST(sem_isr, test_count_after_each_isr_give)
{
	k_sem_reset(&isr_sem);
	zassert_equal(k_sem_count_get(&isr_sem), 0U,
		      "Initial semaphore count must be zero");

	/* irq_offload completes the handler before returning. */
	for (unsigned int expected = 1U; expected <= GIVE_COUNT; ++expected) {
		irq_offload(give_from_isr, NULL);
		zassert_equal(k_sem_count_get(&isr_sem), expected,
			      "Count must increase by one after ISR give %u",
			      expected);
	}
}

ZTEST_SUITE(sem_isr, NULL, NULL, NULL, NULL, NULL);
