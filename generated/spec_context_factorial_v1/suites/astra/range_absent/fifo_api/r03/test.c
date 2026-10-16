#include <zephyr/kernel.h>
#include <zephyr/irq_offload.h>
#include <zephyr/ztest.h>
#include <stdbool.h>

struct fifo_item {
	void *fifo_reserved;
	int value;
};

struct test_context {
	struct k_fifo fifo;
	struct fifo_item items[2];
	bool ran_in_isr;
};

static void enqueue_from_isr(const void *arg)
{
	struct test_context *ctx = (struct test_context *)arg;

	ctx->ran_in_isr = k_is_in_isr();
	k_fifo_put(&ctx->fifo, &ctx->items[0]);
	k_fifo_put(&ctx->fifo, &ctx->items[1]);
}

ZTEST(fifo_isr, test_isr_to_thread_transfer)
{
	struct test_context ctx = {
		.items = {{.value = 11}, {.value = 22}},
	};

	k_fifo_init(&ctx.fifo);
	irq_offload(enqueue_from_isr, &ctx);

	zassert_true(ctx.ran_in_isr, "Producer did not run in ISR context");
	zassert_equal_ptr(k_fifo_get(&ctx.fifo, K_NO_WAIT), &ctx.items[0],
			 "First item is incorrect");
	zassert_equal_ptr(k_fifo_get(&ctx.fifo, K_NO_WAIT), &ctx.items[1],
			 "Second item is incorrect");
	zassert_true(k_fifo_is_empty(&ctx.fifo), "FIFO is not empty");
	zassert_is_null(k_fifo_get(&ctx.fifo, K_NO_WAIT),
			"Empty FIFO returned an item");
}

ZTEST_SUITE(fifo_isr, NULL, NULL, NULL, NULL, NULL);
