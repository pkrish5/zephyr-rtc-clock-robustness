#include <stdbool.h>
#include <zephyr/kernel.h>
#include <zephyr/irq_offload.h>
#include <zephyr/ztest.h>

struct fifo_item {
	void *fifo_reserved;
	int value;
};

struct test_context {
	struct k_fifo *fifo;
	struct fifo_item *first;
	struct fifo_item *second;
	volatile bool ran_in_isr;
};

static void put_from_isr(const void *arg)
{
	struct test_context *ctx = (struct test_context *)arg;

	ctx->ran_in_isr = k_is_in_isr();
	k_fifo_put(ctx->fifo, ctx->first);
	k_fifo_put(ctx->fifo, ctx->second);
}

ZTEST(fifo_irq, test_isr_to_thread_order)
{
	struct k_fifo fifo;
	struct fifo_item first = { .value = 1 };
	struct fifo_item second = { .value = 2 };
	struct test_context ctx = {
		.fifo = &fifo,
		.first = &first,
		.second = &second,
	};

	k_fifo_init(&fifo);
	irq_offload(put_from_isr, &ctx);

	zassert_true(ctx.ran_in_isr, "producer did not run in ISR context");
	zassert_true(k_fifo_get(&fifo, K_NO_WAIT) == &first,
		     "first FIFO item was out of order");
	zassert_true(k_fifo_get(&fifo, K_NO_WAIT) == &second,
		     "second FIFO item was out of order");
	zassert_is_null(k_fifo_get(&fifo, K_NO_WAIT), "FIFO is not empty");
}

ZTEST_SUITE(fifo_irq, NULL, NULL, NULL, NULL, NULL);
