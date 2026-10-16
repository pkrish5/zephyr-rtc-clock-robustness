#include <zephyr/kernel.h>
#include <zephyr/irq_offload.h>
#include <zephyr/ztest.h>
#include <stdbool.h>

struct queue_item {
	void *link; /* Pointer-sized first word reserved for kernel linkage. */
	int value;
};

struct transfer_context {
	struct k_queue queue;
	struct queue_item items[2];
	volatile bool in_isr;
	volatile bool appended;
};

static void append_from_isr(const void *arg)
{
	struct transfer_context *ctx = (struct transfer_context *)arg;

	ctx->in_isr = k_is_in_isr();
	k_queue_append(&ctx->queue, &ctx->items[0]);
	k_queue_append(&ctx->queue, &ctx->items[1]);
	ctx->appended = true;
}

ZTEST(queue_isr_transfer, test_fifo_transfer)
{
	struct transfer_context ctx = {
		.items = {{.value = 11}, {.value = 22}},
	};
	void *item;

	k_queue_init(&ctx.queue);
	irq_offload(append_from_isr, &ctx);

	zassert_true(ctx.in_isr, "Callback did not execute in ISR context");
	zassert_true(ctx.appended, "ISR append path did not complete");

	item = k_queue_get(&ctx.queue, K_NO_WAIT);
	zassert_true(item == &ctx.items[0], "First item out of order");
	item = k_queue_get(&ctx.queue, K_NO_WAIT);
	zassert_true(item == &ctx.items[1], "Second item out of order");
	zassert_is_null(k_queue_get(&ctx.queue, K_NO_WAIT),
			"Queue contains an unexpected item");
	zassert_true(k_queue_is_empty(&ctx.queue), "Queue is not empty");
}

ZTEST_SUITE(queue_isr_transfer, NULL, NULL, NULL, NULL, NULL);
