#include <zephyr/kernel.h>
#include <zephyr/irq_offload.h>
#include <zephyr/ztest.h>

struct fifo_item {
	void *fifo_reserved; /* First word is reserved for FIFO linkage. */
	int value;
};

struct transfer {
	struct k_fifo *fifo;
	struct fifo_item *first;
	struct fifo_item *second;
	bool ran_in_isr;
};

static void enqueue_from_isr(const void *parameter)
{
	struct transfer *transfer = (struct transfer *)parameter;

	transfer->ran_in_isr = k_is_in_isr();
	k_fifo_put(transfer->fifo, transfer->first);
	k_fifo_put(transfer->fifo, transfer->second);
}

ZTEST(fifo_isr_transfer, test_two_items_in_order)
{
	struct k_fifo fifo;
	struct fifo_item first = { .value = 1 };
	struct fifo_item second = { .value = 2 };
	struct transfer transfer = {
		.fifo = &fifo,
		.first = &first,
		.second = &second,
	};
	void *received_first;
	void *received_second;

	k_fifo_init(&fifo);
	irq_offload(enqueue_from_isr, &transfer);

	received_first = k_fifo_get(&fifo, K_NO_WAIT);
	received_second = k_fifo_get(&fifo, K_NO_WAIT);

	zassert_true(transfer.ran_in_isr, "callback did not run in ISR context");
	zassert_true(received_first == &first, "first FIFO item is out of order");
	zassert_true(received_second == &second, "second FIFO item is out of order");
	zassert_true(k_fifo_get(&fifo, K_NO_WAIT) == NULL, "FIFO is not empty");
}

ZTEST_SUITE(fifo_isr_transfer, NULL, NULL, NULL, NULL, NULL);
