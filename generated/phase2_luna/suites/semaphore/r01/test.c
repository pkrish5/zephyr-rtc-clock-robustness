#include <zephyr/kernel.h>
#include <zephyr/irq_offload.h>
#include <zephyr/ztest.h>

static struct k_sem sem;

static void give_sem_from_isr(const void *data)
{
	struct k_sem *target = (struct k_sem *)data;

	k_sem_give(target);
}

ZTEST(semaphore_irq_offload, test_isr_gives_increment_count)
{
	k_sem_init(&sem, 0, 3);
	zassert_equal(k_sem_count_get(&sem), 0U, "initial semaphore count");

	irq_offload(give_sem_from_isr, &sem);
	zassert_equal(k_sem_count_get(&sem), 1U, "count after first ISR give");

	irq_offload(give_sem_from_isr, &sem);
	zassert_equal(k_sem_count_get(&sem), 2U, "count after second ISR give");
}

ZTEST_SUITE(semaphore_irq_offload, NULL, NULL, NULL, NULL, NULL);
