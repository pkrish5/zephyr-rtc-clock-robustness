#include <zephyr/kernel.h>
#include <zephyr/irq_offload.h>
#include <zephyr/ztest.h>
#include <stdbool.h>

struct fifo_item {
	void *reserved;
	int value;
};

struct test_context {
	struct k_fifo fifo;
	struct fifo_item first;
	struct fifo_item second;
	bool ran_in_isr;
};

static void enqueue_from_isr(const void *arg)
{
	struct test_context *ctx = (struct test_context *)arg;

	ctx->ran_in_isr = k_is_in_isr();
	k_fifo_put(&ctx->fifo, &ctx->first);
	k_fifo_put(&ctx->fifo, &ctx->second);
}

ZTEST(fifo_isr, test_isr_to_thread_fifo_order)
{
	struct test_context ctx = {
		.first = { .value = 11 },
		.second = { .value = 22 },
	};

	k_fifo_init(&ctx.fifo);
	irq_offload(enqueue_from_isr, &ctx);

	zassert_true(ctx.ran_in_isr, "Producer did not run in ISR context");
	zassert_false(k_is_in_isr(), "Consumer must run in thread context");
	zassert_equal_ptr(k_fifo_get(&ctx.fifo, K_NO_WAIT), &ctx.first,
			  "First item out of order");
	zassert_equal_ptr(k_fifo_get(&ctx.fifo, K_NO_WAIT), &ctx.second,
			  "Second item out of order");
	zassert_is_null(k_fifo_get(&ctx.fifo, K_NO_WAIT),
			"FIFO must be empty after both gets");
}

ZTEST_SUITE(fifo_isr, NULL, NULL, NULL, NULL, NULL);
