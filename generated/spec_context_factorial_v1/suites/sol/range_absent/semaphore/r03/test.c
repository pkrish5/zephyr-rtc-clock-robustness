#include <zephyr/kernel.h>
#include <zephyr/irq_offload.h>
#include <zephyr/ztest.h>

static void give_from_isr(const void *arg)
{
	k_sem_give((struct k_sem *)arg);
}

ZTEST(sem_irq_offload, test_multiple_isr_gives)
{
	struct k_sem sem;

	zassert_ok(k_sem_init(&sem, 0, 3));
	zassert_equal(k_sem_count_get(&sem), 0);

	for (unsigned int expected = 1; expected <= 3; expected++) {
		irq_offload(give_from_isr, &sem);
		zassert_equal(k_sem_count_get(&sem), expected);
	}
}

ZTEST_SUITE(sem_irq_offload, NULL, NULL, NULL, NULL, NULL);
