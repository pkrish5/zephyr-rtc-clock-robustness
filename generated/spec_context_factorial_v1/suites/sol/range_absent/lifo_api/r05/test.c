#include <stdbool.h>
#include <zephyr/kernel.h>
#include <zephyr/irq_offload.h>
#include <zephyr/ztest.h>

struct lifo_item {
	void *lifo_reserved; /* Kernel linkage must be the first word. */
	int value;
};

static struct k_lifo lifo;
static struct lifo_item items[2];
static volatile bool ran_in_isr;

static void put_from_isr(const void *unused)
{
	ARG_UNUSED(unused);
	ran_in_isr = k_is_in_isr();
	k_lifo_put(&lifo, &items[0]);
	k_lifo_put(&lifo, &items[1]);
}

ZTEST(lifo_irq_offload, test_isr_to_thread_order)
{
	void *first;
	void *second;

	k_lifo_init(&lifo);
	items[0].value = 1;
	items[1].value = 2;
	ran_in_isr = false;

	irq_offload(put_from_isr, NULL);

	zassert_true(ran_in_isr, "offload handler did not run in ISR context");
	first = k_lifo_get(&lifo, K_NO_WAIT);
	second = k_lifo_get(&lifo, K_NO_WAIT);
	zassert_true(first == &items[1], "first get was not the last item put");
	zassert_true(second == &items[0], "second get was not the first item put");
	zassert_true(k_lifo_get(&lifo, K_NO_WAIT) == NULL, "LIFO is not empty");
}

ZTEST_SUITE(lifo_irq_offload, NULL, NULL, NULL, NULL, NULL);
