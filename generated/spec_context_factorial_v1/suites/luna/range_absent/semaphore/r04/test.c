#include <zephyr/kernel.h>
#include <zephyr/irq_offload.h>
#include <zephyr/ztest.h>

ZTEST_SUITE(sem_irq_give, NULL, NULL, NULL, NULL, NULL);

static struct k_sem sem;

static void give_sem_from_isr(const void *arg)
{
	struct k_sem *target = (struct k_sem *)arg;

	k_sem_give(target);
}

ZTEST(sem_irq_give, test_count_tracks_isr_gives)
{
	k_sem_init(&sem, 0, 3);
	zassert_equal(k_sem_count_get(&sem), 0U, "initial count must be zero");

	irq_offload(give_sem_from_isr, &sem);
	zassert_equal(k_sem_count_get(&sem), 1U, "count after first ISR give");

	irq_offload(give_sem_from_isr, &sem);
	zassert_equal(k_sem_count_get(&sem), 2U, "count after second ISR give");
}