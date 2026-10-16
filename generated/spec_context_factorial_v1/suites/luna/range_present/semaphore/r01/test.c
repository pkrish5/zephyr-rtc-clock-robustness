#include <zephyr/kernel.h>
#include <zephyr/irq_offload.h>
#include <zephyr/ztest.h>

static struct k_sem test_sem;

static void give_sem_from_isr(const void *arg)
{
	k_sem_give((struct k_sem *)arg);
}

ZTEST(semaphore_irq, test_isr_gives_increment_count)
{
	k_sem_init(&test_sem, 0, 3);
	zassert_equal(k_sem_count_get(&test_sem), 0, "initial count must be zero");

	irq_offload(give_sem_from_isr, &test_sem);
	zassert_equal(k_sem_count_get(&test_sem), 1, "count after first ISR give");

	irq_offload(give_sem_from_isr, &test_sem);
	zassert_equal(k_sem_count_get(&test_sem), 2, "count after second ISR give");
}

ZTEST_SUITE(semaphore_irq, NULL, NULL, NULL, NULL, NULL);
