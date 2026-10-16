#include <stdbool.h>
#include <zephyr/kernel.h>
#include <zephyr/irq_offload.h>
#include <zephyr/ztest.h>

struct queue_item {
	void *link; /* Reserved for kernel linkage. */
};

struct offload_context {
	struct k_queue *queue;
	struct queue_item *first;
	struct queue_item *second;
	volatile bool executed;
};

static void append_from_isr(const void *arg)
{
	struct offload_context *ctx = (struct offload_context *)arg;

	k_queue_append(ctx->queue, ctx->first);
	k_queue_append(ctx->queue, ctx->second);
	ctx->executed = true;
}

ZTEST(queue_isr, test_isr_to_thread_order)
{
	struct k_queue queue;
	struct queue_item first = { 0 };
	struct queue_item second = { 0 };
	struct offload_context ctx = {
		.queue = &queue,
		.first = &first,
		.second = &second,
	};

	k_queue_init(&queue);
	irq_offload(append_from_isr, &ctx);

	zassert_true(ctx.executed, "ISR append path did not execute");
	zassert_true(k_queue_get(&queue, K_NO_WAIT) == &first,
		     "first item was not retrieved first");
	zassert_true(k_queue_get(&queue, K_NO_WAIT) == &second,
		     "second item was not retrieved second");
	zassert_is_null(k_queue_get(&queue, K_NO_WAIT),
			"queue was not empty afterward");
}

ZTEST_SUITE(queue_isr, NULL, NULL, NULL, NULL, NULL);
