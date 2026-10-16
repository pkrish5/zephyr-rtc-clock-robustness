#include <zephyr/kernel.h>
#include <zephyr/irq_offload.h>
#include <zephyr/ztest.h>

static struct k_sem sem;

static void give_from_isr(const void *arg)
{
	ARG_UNUSED(arg);
	k_sem_give(&sem);
}

ZTEST(sem_isr, test_each_isr_give_increments_count)
{
	k_sem_init(&sem, 0, 3);
	zassert_equal(k_sem_count_get(&sem), 0, "initial count must be zero");

	for (unsigned int expected = 1; expected <= 3; expected++) {
		irq_offload(give_from_isr, NULL);
		zassert_equal(k_sem_count_get(&sem), expected,
			      "ISR give did not increment count to %u", expected);
	}
}

ZTEST_SUITE(sem_isr, NULL, NULL, NULL, NULL, NULL);
