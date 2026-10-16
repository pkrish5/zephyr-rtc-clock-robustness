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
	struct queue_item items[2];
	bool append_completed;
	bool in_isr;
};

static void append_from_isr(const void *arg)
{
	struct transfer_context *ctx = (struct transfer_context *)arg;

	ctx->in_isr = k_is_in_isr();
	k_queue_append(&ctx->queue, &ctx->items[0]);
	k_queue_append(&ctx->queue, &ctx->items[1]);
	ctx->append_completed = true;
}

ZTEST(queue_isr_transfer, test_fifo_transfer)
{
	struct transfer_context ctx = {
		.items = {{ .value = 1 }, { .value = 2 }},
	};

	k_queue_init(&ctx.queue);
	irq_offload(append_from_isr, &ctx);

	zassert_true(ctx.in_isr, "Callback must run in ISR context");
	zassert_true(ctx.append_completed, "ISR append path did not complete");
	zassert_equal_ptr(k_queue_get(&ctx.queue, K_NO_WAIT), &ctx.items[0],
			 "First item out of order");
	zassert_equal_ptr(k_queue_get(&ctx.queue, K_NO_WAIT), &ctx.items[1],
			 "Second item out of order");
	zassert_is_null(k_queue_get(&ctx.queue, K_NO_WAIT),
			"Unexpected item remains");
	zassert_true(k_queue_is_empty(&ctx.queue), "Queue must be empty");
}

ZTEST_SUITE(queue_isr_transfer, NULL, NULL, NULL, NULL, NULL);
