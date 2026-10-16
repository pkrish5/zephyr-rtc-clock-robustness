#include <zephyr/kernel.h>
#include <zephyr/irq_offload.h>
#include <zephyr/ztest.h>
#include <stdbool.h>

struct queue_item {
	void *link; /* First word reserved for kernel linkage. */
	int value;
};

struct test_context {
	struct k_queue queue;
	struct queue_item items[2];
	volatile bool in_isr;
	volatile bool appended;
};

static void append_from_isr(const void *arg)
{
	struct test_context *ctx = (struct test_context *)arg;

	ctx->in_isr = k_is_in_isr();
	k_queue_append(&ctx->queue, &ctx->items[0]);
	k_queue_append(&ctx->queue, &ctx->items[1]);
	ctx->appended = true;
}

ZTEST(queue_isr, test_isr_to_thread_fifo)
{
	struct test_context ctx = {
		.items = {{.value = 1}, {.value = 2}},
	};

	k_queue_init(&ctx.queue);
	irq_offload(append_from_isr, &ctx);

	zassert_true(ctx.in_isr, "Callback must execute in ISR context");
	zassert_true(ctx.appended, "ISR must complete both appends");
	zassert_equal_ptr(k_queue_get(&ctx.queue, K_NO_WAIT),
			 &ctx.items[0], "First item must be retrieved first");
	zassert_equal_ptr(k_queue_get(&ctx.queue, K_NO_WAIT),
			 &ctx.items[1], "Second item must be retrieved second");
	zassert_is_null(k_queue_get(&ctx.queue, K_NO_WAIT),
			"No item may remain in the queue");
	zassert_true(k_queue_is_empty(&ctx.queue), "Queue must be empty");
}

ZTEST_SUITE(queue_isr, NULL, NULL, NULL, NULL, NULL);
