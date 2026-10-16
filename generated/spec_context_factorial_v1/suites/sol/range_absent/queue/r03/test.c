#include <zephyr/kernel.h>
#include <zephyr/irq_offload.h>
#include <zephyr/ztest.h>

struct queue_item {
	void *link; /* First word is reserved for k_queue linkage. */
	int value;
};

struct offload_context {
	struct k_queue *queue;
	struct queue_item *first;
	struct queue_item *second;
	volatile unsigned int appended;
	volatile bool ran_in_isr;
};

static void append_from_isr(const void *parameter)
{
	struct offload_context *ctx = (struct offload_context *)parameter;

	ctx->ran_in_isr = k_is_in_isr();
	k_queue_append(ctx->queue, ctx->first);
	ctx->appended++;
	k_queue_append(ctx->queue, ctx->second);
	ctx->appended++;
}

ZTEST(queue_isr, test_append_order_and_empty)
{
	struct k_queue queue;
	struct queue_item first = { .value = 1 };
	struct queue_item second = { .value = 2 };
	struct offload_context ctx = {
		.queue = &queue,
		.first = &first,
		.second = &second,
	};

	k_queue_init(&queue);
	irq_offload(append_from_isr, &ctx);

	zassert_true(ctx.ran_in_isr, "append callback did not run in ISR context");
	zassert_equal(ctx.appended, 2U, "both ISR appends must execute");
	zassert_true(k_queue_get(&queue, K_NO_WAIT) == &first,
		     "first item was not retrieved first");
	zassert_true(k_queue_get(&queue, K_NO_WAIT) == &second,
		     "second item was not retrieved second");
	zassert_is_null(k_queue_get(&queue, K_NO_WAIT), "queue is not empty");
}

ZTEST_SUITE(queue_isr, NULL, NULL, NULL, NULL, NULL);
