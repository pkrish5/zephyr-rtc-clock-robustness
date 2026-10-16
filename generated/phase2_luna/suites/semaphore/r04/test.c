#include <zephyr/kernel.h>
#include <zephyr/irq_offload.h>
#include <zephyr/ztest.h>

static struct k_sem test_sem;

static void give_sem_from_isr(const void *unused)
{
	ARG_UNUSED(unused);
	k_sem_give(&test_sem);
}

ZTEST(semaphore_irq_offload, test_isr_gives_increment_count)
{
	k_sem_init(&test_sem, 0, 3);
	zassert_equal(k_sem_count_get(&test_sem), 0U, "initial count must be zero");

	irq_offload(give_sem_from_isr, NULL);
	zassert_equal(k_sem_count_get(&test_sem), 1U, "count after first ISR give");

	irq_offload(give_sem_from_isr, NULL);
	zassert_equal(k_sem_count_get(&test_sem), 2U, "count after second ISR give");
}

ZTEST_SUITE(semaphore_irq_offload, NULL, NULL, NULL, NULL, NULL);
