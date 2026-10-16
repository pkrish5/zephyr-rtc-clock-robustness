#include <zephyr/kernel.h>
#include <zephyr/irq_offload.h>
#include <zephyr/ztest.h>

#define GIVE_COUNT 3U

K_SEM_DEFINE(isr_sem, 0, GIVE_COUNT);

static void give_from_isr(const void *arg)
{
	ARG_UNUSED(arg);
	zassert_true(k_is_in_isr(), "Callback must run in interrupt context");
	k_sem_give(&isr_sem);
}

ZTEST(sem_irq, test_each_isr_give_increments_count)
{
	k_sem_reset(&isr_sem);
	zassert_equal(k_sem_count_get(&isr_sem), 0U,
		      "Initial semaphore count must be zero");

	for (unsigned int expected = 1U; expected <= GIVE_COUNT; ++expected) {
		irq_offload(give_from_isr, NULL);
		zassert_equal(k_sem_count_get(&isr_sem), expected,
			      "Each ISR give must increase the count by one");
	}
}

ZTEST_SUITE(sem_irq, NULL, NULL, NULL, NULL, NULL);
