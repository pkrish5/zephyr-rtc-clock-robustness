#include <stdbool.h>
#include <zephyr/kernel.h>
#include <zephyr/irq_offload.h>
#include <zephyr/ztest.h>

struct fifo_item {
	void *fifo_reserved;
	int value;
};

static struct k_fifo test_fifo;
static struct fifo_item items[2] = {
	{ .value = 1 },
	{ .value = 2 },
};
static volatile bool handler_ran;
static volatile bool handler_was_in_isr;

static void put_from_isr(const void *unused)
{
	(void)unused;
	handler_ran = true;
	handler_was_in_isr = k_is_in_isr();
	k_fifo_put(&test_fifo, &items[0]);
	k_fifo_put(&test_fifo, &items[1]);
}

ZTEST(fifo_isr, test_transfer_order)
{
	void *first;
	void *second;

	k_fifo_init(&test_fifo);
	handler_ran = false;
	handler_was_in_isr = false;

	irq_offload(put_from_isr, NULL);

	first = k_fifo_get(&test_fifo, K_NO_WAIT);
	second = k_fifo_get(&test_fifo, K_NO_WAIT);

	zassert_true(handler_ran, "ISR handler did not run");
	zassert_true(handler_was_in_isr, "handler did not run in ISR context");
	zassert_true(first == &items[0], "first FIFO item is out of order");
	zassert_true(second == &items[1], "second FIFO item is out of order");
	zassert_is_null(k_fifo_get(&test_fifo, K_NO_WAIT), "FIFO is not empty");
}

ZTEST_SUITE(fifo_isr, NULL, NULL, NULL, NULL, NULL);
