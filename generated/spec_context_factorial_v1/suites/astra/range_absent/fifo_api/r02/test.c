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
	struct fifo_item items[2];
	bool called;
	bool in_isr;
};

static void enqueue_isr(const void *arg)
{
	struct isr_context *ctx = (struct isr_context *)arg;

	ctx->called = true;
	ctx->in_isr = k_is_in_isr();
	k_fifo_put(ctx->fifo, &ctx->items[0]);
	k_fifo_put(ctx->fifo, &ctx->items[1]);
}

ZTEST(fifo_irq, test_isr_to_thread)
{
	struct k_fifo fifo;
	struct isr_context ctx = {
		.fifo = &fifo,
		.items = {{.value = 11}, {.value = 22}},
	};

	k_fifo_init(&fifo);
	irq_offload(enqueue_isr, &ctx);

	zassert_true(ctx.called, "Offloaded handler did not run");
	zassert_true(ctx.in_isr, "Handler did not run in ISR context");
	zassert_false(k_is_in_isr(), "Consumer must run in thread context");

	void *first = k_fifo_get(&fifo, K_NO_WAIT);
	void *second = k_fifo_get(&fifo, K_NO_WAIT);

	zassert_equal_ptr(first, &ctx.items[0], "Wrong first item");
	zassert_equal_ptr(second, &ctx.items[1], "Wrong second item");
	zassert_true(k_fifo_is_empty(&fifo), "FIFO must be empty");
	zassert_is_null(k_fifo_get(&fifo, K_NO_WAIT),
			"Empty FIFO returned an item");
}

ZTEST_SUITE(fifo_irq, NULL, NULL, NULL, NULL, NULL);
