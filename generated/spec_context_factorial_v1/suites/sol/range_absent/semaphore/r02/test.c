#include <zephyr/kernel.h>
#include <zephyr/irq_offload.h>
#include <zephyr/ztest.h>

static struct k_sem sem;

static void give_from_isr(const void *unused)
{
	ARG_UNUSED(unused);
	k_sem_give(&sem);
}

ZTEST(sem_irq, test_multiple_isr_gives)
{
	zassert_ok(k_sem_init(&sem, 0, 3));
	zassert_equal(k_sem_count_get(&sem), 0);

	for (unsigned int expected = 1; expected <= 3; expected++) {
		irq_offload(give_from_isr, NULL);
		zassert_equal(k_sem_count_get(&sem), expected,
			      "semaphore count after ISR give %u", expected);
	}
}

ZTEST_SUITE(sem_irq, NULL, NULL, NULL, NULL, NULL);
