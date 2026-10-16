#include <stdbool.h>
#include <zephyr/kernel.h>
#include <zephyr/irq_offload.h>
#include <zephyr/ztest.h>

struct fifo_item {
	void *fifo_reserved;
	int value;
};

K_FIFO_DEFINE(test_fifo);

static struct fifo_item first_item = { .value = 1 };
static struct fifo_item second_item = { .value = 2 };
static volatile bool ran_in_isr;

static void put_from_isr(const void *arg)
{
	(void)arg;
	ran_in_isr = k_is_in_isr();
	k_fifo_put(&test_fifo, &first_item);
	k_fifo_put(&test_fifo, &second_item);
}

ZTEST(fifo_isr, test_order_and_empty_state)
{
	ran_in_isr = false;
	irq_offload(put_from_isr, NULL);

	void *first = k_fifo_get(&test_fifo, K_NO_WAIT);
	void *second = k_fifo_get(&test_fifo, K_NO_WAIT);

	zassert_true(ran_in_isr, "producer did not run in ISR context");
	zassert_true(first == &first_item, "first FIFO item is incorrect");
	zassert_true(second == &second_item, "second FIFO item is incorrect");
	zassert_is_null(k_fifo_get(&test_fifo, K_NO_WAIT), "FIFO is not empty");
}

ZTEST_SUITE(fifo_isr, NULL, NULL, NULL, NULL, NULL);
