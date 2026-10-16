#include <zephyr/kernel.h>
#include <zephyr/irq_offload.h>
#include <zephyr/ztest.h>

K_SEM_DEFINE(isr_sem, 0, 4);

static void give_from_isr(const void *arg)
{
	(void)arg;
	k_sem_give(&isr_sem);
}

ZTEST(sem_isr, test_each_isr_give_increments_count)
{
	k_sem_reset(&isr_sem);
	zassert_equal(k_sem_count_get(&isr_sem), 0U,
		      "Initial semaphore count must be zero");

	/* irq_offload completes the handler before returning. No thread
	 * takes this semaphore, and all gives remain below its limit.
	 */
	for (unsigned int expected = 1U; expected <= 3U; ++expected) {
		irq_offload(give_from_isr, NULL);
		zassert_equal(k_sem_count_get(&isr_sem), expected,
			      "ISR give %u did not increment the count", expected);
	}
}

ZTEST_SUITE(sem_isr, NULL, NULL, NULL, NULL, NULL);
