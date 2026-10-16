#include <zephyr/kernel.h>
#include <zephyr/irq_offload.h>
#include <zephyr/ztest.h>
#include <stdbool.h>

struct item {
	void *reserved; /* Pointer-sized first word for kernel linkage. */
	int value;
};

static struct k_lifo lifo;
static struct item first = { .value = 1 };
static struct item second = { .value = 2 };
static bool observed_isr;

static void put_from_isr(const void *arg)
{
	ARG_UNUSED(arg);
	observed_isr = k_is_in_isr();
	k_lifo_put(&lifo, &first);
	k_lifo_put(&lifo, &second);
}

ZTEST(lifo_isr, test_interrupt_to_thread)
{
	k_lifo_init(&lifo);
	observed_isr = false;

	/* Offload completes before returning; no timing bound is assumed. */
	irq_offload(put_from_isr, NULL);

	zassert_true(observed_isr, "Producer did not run in interrupt context");
	zassert_false(k_is_in_isr(), "Consumer must run in thread context");
	zassert_equal_ptr(k_lifo_get(&lifo, K_NO_WAIT), &second,
			  "Expected last inserted item first");
	zassert_equal_ptr(k_lifo_get(&lifo, K_NO_WAIT), &first,
			  "Expected first inserted item second");
	zassert_is_null(k_lifo_get(&lifo, K_NO_WAIT),
			"LIFO must be empty after both gets");
}

ZTEST_SUITE(lifo_isr, NULL, NULL, NULL, NULL, NULL);
