#include <zephyr/kernel.h>
#include <zephyr/irq_offload.h>
#include <zephyr/ztest.h>
#include <stdbool.h>

struct fifo_item {
	void *fifo_reserved;
	int value;
};

struct isr_context {
	struct k_fifo *fifo;
	struct fifo_item *first;
	struct fifo_item *second;
	bool observed_isr;
};

static void fifo_producer_isr(const void *arg)
{
	struct isr_context *ctx = (struct isr_context *)arg;

	ctx->observed_isr = k_is_in_isr();
	k_fifo_put(ctx->fifo, ctx->first);
	k_fifo_put(ctx->fifo, ctx->second);
}

ZTEST(fifo_isr_transfer, test_isr_put_thread_get)
{
	struct k_fifo fifo;
	struct fifo_item items[2] = {
		{ .value = 11 },
		{ .value = 22 },
	};
	struct isr_context ctx = {
		.fifo = &fifo,
		.first = &items[0],
		.second = &items[1],
		.observed_isr = false,
	};

	k_fifo_init(&fifo);
	zassert_false(k_is_in_isr(), "Consumer must run in thread context");

	/* irq_offload completes the handler before returning. */
	irq_offload(fifo_producer_isr, &ctx);
	zassert_true(ctx.observed_isr, "Producer did not run in ISR context");

	void *first = k_fifo_get(&fifo, K_NO_WAIT);
	void *second = k_fifo_get(&fifo, K_NO_WAIT);

	zassert_equal_ptr(first, &items[0], "First item mismatch");
	zassert_equal_ptr(second, &items[1], "Second item mismatch");
	zassert_true(k_fifo_is_empty(&fifo), "FIFO must be empty");
	zassert_is_null(k_fifo_get(&fifo, K_NO_WAIT), "Unexpected extra item");
}

ZTEST_SUITE(fifo_isr_transfer, NULL, NULL, NULL, NULL, NULL);
