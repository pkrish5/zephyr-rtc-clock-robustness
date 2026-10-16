#include <stdbool.h>
#include <zephyr/kernel.h>
#include <zephyr/irq_offload.h>
#include <zephyr/ztest.h>

struct lifo_item {
	void *link; /* Reserved for kernel linkage. */
	int value;
};

K_LIFO_DEFINE(test_lifo);

static struct lifo_item first_item = { .value = 1 };
static struct lifo_item second_item = { .value = 2 };
static volatile bool isr_seen;

static void put_from_isr(const void *arg)
{
	ARG_UNUSED(arg);
	isr_seen = k_is_in_isr();
	k_lifo_put(&test_lifo, &first_item);
	k_lifo_put(&test_lifo, &second_item);
}

ZTEST(lifo_irq, test_isr_to_thread_order)
{
	void *first;
	void *second;

	irq_offload(put_from_isr, NULL);

	first = k_lifo_get(&test_lifo, K_NO_WAIT);
	second = k_lifo_get(&test_lifo, K_NO_WAIT);

	zassert_true(isr_seen, "offload callback did not run in ISR context");
	zassert_true(first == &second_item, "first get was not the last item put");
	zassert_true(second == &first_item, "second get was not the first item put");
	zassert_is_null(k_lifo_get(&test_lifo, K_NO_WAIT), "LIFO is not empty");
}

ZTEST_SUITE(lifo_irq, NULL, NULL, NULL, NULL, NULL);
