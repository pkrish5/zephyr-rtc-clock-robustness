#include <zephyr/kernel.h>
#include <zephyr/irq_offload.h>
#include <zephyr/ztest.h>

static struct k_sem test_sem;

static void give_sem_isr(const void *arg)
{
	struct k_sem *sem = (struct k_sem *)arg;

	k_sem_give(sem);
}

ZTEST(semaphore_irq_offload, test_isr_gives_increment_count)
{
	k_sem_init(&test_sem, 0, 3);

	zassert_equal(k_sem_count_get(&test_sem), 0U,
		      "semaphore should start at zero");

	irq_offload(give_sem_isr, &test_sem);
	zassert_equal(k_sem_count_get(&test_sem), 1U,
		      "first ISR give should increase count to one");

	irq_offload(give_sem_isr, &test_sem);
	zassert_equal(k_sem_count_get(&test_sem), 2U,
		      "second ISR give should increase count to two");
}

ZTEST_SUITE(semaphore_irq_offload, NULL, NULL, NULL, NULL, NULL);
