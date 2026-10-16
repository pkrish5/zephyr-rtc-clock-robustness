#include <stdbool.h>
#include <zephyr/kernel.h>
#include <zephyr/irq_offload.h>
#include <zephyr/ztest.h>

struct lifo_item {
	void *link;
	int value;
};

static struct k_lifo lifo;
static struct lifo_item items[2] = {
	{ .value = 1 },
	{ .value = 2 },
};
static volatile bool isr_seen;

static void put_from_isr(const void *unused)
{
	(void)unused;
	isr_seen = k_is_in_isr();
	k_lifo_put(&lifo, &items[0]);
	k_lifo_put(&lifo, &items[1]);
}

ZTEST(lifo_isr, test_reverse_order_from_isr)
{
	void *first;
	void *second;

	k_lifo_init(&lifo);
	isr_seen = false;
	irq_offload(put_from_isr, NULL);

	zassert_true(isr_seen, "offload callback did not run in ISR context");
	first = k_lifo_get(&lifo, K_NO_WAIT);
	second = k_lifo_get(&lifo, K_NO_WAIT);
	zassert_true(first == &items[1], "first item was not the last inserted");
	zassert_true(second == &items[0], "second item was not the first inserted");
	zassert_is_null(k_lifo_get(&lifo, K_NO_WAIT), "LIFO is not empty");
}

ZTEST_SUITE(lifo_isr, NULL, NULL, NULL, NULL, NULL);
