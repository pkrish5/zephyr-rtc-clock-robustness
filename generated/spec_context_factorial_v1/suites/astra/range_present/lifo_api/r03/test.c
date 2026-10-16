#include <zephyr/kernel.h>
#include <zephyr/irq_offload.h>
#include <zephyr/ztest.h>
#include <stdbool.h>

struct lifo_item {
	void *link; /* First word reserved for kernel linkage. */
	int value;
};

static struct k_lifo lifo;
static struct lifo_item first = { .value = 1 };
static struct lifo_item second = { .value = 2 };
static volatile bool ran_in_isr;

static void put_from_isr(const void *arg)
{
	ARG_UNUSED(arg);

	ran_in_isr = k_is_in_isr();
	k_lifo_put(&lifo, &first);
	k_lifo_put(&lifo, &second);
}

ZTEST(lifo_isr_transfer, test_reverse_order_and_empty)
{
	k_lifo_init(&lifo);
	ran_in_isr = false;

	/* irq_offload completes the ISR before returning to this thread. */
	irq_offload(put_from_isr, NULL);

	zassert_true(ran_in_isr, "Producer did not execute in ISR context");
	zassert_equal_ptr(k_lifo_get(&lifo, K_NO_WAIT), &second,
			  "Expected the last item inserted by the ISR");
	zassert_equal_ptr(k_lifo_get(&lifo, K_NO_WAIT), &first,
			  "Expected the first item inserted by the ISR");
	zassert_is_null(k_lifo_get(&lifo, K_NO_WAIT),
			"LIFO must be empty after both items are removed");
}

ZTEST_SUITE(lifo_isr_transfer, NULL, NULL, NULL, NULL, NULL);
