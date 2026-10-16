#include <zephyr/kernel.h>
#include <zephyr/irq_offload.h>
#include <zephyr/ztest.h>
#include <stdbool.h>

struct lifo_item {
	void *link; /* Pointer-sized first word reserved for kernel linkage. */
};

static struct k_lifo lifo;
static struct lifo_item items[2];
static bool ran_in_isr;

static void producer_isr(const void *arg)
{
	ARG_UNUSED(arg);

	ran_in_isr = k_is_in_isr();
	k_lifo_put(&lifo, &items[0]);
	k_lifo_put(&lifo, &items[1]);
}

ZTEST(lifo_isr, test_isr_to_thread)
{
	void *first;
	void *second;

	k_lifo_init(&lifo);
	ran_in_isr = false;

	/* irq_offload completes the handler before returning to this thread. */
	irq_offload(producer_isr, NULL);

	zassert_true(ran_in_isr, "Producer did not execute in interrupt context");

	first = k_lifo_get(&lifo, K_NO_WAIT);
	second = k_lifo_get(&lifo, K_NO_WAIT);

	zassert_true(first == &items[1], "First get must return the last item put");
	zassert_true(second == &items[0], "Second get must return the first item put");
	zassert_is_null(k_lifo_get(&lifo, K_NO_WAIT), "LIFO must be empty");
}

ZTEST_SUITE(lifo_isr, NULL, NULL, NULL, NULL, NULL);
