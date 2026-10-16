#include <zephyr/kernel.h>
#include <zephyr/irq_offload.h>
#include <zephyr/ztest.h>
#include <stdbool.h>

struct fifo_item {
	void *fifo_reserved; /* Pointer-sized first word for kernel linkage. */
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
		.items = {{.value = 1}, {.value = 2}},
	};

	k_fifo_init(&ctx.fifo);
	zassert_false(k_is_in_isr(), "Consumer must run in thread context");

	/* irq_offload completes the ISR callback before returning. */
	irq_offload(enqueue_from_isr, &ctx);
	zassert_true(ctx.ran_in_isr, "Producer did not run in ISR context");

	void *first = k_fifo_get(&ctx.fifo, K_NO_WAIT);
	void *second = k_fifo_get(&ctx.fifo, K_NO_WAIT);

	zassert_equal_ptr(first, &ctx.items[0], "Wrong first item");
	zassert_equal_ptr(second, &ctx.items[1], "Wrong second item");
	zassert_is_null(k_fifo_get(&ctx.fifo, K_NO_WAIT),
			"FIFO must be empty after both gets");

	/* HSI accuracy alone supplies no delivery-latency bound to assert. */
}

ZTEST_SUITE(fifo_isr_transfer, NULL, NULL, NULL, NULL, NULL);
