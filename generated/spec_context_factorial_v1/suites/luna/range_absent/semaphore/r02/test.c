#include <zephyr/kernel.h>
#include <zephyr/irq_offload.h>
#include <zephyr/ztest.h>

ZTEST(semaphore_irq_suite, test_semaphore_give_from_irq)
{
    struct k_sem sem;

    k_sem_init(&sem, 0, 3);
    zassert_equal(k_sem_count_get(&sem), 0U, "initial count should be zero");

    irq_offload((void (*)(const void *))k_sem_give, &sem);
    zassert_equal(k_sem_count_get(&sem), 1U, "count after first ISR give");

    irq_offload((void (*)(const void *))k_sem_give, &sem);
    zassert_equal(k_sem_count_get(&sem), 2U, "count after second ISR give");
}

ZTEST_SUITE(semaphore_irq_suite, NULL, NULL, NULL, NULL, NULL);
