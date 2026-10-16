#include <zephyr/kernel.h>
#include <zephyr/irq_offload.h>
#include <zephyr/ztest.h>

struct fifo_item {
	void *fifo_reserved;
	int value;
};

static struct k_fifo test_fifo;
static struct fifo_item first_item = { .value = 1 };
static struct fifo_item second_item = { .value = 2 };
static volatile bool ran_in_isr;

static void put_from_isr(const void *arg)
{
	struct k_fifo *fifo = (struct k_fifo *)arg;

	ran_in_isr = k_is_in_isr();
	k_fifo_put(fifo, &first_item);
	k_fifo_put(fifo, &second_item);
}

ZTEST(fifo_isr_transfer, test_two_items_in_order)
{
	void *first;
	void *second;

	k_fifo_init(&test_fifo);
	ran_in_isr = false;
	irq_offload(put_from_isr, &test_fifo);

	first = k_fifo_get(&test_fifo, K_NO_WAIT);
	second = k_fifo_get(&test_fifo, K_NO_WAIT);

	zassert_true(ran_in_isr, "offload did not run in ISR context");
	zassert_true(first == &first_item, "first FIFO item was incorrect");
	zassert_true(second == &second_item, "second FIFO item was incorrect");
	zassert_is_null(k_fifo_get(&test_fifo, K_NO_WAIT), "FIFO was not empty");
}

ZTEST_SUITE(fifo_isr_transfer, NULL, NULL, NULL, NULL, NULL);