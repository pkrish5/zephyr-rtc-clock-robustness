#include <zephyr/kernel.h>
#include <zephyr/irq_offload.h>
#include <zephyr/ztest.h>
#include <stdbool.h>

struct fifo_item {
	void *fifo_reserved;
	int value;
};

static struct k_fifo fifo;
static struct fifo_item first = { .value = 1 };
static struct fifo_item second = { .value = 2 };
static volatile bool ran_in_isr;

static void enqueue_isr(const void *arg)
{
	(void)arg;
	ran_in_isr = k_is_in_isr();
	k_fifo_put(&fifo, &first);
	k_fifo_put(&fifo, &second);
}

ZTEST(fifo_isr_transfer, test_isr_to_thread)
{
	k_fifo_init(&fifo);
	ran_in_isr = false;

	irq_offload(enqueue_isr, NULL);

	zassert_true(ran_in_isr, "Callback must execute in interrupt context");
	zassert_equal_ptr(k_fifo_get(&fifo, K_NO_WAIT), &first,
			  "First get must return the first inserted item");
	zassert_equal_ptr(k_fifo_get(&fifo, K_NO_WAIT), &second,
			  "Second get must return the second inserted item");
	zassert_true(k_fifo_is_empty(&fifo), "FIFO must be empty after both gets");
	zassert_is_null(k_fifo_get(&fifo, K_NO_WAIT),
			"An empty FIFO must return NULL without waiting");
}

ZTEST_SUITE(fifo_isr_transfer, NULL, NULL, NULL, NULL, NULL);
