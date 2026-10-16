#include <zephyr/kernel.h>
#include <zephyr/irq_offload.h>
#include <zephyr/ztest.h>

static struct k_sem test_sem;

static void give_sem_from_isr(const void *unused)
{
	ARG_UNUSED(unused);
	k_sem_give(&test_sem);
}

ZTEST(irq_offload_sem, test_count_increments_for_each_isr_give)
{
	k_sem_init(&test_sem, 0, 3);
	zassert_equal(k_sem_count_get(&test_sem), 0U,
		      "semaphore should start at zero");

	irq_offload(give_sem_from_isr, NULL);
	zassert_equal(k_sem_count_get(&test_sem), 1U,
		      "first ISR give should increment count to one");

	irq_offload(give_sem_from_isr, NULL);
	zassert_equal(k_sem_count_get(&test_sem), 2U,
		      "second ISR give should increment count to two");
}

ZTEST_SUITE(irq_offload_sem, NULL, NULL, NULL, NULL, NULL);
