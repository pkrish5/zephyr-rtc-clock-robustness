#include <zephyr/kernel.h>
#include <zephyr/irq_offload.h>
#include <zephyr/ztest.h>
#include <stdbool.h>

struct fifo_item {
	void *fifo_reserved;
	int value;
};

struct transfer_context {
	struct k_fifo fifo;
	struct fifo_item items[2];
	bool ran_in_isr;
};

static void enqueue_from_isr(const void *arg)
{
	struct transfer_context *ctx = (struct transfer_context *)arg;

	ctx->ran_in_isr = k_is_in_isr();
	k_fifo_put(&ctx->fifo, &ctx->items[0]);
	k_fifo_put(&ctx->fifo, &ctx->items[1]);
}

ZTEST(fifo_isr_transfer, test_isr_to_thread_fifo_order)
{
	struct transfer_context ctx = {
		.items = {{ .value = 11 }, { .value = 22 }},
		.ran_in_isr = false,
	};

	k_fifo_init(&ctx.fifo);
	zassert_false(k_is_in_isr(), "Consumer must run in thread context");

	/* Offload completes before returning; no timing bound is assumed. */
	irq_offload(enqueue_from_isr, &ctx);

	zassert_true(ctx.ran_in_isr, "Producer did not execute in ISR context");
	zassert_true(k_fifo_get(&ctx.fifo, K_NO_WAIT) == &ctx.items[0],
		     "First get must return the first ISR item");
	zassert_true(k_fifo_get(&ctx.fifo, K_NO_WAIT) == &ctx.items[1],
		     "Second get must return the second ISR item");
	zassert_is_null(k_fifo_get(&ctx.fifo, K_NO_WAIT),
			"FIFO must be empty after both gets");
}

ZTEST_SUITE(fifo_isr_transfer, NULL, NULL, NULL, NULL, NULL);
