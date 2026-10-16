#include <stdbool.h>
#include <zephyr/kernel.h>
#include <zephyr/irq_offload.h>
#include <zephyr/ztest.h>

struct queue_item {
	void *link; /* First word reserved for k_queue linkage. */
	int id;
};

struct test_context {
	struct k_queue *queue;
	struct queue_item *first;
	struct queue_item *second;
	bool append_path_ran;
	bool ran_in_isr;
};

static void append_from_isr(const void *parameter)
{
	struct test_context *ctx = (struct test_context *)parameter;

	ctx->ran_in_isr = k_is_in_isr();
	k_queue_append(ctx->queue, ctx->first);
	k_queue_append(ctx->queue, ctx->second);
	ctx->append_path_ran = true;
}

ZTEST(queue_isr, test_append_order_and_empty)
{
	struct k_queue queue;
	struct queue_item first = { .id = 1 };
	struct queue_item second = { .id = 2 };
	struct test_context ctx = {
		.queue = &queue,
		.first = &first,
		.second = &second,
	};

	k_queue_init(&queue);
	irq_offload(append_from_isr, &ctx);

	zassert_true(ctx.append_path_ran);
	zassert_true(ctx.ran_in_isr);
	zassert_true(k_queue_get(&queue, K_NO_WAIT) == &first);
	zassert_true(k_queue_get(&queue, K_NO_WAIT) == &second);
	zassert_is_null(k_queue_get(&queue, K_NO_WAIT));
}

ZTEST_SUITE(queue_isr, NULL, NULL, NULL, NULL, NULL);
