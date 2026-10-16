#include <stdbool.h>
#include <stdint.h>

#include <zephyr/kernel.h>
#include <zephyr/irq_offload.h>
#include <zephyr/ztest.h>

struct fifo_item {
	void *fifo_reserved; /* Required kernel linkage word. */
	uint32_t value;
};

struct offload_context {
	struct k_fifo *fifo;
	struct fifo_item *first;
	struct fifo_item *second;
	volatile bool ran_in_isr;
};

static void enqueue_from_isr(const void *parameter)
{
	struct offload_context *ctx = (struct offload_context *)parameter;

	ctx->ran_in_isr = k_is_in_isr();
	k_fifo_put(ctx->fifo, ctx->first);
	k_fifo_put(ctx->fifo, ctx->second);
}

ZTEST(fifo_irq, test_isr_to_thread_order)
{
	struct k_fifo fifo;
	struct fifo_item first = { .value = 1 };
	struct fifo_item second = { .value = 2 };
	struct offload_context ctx = {
		.fifo = &fifo,
		.first = &first,
		.second = &second,
	};

	k_fifo_init(&fifo);
	irq_offload(enqueue_from_isr, &ctx);

	zassert_true(ctx.ran_in_isr, "offload did not run in ISR context");
	zassert_true(k_fifo_get(&fifo, K_NO_WAIT) == &first,
		     "first FIFO item is out of order");
	zassert_true(k_fifo_get(&fifo, K_NO_WAIT) == &second,
		     "second FIFO item is out of order");
	zassert_is_null(k_fifo_get(&fifo, K_NO_WAIT), "FIFO is not empty");
}

ZTEST_SUITE(fifo_irq, NULL, NULL, NULL, NULL, NULL);
