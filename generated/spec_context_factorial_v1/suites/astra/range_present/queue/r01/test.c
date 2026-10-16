#include <zephyr/kernel.h>
#include <zephyr/irq_offload.h>
#include <zephyr/ztest.h>
#include <stdbool.h>

struct queue_item {
	void *link; /* First word reserved for kernel linkage. */
	int value;
};

struct transfer_context {
	struct k_queue queue;
	struct queue_item first;
	struct queue_item second;
	volatile bool in_isr;
	volatile bool appended;
};

static void append_from_isr(const void *arg)
{
	struct transfer_context *ctx = (struct transfer_context *)arg;

	ctx->in_isr = k_is_in_isr();
	k_queue_append(&ctx->queue, &ctx->first);
	k_queue_append(&ctx->queue, &ctx->second);
	ctx->appended = true;
}

ZTEST(queue_isr_transfer, test_fifo_delivery)
{
	struct transfer_context ctx = {
		.first = { .value = 1 },
		.second = { .value = 2 },
	};

	k_queue_init(&ctx.queue);
	irq_offload(append_from_isr, &ctx);

	zassert_true(ctx.in_isr, "Callback did not execute in ISR context");
	zassert_true(ctx.appended, "ISR append path did not complete");
	zassert_equal_ptr(k_queue_get(&ctx.queue, K_NO_WAIT), &ctx.first,
			 "First item out of order");
	zassert_equal_ptr(k_queue_get(&ctx.queue, K_NO_WAIT), &ctx.second,
			 "Second item out of order");
	zassert_is_null(k_queue_get(&ctx.queue, K_NO_WAIT),
			"Queue still contains an item");

	/* Functional test: HSI accuracy alone supplies no delivery-latency bound. */
}

ZTEST_SUITE(queue_isr_transfer, NULL, NULL, NULL, NULL, NULL);
