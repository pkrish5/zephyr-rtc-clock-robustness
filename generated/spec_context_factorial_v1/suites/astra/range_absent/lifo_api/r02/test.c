#include <zephyr/kernel.h>
#include <zephyr/irq_offload.h>
#include <zephyr/ztest.h>
#include <stdbool.h>

struct lifo_item {
	void *link;
	int value;
};

static struct k_lifo lifo;
static struct lifo_item first = { .value = 1 };
static struct lifo_item second = { .value = 2 };
static volatile bool isr_seen;

static void lifo_isr(const void *arg)
{
	(void)arg;
	isr_seen = k_is_in_isr();
	k_lifo_put(&lifo, &first);
	k_lifo_put(&lifo, &second);
}

ZTEST(lifo_isr_transfer, test_reverse_order)
{
	k_lifo_init(&lifo);
	isr_seen = false;

	irq_offload(lifo_isr, NULL);

	zassert_true(isr_seen, "Producer must execute in interrupt context");
	zassert_equal_ptr(k_lifo_get(&lifo, K_NO_WAIT), &second,
			  "Last inserted item must be retrieved first");
	zassert_equal_ptr(k_lifo_get(&lifo, K_NO_WAIT), &first,
			  "First inserted item must be retrieved second");
	zassert_is_null(k_lifo_get(&lifo, K_NO_WAIT),
			"LIFO must be empty after both items are retrieved");
}

ZTEST_SUITE(lifo_isr_transfer, NULL, NULL, NULL, NULL, NULL);
